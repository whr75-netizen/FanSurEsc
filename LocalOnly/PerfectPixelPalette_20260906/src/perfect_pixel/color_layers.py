"""Lossless single-color layers, editable RGB data, and a one-frame Aseprite file.

``colors.json`` owns editable RGB values; ``manifest.json`` owns mask positions
and bottom-to-top layer order. Masks are cropped, binary, 8-bit grayscale PNGs.
Original RGB underneath zero alpha is separate data, never a visible layer.
``rebuild_color_layers`` applies the current RGB table without changing masks.

The RGBA Aseprite writer follows the official specification:
https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md
It uses normal image/group layers, named palette entries, and zlib cels. In RGBA
mode, editing Aseprite's palette does not automatically recolor existing cels;
the separate RGB table and reconstruction function provide that behavior.
"""
import json
from pathlib import Path
import struct
import zlib

import numpy as np
from PIL import Image


_MAX_PIXELS = 16_777_216
_MAX_DIMENSION = 32_767
_MAX_LAYERS = 2048
_MAX_LAYER_WORK = 268_435_456
_MAX_CEL_PIXELS = 67_108_864
_MAX_JSON_BYTES = 8_388_608
_SCHEMA = 'perfect-pixel-color-layers-v1'


def _validate_rgba(image, name):
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or
            image.ndim != 3 or image.shape[2] != 4 or
            not image.shape[0] or not image.shape[1]):
        raise ValueError(name + ' must be a nonempty uint8 RGBA array')
    height, width = image.shape[:2]
    if max(height, width) > _MAX_DIMENSION or height * width > _MAX_PIXELS:
        raise ValueError(name + ' exceeds the layer export image bound')
    if np.any((image[..., 3] != 0) & (image[..., 3] != 255)):
        raise ValueError(name + ' must have binary alpha (0 or 255)')


def _packed_rgb(image):
    rgb = image[..., :3].astype(np.uint32)
    return (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]


def _prepare_layers(base, highlight):
    records, palette, groups = [], [], []
    work, cel_pixels = 0, 0
    for group_id, source in (('base', base), ('highlight', highlight)):
        packed = _packed_rgb(source)
        opaque = source[..., 3] == 255
        codes = np.unique(packed[opaque])
        if len(records) + len(codes) > _MAX_LAYERS:
            raise ValueError('too many colors for the 2048-layer export bound')
        work += int(source.shape[0] * source.shape[1] * len(codes))
        if work > _MAX_LAYER_WORK:
            raise ValueError('color-layer scan exceeds the processing bound')
        group = {'id': group_id, 'name': group_id.title(), 'layer_ids': []}
        for ordinal, code in enumerate(codes, 1):
            ys, xs = np.nonzero(opaque & (packed == code))
            x, y = int(xs.min()), int(ys.min())
            width, height = int(xs.max()) - x + 1, int(ys.max()) - y + 1
            cel_pixels += width * height
            if cel_pixels > _MAX_CEL_PIXELS:
                raise ValueError('combined layer bounds exceed the export bound')
            rgb = [int(code >> 16), int((code >> 8) & 255), int(code & 255)]
            layer_id = '{}_{:04d}'.format(group_id, ordinal)
            name = '{} #{:02X}{:02X}{:02X}'.format(layer_id, *rgb)
            color = {'id': layer_id, 'name': name, 'rgb': rgb,
                     'aseprite_palette_index': len(palette)}
            layer = {'id': layer_id, 'name': name, 'group_id': group_id,
                     'color_id': color['id'], 'original_rgb': rgb[:],
                     'bounds': {'x': x, 'y': y, 'width': width, 'height': height},
                     'mask_png': 'masks/' + layer_id + '.png',
                     'pixel_count': int(len(xs))}
            records.append((layer, ys - y, xs - x, color))
            palette.append(color)
            group['layer_ids'].append(layer_id)
        groups.append(group)
    return records, palette, groups


def _ase_string(value):
    encoded = value.encode('utf-8')
    return struct.pack('<H', len(encoded)) + encoded


def _ase_chunk(chunk_type, payload):
    return struct.pack('<IH', len(payload) + 6, chunk_type) + payload


def _ase_layer(name, group=False):
    # Visible/editable, normal blend, full opacity; child level 1 inside groups.
    payload = struct.pack('<6HB3x', 3, int(group), int(not group), 0, 0, 0, 255)
    return _ase_chunk(0x2004, payload + _ase_string(name))


def _write_aseprite(path, width, height, records, palette, groups, directory):
    chunks, layer_index = 0, 0
    cel_layer_indices = {}
    with path.open('xb') as stream:
        stream.write(bytes(144))  # Main header and the single frame header.

        def write_chunk(data):
            nonlocal chunks
            stream.write(data)
            chunks += 1

        if palette:
            data = struct.pack('<III8x', len(palette), 0, len(palette) - 1)
            for color in palette:
                data += struct.pack('<H4B', 1, *color['rgb'], 255)
                data += _ase_string(color['name'])
            write_chunk(_ase_chunk(0x2019, data))
        for group in groups:
            write_chunk(_ase_layer(group['name'], group=True))
            layer_index += 1
            for layer, _, _, color in records:
                if layer['group_id'] != group['id']:
                    continue
                write_chunk(_ase_layer(layer['name']))
                info = json.dumps({'color_id': color['id'],
                                   'palette_index': color['aseprite_palette_index'],
                                   'mask_png': layer['mask_png']}, separators=(',', ':'))
                write_chunk(_ase_chunk(0x2020, struct.pack('<I', 1) + _ase_string(info)))
                cel_layer_indices[layer['id']] = layer_index
                layer_index += 1
        for layer, ys, xs, color in records:
            box = layer['bounds']
            mask = np.zeros((box['height'], box['width']), np.uint8)
            mask[ys, xs] = 255
            Image.fromarray(mask).save(directory / layer['mask_png'])
            cel = np.zeros((*mask.shape, 4), np.uint8)
            cel[ys, xs, :3] = color['rgb']
            cel[ys, xs, 3] = 255
            data = struct.pack('<HhhBHh5xHH', cel_layer_indices[layer['id']],
                               box['x'], box['y'], 255, 2, 0,
                               box['width'], box['height'])
            write_chunk(_ase_chunk(0x2005, data + zlib.compress(cel.tobytes())))
        size = stream.tell()
        header = bytearray(128)
        struct.pack_into('<I5HIH', header, 0, size, 0xA5E0, 1, width, height, 32, 3, 100)
        struct.pack_into('<HBB', header, 32, len(palette), 1, 1)
        stream.seek(0)
        stream.write(header)
        stream.write(struct.pack('<IHHH2xI', size - 128, 0xF1FA, chunks, 100, chunks))


def _save_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def export_color_layers(base_rgba, highlight_rgba, output_directory):
    """Export to a new directory and return the JSON-safe manifest.

    Highlights must be opaque pixels within the opaque base silhouette. Inputs
    are never modified. Existing destinations, including empty directories, are
    rejected. Input and resource validation finishes before creating output.
    ``base.png`` retains every source byte, including RGB underneath alpha zero.
    Aseprite reproduces the visible pixels; the separate transparent RGB data
    allows Python reconstruction to retain invisible RGB bytes as well.
    """
    _validate_rgba(base_rgba, 'base_rgba')
    _validate_rgba(highlight_rgba, 'highlight_rgba')
    if base_rgba.shape != highlight_rgba.shape:
        raise ValueError('base and highlight dimensions must match')
    selected = highlight_rgba[..., 3] == 255
    if np.any(selected & (base_rgba[..., 3] == 0)):
        raise ValueError('highlight pixels must stay inside the base silhouette')
    directory = Path(output_directory)
    if directory.exists() or directory.is_symlink():
        raise FileExistsError('color-layer output directory already exists: ' + str(directory))
    records, palette, groups = _prepare_layers(base_rgba, highlight_rgba)
    height, width = base_rgba.shape[:2]
    manifest = {
        'schema': _SCHEMA, 'width': width, 'height': height,
        'color_mode': 'RGBA', 'alpha': 'binary',
        'stack_order': 'bottom_to_top', 'mask_encoding': 'cropped_L_png_0_or_255',
        'colors_json': 'colors.json', 'groups': groups,
        'layers': [record[0] for record in records],
        'transparent_rgb_png': 'base_transparent_rgb.png',
        'base_png': 'base.png', 'highlight_png': 'highlight.png',
        'composite_png': 'composite.png', 'aseprite_file': 'character_layers.aseprite',
        'aseprite_palette_editing': 'RGBA cels do not follow palette edits; '
                                    'edit colors.json and call rebuild_color_layers',
        'original_rgb_policy': 'layer original_rgb is an immutable provenance value; '
                               'colors.json is the editable color authority',
        'transparent_rgb_policy': 'restore RGB beneath alpha zero from the data PNG; '
                                  'these pixels are not visible Aseprite layers',
    }
    composite = base_rgba.copy()
    composite[selected] = highlight_rgba[selected]
    transparent_rgb = base_rgba[..., :3].copy()
    transparent_rgb[base_rgba[..., 3] == 255] = 0
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'masks').mkdir()
    Image.fromarray(base_rgba).save(directory / manifest['base_png'])
    Image.fromarray(highlight_rgba).save(directory / manifest['highlight_png'])
    Image.fromarray(composite).save(directory / manifest['composite_png'])
    Image.fromarray(transparent_rgb).save(directory / manifest['transparent_rgb_png'])
    _write_aseprite(directory / manifest['aseprite_file'], width, height,
                    records, palette, groups, directory)
    _save_json(directory / manifest['colors_json'], {'schema': _SCHEMA, 'colors': palette})
    _save_json(directory / 'manifest.json', manifest)
    return manifest


def _read_json(path):
    if path.stat().st_size > _MAX_JSON_BYTES:
        raise ValueError('color-layer JSON exceeds the read bound')
    with path.open(encoding='utf-8') as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get('schema') != _SCHEMA:
        raise ValueError('unsupported color-layer schema')
    return value


def _contained_file(directory, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('layer data paths must be relative to the export directory')
    candidate = (directory / relative).resolve()
    if directory not in candidate.parents:
        raise ValueError('layer data path escapes the export directory')
    return candidate


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _read_png(path, mode, size):
    with Image.open(path) as image:
        if image.format != 'PNG' or image.mode != mode or image.size != size:
            raise ValueError('layer data PNG has an unexpected format, mode or size')
        return np.array(image)


def rebuild_color_layers(output_directory, include_highlights=True):
    """Rebuild RGBA from saved binary masks and the current ``colors.json``.

    This read-only function makes changing color data useful without modifying
    geometry. Set ``include_highlights=False`` to reconstruct the base alone.
    Stored PNG previews and the Aseprite file are snapshots and are not updated.
    """
    if type(include_highlights) is not bool:
        raise ValueError('include_highlights must be a boolean')
    directory = Path(output_directory).resolve()
    manifest = _read_json(directory / 'manifest.json')
    width, height = manifest.get('width'), manifest.get('height')
    if (not _integer(width, 1, _MAX_DIMENSION) or
            not _integer(height, 1, _MAX_DIMENSION) or width * height > _MAX_PIXELS):
        raise ValueError('invalid color-layer canvas size')
    if (manifest.get('stack_order') != 'bottom_to_top' or
            manifest.get('mask_encoding') != 'cropped_L_png_0_or_255'):
        raise ValueError('unsupported layer order or mask encoding')
    colors = _read_json(_contained_file(directory, manifest.get('colors_json'))).get('colors')
    if not isinstance(colors, list) or len(colors) > _MAX_LAYERS:
        raise ValueError('invalid color table')
    palette = {}
    for color in colors:
        if not isinstance(color, dict):
            raise ValueError('invalid color table entry')
        color_id, rgb = color.get('id'), color.get('rgb')
        if (not isinstance(color_id, str) or not color_id or color_id in palette or
                not isinstance(rgb, list) or len(rgb) != 3 or
                not all(_integer(channel, 0, 255) for channel in rgb)):
            raise ValueError('color entries require unique IDs and integer RGB channels')
        palette[color_id] = rgb
    layers = manifest.get('layers')
    groups = manifest.get('groups')
    if (not isinstance(layers, list) or len(layers) > _MAX_LAYERS or
            not isinstance(groups, list) or len(groups) != 2 or
            any(not isinstance(group, dict) for group in groups) or
            [group.get('id') for group in groups] != ['base', 'highlight']):
        raise ValueError('invalid color-layer group layout')
    output = np.zeros((height, width, 4), np.uint8)
    output[..., :3] = _read_png(_contained_file(directory, manifest.get('transparent_rgb_png')),
                              'RGB', (width, height))
    layer_map, total_area = {}, 0
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError('invalid color-layer record')
        layer_id, color_id, box = layer.get('id'), layer.get('color_id'), layer.get('bounds')
        if (not isinstance(layer_id, str) or layer_id in layer_map or
                not isinstance(color_id, str) or color_id not in palette or
                not isinstance(box, dict)):
            raise ValueError('invalid color-layer identity, color reference or bounds')
        x, y, w, h = (box.get(key) for key in ('x', 'y', 'width', 'height'))
        if (not _integer(x, 0, width - 1) or not _integer(y, 0, height - 1) or
                not _integer(w, 1, width - x) or not _integer(h, 1, height - y)):
            raise ValueError('color-layer bounds exceed the canvas')
        total_area += w * h
        if total_area > _MAX_CEL_PIXELS:
            raise ValueError('combined layer bounds exceed the read bound')
        layer_map[layer_id] = layer
    seen = set()
    for group in groups:
        ids = group.get('layer_ids')
        if not isinstance(ids, list) or len(ids) > _MAX_LAYERS:
            raise ValueError('invalid group layer IDs')
        for layer_id in ids:
            if not isinstance(layer_id, str) or layer_id in seen or layer_id not in layer_map:
                raise ValueError('group layer IDs must reference each layer exactly once')
            seen.add(layer_id)
            layer = layer_map[layer_id]
            if layer.get('group_id') != group['id']:
                raise ValueError('layer group disagrees with its parent')
            if group['id'] == 'highlight' and not include_highlights:
                continue
            box = layer['bounds']
            x, y, w, h = (box[key] for key in ('x', 'y', 'width', 'height'))
            mask = _read_png(_contained_file(directory, layer.get('mask_png')), 'L', (w, h))
            if np.any((mask != 0) & (mask != 255)):
                raise ValueError('layer masks must be binary')
            occupied = mask == 255
            patch = output[y:y + h, x:x + w]
            if group['id'] == 'highlight' and np.any(occupied & (patch[..., 3] == 0)):
                raise ValueError('highlight mask extends outside the base silhouette')
            patch[occupied, :3] = palette[layer['color_id']]
            patch[occupied, 3] = 255
    if seen != set(layer_map):
        raise ValueError('every layer must belong to a group')
    return output
