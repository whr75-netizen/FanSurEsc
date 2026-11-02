"""Audit the missing native lid curve source against actual vertex raster map."""
from pathlib import Path
import sys,json,struct
import numpy as np
from paths114 import H,R,folder
P=folder('113')
sys.path.insert(0,str(P))
from inputs113 import load_packets,buffer,Reader
from trace114 import read,geometry,matrix
from geometry114 import mapped,Face114
def clip_column(a,b,x):
    d=b-a;u=0;t=1
    if abs(d[0])<1e-12:
        if a[0]<x or a[0]>x+1:return None
    else:
        p,q=(x-a[0])/d[0],(x+1-a[0])/d[0];u=max(0,min(p,q));t=min(1,max(p,q))
        if t<=u:return None
    return a+u*d,a+t*d
def row(segs,owner,x):
    total=mass=0
    for a,b in segs:
        if round(a[3])!=owner:continue
        clipped=clip_column(a[:2],b[:2],x)
        if clipped is None:continue
        aa,bb=clipped;w=np.linalg.norm(bb-aa);total+=w*(aa[1]+bb[1])*.5;mass+=w
    return {'meanY':float(total/mass),'row':int(np.floor(total/mass)),'arcLength':float(mass)}if mass>0 else None
def main():
    reg=read(H/'REGISTRATION_CURRENT102.json');source=read(P/'SOURCE113.json');cache=read(folder('109')/'NATIVE_CACHE109.json');_,packets=load_packets(P);trace=read(H/'TRACE114.json');rows=[]
    for (entry,path),tr in zip(packets,trace['frames']):
        if not tr['unsupportedSourceLid']:continue
        m=read(path/'RAW_MANIFEST.json');ctx=geometry(path,m);origin=np.array(tr['sourceOrigin']);ctx=mapped(ctx,reg,origin);ray=Face114(ctx,source['ownSkinMask']);raw=(path/'curve-segments106.f32').read_bytes();n,stride=struct.unpack_from('<ii',raw);assert stride==32 and len(raw)==8+n*32;segs=np.frombuffer(raw,offset=8,dtype='<f4').reshape(n,2,4);pred=[];details=[];at=0;offsets=[];max_uv=0
        for curve in cache['curves']:
            owner=curve['owner'];points=curve['points'];observed=np.vstack([segs[at,0],segs[at:at+len(points)-1,1]]);assert np.all(observed[:,3]==owner);correct=[];pointdata=[]
            for i,p in enumerate(points):
                tid=int(ctx['partMap'][3,p['primitive']-1]);ids=ctx['triangles'][tid,:3];delta=ids-np.array(p['vertices']);assert np.all(delta==delta[0]);offsets.append(int(delta[0]));w=np.array(p['barycentric'],np.float32).astype(float);uv=w@ctx['uv'][ids];max_uv=max(max_uv,float(max(abs(uv-p['sourceUV']))));can=w@ctx['maps'][owner][ids];world=w@ctx['world4'][ids];v=ctx['view']@world;clip=ctx['projection']@v;physical=np.array([(clip[0]/clip[3]*.5+.5)*480,(.5-clip[1]/clip[3]*.5)*272]);mi=int(ctx['triangles'][tid,3]);alpha,weights=ray.alpha.corners(mi,[uv]);bounds=ray.alpha.bounds(mi,[uv])[0];correct.append([*can,float(-v[2]),owner]);pointdata.append({'curvePoint':i,'sourcePrimitive':p['primitive'],'material':mi,'sourceUV':uv.tolist(),'sourceAlphaBilinear':float((alpha*weights).sum()),'sourceAlphaBounds':bounds.tolist(),'nativePhysicalXY':physical.tolist(),'sourceDepth':float(-v[2]),'actualGPUCanonicalXY':observed[i,:2].tolist(),'vertexRasterCanonicalXY':can.tolist(),'mappingDifference':(can-observed[i,:2]).tolist()})
            correct=np.array(correct);pred.extend(np.stack([correct[:-1],correct[1:]],axis=1).tolist())
            for missing in tr['unsupportedSourceLid']:
                if missing['owner']!=owner:continue
                cx,cy=missing['canonicalXY'];chosen=[]
                for j,(a,b)in enumerate(segs[at:at+len(points)-1]):
                    if clip_column(a[:2],b[:2],cx)is not None:chosen.extend([j,j+1])
                chosen=sorted(set(chosen));q=ray.query([pointdata[i]['nativePhysicalXY']for i in chosen],[pointdata[i]['sourceDepth']for i in chosen],owner,expose=False)
                details.append({'missingCanonicalXY':[cx,cy],'owner':owner,'actualUpperRow':row(segs,owner,cx),'correctVertexRasterUpperRow':None,'points':[{**pointdata[i],'intrinsicFace':v}for i,v in zip(chosen,q)]})
            at+=len(points)-1
        assert at==len(segs)and len(set(offsets))==1 and max_uv<1e-6
        pred=np.array(pred)
        for d in details:d['correctVertexRasterUpperRow']=row(pred,d['owner'],d['missingCanonicalXY'][0])
        diff=pred-segs;rows.append({'sourceId':entry['sourceId'],'frame':entry['frame'],'sourceOffsetDerivedFromAllNativePrimitiveBindings':offsets[0],'all848SourceUVBindingMaxError':max_uv,'curveMapGlobalMaxDifferencePixels':float(np.linalg.norm(diff[:,:,:2],axis=2).max()),'cases':details})
    (H/'PIGMENT114.json').write_text(json.dumps({'rows':rows,'sourceImageAndCurrentGeometryUsed':True,'runtimeApplied':False,'missingSamplesNotGivenZeroError':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps([{'frame':r['frame'],'uvMax':r['all848SourceUVBindingMaxError'],'curveMapMax':r['curveMapGlobalMaxDifferencePixels'],'cases':[{'xy':d['missingCanonicalXY'],'oldRow':d['actualUpperRow'],'vertexRow':d['correctVertexRasterUpperRow'],'points':len(d['points']),'alphaRange':[min(p['sourceAlphaBilinear']for p in d['points']),max(p['sourceAlphaBilinear']for p in d['points'])],'nativeVisible':sum(p['intrinsicFace']['faceInterval'][0]>0 for p in d['points']),'deltaMax':max(np.linalg.norm(p['mappingDifference'])for p in d['points'])}for d in r['cases']]}for r in rows],ensure_ascii=False))
if __name__=='__main__':main()
