"""N16 metre-space semantic solids at native pixel centres.

The geometry stage exclusively owns alpha. Materials, source patterns and light
are authored downstream. Smooth primitive tessellation is only the shadow mesh;
it is never used to create internal raster strokes.
"""
from __future__ import annotations

import math
import json
from pathlib import Path
import numpy as np

R = np.array([1.0, 0.0, -1.0]) / math.sqrt(2.0)
U = np.array([1.0 / math.sqrt(8.0), math.sqrt(3.0) / 2.0,
              1.0 / math.sqrt(8.0)])
F = np.cross(R, U)
DEFAULT_PPU = float(json.loads((Path(__file__).resolve().parent/'shading17.json').read_text(encoding='utf-8'))['ppu'])
MATERIALS = {1: 'wood', 2: 'navy', 3: 'brass', 4: 'paper', 5: 'leaf',
             6: 'apple', 7: 'glass', 8: 'ceramic', 9: 'metal', 10: 'fabric'}


def _rotation(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, 0., s], [0., 1., 0.], [-s, 0., c]])


class Parts:
    def __init__(self):
        self.items = []
        self.seams = []
        self.design = None

    def add(self, kind, name, material, **values):
        if material not in MATERIALS:
            raise ValueError('Unknown material role')
        item = dict(kind=kind, name=name, material=material,
                    part=len(self.items), **values)
        self.items.append(item)
        return item

    def box(self, name, lo, hi, material):
        lo, hi = np.array(lo, float), np.array(hi, float)
        if not np.isfinite([lo, hi]).all() or np.any(hi <= lo):
            raise ValueError('Finite positive box dimensions required: ' + name)
        return self.add('box', name, material, lo=lo, hi=hi)

    def ellipsoid(self, name, center, radii, material, angle=0.):
        radii = np.array(radii, float)
        if np.any(radii <= 0):
            raise ValueError('Positive ellipsoid radii required')
        return self.add('ellipsoid', name, material, center=np.array(center, float),
                        radii=radii, rotation=_rotation(angle))

    def cylinder(self, name, center, radius_bottom, radius_top, height,
                 material, axis=1):
        if min(radius_bottom, radius_top, height) <= 0 or axis not in (0, 1, 2):
            raise ValueError('Finite positive cylinder required')
        return self.add('cylinder', name, material, center=np.array(center, float),
                        rb=float(radius_bottom), rt=float(radius_top),
                        height=float(height), axis=axis)

    def wedge(self, name, lo, hi, front_height, material):
        lo, hi = np.array(lo, float), np.array(hi, float)
        # Front is -Z. This closed console slopes from front low to rear high.
        vertices = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                             [hi[0], front_height, lo[2]], [lo[0], front_height, lo[2]],
                             [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                             [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]])
        quads = [[0, 3, 7, 4], [1, 5, 6, 2], [0, 4, 5, 1],
                 [3, 2, 6, 7], [0, 1, 2, 3], [4, 7, 6, 5]]
        triangles, charts = [], []
        for face, q in enumerate(quads):
            triangles.extend([q[:3], [q[0], q[2], q[3]]])
            charts.extend([face, face])
        triangles = _outward(vertices, np.array(triangles), vertices.mean(0))
        return self.add('mesh', name, material, vertices=vertices,
                        triangles=triangles, charts=np.array(charts))


def _outward(vertices, triangles, center):
    triangles = triangles.copy()
    q = vertices[triangles]
    reverse = np.sum(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]) *
                     (q.mean(1)-center), axis=1) < 0
    triangles[reverse] = triangles[reverse][:, [0, 2, 1]]
    return triangles


def _cabinet(parts, w, h, d, kind):
    # Use the approved N15 definition, not a second approximate door/handle
    # design. Its complete envelope is adapted to the existing physical bounds.
    recipe_path = Path(__file__).resolve().parents[1]/'PerfectPixelUniform/native15_recipe.json'
    profile = json.loads(recipe_path.read_text(encoding='utf-8'))['profile'].copy()
    count = {'empty_counter': 3, 'island_body_template': 2,
             'utility_bench': 2, 'cleaning_cabinet': 1}[kind]
    width = 2*profile['end_cap']+count*profile['module_pitch']
    scale = np.array([w/(width+2), h/profile['height'], d/(profile['depth']+2)])
    offset = np.array([-w/2+scale[0], 0., -d/2+scale[2]])
    convert = lambda point: np.asarray(point, float)*scale+offset
    bodytop = profile['height']-profile['cap_thickness']
    parts.box('painted body', convert([0, 0, 0]),
              convert([width, bodytop, profile['depth']]), 2)
    parts.box('continuous oak top', convert([-1, bodytop, -1]),
              convert([width+1, profile['height'], profile['depth']+1]), 1)
    for i in range(count):
        start = profile['end_cap']+i*profile['module_pitch']
        x = start+profile['handle_x']; y = profile['handle_y']
        parts.box('door handle '+str(i), convert([x, y, -.5]),
                  convert([x+profile['handle_width'], y+profile['handle_height'], 0]), 3)
    parts.seams.append(dict(kind='door', pitch=profile['module_pitch']*scale[0],
                            start=offset[0]+profile['end_cap']*scale[0], count=count,
                            y0=6*scale[1], y1=66*scale[1], z=offset[2]))
    parts.design = {'source': 'Tools/PerfectPixelUniform/native15_recipe.json',
                    'profile': profile, 'count': count, 'width_ticks': width,
                    'tick_scale_xyz': scale.tolist(), 'tick_offset_xyz': offset.tolist(),
                    'adaptation': 'whole N15 envelope to preserved physical bounds'}


def _goods(parts, w, h, d, stock=False, refrigerated=False):
    back = d*.23
    levels = 3
    thickness = min(.043, h*.027)
    for level in range(levels):
        shelf_y = .10+level*(h-.20)/levels
        parts.box('oak shelf '+str(level), [-w/2+.04, shelf_y, -d/2+.025],
                  [w/2-.04, shelf_y+thickness, d/2-back], 1)
        columns = max(3, int(round(w/.28)))
        stride = (w-.14)/columns
        for i in range(columns):
            x = -w/2+.07+(i+.5)*stride
            z = -d*.04
            base = shelf_y+thickness
            radius = min(.054, stride*.25, d*.12)
            if stock and (i+level) % 3 != 0:
                width = min(stride*.79, .24)
                height = min((h-.2)/levels*.59, .25)
                parts.box('stock carton', [x-width/2, base, z-d*.19],
                          [x+width/2, base+height, z+d*.19], 4)
                parts.box('carton label', [x-width*.30, base+height*.30, z-d*.19],
                          [x+width*.30, base+height*.68, z-d*.19+.005], 1)
            elif (i+level) % 4 == 0 and not refrigerated:
                height = min(.29, (h-.2)/levels*.65)
                parts.ellipsoid('cloth grain sack', [x, base+height/2, z],
                                [radius*1.45, height/2, radius*1.25], 10)
            else:
                bh = min(.24+(i%3)*.03, (h-.2)/levels*.70)
                color = 5 if (i+level)%3 == 0 else (6 if (i+level)%3 == 1 else 8)
                parts.cylinder('jar or bottle body', [x, base+bh*.42, z],
                               radius, radius, bh*.84, color)
                parts.cylinder('jar neck', [x, base+bh*.91, z],
                               radius*.55, radius*.55, bh*.14, color)
                parts.cylinder('brass jar lid', [x, base+bh*.985, z],
                               radius*.58, radius*.58, bh*.03, 3)
                parts.box('paper goods label', [x-radius*.65, base+bh*.27, z-radius],
                          [x+radius*.65, base+bh*.58, z-radius+.008], 4)


def _shelf(parts, w, h, d, kind):
    t = min(.048, d*.15)
    parts.box('painted back', [-w/2, 0, d/2-t], [w/2, h-.05, d/2], 2)
    for x in (-w/2, w/2-t):
        parts.box('side upright', [x, 0, -d/2], [x+t, h, d/2], 2)
    parts.box('oak top', [-w/2, h-.05, -d/2], [w/2, h, d/2], 1)
    parts.box('bottom plinth', [-w/2, 0, -d/2], [w/2, .10, d/2], 2)
    _goods(parts, w, h-.06, d, stock=kind == 'stock_shelf')


def _fridge(parts, w, h, d):
    t = .06
    parts.box('rear cooler body', [-w/2, 0, d/2-.09], [w/2, h, d/2], 2)
    for x in (-w/2, w/2-t, -t/2):
        parts.box('door frame upright', [x, 0, -d/2], [x+t, h, d/2], 2)
    parts.box('roof casing', [-w/2, h-.08, -d/2], [w/2, h, d/2], 2)
    parts.box('vent base', [-w/2, 0, -d/2], [w/2, .14, d/2], 9)
    for x in (-.095, .095):
        parts.box('door pull', [x-.012, h*.36, -d/2],
                  [x+.012, h*.63, -d/2+.035], 3)
    # Transparent glass is a semantic overlay. Opaque contents own depth.
    _goods(parts, w-.09, h-.10, d-.06, refrigerated=True)


def _register(parts, w, h, d):
    parts.box('cash drawer', [-w/2, 0, -d/2], [w/2, h*.25, d/2], 2)
    parts.wedge('sloping console', [-w*.46, h*.25, -d*.40],
                [w*.46, h*.83, d*.42], h*.43, 3)
    parts.box('raised rear display', [-w*.26, h*.78, d*.22],
              [w*.26, h, d*.40], 2)
    # Each row follows the same console slope; keys stay inside the envelope.
    for row in range(3):
        z = -d*.26+row*d*.14
        y = h*.43+(z+d*.40)/(d*.82)*(h*.40)
        for col in range(5):
            x = (col-2)*w*.13
            parts.ellipsoid('register key', [x, y+.008, z],
                            [w*.040, min(.008,h*.018), d*.044], 4)


def _crate(parts, w, h, d, shallow=False):
    t = min(.018, min(w,d)*.06)
    parts.box('wood crate floor', [-w/2, 0, -d/2], [w/2, t, d/2], 1)
    plank_h = (h-t)/2*.80
    for row in range(2):
        y = t+row*(h-t)/2
        for z in (-d/2, d/2-t):
            parts.box('front back plank', [-w/2, y, z], [w/2, y+plank_h, z+t], 1)
        for x in (-w/2, w/2-t):
            parts.box('side plank', [x, y, -d/2+t], [x+t, y+plank_h, d/2-t], 1)
    for x in (-w/2, w/2-t):
        for z in (-d/2, d/2-t):
            parts.box('crate corner post', [x, 0, z], [x+t, h, z+t], 1)


def _tray(parts, w, h, d):
    ch = min(.10, h*.5)
    _crate(parts, w, ch, d, shallow=True)
    radius = .045
    nx = max(1, int((w-.024)//.09))
    nz = max(1, int((d-.024)//.09))
    for iz in range(nz):
        for ix in range(nx):
            x = (ix-(nx-1)/2)*.09
            z = (iz-(nz-1)/2)*.09
            parts.ellipsoid('ninety millimetre apple', [x, .018+radius, z],
                            [radius, radius*.93, radius], 6)
            parts.cylinder('apple stem', [x, .018+radius*1.97, z],
                           .004, .003, .014, 1)
    second_y = min(h-radius, .018+radius+math.sqrt(.09**2-2*.045**2))
    for iz in range(max(0,nz-1)):
        for ix in range(max(0,nx-1)):
            x = (ix-(nx-2)/2)*.09
            z = (iz-(nz-2)/2)*.09
            parts.ellipsoid('upper apple', [x, second_y, z],
                            [radius, radius*.93, radius], 6)


def _plant(parts, w, h, d):
    ph = h*.27
    pr = min(w,d)*.24
    parts.cylinder('ceramic plant pot', [0, ph/2, 0], pr*.73, pr, ph, 8)
    parts.cylinder('soil', [0, ph-.009, 0], pr*.91, pr*.91, .018, 1)
    parts.cylinder('pot lip', [0, ph-.014, 0], pr*1.04, pr*1.04, .028, 3)
    parts.cylinder('main stem', [0, (ph+h*.9)/2, 0], .016, .009, h*.9-ph, 5)
    for layer in range(4):
        yy = ph+(h-ph)*(.17+layer*.21)
        reach = min(w,d)*(.30-layer*.045)
        length = min(w,d)*(.20-layer*.026)
        breadth = min(w,d)*(.10-layer*.011)
        for leaf in range(4):
            angle = leaf*math.pi/2
            center = [math.cos(angle)*reach, yy, -math.sin(angle)*reach]
            parts.ellipsoid('leaf cluster', center,
                            [length, h*.085, breadth], 5, angle)
    parts.ellipsoid('top new leaf', [0,h*.94,0], [w*.105,h*.06,d*.08], 5)


def _barrel(parts,w,h,d,bin_object=False):
    radius = min(w,d)/2
    if bin_object:
        parts.cylinder('metal bin body',[0,h*.47,0],radius*.89,radius*.96,h*.94,2)
        parts.cylinder('bin lid',[0,h*.97,0],radius,radius,h*.06,9)
        parts.box('pedal',[-w*.13,0,-d/2],[w*.13,h*.08,-d*.33],3)
    else:
        # Two matched frusta form the bulged wooden body.
        parts.cylinder('lower oak barrel',[0,h*.25,0],radius*.83,radius,h*.5,1)
        parts.cylinder('upper oak barrel',[0,h*.75,0],radius,radius*.83,h*.5,1)
        for y in (.08,.26,.73,.93):
            ry = radius*(.83+.17*(1-abs(y-.5)*2))
            parts.cylinder('iron hoop',[0,h*y,0],ry,ry,h*.055,2)
        parts.cylinder('barrel top',[0,h*.985,0],radius*.81,radius*.81,h*.03,1)


def _details(parts, w, h, d, kind):
    if kind == 'detail_ledger':
        parts.box('book pages',[-w*.49,h*.20,-d*.49],[w*.49,h*.80,d*.49],4)
        for y in (0,h*.80):
            parts.box('ledger cover',[-w/2,y,-d/2],[w/2,y+h*.20,d/2],1)
        parts.box('book spine',[-w*.02,0,-d/2],[w*.02,h,d/2],3)
        parts.seams.append(dict(kind='book_spine',x=0))
    elif kind == 'detail_clock':
        radius = min(w,h)/2
        parts.cylinder('clock frame',[0,h/2,d*.10],radius,radius,d*.80,3,axis=2)
        parts.cylinder('ivory clock face',[0,h/2,-d*.33],w*.43,w*.43,d*.20,4,axis=2)
        for index in range(12):
            angle = index*math.tau/12
            x, y = math.sin(angle)*w*.36,h/2+math.cos(angle)*w*.36
            parts.box('hour marker',[x-.006,y-.006,-d/2],
                      [x+.006,y+.006,-d*.45],2)
        parts.box('minute hand',[-.005,h*.50,-d/2],[.005,h*.81,-d*.43],2)
        parts.box('hour hand',[-w*.21,h*.48,-d/2],[.005,h*.52,-d*.43],2)
    elif kind == 'detail_poster':
        # Width/depth swap happened once through the front-axis transform.
        t = min(.025,w*.075)
        parts.box('paper botanical artwork',[-w/2,0,0],[w/2,h,d/2],4)
        for x in (-w/2,w/2-t):
            parts.box('vertical oak picture frame',[x,0,-d/2],[x+t,h,0],1)
        for y in (0,h-t):
            parts.box('horizontal oak picture frame',[-w/2,y,-d/2],[w/2,y+t,0],1)
        parts.box('botanical stem',[-.005,h*.18,-d*.05],[.005,h*.82,0],5)
        for index in range(5):
            yy=h*(.28+index*.10)
            side=-1 if index%2 else 1
            parts.ellipsoid('botanical printed leaf',[side*w*.075,yy,-d*.04],
                            [w*.11,h*.04,d*.018],5)
    elif kind == 'detail_broom':
        # The declared 40mm thickness bounds the shaft. A 20mm shaft had no
        # pixel-centre hits at this grid phase; the reference thickness is kept.
        shaft_radius = min(w*.15,d*.45)
        parts.cylinder('broom shaft',[0,h*.59,0],shaft_radius,
                       shaft_radius*.90,h*.82,1)
        parts.wedge('bound broom bristles',[-w/2,0,-d/2],[w/2,h*.20,d/2],h*.20,10)
        parts.box('broom binding',[-w/2,h*.155,-d*.33],[w/2,h*.185,d*.33],3)
    else:
        raise ValueError('No detail template: '+kind)


def _parts(asset):
    name = asset['id']
    dimensions = np.asarray(asset['size_xyz_m'],float)
    if dimensions.shape != (3,) or not np.isfinite(dimensions).all() or np.any(dimensions <= 0):
        raise ValueError('Three finite positive metre dimensions required')
    facing = asset.get('front_axis',asset.get('facing')) or '-Z'
    if facing not in ('-Z','+Z','-X','+X'):
        raise ValueError('Unsupported front axis '+str(facing))
    angle = {'-Z':0.,'-X':math.pi/2,'+Z':math.pi,'+X':-math.pi/2}[facing]
    if facing in ('-X','+X'):
        w,h,d = dimensions[[2,1,0]]
    else:
        w,h,d = dimensions
    p=Parts()
    if name in ('empty_counter','island_body_template','utility_bench','cleaning_cabinet'):
        _cabinet(p,w,h,d,name)
    elif name in ('left_shelf','rear_shelf','stock_shelf'):
        _shelf(p,w,h,d,name)
    elif name=='fridge': _fridge(p,w,h,d)
    elif name=='register': _register(p,w,h,d)
    elif name=='appletray': _tray(p,w,h,d)
    elif name=='plant': _plant(p,w,h,d)
    elif name=='crate': _crate(p,w,h,d)
    elif name=='barrel': _barrel(p,w,h,d)
    elif name=='detail_bin': _barrel(p,w,h,d,True)
    else: _details(p,w,h,d,name)
    return p, _rotation(angle), dimensions, facing


def _box_hit(item, origin, direction):
    n=len(origin); near=np.full((n,3),-np.inf); far=np.full((n,3),np.inf)
    valid=np.ones(n,bool); faces=np.empty(3,int)
    for axis in range(3):
        di=direction[axis];faces[axis]=axis*2+(1 if di<0 else 0)
        if abs(di)<1e-15:
            valid &= (origin[:,axis]>=item['lo'][axis])&(origin[:,axis]<=item['hi'][axis])
        else:
            a=(item['lo'][axis]-origin[:,axis])/di
            b=(item['hi'][axis]-origin[:,axis])/di
            near[:,axis]=np.minimum(a,b);far[:,axis]=np.maximum(a,b)
    entry=near.max(1);exit=far.min(1)
    chart=np.zeros(n,int)
    for axis in (0,2,1):chart[near[:,axis]==entry]=faces[axis]
    valid &= (entry<exit)&(exit>0)&(entry>=0)
    normal=np.zeros((n,3));axis=chart//2
    normal[np.arange(n),axis]=np.where(chart%2,1.,-1.)
    return np.where(valid,entry,np.inf),normal,chart


def _ellipsoid_hit(item,origin,direction):
    rot=item['rotation'];o=(origin-item['center'])@rot
    dr=direction@rot;scaled=o/item['radii'];vd=dr/item['radii']
    a=float(vd@vd);b=2*(scaled@vd);c=np.sum(scaled*scaled,1)-1
    disc=b*b-4*a*c;positive=disc>0
    root=np.sqrt(np.maximum(disc,0));t=(-b-root)/(2*a)
    exit=(-b+root)/(2*a);t=np.where(t>=0,t,exit)
    valid=positive&(t>=0)
    point=o+t[:,None]*dr
    normal=point/(item['radii']**2)
    length=np.linalg.norm(normal,axis=1)
    normal/=np.maximum(length,1e-30)[:,None];normal=normal@rot.T
    return np.where(valid,t,np.inf),normal,np.zeros(len(origin),int)


def _cylinder_hit(item,origin,direction):
    axis=item['axis'];radial=[i for i in range(3) if i!=axis]
    o=origin-item['center'];half=item['height']/2
    slope=(item['rt']-item['rb'])/item['height'];mid=(item['rt']+item['rb'])/2
    ar=float(sum(direction[j]**2 for j in radial)-(slope*direction[axis])**2)
    br=2*(sum(o[:,j]*direction[j] for j in radial)-
          (mid+slope*o[:,axis])*slope*direction[axis])
    cr=sum(o[:,j]**2 for j in radial)-(mid+slope*o[:,axis])**2
    discriminant=br*br-4*ar*cr
    side_valid=discriminant>0
    if abs(ar)<1e-15:
        roots=[-cr/np.where(abs(br)>1e-15,br,np.inf)]
    else:
        rt=np.sqrt(np.maximum(discriminant,0));roots=[(-br-rt)/(2*ar),(-br+rt)/(2*ar)]
    t=np.full(len(o),np.inf);normal=np.zeros_like(o);chart=np.zeros(len(o),int)
    for candidate in roots:
        yy=o[:,axis]+candidate*direction[axis]
        hit=side_valid&(candidate>=0)&(yy>=-half)&(yy<=half)&(candidate<t)
        point=o+candidate[:,None]*direction
        nn=np.zeros_like(o)
        for j in radial:nn[:,j]=point[:,j]
        nn[:,axis]=-slope*(mid+slope*yy)
        nn/=np.maximum(np.linalg.norm(nn,axis=1),1e-30)[:,None]
        t[hit]=candidate[hit];normal[hit]=nn[hit];chart[hit]=0
    if abs(direction[axis])>1e-15:
        for yy,radius,sign,label in [(-half,item['rb'],-1.,1),(half,item['rt'],1.,2)]:
            candidate=(yy-o[:,axis])/direction[axis]
            point=o+candidate[:,None]*direction
            rr=sum(point[:,j]**2 for j in radial)
            hit=(candidate>=0)&(rr<radius*radius)&(candidate<t)
            t[hit]=candidate[hit];normal[hit]=0;normal[hit,axis]=sign;chart[hit]=label
    return t,normal,chart


def _mesh_hit(item,origin,direction):
    depth=np.full(len(origin),np.inf);normal=np.zeros_like(origin);chart=np.zeros(len(origin),int)
    for triangle,chart_id in zip(item['triangles'],item['charts']):
        a,b,c=item['vertices'][triangle];e1=b-a;e2=c-a
        pv=np.cross(direction,e2);det=e1@pv
        if abs(det)<1e-14:continue
        tv=origin-a;u=(tv@pv)/det;qv=np.cross(tv,e1)
        v=(qv@direction)/det;t=(qv@e2)/det
        hit=(u>=0)&(v>=0)&(u+v<=1)&(t>=0)&(t<depth)
        nn=np.cross(e1,e2);nn/=np.linalg.norm(nn)
        depth[hit]=t[hit];normal[hit]=nn;chart[hit]=chart_id
    return depth,normal,chart


def _primitive_mesh(item):
    kind=item['kind']
    if kind=='mesh':return item['vertices'],item['triangles']
    if kind=='box':
        lo,hi=item['lo'],item['hi']
        v=np.array([[lo[0],lo[1],lo[2]],[hi[0],lo[1],lo[2]],
                    [hi[0],hi[1],lo[2]],[lo[0],hi[1],lo[2]],
                    [lo[0],lo[1],hi[2]],[hi[0],lo[1],hi[2]],
                    [hi[0],hi[1],hi[2]],[lo[0],hi[1],hi[2]]])
        q=[[0,3,7,4],[1,5,6,2],[0,4,5,1],[3,2,6,7],[0,1,2,3],[4,7,6,5]]
        t=np.array([tri for ids in q for tri in [ids[:3],[ids[0],ids[2],ids[3]]]])
        return v,_outward(v,t,v.mean(0))
    slices=16
    if kind=='ellipsoid':
        # One vertex at each pole, interior latitude rings; no zero-area faces.
        rings=8;v=[[0.,-1.,0.]]
        for j in range(1,rings):
            latitude=-math.pi/2+j*math.pi/rings
            for i in range(slices):
                longitude=i*math.tau/slices
                v.append([math.cos(latitude)*math.cos(longitude),math.sin(latitude),
                          math.cos(latitude)*math.sin(longitude)])
        v.append([0.,1.,0.]);t=[]
        for i in range(slices):t.append([0,1+i,1+(i+1)%slices])
        for ring in range(rings-2):
            start=1+ring*slices;other=start+slices
            for i in range(slices):
                nxt=(i+1)%slices;t.extend([[start+i,other+i,other+nxt],
                                          [start+i,other+nxt,start+nxt]])
        top=len(v)-1;start=1+(rings-2)*slices
        for i in range(slices):t.append([top,start+(i+1)%slices,start+i])
        v=np.asarray(v)*item['radii'];v=v@item['rotation'].T+item['center']
        return v,_outward(v,np.asarray(t),item['center'])
    axis=item['axis'];radial=[i for i in range(3) if i!=axis]
    v=[]
    for yy,radius in [(-item['height']/2,item['rb']),(item['height']/2,item['rt'])]:
        for i in range(slices):
            q=np.zeros(3);angle=i*math.tau/slices;q[axis]=yy
            q[radial[0]]=radius*math.cos(angle);q[radial[1]]=radius*math.sin(angle)
            v.append(q+item['center'])
    for yy in (-item['height']/2,item['height']/2):
        q=item['center'].copy();q[axis]+=yy;v.append(q)
    t=[]
    for i in range(slices):
        nxt=(i+1)%slices
        t.extend([[i,nxt,slices+nxt],[i,slices+nxt,slices+i],
                  [2*slices,nxt,i],[2*slices+1,slices+i,slices+nxt]])
    v=np.asarray(v)
    return v,_outward(v,np.asarray(t),item['center'])


def _primitive_bounds(item):
    if item['kind']=='box':return item['lo'],item['hi']
    if item['kind']=='mesh':return item['vertices'].min(0),item['vertices'].max(0)
    if item['kind']=='ellipsoid':
        extent=np.sqrt((item['rotation']**2)@(item['radii']**2))
    else:
        extent=np.full(3,max(item['rb'],item['rt']))
        extent[item['axis']]=item['height']/2
    return item['center']-extent,item['center']+extent


def _edge_roles(result, parts, rotation):
    mask=result['mask'];p=result['part'];chart=result['chart'];normal=result['normal']
    roles=np.zeros(mask.shape,np.uint8)
    # One owner on each *actual* visible crease, not every mesh triangle.
    for axis in (0,1):
        a=(slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
        b=(slice(1,None),slice(None)) if axis==0 else (slice(None),slice(1,None))
        valid=mask[a]&mask[b]
        dot=np.sum(normal[a]*normal[b],axis=-1)
        boundary=((p[a]!=p[b])|(chart[a]!=chart[b]))&valid
        crease=boundary&(dot<.985)
        if parts.design is not None:
            # N15 cap/body contact is conveyed by materials and real shadow,
            # not an extra dark line below the oak top.
            contact=((p[a]==0)&(p[b]==1))|((p[a]==1)&(p[b]==0))
            crease &= ~contact
        # Stable camera-facing owner. Same-normal contacting boxes get no line.
        score_a=normal[a]@(-F);score_b=normal[b]@(-F)
        owner_a=score_a>=score_b
        ra=roles[a];rb=roles[b]
        ra[crease&owner_a]=3;rb[crease&~owner_a]=3
    # The outer silhouette is inside coverage; it adds no occupied pixels.
    padded=np.pad(mask,1)
    interior=(padded[:-2,1:-1]&padded[2:,1:-1]&
              padded[1:-1,:-2]&padded[1:-1,2:])
    silhouette=mask&~interior
    local=result['position']@rotation
    local_n=result['normal']@rotation
    for seam in parts.seams:
        if seam['kind']!='door':continue
        front=mask&(local_n[...,2]<-.99)&(np.abs(local[...,2]-seam['z'])<1e-5)
        active=front&(local[...,1]>=seam['y0'])&(local[...,1]<seam['y1'])
        labels=np.floor((local[...,0]-seam['start'])/seam['pitch']).astype(int)
        for axis in (0,1):
            a=(slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
            b=(slice(1,None),slice(None)) if axis==0 else (slice(None),slice(None,-1))
            if axis==1:b=(slice(None),slice(1,None))
            boundary=active[a]&active[b]&(labels[a]!=labels[b])
            owner_a=labels[a]<labels[b]
            ra=roles[a];rb=roles[b]
            ra[boundary&owner_a]=2;rb[boundary&~owner_a]=2
    roles[silhouette]=1
    return roles


def _build(name,parts,rotation,dimensions,ppu,facing='-Z',declared_bounds=None):
    if not math.isfinite(float(ppu)) or ppu<=0:raise ValueError('Finite positive PPU required')
    lows=[];highs=[];vertices=[];triangles=[];offset=0
    for item in parts.items:
        lo,hi=_primitive_bounds(item)
        corners=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])@rotation.T
        lows.append(corners.min(0));highs.append(corners.max(0))
        v,t=_primitive_mesh(item);vertices.append(v@rotation.T);triangles.append(t+offset);offset+=len(v)
    actual_lo=np.min(lows,0);actual_hi=np.max(highs,0)
    expected_lo=np.array([-dimensions[0]/2,0.,-dimensions[2]/2])
    expected_hi=np.array([dimensions[0]/2,dimensions[1],dimensions[2]/2])
    if declared_bounds is not None:
        expected_lo,expected_hi=np.asarray(declared_bounds,float)
    if np.any(actual_lo<expected_lo-1e-8) or np.any(actual_hi>expected_hi+1e-8):
        raise ValueError('SEMANTIC_PART_OUTSIDE_DECLARED_BOUNDS '+name+': '+
                         repr([actual_lo.tolist(),actual_hi.tolist(),expected_lo.tolist(),expected_hi.tolist()]))
    corners=np.array([[x,y,z] for x in (actual_lo[0],actual_hi[0]) for y in (actual_lo[1],actual_hi[1]) for z in (actual_lo[2],actual_hi[2])])
    projected=np.column_stack((corners@R,-corners@U))*ppu
    origin=np.floor(projected.min(0)).astype(int)-2
    maximum=np.ceil(projected.max(0)).astype(int)+2
    size=maximum-origin+1
    yy,xx=np.indices((size[1],size[0]));u=xx+origin[0]+.5;v=yy+origin[1]+.5
    screen=(u[...,None]*R-v[...,None]*U)/ppu
    world_o=(screen-F*100.).reshape(-1,3)
    o=world_o@rotation;direction=F@rotation
    depth=np.full(len(o),np.inf);part=np.full(len(o),-1,np.int32)
    material=np.zeros(len(o),np.uint8);chart=np.full(len(o),-1,np.int16)
    normals=np.zeros_like(o)
    dispatch={'box':_box_hit,'ellipsoid':_ellipsoid_hit,
              'cylinder':_cylinder_hit,'mesh':_mesh_hit}
    for item in parts.items:
        hit,nn,cc=dispatch[item['kind']](item,o,direction)
        take=hit<depth
        depth[take]=hit[take];part[take]=item['part'];material[take]=item['material']
        chart[take]=cc[take];normals[take]=nn[take]
    mask=np.isfinite(depth);position=np.zeros_like(o)
    position[mask]=world_o[mask]+depth[mask,None]*F
    normals=normals@rotation.T
    shape=(int(size[1]),int(size[0]))
    result={'mask':mask.reshape(shape),'position':position.astype(np.float32).reshape(*shape,3),
            'normal':normals.astype(np.float32).reshape(*shape,3),
            'part':part.reshape(shape),'material':material.reshape(shape),
            'chart':chart.reshape(shape),'depth':depth.reshape(shape),
            'origin':origin.tolist(),'size':size.tolist(),
            'bounds':[actual_lo.tolist(),actual_hi.tolist()],
            'mesh_vertices':np.concatenate(vertices).astype(np.float32),
            'mesh_triangles':np.concatenate(triangles).astype(np.int32)}
    result['edge']=_edge_roles(result,parts,rotation)
    metadata={'id':name,'units':'Unity local XYZ metres, Y-up',
              'pixels_per_metre':float(ppu),'front_axis':facing,
              'declared_dimensions_m':dimensions.tolist(),
              'bounds':result['bounds'],'origin_projected_px':origin.tolist(),
              'size':size.tolist(),'parts':[{'id':i['part'],'name':i['name'],
                 'shape':i['kind'],'material':i['material'],
                 'bounds_canonical_m':[x.tolist() for x in _primitive_bounds(i)]}
                for i in parts.items],
              'seams':parts.seams,'R':R.tolist(),'U':U.tolist(),'F':F.tolist(),
              'coverage':'native pixel centre nearest positive finite solid hit',
              'perimeter_expansion_pixels':0,
              'normal_space':'Unity local XYZ metres',
              'shadow_mesh':'closed 16-segment/8-ring approximation of the same analytic solids',
              'glass_policy':'fridge glazing is overlay only; opaque frame and goods own primary depth',
              'hidden_surface_policy':'explicit semantic template, not inferred source recovery'}
    result['metadata']=metadata
    if parts.design is not None:
        design = dict(parts.design, rotation=rotation.tolist())
        metadata['cabinet_design'] = design
        local = result['position']@rotation
        result['design_tick'] = ((local-np.asarray(design['tick_offset_xyz']))/
                                 np.asarray(design['tick_scale_xyz'])).astype(np.float32)
        result['design_normal'] = (result['normal']@rotation).astype(np.float32)
    return result


def build_asset(asset:dict,ppu=DEFAULT_PPU):
    """Build one of the eighteen B37 semantic templates; no source resampling."""
    parts,rotation,dimensions,facing=_parts(asset)
    return _build(asset['id'],parts,rotation,dimensions,ppu,facing)


def build_box(name,bounds,ppu=DEFAULT_PPU,material=2):
    """Build an actual structural box, with the caller's metre-space bounds."""
    lo,hi=np.asarray(bounds,dtype=float)
    p=Parts();p.box(name,lo,hi,material)
    # Ray samples, position buffers and image origin must all use the same
    # actual caller space. Moving positions after rasterization changed their
    # projected phase and caused the observed 36.43px structural error.
    return _build(name,p,np.eye(3),hi-lo,ppu,declared_bounds=[lo,hi])
