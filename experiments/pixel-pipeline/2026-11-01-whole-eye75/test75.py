from pathlib import Path
import json
from joint75 import hall,state_contract,layered_identity
R=Path(__file__).resolve().parent
def main():
 cases=[]
 def test(n,b):assert b,n;cases.append(n)
 test('joint overlap exposes Hall conflict despite separate family capacities',not hall({'iris':{(0,0),(1,0)},'lid':{(0,0)}},{'iris':2,'lid':1})['capacityFeasible'])
 test('one shared-cell opposite parts cannot both own opaque cell',not hall({'iris':{(0,0)},'lid':{(0,0)}},{'iris':1,'lid':1})['capacityFeasible'])
 test('separate support permits relaxed joint ownership',hall({'iris':{(0,0)},'lid':{(0,-1)}},{'iris':1,'lid':1})['capacityFeasible'])
 test('no forced size or lower bound for absent declared part',hall({'iris':set(),'lid':set()},{'iris':0,'lid':0})['capacityFeasible'])
 a=hall({'iris':{(0,0),(1,0)},'lid':{(0,0)}},{'iris':2,'lid':1});b=hall({'lid':{(0,0)},'iris':{(1,0),(0,0)}},{'lid':1,'iris':2})
 test('family/destination iteration order does not change witness',a==b)
 test('missing lid definition is reported instead of fabricated',state_contract({'iris':{'intrinsicDefinition':'source'},'white':{'intrinsicDefinition':'source'}},['iris','white','lid'])['missing']==['lid'])
 test('closed state never borrows open keyform',not state_contract({},['iris','white','lid'])['openFallbackAllowed'])
 cells=[{'cellId':'a','eye':1,'role':1,'rgba8':[10,20,30,255]},{'cellId':'b','eye':1,'role':6,'rgba8':[1,2,3,255]}];layers=layered_identity(cells,{'b'})
 test('occlusion hides a source token without deleting cache identity',len(layers)==2 and not layers[0]['visible']and layers[1]['visible'])
 test('cache colour family and source colour retained while hidden',layers[0]['role']==1 and layers[0]['rgba8']==[10,20,30,255])
 test('a capacity pass does not certify relative geometry',hall({'iris':{(1,0)},'lid':{(0,1)}},{'iris':1,'lid':1})['capacityFeasible'])
 with (R/'TEST75.json').open('x')as f:json.dump({'passed':len(cases),'cases':cases,'UnityCalls':0,'productChanges':0,'limits':'constraint logic only, not whole-eye aesthetic/occlusion raster proof'},f,indent=2)
 print('passed',len(cases))
if __name__=='__main__':main()
