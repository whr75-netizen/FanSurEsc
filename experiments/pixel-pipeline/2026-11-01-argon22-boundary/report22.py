"""Summarize the one boundary hypothesis; no extra candidate or Unity run."""
from pathlib import Path
import json,hashlib,sys,ast
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from paths22 import H,R,OLD
from stored110 import P108,source_packet,plane
def read(p):return json.loads(p.read_text(encoding='utf8'))
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
COL=np.array([[24,32,43],[60,202,233],[252,236,191],[191,124,252],[248,78,139]],np.uint8)
def main():
    data=read(H/'RESULTS22.json');lost=[];minimum=[]
    for case in data['cases']:
        d=np.load(P108/'fixtures'/(case['dataset']+'.npz'));keys=[tuple(map(int,x))for x in d['keys']];loss=[]
        for code,part,name in [(1,1,'iris'),(2,4,'white')]:
            index=keys.index((case['owner'],part));mass=float(d['lower'][index].sum())
            if mass>0 and all(v[name]==0 for v in case['counts']):loss.append({'sourcePart':part,'certainVisibleSourceMass':mass})
        case['positiveSourcePartsLost']=loss
        if loss:lost.append({'dataset':case['dataset'],'owner':case['owner'],'Close':case['Close'],'lost':loss,'counts':case['counts']})
        if case['dataset']=='actual107-frame105'and case['owner']==2:
            for y,x in np.argwhere(sum(d['lower'][keys.index((2,p))]for p in [1,4])>0):
                v=[float(d['lower'][keys.index((2,p))][y,x])for p in [1,4]];minimum.append({'canonicalCellYX':[int(y),int(x)],'visibleIrisWhiteMass':v,'candidateLabel':case['labels'][0][y][x],'proposedBoundaryRow':dict(case['literalBoundaryRowsXY']).get(int(x))})
    phase=[]
    for owner in [1,2]:
        q=[next(v for v in data['cases']if v['dataset']==f'actual107-frame{f}'and v['owner']==owner)for f in [121,125,129]];same=q[0]['labels']==q[1]['labels']==q[2]['labels'];assert same;phase.append({'owner':owner,'frames':[121,125,129],'canonicalLabelArraysExactlyEqual':same,'notFinalRGBOrTemporalGPUProof':True})
    data['summary']['casesWithPositiveVisibleSourcePartExtinguished']=len(lost);data['positivePartLosses']=lost;data['phaseComparison']=phase;data['minimumPartial75Counterexample']=minimum;data['documentPolicyScope']={'validDirection':'UpperLine is a feature boundary, not an area quota; finite palette colours are a separate final lookup.','notUniversalProof':'One row per global screen column is not rotation covariant or always8-connected. Prototype uses existing registered canonical eye grid.','strictProseVersusEquation':'The document also allows below-boundary UpperLine when I+W=0; that exception differs from strict one-per-column. This test implements the strict boundary prose only.','colour':'Nearest prototype labels give a total colour assignment, not connected spatial regions. Medoid counts/thresholds and weak-blush merge are style policy, not proven universal noise thresholds. P[r,q] implies equal output only when r/q and encoding are equal.','current108Correction':'108/110 do not impose ceil(lid_mass) as an adopted hard upper bound; the conflict was diagnostic.110 already has no such quota.'}
    (H/'RESULTS22.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    rows=[(99,'열림'),(101,'Close25'),(103,'Close50'),(105,'Close75 · 양의 눈 영역 소실'),(107,'Close100'),(125,'순수 위상0.5')]
    board=Image.new('RGB',(1100,1260),'#101923');dr=ImageDraw.Draw(board);dr.text((24,18),'Argon2.2 경계 규칙 — 저장 입력 비교 / GPU 미적용',font=font(25),fill='white');dr.text((24,58),'왼쪽은 실제 저장 GPU77. 오른쪽은 진단색 라벨이며 새 최종 RGB 렌더가 아닙니다.',font=font(17),fill='#bfd5e8');dr.text((24,87),'홍채=청록 / 흰자=크림 / 상안검=보라. 안검 역할을 분리해 임의 픽셀 예산·가중 합을 없앴습니다.',font=font(17),fill='#bfd5e8')
    for x,t in [(24,'실제 GPU77 머리'),(190,'110의 조건부 공동 해'),(520,'2.2 경계 후보 (가림 전)'),(800,'source 비교 / 제한')]:dr.text((x,125),t,font=font(16),fill='white')
    for n,(frame,title)in enumerate(rows):
        y=170+n*177;row=next(v for v in read(P108/'INPUT108.json')if v['name']==f'actual107-frame{frame}');a=np.flipud(plane(source_packet(row)/'H-product77-final.plane')[1])[:,:,:3];a=np.clip(a,0,1);rgb=np.rint(np.where(a<=.0031308,a*12.92,1.055*a**(1/2.4)-.055)*255).astype(np.uint8);head=Image.fromarray(rgb);head.save(H/f'frame{frame}-actual77-head.png');board.paste(head.resize((120,144),Image.Resampling.NEAREST),(24,y+20))
        dr.text((24,y-6),f'F{frame} {title}',font=font(15),fill='#dbe8f1')
        old=np.zeros((10,20),int);new=old.copy();stats=[]
        for owner in [1,2]:
            p=read(OLD/'separated'/f'frame{frame}-eye{owner}-result.json');ix=p.get('selectedIndicesWithinEnumeratedOptima',[])
            for j,(yy,xx)in enumerate(p['cells']):
                values={p['solutions'][i][j]for i in ix}
                if values:old[yy,xx+1]=next(iter(values))if len(values)==1 else 4
            c=next(v for v in data['cases']if v['dataset']==f'actual107-frame{frame}'and v['owner']==owner);a=np.array(c['labels'][0]);new[:a.shape[0],1:1+a.shape[1]]=np.maximum(new[:a.shape[0],1:1+a.shape[1]],np.where(a<0,4,a));stats.append(c)
            for extra in c['extraBoundarySourceLabelsOutsideOldROI']:
                yy,xx=extra['cellYX']
                if 0<=yy<len(new)and 0<=xx+1<new.shape[1]:new[yy,xx+1]=3
        board.paste(Image.fromarray(COL[old]).resize((260,130),Image.Resampling.NEAREST),(190,y+20));board.paste(Image.fromarray(COL[new]).resize((260,130),Image.Resampling.NEAREST),(520,y+20))
        for i,c in enumerate(stats):
            count=c['counts'][0];dr.text((800,y+22+i*40),f'눈{c["owner"]}: I/W/L {count["iris"]}/{count["white"]}/{count["upperLine"]}',font=font(16),fill='#d8e6ef')
        note='눈1 흰자 .862 / 눈2 홍채 .781·흰자 .344'if frame==105 else '위상0·0.5·1 라벨 배열 동일 (현재 입력)'if frame==125 else '셀 수는 결과값이며 강제한 디자인 수치 아님'
        dr.text((800,y+114),note,font=font(13),fill='#ffad9f'if frame==105 else'#b4cfdf')
    board.save(H/'BOUNDARY22_COMPARE.png')
    index='''<!doctype html><meta charset="utf-8"><title>Argon2.2 경계 후보</title><style>body{background:#111b26;color:#dbe8ee;font:17px/1.6 system-ui;max-width:1200px;margin:30px auto;padding:0 20px}a{color:#7ddaea}img{max-width:100%;image-rendering:pixelated}strong{color:#ffac9f}</style><h1>Argon2.2 경계 후보 — 오프라인, 미채택</h1><p>원본 <code>C:\\Users\\15352\\Desktop\\Argon2.2.md</code>는 수정하지 않았습니다. SHA256 <code>97ed2bf4efbf24136ec9769256abb6eb5aa0bfa28457bb71ef6fc9572631c3d4</code>. 그대로 보존한 <a href="references/Argon2.2.md">참고 문서</a>와 <a href="DOCUMENT_PROVENANCE.json">출처/해시</a>가 있습니다.</p><p>2/2.1의 독립 Layer0→눈→외부 머리 가림 구조를 유지하면서, 2.2의 핵심인 ‘상안검은 면적 경쟁 파트가 아니라 개구부 경계’라는 규칙을 한정 구현했습니다. 현재 눈 로컬 격자의 열 안에서 실제 색소 경로의 길이 가중 중심을 내리고, 위=바탕/경계=UpperLine/아래=102의 EyeUnion→Iris·White 분류를 적용했습니다. 구체적인 셀 수·갈색·RGB 혼합은 쓰지 않았습니다.</p><p>저장40입력에서 미확정0, 연결된 안검, 완전Close의 홍채·흰자0을 확인했습니다. 열린 눈은 홍채3/4셀, 실제 위상0·0.5·1의 라벨 배열이 양눈 모두 동일합니다. <strong>전체 규칙이 완성된 것은 아닙니다.</strong> Close75에서 양의 source I/W가 있는데 경계가 같은 행을 차지해 eye1의 흰자, eye2의 홍채·흰자가 모두 사라집니다. 총4개 눈/상태가 이 손실에 해당합니다. Source가 없는 것이 아니라 경계 stroke와 부분 개구부를 함께 픽셀화하는 기준이 더 필요합니다.</p><img src="BOUNDARY22_COMPARE.png"><p>그림은 실제77(왼쪽)과 false-colour 라벨 비교입니다. 신규 GPU/최종 RGB가 아닙니다. 원래 ROI 밖에 확인된 경계 라벨은 디버그에 함께 표시했으며, 실제 렌더에는 native 색소의 전체 span에서 유도한 새 bounds가 필요합니다(17입력).</p><p>110의 source cell을 실제 display 위치의 미이동 메쉬와 다시 교차시키는 조건은 세 경계 셀을 잘못 배제했습니다. 기존102는 source intrinsic cell을 display로 옮기므로 source 현재 색소 경로/가시성으로 계획해야 합니다. 그렇다고 source 한 점 깊이로 셀 전체를 덮는 것을 허용한 것은 아닙니다. GPU 합성에는 source footprint의 여러 UV/depth와 별도의 외부 가림을 유지해야 합니다.</p><p>전역 화면 x만 사용하는 열 규칙은90도 회전에서6셀→2셀이 되고, 급경사에서는 이웃 행이3칸 뜨는 반례가 있습니다. 등록된 eye-local frame과 곡선 래스터 계약이 필요합니다. 또한 문서의 strict ‘열당1셀’ 설명과 I+W=0이면 아래쪽도 허용하는 식은 다릅니다. 이번에는 strict 경계 해석만 사용했습니다.</p><p>색상 최근접 prototype은 모든 텍셀에 유한 colour label을 배정하지만 공간 연결성/특징 의미를 보장하지 않습니다. ΔE와 M≤4는 후보 스타일 정책입니다. P[r,q] 직접 대입은 같은r/q·변환에서 같은RGB를 보장할 뿐 Q 변화 자체를 멈추지는 않습니다. 새 팔레트/전신/외곽선은 아직 적용하지 않았습니다.</p><p><a href="RESULTS22.json">수치·최소반례</a> / <a href="aperture22.py">경계 함수</a> / <a href="verify22.py">같은 입력 검산</a>. 코드·그림·저장 결과만 작성했으며 Unity/Play/GPU/Assets 변경0입니다. 신규 시간 안정성·미감 성공을 선언하지 않습니다.</p>'''
    (H/'INDEX.html').write_text(index,encoding='utf8')
    source=Path(read(H/'DOCUMENT_PROVENANCE.json')['path']);assert hashlib.sha256(source.read_bytes()).hexdigest()==read(H/'DOCUMENT_PROVENANCE.json')['sha256']
    code={p.name:[{'function':n.name,'line':n.lineno}for n in ast.parse(p.read_text(encoding='utf8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]for p in H.glob('*.py')};(H/'CODE_INDEX22.json').write_text(json.dumps(code,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'positivePartLosses':lost,'phase':phase,'minimum':minimum,'documentOriginalHashUnchanged':True,'newGPU':0}))
if __name__=='__main__':main()
