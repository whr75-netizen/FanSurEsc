from pathlib import Path
import json,hashlib,sys,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent
from inputs113 import plane,buffer,load_packets
def read(p):return json.loads(p.read_text(encoding='utf8'))
def rgba(v):
    rgb=np.rint(np.clip(np.where(v[...,:3]<=.0031308,v[...,:3]*12.92,1.055*np.maximum(v[...,:3],0)**(1/2.4)-.055),0,1)*255).astype(np.uint8);return np.dstack([rgb,np.rint(np.clip(v[...,3],0,1)*255).astype(np.uint8)])
def full(p,name):
    data=np.zeros((272,480,4),np.float32);cover=np.zeros(272,int);sid=None
    for q in sorted(p.glob('FULL-'+name+'-y*.plane'),key=lambda v:v.name):
        meta,a=plane(q);x,y,w,h=meta['roi'];assert w==480 and h<=32;sid=meta['sourceId']if sid is None else sid;assert sid==meta['sourceId'];data[y:y+h,x:x+w]=a;cover[y:y+h]+=1
    assert(cover==1).all();return data,sid
def stats_values(a):
    vals,counts=np.unique(a,return_counts=True);return{str(float(v)):int(c)for v,c in zip(vals,counts)}
def main():
    state,packets=load_packets(H);assert state['PlayExited']and not state.get('error')and not state.get('restorationError');out=H/'results';out.mkdir(exist_ok=True);data=read(H/'SOURCE113.json');rows=[];images=[]
    for k,(packet,p) in enumerate(packets):
        m=read(p/'RAW_MANIFEST.json');assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip();assert m['sourceId']==packet['sourceId']and m['algorithmValid113']and m['frameUnchangedDuringReadback']and m['displayPhysicalProjectionEqual113'];assert m['forward102']['region113']['drawnFrame']==m['frameIndex'];assert m['runtimeShaderName113'].startswith('ForwardEye113');
        control,sid=full(p,'product77');candidate,sid2=full(p,'candidate113');assert sid==sid2==m['sourceId'];r=m['grid102']['eyeTopLeftROI'];offset=m['grid102']['headToMainOffset'];rect=[r[0]+round(offset[0]),272-r[1]-r[3]+round(offset[1]),r[2],r[3]];x,y,w,h=rect;outside=np.ones((272,480),bool);outside[y:y+h,x:x+w]=False;assert np.array_equal(candidate[outside],control[outside]);
        base=Image.fromarray(rgba(np.flipud(control)));img=Image.fromarray(rgba(np.flipud(candidate)));base.save(out/f'{k:02d}-control.png');img.save(out/f'{k:02d}-candidate.png');images.append(img)
        tile=img.crop((x,272-y-h,x+w,272-y));tile.resize((w*16,h*16),Image.Resampling.NEAREST).save(out/f'{k:02d}-eye-nearest.png')
        ids=buffer(p/'curve-identity.f32').reshape(-1,4);col=buffer(p/'curve-colour.f32').reshape(-1,4);audit=buffer(p/'curve-audit.f32').reshape(-1,4);f=buffer(p/'REGION113-frame.f32').reshape(-1,4);u=f.view(np.uint32);best=buffer(p/'REGION113-best.f32').reshape(2,3,4);ex=buffer(p/'REGION113-exposure.f32').reshape(512,2,4)[:w*h];cells=buffer(p/'REGION113-cells.f32').reshape(512,7,4);cw=m['forward102']['canonicalSize'][0]//4
        eyes=[]
        for eye in [1,2]:
            q=(ids[:,1]==eye);v={str(part):int(np.sum(q&(ids[:,0]==part)))for part in [1,4,6]};paletteErrors={}
            for part in [1,4,6]:
                c=rgba(col.reshape(1,-1,4))[0,:,:3][q&(ids[:,0]==part)];expected=np.array([z['RGB8']for z in(data['keys']if part in[1,4]else data['lidPalette'])if z.get('owner')==eye and(part==6 or z.get('part')==part)],int);paletteErrors[str(part)]=sum(not np.any((expected==a).all(1))for a in c)
            header=u[(eye-1)*32];indices=np.where((cells[:,3,0]==eye)&(cells[:,5,0]==1))[0];expectedCounts=[int(np.sum(cells[indices,0,0]>0)),int(np.sum(cells[indices,0,2]>0))];assert header[1:3].tolist()==expectedCounts and header[3]==0
            eyes.append({'owner':eye,'canonicalCounts':v,'paletteRGB8Errors':{k:int(v)for k,v in paletteErrors.items()},'GPUHeader':header.tolist(),'sourceMassCells':(f[(eye-1)*32+1]/65536).tolist(),'score':best[eye-1,0].tolist(),'optima':int(best[eye-1,2].view(np.uint32)[1])})
        row={'index':k,'sourceId':sid,'frame':m['frameIndex'],'serial':m['mainSerial'],'testStage':packet['testStage82'],'testIndex':packet['stageIndex82'],'requestedClose':m['motion82'].get('requestedClose'),'evaluatedCloseError':m['motion82'].get('evaluatedVsOwnedBakeMax',m['motion82'].get('evaluatedCloseError111')),'pixelRectBottomLeft':rect,'changedPixels':int(np.sum(abs(candidate-control).max(2)>1e-6)),'outsideEyeRectByteEqual':True,'sourceLayoutAudit':stats_values(audit[:,0]),'finalExposureStatus':stats_values(ex[:,1,3]),'eyes':eyes,'computeSHA113':m['computeSHA113'],'validRendererCapture':True,'completeBeautyOrTemporalValidation':False};rows.append(row)
    assert len(rows)==12 and len({r['sourceId']for r in rows})==12
    (H/'RESULT113.json').write_text(json.dumps({'frames':rows,'actualNormalGraphGPUFrames':12,'offlineLayoutReplay':False,'GPUCPUAllocationFeedback':False,'product77DefaultChanged':False,'newComputeAssetOnly':True,'finalSourceForm111ParetoComplete':False,'projectionContract':'Current12 frames have equal effective/physical projection. Other projection offsets fail instead of being accepted.','dataLimitation':'No actual turn/walk/subpixel sequence in this12-state capture. Field gaps are recorded; no complete temporal claim.'},indent=2)+'\n',encoding='utf8')
    images[0].save(out/'CLOSE_REOPEN113.webp',save_all=True,append_images=images[1:9],duration=180,loop=0,lossless=True,method=4)
    print(json.dumps([{'i':r['index'],'frame':r['frame'],'close':r['requestedClose'],'eyes':[(e['canonicalCounts'],e['optima'],e['paletteRGB8Errors'])for e in r['eyes']],'audit':r['sourceLayoutAudit'],'exposure':r['finalExposureStatus']}for r in rows],ensure_ascii=False))
if __name__=='__main__':main()
