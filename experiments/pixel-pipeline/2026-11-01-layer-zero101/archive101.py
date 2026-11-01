from pathlib import Path
import sys,json,hashlib,zipfile,shutil,subprocess
H=Path(__file__).resolve().parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');REL='experiments/pixel-pipeline/2026-11-01-layer-zero101';DOC='docs/ai/PIXEL_ALBEDO_20261030.md';BASE='1bd13a5c6f6afc5179e2a65f90278d9a8ba0dbba'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(P),*args],encoding='utf-8')
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copy2(p,q)
def prepare():
 d=H/'archive';d.mkdir(exist_ok=False);cap=H/'captureB';state=load(sorted(cap.glob('STATE101-*'))[-1]);assert state['stage']=='finished'and not state.get('error')and not state.get('restorationError');assert all(r['referenceCoveredButCanvasMissing']==0 for r in load(H/'RESULT101.json')['states'])
 for p in H.iterdir():
  if p.is_file()and p.suffix in ['.py','.cs','.hlsl','.shader','.json']:copy(p,d/p.name)
 (d/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='utf-8')
 for p in (H/'review').iterdir():copy(p,d/'review'/p.name)
 for name in ['SkinSource101.cs','LayerZero101.cs','LayerZeroFragment101.hlsl']:assert(d/name).exists()
 copy(H.parent/'apply-capture66/analyse_capture68.py',d/'reader68.py')
 for p in cap.iterdir():
  if p.is_file()and(p.suffix=='.cs'or p.name.startswith('RUN_')or p.name.startswith('STATE101-')or p.name in ['Post101_CONSOLE_AFTER.json','Compile101_REPLY.json','Capture101_REPLY.json','GLOBAL_NAMES66.json','POST101.json']):copy(p,d/'captureB'/p.name)
 failed=load(sorted((H/'capture').glob('STATE101-*'))[-1]);save(d/'FAILED_FIRST_ATTEMPT101.json',{k:failed.get(k)for k in ['error','PlayExited','nativeComparisons72','motionRestoration82','editInputRestoration82','optionsRestored','timeRestored','pipelineRestored','globalRestoreErrors','layer101Disposed']})
 with zipfile.ZipFile(d/'RAW101.zip','x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for e in state['sequencePackets']:
   p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
   for f in p.iterdir():
    if f.is_file():z.write(f,'frame-'+str(e['frame'])+'/'+f.name)
 page='''<!doctype html><meta charset="utf-8"><title>101 격리 얼굴 바탕</title><style>body{font-family:system-ui;background:#20252c;color:#eee;max-width:1250px;margin:auto}img{max-width:100%;image-rendering:pixelated}a{color:#ace}</style><h1>101: 구버전 눈을 입력받지 않는 얼굴 바탕</h1><p>제품77 미변경. 실제 같은 카메라/프레임의 독립 GPU 패스. 원본 native 피부와 현재 변형 안구를 skin proxy로 그린다. 안구 색은 eye UV가 아니라 native 피부 경계의 원재질 UV medoid에서 공급한다. 주변 화면색 추정, 기존 눈 결과 복사, 최종 RGB×명암 연산은 socket proxy에 없다.</p><img src="review/LAYER0_COMPARE101.png"><p>주의: 네 번째/세 번째 열은 각각 coverage와 진단용 바탕 미리보기다. 머리 가림·새 눈은 아직 합성하지 않았다. 원본 얼굴 부분은 unlit source 진단이며 얼굴 전체 P[region,q] 출력은 미완이다. 안구 skin proxy만 유한 팔레트 직접 조회를 검증했다. 픽셀 미리보기는4x중 선언한1표본이며 완성된 공동 cell 배치가 아니다.</p><p>3상태 모두 reference가 덮은 표본의 canvas 누락0, proxy 팔레트 밖 RGB8 0. 원상복구/RT30→30/dirty31 유지. 직렬화46개 일치, 임시 AssetImporter1개는 종료 뒤 unavailable. 실제 PlayerSettings 직렬화는 동일. 첫 시험의 카메라 연결 실패도 보존했다. 회전/Close/시간 안정성·미관 성공은 아직 주장하지 않는다.</p><p><a href="RESULT101.json">실측</a> · <a href="RAW101.zip">3프레임 원시 버퍼</a> · <a href="LayerZero101.cs">Graph 패스</a> · <a href="SkinSource101.cs">원본 UV 피부 공급</a></p>'''
 (d/'INDEX.html').write_text(page,encoding='utf-8');save(d/'ARTIFACTS101.json',{'files':[{'path':p.relative_to(d).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(d.rglob('*'))if p.is_file()]});print(json.dumps({'files':len(load(d/'ARTIFACTS101.json')['files'])+1,'rawZipBytes':(d/'RAW101.zip').stat().st_size}))
def install():
 assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();a=load(H/'ASSET101.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);assert git('diff','--name-only').splitlines()==a['modifiedBefore'];dest=P/REL;assert not dest.exists()
 for p in sorted((H/'archive').rglob('*')):
  if p.is_file():copy(p,dest/p.relative_to(H/'archive'))
 save(H/'PRESERVATION101.json',{'protected32Exact':True,'userTrackedModified':30,'sourceAssetsOverwritten':0,'product77Unchanged':True});print('101 isolated results copied; handoff patch pending')
def commit():
 assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();a=load(H/'ASSET101.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);assert(P/DOC).read_text(encoding='utf-8')==git('show','HEAD:'+DOC)+(H/'HANDOFF_APPEND101.txt').read_text(encoding='utf-8')
 allowed={REL+'/'+f['path']for f in load(P/REL/'ARTIFACTS101.json')['files']}|{REL+'/ARTIFACTS101.json',DOC,a['newAsset'],a['newAsset']+'.meta'};git('add','--',REL,DOC,a['newAsset'],a['newAsset']+'.meta');assert set(git('diff','--cached','--name-only').splitlines())==allowed;assert not git('diff','--cached','--check');print(git('diff','--cached','--stat'));git('commit','-m','feat(pixel): validate isolated source-backed face canvas')
 assert not git('diff','--cached','--name-only').strip()and git('diff','--name-only').splitlines()==a['modifiedBefore'];assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);save(H/'COMMIT101.json',{'commit':git('rev-parse','HEAD').strip(),'selectedFiles':len(allowed),'productDefault':77,'push':False,'protected32Exact':True});print(json.dumps(load(H/'COMMIT101.json')))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
