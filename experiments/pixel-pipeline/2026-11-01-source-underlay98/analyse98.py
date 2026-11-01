from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import rgb8
from input98 import packet
sys.path.insert(0,str(ROOT/'live-joint96'));from validate96 import read
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    folder=sys.argv[1]if len(sys.argv)>1 else'capture';dest=HERE if folder=='capture'else HERE/('analysis-c'if folder=='capture-c'else'analysis-b');dest.mkdir(exist_ok=True)
    state=json.loads(sorted((HERE/folder).glob('STATE98*'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError');out=dest/'review';out.mkdir(exist_ok=True);rows=[];changes=[];panels={}
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));a=d['a'];m=d['m'];old=a['legacy96-final3'];new=a['live96-final3'];colour=a['live96-final0'];owner=a['live96-final1'];depth=a['live96-final2'];stage=e['testStage82'];frame=e['frame'];fix=(old[...,0]<0)&(new[...,0]>=0);rem=(new[...,0]<0);different=np.any(colour!=a['legacy96-final0'],axis=-1);protected=new[...,2]>0;assert all(np.array_equal(a[f'live96-final{i}'][protected],a[k][protected])for i,k in enumerate(['native-final-rgba','native-final-owner','native-final-depth']))
        passed=(new[...,0]==0)|(new[...,0]<0);assert all(np.array_equal(a[f'live96-final{i}'][passed],a[k][passed])for i,k in enumerate(['native-final-rgba','native-final-owner','native-final-depth']))
        world=new[...,0]==5;assert np.array_equal(colour[world],a['actual-world98-0'][world])and not owner[world].any();assert np.array_equal(depth[world,0],a['actual-world98-1'][world,3])and not depth[world,1:].any()
        worldError=abs(a['actual-world98-1'][...,3]-a['native-final-depth'][...,0]);assert worldError.max()==0
        # Same exact physical raster point as the compute, not a neighbouring
        # colour guess. Preserve float32 operation order for the depth check.
        nr=m['nativeFinalReference89']['nativeROI'];origin=np.array(m['nativeFinalReference89']['origin']);scale=m['nativeFinalReference89']['scale'];offset=np.array(m['trace86']['headJoinOffset'])+np.array(m['camera86']['deliveredDelta'][:2]);roi=m['currentSources91']['roiTopLeft'];depthOffset=np.float32(m['retarget89']['physicalView'][14]-m['main']['view'][14])if 'main'in m else None
        coords=[]
        for y,x in np.argwhere(new[...,0]==4):
            bottom=(np.array([x+nr[0],y+nr[1]])+.5-origin)/scale-offset;p=np.floor((bottom-[roi[0],272-roi[1]-roi[3]])*2).astype(int);nx,ny=p;bc=a['current-non-eye98-0'][ny,nx];bm=a['current-non-eye98-1'][ny,nx];uv=a['current-non-eye98-2'][ny,nx];assert np.array_equal(colour[y,x],bc)and owner[y,x,0]==bm[1]and owner[y,x,1]==bm[2]and owner[y,x,3]==uv[2]
            coords.append({'nativeROIxy':[int(x),int(y)],'nativeAbsoluteXY':[int(x+nr[0]),int(y+nr[1])],'physicalNonEyeSampleXY':[int(nx),int(ny)],'literalSourceRGBA':bc.tolist(),'sourceMeta':bm.tolist(),'sourceUVPrimitiveRenderer':uv.tolist(),'finalOwner':owner[y,x].tolist(),'depthOffsetObserved':float(owner[y,x,2]-bm[0]),'sourceRole':int(bm[1])-1})
        c=read(d['path']/'live96-colour.buffer');ident=read(d['path']/'live96-identity.buffer');source=set()
        for p in [1,2,3]:
            ar=a[f'retarget-part{p}-0'];meta=a[f'retarget-part{p}-1'];source.update(tuple(v)for v in ar[meta[...,0]>0,:3])
        assert all(tuple(v)in source for v in c[ident[:,0]>0,:3])
        row={'frame':frame,'sourceId':e['sourceId'],'stage':stage,'index':e['stageIndex82'],'legacyInvalid':int((old[...,0]<0).sum()),'candidateInvalid':int(rem.sum()),'fixedInvalid':int(fix.sum()),'regressedInvalid':int(((old[...,0]>=0)&rem).sum()),'nonEyeSourceRestores':int((new[...,0]==4).sum()),'worldSourceRestores':int(world.sum()),'differentColourPixels':int(different.sum()),'canonicalUnknown':m['live96']['canonicalUnknown'],'roleOwnerSignature':hashlib.sha256(ident[:,:2].tobytes()).hexdigest(),'colourSignature':hashlib.sha256(c.tobytes()).hexdigest(),'worldDepthExact':True,'gpuProfiling':m['underlay98']['profiling'],'GPUCost':m['live96']}
        if stage=='evaluated-blink':row.update({k:m['motion82'][k]for k in ['getterClose','evaluatedVsOwnedBakeMax','evaluatedStateConditionPassed']});row['irisScleraCanonical']=int(np.isin(ident[:,0],[1,4]).sum())
        changes.append({'frame':frame,'sourceId':e['sourceId'],'nonEye':coords,'fixedNativeROIxy':[list(map(int,[x,y]))for y,x in np.argwhere(fix)],'worldNativeROIxy':[list(map(int,[x,y]))for y,x in np.argwhere(world)],'remainingUnknownNativeROIxy':[list(map(int,[x,y]))for y,x in np.argwhere(rem)]});rows.append(row)
        images=[]
        for label,key in [('product77','native-final-rgba'),('legacy96','legacy96-final0'),('underlay98','live96-final0')]:
            im=Image.fromarray(np.flipud(rgb8(a[key][...,:3])));im.save(out/f'frame{frame}-{label}-native1x.png');images.append((label,im))
        mask=np.zeros((*new.shape[:2],3),np.uint8);mask[fix]=[40,220,100];mask[rem]=[240,80,180];mask[(new[...,0]==4)&~fix]=[60,130,255];mask[world&~fix]=[240,180,40];images.append(('fixed green / unresolved pink',Image.fromarray(np.flipud(mask))))
        w=max(im.width for _,im in images);h=max(im.height for _,im in images);panel=Image.new('RGB',(w*8*4,h*8+26),'#20242a');draw=ImageDraw.Draw(panel)
        for i,(label,im)in enumerate(images):panel.paste(im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST),(i*w*8,26));draw.text((i*w*8+3,5),f'{label} {stage}{row["index"]} f{frame}',fill='white')
        panel.save(out/f'frame{frame}-comparison8.png');panels.setdefault(stage,[]).append(panel)
    for stage,images in panels.items():
        w=max(x.width for x in images);h=max(x.height for x in images);fixed=[]
        for im in images:canvas=Image.new('RGB',(w,h),'#20242a');canvas.paste(im,(0,0));fixed.append(canvas)
        fixed[0].save(out/(stage+'.gif'),save_all=True,append_images=fixed[1:],duration=300,loop=0)
    summary={'status':'ACTUAL_SAME_FRAME_LEGACY96_VS_GENERIC_UNDERLAY98','frames':len(rows),'actualSourceIdsDistinctFrom97':True,'legacyInvalidTotal':sum(r['legacyInvalid']for r in rows),'candidateInvalidTotal':sum(r['candidateInvalid']for r in rows),'fixedTotal':sum(r['fixedInvalid']for r in rows),'regressedTotal':sum(r['regressedInvalid']for r in rows),'nonEyeRestoresTotal':sum(r['nonEyeSourceRestores']for r in rows),'worldRestoresTotal':sum(r['worldSourceRestores']for r in rows),'worldDepthAllNativeExact':True,'protectedNativeAllExact':True,'unknownOriginalPassThroughExact':True,'literalSourceRGBForAllEyeOutputs':True,'phaseRoleOwnerSignatures':len({r['roleOwnerSignature']for r in rows if r['stage']=='measured-phase'}),'phaseColourSignatures':len({r['colourSignature']for r in rows if r['stage']=='measured-phase'}),'rows':rows,'productDefault':77,'aestheticSuccess':False}
    save(dest/'COMPARISON98.json',summary);save(dest/'CHANGED_SOURCE98.json',changes);print(json.dumps({k:v for k,v in summary.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
