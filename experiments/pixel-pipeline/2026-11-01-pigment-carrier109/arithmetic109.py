"""Compare source-producer arithmetic, without changing any observation bound."""
import numpy as np,json
from native109 import H,R,read,static
from io109 import entries,packet
from geometry109 import prepare_packet,buffer,uv_bary

def main():
    d=np.load(H/'NATIVE_DOMAIN109.npz');cache=read(H/'NATIVE_CACHE109.json');reg=read(static('REGISTRATION89.json',R/'native-feature89/REGISTRATION89.json'));seq=entries(H,'105',lambda:read(sorted((R/'closed-support105/direct').glob('STATE102-*'))[-1])['sequencePackets']);results=[]
    from io109 import mesh
    for e in seq:
        from pathlib import Path
        p=packet(H,e,'105');ctx=prepare_packet(p,d,cache);m=ctx['manifest'];identity,model,current,uv,indices=mesh(p/'current-face105.mesh');nr=m['forward102']['nativeRegistration'];head=np.array(m['headMatrix105'],np.float32).reshape(4,4,order='F');world=np.c_[current.astype(np.float32),np.ones(len(current),np.float32)]@model.astype(np.float32).T;headq=world@np.linalg.inv(head).T
        maps={}
        for row in reg['eyes']:
            owner=row['eye'];inv=np.array(next(q for q in m['existingEyeInverse105']if q['eye']==owner)['inverseHomography'],np.float32).reshape(4,4,order='F');inv[3,3]=1;forward=np.linalg.inv(inv)
            native=headq@np.asarray(row['nativeToAuthoredProjection'],np.float32);q=np.c_[native,np.ones(len(native),np.float32),np.zeros(len(native),np.float32)]@forward.T;local=q[:,:2]/q[:,2:3]-np.asarray(nr['anchor'],np.float32)
            v=-world@np.asarray(nr['physicalView'],np.float32).reshape(4,4,order='F').T;clip=np.c_[local[:,0],-local[:,1],v[:,2],np.ones(len(local),np.float32)]@np.asarray(nr['canonicalGPUProjection'],np.float32).reshape(4,4,order='F').T
            size=np.asarray(m['forward102']['canonicalSize'],float)/4;maps[owner]=(clip[:,:2]/clip[:,3:4]*.5+.5)*size
        w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);errors=[]
        for y,x in np.argwhere(a[3,1,:,:,0]>0):
            owner=round(float(a[3,1,y,x,2]));tid=round(float(a[3,3,y,x,2]))-1;ids=indices[6][tid];b=uv_bary(uv[ids],a[3,3,y,x,:2].astype(float));target=np.array([(x+.5)/4,(y+.5)/4]);errors.append([np.linalg.norm(b@ctx['maps'][owner][ids]-target),np.linalg.norm(b@maps[owner][ids]-target)])
        results.append({'sourceId':m['sourceId'],'frame':m['frameIndex'],'maxDoubleReferencePixels':float(np.max(errors,0)[0]),'maxFloat32ProducerPixels':float(np.max(errors,0)[1]),
          'publicEyeInverseWasSaved':True,'exactAppliedHeadInverseAndForwardShaderMatricesWereNotSaved':True,'notClaimingExactNativeInverseOrGPUFMAReproduction':True})
    (H/'ARITHMETIC109.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':main()
