from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from uv_features64 import extract,colour_intervals,lab,palette_invariant,source_key
R=Path(__file__).resolve().parent

def gray_L(L):
 v=np.asarray(L)**3;s=np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055);q=np.clip(np.floor(s*255+.5),0,255).astype('uint8');return np.repeat(q[:,:,None],3,axis=2)
fixtures=[];W=H=65;X,Y=np.meshgrid(np.arange(W),np.arange(H));mask=np.ones((H,W),bool)
two=((X>=10)&(X<22)&(Y>=12)&(Y<24))|((X>=42)&(X<54)&(Y>=40)&(Y<52))
for name,rgb in [('constant',np.full((H,W,3),[50,28,29],np.uint8)),('linear-L',gray_L(.2+.4*X/(W-1))),('quadratic-L',gray_L(.2+.3*(X/(W-1))**2)),('step',np.where((X<32)[:,:,None],np.array([50,28,29],np.uint8),np.array([170,109,86],np.uint8))),('two-same-colour-motifs',np.where(two[:,:,None],np.array([170,109,86],np.uint8),np.array([50,28,29],np.uint8))),('one-texel-line',np.where((X==32)[:,:,None],np.array([170,109,86],np.uint8),np.array([50,28,29],np.uint8))),('three-texel-line',np.where(((X>=31)&(X<=33))[:,:,None],np.array([170,109,86],np.uint8),np.array([50,28,29],np.uint8))),('one-texel-dot',np.where(((X==32)&(Y==32))[:,:,None],np.array([170,109,86],np.uint8),np.array([50,28,29],np.uint8))),('smooth-narrow-bump',gray_L(.2+.25*np.exp(-((X-32)/1.2)**2)) )]:
 before=hashlib.sha256(rgb.tobytes()).hexdigest();e=extract(rgb,mask);assert hashlib.sha256(rgb.tobytes()).hexdigest()==before
 counts={'persistentX':int(e['x']['persistent'].sum()),'persistentY':int(e['y']['persistent'].sum()),'fineX':int(e['x']['fine'].sum()),'fineY':int(e['y']['fine'].sum()),'thinRidgeCells':int((e['thinRidgeX']|e['thinRidgeY']).sum()),'coarseRegions':e['coarseRegions'],'fineRegions':e['fineRegions'],'persistentContourComponents':len(e['contourHierarchy']['persistent']),'fineContourComponents':len(e['contourHierarchy']['fine'])}
 if name in ['constant','linear-L','quadratic-L']:assert counts['persistentX']==counts['persistentY']==0,(name,counts)
 if name=='step':assert e['x']['persistent'][:,31][8:-8].all(),counts
 if name=='step':assert counts['coarseRegions']==counts['fineRegions']==2,counts
 if name=='one-texel-line':assert e['thinRidgeX'][:,32].all(),counts
 if name in ['three-texel-line','one-texel-dot']:assert counts['fineX']+counts['fineY']+counts['thinRidgeCells']>0,counts
 if name=='smooth-narrow-bump':assert counts['persistentX']==counts['persistentY']==0,counts
 if name=='two-same-colour-motifs':assert counts['coarseRegions']==3 and counts['persistentContourComponents']==2,counts
 fixtures.append({'name':name,**counts,'sourceRGBUnchanged':True,'meaning':'thin/ridge evidence is not proof of a painted semantic feature'if name in ['one-texel-line','smooth-narrow-bump']else'source signal fixture'})
 debug=np.zeros((H,W,3),np.uint8);debug[e['x']['fine']|e['y']['fine']]=[230,170,50];debug[e['x']['persistent']|e['y']['persistent']]=[60,225,160];debug[e['thinRidgeX']|e['thinRidgeY']]=[230,80,200]
 board=Image.new('RGB',(W*8*2,H*8+30),(24,26,31));draw=ImageDraw.Draw(board)
 board.paste(Image.fromarray(rgb).resize((W*8,H*8),Image.Resampling.NEAREST),(0,30));board.paste(Image.fromarray(debug).resize((W*8,H*8),Image.Resampling.NEAREST),(W*8,30));draw.text((0,5),name,fill='white');draw.text((W*8,5),'green persistent / amber fine / pink ridge',fill='white');board.save(R/f'FIXTURE64-{name}.png')

# A non-trivial interval test: interior RGB samples must stay in propagated Lab
# bounds. It checks numeric implementation, not a universal artistic guarantee.
rng=np.random.default_rng(6401);rgb=rng.integers(1,255,(8,8,3),dtype=np.uint8);_,lo,hi=colour_intervals(rgb);violations=0
for _ in range(50):
 actual=lab(rgb+rng.uniform(-.5,.5,rgb.shape));violations+=int(np.any((actual<lo)|(actual>hi),axis=2).sum())
assert violations==0
assert source_key(rgb,mask[:8,:8],[2,4,8])==source_key(rgb.copy(),mask[:8,:8].copy(),[2,4,8])
assert source_key(rgb,mask[:8,:8],[2,4,8])!=source_key(rgb,mask[:8,:8],[2,4])
syntheticRows=[{'x':0,'y':0,'Q':0,'materialId':11,'sourceRegionId':'shape-a'},{'x':1,'y':0,'Q':0,'materialId':12,'sourceRegionId':'shape-b'}]
assert not palette_invariant(syntheticRows,[[50,28,29]]*2,[[50,28,29]]*2)
assert len(palette_invariant(syntheticRows,[[50,28,29]]*2,[[50,28,29],[48,26,27]]))==1

S=R.parent/'source-regions62'
if not S.exists():S=R.parent/'2026-10-31-source-regions62'
d=json.loads((S/'CELLS62.json').read_text());contradictions=palette_invariant(d['rows'],d['sourceRGB8'],d['beforeLineRGB8']);coords={(r['x'],r['y']):i for i,r in enumerate(d['rows'])};pairs=[]
for (x,y),i in coords.items():
 for dx,dy in [(1,0),(0,1)]:
  j=coords.get((x+dx,y+dy))
  if j is not None and d['sourceRGB8'][i]==d['sourceRGB8'][j]and d['rows'][i]['Q']==d['rows'][j]['Q']and d['beforeLineRGB8'][i]!=d['beforeLineRGB8'][j]:pairs.append([[x,y],[x+dx,y+dy]])
assert len(pairs)==18
out={'fixtures':fixtures,'intervalInteriorSamples':8*8*50,'intervalViolations':violations,'materialAnchorInvariant':{'legacyAdjacentContradictions':18,'allEqualInputContradictoryCohorts':len(contradictions),'pairs':pairs,'cohorts':contradictions,'baselinePass':False,'newPaletteCreated':False,'RGBOrRegionChanged':False},'newUnityCalls':0,'artisticAcceptance':False,'semanticResolution':'painted thin mark versus identical smooth highlight cannot be decided from RGB alone'}
(R/'TEST64.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items()if k!='materialAnchorInvariant'},indent=2));print('baseline equal-input check: FAIL18 adjacent pairs (preserved evidence)')
