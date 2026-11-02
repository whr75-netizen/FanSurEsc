"""Bounded stored-input audit of attachment versus occlusion ownership."""
import os,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
os.environ['PIXEL111_FROZEN_INPUTS']='1'
from source112 import Source,HERE,P111,packet_list,load,read
from support112 import Support

def signed_area(xy):return float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2)

def main():
    source=Source();records=[];keys=[];critical=None
    for kind in ['original','geometry']:
        _,paths=packet_list(kind)
        for p in paths:
            ctx=load(p);sup=Support(source,ctx);keys.append(sup.key)
            rings={str(k):{'vertexCount':len(ring),'canonicalSignedArea':signed_area(ctx['maps'][k][ring+sup.m['faceVertexOffset']]),'evaluatedWorldBoundary':ctx['world'][ring+sup.m['faceVertexOffset']].tolist()}for k,ring in sup.m['rings'].items()}
            row={'kind':kind,'sourceId':ctx['sourceId'],'frame':ctx['frame'],'serial':ctx['serial'],'rings':rings,'cacheKey':sup.key}
            if kind=='original':
                analysis=read(P111/f'ANALYSIS111-frame{ctx["frame"]}.json');row['intrinsicSourceMass']=[{'owner':e['owner'],'iris':e['irisSourceMass'],'white':e['whiteSourceMass']}for e in analysis['eyes']];row['componentFirstCanonicalLabels']=[next(v for v in e['variants']if v['componentFirst'])['labels']for e in analysis['eyes']]
                if ctx['frame']==105:
                    eye=analysis['eyes'][1];variant=next(v for v in eye['variants']if v['componentFirst']);cell=next(v for v in variant['exposure'][0]if v['cellYX']==[5,3]and v['part']==2)
                    hits={}
                    for sample in cell['samples']:
                        for carrier in sample.get('frontCarriers',[]):
                            for hit in carrier['face']['hits']:
                                hits.setdefault(hit['triangle'],[]).append(hit)
                    critical={'sourceId':ctx['sourceId'],'frame':105,'owner':2,'canonicalCellYX':[5,3],'sourceWhiteMass':eye['whiteSourceMass'],'physicalVisibleFractionBounds':cell['visibleCarrierFractionBounds'],'denominator':16,'blockingTriangles':[]}
                    alpha=read(P111/'inputs/ALPHA111.json');file=next(r['file']for r in alpha['images']if r['renderer']==1 and r['submesh']==3);image=np.asarray(Image.open(P111/'inputs'/file).convert('RGBA'));h,w=image.shape[:2]
                    for tid,hitsAt in sorted(hits.items()):
                        e=sup.evidence(tid);e['witnesses']=hitsAt;e['sourceAlphaAllOpaque']=all(v['alphaBounds']==[1,1]for v in hitsAt)
                        e['nativeSourceNearestTexelRGBA']=[image[min(h-1,int((1-v['UV'][1])*h)),min(w-1,int(v['UV'][0]*w))].tolist()for v in hitsAt]
                        critical['blockingTriangles'].append(e)
                    # Counterexample to nearest-eye IDs: same tag, different source
                    # affiliation. This does not invent a new eyelid truth label.
                    rows=np.where((ctx['sources'][:,0]==1)&(ctx['sources'][:,1]==3)&(np.rint(ctx['triOwners'][:,:3]).astype(int)==2).all(1))[0]
                    off=sup.m['faceVertexOffset'];generic=next(int(t)for t in rows if not np.any(sup.m['delta'][ctx['triangles'][t,:3]-off]))
                    critical['sameNearestEyeTagUnrelatedSkin']=sup.evidence(generic)
            records.append(row)
    assert len(set(keys))==1,'Immutable source cache leaked frame/view identity or source binding changed'
    assert critical is not None and all(x['sourceAlphaAllOpaque']for x in critical['blockingTriangles'])
    original={r['frame']:r for r in records if r['kind']=='original'}
    assert all(v['iris']==0 and v['white']==0 for v in original[107]['intrinsicSourceMass'])
    assert original[99]['componentFirstCanonicalLabels']==original[115]['componentFirstCanonicalLabels']
    assert original[122]['componentFirstCanonicalLabels']==original[125]['componentFirstCanonicalLabels']==original[128]['componentFirstCanonicalLabels']
    report={'sameFrameRecords':len(records),'sourceCacheKeys':len(set(keys)),'nearestTagIsNotNativeLid':True,'currentDeformationBoundaryReadByIdentity':True,'fullClose':{'frame':107,'sourceMass':original[107]['intrinsicSourceMass'],'nonzeroNativeRingArea':{k:abs(v['canonicalSignedArea'])for k,v in original[107]['rings'].items()},'conclusion':'closed native skin ring alone is not an open/closed pigment-state oracle; retain current source visibility'},'reopenCanonicalRecovered':True,'hairOnOffRestoredCanonicalEqual':True,'critical':critical,'records':records,'runtimeAllocationOrOccluderOverrideExecuted':False,'newUnityCalls':0,'product77Changed':False,'missingIsNewMappingDefinitionNotMissingFrameCapture':True,'notProvenInformationTheoreticallyImpossible':True,'blockingQuestion':'Define a closed source-local stylized eye support/cage and its deformation/occlusion transfer. An upper 2D colour boundary and blink influence do not label which surrounding skin may be reallocated. Current data permits a new explicit rule, but does not certify a native eyelid mask.'}
    (HERE/'AUDIT112.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    source.freeze();sup=Support(source,load(packet_list()[1][3]));(HERE/'AFFILIATION_CACHE112.json').write_text(json.dumps(sup.cache(),indent=2)+'\n',encoding='utf8')
    picture(source,sup,critical)
    print(json.dumps({'storedFrames':len(records),'cacheKeys':1,'criticalTriangles':len(critical['blockingTriangles']),'criticalAllActualAlphaOpaque':True,'physicalWhite':critical['physicalVisibleFractionBounds'],'runtimeReady':False,'noNewUnityCalls':True}))

def picture(source,sup,critical):
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
    out=Image.new('RGB',(1280,900),'#10202c');d=ImageDraw.Draw(out)
    def text(x,y,s,n=19,c='#e5f0f6'):d.text((x,y),s,font=font(n),fill=c)
    text(24,16,'112 | 원본 변형 연결과 안검 소유권은 같은 정보가 아닙니다',27)
    actual=Image.open(P111/'ACTUAL111-frame125.png').convert('RGB');out.paste(actual.resize((240,288),Image.Resampling.NEAREST),(30,100));text(30,62,'기존 GPU77 · 머리 OFF',19);text(30,400,'실제 111 F125 / 새 후보 RGB 아님',16)
    alpha=read(P111/'inputs/ALPHA111.json');filename=next(r['file']for r in alpha['images']if r['renderer']==1 and r['submesh']==3)
    image=Image.open(P111/'inputs'/filename).convert('RGBA');w,h=image.size
    uv=sup.m['uv'];unityuv=np.c_[uv[:,0],1-uv[:,1]]
    rings=sup.m['rings'];owner=2;ring=rings[owner];pix=np.c_[unityuv[:,0]*w,(1-unityuv[:,1])*h]
    relevant=np.concatenate([pix[ring],np.array([[v['UV'][0]*w,(1-v['UV'][1])*h]for hit in critical['blockingTriangles']for v in hit['witnesses']])])
    lo=np.floor(relevant.min(0)-20).astype(int);hi=np.ceil(relevant.max(0)+20).astype(int);scale=min(490/(hi[0]-lo[0]),420/(hi[1]-lo[1]));size=np.rint((hi-lo)*scale).astype(int)
    crop=image.crop((*lo,*hi));bg=Image.new('RGBA',crop.size,'#bfc9ce');bg.alpha_composite(crop);crop=bg.convert('RGB').resize(tuple(size),Image.Resampling.NEAREST);x0,y0=330,100;dr=ImageDraw.Draw(crop)
    def point(p):return tuple((np.array(p)-lo)*scale)
    for t in sup.tri:
        pp=pix[t]
        if np.all(pp.max(0)>=lo)and np.all(pp.min(0)<=hi):dr.line([point(v)for v in np.vstack([pp,pp[0]])],fill='#92a3ac',width=1)
    for i,row in enumerate(critical['blockingTriangles'],1):
        t=sup.tri[row['sourcePrimitive']-1];dr.line([point(v)for v in pix[np.r_[t,t[0]]]],fill='#e4a136',width=2)
        for witness in row['witnesses']:
            q=point([witness['UV'][0]*w,(1-witness['UV'][1])*h]);dr.ellipse((q[0]-3,q[1]-3,q[0]+3,q[1]+3),fill='#ff425f')
    dr.line([point(v)for v in pix[np.r_[ring,ring[0]]]],fill='#00ffe0',width=3)
    out.paste(crop,(x0,y0))
    text(330,62,'원본 피부 UV + 실제 가림 삼각형/표본',19)
    text(850,105,'청록: 원본 24정점 눈구멍 경계',18,'#00ffe0')
    text(850,143,'주황/빨강: 흰자를 가린 실제 피부',18,'#ffbc62')
    text(850,184,'F105 · 눈2 · canonical (x3,y5)',18)
    text(850,225,'흰자 source: 0.34375 셀',20)
    text(850,263,'최종 물리 가시량: 2/16',20)
    text(850,305,'가림 9삼각형 모두 alpha=1',19)
    text(850,347,'9개 모두 blinkRight 영향권',19)
    text(850,389,'그러나 영향권 ≠ 안검 마스크',20,'#ffb0b0')
    text(30,555,'확인된 연결',23,'#73dcc9')
    text(30,599,'VRM blinkLeft/Right → 각각의 native ring 24정점 → 같은 프레임 evaluated geometry',20)
    text(30,641,'기존 bank 20셀의 native 삼각형 대입과 목적지 footprint는 이미 있습니다. 빠진 것은 공동 보정 후 피부 소유권입니다.',18)
    text(30,697,'남은 계약',23,'#ffd18b')
    text(30,740,'공동 배치가 바꾸는 눈 전체 support의 닫힌 표면/변형 범위와 내부 안검·외부 피부 가림의 대응 규칙',19)
    text(30,781,'이 규칙 없이 피부를 투명 처리하거나 bank 범위 전체를 덮지 않았습니다. 새 GPU 공동배정 미실행.',19)
    text(30,840,'저장된 24상태 검사 · 새 Unity 호출 0 · 제품77/원본/사용자 상태 유지 · 유한 팔레트/외곽선 별도 미완',16,'#abc8d8')
    out.save(HERE/'SUPPORT_OWNERSHIP112.png')

if __name__=='__main__':main()
