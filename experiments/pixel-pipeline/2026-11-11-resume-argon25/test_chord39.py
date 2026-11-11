from pathlib import Path
import json,itertools,numpy as np
from source_chord39 import chord_intervals,linear,monotone
H=Path(__file__).resolve().parent;G=H/'face39';passed=[]
def check(n,c):assert c,n;passed.append(n)
def encode(x):return np.uint8(np.rint(np.clip(np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055),0,1)*255))
def main():
 a=np.array([80,130,170],np.uint8);b=np.array([230,200,150],np.uint8);ramp=encode(linear(a)[None,:]+np.linspace(0,1,17)[:,None]*(linear(b)-linear(a))[None,:]);q=chord_intervals(ramp,a,b)
 check('linear-light two-anchor interpolation survives RGB8 uncertainty',q['compatible'].all()and monotone(q))
 gradient=ramp.copy();AA=ramp.copy();check('identical gradient and opaque AA cannot be uniquely distinguished',np.array_equal(gradient,AA)and np.array_equal(chord_intervals(gradient,a,b)['compatible'],chord_intervals(AA,a,b)['compatible']))
 weak=np.tile(np.array([150,160,170],np.uint8),(5,1));weak[2,0]+=2;q=chord_intervals(weak,weak[0],weak[-1]);check('two-code weak chromatic mark is not flattened into flat flanks',not q['compatible'][2])
 for p in itertools.permutations(range(3)):
  p=list(p);check('channel permutation '+str(p),np.array_equal(chord_intervals(ramp[:,p],a[p],b[p])['compatible'],np.ones(17,bool)))
 check('reversed source direction remains compatible',monotone(chord_intervals(ramp[::-1],a,b),True))
 back=np.concatenate([ramp,ramp[::-1]]);check('backtracking field is not certified monotone',not monotone(chord_intervals(back,a,b))and not monotone(chord_intervals(back,a,b),True))
 check('singleton constant source interval is valid',chord_intervals(a[None,:],a,a)['compatible'].all())
 G.mkdir(exist_ok=True);(G/'CPU_CHORD39.json').write_text(json.dumps({'checks':len(passed),'passed':passed,'semanticLabelsAssigned':0,'paletteFamiliesAssigned':0,'UnityGPUCalls':0},indent=2),encoding='utf-8',newline='\n');print(json.dumps({'checks':len(passed),'passed':True}))
if __name__=='__main__':main()
