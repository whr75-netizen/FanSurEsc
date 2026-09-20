"""Run in Blender --background --factory-startup; produces real volume geometry."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT = Path(__file__).resolve().parents[2] / 'LocalOnly/DeskReference20'
s = json.loads((OUT/'spec.json').read_text())
W,D,H,T,L,I = [s[k] for k in ['width','depth','height','top_thickness','leg_width','common_leg_inset']]
P = s['pixels_per_meter']
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x,scene.render.resolution_y = s['size']
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.render.film_transparent = True
scene.render.filter_size = .01
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0
if hasattr(scene,'eevee'):
    scene.eevee.taa_render_samples = 1

roles = s['face_srgb_factors']
woods={}
for role in [*roles,'handle']:
    woods[role]=bpy.data.images.load(str(OUT/f'wood_{role}.png'),check_existing=True)
    woods[role].pack()

def linear(c):
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4

def mat(role, dims, name, dark=False):
    m = bpy.data.materials.new(name)
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    def node(kind): return nt.nodes.new(kind)
    def link(a,output,b,input): nt.links.new(a.outputs[output],b.inputs[input])
    output=node('ShaderNodeOutputMaterial')
    emission=node('ShaderNodeEmission'); emission.inputs['Strength'].default_value=1
    link(emission,0,output,'Surface')
    tex=node('ShaderNodeTexImage'); tex.image=woods['handle' if dark else role]; tex.interpolation='Closest'; tex.extension='EXTEND'
    uv=node('ShaderNodeUVMap'); uv.uv_map='WoodUV'; link(uv,'UV',tex,'Vector')
    border_uv=node('ShaderNodeUVMap'); border_uv.uv_map='FaceUV'
    sep=node('ShaderNodeSeparateXYZ'); link(border_uv,'UV',sep,'Vector')
    def math_node(op,a=None,b=None):
        n=node('ShaderNodeMath'); n.operation=op
        if a is not None:n.inputs[0].default_value=a
        if b is not None:n.inputs[1].default_value=b
        return n
    invx=math_node('SUBTRACT',1); link(sep,'X',invx,1)
    invy=math_node('SUBTRACT',1); link(sep,'Y',invy,1)
    minx=math_node('MINIMUM'); link(sep,'X',minx,0); link(invx,0,minx,1)
    miny=math_node('MINIMUM'); link(sep,'Y',miny,0); link(invy,0,miny,1)
    dx=math_node('MULTIPLY',b=dims[0]); link(minx,0,dx,0)
    dy=math_node('MULTIPLY',b=dims[1]); link(miny,0,dy,0)
    edge=math_node('MINIMUM'); link(dx,0,edge,0); link(dy,0,edge,1)
    compare=math_node('LESS_THAN',b=.0055); link(edge,0,compare,0)
    mix=node('ShaderNodeMixRGB'); link(compare,0,mix,0); link(tex,'Color',mix,1)
    mix.inputs[2].default_value=tuple(linear(c/255) for c in (79,44,23))+(1,)
    link(mix,0,emission,'Color')
    return m

def box(name,center,dimensions,kind='body'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object; obj.name=name; obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mesh=obj.data; wood_uv=mesh.uv_layers.new(name='WoodUV'); face_uv=mesh.uv_layers.new(name='FaceUV')
    for face in mesh.polygons:
        n=face.normal
        axis=max(range(3),key=lambda i:abs(n[i]))
        axes=([1,2],[0,2],[0,1])[axis]
        size_u,size_v=dimensions[axes[0]],dimensions[axes[1]]
        role='top' if axis==2 and n.z>0 else ('bottom' if axis==2 else ('front' if axis==1 else 'side'))
        material=mat(role,(size_u,size_v),f'{name}_{face.index}_{role}',dark=kind=='handle')
        mesh.materials.append(material); face.material_index=len(mesh.materials)-1
        for loop_i in face.loop_indices:
            co=mesh.vertices[mesh.loops[loop_i].vertex_index].co
            fu=co[axes[0]]/size_u+.5; fv=co[axes[1]]/size_v+.5
            face_uv.data[loop_i].uv=(fu,fv)
            world=co+obj.location
            if kind=='leg' and axis!=2:
                # Same vertical grain convention on all four identical legs.
                wu=world.z/(H-T); wv=1-fu*.28
            elif axis==2:
                wu=world.x/W+.5; wv=1-(world.y/D+.5)
                if name=='Tabletop' and n.z>0:
                    # Undo material crop so top grain stays at its measured location.
                    wu=(wu-.025)/.95; wv=(wv-.045)/.91
            elif axis==1:
                wu=world.x/W+.5; wv=1-(world.z-(H-T-.19))/.27
            else:
                wu=world.y/D+.5; wv=1-(world.z-(H-T-.19))/.27
            wood_uv.data[loop_i].uv=(wu,wv)
    obj['part_role']=kind
    obj['canonical_dimensions']=list(dimensions)
    return obj

box('Tabletop',(0,0,H-T/2),(W,D,T))
legs=[]
for ix in (-1,1):
    for iy in (-1,1):
        legs.append(box(f'Leg_{ix}_{iy}',(ix*(W/2-I-L/2),iy*(D/2-I-L/2),(H-T)/2),(L,L,H-T),'leg'))

apron_height=.19
inside_w=W-2*(I+L)
inside_d=D-2*(I+L)
front_y=-D/2+I+L*.48
back_y=D/2-I-L*.48
z=H-T-apron_height/2
box('Apron_back',(0,back_y,z),(inside_w,.03,apron_height))
for ix in (-1,1):
    box(f'Apron_side_{ix}',(ix*(W/2-I-L*.48),0,z),(.03,inside_d,apron_height))
# Two fronts fill the front span; all dimensions derive from the same desk template.
gap=.011
drawer_w=(inside_w-gap)/2
for ix in (-1,1):
    x=ix*(drawer_w+gap)/2
    box(f'Drawer_{ix}',(x,front_y,z),(drawer_w,.036,apron_height))
    box(f'Handle_{ix}',(x,front_y-.034,z),(drawer_w*.19,.032,.032),'handle')

camera_data=bpy.data.cameras.new('OrthographicCamera')
camera=bpy.data.objects.new('OrthographicCamera',camera_data)
scene.collection.objects.link(camera); scene.camera=camera
camera_data.type='ORTHO'; camera_data.clip_start=.01; camera_data.clip_end=100

def configure_camera(phi,theta,matched=True):
    r=Vector((math.cos(phi),math.sin(phi),0))
    u=Vector((-math.sin(phi)*math.sin(theta),math.cos(phi)*math.sin(theta),math.cos(theta)))
    direction=r.cross(u)
    px,py=s['size']; ox,oy=s['origin_px']
    target=r*((px/2-ox)/P)+u*((oy-py/2)/P) if matched else Vector((0,0,H*.5))
    camera.location=target+direction*5
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.ortho_scale=1
    frame=camera_data.view_frame(scene=scene)
    frame_width=max(v.x for v in frame)-min(v.x for v in frame)
    camera_data.ortho_scale=(px/P)/frame_width
    bpy.context.view_layer.update()
    return r,u,direction

r,u,direction=configure_camera(s['azimuth'],s['elevation'])
projection_errors=[]
for point in [Vector((0,0,0)),Vector((W/2,D/2,H)),Vector((-W/2,-D/2,H))]:
    view=world_to_camera_view(scene,camera,point)
    actual=Vector((view.x*s['size'][0],(1-view.y)*s['size'][1]))
    expected=Vector((s['origin_px'][0]+P*r.dot(point),s['origin_px'][1]-P*u.dot(point)))
    projection_errors.append((actual-expected).length)
leg_bounds=[]
for leg in legs:
    vertices=[leg.matrix_world@Vector(v) for v in leg.bound_box]
    leg_bounds.append({'name':leg.name,'dimensions':list(leg.dimensions),
                       'foot_z':min(v.z for v in vertices),'top_z':max(v.z for v in vertices),
                       'center':list(leg.location)})
invariants=(len(legs)==4 and max(projection_errors)<.001 and
    all(max(abs(x-y) for x,y in zip(leg['dimensions'],(L,L,H-T)))<1e-6 and
        abs(leg['foot_z'])<1e-6 and abs(leg['top_z']-(H-T))<1e-6 for leg in leg_bounds) and
    all(min(o.dimensions)>0 for o in scene.objects if o.type=='MESH'))
check={'invariants_passed':bool(invariants),'legs':leg_bounds,
       'projection_max_error_px':max(projection_errors),'light_count':sum(o.type=='LIGHT' for o in scene.objects),
       'mesh_count':sum(o.type=='MESH' for o in scene.objects),
       'basis_dot_products':[r.dot(u),r.dot(direction),u.dot(direction)],
       'render_size':s['size'],'bpy_version':bpy.app.version_string}
(OUT/'geometry_check.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
assert invariants,check

scene.render.filepath=str(OUT/'render.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'desk.blend'))
bpy.ops.render.render(write_still=True)
scene.render.resolution_x,scene.render.resolution_y=s['coarse_size']
scene.render.filepath=str(OUT/'render_coarse.png')
bpy.ops.render.render(write_still=True)
scene.render.resolution_x,scene.render.resolution_y=768,512
for label,offset in [('left',-math.pi/6),('right',math.pi/6)]:
    configure_camera(s['azimuth']+offset,s['elevation'],matched=False)
    scene.render.filepath=str(OUT/f'view_{label}.png')
    bpy.ops.render.render(write_still=True)
print('D20_RENDER_COMPLETE '+json.dumps(check))
