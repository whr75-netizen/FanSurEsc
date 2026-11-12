"""Five completed CPU adapter/evidence files, handoff and narrow local commit."""
from pathlib import Path
import json,hashlib,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';DOC='docs/ai/PIXEL_ALBEDO_20261030.md';G=H/'face87'
NAMES=['SourceShade87.cs','SourceShadeTests87.cs','audit_source_shade87.py','checkpoint87.py','face87/SOURCE_SHADE87.json','face87/DELIVERABLE87.json']
NOTE='''

## 87. 색 지지 성분·원본 색 주소·Q의 분리 소비자 (2026-11-12, CPU)

- `SourceShade87.Input/Packet/TryCompose`는86 support ID를 colour-family ID로 사용하지 않는다. 외부에서 명시 배정한 원본 UV→colour address와 현재85 Q를 유한 LUT에 직접 대입한다. sourceId/frame/원본 계약을 대조하며, 같은 원본RGB/같은 팔레트 정책이면 support나 material anchor가 달라도 전체 LUT가 같아야 한다. Q가 이전과 같아도 LUT 대입을 건너뛰지 않는다. RGB에 명암을 곱하지 않고 현재 alpha와 비얼굴 RGB는 보존한다.
- source mask 전체에 색 주소가 준비되지 않았거나 현재 visible source/Q/stamp가 불완전하면 **출력 자체를 만들지 않는다**. 알려진 셀만 LUT, 나머지는 기존RGB로 섞어 얼룩을 재생산하는 부분 fallback을 방지한다. 배열은 owner가 복사 보유하며 Unity/static cache/GPU readback/자원 추가 없음. 이 소비자는 C# CPU 실험이고 현재 GPU/제품77에 연결되지 않았다.
- `SourceShadeTests87.Main`: 서로 다른 원본색2개, sameRGB/Q 불변식, 다른 source/frame 거절, 미배정 source 및 잘못된 Q의 atomic 거절, 입력 복사 수명, alpha/비얼굴 보존 등13검사 통과. `audit_source_shade87.main`은 기존58 math(해시 c99c191d…)를 그대로 사용하고 실제85 저장6프레임의 모든 visible face240셀을 대조한다. sourceUV/support 부재0. 현재 fixture는 **whole component가 exact constant인81성분/60원본색만** 주소를 준 매우 제한된 입력이므로 전체866160source texel 중866073미배정이고, visible240도 전부 이 조건에서 미배정이다. 따라서6개 모두 newRGB=null로 거절했다. 이는 **우리의 제한된 상수성분 입력 정책 때문**이며 원본 RGB/UV 부재, 자동 영역화 원천 불가능, 사용자 새 디자인 수치가 필요하다는 증명이 아니다. 현재397 nonconstant support의 값 변화를 유지하는 source-value→colour-address 단계가 구현 미완이며, 여기에 단색 또는82미채택 palette를 넣어 통과시키지 않는다.
- 검증: .NET CPU 컴파일/13회귀 및 저장 실제6입력. 새 Unity 호출/import/Play/GPU/씬저장/제품77 기본값 변경 없음. 재검산 `python audit_source_shade87.py`(기존58 원본 및 b900f30d의6 actual atlas 사용); 외부 출력은 `--output-root <workspace-directory>`로 지정할 수 있다. runtime history85와87 CPU 소비자의 기술적 성공을 전체 얼굴 미술/LUT 얼룩 해소로 확대하지 않는다.
- 실제120프레임 비교 PNG는 Library `FACE_Q_HISTORY_120_ACTUAL_GPU.png`, id `libfile_fde3_f-4df32db89a0081919a537c03c0b2320a_63ba02b4784c8191890f3a4c58eb6764`(`file_000000008df881f5be3cf628c66743cd`). native RGB control / actual Q / actual GPU Q history로 명시한 그림이며 새 최종 팔레트 RGB 결과가 아니다. 업로드 성공, Windows helper의 os.setxattr 미지원으로 로컬 xattr 적용만 실패했다. Library identity는 별도 sidecar와 `face87/DELIVERABLE87.json`으로 보존했고 중복 업로드하지 않았다.
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
 r=subprocess.run(['git',*args],cwd=R,capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;return r.stdout.strip()
def main():
 assert '--publish'in sys.argv
 assert git('rev-parse','HEAD')=='b900f30dc5543322157ab29c28f397eb1a955578'and not git('diff','--cached','--name-only')
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];protected=json.loads((H/'face55/backup/DISK_BEFORE.json').read_text());assert all(sha(R/p)==v for p,v in user.items())and all(sha(R/x['path'])==x['sha256']for x in protected if x['exists'])
 old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);assert(R/DOC).read_bytes()==old+NOTE.encode('utf-8')
 for n in NAMES:
  dst=R/P/n;assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 # Read the actual repository code and existing fixtures, write CPU temporaries
 # to our workspace only. This performs no Unity import or GPU operation.
 replay=subprocess.run([sys.executable,'-B','-u','-X','utf8',str(R/P/'audit_source_shade87.py'),'--output-root',str(G/'repo-check')],capture_output=True,text=True);assert replay.returncode==0,replay.stdout+replay.stderr
 result=json.loads((G/'repo-check/SOURCE_SHADE87.json').read_text());assert result==json.loads((G/'SOURCE_SHADE87.json').read_text())
 selected=[P+'/'+n for n in NAMES]+[DOC];spec=G/'SELECT87.paths';spec.write_bytes(('\0'.join(selected)+'\0').encode('utf-8'));git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(selected);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check');assert all(sha(R/p)==v for p,v in user.items())and all(sha(R/x['path'])==x['sha256']for x in protected if x['exists'])
 body=G/'COMMIT_BODY87.txt';body.write_text('Separate observed support, source colour address and selected shade\n\nAdd atomic finite-LUT candidate consumer with13 CPU invariants. Reuse58 palette math and six actual85 input frames; reject incomplete nonconstant-source assignment rather than mixing LUT with old RGB. Native UV/RGB exist; the colour-field implementation remains incomplete. Preserve product77 and user30/protected128; no new GPU/Unity call or push.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only');out={'commit':git('rev-parse','HEAD'),'files':len(selected),'repositoryCPUReplayExact':True,'user30Protected128Equal':True,'product77Changed':False,'newGPUExecution':False,'fullFaceColourOrArtCompleted':False};(G/'COMMIT87.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
