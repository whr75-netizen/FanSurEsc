"""One triangle-query witness and a separate source-only shade audit."""
from pathlib import Path
import hashlib, json, sys, numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet,mesh
from analyse_capture68 import camera
from surface_query90 import ProjectedSurface

def main():
 old=ROOT/'native-feature89';state=json.loads(sorted((old/'capture89f').glob('STATE89*.json'))[-1].read_text());entry=next(e for e in state['sequencePackets']if e['frame']==140);d=packet(Path(entry['output']));v,n,uv,tri,world=mesh(d['path']/'eye-evaluated.mesh');cam=camera(d['path']/'source.camera');wv=np.c_[v,np.ones(len(v))]@world.T
 q=json.loads((HERE/'CLOSE_RESULT90.json').read_text())['target'];surface=ProjectedSurface(wv,uv,tri[3],cam['view'],cam['projection'],[480,272]);rows=[]
 for primitive in [3120,3116]:
  indices=tri[3][primitive-1];rows.append({'primitive':primitive,'indices':indices.tolist(),'worldVertices':wv[indices].tolist(),'UV':uv[indices].tolist(),'screenTopLeft':surface.xy[indices].tolist(),'depth':surface.depth[indices].tolist()})
 witness={'sourceId':d['m']['sourceId'],'frame':140,'renderSerial':d['m']['mainSerial'],'view':cam['view'].tolist(),'projection':cam['projection'].tolist(),'viewport':[480,272],'query':q['physicalXYTopLeft'],'whiteDepth':q['whiteDepth'],'triangles':rows,'exactQueryHits':surface.hits(q['physicalXYTopLeft']),'interpretation':'The old nearest4x selected triangle3120 does not contain this query. Adjacent triangle3116 does and is opaque in front. This is not a Close-state deletion rule.'}
 (HERE/'GEOMETRY_WITNESS90.json').write_text(json.dumps(witness,indent=2)+'\n')
 # Diagram keeps geometric sample coordinates; it is not a smoothed image.
 board=Image.new('RGB',(700,470),'#141923');draw=ImageDraw.Draw(board);centre=np.asarray(q['physicalXYTopLeft']);scale=800;origin=np.array([340,235])
 def pt(p):return tuple((origin+(np.asarray(p)-centre)*scale).tolist())
 for row,colour in zip(rows,['#ffaf46','#5cd99b']):
  points=[pt(p)for p in row['screenTopLeft']];draw.line(points+[points[0]],fill=colour,width=3)
  middle=np.asarray(row['screenTopLeft']).mean(0);draw.text(pt(middle),str(row['primitive']),fill=colour)
 draw.ellipse((336,231,344,239),fill='#ffffff');draw.text((351,225),'query (226.3731,52.5698)',fill='white')
 draw.text((12,12),'Frame140: actual source query vs nearest4x triangle',fill='white')
 draw.text((12,35),'Orange3120 misses the query; green3116 contains it.',fill='white')
 draw.text((12,413),'skin depth13.73193354 < white13.74600601; alpha1; gap0.01407247',fill='white')
 draw.text((12,438),'World geometry + UV provenance; no threshold on Close or RGB.',fill='white');board.save(HERE/'QUERY_TRIANGLES90.png')
 repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');alpha=json.loads((HERE/'ALPHA_SOURCE90.json').read_text());package=Path(alpha['package']['resolvedPath'])
 files={
 'continuousLight':repo/'Assets/EUnityValidation01/SkinPalette302/Shaders/FaceSceneLight335.hlsl',
 'originalSource':repo/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeSurface348.shader',
 'retargetSource':old/'NativeSurface89.shader',
 'normal':package/'MToon10/Shaders/vrmc_materials_mtoon_geometry_normal.hlsl',
 'vertex':package/'MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl',
 'alpha':package/'MToon10/Shaders/vrmc_materials_mtoon_geometry_alpha.hlsl',
 'backingProducer':repo/'Assets/EUnityValidation01/HeadLocal367/Runtime/FullFeature367.cs',
 'phaseCacheConsumer':repo/'Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs',
 'independentMetadata':repo/'Assets/EUnityValidation01/GameMapIntegration333/Shaders/Independent333.shader'}
 functions={'continuousLight':['AccumulateSurfaceLight335','ContinuousSurfaceLight335'],'originalSource':['Eye333Vertex','Eye333Fragment'],'retargetSource':['Eye333Vertex','Eye333Fragment','SourceLogicalScreen89'],'normal':['GetMToonGeometry_Normal'],'vertex':['MToonVertex'],'alpha':['GetMToonGeometry_Alpha'],'backingProducer':['RecordRenderGraph'],'phaseCacheConsumer':['PrepareCurrent'],'independentMetadata':['meta=float4','role+1']}
 evidence={}
 for name,path in files.items():
  text=path.read_text(encoding='utf-8-sig');lines=text.splitlines();evidence[name]={'path':str(path),'SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'matches':[{ 'line':i+1,'text':line.strip()}for i,line in enumerate(lines)if any(f in line for f in functions[name])]}
 (HERE/'SOURCE_INDEX90.json').write_text(json.dumps(evidence,indent=2)+'\n')
 control=json.loads((old/'capture89f/STATE89-0003-same-head-camera-native-control.json').read_text())['sourceControl89']
 audit={'status':'CONTINUOUS_SHADE_PRODUCER_MISMATCH_NOT_RESOLVED','maxAbs':max(f['maxAbs']for t in control['trials']for f in t['fields']if f['channel']==4),'sourceControl':control,
 'formula':'g = available>1e-6 ? saturate(lit/available) :0; ambient=Y(SampleSH(normalWS)); lit starts ambient; each light adds Y(light.color)*distanceAttenuation*shadowAttenuation*saturate(dot(n,l)*.5+.5), available adds the same weight without shadow/diffuse.',
 'confirmed':'RGBA/meta/rest/UV and quantized shade/factor agree in the accepted geometry-only control. Continuous g does not. Normal construction uses face orientation, normal/tangent and optional normal map, not viewDirWS. Thus the overridden viewDir alone is not a proven direct diffuse cause.',
 'excludedInference':'Do not identify SH, gamma, colour palette, screenY or material exposure as the cause without per-producer inputs. No RGB correction is applied.',
 'observationLimit':'The calibration retained maxima and only first4 differing samples, not the max sample index nor exact paired raw input. Later frame140 is not that calibration frame. Stored32frame packets cannot reconstruct that old maximum sample.',
 'minimumNextProbe':{'scope':'one same-frame original/clone S3 sample from a new sourceId; reject capture unless matching primitive/UV/position/depth and render serial','fields':['actual shader variant and source material property/keyword signature','normalWS after normal mapping; VFACE; tangentWS/sign; UV; worldPosition','SampleSH(normalWS) and luminance','main-light direction/RGB/distance/shadow attenuation','additional-light index set and accumulated lit/available','actual normalizedScreenSpaceUV; continuous g; Q(g); factor'], 'notNeeded':'new whole renderer, texture-average correction or full-frame readback'},
 'productIntegration':False,'newPlayEntries':0}
 (HERE/'SHADE_AUDIT90.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({'triangleWitness':True,'shadeMax':audit['maxAbs'],'sourceFiles':len(evidence)}))
if __name__=='__main__':main()
