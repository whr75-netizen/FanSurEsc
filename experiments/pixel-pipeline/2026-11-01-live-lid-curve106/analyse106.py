from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import buffer,load,rgba,font,components
from analyse_capture68 import plane,rgb8
from curve_reference106 import apply,tests

def curve_segments(p):
    b=p.read_bytes();n,stride=struct.unpack_from('<ii',b);assert stride==32 and len(b)==8+n*32
    return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,2,4)

def signature(ids,colours,bounds):
    w,h=ids.shape[:2];result={};rgb=rgb8(colours[...,:3])
    for y,x in np.argwhere(ids[...,0]>0):
        k=(int(round(ids[y,x,0])),int(round(ids[y,x,1])),int(x+bounds[0]),int(y+bounds[1]))
        result[k]=rgb[y,x].tolist()
    return result

def main():
    D=H/'capture';state=load(sorted(D.glob('STATE106-*'))[-1]);assert state['stage']=='finished'and state['PlayExited']and not state.get('error')and not state.get('restorationError')
    assert not any(x['equal']is False for x in state['nativeComparisons72'])
    review=H/'review';review.mkdir(exist_ok=True);rows=[];mismatches=[];refCells=0;paletteViolations=0;phase={};strips=[]
    bank=np.load(R/'hair-isolation100/TEMPLATE_REFERENCE100.npz');pal={role:{tuple(x)for x in bank['TemplateRGBA'][bank['TemplateRole'][...,0]==role,:3]}for role in (1,4)}
    for entry in state['sequencePackets']:
        p=Path(entry['output']);m=load(p/'RAW_MANIFEST.json');assert m['curveCPUUploadEqualsGPU106']and m['forwardFrame']==m['frameIndex']
        assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()
        w,h=m['forward102']['canonicalSize'];cs=(h//4,w//4)
        layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        bc=buffer(p/'canonical-colour.f32');bi=buffer(p/'canonical-identity.f32');bd=buffer(p/'canonical-decision.f32')
        out=buffer(p/'curve-colour.f32');ids=buffer(p/'curve-identity.f32');dec=buffer(p/'curve-decision.f32');audit=buffer(p/'curve-audit.f32')
        segments=curve_segments(p/'curve-segments106.f32');ref=apply(segments,layers,vis,bc,bi,bd)
        for k in range(len(bc)):
            refCells+=1
            if not(np.array_equal(out[k],ref[0][k])and np.array_equal(ids[k],ref[1][k])and np.array_equal(dec[k],ref[2][k])and audit[k,0]==ref[3][k,0]):
                mismatches.append({'frame':entry['frame'],'cell':k,'GPUaudit':audit[k].tolist(),'CPUaudit':ref[3][k].tolist(),'GPUidentity':ids[k].tolist(),'CPUidentity':ref[1][k].tolist(),'GPUrgb8':rgb8(out[k,:3]).tolist(),'CPUrgb8':rgb8(ref[0][k,:3]).tolist()})
        protected=np.isin(np.rint(bi[:,0]).astype(int),[1,4]);assert np.array_equal(out[protected],bc[protected])and np.array_equal(ids[protected],bi[protected])
        exactSource=0
        for k in np.flatnonzero(audit[:,0]==3):
            si=int(round(audit[k,2]))-1;y,x=divmod(si,w)
            assert np.array_equal(out[k,:3],layers[3,0,y,x,:3])and out[k,3]==1
            assert vis[3,y,x,0]>0 and vis[3,y,x,0]==vis[3,y,x,1]
            assert ids[k,1]==layers[3,1,y,x,2]and ids[k,2]==layers[3,1,y,x,0]
            exactSource+=1
        a={name:plane(p/(name+'.plane'))[1]for name in ['B-EyeRGBA','B-EyeOwner','B-FinalRGBA','B-FinalOwner','F-EyeRGBA','F-EyeOwner','F-FinalRGBA','F-FinalOwner','S4-rgba','S4-meta','H-product77-final']}
        eye=a['F-EyeRGBA'];owner=a['F-EyeOwner'];final=a['F-FinalRGBA'];fowner=a['F-FinalOwner'];hairChanges=np.any(final!=eye,axis=-1)
        for y,x in np.argwhere(hairChanges):
            choices=a['S4-rgba'][y*4:y*4+4,x*4:x*4+4,:3].reshape(-1,3)
            assert any(np.array_equal(q,final[y,x,:3])for q in choices)
            assert 12<=round(float(fowner[y,x,0]))<=15
        for native,role in [(1,2),(4,5)]:
            colours=rgb8(eye[owner[...,0]==role,:3]);paletteViolations+=sum(tuple(x)not in pal[native]for x in colours)
        counts={str(native):{'before':int((a['B-EyeOwner'][...,0]==role).sum()),'after':int((owner[...,0]==role).sum())}for native,role in [(1,2),(4,5),(6,7)]}
        ownerParts={}
        for eyeId in (1,2):
            union=(owner[...,1]==eyeId)&np.isin(np.rint(owner[...,0]).astype(int),[2,5,7]);lid=(owner[...,1]==eyeId)&(owner[...,0]==7)
            ownerParts[str(eyeId)]={'eyeComponents4':components(union),'lidComponents4':components(lid)}
        motion=m['motion82'];row={'frame':entry['frame'],'sourceId':m['sourceId'],'stage':entry['testStage82'],'index':entry['stageIndex82'],
            'requestedClose':motion.get('requestedClose',motion.get('actualClose106')),'evaluatedSourceError':motion.get('evaluatedVsOwnedBakeMax',motion.get('evaluatedCloseError106')),
            'canonicalSize':[w,h],'parts':counts,'perEye':ownerParts,'auditCounts':{str(int(k)):int(v)for k,v in zip(*np.unique(audit[:,0],return_counts=True))},
            'nativeRGBExactProofs':exactSource,'protectedIrisWhiteUnchanged':True,'GPUToCPUUploadExact':True,'externalHairChanges':int(hairChanges.sum()),
            'relativeRootProjected':motion.get('worldRootProjectedRaw'),'requestedPhase':motion.get('requestedPhase'),'frameUnchangedDuringReadback':m['frameUnchangedDuringReadback'],
            'closedCurveNewGPU':True,'finiteLidPalettePending':True}
        rows.append(row)
        stage=entry['testStage82']
        if 'measured-phase'in stage:
            local=ids.reshape(*cs,4);colours=out.reshape(*cs,4);sig=signature(local,colours,m['forward102']['nativeRegistration']['bounds'][:2])
            phase.setdefault(stage,[]).append({'frame':entry['frame'],'signature':sig,'rootProjected':motion['worldRootProjectedRaw'],'requestedPhase':motion['requestedPhase']})
        for prefix,key in [('baseline102','B-FinalRGBA'),('live106','F-FinalRGBA'),('live-eye106','F-EyeRGBA')]:rgba(a[key]).save(review/f'{prefix}-frame{entry["frame"]}-1x.png')
        if stage=='evaluated-blink106'or(stage in('open-turn','closed-turn')and entry['stageIndex82']in(0,4,9)):
            strips.append((row,rgba(a['B-EyeRGBA']),rgba(eye),rgba(final)))
        print(json.dumps({'frame':entry['frame'],'stage':stage,'parts':counts,'audit':row['auditCounts']}),flush=True)
    phaseResults={}
    for stage,items in phase.items():
        base=items[0]['signature'];keyVariants={tuple(sorted(x['signature']))for x in items};colourChanges=[]
        for item in items[1:]:
            for key in base.keys()&item['signature'].keys():
                if base[key]!=item['signature'][key]:colourChanges.append({'frame':item['frame'],'sourceLocalKey':list(key),'beforeRGB8':base[key],'afterRGB8':item['signature'][key]})
        phaseResults[stage]={'frames':len(items),'identityVariants':len(keyVariants),'RGB8changes':colourChanges,'rootProjected':[[x['requestedPhase'],x['rootProjected']]for x in items]}
    board=Image.new('RGB',(1250,130+len(strips)*205),'#20252c');draw=ImageDraw.Draw(board)
    draw.text((20,12),'106 · 매 프레임 실제 source 곡선 → GPU 선택 / 제품77 유지',font=font(25),fill='white')
    for x,title in zip([20,435,850],['같은 입력 GPU102','live GPU106 · 가림 전','live GPU106 · 실제 머리 가림 후']):draw.text((x,65),title,font=font(18),fill='#bcd5e1')
    for j,(row,*images)in enumerate(strips):
        yy=115+j*205;draw.text((20,yy),row['stage']+' '+str(row['requestedClose']if row['requestedClose']is not None else row['index'])+' / frame '+str(row['frame']),font=font(18),fill='white')
        for x,im in zip([20,435,850],images):
            scale=min(18,380//im.width,150//im.height);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);board.paste(im,(x,yy+30),im)
    board.save(review/'LIVE_CURVE_COMPARE106.png')
    result={'actualFrames':len(rows),'PlayEntries':state['PlayEntries'],'CPUReferenceCells':refCells,'CPUGPUMismatches':len(mismatches),'mismatchExamples':mismatches[:15],
       'irisWhiteSourcePaletteViolations':paletteViolations,'phase':phaseResults,'tests':tests(),'frames':rows,'productDefault':77,'GPUActualImplementation':True,
       'fullFaceRegionResolverPending':True,'finiteLidPalettePending':True,'restoration':{'PlayExited':state['PlayExited'],'nativeExact':sum(x['equal']is True for x in state['nativeComparisons72']),
       'unavailable':[x for x in state['nativeComparisons72']if x['equal']is None],'Input':state['editInputRestoration82'],'options':state['optionsRestored'],'time':state['timeRestored'],'pipeline':state['pipelineRestored'],'globalErrors':state['globalRestoreErrors'],
       'RT':[state['beforeMemory']['renderTextureCount'],state['afterMemory']['renderTextureCount']],'beforeMemory':state['beforeMemory'],'afterMemory':state['afterMemory']}}
    (H/'RESULT106.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');(H/'MISMATCHES106.json').write_text(json.dumps(mismatches,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items()if k not in('frames','phase')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
