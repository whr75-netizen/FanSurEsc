"""Automated verification suite for Tools/PixelLayerGraph.

Proves mechanically that every real failure observed in R1..R22 (mixel sub-cells,
frog-eye clip leaks, frontal eye asymmetry, out-of-palette RGB multiplication,
forbidden inverse ray-tracing scripts, undeclared side folders, TBD design hijacking,
and infinite retry loops) is caught and blocked deterministically.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import invariants as inv  # noqa: E402
import layer_graph as lg  # noqa: E402


def make_block_rgba(logical_w: int, logical_h: int, pitch: int, fn) -> tuple[int, int, list[inv.RGBA]]:
    w, h = logical_w * pitch, logical_h * pitch
    pixels: list[inv.RGBA] = [(0, 0, 0, 0)] * (w * h)
    for ly in range(logical_h):
        for lx in range(logical_w):
            col = fn(lx, ly)
            for dy in range(pitch):
                for dx in range(pitch):
                    pixels[(ly * pitch + dy) * w + (lx * pitch + dx)] = col
    return w, h, pixels


class PixelLayerGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tree_path = HERE / "character_layer_tree.json"
        self.tree = lg.load_json(self.tree_path)

    def test_tree_integrity_and_infinite_extensibility(self) -> None:
        res = inv.check_layer_tree_integrity(self.tree)
        self.assertTrue(res["passed"], res["errors"])
        self.assertGreaterEqual(res["nodeCount"], 22)
        self.assertEqual(res["tbdDesignCount"], 3)  # 2-1-1, 3-3, 3-4

        # Verify inherited clipping chain on deep 6-level nested node 3-2-1-1-1-1 (EyePupilAndHighlight)
        clips = lg.inherited_clip_chain(self.tree, "3-2-1-1-1-1")
        self.assertEqual(clips, ["3-2-1", "3-2-1-1", "3-2-1-1-1"])

    def test_compile_gpu_plan_flattens_25_logical_layers_to_5_passes(self) -> None:
        plan = lg.compile_gpu_plan(self.tree)
        self.assertEqual(plan["logical_layer_count"], len(self.tree["nodes"]))
        self.assertEqual(plan["physical_gpu_pass_count"], 5)
        total_assigned = sum(len(p["nodes"]) for p in plan["passes"])
        self.assertEqual(total_assigned, len(self.tree["nodes"]))

    def test_mixel_gate_catches_r22_half_pixel_fracture(self) -> None:
        # Clean 2x2 pitch=2 grid passes
        w, h, px = make_block_rgba(4, 4, 2, lambda x, y: (61, 46, 46, 255) if x < 2 else (242, 235, 234, 255))
        self.assertTrue(inv.check_uniform_grid_no_mixels(px, w, h, 2)["passed"])

        # Introduce 1x1 physical mixel (exact bug from COMMON_GRID_PITCH_TRACE.json!)
        px[0] = (33, 31, 57, 255)
        bad = inv.check_uniform_grid_no_mixels(px, w, h, 2)
        self.assertFalse(bad["passed"])
        self.assertEqual(bad["mixelCellCount"], 1)

    def test_parent_clip_gate_blocks_frog_eye_spill(self) -> None:
        # Parent aperture mask covers x in [1..2], y in [1..2]
        w, h, parent_mask = make_block_rgba(4, 4, 1, lambda x, y: (255, 255, 255, 255) if 1 <= x <= 2 and 1 <= y <= 2 else (0, 0, 0, 0))
        _, _, clean_iris = make_block_rgba(4, 4, 1, lambda x, y: (61, 46, 46, 255) if 1 <= x <= 2 and 1 <= y <= 2 else (0, 0, 0, 0))
        self.assertTrue(inv.check_parent_clip_containment(clean_iris, parent_mask, w, h)["passed"])

        # Oversized eyeball spills to (0, 1) -> Frog-eye leak caught!
        frog_iris = list(clean_iris)
        frog_iris[1 * w + 0] = (61, 46, 46, 255)
        bad = inv.check_parent_clip_containment(frog_iris, parent_mask, w, h)
        self.assertFalse(bad["passed"])
        self.assertEqual(bad["leakCount"], 1)
        self.assertEqual(bad["leakWitnessXY"], [[0, 1]])

    def test_frontal_local_eye_symmetry_attributes_upstream_3d(self) -> None:
        # Perfectly mirrored 4x3 local eye grids pass
        w, h, left_eye = make_block_rgba(4, 3, 1, lambda x, y: (61, 46, 46, 255) if x in (1, 2) else (242, 235, 234, 255))
        _, _, right_eye = make_block_rgba(4, 3, 1, lambda x, y: left_eye[y * 4 + (3 - x)])
        ok = inv.check_local_eye_frontal_symmetry(left_eye, right_eye, w, h)
        self.assertTrue(ok["passed"])
        self.assertEqual(ok["exitClass"], "NODE_DONE")

        # Break 1 cell on right eye -> must report UPSTREAM_3D_ASYMMETRY
        asym_right = list(right_eye)
        asym_right[0] = (124, 85, 69, 255)
        fail = inv.check_local_eye_frontal_symmetry(left_eye, asym_right, w, h)
        self.assertFalse(fail["passed"])
        self.assertEqual(fail["exitClass"], "UPSTREAM_3D_ASYMMETRY")

    def test_finite_palette_and_png_roundtrip(self) -> None:
        allowed = [(61, 46, 46), (124, 85, 69), (242, 235, 234)]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.png"
            w, h, px = make_block_rgba(2, 2, 2, lambda x, y: (61, 46, 46, 255) if (x + y) % 2 == 0 else (242, 235, 234, 255))
            inv.write_png_rgba(p, w, h, px)
            rw, rh, rpx = inv.read_png_rgba(p)
            self.assertEqual((rw, rh), (w, h))
            self.assertEqual(rpx, px)
            self.assertTrue(inv.check_finite_palette_exact(rpx, allowed)["passed"])

            # Introduce double-multiplied RGB out of palette
            rpx[0] = (60, 45, 45, 255)
            bad = inv.check_finite_palette_exact(rpx, allowed)
            self.assertFalse(bad["passed"])
            self.assertEqual(bad["outOfPaletteCount"], 1)

    def test_state_machine_enforces_scope_forbidden_ops_attempts_and_invalidation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_path = root / "state.json"
            lg.init_state(state_path, self.tree_path)

            # 1. Next ticket must be node "1" (BackHair) and compact (< 3 KB)
            t1 = lg.next_ticket(state_path)
            self.assertEqual(t1["ticket_status"], "READY")
            self.assertEqual(t1["node_id"], "1")
            self.assertLess(len(json.dumps(t1, ensure_ascii=False)), 3500)

            # Create allowed shader file containing FORBIDDEN legacy pattern
            shader_rel = "Assets/Rendering/PixelLayerTree/Shaders/RootGBufferPass.shader"
            shader_abs = root / shader_rel
            shader_abs.parent.mkdir(parents=True, exist_ok=True)
            shader_abs.write_text("// accidental legacy call nativeReserveSupportMask\n", encoding="utf-8")

            good_png = root / "node_1.png"
            w, h, px = make_block_rgba(4, 4, 2, lambda x, y: (61, 46, 46, 255))
            inv.write_png_rgba(good_png, w, h, px)

            sub_path = root / "sub.json"
            lg.save_json(sub_path, {
                "node_id": "1",
                "changed_files": [shader_rel],
                "artifacts": {"node_png": str(good_png), "pitch": 2},
            })
            # Attempt 1 rejected for forbidden legacy pattern
            r1 = lg.submit_node(state_path, sub_path, root)
            self.assertFalse(r1["passed"])
            self.assertEqual(r1["exit_class"], "FORBIDDEN_DOUBLE_OP")

            # Attempt 2: try undeclared side-folder file -> rejected & hits max_attempts=2!
            side_file = root / "t3-aperture-154/r23/solve_aperture.py"
            side_file.parent.mkdir(parents=True, exist_ok=True)
            side_file.write_text("# hack\n", encoding="utf-8")
            lg.save_json(sub_path, {
                "node_id": "1",
                "changed_files": [shader_rel, "t3-aperture-154/r23/solve_aperture.py"],
                "artifacts": {"node_png": str(good_png), "pitch": 2},
            })
            r2 = lg.submit_node(state_path, sub_path, root)
            self.assertFalse(r2["passed"])
            self.assertEqual(r2["exit_class"], "SCOPE_VIOLATION")
            self.assertEqual(r2["status"], "BLOCKED_MAX_ATTEMPTS")

            # Next ticket now reports BLOCKED (stops infinite retry loop!)
            blocked = lg.next_ticket(state_path)
            self.assertEqual(blocked["ticket_status"], "BLOCKED")

            # Clean fix + invalidate node "1" -> now passes cleanly!
            shader_abs.write_text("// clean forward root G-Buffer shader\n", encoding="utf-8")
            lg.invalidate_node(state_path, "1")
            lg.save_json(sub_path, {
                "node_id": "1",
                "changed_files": [shader_rel],
                "artifacts": {"node_png": str(good_png), "pitch": 2},
            })
            r3 = lg.submit_node(state_path, sub_path, root)
            self.assertTrue(r3["passed"])
            self.assertEqual(r3["status"], "DONE")

            # Attempt to submit a TBD_DESIGN node ("3-4" NoseAndMouth) -> hard rejected!
            lg.save_json(sub_path, {"node_id": "3-4", "changed_files": [], "artifacts": {}})
            with self.assertRaises(ValueError):
                lg.submit_node(state_path, sub_path, root)


if __name__ == "__main__":
    unittest.main()
