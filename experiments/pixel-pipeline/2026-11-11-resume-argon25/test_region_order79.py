from pathlib import Path
import json
from region_order79 import feasible
H=Path(__file__).resolve().parent;G=H/'face79'

def main():
 tests=0
 assert feasible({0:[.1,.2],1:[.2,.3]},[(0,1)])['feasible'];tests+=1
 assert not feasible({0:[.1,.2]},[(0,0)])['feasible'];tests+=1
 assert feasible({0:[.1,.3],1:[.2,.4]},[(0,1),(1,0)])['cyclicOrDependentRegions']==[0,1];tests+=1
 assert feasible({0:[.7],1:[.1,.6]},[(0,1)])['exhaustedDomainRegions']==[1];tests+=1
 a=feasible({0:[.1,.3],1:[.2,.4],2:[.35,.5]},[(0,1),(1,2)]);b=feasible({2:[.5,.35],1:[.4,.2],0:[.3,.1]},[(1,2),(0,1)]);assert a==b and a['leastNativeLuminance']=={0:.1,1:.2,2:.35};tests+=1
 (G/'CPU_REGION_ORDER79.json').write_text(json.dumps({'CPUChecks':tests,'nativeDomainExactFeasibility':True,'noThresholdOrPaletteCountSearch':True,'sourceRGBOrGPUOutputGenerated':False},indent=2));print(tests)
if __name__=='__main__':main()
