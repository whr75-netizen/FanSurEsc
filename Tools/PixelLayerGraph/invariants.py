"""Mechanical mathematical invariant checkers for the Hierarchical Pixel Layer Graph.

Zero external dependencies (Python 3.10 standard library only).
AI workers cannot self-certify pass/fail; every gate here computes exact deterministic
proofs over actual RGBA pixel buffers, PNG files, layer-tree schemas, and source code.
"""
from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

RGBA = Tuple[int, int, int, int]
RGB = Tuple[int, int, int]

VALID_DOMAINS = ("3D_SOURCE", "LOCAL_GRID", "2D_COMPOSE", "2D_FINISH")
DOMAIN_ORDER = {d: i for i, d in enumerate(VALID_DOMAINS)}
VALID_GRIDS = {"ROOT_GRID", "LOCAL_EYE_GRID", "FINAL_2D_GRID"}
VALID_CLIPS = {"NONE", "CLIP_TO_PARENT", "CLIP_TO_MASK"}
VALID_OCCLUDES = {"BASE", "DEPTH_Z_TEST", "LAYER_OVER_PARENT"}
VALID_PALETTES = {"INDEX_ONLY_RQ", "FINAL_LUT_RESOLVE"}
VALID_DESIGN_STATUS = {"CONFIRMED", "TBD_DESIGN"}

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def write_png_rgba(path: str | Path, width: int, height: int, pixels: Sequence[RGBA]) -> None:
    """Write an uncompressed-filter-0 RGBA8 PNG using pure stdlib zlib+struct."""
    if len(pixels) != width * height:
        raise ValueError(f"Pixel count {len(pixels)} != {width}*{height}")
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # Filter type 0 (None)
        row_start = y * width
        for x in range(width):
            r, g, b, a = pixels[row_start + x]
            raw.extend((r & 255, g & 255, b & 255, a & 255))

    def chunk(ctype: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=6)
    out = PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    Path(path).write_bytes(out)


def read_png_rgba(path: str | Path) -> Tuple[int, int, List[RGBA]]:
    """Read an 8-bit RGB or RGBA non-interlaced PNG using pure stdlib."""
    data = Path(path).read_bytes()
    if not data.startswith(PNG_SIG):
        raise ValueError(f"Not a PNG file: {path}")
    pos = len(PNG_SIG)
    width = height = bit_depth = color_type = interlace = 0
    idat_parts: List[bytes] = []
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos : pos + 8])
        pos += 8
        payload = data[pos : pos + length]
        pos += length + 4  # skip CRC
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif ctype == b"IDAT":
            idat_parts.append(payload)
        elif ctype == b"IEND":
            break
    if bit_depth != 8 or color_type not in (2, 6) or interlace != 0:
        raise ValueError(f"Unsupported PNG format in {path}: bit_depth={bit_depth}, color_type={color_type}, interlace={interlace}")
    bpp = 4 if color_type == 6 else 3
    stride = width * bpp
    raw = zlib.decompress(b"".join(idat_parts))
    recon = bytearray(height * stride)
    src = 0
    for y in range(height):
        ftype = raw[src]
        src += 1
        row_off = y * stride
        prev_off = (y - 1) * stride
        for i in range(stride):
            x = raw[src]
            src += 1
            a = recon[row_off + i - bpp] if i >= bpp else 0
            b = recon[prev_off + i] if y > 0 else 0
            c = recon[prev_off + i - bpp] if (y > 0 and i >= bpp) else 0
            if ftype == 0:
                val = x
            elif ftype == 1:
                val = (x + a) & 255
            elif ftype == 2:
                val = (x + b) & 255
            elif ftype == 3:
                val = (x + ((a + b) >> 1)) & 255
            elif ftype == 4:
                val = (x + _paeth(a, b, c)) & 255
            else:
                raise ValueError(f"Invalid PNG filter {ftype}")
            recon[row_off + i] = val
    pixels: List[RGBA] = []
    if bpp == 4:
        for i in range(0, len(recon), 4):
            pixels.append((recon[i], recon[i + 1], recon[i + 2], recon[i + 3]))
    else:
        for i in range(0, len(recon), 3):
            pixels.append((recon[i], recon[i + 1], recon[i + 2], 255))
    return width, height, pixels


def check_layer_tree_integrity(tree: dict) -> dict:
    """Validate hierarchical layer tree schema, acyclicity, parent links, and domain rules."""
    errors: List[str] = []
    nodes = tree.get("nodes", [])
    if not nodes:
        return {"passed": False, "errors": ["Tree has zero nodes"], "nodeCount": 0}
    by_id: Dict[str, dict] = {}
    for idx, node in enumerate(nodes):
        nid = node.get("id")
        if not nid or not isinstance(nid, str):
            errors.append(f"Node index {idx} missing valid string id")
            continue
        if nid in by_id:
            errors.append(f"Duplicate node id: {nid}")
            continue
        by_id[nid] = node
        if node.get("domain") not in DOMAIN_ORDER:
            errors.append(f"Node {nid}: invalid domain {node.get('domain')}")
        if node.get("grid_space") not in VALID_GRIDS:
            errors.append(f"Node {nid}: invalid grid_space {node.get('grid_space')}")
        if node.get("clip_mode") not in VALID_CLIPS:
            errors.append(f"Node {nid}: invalid clip_mode {node.get('clip_mode')}")
        if node.get("occlude_mode") not in VALID_OCCLUDES:
            errors.append(f"Node {nid}: invalid occlude_mode {node.get('occlude_mode')}")
        if node.get("palette_mode") not in VALID_PALETTES:
            errors.append(f"Node {nid}: invalid palette_mode {node.get('palette_mode')}")
        if node.get("design_status") not in VALID_DESIGN_STATUS:
            errors.append(f"Node {nid}: invalid design_status {node.get('design_status')}")

    for node in nodes:
        nid = node["id"]
        pid = node.get("parent_id")
        if pid is not None:
            if pid not in by_id:
                errors.append(f"Node {nid}: parent_id '{pid}' does not exist")
            elif pid == nid:
                errors.append(f"Node {nid}: self-parent cycle")
            else:
                # Cycle detection
                seen = {nid}
                cur = pid
                while cur is not None:
                    if cur in seen:
                        errors.append(f"Cycle detected involving node {nid}")
                        break
                    seen.add(cur)
                    cur = by_id[cur].get("parent_id")
                # Hierarchical prefix check (e.g., 3-2-1 must be child of 3-2)
                if not nid.startswith(pid + "-"):
                    errors.append(f"Node {nid}: hierarchical id does not start with parent prefix '{pid}-'")
        elif node.get("clip_mode") == "CLIP_TO_PARENT":
            errors.append(f"Node {nid}: CLIP_TO_PARENT requires a non-null parent_id")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "nodeCount": len(nodes),
        "confirmedCount": sum(1 for n in nodes if n.get("design_status") == "CONFIRMED"),
        "tbdDesignCount": sum(1 for n in nodes if n.get("design_status") == "TBD_DESIGN"),
    }


def check_uniform_grid_no_mixels(pixels: Sequence[RGBA], width: int, height: int, pitch: int) -> dict:
    """Reject half-pixel/sub-cell fractures ('mixels') when rendered at integer pitch >= 1."""
    if pitch < 1:
        raise ValueError("pitch must be >= 1")
    if width % pitch != 0 or height % pitch != 0:
        return {
            "passed": False,
            "mixelCellCount": -1,
            "reason": f"Dimensions {width}x{height} are not divisible by pitch {pitch}",
            "witnessCells": [],
        }
    if pitch == 1:
        return {"passed": True, "mixelCellCount": 0, "checkedLogicalCells": width * height, "witnessCells": []}

    lw, lh = width // pitch, height // pitch
    mixels: List[dict] = []
    for ly in range(lh):
        for lx in range(lw):
            first = pixels[(ly * pitch) * width + (lx * pitch)]
            uniform = True
            for dy in range(pitch):
                row_off = (ly * pitch + dy) * width + (lx * pitch)
                for dx in range(pitch):
                    if pixels[row_off + dx] != first:
                        uniform = False
                        break
                if not uniform:
                    break
            if not uniform:
                if len(mixels) < 16:
                    mixels.append({"logicalXY": [lx, ly], "topLeftPhysicalXY": [lx * pitch, ly * pitch]})
    return {
        "passed": len(mixels) == 0,
        "mixelCellCount": len(mixels),
        "checkedLogicalCells": lw * lh,
        "pitch": pitch,
        "witnessCells": mixels,
    }


def check_parent_clip_containment(
    child_pixels: Sequence[RGBA],
    parent_mask_pixels: Sequence[RGBA],
    width: int,
    height: int,
    alpha_threshold: int = 1,
) -> dict:
    """Prove 100% of opaque child pixels stay inside parent clip mask (0 frog-eye leaks)."""
    if len(child_pixels) != width * height or len(parent_mask_pixels) != width * height:
        raise ValueError("Child and parent mask dimensions mismatch")
    leaks: List[List[int]] = []
    child_opaque = 0
    for y in range(height):
        row = y * width
        for x in range(width):
            if child_pixels[row + x][3] >= alpha_threshold:
                child_opaque += 1
                if parent_mask_pixels[row + x][3] < alpha_threshold:
                    if len(leaks) < 32:
                        leaks.append([x, y])
    return {
        "passed": len(leaks) == 0,
        "childOpaquePixels": child_opaque,
        "leakCount": len(leaks),
        "leakWitnessXY": leaks,
    }


def check_local_eye_frontal_symmetry(
    left_pixels: Sequence[RGBA],
    right_pixels: Sequence[RGBA],
    width: int,
    height: int,
) -> dict:
    """Verify exact horizontal mirror symmetry (u <-> W-1-u) on independent local eye grids.

    If this fails in a frontal pose, the bug is upstream in 3D/rig/UV/lighting (G1),
    NOT something to paper over in 2D pixelation!
    """
    if len(left_pixels) != width * height or len(right_pixels) != width * height:
        raise ValueError("Left/right eye grid dimensions mismatch")
    mismatches: List[dict] = []
    for y in range(height):
        row = y * width
        for x in range(width):
            l_px = left_pixels[row + x]
            r_px = right_pixels[row + (width - 1 - x)]
            if l_px != r_px:
                if len(mismatches) < 32:
                    mismatches.append({"localXY": [x, y], "leftRGBA": list(l_px), "rightMirrorRGBA": list(r_px)})
    passed = len(mismatches) == 0
    return {
        "passed": passed,
        "exitClass": "NODE_DONE" if passed else "UPSTREAM_3D_ASYMMETRY",
        "mismatchCount": len(mismatches),
        "witnesses": mismatches,
    }


def check_finite_palette_exact(
    pixels: Sequence[RGBA],
    allowed_rgb: Iterable[RGB],
    alpha_threshold: int = 1,
) -> dict:
    """Prove every opaque output pixel belongs 100% to the finite LUT palette (0 double RGB mult)."""
    palette_set: Set[RGB] = {(r, g, b) for r, g, b in allowed_rgb}
    bad: List[List[int]] = []
    opaque = 0
    for r, g, b, a in pixels:
        if a >= alpha_threshold:
            opaque += 1
            if (r, g, b) not in palette_set:
                if len(bad) < 32:
                    bad.append([r, g, b])
    return {
        "passed": len(bad) == 0,
        "opaquePixels": opaque,
        "outOfPaletteCount": len(bad),
        "witnessRGB": bad,
    }


def check_source_no_forbidden_ops(file_paths: Sequence[str | Path], forbidden_patterns: Sequence[str]) -> dict:
    """Static source code gate rejecting legacy double-ops, D3D11 fences, and inverse ray solvers."""
    hits: List[dict] = []
    checked = 0
    compiled = [(pat, re.compile(re.escape(pat))) for pat in forbidden_patterns]
    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            hits.append({"file": str(p), "pattern": "<MISSING_FILE>", "line": 0})
            continue
        checked += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat, rx in compiled:
                if rx.search(line):
                    hits.append({"file": str(p), "pattern": pat, "line": lineno})
    return {
        "passed": len(hits) == 0,
        "checkedFiles": checked,
        "violationCount": len(hits),
        "violations": hits,
    }
