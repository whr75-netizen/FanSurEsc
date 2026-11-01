"""Cross-check captured current geometry against actual S3 rest/primitive/depth."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent;P76=HERE.parent/'whole-eye76'
sys.path.insert(0,str(P76));from validate_final76 import packet
sys.path.insert(0,str(HERE.parent/'apply-capture66'));from analyse_capture68 import geometry,camera
def main():
 mode=sys.argv[1];st=json.loads(sorted((HERE/mode).glob('STATE77-*.json'))[-1].read_text());native=np.load(HERE.parent/'whole-eye52/SOURCE_SURFACES52.npz');original=native['native_xyz_head'];tri=native['native_role6_tri'];rows=[]
 for entry in st['sequencePackets']:
  root=Path(entry['output']);d=packet(root);a=d['arrays'];gi,meshes=geometry(root/'evaluated-source.geometry');cam=camera(root/'source.camera');m=meshes[1];rx,ry,rw,rh=d['eyeROI'];rest=a['S3-point'];meta=a['S3-meta'];uv=a['S3-uv'];valid=(meta[...,0]>0)&(rest[...,3]>.5)&(meta[...,3]>0);errors=[]
  for y,x in np.argwhere(valid):
   pi=int(round(float(uv[y,x,2])))-1;ids=tri[pi];src=original[ids];q=rest[y,x,:3].astype(float);weights=np.linalg.lstsq(np.c_[src,np.ones(3)].T,np.r_[q,1],rcond=None)[0];local=weights@m['vertices'][ids];world=m['matrix']@np.r_[local,1];view=cam['view']@world;clip=cam['effective']@view;ndc=clip[:2]/clip[3];xy=(ndc*.5+.5)*[480,272];target=np.array([rx+(x+.5)/4,ry+(y+.5)/4]);errors.append([abs(-view[2]-meta[y,x,0]),np.linalg.norm(xy-target),np.linalg.norm(np.array([xy[0],272-xy[1]])-target),float(np.linalg.norm(weights@src-q))])
  z=np.array(errors);morph=dict(m['morphs']);rows.append({'identity':d['identity'],'recordedSourceCloseWeight':morph.get('Fcl_EYE_Close'),'validSamples':len(errors),'maxDepthError':float(z[:,0].max()),'screenYDirectMaxError':float(z[:,1].max()),'screenYFlippedMaxError':float(z[:,2].max()),'restReconstructionMaxError':float(z[:,3].max())})
 out={'rows':rows,'limits':'Morph API value is not declared the effective baked geometry state; GPU sample/depth is independently compared to captured evaluated geometry.'};(HERE/('GEOMETRY_'+mode+'77.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
