from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet,ActorQuery
from review_packed93 import ribbon
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 root=H/'face97'/sys.argv[1];r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['Edit']and r['ownedResourcesReleased']and r['restorationChecksPass']and not r['errors'];assert r['stream77']['sourceAlpha97ManagedBytesAfterRelease']==0;rows=[];pictures=[];sequence=[];maxGreen=0.;samples=0;sourceErrors=[];changes=[]
 for f in r['stream77']['frames']:
  if '--selected-only'in sys.argv and 'actorSource96'not in f:continue
  a,_,_=packet(root,f);meta=f['joint97'];assert meta['frame']==f['frame']and meta['sourceId']==f['sourceId']and meta['sameFrameRuntimeCPUSelection']and not meta['GPUReadbackForSelection'];states=a[3,:,:,0];applied=a[3,:,:,3];assert np.isin(states,[0,1,2,3]).all()and np.isin(applied,[-1,0,1]).all();unknown=states==3;added=applied==1;ordinary=(~unknown)&(~added);assert np.array_equal(a[12][unknown],a[9][unknown]);assert np.array_equal(a[12][ordinary],a[5][ordinary]);ink=np.array(f['ribbon93']['originalInkLinear']+[1],np.float32);assert np.array_equal(a[12][added],np.broadcast_to(ink,(int(added.sum()),4)));greens={int(g[0]):g[1:]for g in meta['sourceGreens']};gErrors=[]
  for y,x in np.argwhere(a[6,:,:,0]>0):
   _,edge,t,g=a[6,y,x];ga,gb=greens[int(edge)];gErrors.append(abs(ga+(gb-ga)*float(t)-float(g)))
  maxGreen=max(maxGreen,max(gErrors,default=0));changed=(a[12]!=a[9]).any(2);removed=(states==2)&(a[10,:,:,3]==1);new=added&(a[10,:,:,3]!=1);rows.append({'frame':f['frame'],'CPUms':meta['CPUms'],'queries':meta['pointQueries'],'visits':meta['triangleVisits'],'indexEntries':meta['indexEntries'],'projectionInvariantChecks':meta.get('projectionInvariantChecks'),'knownSomeVisible':int((states==1).sum()),'fullyCovered':int((states==2).sum()),'unknown':int(unknown.sum()),'opaqueAdded':int(added.sum()),'changedVsControl':int(changed.sum()),'knownCoveredOldLineRemoved':int(removed.sum()),'newVisibleLineCells':int(new.sum()),'widthGreenMaximumError':max(gErrors,default=None)});changes += [{'frame':f['frame'],'xy':[int(x),int(y)],'state':int(states[y,x]),'applied':float(applied[y,x]),'wasOldLine':bool(a[10,y,x,3]==1)}for y,x in np.argwhere(changed)]
  if 'actorSource96'in f:
   q=ActorQuery(root,f);anchors=ribbon(root/'capture'/f['ribbon93']['file'])[4];shift=np.array([anchors[2]-anchors[0],-(anchors[3]-anchors[1])]);selected={tuple(v[:2]):v for v in meta['rows']}
   for y,x in np.argwhere(states==1):
    v=selected[x,y];p=np.array(v[4:6]);z=v[6]
    for label,point in [('source',p-shift),('destination',p)]:
     hit=q.query(point);samples+=1
     if not hit['known']or hit['hit']is not None and hit['hit']['depth']<z-1e-4:sourceErrors.append({'frame':f['frame'],'xy':[int(x),int(y)],'phase':label,'query':hit,'lineZ':z})
  p=Image.new('RGB',(1010,280),'#20252c');d=ImageDraw.Draw(p);d.text((12,8),f"ACTUAL97 frame {f['frame']}: current C# geometry selection -> GPU palette/ink composition. Product77 default unchanged.",fill='white')
  for i,(plane,label)in enumerate([(11,'Native baseline'),(5,'LUT92'),(9,'Control93'),(12,'Joint97')]):
   im=srgb(a[plane,:,:,:3]);p.paste(im,(12+i*225,31));p.paste(im.resize((208,208),Image.Resampling.NEAREST),(12+i*225,62));d.text((47+i*225,35),label,fill='white')
  d.text((914,80),'state3 keeps',fill='white');d.text((914,99),'exact control;',fill='white');d.text((914,118),'not transparent',fill='white');sequence.append(p)
  if len(pictures)<1 or 'actorSource96'in f:pictures.append(p)
 out={'actualGPUFrames':len(rows),'sameFrameRuntimeCPUSelector':True,'GPUSelectCompute':False,'GPUReplayOfOfflineColours':False,'exactCurrentLUTOrOriginalOutlineInk':True,'unknownPreservesExactControl':True,'knownSourceDestinationQuerySamples':samples,'knownSourceDestinationQueryErrors':sourceErrors,'maxWidthGreenError':maxGreen,'widthGPU8FractionalBitBound':1/128+16*float(np.finfo(np.float32).eps),'widthWithinBound':maxGreen<=1/128+16*float(np.finfo(np.float32).eps),'knownOldLineCellsRemoved':sum(p['knownCoveredOldLineRemoved']for p in rows),'newVisibleLineCells':sum(p['newVisibleLineCells']for p in rows),'rows':rows,'changes':changes,'generalOpaquePixelAreaOrIntegerLinePolicySolved':False,'continuousWorldOcclusionProven':False,'artAdopted':False};(root/('SELECTED_JOINT97.json'if '--selected-only'in sys.argv else'ACTUAL_JOINT97.json')).write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(1010,len(pictures)*280+74),'#20252c');d=ImageDraw.Draw(sheet)
 for i,p in enumerate(pictures):sheet.paste(p,(0,i*280))
 y=len(pictures)*280;d.text((12,y+8),f"Known hidden old-line cells removed: {out['knownOldLineCellsRemoved']}. Source/destination point errors: {len(sourceErrors)}.",fill='white');d.text((12,y+30),'Opaque1-cell expansion and general width/opacity policy remain unresolved. This is a visibility correction.',fill='white');sheet.save(root/('SELECTED_JOINT97.png'if '--selected-only'in sys.argv else'ACTUAL_JOINT97.png'));sequence[0].save(root/('SELECTED_SEQUENCE97.webp'if '--selected-only'in sys.argv else'ACTUAL_SEQUENCE97.webp'),save_all=True,append_images=sequence[1:],duration=80,loop=0,lossless=True);print(json.dumps({k:v for k,v in out.items()if k not in['rows','changes','knownSourceDestinationQueryErrors']}));assert not sourceErrors
if __name__=='__main__':main()
