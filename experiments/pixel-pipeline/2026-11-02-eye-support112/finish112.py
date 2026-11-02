"""Small source/contract index, not an additional algorithm proposal."""
from pathlib import Path
import hashlib,json
from source112 import HERE,P111

def main():
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    a=read(HERE/'AUDIT112.json');cache=read(HERE/'AFFILIATION_CACHE112.json');checks=read(HERE/'CHECK112.json')
    assert a['sourceCacheKeys']==1 and all(r['cacheKey']==cache['cacheKey']for r in a['records'])
    repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');before=read(P111/'DISK_BEFORE111.json')['files'];after={p:hashlib.sha256((repo/p).read_bytes()).hexdigest()for p in before};changed=[p for p in before if before[p]!=after[p]]
    assert not changed,changed
    status={'status':'SOURCE_AFFILIATION_VERIFIED_OCCLUSION_OWNERSHIP_UNDEFINED','baselineCommit':'7736f2ced41c90caec33988e64bcfe13dcea5baf','implementation':['Original VRM semantic blink binding -> native ring IDs -> exact captured primitive/UV/deformed vertex association','Conservative cache explicitly refuses to call nearby face IDs or morph influence an anatomical lid mask'],'validation':{'frozenSourceFrames':a['sameFrameRecords'],'testsPassed':checks['passed'],'protectedFileHashesUnchanged':len(before),'imageOpenedForInspection':True},'newUnityCalls':0,'newPlayEntries':0,'product77Changed':False,'gpuJointAllocatorExecuted':False,'newUserApprovalOrToolDenialBlocking':False,'blockerType':'missing representation/occlusion transfer definition; not raw frame data or permission','missingContract':cache['missingDefinition'],'notClaimed':['unique native anatomical lid segmentation','new final RGB render','time stability','finite palette/outline completion','information-theoretic impossibility'],'lastEditorObservationOnly':'111 post-query 2026-11-01T23:52:44.3230592Z; PID35364/Edit/dirty31. Not queried in112 and not asserted to be current.','nativeDataNeededBeforeMoreCapture':'No additional capture of the same existing fields identifies a semantic stylized surface ownership mask. Need an explicit source-local support/embedding/occlusion transfer rule, or an authored map if such a distinction is intended.','externalArgonContact':False}
    (HERE/'STATUS112.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
    (HERE/'PRESERVATION112.json').write_text(json.dumps({'reference':'111 protected32 snapshot, no product write in112','files':after,'changed':changed,'UnityStateNotChangedOrQueriedBy112':True},indent=2)+'\n',encoding='utf8')
    names={'source112.py':['Source.__init__','Source.accessor','Source.map_to_capture','Source.freeze'],'support112.py':['connected','Support.__init__','Support.evidence','Support.cache'],'audit112.py':['main','picture'],'check112.py':['main'],'finish112.py':['main']};idx=[]
    for name,terms in names.items():
        lines=(HERE/name).read_text(encoding='utf8').splitlines()
        for term in terms:
            simple=term.rsplit('.',1)[-1];line=next((i for i,t in enumerate(lines,1)if t.lstrip().startswith('def '+simple+'(')),None);idx.append({'script':name,'function':term,'line':line})
    (HERE/'CODE_INDEX112.json').write_text(json.dumps(idx,indent=2)+'\n',encoding='utf8')
    html='''<!doctype html><meta charset="utf-8"><title>112 · native support / ownership</title><style>body{margin:24px auto;max-width:1280px;background:#10202c;color:#e5f0f6;font:17px/1.7 sans-serif}img{width:100%;image-rendering:pixelated}a{color:#80dfea}code{color:#ffd69b}</style><h1>112: 변형 연결은 확인, 안검 소유권은 미정</h1><p>기존 GPU77과 실제 원본 UV·가림 표본입니다. 새 공동 배정 결과가 아닙니다. Unity/Play 호출 0, 제품 기본값 변경 0.</p><img src="SUPPORT_OWNERSHIP112.png"><p>단안 blink가 등록 ring 각24정점을 식별합니다. 그러나 피부 blink 영향 영역은 양눈을 연결하고 단안 영향도 피부43정점에서 겹칩니다. 안검 색소848점은 별도 mesh/UV 경로이며 피부 surface의 내부/외부 가림 분류를 제공하지 않습니다.</p><p>완전 Close에서는 I/W source가0인데도 피부 ring 면적이 남습니다. 원형 parent/상부 색소 경계만으로 새로운 눈 전체의 닫힌 support 표면과 깊이/가림 대응을 정의할 수 있다고 가정하지 않았습니다.</p><p>최소 반례: F105 눈2 (x3,y5), source white0.34375셀, 물리 노출2/16. 가림9삼각형의 실제 alpha는 모두1입니다. 이것을 skin/bank 규칙으로 투명화하지 않았습니다. 추가 같은 데이터 캡처 대신 source-local support/cage 및 내부/외부 가림 transfer 정의가 필요합니다. 이는 기존 정식화의 공백이며 불가능성 증명이 아닙니다.</p><p>최신 검토 질문과 코드 위치는 저장소 <code>docs/ai/PIXEL_ALBEDO_20261030.md</code> 112절 하나에 있습니다.</p><p><a href="STATUS112.json">적용 구분</a> · <a href="AFFILIATION_CACHE112.json">source cache / 미정 필드</a> · <a href="AUDIT112.json">24상태·9삼각형 증거</a> · <a href="CHECK112.json">회귀 검사</a> · <a href="CODE_INDEX112.json">함수 위치</a></p>'''
    (HERE/'INDEX.html').write_text(html,encoding='utf8')
    print(json.dumps({'tests':checks['passed'],'protectedHashes':len(before),'runtimeReady':False,'blocker':status['blockerType']}))

if __name__=='__main__':main()
