"""Actual same-frame GPU102/106/107 + diagnostic8x source/visibility audit."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,rgba,font,components
from analyse_capture68 import plane,rgb8
sys.path.insert(0,str(R/'live-curve106'));from analyse106 import curve_segments,signature
from verify106 import hair
from curve_reference106 import apply as old_apply,intersects
from joint_reference107 import apply,contributions,tests

def numeric(v):
    if isinstance(v,np.generic):return v.item()
    raise TypeError(type(v).__name__)
def save(n,x):(OUTROOT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=numeric)+'\n',encoding='utf-8')
def main():
    global OUTROOT
    cap=sys.argv[1]if len(sys.argv)>1 else'capture-b';OUTROOT=H/('analysis-final'if cap=='capture-final'else'analysis4x');OUTROOT.mkdir(exist_ok=True)
    files=sorted((H/cap).glob('STATE107-*'));assert files,'No actual107 states'
    state=load(files[-1]);assert state['stage']=='finished'and state['PlayExited']and not state.get('restorationError'),{k:state.get(k)for k in ['stage','error','restorationError']}
    if state.get('error'):assert state['error'].startswith('System.InvalidOperationException: 100 original draw ranges not restored')and len(state['sequencePackets'])==51
    assert state['motionRestoration82']['allRestored']and not any(x['equal']is False for x in state['nativeComparisons72'])
    out=OUTROOT/'review';out.mkdir(exist_ok=True);rows=[];gaps=[];jointProof=[];mismatch=[];cells=0;variants={};boards=[];allHair=0;paletteOutside=0;planeChecks=0;reopen={};hairStates={}
    bank=np.load(R/'hair-isolation100/TEMPLATE_REFERENCE100.npz');pal={role:{tuple(x)for x in bank['TemplateRGBA'][bank['TemplateRole'][...,0]==role,:3]}for role in (1,4)}
    for e in state['sequencePackets']:
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()
        a={}
        for f in p.glob('*.plane'):
            h,v=plane(f);assert h['sourceId']==m['sourceId']and h['frameIndex']==e['frame']and h['renderSerial']==e['serial']and np.isfinite(v).all();a[f.stem]=v;planeChecks+=1
        scale=m.get('jointInputSampleScale107',4)
        assert len(a)==(25 if scale==8 else 23)and m['frameUnchangedDuringReadback']and m['curveCPUUploadEqualsGPU106']
        w,h=m['forward102']['canonicalSize'];cw,ch=w//4,h//4;dw,dh=m['forward102']['denseSize'];assert dw==w*2 and dh==h*2
        ls=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        baseline=[buffer(p/('canonical-'+n+'.f32'))for n in ['colour','identity','decision']];seg=curve_segments(p/'curve-segments106.f32')
        actual=[buffer(p/('curve-'+n+'.f32'))for n in ['colour','identity','decision','audit']];legacy=[buffer(p/('legacy106-'+n+'.f32'))for n in ['colour','identity','decision','audit']]
        jointLs,jointVis=ls,vis
        if scale==8:
            jointLs=np.zeros((4,5,dh,dw,4),np.float32);jointVis=np.zeros((4,dh,dw,4),np.float32)
            for part in [1,2]:jointLs[part,1]=np.flipud(a['D-part'+str(part)+'-meta'])
            for channel,name in enumerate(['rgba','meta','rest','uv']):jointLs[3,channel]=np.flipud(a['D-lid-'+name])
            jointVis[1:4]=buffer(p/'dense-three-part-visibility.f32').reshape(3,dh,dw,4)
        ref=apply(seg,jointLs,jointVis,*baseline,scale=scale);oldref=old_apply(seg,ls,vis,*baseline)
        for k in range(len(baseline[0])):
            cells+=1
            for label,got,want in [('107',actual,ref),('106',legacy,oldref)]:
                if not all(np.array_equal(got[j][k],want[j][k])for j in [0,1,2])or got[3][k,0]!=want[3][k,0]:mismatch.append({'frame':e['frame'],'cell':k,'variant':label,'gpuAudit':got[3][k].tolist(),'cpuAudit':want[3][k].tolist()})
        c,ids,dec,audit=actual;bc,bi,bd=baseline
        for k in np.flatnonzero(audit[:,0]==3):
            q=int(round(audit[k,2]))-1;yy,xx=divmod(q,jointLs.shape[3]);lo,hi=contributions(jointLs,jointVis,yy,xx)
            assert lo[2]>max(hi[0],hi[1],hi[3])and np.array_equal(c[k,:3],jointLs[3,0,yy,xx,:3])and ids[k,2]==jointLs[3,1,yy,xx,0]
            if bi[k,0]in [1,4]:jointProof.append({'frame':e['frame'],'sourceId':m['sourceId'],'canonicalXY':[k%cw,k//cw],'priorIdentity':bi[k].tolist(),'jointIdentity':ids[k].tolist(),'sampleXY':[xx,yy],'sampleScale':scale,'sourceUVPrimitive':jointLs[3,3,yy,xx].tolist(),'partLower':lo.tolist(),'partUpper':hi.tolist(),'sourceRGBlinear':c[k,:3].tolist()})
        untouched=audit[:,0]!=3;assert np.array_equal(c[untouched],bc[untouched])and np.array_equal(ids[untouched],bi[untouched])
        for prefix in ['B','C','F']:
            hc,ho,proof=hair(a[prefix+'-EyeRGBA'],a[prefix+'-EyeOwner'],a['S4-rgba'],a['S4-meta']);assert np.array_equal(hc,a[prefix+'-FinalRGBA'])and np.array_equal(ho,a[prefix+'-FinalOwner']);allHair+=len(proof)
        for role,outputRole in [(1,2),(4,5)]:paletteOutside+=sum(tuple(x)not in pal[role]for x in rgb8(a['F-EyeRGBA'][a['F-EyeOwner'][...,0]==outputRole,:3]))
        dvis=buffer(p/'dense-lid-visibility.f32').reshape(dh,dw,4);normalProof=buffer(p/'normal-skin-query-proof.f32').reshape(h,w,2,4);denseProof=buffer(p/'dense-skin-query-proof.f32').reshape(dh,dw,2,4)
        validDense=np.flipud(a['D-lid-meta'])[...,0]>0
        assert np.array_equal(dvis[...,2][validDense],np.flipud(a['D-lid-meta'])[...,0][validDense]),'dense RT/canonical orientation or source mismatch'
        for k in np.flatnonzero(np.isin(legacy[3][:,0],[-1,2])):
            yy,xx=divmod(int(k),cw);eyes={round(float(s[0,3]))for s in seg if intersects(s[0,:2],s[1,:2],[xx,yy])};oldraw=ls[3,0,yy*4:yy*4+4,xx*4:xx*4+4,3]
            dl=a['D-lid-rgba'][dh-(yy+1)*8:dh-yy*8,xx*8:xx*8+8];dm=a['D-lid-meta'][dh-(yy+1)*8:dh-yy*8,xx*8:xx*8+8]
            # Native RT planes use bottom-up; canonical buffers use top-down.
            dv=dvis[yy*8:yy*8+8,xx*8:xx*8+8];draw=(dl[...,3]>0)&(dm[...,0]>0)&np.isin(np.rint(dm[...,2]).astype(int),list(eyes))
            gap={'frame':e['frame'],'stage':e['testStage82'],'canonicalXY':[xx,yy],'prior106Audit':legacy[3][k].tolist(),'normalRawSamples':int((oldraw>0).sum()),'denseRawSamples':int(draw.sum()),'denseCertainVisibleSamples':int((np.flipud(draw)&(dv[...,0]>0)&(dv[...,0]==dv[...,1])).sum()),'sourceId':m['sourceId']}
            gap['interpretation']='4x misses pigment sampled at8x'if gap['normalRawSamples']==0 and gap['denseRawSamples']>0 else'no pigment witness at either captured density; continuous absence not proven'if gap['normalRawSamples']==0 else'pigment exists; use joint visibility/face witness'
            proofs=[]
            for sy in range(4):
                for sx in range(4):
                    atY,atX=yy*4+sy,xx*4+sx;v=vis[3,atY,atX];q=normalProof[atY,atX]
                    if ls[3,0,atY,atX,3]>0 and v[1]<=0 and q[0,0]>0:proofs.append({'sampleXY':[atX,atY],'blocker':q[0].tolist(),'hitUVUpperAlphaCandidateDepth':q[1].tolist(),'candidateUVPrimitive':ls[3,3,atY,atX].tolist(),'candidateRest':ls[3,2,atY,atX].tolist()})
            gap['normalFaceQueryWitnesses']=proofs;gaps.append(gap)
        role=ids.reshape(ch,cw,4);parts={}
        for eye in [1,2]:
            parts[str(eye)]={str(r):{'cells':int(((role[...,0]==r)&(role[...,1]==eye)).sum()),'components4':components((role[...,0]==r)&(role[...,1]==eye))}for r in [1,4,6]}
        counts={str(r):int((ids[:,0]==r).sum())for r in [1,4,6]};motion=m['motion82'];row={'frame':e['frame'],'stage':e['testStage82'],'index':e['stageIndex82'],'sourceId':m['sourceId'],'parts':parts,'counts':counts,'requestedClose':motion.get('requestedClose',motion.get('actualClose107')),'evaluatedError':motion.get('evaluatedVsOwnedBakeMax',motion.get('evaluatedCloseError107')),'audit':{str(k):int((audit[:,0]==k).sum())for k in [-4,-3,-2,-1,0,3,4]}}
        rows.append(row)
        if 'measured-phase'in e['testStage82']:variants.setdefault(e['testStage82'],[]).append(signature(role,c.reshape(ch,cw,4),m['forward102']['nativeRegistration']['bounds'][:2]))
        if e['testStage82']=='evaluated-blink106':reopen[e['stageIndex82']]=[a['F-EyeRGBA'],a['F-EyeOwner']]
        if e['testStage82'].startswith('partial-hair-'):hairStates[e['stageIndex82']]={'rgba':a['F-FinalRGBA'],'owner':a['F-FinalOwner'],'eye':a['F-EyeRGBA'],'meta':a['S4-meta']}
        for prefix in ['B','C','F']:rgba(a[prefix+'-FinalRGBA']).save(out/f'{prefix}-final-frame{e["frame"]}-1x.png')
        rgba(a['F-EyeRGBA']).save(out/f'F-eye-frame{e["frame"]}-1x.png')
        if e['testStage82']=='evaluated-blink106'or e['testStage82'].startswith('partial-hair-')or(e['testStage82']in ['open-turn','closed-turn']and e['stageIndex82']in [0,4,9]):boards.append((row,[rgba(a[k])for k in ['C-EyeRGBA','F-EyeRGBA','F-FinalRGBA']]))
    assert not mismatch,mismatch[:8]
    board=Image.new('RGB',(1200,135+len(boards)*215),'#20252c');dr=ImageDraw.Draw(board);dr.text((20,10),'107 실제 GPU · 같은 표본의 세 파츠 가시성 / 제품77 유지',font=font(24),fill='white')
    for x,t in zip([20,420,820],['106 무조건 홍채·흰자 보호','107 곡선 위치 공동 가시성','107 + 실제 외부 머리 가림']):dr.text((x,65),t,font=font(17),fill='#c4d9e8')
    for j,(row,ims)in enumerate(boards):
        y=115+j*215;dr.text((20,y),str(row['frame'])+' / '+row['stage']+' / '+str(row['requestedClose']if row['requestedClose']is not None else row['index']),font=font(17),fill='white')
        for x,im in zip([20,420,820],ims):
            zoom=min(18,365//im.width,165//im.height);big=im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST);board.paste(big,(x,y+31),big)
    board.save(out/'JOINT_VISIBILITY107.png')
    reopened=all(np.array_equal(a,b)for a,b in zip(reopen[0],reopen[8]))
    hairSummary={'captured':len(hairStates)}
    if len(hairStates)==3:
        hairSummary.update({'offHasHairSamples':bool((hairStates[1]['meta'][...,0]>0).any()),'offFinalEqualsEye':bool(np.array_equal(hairStates[1]['rgba'],hairStates[1]['eye'])),'onRestoredRGBA':bool(np.array_equal(hairStates[0]['rgba'],hairStates[2]['rgba'])),'onRestoredOwner':bool(np.array_equal(hairStates[0]['owner'],hairStates[2]['owner']))})
    summary={'actualGPUFrames':len(rows),'jointInputSampleScale':scale,'captureRunComplete':not bool(state.get('error')),'captureRunError':state.get('error'),'CPUReferenceCells':cells,'CPUGPUMismatch':len(mismatch),'sameSourcePlaneChecks':planeChecks,'jointOverridesPriorIrisWhite':len(jointProof),'sourcePaletteOutsideIrisWhite':paletteOutside,'hairSourceDepthCoverageDecisionsExact':allHair,'samePoseReopenExact':reopened,'hairOnOff':hairSummary,
             'phaseIdentityVariants':{k:len({tuple(sorted(s))for s in seq})for k,seq in variants.items()},'tests':tests(),'productDefault':77,'finiteLidPalettePending':True,'fullFaceRegionResolverPending':True,'frames':rows}
    save('RESULT107.json',summary);save('JOINT_SOURCE_PROOFS107.json',jointProof);save('DENSITY_OCCLUSION107.json',gaps);save('MISMATCHES107.json',mismatch)
    print(json.dumps({k:v for k,v in summary.items()if k!='frames'},ensure_ascii=False));print('FOCUS',json.dumps([r for r in rows if r['stage']=='evaluated-blink106'or r['stage'].startswith('partial-hair-')],ensure_ascii=False))
if __name__=='__main__':main()
