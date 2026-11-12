from pathlib import Path
import sys,re,argparse
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('name');parser.add_argument('--frames',type=int,default=64);parser.add_argument('--pose-every',type=int,default=24);args=parser.parse_args();name=args.name;count=args.frames;poseEvery=args.pose_every
 assert re.fullmatch(r'[A-Za-z0-9_-]+',name)and 1<=count<=1800 and 1<=poseEvery<=count
 root=H/'face99'/name
 for d in ['capture','preflight/final','post/final','console']:(root/d).mkdir(parents=True,exist_ok=True)
 assert not(root/'capture/REQUEST.json').exists()
 s=(H/'face99/optimized12/capture/RUN.cs.txt').read_text();oldroot=str(H/'face99/optimized12');newroot=str(root);assert oldroot in s;s=s.replace(oldroot,newroot).replace('face99-optimized-','face99-fine-'+name+'-').replace('motion40.FirstTarget,12,1,motion40.Snapshot','motion40.FirstTarget,'+str(count)+','+str(poseEvery)+',motion40.Snapshot').replace('["plannedSourceFrames"]=12','["plannedSourceFrames"]='+str(count))
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 oldGeometry=(H/'JointLine99.cs').read_text();newGeometry=(H/'JointLine99C.cs').read_text();once(oldGeometry[oldGeometry.index('namespace LineGeometry97'):],newGeometry[newGeometry.index('namespace LineGeometry97'):])
 once('["indexEntries"]=scene.entries,','["indexEntries"]=scene.entries,["fineEntries99"]=scene.fineEntries99,')
 if count>64:once('EditorApplication.timeSinceStartup-started>120)throw new TimeoutException("95 bounded source observation120s CPU-IO limit; no retry or time-based resource release")','EditorApplication.timeSinceStartup-started>900)throw new TimeoutException("99 planned long observation900s total CPU-IO budget; no retry or time-based resource release")')
 once('public long Bytes=>bytes;public Obj40 profile99;','public long Bytes=>bytes;public Obj40 profile99;readonly SourceWidthCache99 widthCache99=new SourceWidthCache99();bool worldWritten99;public bool ClaimWorldInventory99(){if(worldWritten99)return false;worldWritten99=true;return true;}public SourceWidthCache99.Entry Width99(Texture2D t)=>widthCache99.Require(t);public int WidthEntries99=>widthCache99.Entries;public int WidthHits99=>widthCache99.hits;public int WidthMisses99=>widthCache99.misses;')
 once('if(disposed)return;disposed=true;foreach(var image in images)','if(disposed)return;disposed=true;widthCache99.Dispose();foreach(var image in images)')
 once('SourceOpacity97Cache sourceOpacity97;Material jointMaterial97;','SourceWidthCache99.Entry frameWidth99;SourceOpacity97Cache sourceOpacity97;Material jointMaterial97;')
 once('double requireClock99=EditorApplication.timeSinceStartup;sourceOpacity97.Require','InventoryWorld99();double requireClock99=EditorApplication.timeSinceStartup;sourceOpacity97.Require')
 once('double requireMs99=1000*','if(widthMap40)frameWidth99=sourceOpacity97.Width99((Texture2D)sourceWidth40);double requireMs99=1000*')
 start=s.index(' float WidthGreen97(');end=s.index(' sealed class Pass97',start);s=s[:start]+' float WidthGreen97(float u,float v){if(frameWidth99==null)throw new InvalidOperationException("99 original width cache not required this frame");return frameWidth99.Sample(u,v);}'+'\n'+s[end:]
 once('jointData97=null;sourceOpacity97=null;','jointData97=null;frameWidth99=null;sourceOpacity97=null;')
 once('["requireMsExcludedFrom97"]=requireMs99,','["requireMsExcludedFrom97"]=requireMs99,["widthEntries99"]=sourceOpacity97.WidthEntries99,["widthHits99"]=sourceOpacity97.WidthHits99,["widthMisses99"]=sourceOpacity97.WidthMisses99,')
 once('["sourceAlpha97ManagedBytesAfterRelease"]=opacity97.Bytes,','["sourceAlpha97ManagedBytesAfterRelease"]=opacity97.Bytes,["sourceWidth99EntriesAfterRelease"]=opacity97.WidthEntries99,')
 s+='\n'+(H/'SourceWidthCache99.cs.txt').read_text()+'\n'+(H/'WorldInventory99.cs.txt').read_text()
 assert oldroot not in s and s.count(newroot)==1 and'EvaluateForm115'not in s and'BoundRun115'not in s and s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1
 p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,H/'face99/build'/(name+'.dll'))
 for d in ['preflight/final','post/final']:
  s=(H/'face99/optimized12'/d/'RUN.cs.txt').read_text().replace(oldroot,newroot);assert oldroot not in s and newroot in s;p=root/d/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,H/'face99/build'/(name+'-'+d.replace('/','-')+'.dll'))
 (root/'console/ARGS.json').write_bytes((H/'face99/optimized12/console/ARGS.json').read_bytes());print('CPU cache candidate compiled; no new shader/import/device/dispatch executed')
if __name__=='__main__':main()
