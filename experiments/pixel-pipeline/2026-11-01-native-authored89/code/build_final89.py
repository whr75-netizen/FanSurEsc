"""Make bounded final-fill packets from real89 inputs; uncertainty stays explicit."""
from pathlib import Path
import json,struct,sys
import numpy as np
from analyse89 import packet,geometry,visibility,PARTS,rgb8
HERE=Path(__file__).resolve().parent
def string(f,s):
 b=s.encode();n=len(b)
 while n>=128:f.write(bytes([(n&127)|128]));n>>=7
 f.write(bytes([n]));f.write(b)
def linear(c):
 c=np.asarray(c,float)/255;return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def main():
 state=json.loads(sorted((HERE/'capture89f').glob('STATE89*.json'))[-1].read_text());details=json.loads((HERE/'result89-ray/CELL_PROVENANCE89.json').read_text());byFrame={r['frame']:r for r in details};out=HERE/'final-input89';out.mkdir(exist_ok=False);summaries=[]
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));m=d['m'];a=d['a'];frame=m['frameIndex'];source=np.load(HERE/f'result89-ray/frame{frame}.npz');layers,physical,geom=geometry(d);vis,uncertain=visibility(d,layers,physical);base=a['native-final-rgba'];h,w=base.shape[:2];nroi=m['nativeFinalReference89']['nativeROI'];origin=np.asarray(m['nativeFinalReference89']['origin']);offset=np.asarray(m['trace86']['headJoinOffset']);delta=np.asarray(m['camera86']['deliveredDelta'][:2]);yy,xx=np.mgrid[:h,:w];bottom=(np.stack([xx+nroi[0]+.5,yy+nroi[1]+.5],-1)-origin)/m['nativeFinalReference89']['scale']-offset-delta;top=bottom.copy();top[...,1]=272-bottom[...,1];anchor=np.asarray(m['retarget89']['anchor']);bounds=np.asarray(m['retarget89']['bounds']);local=np.floor(top-anchor-bounds[:2]).astype(int);rx,ry,rw,rh=d['roi'];hx=np.floor(bottom[...,0]).astype(int)-rx;hy=np.floor(bottom[...,1]).astype(int)-ry;inside=(hx>=0)&(hx<rw)&(hy>=0)&(hy<rh);px=np.clip(hx,0,rw-1);py=np.clip(hy,0,rh-1);old=a['old-eye-owner'][py,px];intr=a['old-intrinsic'][py,px];oldFeature=inside&(((np.rint(old[...,0])==2)&(intr[...,0]>0))|(np.rint(old[...,0])==7));ex,ey,ew,eh=d['eyeROI'];ix=np.floor(bottom[...,0]).astype(int)-ex;iy=np.floor(bottom[...,1]).astype(int)-ey;ri=(ix>=0)&(ix<ew)&(iy>=0)&(iy<eh);ix=np.clip(ix,0,ew-1);iy=np.clip(iy,0,eh-1);protected=ri&(d['records'][iy,ix,14,2]>.5)
  for variant,cname,iname,dname in [('coupled','rawColour','rawIdentity','raw'),('ray-visible','visibleColour','visibleIdentity','sourceVisible')]:
   colour=source[cname];identity=source[iname];ch,cw=colour.shape[:2];kx=np.clip(local[...,0],0,cw-1);ky=np.clip(local[...,1],0,ch-1);inLocal=(local[...,0]>=0)&(local[...,0]<cw)&(local[...,1]>=0)&(local[...,1]<ch);ids=identity[ky,kx];rgba=colour[ky,kx];newEye=inLocal&np.isin(np.rint(ids[...,0]),[1,4,6]);validCell=np.ones((ch,cw),bool)
   if variant=='ray-visible':
    for row in byFrame[frame][dname]:
     x,y=row['cell'];sx,sy=row['sample'];validCell[y,x]=not uncertain[PARTS.index(row['part']),sy,sx]
   else:validCell[:]=False # Raw warped skin depth has not validated physical visibility.
   candidateUnknown=newEye&~validCell[ky,kx];baseMeta=a['base-meta'][py,px];foreground=inside&newEye&(baseMeta[...,0]>0)&(baseMeta[...,0]<ids[...,3]-3e-5)&~np.isin(np.rint(baseMeta[...,1]),[0,1,3,4,6]);newEye&=~foreground&~protected;candidateUnknown&=newEye
   replaceOld=oldFeature&~newEye&~foreground&~protected;chosen=rgba.copy();chosen[...,3]=1;family=ids[...,0].copy();depth=ids[...,3].copy();invalid=candidateUnknown.copy();scope=newEye|replaceOld
   available=np.zeros((h,w),bool)
   for prefix in ['base','backing']:
    q=a[prefix+'-meta'][py,px];c=a[prefix+'-rgba'][py,px];clean=(q[...,0]>0)&(c[...,3]>=.999)&~np.isin(np.rint(q[...,1]),[0,1,4,6]);take=replaceOld&~available&clean;chosen[take]=c[take];family[take]=q[take,1];depth[take]=q[take,0];available|=take
   missing=replaceOld&~available;chosen[missing]=0;invalid|=missing
   # The finite table contains exact RGB8 from a source sample, with no RGB mix.
   code=rgb8(chosen[...,:3]);packed=np.c_[code[scope],np.rint(chosen[scope,3]*255).astype(np.uint8)];unique,inv=np.unique(packed,axis=0,return_inverse=True)
   if len(unique)==0:unique=np.zeros((1,4),np.uint8)
   palette=np.c_[linear(unique[:,:3]),unique[:,3]/255].astype('<f4');mapping=np.zeros((h,w,4),'<f4');mapping[scope,0]=inv+1;mapping[scope,1]=family[scope];mapping[scope,2]=depth[scope];mapping[scope,3]=np.where(invalid[scope],-1,1);expected=base.copy();expected[scope]=palette[inv];validity=np.ones_like(base);validity[...,1:]=0;validity[invalid,0]=0;validity[invalid,1]=2
   stem=f'{frame:04d}-{variant}';file=out/(stem+'.bin')
   with file.open('xb')as f:
    string(f,'final-palette89/v1');string(f,m['sourceId']);string(f,variant);f.write(struct.pack('<5i',frame,m['mainSerial'],w,h,len(palette)));f.write(base.astype('<f4').tobytes());f.write(mapping.tobytes());f.write(palette.tobytes())
   np.savez_compressed(out/(stem+'-expected.npz'),colour=expected,owner=mapping,valid=validity,scope=scope,invalid=invalid,protected=protected,foreground=foreground,palette=palette)
   summaries.append({'file':file.name,'sourceId':m['sourceId'],'frame':frame,'variant':variant,'stage':entry['testStage82'],'index':entry['stageIndex82'],'size':[w,h],'paletteCount':len(palette),'scopeNativePixels':int(scope.sum()),'invalidNativePixels':int((invalid&scope).sum()),'missingBackingNativePixels':int(missing.sum()),'unknownSelectedSourceNativePixels':int(candidateUnknown.sum()),'protectedNativePixels':int(protected.sum()),'foregroundPreservedNativePixels':int(foreground.sum()),'rawSourceVisibilityValidated':False,'finalAcceptance':False})
 (out/'INPUT_INDEX89.json').write_text(json.dumps(summaries,indent=2)+'\n');print(json.dumps({'packets':len(summaries),'scope':sum(x['scopeNativePixels']for x in summaries),'invalid':sum(x['invalidNativePixels']for x in summaries),'missingBacking':sum(x['missingBackingNativePixels']for x in summaries),'maxPalette':max(x['paletteCount']for x in summaries)},indent=2))
if __name__=='__main__':main()
