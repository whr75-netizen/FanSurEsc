"""Selective local experiment snapshot + handoff commit. No Assets/UI/Unity.
Only this new experiment folder and the existing named handoff are staged.
Does not reset, clean, stash, delete, overwrite a user asset, or push.
"""
from pathlib import Path
import subprocess,json,hashlib,sys,os
H=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
DEST=REPO/'experiments/pixel-pipeline/2026-11-01-joint-resolver110'
DOC=REPO/'docs/ai/PIXEL_ALBEDO_20261030.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    q=subprocess.run(['git','-C',str(REPO),*args],check=True,capture_output=True);return q.stdout
def names(*args):return set(git(*args,'-z').decode('utf8').strip('\0').split('\0'))-{''}
def main():
    assert git('rev-parse','--show-toplevel').decode().strip().replace('\\','/').lower()==str(REPO).replace('\\','/').lower()
    assert git('branch','--show-current').decode().strip()=='master'
    assert not names('diff','--cached','--name-only'),'Preexisting staged work must not be mixed'
    before=names('diff','--name-only');assert str(DOC.relative_to(REPO)).replace('\\','/')not in before,'Do not stage another writer handoff change'
    old=git('rev-parse','HEAD').decode().strip();base=json.loads((H.parent/'joint-lid107/ASSET107_FINAL.json').read_text(encoding='utf8'));protected={v['path']:sha(REPO/v['path'])for v in base['protected32']};baselineMatches=all(protected[v['path']]==v['sha']for v in base['protected32']);assert (DEST.resolve()).is_relative_to((REPO/'experiments').resolve())
    files=[p for p in H.rglob('*')if p.is_file()and'library-private110'not in p.parts and'__pycache__'not in p.parts and not p.name.endswith('-footprint.json')and p.suffix in ['.py','.json','.png','.npz','.html','.zip','.gz']and p.name not in ['COMMIT110.json']]
    copied=[]
    for source in sorted(files):
        rel=source.relative_to(H);target=DEST/rel;assert target.resolve().is_relative_to(DEST.resolve());data=source.read_bytes();target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==data,f'Existing target differs: {target}'
        else:
            with target.open('xb')as f:f.write(data)
        assert sha(source)==sha(target);copied.append(str(target.relative_to(REPO)).replace('\\','/'))
    # Validate the copied code against prior FROZEN sibling inputs, not the
    # original absolute capture directories. No Unity or network involved.
    replayEnv=os.environ.copy();replayEnv['PIXEL110_FROZEN_INPUTS']='1';replay=subprocess.run([sys.executable,'-B','-u','-X','utf8',str(DEST/'check110.py')],cwd=str(REPO),env=replayEnv,capture_output=True,text=True)
    assert replay.returncode==0,replay.stderr
    (H/'CHECK110.json').write_bytes((DEST/'CHECK110.json').read_bytes())
    block='''

### 110 — 색소/carrier/source 형상 공동 resolver, 오프라인 미채택

- 최신: `experiments/pixel-pipeline/2026-11-01-joint-resolver110/INDEX.html`. 기준 `e26c58b3`; 이번 커밋은 `git log -- experiments/pixel-pipeline/2026-11-01-joint-resolver110`으로 찾는다. Unity/Play/GPU/Assets 변경 0, 제품77 유지. 저장107의19상태×양눈과 독립105 Close×양눈, 총40입력을 같은 규칙으로 계산했다.
- `fields110.build/FaceVisibility.query`, `separate110.problem_from_fields/exposure`: 삼각형 polygon·bary/UV/world/depth와 표본별 가림을 유지한다. 629개 carrier 셀에서 머리 앞/뒤 판정이 표본마다 달랐다. 외부 머리 가림으로 원형 배치를 다시 결정하던 오류를 분리했다. ON/OFF/복구의 배치 후보 집합은 양눈 모두 정확히 같으며, 측면 Close의 잠재 안검3셀은 기록 표본 노출0이다. 이는 최종 RGB 렌더 검증이 아니다.
- `resolver110.solve/feasible`: 세 파트가 하나의 셀 변수를 공유하는 유한 CSP. 면적 반올림·우선순위·고정 셀 수·RGB 비용 없이 source→픽셀 사각형/픽셀 corner→source의 최대 기하 오차를 최소화하는 명시적 가설이다. F103 `(12,4)`의 조건부 해는 홍채이며 안검2표본을 셀 전체 소유권으로 확대하지 않는다. 같은105 실제 색소 경로 누락은108의51.38%/73.84%에서2.49%/8.13%이나, 안검3+3셀→7+8셀로 넓어진 대가가 있다. 미관 성공으로 채택하지 않았다.
- `identity110.rank_with_relative/relative_form`: source-ID 분포만 같아도 원형 모양은 다를 수 있어 source 쌍의 상대 좌표 오차·누락을 별도 Pareto 차원으로 추가했다. History는 동일한 현재 형상 비용 사이에서만 사용하고, 현재 Close/가림을 무효화하지 않는다. Native 연속 UV interval의 완전한 형상/history 및8× 홍채·흰자 source ID는 아직 미검증(현재 실제 ID는4× 입력).
- `reconstruct110.recover/checks`: 105 Open/Close와107의 현재 head·실제 Close(누락 시 교정 정점 깊이 추정)의 재구성 가설이다. 독립54상태 최대0.001584px/1.963µm, 별도2프레임 정점 최대1.421µm. 105=107의 정확한 동일 상태/전체 표면 증명이 아니다. 저장375파일은 기존107 동결본과 byte 동일. 24개 유한 좌표 perturbation에서 검사한 최적 라벨 집합은 같았지만 전체 오차구간 증명은 아니다.
- 미완: `COUNT_RANGE110.json`의 정확한 feasibility 검사에서 F99 눈1은 같은 기하 최적값에 홍채1~5셀이 모두 가능하다. 64해만 열거한 조건부 선택을 유일 해/전체 Pareto로 부르면 안 된다. 원형 상대 배치 기준과 완전한 최적해 선택이 더 필요하며 아직 디자인 셀 수를 사용자에게 요구하지 않는다. 최종 팔레트/외곽선/시간 안정성/GPU 통합은 미완이다. 새 메쉬 캡처로 이 목적함수 동률은 해결되지 않는다.
- `check110.py`, `audit110.py`, `NEXT_INPUT110.json`: 독립 작은 완전탐색24, quota 진단40, 실제 D4/순회18, GPU 가림173증거와 footprint 검사. 다음 직접 캡처는 평가 정점 약49KB·실제 적용 행렬·source 색소 경로의 실제 가림 query·bounded dense source ID가 재구성보다 정확하고 저렴하다. 현재 offline adapter 수초/CSP 수십ms는 실시간 GPU 성능이나 상한이 아니다. 소유/다중뷰/모델 교체/무효화 계획만 작성했으며 새 실행은 하지 않았다. 세부 함수/행은 `CODE_INDEX110.json`.
'''
    current=DOC.read_bytes();marker='### 110 —'.encode('utf8');assert marker not in current,'Do not append the same handoff twice';DOC.write_bytes(current+block.encode('utf8'));allowed=set(copied)|{str(DOC.relative_to(REPO)).replace('\\','/')};pathspec=H/'STAGE_PATHS110.nul';pathspec.write_bytes(b''.join(x.encode('utf8')+b'\0'for x in sorted(allowed)))
    git('add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul');assert names('diff','--cached','--name-only')==allowed;git('diff','--cached','--check')
    stagedNumstat=git('diff','--cached','--numstat').decode();git('commit','-m','Record joint resolver110 and separate external hair occlusion');commit=git('rev-parse','HEAD').decode().strip();assert commit!=old;assert not names('diff','--cached','--name-only');assert names('diff','--name-only')==before
    assert all(sha(REPO/path)==value for path,value in protected.items());assert sha(REPO/base['newAsset'])==base['sha256']
    result={'beforeCommit':old,'commit':commit,'branch':'master','experimentFiles':len(copied),'changedPaths':len(allowed),'snapshotBytes':sum(p.stat().st_size for p in files),'originalModifiedPathsPreserved':len(before),'protected32Unchanged':True,'protected32MatchPrior107':baselineMatches,'product107CloneUnchanged':True,'copiedFrozenInputReplayPassed':True,'stageEmpty':True,'AssetsTouched':False,'UnityCalled':False,'push':False,'target':str(DEST),'stagedNumstat':stagedNumstat}
    (H/'COMMIT110.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items()if k!='stagedNumstat'}))
if __name__=='__main__':main()
