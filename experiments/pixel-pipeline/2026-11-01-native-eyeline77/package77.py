from pathlib import Path
import json,sys,hashlib,ast,shutil,numpy as np
HERE=Path(__file__).resolve().parent;OUT=HERE/'archive77';OUT.mkdir(exist_ok=False);P76=HERE.parent/'whole-eye76';sys.path.insert(0,str(P76));from validate_final76 import packet
values={};frames=[];counter=0;provenance={}
def text(src,name=None):
 src=Path(src);dest=OUT/(name or src.name);raw=src.read_bytes();out=raw.replace(b'\r\n',b'\n');dest.write_bytes(out);provenance[dest.name]={'originalSHA':hashlib.sha256(raw).hexdigest(),'archiveSHA':hashlib.sha256(out).hexdigest(),'textNewlines':'LF, compiled semantics unchanged'}
source=np.load(HERE.parent/'whole-eye52/SOURCE_SURFACES52.npz');values['nativeXYZ']=source['native_xyz_head'];values['nativeTriangles']=source['native_role6_tri']
for mode in ['gpucache','final']:
 state=json.loads(sorted((HERE/mode).glob('STATE77-*.json'))[-1].read_text());assert state['stage']=='finished'and state['PlayExited']and not state.get('error')and not state.get('restorationError')
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));pre=f'f{counter}_';counter+=1
  for name in ['baseline','records','counts','original']:values[pre+name]=d[name]
  for name,a in d['arrays'].items():
   if name.startswith('S')or name=='old-eye-owner':values[pre+name]=a
  frames.append({'prefix':pre,'mode':mode,'identity':d['identity'],'roi':d['roi'],'eyeROI':d['eyeROI'],'eyeFeature':d['manifest']['eyeFeature'],'close':d['manifest']['actualBlinkWeight77'],'sourceFrame':d['manifest']['sourceFrame'],'deltaTime':entry['deltaTime'],'gpuCache':d['manifest']['gpuSourceCache77']})
 text(HERE/mode/'Capture77.cs','ActualRunner_'+mode+'77.cs.txt');text(HERE/('result-'+mode)/'RESULT77.json','RESULT_'+mode+'77.json')
 for name in ['sequence-nearest10.png','comparison-nearest18.png','full.png']:
  shutil.copyfile(HERE/('result-'+mode)/name,OUT/(mode+'-'+name))
np.savez_compressed(OUT/'fixture77.npz',**values);(OUT/'FIXTURE77.json').write_text(json.dumps({'frames':frames,'limits':'Compact source samples, not complete VRM/scene reconstruction. Complete CPU geometry/camera captures remain in local workspace. Earlier GPU8 and final cleaned-source4 are distinct sourceId cohorts.'},indent=2)+'\n')
code='import numpy as np\n'
for file,names in [(HERE/'source_candidate77.py',['components']),(HERE/'analyse77.py',['valid','cov']),(HERE/'validate77.py',['iris_allocation']),(P76/'test76.py',['supported'])]:
 s=file.read_text();tree=ast.parse(s)
 for node in tree.body:
  if isinstance(node,ast.FunctionDef)and node.name in names:code+='\n'+ast.get_source_segment(s,node)+'\n'
(OUT/'reference77.py').write_text(code,encoding='utf8')
for name in ['test_archive77.py','package77.py','analyse77.py','source_candidate77.py','validate77.py','geometry_check77.py','NativeSource77.cs','prepare_gpu77.py','NativeCacheGPU77.hlsl','NativeSourceSelection77.hlsl','NativeCacheGPU77.GPU_TESTED8.hlsl','NativeSourceSelection77.TESTED8.hlsl','Product77GPU.TESTED8.compute','ProductBefore77.compute','Product77GPU.linked.compute','PRODUCT77.patch','PRODUCT_SOURCE77.json','CACHE_OWNERSHIP77.json','CACHE_TEST_CORRECTION77.json','W_REFERENCES_ALL_ASSETS77.json','ABLATION77.json','SOURCE_CANDIDATE77.json','SOURCE_COLOUR_FINAL77.json','WARNING_CLEANUP77.json','WARNING_COMPARE_FINAL77.json','HUNK_CHECK77.json','GEOMETRY_blinksettle77.json','GEOMETRY_gpucache77.json','GEOMETRY_final77.json']:
 if(HERE/name).exists():text(HERE/name)
for name in ['CACHE_GPU_REVIEW77.json','IMPORT_REVIEW77.json','CURRENT77.json','POST77.json','CURRENT_WARNINGS77.json']:
 text(HERE/'final'/name)
(OUT/'TEXT_PROVENANCE77.json').write_text(json.dumps(provenance,indent=2)+'\n')
(OUT/'.gitattributes').write_text('* -text\n')
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>눈 안검 원본 경계 선택77</title><style>body{background:#151a20;color:#e4ebf4;font:16px/1.7 system-ui;margin:28px;max-width:1500px}img{max-width:100%;image-rendering:pixelated}a{color:#8dcfff}pre{white-space:pre-wrap}</style><h1>눈 안검 원본 경계 선택77 — 부분 수정</h1><p>실제 제품 compute와 새 helper에 적용했습니다. 기존 사용자 변경이 섞인 main compute 전체는 stage하지 않습니다. 새 helper와 분리 가능한 선언 hunk만 실제 경로에 보존하고, 전체 정확한 작업 소스/패치를 여기에 남깁니다.</p><p>원인: 외부 머리 가림을 뺀 native 면적이 0.510→0.449로 내려가 반올림 예산이1→0이 됩니다. 별도로 colour-competition rank가 같은 source upper 경계의 반대 끝을 고릅니다. 원본 연결 upper 영역의 intrinsic 면적과 현재 실제 가시성, rest-source 중심 위치를 분리했습니다. 고정 최소 pixel 수/화면 RGB history/다른 family 색으로 채우기는 사용하지 않습니다.</p><h2>최종 경고 정리 후 같은 코드 4프레임</h2><img src="final-comparison-nearest18.png"><img src="final-sequence-nearest10.png"><p>이전8프레임의 반감김 검증과 아래 최종4프레임은 다른 sourceId입니다. 같은 프레임의76/77 compute 비교만 동일 입력 대조입니다.</p><h2>이전 실제8프레임</h2><img src="gpucache-sequence-nearest10.png"><p>열림→반감김→감김→반감김→재열림. iris8→5→0→5→8이며 실제 변형 mesh와 GPU 표본의 대응을 검사했습니다. Close API 값만을 실제 baked 상태라고 가정하지 않았습니다.</p><h2>한계</h2><p>모든 눈 모양을 공동 설계한 allocator가 아닙니다. rest component의 중심을 기준으로 native 상안검의 흔들림만 줄입니다. 곡선 전체/소수 좌표 움직임/긴 회전·걷기·모든 모델의 미관 성공은 미검증입니다. native 원색 자체가 밝은 셀은 그대로이며 검은 선을 새로 그리지 않았습니다. 좁은4배 표본의 가시성/반올림 경계는 남습니다. hot sharedMesh 교체는 기존 Initialise부터 미지원이며 새 renderer/재초기화 수명만 검사했습니다.</p><p>최종 Edit 복귀, 미저장29 내용/옵션/time/pipeline/global 복원, 소유 buffer만 해제했습니다. 비dirty ProjectSettings AssetImporter 한 객체는 종료 후 unavailable이며 전체 native 상태 동등성을 주장하지 않습니다. 내부 allocated 증가를 물리 RAM/누수 확정으로 취급하지 않습니다.</p><img src="final-full.png"><p><a href="RESULT_final77.json">최종4 결과</a> · <a href="RESULT_gpucache77.json">이전8 결과</a> · <a href="CACHE_OWNERSHIP77.json">소유권/무효화</a> · <a href="CACHE_GPU_REVIEW77.json">GPU7검사</a> · <a href="PRODUCT77.patch">전체 작업 패치</a> · <a href="test_archive77.py">portable 실제 입력 검사</a></p></html>'''
(OUT/'INDEX.html').write_text(html,encoding='utf8');manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.iterdir()if p.is_file()};(OUT/'MANIFEST77.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'files':len(manifest)+1,'bytes':sum(p.stat().st_size for p in OUT.iterdir()),'folder':str(OUT)},ensure_ascii=False))
