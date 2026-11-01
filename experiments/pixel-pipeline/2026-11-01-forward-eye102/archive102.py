from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');REL='experiments/pixel-pipeline/2026-11-01-forward-eye102';BASE='109fe57c5a6129c483e3ea4a59fb3661910dac72';DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(P),*args],encoding='utf-8')
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copy2(p,q)
def prepare():
 d=H/'archive';d.mkdir(exist_ok=False);v=load(H/'HIERARCHY_VALIDATION102.json');assert not v['CPUGPUSelectorMismatches']and not any(v['unresolvedByFrame'])
 for p in H.iterdir():
  if p.is_file()and p.suffix in ['.py','.cs','.compute','.hlsl','.json']:copy(p,d/p.name)
 (d/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='utf-8')
 for p in (H/'reviewH').iterdir():copy(p,d/'reviewH'/p.name)
 for folder in ['review','review-motion','review-motionH']:
  for p in (H/folder).iterdir():
   if p.name.endswith('-1x.png'):copy(p,d/folder/p.name)
 shared=['layer-zero101/LayerZero101.cs','layer-zero101/SkinSource101.cs','source-palette58/SourcePalette58.cs','renderer-family59/RendererFamily59.cs','live-underlay98/NativeRetarget96.cs','live-underlay98/LiveSurface96.cs','live-underlay98/WholeEye96.cs','live-underlay98/MotionScope97.cs','final-eye95/MotionScope95.cs','hair-isolation100/HairDrawScope100.cs']
 for f in shared:copy(R/f,d/'src'/Path(f).name)
 copy(R/'apply-capture66/analyse_capture68.py',d/'reader68.py');copy(R/'hair-isolation100/TEMPLATE_REFERENCE100.npz',d/'TEMPLATE_REFERENCE100.npz')
 receipts=[]
 with zipfile.ZipFile(d/'RAW102.zip','x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for folder in ['capture','motion','ties','captureH','motionH']:
   cap=H/folder;last=sorted(cap.glob('STATE102-*'))[-1];s=load(last);assert s['stage']=='finished'and not s.get('error')and not s.get('restorationError')and s['PlayExited'];copy(last,d/folder/last.name)
   for name in ['Capture102.cs','RUN_Capture102.cs.txt']:
    copy(cap/name,d/folder/name)
   for name in ['GLOBAL_NAMES66.json','POST102.json','Post102_CONSOLE_AFTER.json','IMPORT102.json']:
    if(cap/name).exists():copy(cap/name,d/folder/name)
   receipts.append({'folder':folder,'request':load(cap/'Capture102_REQUEST.json'),'reply':load(cap/'Capture102_REPLY.json')})
   for e in s['sequencePackets']:
    p=Path(e['output']);assert(p/'RAW_COMPLETE76.marker').read_text()==sha(p/'RAW_MANIFEST.json')
    for f in p.iterdir():
     if f.is_file():z.write(f,folder+'/frame-'+str(e['frame'])+'/'+f.name)
 save(d/'EXECUTION102.json',receipts)
 source=R/'source-regions103';target=d/'source-regions103'
 for p in source.rglob('*'):
  if p.is_file()and p.suffix in ['.py','.json','.png','.npz']:copy(p,target/p.relative_to(source))
 page='''<!doctype html><meta charset="utf-8"><title>102 forward eye — isolated</title><style>body{font-family:system-ui;background:#20252c;color:#eee;max-width:1250px;margin:auto}img{max-width:100%;image-rendering:pixelated}a{color:#ace}</style><h1>102: clean canvas → 눈 전체 → 내부 파츠 → 머리 이산 가림</h1><p>제품77은 유지했다. 격리 GPU 경로는 이전295/348/98의 완성 RGB나 world backing을 읽지 않는다. source-local native/authored eye와 현재 변형 피부를 먼저 공동 선택하고 머리의 실제 depth/coverage는 후단에 한 색으로 선택한다. RGB lerp/시간 평균/고정 눈 픽셀 예산은 없다.</p><img src="reviewH/EYE_FORWARD_COMPARE102.png"><p><a href="reviewH/EYE_MOTION102.webp">실제 움직임 (느리게)</a> · <a href="RESULT102H.json">머리 OFF/ON·Close/reopen9상태</a> · <a href="MOTION_RESULT102H.json">움직임28프레임</a> · <a href="HIERARCHY_VALIDATION102.json">동결 GPU 입력 CPU4092셀 재검산</a> · <a href="RAW102.zip">원시 버퍼와 marker</a></p><h2>확정한 오류와 수정</h2><p>실제 실패 입력은 iris2+white7+canvas7이다. 이전 선택은 각 part를 canvas와 따로 경쟁시켜 미확정 처리했다. union eye9가 canvas7보다 크므로 부모 특징을 먼저 선택해야 한다. 새 Select는 feature union→child coverage→유일한 actual source depth 순서다. 같은 coverage와 source depth까지 같은 경우는 여전히 미확정으로 남긴다. exact .5는 foreground 포함이며 최소 셀 예산이 아니다. frame-order witness는 판단에 쓰지 않는다.</p><p>수정 후28프레임 미확정0,4092셀 CPU/GPU 불일치0. 위상10상태 identity1종, 측정 이동.99998474px 및 원점 복귀0. 홍채·흰자는 원본 bank palette 밖0. Native 안검은 phase frame104에서 RGB[118,94,81]→[118,93,81]1코드 변동이 남는다. geometry 안정성을 colour/전체시간 안정화로 확대하지 않는다. 완전Close iris/sclera0, 재개방 원복이나 닫힌 안검은1셀만 남아 읽히는 눈매 완성은 아니다.</p><h2>남은 source resolver 전제 오류</h2><p>원본 얼굴 재질UV 도메인866160texel/11638RGB8을64 affine-jump 방식으로 검사했다. coarse5 중 main798508texel은 피부와 진한 두피를 같은 region으로 합친다. 같은 region RGB[42,20,21]과[254,248,231], OKLab L.223~.979. 원본 경계는 AA된 연속 전이여서 strict jump 근거가 없다. fine1368로 대신하면 과분절된다. native lid도 coarse28/fine2176이며 fine을 미술 특징으로 확정하지 않았다.</p><p><a href="source-regions103/SOURCE_EVIDENCE103.json">정확한 source/hash/UV</a> · <a href="source-regions103/COUNTEREXAMPLES103.json">같은region 대조 좌표</a><br><img width="48%" src="source-regions103/part3/source.png"> <img width="48%" src="source-regions103/part3/persistent-regions.png"></p><p>이 실패 map으로 P를 만들면 다시 피부·두피가 같은색으로 붕괴하므로 적용하지 않았다. 다음 resolver에는 finite-width AA colour transition과 지속 gradient/얇은 painted feature의 구별 및 source hierarchy가 필요하다. native skin·lid 전체 P/outline 경로는 미완이다. 사용자6+2 평가는 참고이며 force/template target으로 추가하지 않았다. source bank의 기준각과 사용자 표현이 일치한다고 단정하지 않았다.</p><p>보존: 최종Edit,dirty31,입력 동일 객체22값·장치/옵션/time/pipeline/globals/사용자30변경·보호32파일. RT30→30. 초기47snapshot의 임시 ProjectSettings importer는 수명 종료 후 unavailable였고, 후기 baseline46은46exact. 실제 PlayerSettings는 계속 exact. 삭제/reset/저장/CUA/force kill/push없음. 원배율/nearest PNG를 직접 검수했다. 미관완성·제품통합·모델100%범용성은 주장하지 않는다.</p></html>'''
 (d/'INDEX.html').write_text(page,encoding='utf-8');save(d/'ARTIFACTS102.json',{'files':[{'path':p.relative_to(d).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size}for p in sorted(d.rglob('*'))if p.is_file()]});print(json.dumps({'files':len(load(d/'ARTIFACTS102.json')['files'])+1,'rawZipBytes':(d/'RAW102.zip').stat().st_size}))
def install():
 assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();a=load(H/'ASSET102.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);assert git('diff','--name-only').splitlines()==a['modifiedBefore'];dest=P/REL;assert not dest.exists()
 for p in sorted((H/'archive').rglob('*')):
  if p.is_file():copy(p,dest/p.relative_to(H/'archive'))
 print('102 snapshot and103 rejected-source evidence installed; product77 unchanged')
def commit():
 assert git('rev-parse','HEAD').strip()==BASE;a=load(H/'ASSET102.json');assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);assert(P/DOC).read_text(encoding='utf-8')==git('show','HEAD:'+DOC)+(H/'HANDOFF_APPEND102.txt').read_text(encoding='utf-8');asset=a['newAsset'].replace('\\','/');allowed={REL+'/'+f['path']for f in load(P/REL/'ARTIFACTS102.json')['files']}|{REL+'/ARTIFACTS102.json',asset,asset+'.meta',DOC};assert set(git('diff','--cached','--name-only').splitlines())<=allowed;git('add','--',REL,asset,asset+'.meta',DOC);assert set(git('diff','--cached','--name-only').splitlines())==allowed;assert not git('diff','--cached','--check');git('commit','-m','fix(pixel): select whole eye feature before child parts in isolated pipeline');assert not git('diff','--cached','--name-only').strip()and git('diff','--name-only').splitlines()==a['modifiedBefore'];assert all(sha(P/r['path'])==r['sha']for r in a['protected32']);save(H/'COMMIT102.json',{'commit':git('rev-parse','HEAD').strip(),'selectedFiles':len(allowed),'productDefault':77,'sourceRegions103Rejected':True,'protected32Exact':True,'userModifiedRemaining':30,'push':False});print(json.dumps(load(H/'COMMIT102.json')))
if __name__=='__main__':{'prepare':prepare,'install':install,'commit':commit}[sys.argv[1]]()
