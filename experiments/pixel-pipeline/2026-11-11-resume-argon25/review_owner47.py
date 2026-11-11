from pathlib import Path
import json,numpy as np
from native_contour42 import coordinates,oracle
H=Path(__file__).resolve().parent;G=H/'face47';C=G/'capture'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors'];rows=[]
 for f in r['frames']:
  def read(name):
   p=next(p for p in r['planes']if p['frame']==f['frame']and p['name']==name);return np.fromfile(C/p['file'],dtype='<f4').reshape(p['height'],p['width'],4)
  a=read('atlas40');w=f['QROI'][2];assert a.shape[1]==16*w;fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');assert b.shape[1]==4*w;back=[b[:,i*w:(i+1)*w]for i in range(4)];current=read('currentColour47');info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);expected,gate=oracle(fields[3],fields[4],fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink);assert expected.tobytes()==fields[10].tobytes()and gate.tobytes()==fields[11].tobytes();use=gate[:,:,3]==1;native=fields[14][:,:,2]==1;kind=np.where(use,1,np.where(native,2,3));assert np.isfinite(b).all()and np.all(back[3][:,:,3]==1)and np.all(fields[15][:,:,0]==kind)and np.all(fields[15][:,:,2]==1)
  rawOwner=fields[12][:,:,[1,2,0,3]];assert np.array_equal(back[0][native],rawOwner[native])and np.all(back[0][~native]==0);assert np.array_equal(back[2][~use],back[0][~use]);assert np.all(back[2][use,0]==fields[4][use,1])and np.all(back[2][use,1]==fields[4][use,2])and np.all(back[2][use,2:]==0)
  different=native&(fields[9][:,:,:3]!=current[:,:,:3]).any(2);role=np.rint(back[0][:,:,0]).astype(int);counts={}
  for value in np.unique(role[native]):
   mask=native&(role==value);counts[str(value)]={'pixels':int(mask.sum()),'beforeRGBCount':len(np.unique(fields[9][mask,:3],axis=0)),'currentRGBCount':len(np.unique(current[mask,:3],axis=0)),'nativeVsCurrentRGBDifferent':int((mask&different).sum()),'primitivePayloadRange':[float(back[0][mask,3].min()),float(back[0][mask,3].max())]}
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'typedCounts':{str(i):int((kind==i).sum())for i in [1,2,3]},'nativeOwnerBytePreserved':True,'curveNeverAliasesPrimitive':True,'invalidOwnerReceipts':0,'nativeVsCurrentRGBDifferent':int(different.sum()),'roles':counts})
 result={'actualFrames':len(rows),'GPUContractPass':True,'types':{'1':'SourceCurve(edge,t)','2':'OriginalNativeProducerOwner raw role/renderer/depth/primitive payload, not guessed real mesh triangle','3':'WorldUnresolved; original Native395 world has no object/primitive ID'},'sourceRGBAOrPaletteChanged':False,'productionHistoryChanged':False,'currentColourReceipt':'same-frame main.colour before Native395 optional colour history; q matches actual Native395 cell receipt','historyCausalityLimit':'RGB difference alone is not enough to classify intended temporal stylization or a defect; no palette/Q history was invented','rows':rows};(G/'ACTUAL_OWNER47.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
