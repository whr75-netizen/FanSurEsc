"""N15 native pixel-center geometry: finite solids or independent plane coverage.

No image perimeter is OR-ed into coverage.  ``position`` is in editable canonical
ticks; ``normal`` is in world meters' coordinate basis.  Palette/edges are separate
stages and may only address pixels already owned by this geometry stage.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


_SQRT6 = math.sqrt(6.0)
_PRIMARY_DIRECTION = np.array([1.0, -2.0, 1.0], dtype=np.float64)
_FACE_PRIORITY = np.array([2, 2, 0, 0, 1, 1], dtype=np.int8)
_WORLD_NORMALS = np.array([
    [0.0, -1.0, 0.0], [0.0, 1.0, 0.0],
    [0.0, 0.0, -1.0], [0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
], dtype=np.float64)


def project(points):
    """Canonical width/height/depth -> the fixed 2:1 native projection."""
    p = np.asarray(points, dtype=np.float64)
    return np.stack((2.0*p[..., 0]-2.0*p[..., 2],
                     -p[..., 0]-p[..., 2]-p[..., 1]), axis=-1)


def to_world(points):
    p = np.asarray(points, dtype=np.float64)
    return np.stack((-p[..., 2]/32.0, p[..., 0]/32.0,
                     p[..., 1]/(32.0*_SQRT6)), axis=-1)


def light_to_ticks(light_world):
    light = np.asarray(light_world, dtype=np.float64)
    if light.shape != (3,) or not np.isfinite(light).all():
        raise ValueError('light_world must be a finite 3-vector')
    length = float(np.linalg.norm(light))
    if length == 0.0:
        raise ValueError('A zero light direction has no shadow ray')
    light = light/length
    return np.array([light[1]*32.0, light[2]*32.0*_SQRT6,
                     -light[0]*32.0], dtype=np.float64)


def _profile_values(profile, count):
    if isinstance(count, bool) or int(count) != count or count < 1:
        raise ValueError('count must be a positive integer')
    count = int(count)
    names = ('end_cap', 'module_pitch', 'height', 'cap_thickness', 'depth',
             'handle_x', 'handle_y', 'handle_height', 'handle_width')
    p = {key: float(profile[key]) for key in names}
    if not all(math.isfinite(value) for value in p.values()):
        raise ValueError('Geometry dimensions must be finite')
    if any(p[key] <= 0 for key in ('module_pitch', 'height', 'cap_thickness',
                                  'depth', 'handle_height', 'handle_width')):
        raise ValueError('Physical dimensions must be positive')
    if p['end_cap'] < 0 or p['cap_thickness'] >= p['height']:
        raise ValueError('Invalid cap/body dimensions')
    p['count'] = count
    p['width'] = 2.0*p['end_cap']+count*p['module_pitch']
    p['body_top'] = p['height']-p['cap_thickness']
    if not (0 <= p['handle_y'] < p['handle_y']+p['handle_height'] <= p['body_top']):
        raise ValueError('Handle must attach inside the body front')
    if not (0 <= p['handle_x'] < p['handle_x']+p['handle_width'] <= p['module_pitch']):
        raise ValueError('Handle must fit its repeated module')
    return p


def _make_boxes(p):
    boxes = [
        {'part': 0, 'name': 'body', 'minimum_ticks': [0.0, 0.0, 0.0],
         'maximum_ticks': [p['width'], p['body_top'], p['depth']]},
        {'part': 1, 'name': 'cap', 'minimum_ticks': [-1.0, p['body_top'], -1.0],
         'maximum_ticks': [p['width']+1.0, p['height'], p['depth']+1.0]},
    ]
    for index in range(p['count']):
        x = p['end_cap']+index*p['module_pitch']+p['handle_x']
        boxes.append({'part': index+2, 'name': f'handle.{index}',
                      'minimum_ticks': [x, p['handle_y'], -0.5],
                      'maximum_ticks': [x+p['handle_width'],
                                        p['handle_y']+p['handle_height'], 0.0]})
    return boxes


def _corners(box):
    lo = box['minimum_ticks']; hi = box['maximum_ticks']
    return np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                     [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
                     [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                     [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]],
                    dtype=np.float64)


def _canvas(boxes):
    points = np.concatenate([project(_corners(box)) for box in boxes])
    minimum = np.floor(points.min(axis=0)).astype(np.int64)-3
    maximum = np.ceil(points.max(axis=0)).astype(np.int64)+3
    size = (maximum-minimum+1).tolist()
    origin = (-minimum).tolist()
    yy, xx = np.indices((size[1], size[0]), dtype=np.float64)
    u = xx-origin[0]+0.5
    v = yy-origin[1]+0.5
    eye = np.stack((-v/2.0+u/4.0-1000.0,
                    np.full_like(u, 2000.0),
                    -v/2.0-u/4.0-1000.0), axis=-1)
    return size, origin, u, v, eye


def _slab(origin, direction, box):
    """Return positive-volume interval and its entry face, without tolerance."""
    lo = np.asarray(box['minimum_ticks'], dtype=np.float64)
    hi = np.asarray(box['maximum_ticks'], dtype=np.float64)
    shape = origin.shape[:-1]
    near = np.full((*shape, 3), -np.inf, dtype=np.float64)
    far = np.full((*shape, 3), np.inf, dtype=np.float64)
    admissible = np.ones(shape, dtype=bool)
    entering_faces = np.empty(3, dtype=np.int8)
    for axis in range(3):
        d = float(direction[axis])
        entering_faces[axis] = 2*axis+(1 if d < 0.0 else 0)
        if d == 0.0:
            admissible &= ((origin[..., axis] >= lo[axis]) &
                           (origin[..., axis] <= hi[axis]))
        else:
            t0 = (lo[axis]-origin[..., axis])/d
            t1 = (hi[axis]-origin[..., axis])/d
            near[..., axis] = np.minimum(t0, t1)
            far[..., axis] = np.maximum(t0, t1)
    entry = np.max(near, axis=-1)
    exit = np.min(far, axis=-1)
    # Priority on tied entry planes is +height, front, side (axis 1, 2, 0).
    face = np.full(shape, entering_faces[0], dtype=np.int8)
    for axis in (0, 2, 1):
        face[near[..., axis] == entry] = entering_faces[axis]
    valid = admissible & (entry < exit) & (exit > 0.0)
    return entry, exit, face, valid


def _empty(size):
    shape = (size[1], size[0])
    return {'mask': np.zeros(shape, dtype=bool),
            'part': np.full(shape, -1, dtype=np.int16),
            'face': np.full(shape, -1, dtype=np.int8),
            'position': np.zeros((*shape, 3), dtype=np.float64),
            'normal': np.zeros((*shape, 3), dtype=np.float64),
            'depth': np.full(shape, np.inf, dtype=np.float64)}


def _solid(boxes, size, eye):
    result = _empty(size)
    rank = np.full(result['mask'].shape, 9, dtype=np.int8)
    # Stable geometry order handles equal-depth/equal-normal ties independently
    # of creation order or semantic part names.
    ordered = sorted(boxes, key=lambda b: tuple(b['minimum_ticks']+b['maximum_ticks']))
    for box in ordered:
        entry, _, face, valid = _slab(eye, _PRIMARY_DIRECTION, box)
        priority = _FACE_PRIORITY[face]
        take = valid & ((entry < result['depth']) |
                        ((entry == result['depth']) & (priority < rank)))
        result['depth'][take] = entry[take]
        result['part'][take] = box['part']
        result['face'][take] = face[take]
        rank[take] = priority[take]
    result['mask'] = result['part'] >= 0
    mask = result['mask']
    result['position'][mask] = eye[mask]+result['depth'][mask, None]*_PRIMARY_DIRECTION
    result['normal'][mask] = _WORLD_NORMALS[result['face'][mask]]
    return result


def _quad(box, face):
    lo = box['minimum_ticks']; hi = box['maximum_ticks']
    if face == 4:  # Front, -depth.
        return [[lo[0], hi[1], lo[2]], [hi[0], hi[1], lo[2]],
                [hi[0], lo[1], lo[2]], [lo[0], lo[1], lo[2]]]
    if face == 0:  # Near side, -width.
        return [[lo[0], hi[1], lo[2]], [lo[0], hi[1], hi[2]],
                [lo[0], lo[1], hi[2]], [lo[0], lo[1], lo[2]]]
    if face == 3:  # Top, +height.
        return [[lo[0], hi[1], lo[2]], [hi[0], hi[1], lo[2]],
                [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]]
    raise ValueError('Only camera-facing planar quads are supported')


def _planar_faces(boxes):
    body, cap = boxes[:2]
    faces = [{'part': body['part'], 'face': face, 'vertices': _quad(body, face)}
             for face in (0, 4)]
    faces += [{'part': box['part'], 'face': 4, 'vertices': _quad(box, 4)}
              for box in boxes[2:]]
    # The real cap occludes hardware/body. Top is the last visible cap surface.
    faces += [{'part': cap['part'], 'face': face, 'vertices': _quad(cap, face)}
              for face in (0, 4, 3)]
    return faces


def _planar(boxes, size, u, v):
    result = _empty(size)
    query = np.stack((u, v), axis=-1)
    faces = _planar_faces(boxes)
    for item in faces:
        q3 = np.asarray(item['vertices'], dtype=np.float64)
        q2 = project(q3)
        basis = np.column_stack((q2[1]-q2[0], q2[3]-q2[0]))
        uv = (query-q2[0])@np.linalg.inv(basis).T
        take = ((uv[..., 0] >= 0.0) & (uv[..., 0] < 1.0) &
                (uv[..., 1] >= 0.0) & (uv[..., 1] < 1.0))
        position = q3[0]+uv[..., 0, None]*(q3[1]-q3[0])+uv[..., 1, None]*(q3[3]-q3[0])
        result['part'][take] = item['part']
        result['face'][take] = item['face']
        result['position'][take] = position[take]
        result['normal'][take] = _WORLD_NORMALS[item['face']]
        result['depth'][take] = 1000.0-position[take, 1]/2.0
    result['mask'] = result['part'] >= 0
    return result, faces


def generate(profile, count, mode='solid'):
    """Produce geometry buffers; the caller owns their output directory.

    ``solid`` uses only nearest finite-box hits. ``planar`` independently uses
    affine quad interiors and a declared painter order, including handle fronts
    but no handle side/top volume. Both are native-resolution authoring methods.
    """
    if mode not in ('solid', 'planar'):
        raise ValueError('mode must be solid or planar')
    p = _profile_values(profile, count)
    boxes = _make_boxes(p)
    size, origin, u, v, eye = _canvas(boxes)
    if mode == 'solid':
        result = _solid(boxes, size, eye)
        planar_faces = []
    else:
        result, planar_faces = _planar(boxes, size, u, v)
    result['size'] = size
    result['origin'] = origin
    result['metadata'] = {
        'contract': 'NATIVE15.md', 'mode': mode, 'count': int(count),
        'width_ticks': p['width'], 'height_ticks': p['height'],
        'body_top_ticks': p['body_top'], 'depth_ticks': p['depth'],
        'boxes': boxes, 'planar_faces': planar_faces,
        'size': size, 'origin': origin,
        'projection': 'u=2*x-2*z; v=-x-z-y',
        'world': '(-z/32, x/32, y/(32*sqrt(6))) meters',
        'sample': 'screen pixel center (x-origin.x+0.5, y-origin.y+0.5)',
        'coverage': ('finite slab entry < exit; nearest entry owns surface'
                     if mode == 'solid' else 'affine UV interior: 0 <= u,v < 1; painter order'),
        'perimeter_expansion_pixels': 0,
        'face_ids': {'negative_x': 0, 'positive_x': 1, 'negative_y': 2,
                     'positive_y': 3, 'negative_z': 4, 'positive_z': 5},
        'face_tie_priority': [3, 4, 0],
        'depth': 'primary ray parameter t; eye tick y=2000; direction=(1,-2,1)',
        'camera': {'azimuth_degrees': 45, 'elevation_degrees': 30,
                   'pixels_per_meter': 64.0*math.sqrt(2.0)},
    }
    return result


def shadow(profile, count, buffers, light_world):
    """Return actual solid light occlusion, not painted contact bands or AO.

    The 1e-7 meter departure is along the unit to-light vector, orders of
    magnitude below one native tick. Tangent/zero-length slab intervals never
    count as occluders. Planar comparison explicitly has no volume shadow.
    """
    mask = np.asarray(buffers['mask'], dtype=bool)
    output = np.zeros(mask.shape, dtype=bool)
    if buffers['metadata']['mode'] == 'planar':
        return output
    boxes = _make_boxes(_profile_values(profile, count))
    direction = light_to_ticks(light_world)
    start = np.asarray(buffers['position'], dtype=np.float64)[mask]+direction*1e-7
    hidden = np.zeros(len(start), dtype=bool)
    for box in boxes:
        entry, exit, _, valid = _slab(start, direction, box)
        hidden |= valid & (np.maximum(entry, 0.0) < exit)
    output[mask] = hidden
    return output


def _mesh_obj(result):
    lines = ['# N15 editable canonical geometry; world meters; no render materials']
    if result['metadata']['mode'] == 'planar':
        for index, item in enumerate(result['metadata']['planar_faces']):
            points = to_world(item['vertices'])
            lines.append(f'o part_{item["part"]}_face_{item["face"]}')
            for point in points:
                lines.append('v '+' '.join(format(float(value), '.12g') for value in point))
            ids = np.arange(4)+index*4+1
            cross = np.cross(points[1]-points[0], points[2]-points[0])
            if np.dot(cross, _WORLD_NORMALS[item['face']]) < 0:
                ids = ids[::-1]
            lines.append('f '+' '.join(str(int(value)) for value in ids))
    else:
        face_indices = [[0, 3, 7, 4], [1, 5, 6, 2], [0, 4, 5, 1],
                        [3, 2, 6, 7], [0, 1, 2, 3], [4, 7, 6, 5]]
        for index, box in enumerate(result['metadata']['boxes']):
            points = to_world(_corners(box))
            lines.append('o '+box['name'])
            for point in points:
                lines.append('v '+' '.join(format(float(value), '.12g') for value in point))
            for face, corners in enumerate(face_indices):
                ids = np.array(corners)
                q = points[ids]
                cross = np.cross(q[1]-q[0], q[2]-q[0])
                if np.dot(cross, _WORLD_NORMALS[face]) < 0:
                    ids = ids[::-1]
                lines.append('f '+' '.join(str(int(value)) for value in ids+index*8+1))
    return '\n'.join(lines)+'\n'


def write_assets(result, outputdir, count):
    """Save only the caller-requested new output path; no Unity mutation."""
    directory = Path(outputdir)
    directory.mkdir(parents=True, exist_ok=True)
    array_keys = ('mask', 'part', 'face', 'position', 'normal', 'depth')
    np.savez_compressed(directory/f'buffers{count}.npz',
                        **{key: result[key] for key in array_keys})
    metadata = dict(result['metadata'])
    metadata['visible_pixels'] = int(np.count_nonzero(result['mask']))
    metadata['visible_faces'] = sorted(int(value) for value in
                                       np.unique(result['face'][result['mask']]))
    (directory/f'geometry{count}.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
        encoding='utf-8')
    (directory/f'model{count}.obj').write_text(_mesh_obj(result), encoding='utf-8')
    return metadata
