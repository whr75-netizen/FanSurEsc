"""Metric open crate + 18 independently sampled apples, sharing one color/depth owner.

Run: python Tools/Building35/tray-composite.py --crate-spec SPEC --apple NATIVE --output DIR
No image generation, source resizing, camera changes, or Unity mutation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from project_faces import ROOT, R, U, D, polygon_distance, project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fruit_centres(diameter=.09, floor=.015, nx=4, nz=3):
    r = diameter / 2
    lower = [[(x-(nx-1)/2) * diameter, floor + r, (z-(nz-1)/2) * diameter] for x in range(nx) for z in range(nz)]
    rise = math.sqrt(diameter ** 2 - 2 * r ** 2)
    upper = [[(x-(nx-2)/2) * diameter, floor + r + rise, (z-(nz-2)/2) * diameter] for x in range(nx-1) for z in range(nz-1)]
    points = np.asarray(lower + upper)
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    np.fill_diagonal(distances, np.inf)
    if distances.min() < diameter - 1e-9:
        raise ValueError("Fruit spheres intersect")
    return points, float(distances.min()), rise


def validate_open_crate(spec, centres, floor, ppu, crate_height, lower_count):
    if spec['ppu'] != ppu or spec.get('ground_from_source_outline', False):
        raise ValueError("Crate must use catalog PPU and fixed physical floor; no outline-driven Y shift")
    floor_found = False
    for face in spec['faces']:
        xyz = np.asarray(face['xyz'], float)
        if np.ptp(xyz[:, 1]) > 1e-8:
            continue
        height = float(xyz[0, 1])
        floor_found |= abs(height - floor) < 1e-8
        # A closed top plane would incorrectly hide the fruit inside this open tray.
        if floor + 1e-8 < height <= crate_height+1e-8:
            inside = polygon_distance(centres[:lower_count, [0, 2]], xyz[:, [0, 2]]) <= 1e-8
            if inside.any():
                raise ValueError(f"Closed crate lid/rim over fruit centre: {face['id']}; provide open rim and floor")
    if not floor_found:
        raise ValueError("Crate spec needs its actual inner floor plane at Y=.015")


def compose(crate_spec, apple_path, output, catalog_path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing to replace an existing composite: {output}")
    spec = json.loads(crate_spec.read_text(encoding='utf-8-sig'))
    catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
    metric = catalog['assets']['appletray']; ppu = catalog['nativePpu']
    w,d,h=metric['width_x'],metric['depth_z'],metric['crate_height_y']
    diameter,floor,wall=metric['composite_fruit_diameter'],metric['crate_floor_height'],metric['crate_wall_thickness']
    r=diameter/2;nx=math.floor((w-2*wall+1e-9)/diameter);nz=math.floor((d-2*wall+1e-9)/diameter)
    if min(nx,nz)<2 or not 0<floor<h or ppu!=127:
        raise ValueError("Need a valid open tray with at least2x2fruit positions at the declared common PPU")
    # The source annotation is a fixed physical template. Only named shell planes are variable.
    axes=[{-.2:-w/2,-.188:-w/2+wall,0:0,.188:w/2-wall,.2:w/2},
          {0:0,.015:floor,.1:h},
          {-.15:-d/2,-.138:-d/2+wall,0:0,.138:d/2-wall,.15:d/2}]
    for face in spec['faces']:
        for vertex in face['xyz']:
            for axis,mapping in enumerate(axes):
                key=min(mapping,key=lambda k:abs(vertex[axis]-k))
                if abs(vertex[axis]-key)>1e-7:raise ValueError("Unknown shell template coordinate; update declared vertex roles first")
                vertex[axis]=mapping[key]
    centres, minimum_distance, rise = fruit_centres(diameter, floor, nx, nz)
    if float(centres[:,1].max()+r)>metric['display_content_collision_height']:
        raise ValueError("Declared collider height does not contain the fruit; adjust the metric envelope first")
    if np.any(abs(centres[:, 0]) + r > w/2-wall+1e-9) or np.any(abs(centres[:, 2]) + r > d/2-wall+1e-9):
        raise ValueError("Fruit spheres exceed tray footprint")
    validate_open_crate(spec, centres, floor, ppu,h,nx*nz)
    source = np.asarray(Image.open(apple_path).convert('RGBA'))
    ay, ax = np.nonzero(source[..., 3] > 25)
    if not len(ax):
        raise ValueError("Apple source is empty")
    bbox = np.array([ax.min(), ay.min(), ax.max() + 1, ay.max() + 1])
    frame_side = int(max(bbox[2:] - bbox[:2]))
    frame_centre = (bbox[:2] + bbox[2:]) / 2
    frame_min = frame_centre - frame_side / 2
    output.mkdir(parents=True, exist_ok=True)
    crate_dir = output / 'crate-raster'
    crate = project(spec, crate_dir)  # Existing homography/rasterizer is reused unchanged.
    base = np.asarray(Image.open(crate_dir / 'native.png').convert('RGBA'))
    base_xyz = np.flipud(np.fromfile(crate_dir / 'positions.rgba32f', dtype='<f4').reshape(crate['height'], crate['width'], 4))
    base_origin = np.array([crate['left'] * ppu, -crate['top'] * ppu])
    if np.max(abs(base_origin - np.rint(base_origin))) > 1e-6:
        raise ValueError("Crate output has a different native grid phase")
    projected = np.column_stack([centres @ R, -centres @ U]) * ppu
    origin = np.floor(np.minimum(base_origin, (projected - r * ppu).min(0)))
    end = np.ceil(np.maximum(base_origin + [crate['width'], crate['height']], (projected + r * ppu).max(0)))
    width, height = (end - origin).astype(int)
    color = np.zeros((height, width, 4), np.uint8)
    xyz = np.zeros((height, width, 4), np.float32)
    dx, dy = np.rint(base_origin - origin).astype(int)
    color[dy:dy + crate['height'], dx:dx + crate['width']] = base
    xyz[dy:dy + crate['height'], dx:dx + crate['width']] = base_xyz
    owner = np.where(xyz[..., 3] > .5, 0, -1).astype(np.int16)
    near = np.where(xyz[..., 3] > .5, xyz[..., :3] @ D, np.inf)
    yy, xx = np.indices((height, width))
    screen = (np.stack([xx + .5, yy + .5], -1) + origin) / ppu
    records = []
    for index, centre in enumerate(centres, 1):
        sx = screen[..., 0] - centre @ R
        sy = -screen[..., 1] - centre @ U
        source_q = np.stack([sx / diameter + .5, .5 - sy / diameter], -1) * frame_side + frame_min
        ix, iy = np.floor(source_q).astype(int).transpose(2, 0, 1)
        valid = (abs(sx) <= r) & (abs(sy) <= r) & (ix >= 0) & (iy >= 0) & (ix < source.shape[1]) & (iy < source.shape[0])
        rgba = source[np.clip(iy, 0, source.shape[0] - 1), np.clip(ix, 0, source.shape[1] - 1)]
        valid &= rgba[..., 3] > 25
        radial2 = sx * sx + sy * sy
        front = np.sqrt(np.maximum(0, r * r - radial2))
        positions = centre + sx[..., None] * R + sy[..., None] * U - front[..., None] * D
        depth = positions @ D
        write = valid & (depth < near - 1e-7)
        color[write] = rgba[write]; color[write, 3] = 255
        xyz[write, :3] = positions[write]; xyz[write, 3] = 1
        near[write] = depth[write]; owner[write] = index
        extension = valid & (radial2 > r * r)
        records.append({'id': index, 'centre_xyz': centre.tolist(), 'sampled_opaque_pixels': int(valid.sum()),
                        'equator_plane_extension_pixels': int(extension.sum()),
                        'maximum_extension_m': float(np.maximum(0, np.sqrt(radial2[valid]) - r).max()) if valid.any() else 0.0})
    for record in records:
        record['visible_pixels_after_all_occlusion'] = int((owner == record['id']).sum())
    if not np.array_equal(color[..., 3] > 25, xyz[..., 3] > .5):
        raise ValueError("Composite color/depth ownership mismatch")
    Image.fromarray(color).save(output / 'native.png')
    np.flipud(xyz).astype('<f4').tofile(output / 'positions.rgba32f')
    Image.fromarray((owner + 1).astype(np.uint8)).save(output / 'owner-id.png')
    occupied = xyz[xyz[..., 3] > .5, :3]
    receipt = {'id': 'appletray_composite', 'width': int(width), 'height': int(height), 'ppu': ppu,
        'left': float(origin[0] / ppu), 'top': float(-origin[1] / ppu), 'support_height': 0.0,
        'crate_spec': str(crate_spec), 'crate_spec_sha256': digest(crate_spec), 'crate_raster_receipt': str(crate_dir / 'receipt.json'),
        'apple_source': str(apple_path), 'apple_source_sha256': digest(apple_path), 'apple_source_bbox_xyxy': bbox.tolist(),
        'apple_source_square_frame_min_xy': frame_min.tolist(), 'apple_source_square_frame_size': frame_side,
        'catalog': str(catalog_path), 'catalog_sha256': digest(catalog_path),
        'crate_dimensions_xyz_m': [w,h,d], 'collider_size_xyz_m': [w,metric['display_content_collision_height'],d],
        'packing_columns_rows':[nx,nz],
        'fruit_diameter_m': diameter, 'fruit_frame_diameter_native_px': diameter * ppu, 'fruit_count': len(centres),
        'minimum_fruit_centre_distance_m': minimum_distance, 'second_layer_rise_m': rise,
        'fruit_sphere_top_y_m': float(centres[:, 1].max() + r), 'fruit_records': records,
        'surface_xyz_min': occupied.min(0).tolist(), 'surface_xyz_max': occupied.max(0).tolist(),
        'occlusion_rule': 'minimum dot(surfaceXYZ,D); selected surface owns color, alpha and XYZ together',
        'extension_rule': 'Opaque pixels outside the sphere disc use its centre-depth equator plane; no source-alpha clipping by circle. These are fixed-view leaf/stem details, not sphere geometry.',
        'limitations': ['Square frame includes stem/leaf: it bounds the 9cm sphere projection but does not segment measured fruit flesh diameter.',
                       'Native output resamples at physical 127 PPU; nearest colors do not guarantee all source texels or subpixel details survive.',
                       'No source relighting, hidden-view reconstruction, Unity validation or artistic acceptance is claimed.']}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    (output.parent / 'production-manifest.json').write_text(json.dumps({'assets': [{'id': receipt['id'], 'folder': str(output), 'receipt': str(output / 'receipt.json')}]}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'id': receipt['id'], 'size': [int(width), int(height)], 'fruit_count': len(centres), 'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--crate-spec', type=Path, required=True)
    parser.add_argument('--apple', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'Tools/Building35/metric-catalog.json')
    args = parser.parse_args()
    compose(args.crate_spec, args.apple, args.output, args.catalog)
