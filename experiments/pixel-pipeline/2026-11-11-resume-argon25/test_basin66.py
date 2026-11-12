from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_basin66 import witnesses
H=Path(__file__).resolve().parent;G=H/'face66'
def transform(a,k,mirror):return np.rot90(a[:,::-1]if mirror else a,k)
def main():
 tests=0;cases=[]
 rgba=np.full((17,17,4),255,np.uint8);rgba[:,:,:3]=[220,190,160];rgba[6:11,7:10,:3]=[218,175,155];mask=np.ones((17,17),bool);m=witnesses(rgba,mask,(8,8));assert m['core'][8,8] and not m['nominalUnion'][0,0];tests+=1
 # Distinct motifs remain distinct even with exactly the same original RGB.
 rgba[2:5,2:5,:3]=[218,175,155];m=witnesses(rgba,mask,(8,8));assert not m['nominalUnion'][3,3];tests+=1
 for mirror in [False,True]:
  for k in range(4):
   z=witnesses(transform(rgba,k,mirror),mask,(8,8));assert np.array_equal(z['core'],transform(m['core'],k,mirror))and np.array_equal(z['nominalUnion'],transform(m['nominalUnion'],k,mirror));tests+=1
 # A monotone gradient and a two-colour monotone AA transition have no positive
 # interior colour extremum: never turn their unknowns into deletion permission.
 for profile in [np.arange(17),np.clip(np.arange(17)-6,0,4)*4]:
  a=np.full((17,17,4),255,np.uint8);a[:,:,:3]=180+profile[None,:,None];z=witnesses(a,mask,(8,8));assert not z['witnesses'] and not z['familyConfirmed'];tests+=1
 source=np.load(H/'face28/SOURCE_NATIVE28.npz');r=witnesses(source['rgba'],source['mask'],(382,704));assert r['witnesses'] and r['core'][704,382];tests+=1
 np.savez_compressed(G/'SOURCE_BASIN66.npz',core=r['core'],nominalUnion=r['nominalUnion'])
 points=[]
 for x,y in [(382,704),(380,704),(384,704)]:points.append({'xy':[x,y],'RGB8':source['rgba'][y,x,:3].tolist(),'robustCore':bool(r['core'][y,x]),'nominalPossible':bool(r['nominalUnion'][y,x])})
 result={'CPUChecks':tests,'actualSourceRGBAChanged':0,'realWeakPaintPoints':points,'actualWitnesses':r['witnesses'],'robustCoreTexels':int(r['core'].sum()),'nominalUnionTexels':int(r['nominalUnion'].sum()),'axesAndScalesAgreeOnWholeRegion':r['uniqueNominal'],'familyConfirmed':False,'newUnityGPUCalls':0,'interpretation':'Closed measured source components preserve the weak witness. Different axes/scales and AA uncertainty remain visible; no complete semantic region or palette mapping is inferred.'}
 (G/'CPU_BASIN66.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 box=(310,620,425,710);src=source['rgba'][620:710,310:425,:3];debug=src.copy();debug[r['nominalUnion'][620:710,310:425]]=[240,170,30];debug[r['core'][620:710,310:425]]=[30,210,220];board=Image.new('RGB',(690,300),(28,30,35));d=ImageDraw.Draw(board)
 for i,(a,title)in enumerate([(src,'Actual native source'),(debug,'Cyan: robust core | orange: axis/scale possible')]):board.paste(Image.fromarray(a).resize((345,270),Image.Resampling.NEAREST),(i*345,25));d.text((i*345+4,5),title,fill='white')
 board.save(G/'SOURCE_BASIN66.png')
if __name__=='__main__':main()
