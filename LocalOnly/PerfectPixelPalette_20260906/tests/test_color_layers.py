import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from perfect_pixel.color_layers import export_color_layers, rebuild_color_layers


def _fixture():
    base = np.zeros((7, 9, 4), np.uint8)
    base[1:6, 1:8] = (30, 60, 90, 255)
    base[3:5, 4:7] = (110, 80, 40, 255)
    base[2, 3] = (2, 3, 4, 255)
    base[0, 0, :3] = (7, 8, 9)  # Invisible RGB is still original data.
    highlight = np.zeros_like(base)
    highlight[1, 2:5] = (100, 140, 180, 255)
    highlight[3, 5] = (170, 140, 90, 255)
    highlight[5, 6] = base[3, 5]  # Same RGB in different groups stays independent.
    return base, highlight


def _read_aseprite(path):
    """Independent, deliberately small reader for the emitted standard chunks."""
    raw = path.read_bytes()
    size, magic, frames, width, height, depth = struct.unpack_from('<I5H', raw)
    assert (size, magic, frames, depth) == (len(raw), 0xA5E0, 1, 32)
    frame_size, frame_magic, old_count, duration, new_count = struct.unpack_from('<IHHH2xI', raw, 128)
    assert frame_size == len(raw) - 128 and frame_magic == 0xF1FA and duration == 100
    assert old_count == new_count
    layers, cels, palette = [], [], []
    position = 144
    for _ in range(new_count):
        chunk_size, kind = struct.unpack_from('<IH', raw, position)
        assert chunk_size >= 6 and position + chunk_size <= len(raw)
        payload = raw[position + 6:position + chunk_size]
        if kind == 0x2004:
            flags, layer_type, child, _, _, blend, opacity = struct.unpack_from('<6HB', payload)
            length = struct.unpack_from('<H', payload, 16)[0]
            name = payload[18:18 + length].decode('utf-8')
            assert flags & 3 == 3 and blend == 0 and opacity == 255
            layers.append({'name': name, 'type': layer_type, 'child': child})
        elif kind == 0x2005:
            layer, x, y, opacity, cel_type, z_index = struct.unpack_from('<HhhBHh', payload)
            w, h = struct.unpack_from('<HH', payload, 16)
            assert opacity == 255 and cel_type == 2 and z_index == 0
            pixels = np.frombuffer(zlib.decompress(payload[20:]), np.uint8).reshape(h, w, 4)
            assert layers[layer]['type'] == 0
            cels.append((layer, x, y, pixels))
        elif kind == 0x2019:
            count, start, end = struct.unpack_from('<III', payload)
            assert start == 0 and end == count - 1
            cursor = 20
            for _ in range(count):
                flags, r, g, b, a = struct.unpack_from('<H4B', payload, cursor)
                cursor += 6
                assert flags == 1 and a == 255
                length = struct.unpack_from('<H', payload, cursor)[0]
                cursor += 2
                name = payload[cursor:cursor + length].decode('utf-8')
                cursor += length
                palette.append((name, [r, g, b]))
            assert cursor == len(payload)
        else:
            assert kind == 0x2020  # Layer metadata only.
        position += chunk_size
    assert position == len(raw)
    composite = np.zeros((height, width, 4), np.uint8)
    base = composite.copy()
    group = None
    for layer_index, layer in enumerate(layers):
        if layer['type'] == 1:
            assert layer['child'] == 0
            group = layer['name']
            continue
        assert layer['child'] == 1
        for cel_layer, x, y, pixels in cels:
            if cel_layer != layer_index:
                continue
            selected = pixels[..., 3] == 255
            assert set(np.unique(pixels[..., 3])) <= {0, 255}
            assert len(np.unique(pixels[selected, :3], axis=0)) == 1
            h, w = pixels.shape[:2]
            composite[y:y + h, x:x + w][selected] = pixels[selected]
            if group == 'Base':
                base[y:y + h, x:x + w][selected] = pixels[selected]
    return layers, cels, palette, base, composite


class ColorLayerTests(unittest.TestCase):
    def test_exact_png_and_mask_roundtrip_including_invisible_rgb(self):
        base, highlight = _fixture()
        before = base.copy(), highlight.copy()
        expected = base.copy()
        expected[highlight[..., 3] == 255] = highlight[highlight[..., 3] == 255]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            meta = export_color_layers(base, highlight, directory)
            self.assertEqual(json.loads(json.dumps(meta, allow_nan=False)), meta)
            self.assertEqual(json.loads((directory / 'manifest.json').read_text()), meta)
            for name, array in (('base_png', base), ('highlight_png', highlight), ('composite_png', expected)):
                with Image.open(directory / meta[name]) as image:
                    np.testing.assert_array_equal(np.array(image), array)
            np.testing.assert_array_equal(rebuild_color_layers(directory, False), base)
            np.testing.assert_array_equal(rebuild_color_layers(directory), expected)
            self.assertEqual([group['id'] for group in meta['groups']], ['base', 'highlight'])
            self.assertEqual(len(meta['layers']), 6)
            for layer in meta['layers']:
                with Image.open(directory / layer['mask_png']) as image:
                    mask = np.array(image)
                    self.assertEqual(image.mode, 'L')
                    self.assertEqual(image.size, (layer['bounds']['width'], layer['bounds']['height']))
                self.assertEqual(np.count_nonzero(mask), layer['pixel_count'])
                self.assertEqual(set(np.unique(mask)) - {0, 255}, set())
        np.testing.assert_array_equal(base, before[0])
        np.testing.assert_array_equal(highlight, before[1])

    def test_aseprite_groups_cropped_cels_palette_and_visible_roundtrip(self):
        base, highlight = _fixture()
        expected = base.copy()
        expected[highlight[..., 3] == 255] = highlight[highlight[..., 3] == 255]
        base[base[..., 3] == 0] = 0
        expected[expected[..., 3] == 0] = 0
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            meta = export_color_layers(base, highlight, directory)
            layers, cels, palette, actual_base, actual = _read_aseprite(directory / meta['aseprite_file'])
            self.assertEqual([layer['name'] for layer in layers if layer['type'] == 1], ['Base', 'Highlight'])
            self.assertEqual(len(cels), len(meta['layers']))
            self.assertEqual([color[1] for color in palette], [layer['original_rgb'] for layer in meta['layers']])
            self.assertTrue(all(cel[1] > 0 and cel[2] > 0 for cel in cels))
            np.testing.assert_array_equal(actual_base, base)
            np.testing.assert_array_equal(actual, expected)

    def test_palette_edit_changes_one_color_without_mask_or_base_mutation(self):
        base, highlight = _fixture()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            meta = export_color_layers(base, highlight, directory)
            original_masks = {p.name: p.read_bytes() for p in (directory / 'masks').iterdir()}
            colors_path = directory / meta['colors_json']
            colors = json.loads(colors_path.read_text())
            chosen = next(c for c in colors['colors'] if c['id'].startswith('highlight_'))
            old = chosen['rgb'][:]
            chosen['rgb'] = [245, 246, 247]
            colors_path.write_text(json.dumps(colors))
            rebuilt = rebuild_color_layers(directory)
            selected = np.all(highlight[..., :3] == old, axis=2) & (highlight[..., 3] == 255)
            np.testing.assert_array_equal(rebuilt[selected, :3], np.tile(chosen['rgb'], (int(selected.sum()), 1)))
            np.testing.assert_array_equal(rebuild_color_layers(directory, False), base)
            np.testing.assert_array_equal(rebuilt[..., 3], base[..., 3])
            self.assertEqual(original_masks, {p.name: p.read_bytes() for p in (directory / 'masks').iterdir()})

    def test_all_transparent_and_empty_overlay_are_supported(self):
        for opaque in (False, True):
            with self.subTest(opaque=opaque), tempfile.TemporaryDirectory() as temporary:
                base = np.full((2, 3, 4), (6, 7, 8, 255 if opaque else 0), np.uint8)
                highlight = np.zeros_like(base)
                directory = Path(temporary) / 'layers'
                meta = export_color_layers(base, highlight, directory)
                np.testing.assert_array_equal(rebuild_color_layers(directory), base)
                self.assertEqual(meta['groups'][1]['layer_ids'], [])
                _read_aseprite(directory / meta['aseprite_file'])

    def test_existing_empty_directory_and_existing_file_are_not_overwritten(self):
        base, highlight = _fixture()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.assertRaises(FileExistsError):
                export_color_layers(base, highlight, directory)
            existing = directory / 'sentinel'
            existing.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):
                export_color_layers(base, highlight, existing)
            self.assertEqual(existing.read_bytes(), b'keep')
            self.assertEqual(list(directory.iterdir()), [existing])

    def test_invalid_input_and_resource_bounds_write_nothing(self):
        base, highlight = _fixture()
        partial = base.copy()
        partial[2, 2, 3] = 128
        outside = highlight.copy()
        outside[0, 0] = (200, 200, 200, 255)
        cases = [(base.astype(float), highlight), (base[..., :3], highlight),
                 (base[:0], highlight[:0]), (partial, highlight), (base, partial),
                 (base, highlight[:, :-1]), (base, outside)]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            for a, b in cases:
                with self.assertRaises(ValueError):
                    export_color_layers(a, b, directory)
                self.assertFalse(directory.exists())
            for limit in ('_MAX_PIXELS', '_MAX_DIMENSION', '_MAX_LAYERS', '_MAX_LAYER_WORK', '_MAX_CEL_PIXELS'):
                with patch('perfect_pixel.color_layers.' + limit, 1):
                    with self.assertRaises(ValueError):
                        export_color_layers(base, highlight, directory)
                self.assertFalse(directory.exists())

    def test_rebuild_rejects_path_escape_and_nonbinary_mask(self):
        base, highlight = _fixture()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            meta = export_color_layers(base, highlight, directory)
            manifest_path = directory / 'manifest.json'
            meta['layers'][0]['mask_png'] = '../outside.png'
            manifest_path.write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError, 'escapes'):
                rebuild_color_layers(directory)
            meta['layers'][0]['mask_png'] = 'masks/' + meta['layers'][0]['id'] + '.png'
            manifest_path.write_text(json.dumps(meta))
            path = directory / meta['layers'][0]['mask_png']
            with Image.open(path) as image:
                mask = np.array(image)
            mask[0, 0] = 128
            Image.fromarray(mask).save(path)
            with self.assertRaisesRegex(ValueError, 'binary'):
                rebuild_color_layers(directory)

    def test_rebuild_rejects_invalid_editable_rgb(self):
        base, highlight = _fixture()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'layers'
            meta = export_color_layers(base, highlight, directory)
            colors_path = directory / meta['colors_json']
            colors = json.loads(colors_path.read_text())
            for bad in ([0, 0, 256], [0, True, 0], [0.5, 2, 3], [1, 2]):
                colors['colors'][0]['rgb'] = bad
                colors_path.write_text(json.dumps(colors))
                with self.assertRaises(ValueError):
                    rebuild_color_layers(directory)


if __name__ == '__main__':
    unittest.main()
