from pathlib import Path
import array,ast,base64,collections,hashlib,json,struct,zipfile
from pngio import read
R=Path(__file__).resolve().parent;B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34');current=B/'region-colour40/contrast-bounded';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();data=load(R/'INPUT.json');palette=load(R/'PALETTE_LEGACY.json');result={}
def npz(path):
 out={}
 with zipfile.ZipFile(path)as z:
  for n in z.namelist():
   raw=z.read(n);h=struct.unpack_from('<H',raw,8)[0];meta=ast.literal_eval(raw[10:10+h].decode());v=array.array({'<i8':'q'}[meta['descr']]);v.frombytes(raw[10+h:]);out[n[:-4]]=list(v)
 return out
for name in ['preserve','simplify']:
 model=load(current/f'MODEL_{name.upper()}.json');labels=npz(current/f'{name}-LABELS.npz');w,h,rgba=read(current/f'{name}-after-1x.png');rows=[];off=[];Qerrors=[]
 for c in data['cells']:
  if not c:rows.append(None);continue
  i=c['index'];p=(i//32*2*64+i%32*2)*4;rgb=tuple(rgba[p:p+3]);known=labels['colourRegion'][i]>=0;ref=labels['reference'][i];q=labels['shade'][i]
  if known:
   if q!=c['Q']:Qerrors.append(i)
   expected=model['compactPaletteRGB8'][model['perReferenceShadePaletteIndices'][ref][q]]
   if list(rgb)!=expected:off.append(i)
  rows.append({'RGB':rgb,'known':known,'family':0,'Q':q,'featureDomain':labels['featureDomain'][i],'colourRegion':labels['colourRegion'][i],'reference':ref})
 def mapping(fields):
  table=collections.defaultdict(set)
  for r in rows:
   if r and r['known']:table[tuple(r[k]for k in fields)].add(r['RGB'])
  return{'groups':len(table),'multiRGB':sum(len(v)>1 for v in table.values())}
 allRGB={r['RGB']for r in rows if r};knownRGB={r['RGB']for r in rows if r and r['known']};unknownRGB={r['RGB']for r in rows if r and not r['known']};fullPalette={tuple(c)for c in model['compactPaletteRGB8']}
 result[name]={'sourceId':model['sourceId'],'samePrimarySource':model['sourceId']==data['context']['primarySourceId'],
  'sameFrozenPaletteTable':model['perReferenceShadePaletteIndices']==palette['perReferenceShadePaletteIndices']and model['compactPaletteRGB8']==palette['compactPaletteRGB8'],
  'sameSourceSelector':model['sourceSelectionKnots']==palette['sourceSelectionKnots'],'knownCells':sum(bool(r and r['known'])for r in rows),'unknownCells':sum(bool(r and not r['known'])for r in rows),
  'finalRGBUniqueFullMask':len(allRGB),'finalRGBUniqueKnown':len(knownRGB),'unknownRGBUnique':len(unknownRGB),'fullMaskOffPaletteCells':sum(r['RGB']not in fullPalette for r in rows if r),
  'unknownOffPaletteCells':sum(r['RGB']not in fullPalette for r in rows if r and not r['known']),'knownOffPaletteCells':len(off),'QErrorsAgainstFrozenGeometry':Qerrors,
  'featureDomain_Q_to_RGB':mapping(['featureDomain','Q']),'colourRegion_Q_to_RGB':mapping(['colourRegion','Q']),'reference_Q_to_RGB':mapping(['reference','Q']),
  'meaning':'featureDomain is not a flat colour label; colourRegion/reference+Q is actual emission contract. Unknown cells deliberately retain original display RGB, not post-AA additions.',
  'filesSHA256':{p.name:sha(p)for p in [current/f'MODEL_{name.upper()}.json',current/f'{name}-LABELS.npz',current/f'{name}-after-1x.png']}}
(R/'CURRENT_PIPELINE_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
