"""One-frame depth-state isolation; same shader, no import or automatic retry."""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face81/depth-probe'

def main():
 for d in['capture','final','post/final','console','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists();s=(H/'face81/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face81\\capture','resume-20261111\\face81\\depth-probe\\capture').replace('face81-current-curve-motion-','face81-depth-state-only-');assert s.count('motion40.FirstTarget,6,1,')==1;s=s.replace('motion40.FirstTarget,6,1,','motion40.FirstTarget,1,1,').replace('["plannedSourceFrames"]=6,','["plannedSourceFrames"]=1,')
 s=s.replace('volatile bool invalid81;','Material probeAlways81;volatile bool invalid81;');old='for(int i=0;i<10;i++)Fields[i]=Target(W77,W77);';assert s.count(old)==1;s=s.replace(old,'probeAlways81=new Material(inkStyle39){name="31 owned curve81 depth probe",hideFlags=HideFlags.HideAndDontSave};probeAlways81.SetInt("_DepthCompare81",(int)CompareFunction.Always);inkStyle39.SetInt("_DepthCompare81",(int)CompareFunction.LessEqual);'+old)
 old='o.inkStyle39,0,0,p.properties';assert s.count(old)==1;s=s.replace(old,'p.first==0?o.probeAlways81:o.inkStyle39,0,0,p.properties');old='if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);';assert s.count(old)==1;s=s.replace(old,'if(probeAlways81)UnityEngine.Object.DestroyImmediate(probeAlways81);'+old);s=s.replace('["rawAndJointSameFrame"]=true','["rawAndJointSameFrame"]=true,["depthStateIsolationOnly"]=true,["rawDepthTest"]="Always",["jointDepthTest"]="LessEqual"')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/probe81.dll')
 for phase in['final','post/final']:
  q=(H/'face81'/phase/'RUN.cs.txt').read_text().replace('resume-20261111\\face81','resume-20261111\\face81\\depth-probe');needle='CreateOnly40.Text(Path.Combine(Root,"final","STATE.json"),state.ToString());';assert q.count(needle)==1;q=q.replace(needle,'state["probe81Materials"]=Resources.FindObjectsOfTypeAll<Material>().Count(m=>m&&m.name=="31 owned curve81 depth probe");'+needle);(G/phase/'RUN.cs.txt').write_text(q,encoding='utf-8',newline='\n');compile_unity_language(G/phase/'RUN.cs.txt',G/'build'/('post.dll'if phase.startswith('post')else'pre.dll'))
 (G/'console/ARGS.json').write_text((H/'face81/console/ARGS.json').read_text());d=json.loads((H/'face81/CPU_PREPARED81.json').read_text());d.update(normalFrames=1,depthStateIsolationOnly=True,noNewShaderImport=True,notLayoutQualityComparison=True);(G/'CPU_PREPARED81.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
