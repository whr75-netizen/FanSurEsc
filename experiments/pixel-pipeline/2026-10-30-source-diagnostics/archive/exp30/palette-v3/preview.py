from pathlib import Path
import json
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34\source-export\bundle')
data={'model':load(R/'SHARED_NATIVE_PALETTE.json'),'binding':load(R/'BINDINGS.json'),'frame':load(B/'frame-source-data.json')}
summary=load(R/'SUMMARY.json');examples=load(R/'PIXEL_EVIDENCE.json')
cards=''
for name,title in [('preserve','원본 무늬 보존안'),('simplify','중간톤 경로 정규화안')]:
 cards+='<h2>'+title+' / 같은 입력</h2><div class="grid">'
 for label,caption in [('source','실제 선택 UV 원색'),('old','기존 v2 두 기준색'),('existing16','같은 기존16색 공유 / 매핑 효과만'),('new','원본 구간 재분배16색 / 새 후보')]:
  cards+=f'<article><h3>{caption}</h3><a href="{name}-{label}-8x.png"><img class="head" src="{name}-{label}-1x.png" alt="{title} {caption}"></a></article>'
 cards+='</div>'
cells='<table><tr><th>로컬 셀 / Q</th><th>실제 원색</th><th>기존 최종</th><th>새 최종</th></tr>'
for r in examples['preserve']:cells+=f'<tr><td>{r["cell"]} / {r["shadeK"]}</td><td>{r["sourceRGB8"]}<br>L {r["sourceLabL"]:.6f}</td><td>{r["oldRGB8"]}<br>L {r["oldLabL"]:.6f}</td><td>{r["newRGB8"]}<br>L {r["newLabL"]:.6f}</td></tr>'
cells+='</table>'
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>원색 팔레트 매핑 점프 수정 후보</title>
<style>body{font:15px/1.6 "Malgun Gothic",sans-serif;background:#202126;color:#eee;margin:24px;max-width:1500px}h1{font-size:25px}h2{margin-top:35px}a{color:#a9cdf5}.note{background:#3b3031;padding:15px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.controls{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:#292a30;padding:12px}h3{font-size:16px}img,canvas{image-rendering:pixelated;max-width:100%}.head{width:256px;height:320px}table{border-collapse:collapse}td,th{border:1px solid #666;padding:8px}.sw{display:inline-block;width:30px;height:26px;border:1px solid #999;margin:2px}input{width:330px;max-width:90%}output{font-variant-numeric:tabular-nums}code{overflow-wrap:anywhere}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}.controls{grid-template-columns:1fr}}</style>
<h1>원색 팔레트 매핑의 큰 점프 수정 — 별도 후보</h1>
<p class="note">tone-boundary의 미채택 1셀 변경은 사용하지 않았습니다. 이전 보존안·정규화안의 실제 UV 원색/기하/Q(g)를 고정했습니다. 두 미술안 중 하나를 채택하지 않았고, R6·31·34·Unity·원본 결과를 수정하지 않았습니다.</p>
<p><a href="REPORT_KO.md">원인·검증·남은 분절</a> · <a href="CONTRACT_DIFF.md">main 연결 계약</a> · <a href="SHARED_NATIVE_PALETTE.json">팔레트 모델</a> · <a href="BINDINGS.json">원본 샘플과 셀 ID</a> · <a href="EDGES.json">새 경계·병합 경계 전부</a> · <a href="SUMMARY.json">비교 수치</a></p>
<p>같은 Q=2인 두 셀의 원본 L 차이 0.022170이 기존 매핑에서 0.260591로 커졌습니다. 새 후보는 같은 근접 native 기준색을 선택합니다. palette-v2의16색 예산을 유지하고, 실제 원본 텍스처의 명도 범위에 고르게 구간을 배정해 각 구간의 실제 texel medoid를 사용했습니다.</p>
__CARDS__
<h2>실제 문제 셀 / 보존안</h2>__CELLS__
<h2>왼쪽 아래 확대 / 원색·기존·새 후보</h2><div class="grid"><article><img src="preserve-source-lower-left.png"></article><article><img src="preserve-old-lower-left.png"></article><article><img src="preserve-new-lower-left.png"></article></div>
<p class="note">큰 거짓 점프는 줄었지만 새 톤 분절은 생겼습니다. 보존안에서 기존에 같던 최종색 사이에 새 경계113개가 생겼고, 한 셀짜리 색 연결영역은44→106개입니다. 원본 색차는113개 모두 존재하지만 모든 분절을 미술 특징으로 인정할 수는 없습니다. 이 후보를 영역 정돈·시간 안정성 완료로 판정하지 않았습니다.</p>
<h2>직접 입력: 각 안의 팔레트 간격 배율</h2><p>배율은 팔레트 기준색 주변의 명암 간격만 바꿉니다. 원색 선택 ID, appearance, Q(g), UV, g, 다른 안의 입력값은 고정됩니다. 파생 색표는 직접 입력 슬라이더가 아닙니다.</p>
<div class="controls"><article><h3>보존안 검사</h3><label>간격 m <input id="preserve-m" type="range" min="0" max="2" step="0.01" value="1"></label> <output id="preserve-value">1.00</output><p><canvas id="preserve-result" width="64" height="80" class="head"></canvas></p><div id="preserve-palette"></div></article><article><h3>정규화안 검사</h3><label>간격 m <input id="simplify-m" type="range" min="0" max="2" step="0.01" value="1"></label> <output id="simplify-value">1.00</output><p><canvas id="simplify-result" width="64" height="80" class="head"></canvas></p><div id="simplify-palette"></div></article></div>
<p id="status"></p><p>각 안의 358셀은 완성된 P[원색 기준 ID][Q(g)]를 직접 출력합니다. 미확정10셀과 머리 외부·alpha는 그대로입니다. 단계0/1과2/3의 각 쌍이 같은 RGB인 구조는 이전 후보와 같습니다. 표본별 원색 값을 후단 RGB에 다시 곱하지 않습니다.</p>
<script id="data" type="application/json">__DATA__</script><script src="palette_math.cjs"></script><script src="palette.cjs"></script><script>
const data=JSON.parse(document.getElementById('data').textContent),inputs={preserve:1,simplify:1},initial=JSON.stringify(data.binding),source=JSON.stringify(data.frame),basePixels=Uint8ClampedArray.from(atob(data.frame.originalRGBA),c=>c.charCodeAt(0));let results={};
function draw(name){
 const m=inputs[name],P=PaletteV3.buildPalette(data.model,m),rgba=basePixels.slice(),ids=[];
 for(const r of data.binding.variants[name].rows){if(!r||r.unresolved){ids.push(r?-2:-1);continue;}const v=PaletteV3.referenceForSample(data.model,r.sample,{colourGroupId:r.appearance,uncertain:false});ids.push(v.paletteReferenceId);const rgb=P.tablesRGB8[v.paletteReferenceId][r.shadeK];
  for(let dy=0;dy<2;dy++)for(let dx=0;dx<2;dx++){const p=((Math.floor(r.index/32)*2+dy)*64+r.index%32*2+dx)*4;rgba.set(rgb,p);}
 }
 document.getElementById(name+'-result').getContext('2d').putImageData(new ImageData(rgba,64,80),0,0);document.getElementById(name+'-value').value=m.toFixed(2);
 document.getElementById(name+'-palette').innerHTML=P.tablesRGB8.map((row,i)=>'<span title="기준 '+i+' / '+data.model.references[i].anchorRGB8.join(',')+'">'+row.map(rgb=>'<span class="sw" title="'+rgb.join(',')+'" style="background:rgb('+rgb.join(',')+')"></span>').join('')+'</span><br>').join('');
 results[name]={pixels:Array.from(rgba),referenceIds:ids,tables:P.tablesRGB8};
 document.getElementById('status').textContent='원본/영역/명암 라벨 고정 · 두 안의 간격 입력 독립';
}
for(const name of ['preserve','simplify']){document.getElementById(name+'-m').addEventListener('input',e=>{inputs[name]=Number(e.target.value);draw(name);});draw(name);}
window.workbench={ready:true,snapshot:()=>structuredClone({inputs,results,sourceAndRegionsUnchanged:JSON.stringify(data.binding)===initial&&JSON.stringify(data.frame)===source})};
</script></html>'''
html=html.replace('__CARDS__',cards).replace('__CELLS__',cells).replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/'))
(R/'INDEX.html').write_text(html,encoding='utf-8');print('preview ready')
