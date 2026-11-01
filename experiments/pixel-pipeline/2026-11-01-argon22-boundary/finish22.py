"""Render role-map comparisons and update the existing experiment index."""
import json,ast,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from paths22 import H

def read(p):return json.loads(p.read_text(encoding='utf8'))
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
COL=np.array([[24,32,43],[60,202,233],[252,236,191],[191,124,252],[248,78,139]],np.uint8)
def combined(cases,frame):
    a=np.zeros((10,20),int)
    for owner in [1,2]:
        c=next(v for v in cases if v['dataset']==f'actual107-frame{frame}'and v['owner']==owner);maps=[np.array(v)for v in c['labels']];m=maps[0].copy()
        for b in maps[1:]:m[m!=b]=4
        a[:m.shape[0],1:1+m.shape[1]]=np.maximum(a[:m.shape[0],1:1+m.shape[1]],np.where(m<0,4,m))
        for v in c['extraBoundarySourceLabelsOutsideOldROI']:
            y,x=v['cellYX']
            if 0<=y<10 and 0<=x+1<20:a[y,x+1]=3
    return a

def main():
    local=read(H/'RESULTS22.json');area=read(H/'REGION_RESULTS22.json');topo=read(H/'TOPOLOGY_RESULTS22.json');check=read(H/'CHECK22.json');doc=read(H/'DOCUMENT_PROVENANCE.json');assert hashlib.sha256(__import__('pathlib').Path(doc['path']).read_bytes()).hexdigest()==doc['sha256']
    frames=[(99,'Open'),(101,'Close25'),(103,'Close50'),(105,'Close75: visible aperture'),(107,'Close100'),(204,'Hair ON; compare207/OFF')];board=Image.new('RGB',(1240,1380),'#101923');d=ImageDraw.Draw(board)
    d.text((22,15),'Argon2.2: source boundary + feature allocation (OFFLINE)',font=font(27),fill='white');d.text((22,58),'Actual77 head is a saved GPU image. The other columns are LABEL DEBUG, not final RGB or a new GPU render.',font=font(17),fill='#bed6e8');d.text((22,85),'Cyan=iris, cream=white, violet=UpperLine. Source-derived extra curve cells shown; final depth/alpha remains unverified.',font=font(16),fill='#bed6e8')
    titles=[(22,'Saved actual77'),(190,'2.2 + local half cutoff'),(500,'Region area only: rejected'),(810,'+ source-bank connectivity')]
    for x,t in titles:d.text((x,125),t,font=font(17),fill='white')
    for n,(frame,title)in enumerate(frames):
        y=170+n*195;d.text((22,y-5),f'F{frame} {title}',font=font(17),fill='#dce9f4');head=Image.open(H/f'frame{frame if frame!=204 else 101}-actual77-head.png').convert('RGB')
        if frame==204:
            # Load the exact204 packet instead of substituting a different pose.
            from stored110 import P108,source_packet,plane
            row=next(v for v in read(P108/'INPUT108.json')if v['name']=='actual107-frame204');q=np.clip(np.flipud(plane(source_packet(row)/'H-product77-final.plane')[1])[:,:,:3],0,1);rgb=np.rint(np.where(q<=.0031308,q*12.92,1.055*q**(1/2.4)-.055)*255).astype(np.uint8);head=Image.fromarray(rgb);head.save(H/'frame204-actual77-head.png')
        board.paste(head.resize((120,144),Image.Resampling.NEAREST),(22,y+25))
        for x,data in [(190,local),(500,area),(810,topo)]:
            a=combined(data['cases'],frame);im=Image.fromarray(COL[a]);board.paste(im,(x,y+24));board.paste(im.resize((280,140),Image.Resampling.NEAREST),(x,y+40))
            text=[]
            for owner in [1,2]:
                c=next(v for v in data['cases']if v['dataset']==f'actual107-frame{frame}'and v['owner']==owner);v=c['counts'][0];text.append(f'E{owner} I/W/L {v["iris"]}/{v["white"]}/{v["upperLine"]}')
            d.text((x,y+181),' | '.join(text),font=font(13),fill='#d1e6f3')
    d.text((22,1350),'No new Unity/Play/Assets changes. Not adopted. White-component/partial-aperture representation and final composition remain open.',font=font(16),fill='#ffb2a7');board.save(H/'ARGON22_BOUNDARY_ABLATION.png')
    # Save actual-size role maps as well as the nearest-neighbour board.
    for frame,_ in frames:
        for name,data in [('local',local),('area-only',area),('topology',topo)]:Image.fromarray(COL[combined(data['cases'],frame)]).save(H/f'frame{frame}-{name}-labels.png')
    irisBad=lambda data:sum(any(len(v.get('irisComponents4',[]))>1 for v in c['counts'])for c in data['cases'])
    partial=[{'frame':c['frame'],'owner':c['owner'],'lost':c['positiveSourcePartsLost']}for c in topo['cases']if c['positiveSourcePartsLost']]
    status={'sourceDocument':doc,'newUnityCalls':0,'newGPU':0,'productApplied':False,'stage':'offline candidate and counterexamples; not a complete renderer','localHalfCutoffEyeUnionLossCases':local['summary']['casesWithPositiveVisibleSourcePartExtinguished'],'regionAreaOnlySplitIrisCases':irisBad(area),'sourceTopologySplitIrisCases':irisBad(topo),'partialSourcePartLosses':partial,'completeLayoutEnumeration':True,'enumerationCap110IsNotTotal':{'retainedWitnessLimit':64,'frame99Eye1PrimaryOptimaAtLeast':68,'frame103Eye1PrimaryOptimaCompletelyEnumerated':32},'sameInputPhaseCanonicalSetsEqual':topo['summary']['phase'],'ambiguousSourceFormCases':topo['summary']['ambiguousSourceFormCases'],'ROIExpansionCases':local['summary']['casesRequiringSourceDerivedROIBeyondOldPadding'],'sourceCurveCarrierMissingAfterCoordinateFix':0,'sourceCurveIsNotAutomaticallyAnatomicalApertureEdge':True,'finalPaletteOrOutlineValidated':False,'newTemporalRGBValidated':False,'runtimeCost':'exact offline subset enumeration only: current candidates <=9 iris/12 white; no per-frame GPU implementation or performance claim'}
    (H/'STATUS22.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
    html='''<!doctype html><meta charset="utf-8"><title>Argon2.2 경계 실험</title><style>body{background:#101923;color:#dce9f2;font:17px/1.65 system-ui;max-width:1280px;margin:28px auto;padding:0 18px}a{color:#79d9ed}img{max-width:100%;image-rendering:pixelated}code{overflow-wrap:anywhere}strong{color:#ffb4a4}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #41556c}</style><h1>Argon2.2 경계·전체 특징 배정 — 오프라인, 미채택</h1>
<p>원본 <code>C:\\Users\\15352\\Desktop\\Argon2.2.md</code>는 수정하지 않았습니다. SHA256 <code>97ed2bf4efbf24136ec9769256abb6eb5aa0bfa28457bb71ef6fc9572631c3d4</code>. <a href="references/Argon2.2.md">보존된 원문</a> / <a href="DOCUMENT_PROVENANCE.json">정확한 경로·해시</a>.</p>
<p>2/2.1의 Layer0·눈·외부 머리 가림 분리는 유지합니다. 2.2에서 가져온 핵심은 <b>안검의 색소 곡선을 면적 경쟁자가 아닌 개구부 경계로 취급</b>하는 것입니다. 실제109 색소 경로를 등록된 눈 로컬 좌표로 투영하고, 열마다 잘린 곡선의 호 길이 가중 중심 행을 사용했습니다. 이것은 구현 가능한 명시적 가설이며, 원본 제작자의 해부학적 눈 경계를 복원했다고 주장하지 않습니다.</p>
<p>3개 누락은 source 셀을 이동 후 화면 위치의 mesh로 다시 검사한 좌표계 불일치였습니다(F105·109 눈1 x10/y4, F147 눈1 x10/y5). current source 곡선 표본으로 검사하면 누락0입니다. <strong>한 source 점의 깊이를 목적지 셀 전체에 복사해도 된다는 뜻은 아닙니다.</strong> 실제 합성은 footprint별 UV·depth·alpha와 외부 머리 가림을 별도로 판정해야 합니다. 기존 bank+padding 밖 곡선이 있는17입력의 bounds 확장도 아직 런타임에 연결하지 않았습니다.</p>
<p>문서 방향만으로 아래쪽에 기존 셀별50% 문턱을 적용하면 Close75의 가시 눈까지 사라집니다. 눈1 흰자0.862, 눈2 홍채0.781·흰자0.344셀의 가시량이 실제 입력에 있습니다. 이를 전체 EyeUnion 면적 오차→자식 색소 면적 오차→source 재구성 오차 순서로 배정하면 전멸은 막지만, 홍채의 새 대각 분절이 생깁니다. 따라서 연결된 원본 홍채 bank와 현재 확실한 source 연결 표지를 함께 제약으로 사용했습니다. 흰자 bank는 원래 분리돼 있어 무조건 연결하지 않았습니다. 면적은 고정 셀 수가 아니라 현재 입력의 오차 항이며, 안검에는 면적 할당량을 주지 않았습니다.</p>
<p>Close75의 남은2후보는 상대배치 검사의 ‘관측된 source 쌍 없음’을 오차0으로 취급하던 것이 원인이었습니다. 미측정 geometry를 <code>null</code>로 기록하고 명시적 source 대응 손실을 유지하면 현재 후보는 하나로 좁혀집니다. 미측정값을 완벽한 형상이라고 비교한 잘못을 고친 것이며, 임의 가중치나 첫 후보 선택이 아닙니다.</p>
<img src="ARGON22_BOUNDARY_ABLATION.png" alt="기존 GPU와 세 단계 label ablation">
<p>왼쪽만 저장된 실제77 GPU 이미지이고, 나머지는 역할을 보여주는 label debug입니다. <strong>후보의 최종 RGB 렌더가 아닙니다.</strong> 실제 입력40개, 작은 완전탐색 oracle12개와 내부 배정 D4검사96개를 검산했습니다. 현재 source가 연결된 홍채의 새 분절0, 가시 EyeUnion 전체 소실0, 완전Close 홍채·흰자 재생성0, 위상0·0.5·1의 canonical 배열 동일입니다. 이 결과는 새 시퀀스의 시간 안정성·최종 외부 가림·색·외곽선 완성을 뜻하지 않습니다.</p>
<p><strong>남은 반례:</strong> Close75 눈2의 작은 흰자는 0.344셀의 확실한 가시량이 있어도 현재 영역 예산에서는 생략됩니다. 흰자 bank의 여러 원형 클러스터와 source 대응을 더 구체적으로 보존해야 하며, 모든 양의 alpha를 무조건1셀로 승격할 수도 없습니다. 또 문서의 전역 x당1셀 규칙은90도 회전에서6→2셀, 급경사에서 이웃 행3/2칸 점프 반례가 있습니다. 현재 검사는 등록된 canonical frame에 한정합니다. 문서의 strict1행 설명과 I+W=0이면 아래쪽도 안검으로 두는 식은 서로 다르며, 이번 실험은 strict 경계 설명만 따랐습니다.</p>
<p>유한 팔레트 <code>P[region,q]</code>는 타당한 출력 계약이지만 색 prototype 수·ΔE 임계값·볼 병합은 별도의 표현 정책입니다. 총 colour label 지정은 공간 연결 영역을 자동 증명하지 않습니다. 이 작업에서는 얼굴 팔레트나 외곽선·명암 범위를 수정하지 않았습니다. 같은 RGB 보장은 region/q/encoding이 같을 때만 성립합니다.</p>
<p>110의64는 열거 상한입니다. F99 눈1의1차 기하 최적해는 적어도68개이며 전체 수는 미집계입니다. iris1~5는 bank/history 적용 전 범위입니다. F103의32개는 그1차 문제에서만 완전 열거했습니다. 이번 작은 배정 문제는 모든 최적해를 열거한 후 source를 비교했고, cap으로 자른 표본을 최종 유일해라고 부르지 않았습니다.</p>
<p><a href="STATUS22.json">현재 범위·한계</a> / <a href="CHECK22.json">검증</a> / <a href="RESULTS22.json">문서+셀별 문턱</a> / <a href="REGION_RESULTS22.json">면적만: 실패 보존</a> / <a href="TOPOLOGY_RESULTS22.json">source 구조 제약 결과</a> / <a href="CODE_INDEX22.json">함수 위치</a>. Unity/Play/GPU/Assets 변경0. 원본과 제품77 보존. 기존 저장소 handoff만 최신화하며 외부 Argon과 직접 통신하지 않았습니다.</p>'''
    (H/'INDEX.html').write_text(html,encoding='utf8')
    code={p.name:[{'function':n.name,'line':n.lineno}for n in ast.parse(p.read_text(encoding='utf8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]for p in H.glob('*.py')};(H/'CODE_INDEX22.json').write_text(json.dumps(code,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in status.items()if k!='sourceDocument'}))
if __name__=='__main__':main()
