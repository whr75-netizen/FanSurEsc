"""Fix only the diagnostic18 extent; original failed run stays immutable."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;G=H/'face36';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def main():
 r=json.loads((G/'capture/FAILED.json').read_text());assert r['ownedResourcesReleased']and r['restorationChecksPass']and r['pendingOwners']==0 and r['Edit']
 assert 'readback ROI' in r['error'] and not r['errors']
 p=G/'fix1/capture';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists()
 s=(G/'capture/RUN.cs.txt').read_text();old='foreach(int i in (cohortRead==0?new[]{5,6,7,9,11,12,16,17,18}:new[]{6,7,9,12,18}))tasks.Add(new Plane(true,i,"q"+i,q.width*(i>=13?8:1),q.height*(i>=13?8:1)));';new='foreach(int i in (cohortRead==0?new[]{5,6,7,9,11,12,16,17,18}:new[]{6,7,9,12,18})){var extent=producer.FieldExtent36(true,i);tasks.Add(new Plane(true,i,"q"+i,extent.x,extent.y));}';assert s.count(old)==1;s=s.replace(old,new)
 token='public void RequestFieldReadback36(';assert s.count(token)==1;s=s.replace(token,'public Vector2Int FieldExtent36(bool q,int index){RequireCompleted();var fields=q?QFields:Fields;if(index<0||index>=fields.Length)throw new ArgumentOutOfRangeException(nameof(index));return new Vector2Int(fields[index].rt.width,fields[index].rt.height);}\n '+token)
 s=s.replace('face36\\capture','face36\\fix1\\capture');(p/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/capture36fix1.dll')
 tests=[]
 for i in range(19):
  scale=8 if 13<=i<18 else 1;w,h=28*scale,29*scale;row=0
  while row<h:
   rows=min(h-row,max(1,16384//w));assert rows*w*16<=262144 and row+rows<=h;row+=max(1,16384//w)
  tests.append({'field':i,'scale':scale,'width':w,'height':h,'boundedStripsValid':True})
 for x,y in [(0,0),(27,28),(12,9)]:assert 0<=8*x<224 and 0<=8*y<232 and 8*x+8<=224 and 8*y+8<=232
 result={'reason':'field18 is coarse output, not fine MRT13..17; use actual owned target extent instead of inferred index scale','CPUCompile':'passed','fields':tests,'watchCases':3,'computeSourceUnchanged':True,'originalExecutionPreserved':True,'newCommandSHA':hashlib.sha256((p/'RUN.cs.txt').read_bytes()).hexdigest()};(G/'READBACK_FIX36.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items()if k!='fields'}))
if __name__=='__main__':main()
