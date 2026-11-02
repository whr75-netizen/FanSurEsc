"""Compact evidence/patch index. No Unity calls or Library uploads."""
from pathlib import Path
import json,hashlib,difflib,collections
from PIL import Image,ImageDraw,ImageFont
from paths114 import H,folder
from trace114 import read
def main():
    source=folder('113');ties=read(H/'TIES114.json');pairs=read(H/'PAIRING_ALL114.json');trace=read(H/'TRACE_ALL114.json');pig=read(H/'PIGMENT114.json');check=read(H/'CHECK114.json')
    changes=[]
    for r in pairs['rows']:
        for c in r['issues']:
            if c['finalRGBAChanged']:changes.append({'frame':r['frame'],'mainXYBottomLeft':c['mainXY'],'part':c['part'],'oldFinal':c['oldFinal'],'pairedPointCPUFinal':c['correctPointFinal']})
    counts=collections.Counter((int(c['oldFinal']['role']),int(c['pairedPointCPUFinal']['role']))for c in changes)
    summary={'baselineCommit':'e4a84a88ff90f7dd3dc5380d8f24e95b660bcc38','UnityCalls':0,'Play':0,'AssetsChanged':False,'product77Changed':False,'GPU113ShaderChanged':False,'LibraryUpload':False,'tie':{'actualFrames':[103,111],'completeOptimaCount':2,'notEnumerationCap':True,'sourceWhiteKey':[2,4,215,79],'differingCanonicalXY':[[5,5],[6,5]],'currentSameKeyMasses':['1/64','11/64'],'runtime113HasOnlyKeyCountPenalty':True,'runtime113RelativeFormAndHistoryImplemented':False,'reused111And22FormWinner':1,'historyOnlyWinners':[0,1],'missingGeometryHandledAsNone':True},'sampling':{'oldSampleShiftXY':[.0625,.0625],'sourceDenseScale':8,'destinationExpectedSampleScale':4,'carrierNativeGeometryChecks':4320,'carrierMembershipMismatches':0,'matchedGPUFaceQueries':3190,'maxMatchedFaceIntervalError':0,'matchedGPUFinalCompositions':270,'maxMatchedNativeDepthResidualMetres':trace['matchedDepthMaxError'],'unpairedDepthError':None,'preparedPatchImported':False,'preparedPatchCompiled':False,'preparedPatchGPUExecuted':False,'counterfactualChanges':changes,'changesByRole':{str(k):n for k,n in counts.items()},'notAnAdoptedCompleteFix':True},'sourceLid':{'frame':107,'canonicalXY':[8,5],'sourceDenseMetaAndAlphaCount':0,'actualNativeUVBoundCurvePoints':6,'originalSourceBilinearAlphaRange':[min(p['sourceAlphaBilinear']for p in pig['rows'][0]['cases'][0]['points']),max(p['sourceAlphaBilinear']for p in pig['rows'][0]['cases'][0]['points'])],'intrinsicCPUVisibilityOfThesePoints':6,'rasterMappingGlobalMaxDeltaPixels':pig['rows'][0]['curveMapGlobalMaxDifferencePixels'],'rowUnchanged':5,'columnArcPixels':pig['rows'][0]['cases'][0]['actualUpperRow']['arcLength'],'runtimeCurvePointGPUQueriesRecorded':False,'interpretation':'Original UV pigment/current source geometry exist; dense8x pixel centres missed this thin endpoint. No invented RGB; original curve-point eligibility query is still required online.'},'policy12mm':{'coordinate':'world camera-depth difference, not source-local anatomical thickness','actorScaleInvariant':False,'uniformHalfVsDoubleScaleDifferentQueries':pairs['scaleChangesQueryVisibility'],'queriesExamined':pairs['knownGPUQueryComparisons'],'analyticalExistingGeometryOnly':True,'actualSideOrOtherScaleCapture':False,'example':{'frame':99,'mainXYBottomLeft':[222,222],'sourceSkinPrimitive':2726,'belongsToUnilateralRingComponent':True,'currentGapMetres':.015530814087185263,'halfScaleGapMetres':.0077654070435926315,'doubleScaleGapMetres':.031061628174370526},'thresholdRetuned':False},'singleDepthAudit':{'positiveEyeUsesPerFineDepths':16,'ownerDepthMinimumIsOutputMetadata':True,'holeSubsamplesRemainUnknownToHairTest':True,'nativeCoverageStillCutsOpaqueAssignedCell':True},'nextRuntimeScope':['Port existing111/2.2 source-form ranking among complete equal-primary solutions; no arbitrary scalar weight.','Use independent4x destination carrier matching S4 exactly; keep8x intrinsic source/IDs. Apply to a new clone shader and new unique capture sourceId/output folder only.','Before adopting the pairing correction, implement the documented selected-cell support/depth transport, with actual current native fragments and visibility intervals; do not use a guessed single cell depth.','Query current native UV-bound curve point visibility/alpha when dense source samples miss it; cached curve alone cannot prove current visibility.'],'ArgonQuestions':['2.3의 selected opaque cell에서 native carrier가 없는 하위 표본은 현재 같은 셀의 실제 삼각형 plane 연장과 ring plane 중 어떤 명시적 source-local 규칙으로 운반합니까? 예: F105 main(221,221)의0/64와 F125 main(224,219)의33/64. 표면 선택/깊이 구간을 정의해야 geometry coverage가 눈을 재절단하거나 단일 깊이로 머리를 뚫지 않습니다.','12mm world camera-depth가 원형/scale/측면에서도 자기 피부와 외부 피부의 구분 권위입니까, 아니면 source-local 관계/두께로 정규화할 의도입니까? 현재 같은 unilateral component의15.53mm hit도 있고, 동일 geometry의 scale만 바꾸면626/3190 query visibility가 달라집니다. 임의 임계값 재튜닝 대신 소유권 계약을 확인해야 합니다.'],'unresolved':['Paired-point patch is necessary for coordinate correctness but is not a nonregression-complete artistic solution.','Original-pigment endpoint query is still a runtime implementation task.','No new actual movement/side/blink GPU validation, full face UV/outline or temporal completion.']}
    (H/'FINDINGS114.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Preserve exact source differences without applying them to Assets or113.
    capture_before=source/'attempt5/Capture113.cs'if(source/'attempt5/Capture113.cs').exists()else source/'Capture113.cs'
    diff=[];mapping={'NativeCarrier113.cs':source/'NativeCarrier113.cs','RegionDriver113.cs':source/'RegionDriver113.cs','Forward113.cs':source/'Forward113.cs','Region113.hlsl':source/'Region113.hlsl','Capture113.cs':capture_before}
    for name,old in mapping.items():
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf8').splitlines(True),(H/'paired-point-patch'/name).read_text(encoding='utf8').splitlines(True),fromfile='113/'+name,tofile='114-review-only/'+name))
    (H/'PAIRED_SAMPLING114.patch').write_text(''.join(diff),encoding='utf8')
    code={}
    for name,fn in{'trace114.py':['geometry','transferred_sample','main'],'geometry114.py':['mapped','query','carriers','original_alpha'],'tie114.py':['complete_pool','transport','main'],'pairing114.py':['compose','main'],'pigment114.py':['clip_column','row','main'],'check114.py':['main']}.items():
        lines=(H/name).read_text().splitlines();code[name]={f:[i+1 for i,l in enumerate(lines)if l.lstrip().startswith('def '+f+'(')]for f in fn}
    (H/'CODE_INDEX114.json').write_text(json.dumps(code,indent=2)+'\n',encoding='utf8')
    # Diagnostic masks are explicitly not final renderer PNGs.
    im=Image.new('RGB',(1210,870),'#171b24');d=ImageDraw.Draw(im);ft=lambda n:ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',n)
    def text(x,y,s,n=18,fill='#eef2fa'):d.text((x,y),s,font=ft(n),fill=fill)
    text(20,15,'114 | 저장된 실제113 입력의 원인 추적 — 새 GPU 렌더가 아닙니다',27)
    text(20,60,'Close50 / owner2 · 동일한 primary 최적값의 완전한 두 해',21)
    r=ties['rows'][0];colours={0:'#262b38',1:'#7795e0',2:'#f4ebd2'}
    for v in range(2):
        x0=20+v*360;y0=128;s=30
        text(x0,y0-29,'해 '+str(v)+(' · 기존 원형 기준 우세'if v==1 else' · 같은 key 개수'),17)
        for(y,x),part in zip(r['pointsYX'],r['layouts'][v]):
            d.rectangle((x0+x*s,y0+y*s,x0+(x+1)*s-2,y0+(y+1)*s-2),fill=colours[part]);text(x0+x*s+4,y0+y*s+2,str(part),14)
        for x,y in[[5,5],[6,5]]:d.rectangle((x0+x*s-1,y0+y*s-1,x0+(x+1)*s-1,y0+(y+1)*s-1),outline='#ffad6f',width=2)
    text(785,102,'1=홍채, 2=흰자, 0=바탕',17)
    text(785,137,'흰자 key는 같지만 지지 질량은',17)
    text(785,166,'왼쪽 셀1/64, 오른쪽 셀11/64',17)
    text(785,210,'기존 source-form으로 두 프레임',17)
    text(785,239,'모두 해1 우세. history만으로 동률.',17)
    text(20,352,'서로 다른 표본 위치를 비교했던 연결 오류',21)
    text(20,389,'4배 S4 위치 → 8배 floor 재사용: (+0.0625,+0.0625)px',18)
    text(20,425,'F125 (224,219): 7/16 → 정확한 같은 위치 계산8/16',18)
    text(20,461,'다만 전체270셀에서는 RGB22개 변경 → 단독 완성안 미채택',18, '#ffcc88')
    text(20,505,'지지 표면 / 가림 검증',21)
    text(20,542,'현재 geometry4320개 carrier 포함 여부 일치',18)
    text(20,574,'실제 GPU3190개 얼굴 query 및270개 최종 합성 일치',18)
    text(20,606,'관측 없는 깊이/상대배치 오차는 None, 0으로 인증하지 않음',17)
    text(680,352,'완전 Close / canonical(8,5)',21)
    text(680,389,'8배 중심64개: 원본 안검 표본0',18)
    text(680,425,'하지만 실제 UV 곡선6점이 가시적',18)
    text(680,461,'alpha0.199~0.803 / 끝부분 길이0.052px',18)
    text(680,497,'곡선 변환 차이0.00028px는 행5를',18)
    text(680,529,'바꾸지 않음. 얇은 끝부분 표본화 손실.',18)
    text(20,674,'12mm 정책의 한계',21)
    text(20,713,'동일 원본·UV·소유권에서 scale0.5 /2만 가정해도626/3190 query가 달라짐.',17)
    text(20,749,'새 측면/scale 렌더 시험은 하지 않았습니다. 임계값은 바꾸지 않았습니다.',17)
    text(20,801,'제품77·실제 GPU113은 그대로. 준비 패치는 import/컴파일/실행 전이며 중복 업로드하지 않았습니다.',17,'#ffcc88')
    im.save(H/'FAILURES114.png')
    print(json.dumps({'findings':str(H/'FINDINGS114.json'),'pairedChanges':len(changes),'extraUnityCalls':0,'extraPlay':0,'runtimePatchAdopted':False},ensure_ascii=False))
if __name__=='__main__':main()
