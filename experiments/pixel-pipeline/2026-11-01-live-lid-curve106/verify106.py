"""Same-input source, external occlusion, residual-gap and preservation audit.
Reads the completed106 capture only. No Unity or new renderer execution.
Curve intersections are the registered geometric reference, not an authored
pigment boundary or an automatically approved target eye design.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent; R=H.parent
sys.path.insert(0,str(R/'forward-eye102'))
from analyse102 import load,buffer,rgba,font,components
from analyse_capture68 import plane,rgb8
from analyse106 import curve_segments,signature
from curve_reference106 import intersects
F=np.float32

def save(name,x):
    (H/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def hair(c,o,hc,hm):
    """Literal ComposeForward102 hair rule, float32 sum and traversal order."""
    out=c.copy(); ids=o.copy(); proofs=[]
    for y in range(c.shape[0]):
        for x in range(c.shape[1]):
            coverage=F(0);best=F(-1);pick=None
            for sy in range(4):
                for sx in range(4):
                    q=hm[y*4+sy,x*4+sx];v=hc[y*4+sy,x*4+sx]
                    if q[0]>0 and q[3]>0 and v[3]>0 and(o[y,x,2]<=0 or q[0]<F(o[y,x,2]-F(3e-5))):
                        w=F(np.clip(q[3],0,1));coverage=F(coverage+w)
                        if w>best:best=w;pick=(sy,sx)
            if coverage>=8:
                sy,sx=pick;q=hm[y*4+sy,x*4+sx];v=hc[y*4+sy,x*4+sx]
                out[y,x]=[*v[:3],1];ids[y,x]=[round(float(q[1])),round(float(q[2])),q[0],0]
                proofs.append({'xyROIbottom':[x,y],'sample':[sx,sy],'coverage':float(coverage),'sourceDepth':float(q[0]),'priorOwnerDepth':float(o[y,x,2])})
    return out,ids,proofs

def main():
    state=load(sorted((H/'capture').glob('STATE106-*'))[-1]); result=load(H/'RESULT106.json')
    assert state['stage']=='finished'and state['PlayExited']and state['observerRemoved']
    before=load(H/'capture/CURRENT102.json'); after=load(H/'capture/POST102.json')
    assert not after['playing']and not after['transitioning']and not after['compiling']
    assert before['dirty']==after['dirty']and before['scenes']==after['scenes']
    assert before['input']==after['input']
    comparisons={k:before[k]==after[k]for k in ['runInBackground','playerRunInBackground','options','optionsEnabled','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','buildScenes','paused','domain']}
    assert all(comparisons.values())
    asset=load(H/'ASSET106.json'); repo=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game'); checks=[]
    for row in asset['protected32']:
        actual=hashlib.sha256((repo/row['path']).read_bytes()).hexdigest();assert actual==row['sha'];checks.append(row['path'])
    assert hashlib.sha256((repo/asset['newAsset']).read_bytes()).hexdigest()==asset['newSourceSHA256']
    rows=[];phaseSamples={};boards=[];reopen={};allHair=0;sourceChecks=0;phaseUVChanges=[]
    for entry in state['sequencePackets']:
        p=Path(entry['output']); m=load(p/'RAW_MANIFEST.json'); a={}
        for f in p.glob('*.plane'):
            hd,v=plane(f);assert hd['sourceId']==m['sourceId']and hd['frameIndex']==entry['frame']and hd['renderSerial']==entry['serial']and np.isfinite(v).all();a[f.stem]=v;sourceChecks+=1
        assert len(a)==15 and m['curveCPUUploadEqualsGPU106']and m['frameUnchangedDuringReadback']
        assert m['forwardFrame']==m['frameIndex']==m['forward102']['curves106']['updatedFrame']
        counts=[]
        for prefix in ['B','F']:
            c,o,proof=hair(a[prefix+'-EyeRGBA'],a[prefix+'-EyeOwner'],a['S4-rgba'],a['S4-meta'])
            assert np.array_equal(c,a[prefix+'-FinalRGBA'])and np.array_equal(o,a[prefix+'-FinalOwner'])
            counts.append(len(proof));allHair+=len(proof)
        w,h=m['forward102']['canonicalSize'];cw,ch=w//4,h//4
        layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        bi=buffer(p/'canonical-identity.f32');out=buffer(p/'curve-colour.f32');ids=buffer(p/'curve-identity.f32');audit=buffer(p/'curve-audit.f32')
        segments=curve_segments(p/'curve-segments106.f32');cells=[];selected={};reasonCounts=collections.Counter()
        for y in range(ch):
            for x in range(cw):
                k=y*cw+x;touched=sorted({round(float(s[0,3]))for s in segments if intersects(s[0,:2],s[1,:2],[x,y])})
                if not touched:continue
                evidence={}
                for eye in touched:
                    sl=np.s_[y*4:y*4+4,x*4:x*4+4];col=layers[3,0][sl];meta=layers[3,1][sl];vv=vis[3][sl]
                    raw=(col[...,3]>0)&(meta[...,0]>0)&(np.rint(meta[...,2])==eye)
                    evidence[str(eye)]={'rawSamples':int(raw.sum()),'rawAlpha':float(col[...,3][raw].sum()),
                      'certainVisibleSamples':int((raw&(vv[...,0]>0)&(vv[...,0]==vv[...,1])).sum()),
                      'uncertainSamples':int((raw&(vv[...,0]!=vv[...,1])).sum()),'fullyOccludedSamples':int((raw&(vv[...,1]<=0)).sum())}
                flag=round(float(audit[k,0]));reason='selected-source'if flag==3 else'protected-iris-white'if flag==2 else'uncertain-colour-tie'if flag==-2 else'conflicting-owners'if flag==-3 else'no-captured-pigment'if all(v['rawSamples']==0 for v in evidence.values())else'unknown-visibility'if any(v['uncertainSamples']for v in evidence.values())else'certain-face-occlusion'
                reasonCounts[reason]+=1
                row={'canonicalXYtop':[x,y],'curveEyeIds':touched,'reason':reason,'audit':audit[k].tolist(),'baselineIdentity':bi[k].tolist(),'outputIdentity':ids[k].tolist(),'sourceEvidence':evidence}
                cells.append(row)
                if flag==3:
                    at=int(round(audit[k,2]))-1;yy,xx=divmod(at,w)
                    selected[(int(round(ids[k,1])),x,y)]={'sampleXY':[xx,yy],'sourceUVPrimitive':layers[3,3,yy,xx].tolist(),'sourceRGBlinear':layers[3,0,yy,xx,:3].tolist(),'RGB8':rgb8(out[k,:3]).tolist()}
        canonical=ids.reshape(ch,cw,4);bcanonical=bi.reshape(ch,cw,4)
        row={'frame':entry['frame'],'stage':entry['testStage82'],'index':entry['stageIndex82'],'sourceId':m['sourceId'],'reasons':dict(reasonCounts),'cells':cells,'hairDecisionsExact':counts,
             'perEyeCanonical':{str(e):{'beforeLidComponents4':components((bcanonical[...,0]==6)&(bcanonical[...,1]==e)),
             'afterLidComponents4':components((canonical[...,0]==6)&(canonical[...,1]==e)),
             'curveCells4':components(np.array([[any(round(float(s[0,3]))==e and intersects(s[0,:2],s[1,:2],[x,y])for s in segments)for x in range(cw)]for y in range(ch)]))}for e in (1,2)}}
        rows.append(row)
        if entry['testStage82']=='evaluated-blink106':reopen[entry['stageIndex82']]=[a['F-EyeRGBA'],a['F-EyeOwner']]
        if 'measured-phase'in entry['testStage82']:
            bounds=m['forward102']['nativeRegistration']['bounds']; sig={}
            for (owner,x,y),v in selected.items():sig[(owner,int(x+bounds[0]),int(y+bounds[1]))]=v
            phaseSamples.setdefault(entry['testStage82'],[]).append((entry['frame'],sig))
        if entry['frame']in [99,101,107,192]:
            boards.append((row,ids,bi,(cw,ch),segments,a['F-EyeRGBA'],a['F-FinalRGBA']))
    for stage,seq in phaseSamples.items():
        base=seq[0][1]
        for frame,sig in seq[1:]:
            for k in base.keys()&sig.keys():
                if base[k]['RGB8']!=sig[k]['RGB8']:phaseUVChanges.append({'stage':stage,'frame':frame,'localEyeXY':list(k),'before':base[k],'after':sig[k]})
    reopenEqual=all(np.array_equal(a,b)for a,b in zip(reopen[0],reopen[8]));assert reopenEqual
    # The diagnostic reports missing source witnesses; it does not invent them.
    board=Image.new('RGB',(1420,160+len(boards)*315),'#20252c');d=ImageDraw.Draw(board)
    d.text((20,12),'106 · 남은 분절 원인 / 곡선은 skin-ring 기하 기준, 색소 정답이 아님',font=font(25),fill='white')
    d.text((20,55),'초록: 실제 색소 선택 / 파랑: 홍채·흰자 보호 충돌 / 빨강: 해당 셀 표본 없음 / 주황: 실제 얼굴 가림',font=font(18),fill='#d9dfeb')
    for j,(row,ids,bi,shape,segments,eye,final)in enumerate(boards):
        y0=130+j*315;cw,ch=shape;sz=25
        d.text((20,y0-24),f"frame {row['frame']} · {row['stage']} · canonical x/y(top)",font=font(17),fill='white')
        for y in range(ch):
            for x in range(cw):
                k=y*cw+x;role=int(round(ids[k,0]));c='#53565e'if role==0 else'#ae84dc'if role==1 else'#f6e9d0'if role==4 else'#a97e5c'
                d.rectangle((20+x*sz,y0+y*sz,20+(x+1)*sz-1,y0+(y+1)*sz-1),fill=c,outline='#2b3038')
        colour={'selected-source':'#64f29b','protected-iris-white':'#58baff','no-captured-pigment':'#ff637b','certain-face-occlusion':'#ffb13e','unknown-visibility':'#fada66'}
        for cell in row['cells']:
            x,y=cell['canonicalXYtop'];d.rectangle((21+x*sz,y0+1+y*sz,18+(x+1)*sz,y0+(y+1)*sz-2),outline=colour.get(cell['reason'],'white'),width=2)
        for s in segments:d.line([(20+float(v[0])*sz,y0+float(v[1])*sz)for v in s],fill='#d9ffb3',width=2)
        for x,title,im in [(565,'실제 GPU · 머리 가림 전',rgba(eye)),(975,'실제 GPU · 머리 가림 후',rgba(final))]:
            d.text((x,y0),title,font=font(17),fill='white');im=im.resize((im.width*16,im.height*16),Image.Resampling.NEAREST);board.paste(im,(x,y0+35),im)
        d.text((20,y0+max(235,ch*sz+5)),str(row['reasons']),font=font(13),fill='#c9d6df')
    board.save(H/'review/RESIDUAL_GAPS106.png')
    consoleBefore=load(H/'capture/Capture106_CONSOLE_BEFORE.json')['data'];consoleAfter=load(H/'capture/Post106_CONSOLE_AFTER.json')['data']
    assert consoleBefore['errorCount']==consoleAfter['errorCount']==0
    verification={'planeSourceChecks':sourceChecks,'hairCoverageDepthColourOwnerDecisionsExact':allHair,'hairFormula':'same102: per-sample front depth, coverage >=8/16, first strictly maximum alpha source; no eye feedback',
      'sameFrameReopenEyeRGBAOwnerExact':reopenEqual,'phaseNativeUVRGBChanges':phaseUVChanges,'allStateNative46Exact':True,'additionalAssetImporterUnavailable':result['restoration']['unavailable'],
      'dirtyListExact':len(after['dirty']),'scenesExact':True,'inputObjectAndJSONDevicesExact':True,'settingsComparisons':comparisons,'protectedFileHashesExact':len(checks),
      'newComputeSHA256':asset['newSourceSHA256'],'productDefault':77,'notAdoptedReasons':['partial Close and rotation contain disconnected lid components','source reference is registered skin-ring upper chain, not native pigment contour','finite native lid palette and face source-region resolver remain unresolved'],
      'postUTC':after['utc'],'postEdit':True,'consoleErrorsBeforeAfter':[consoleBefore['errorCount'],consoleAfter['errorCount']],'allocatedCounterName':'UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong (not physical WS)','allocatedDeltaBytes':state['afterMemory']['allocated']-state['beforeMemory']['allocated'],
      'gapScope':'certainty within captured4x4 native samples only; no captured pigment does not prove continuous source pigment absent','frames':rows}
    save('VERIFICATION106.json',verification)
    print(json.dumps({k:v for k,v in verification.items()if k not in ['frames','phaseNativeUVRGBChanges']},ensure_ascii=False))
    print('PHASE RGB CHANGES',json.dumps(phaseUVChanges[:3],ensure_ascii=False))
if __name__=='__main__':main()
