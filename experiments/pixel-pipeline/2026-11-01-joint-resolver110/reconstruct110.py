"""Stored geometry reconstruction hypothesis, checked against independent GPU
samples. It is NEVER described as a same-frame full-mesh export.

105 supplies rest-in-current-head open/Close100 evaluated vertex templates.
107 supplies its actual head matrix, actual evaluated Close, and logged native
skin-ring positions used ONLY as homography calibration markers, not pigment
shape. Independent UV/depth/occluder vertices test the recovered current map.
"""
from pathlib import Path
import sys,json,struct
import numpy as np
from stored110 import H,R,P109,P108,source_packet,fit_homography,upper_arc
from native109 import read,static
from geometry109 import prepare_packet,transform,physical
from io109 import packet,buffer

def template():
    root=P109;domain=np.load(root/'NATIVE_DOMAIN109.npz');cache=read(root/'NATIVE_CACHE109.json');index=read(root/'RAW_INPUT109_INDEX.json');out=[]
    for frame in [99,104,107]:
        entry=next(x for x in index['entries105']if x['frame']==frame);ctx=prepare_packet(packet(root,entry,'105'),domain,cache);head=np.array(ctx['manifest']['headMatrix105']).reshape(4,4,order='F');local=transform(np.linalg.inv(head),ctx['world'])[:,:3];out.append((local,ctx))
    return domain,out

def recover(row,domain,templates):
    p=source_packet(row);m=read(p/'RAW_MANIFEST.json');native=m['forward102']['nativeRegistration'];motion=m['motion82'];value=motion.get('getterClose',motion.get('actualClose107',None))
    assert m['sourceId']==row['sourceId']and m['frameIndex']==row['frame']and m['frameUnchangedDuringReadback']
    head=np.array(native['headMatrix']).reshape(4,4,order='F');reg=read(P109/'inputs/REGISTRATION89.json');raw=(p/'curve-segments106.f32').read_bytes();count,stride=struct.unpack_from('<ii',raw);assert stride==32 and len(raw)==8+count*stride;segs=np.frombuffer(raw,offset=8,dtype='<f4').reshape(count,2,4);maps={};calibration=[]
    view=np.array(native['physicalView']).reshape(4,4,order='F')
    if value is None:
        # Some motion manifests omit Close. Fit ONLY the logged calibration
        # vertex depths, never assume the stage name means an open eye.
        aa=[];bb=[]
        for eye in reg['eyes']:
            arc=np.array(eye['nativeRingVertexIds'])[upper_arc(eye)];log=segs[segs[:,0,3]==eye['eye']];zlog=np.r_[log[0,0,2],log[:,1,2]]
            z0=-transform(view,transform(head,templates[0][0][arc])[:,:3])[:,2];z1=-transform(view,transform(head,templates[1][0][arc])[:,:3])[:,2]
            aa.extend(z1-z0);bb.extend(zlog-z0)
        aa=np.array(aa);bb=np.array(bb);c=float(aa@bb/(aa@aa));assert -0.001<c<1.001
        source='fit-from-logged-ring-depth; not-independent-depth-validation';c=float(np.clip(c,0,1))
    else:c=float(value)/100;source='recorded-actual-Close'
    assert 0<=c<=1;local=templates[0][0]*(1-c)+templates[1][0]*c;world=transform(head,local)[:,:3]
    offset=np.array(native['anchor'])+np.array(native['bounds'][:2]);view=np.array(native['physicalView']).reshape(4,4,order='F');projection=np.array(m['grid102'].get('queryPhysicalProjection107',m['grid102']['headProjection'])).reshape(4,4,order='F')
    for eye in reg['eyes']:
        owner=eye['eye'];arc=np.array(eye['nativeRingVertexIds'])[upper_arc(eye)];logged=segs[segs[:,0,3]==owner];target=np.concatenate([logged[:1,0,:2],logged[:,1,:2]]);zlog=np.r_[logged[0,0,2],logged[:,1,2]];assert len(arc)==len(target)
        q=transform(np.eye(4),local)@np.array(eye['nativeToAuthoredProjection']);h=fit_homography(q[arc],target+offset);v=np.c_[q,np.ones(len(q))]@h.T;maps[owner]=v[:,:2]/v[:,2:3]-offset
        z=-(transform(view,world[arc]))[:,2];calibration.append({'owner':owner,'markerMaxPixels':float(np.linalg.norm(maps[owner][arc]-target,axis=1).max()),'markerDepthMax':float(np.max(abs(z-zlog))),'skinRingIsCalibrationOnly':True,'CloseSource':source})
    ctx={'manifest':m,'world':world,'uv':domain['uv'],'indices':templates[0][1]['indices'],'maps':maps,'depth':-transform(view,world)[:,2],'view':view,'projection':projection,'owners':templates[0][1]['owners']}
    xy,z,w=physical(view,projection,world);ctx['physicalXY']=xy;ctx['physicalW']=w
    return ctx,calibration,c

def checks(row,ctx):
    p=source_packet(row);m=ctx['manifest'];w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);records=[]
    from native109 import uv_bary
    for part,index in [(1,1),(4,2),(6,3)]:
        errors=[]
        for y,x in np.argwhere(a[index,1,:,:,0]>0):
            v=a[index,:,y,x];owner=round(float(v[1,2]));prim=round(float(v[3,2]))-1;ids=ctx['indices'][part][prim];b=uv_bary(ctx['uv'][ids],v[3,:2].astype(float))
            if b is None:continue
            xy=b@ctx['maps'][owner][ids];depth=b@ctx['depth'][ids];errors.append([float(np.linalg.norm(xy-[(x+.5)/4,(y+.5)/4])),abs(float(depth-v[1,0]))])
        records.append({'part':part,'sampleCount':len(errors),'maxCanonicalPixels':float(np.max(errors,axis=0)[0])if errors else None,'maxDepth':float(np.max(errors,axis=0)[1])if errors else None})
    world=[]
    for name in ['normal-query-geometry107.json','dense-query-geometry107.json']:
        if not(p/name).exists():continue
        g=read(p/name);assert g['sameSourceId']==m['sourceId']and g['frame']==m['frameIndex']
        for tri in g['triangles']:
            if tri['source'][0]!=1:continue
            part,prim=tri['source'][1:];ids=ctx['indices'][part][prim-1];world.append(float(np.linalg.norm(ctx['world'][ids]-np.array(tri['world'])[:,:3],axis=1).max()))
    return {'independentSamples':records,'directQueryTriangleChecks':len(world),'directQueryWorldMaxMetres':max(world)if world else None}

def main():
    H.mkdir(exist_ok=True);domain,templates=template();rows=read(P108/'INPUT108.json');reports=[]
    for row in rows:
        if not row['name'].startswith('actual107'):continue
        ctx,calibration,c=recover(row,domain,templates);report={'frame':row['frame'],'sourceId':row['sourceId'],'stage':row['stage'],'evaluatedClose':c,'reconstructedNotDirectMeshExport':True,'calibration':calibration}|checks(row,ctx);reports.append(report)
    out={'sourceTemplates105OpenReopenHeadLocalMaxMetres':float(np.linalg.norm(templates[0][0]-templates[2][0],axis=1).max()),'frames':reports,'newUnityCalls':0,'hypothesisNotUniversalSkinningProof':True}
    (H/'RECONSTRUCTION110.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'states':len(reports),'openReopenHeadLocalMax':out['sourceTemplates105OpenReopenHeadLocalMaxMetres'],'maxUVProjectedError':max(v['maxCanonicalPixels']or 0 for r in reports for v in r['independentSamples']),'maxDepthError':max(v['maxDepth']or 0 for r in reports for v in r['independentSamples']),
      'directGeometry':[{'frame':r['frame'],'triangles':r['directQueryTriangleChecks'],'worldError':r['directQueryWorldMaxMetres']}for r in reports if r['directQueryTriangleChecks']]}))
if __name__=='__main__':main()
