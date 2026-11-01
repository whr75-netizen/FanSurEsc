from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent
if '--direct' in sys.argv:H=H/'direct'
sys.path.insert(0,str(R/'forward-eye102'))
from analyse102 import buffer,rgba,font,load
from selection102 import cell
from analyse_capture68 import plane

def main():
    state=load(sorted(H.glob('STATE102-*'))[-1])
    assert state['stage']=='finished'and state['PlayExited']and not state.get('error')and not state.get('restorationError')
    unavailable=[r for r in state['nativeComparisons72']if r['equal']is None]
    assert not any(r['equal']is False for r in state['nativeComparisons72'])
    assert all(r['type']=='UnityEditor.AssetImporter'and r['path']=='ProjectSettings/ProjectSettings.asset'for r in unavailable)
    board=Image.new('RGB',(1400,1040),'#20252c');draw=ImageDraw.Draw(board)
    draw.text((20,10),'105 · 안검 원본 지지 → 실제 가림 → 셀 선택 (제품77 유지)',font=font(25),fill='white')
    rows=[];details=[];mismatches=[]
    for j,e in enumerate(state['sequencePackets']):
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json')
        assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()
        w,h=m['forward102']['canonicalSize'];layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4)
        vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        decision=buffer(p/'canonical-decision.f32').reshape(h//4,w//4,4)
        raw=layers[3,0,:,:,3];covered=(layers[3,1,:,:,0]>0)&(raw>0)
        v=vis[3,:,:,0];vu=vis[3,:,:,1];owners=np.rint(layers[3,1,:,:,2]).astype(int)
        cells=[];rawgrid=raw.reshape(h//4,4,w//4,4).sum((1,3));vg=v.reshape(h//4,4,w//4,4).sum((1,3))
        for y in range(h//4):
            for x in range(w//4):
                ref=cell(layers,vis,x,y);code=-1 if ref['winner']<0 else[1,4,6,0][ref['winner']]
                if code!=round(float(decision[y,x,0])):mismatches.append({'frame':e['frame'],'xy':[x,y]})
                if rawgrid[y,x]>0:
                    cells.append({'canonicalXY':[x,y],'rawSourceLidAlpha':float(rawgrid[y,x]),'afterQueryLidAlpha':float(vg[y,x]),
                       'sourceOwners':sorted(set(owners[y*4:y*4+4,x*4:x*4+4][covered[y*4:y*4+4,x*4:x*4+4]].tolist())),
                       'GPUrole':int(round(decision[y,x,0])),'selection':ref})
        row={'frame':e['frame'],'sourceId':m['sourceId'],'requestedClose':m['motion82']['requestedClose'],
             'evaluatedSourceError':m['motion82']['evaluatedVsOwnedBakeMax'],'canonicalSize':[w,h],
             'rawLidSamples':int(covered.sum()),'rawAlphaSum':float(raw[covered].sum()),
             'afterNativeSkinQueryAlphaSum':float(v.sum()),'queryUnknownSamples':int((v!=vu).sum()),
             'sampleCullOrOcclusionLoss':float((raw-v).sum()),'positiveSourceLogicalCells':int((rawgrid>0).sum()),
             'positiveVisibleLogicalCells':int((vg>0).sum()),'selectedLidCells':int((decision[...,0]==6).sum()),
             'perEye':[{'eye':eye,'rawSourceSamples':int((covered&(owners==eye)).sum()),
                        'rawAlphaSum':float(raw[covered&(owners==eye)].sum()),
                        'queryVisibleAlphaSum':float(v[owners==eye].sum())}for eye in (1,2)]}
        rows.append(row);details.append({'frame':e['frame'],'sourceId':m['sourceId'],'cells':cells})
        yy=70+j*300;draw.text((20,yy),f'frame {e["frame"]} · evaluated Close {row["requestedClose"]} · 안검 선택 {row["selectedLidCells"]}셀',font=font(20),fill='white')
        masks=[]
        for a in (raw,v):
            rgb=np.zeros((h,w,4),np.uint8);rgb[...,:3]=np.rint(np.clip(a,0,1)[...,None]*255).astype(np.uint8);rgb[...,3]=255
            masks.append(Image.fromarray(rgb))
        chosen=np.zeros((h//4,w//4,4),np.uint8);chosen[...,3]=255;chosen[decision[...,0]==6,:3]=[255,206,90]
        masks.append(Image.fromarray(chosen));eye=plane(p/'F-EyeRGBA.plane')[1];masks.append(rgba(eye))
        for i,(im,title)in enumerate(zip(masks,['native 안검 알파(가시화)','Query 후 알파(가시화)','최종 안검 label','실제 격리 GPU 출력'])):
            scale=min(14,315//im.width,185//im.height);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            board.paste(im,(20+i*345,yy+38),im);draw.text((20+i*345,yy+230),title,font=font(16),fill='#bcd5e1')
        rgba(eye).save(H/f'eye-frame{e["frame"]}-1x.png')
    assert len(rows)==3 and not mismatches
    result={'frames':rows,'CPUReferenceMismatches':mismatches,'productDefault':77,'newShaderChanges':0,
            'finding':'Per-cell feature/canvas majority is still an area sampler. It does not impose connected closed-lid curve support. Diagnose source/culling loss separately from post-Query area rejection.',
            'restoration':{'PlayExited':state['PlayExited'],'nativeExact':sum(r['equal']is True for r in state['nativeComparisons72']),
             'nativeUnavailable':unavailable,'unavailableMeaning':'Temporary importer wrapper expired; actual PlayerSettings is separately exact. No full 47/47 claim.',
             'input':state['editInputRestoration82'],'options':state['optionsRestored'],'time':state['timeRestored'],
             'pipeline':state['pipelineRestored'],'globals':state['globalRestoreErrors'],
             'RT':[state['beforeMemory']['renderTextureCount'],state['afterMemory']['renderTextureCount']],
             'allocatedBytes':[state['beforeMemory']['allocated'],state['afterMemory']['allocated']]}}
    (H/'RESULT105.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    (H/'CELLS105.json').write_text(json.dumps(details,indent=2,ensure_ascii=False),encoding='utf-8')
    draw.text((20,995),'관측만 수행. 면적 표본 수와 특징 형태 계약은 다르며, 6+2셀 목표나 고정 셀 수를 추가하지 않았습니다.',font=font(19),fill='#f4c880')
    board.save(H/'CLOSED_LID_CAUSE105.png')
    print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
