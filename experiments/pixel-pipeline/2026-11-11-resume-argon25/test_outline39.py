from pathlib import Path
import json,numpy as np
H=Path(__file__).resolve().parent;G=H/'face39';passed=[]
def resolve(on,off,old,ink):
 on=np.asarray(on,float);off=np.asarray(off,float)
 assert on.shape==off.shape==(8,8)
 invalid=not(np.isfinite(on).all()and np.isfinite(off).all())or(on<0).any()or(on>1).any()or(off<0).any()or(off>1).any()or(on>off).any()
 a,b=on.sum()/64,off.sum()/64
 if invalid:return np.array(old),np.array([a,b,0,-1])
 selected=a>.5;status=2 if a==.5 else 3 if b>.5 and a<=.5 else 1
 return np.array([*ink,1])if selected else np.array(old),np.array([a,b,int(selected),status])
def check(name,condition):assert condition,name;passed.append(name)
def main():
 old=[.72,.51,.42,1];ink=[.0612460561,.008568122,.014443838];full=np.ones((8,8));empty=np.zeros((8,8));thin=empty.copy();thin[0,:]=1
 check('empty ribbon preserves exact existing RGB',np.array_equal(resolve(empty,empty,old,ink)[0],old))
 check('full visibility is exact source ink without LineTone',np.array_equal(resolve(full,full,old,ink)[0],[*ink,1]))
 check('thin native sample alone is not claimed a full visible pixel',resolve(thin,thin,old,ink)[1][2]==0)
 check('real hair occlusion overrides an otherwise visible ribbon',np.array_equal(resolve(empty,full,old,ink)[0],old)and resolve(empty,full,old,ink)[1][3]==3)
 half=empty.copy();half[:4]=1;check('exact half is unresolved not arbitrary ink',resolve(half,full,old,ink)[1][3]==2 and np.array_equal(resolve(half,full,old,ink)[0],old))
 mask=empty.copy();mask[:5,1:7]=1;mask[5,1:4]=1
 for k in range(4):
  for flip in [False,True]:
   f=lambda a:np.rot90(np.fliplr(a)if flip else a,k)
   check('D4 visibility '+str((k,flip)),np.array_equal(resolve(f(mask),full,old,ink)[0],resolve(mask,full,old,ink)[0]))
 check('on/off visibility contradiction blocks overlay',resolve(full,empty,old,ink)[1][3]==-1)
 bad=full.copy();bad[0,0]=float('nan');check('nonfinite visibility blocks overlay',resolve(bad,full,old,ink)[1][3]==-1)
 for colour in [[1,0,0],[0,1,0],[.19,.42,.81]]:check('source palette independent '+str(colour),np.array_equal(resolve(full,full,old,colour)[0],[*colour,1]))
 G.mkdir(exist_ok=True);(G/'CPU_OUTLINE39.json').write_text(json.dumps({'checks':len(passed),'passed':passed,'GPUUnityCalls':0,'importantPigmentAllocator':False,'geometryMinimumWidthIsExperimental':True},indent=2),encoding='utf-8',newline='\n');print(json.dumps({'checks':len(passed),'passed':True}))
if __name__=='__main__':main()
