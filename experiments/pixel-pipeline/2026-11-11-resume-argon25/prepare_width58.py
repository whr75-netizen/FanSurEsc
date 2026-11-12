"""Capture already-produced native outline support and evaluated normals; no new shader."""
from pathlib import Path
import json,hashlib,difflib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face58'
def main():
 p=G/'capture';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists()
 old=(H/'face57/capture/RUN.cs.txt').read_text();s=old.replace('resume-20261111\\face57\\capture','resume-20261111\\face58\\capture').replace('face57-source-domain-','face58-authored-width-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 needle='report["frameInfo"]=producer.FrameInfo40;'
 more='''foreach(int field58 in new[]{0,1,4,5}){var ex58=producer.FieldExtent40(false,field58);tasks.Add(new Plane(false,field58,new[]{"nativeOutlineOn58","nativeOutlineMetaOn58","nativeOutlineOff58","nativeOutlineMetaOff58"}[field58<2?field58:field58-2],ex58.x,ex58.y));}foreach(int q58 in new[]{3,4}){var ex58=producer.FieldExtent40(true,q58);tasks.Add(new Plane(true,q58,q58==3?"initialAppliedQ58":"initialSurfaceMeta58",ex58.x,ex58.y));}'''
 rep(needle,more+needle)
 # Preserve the original geometry format and add a small explicit sidecar.
 line=next(x for x in s.splitlines()if 'geometry-frame' in x and 'BinaryWriter'in x)
 sidecar='''
   if(!String.IsNullOrEmpty(EvidenceRoot40)){
    if(normals.Length!=vertices.Length||sourceUV40.Length!=vertices.Length||(long)vertices.Length*32>262144)throw new InvalidOperationException("58 bounded evaluated width carrier ABI");
    using(var bw58=new BinaryWriter(new FileStream(Path.Combine(EvidenceRoot40,"width-carrier-frame"+frame+".bin"),FileMode.CreateNew))){bw58.Write("source-width58/v1");bw58.Write(FrameKey);bw58.Write(frame);bw58.Write(vertices.Length);for(int c58=0;c58<16;c58++)bw58.Write(transform[c58]);for(int n58=0;n58<vertices.Length;n58++){var n=normals[n58];var wn=normalMatrix.MultiplyVector(n).normalized;var uv58=sourceUV40[n58];foreach(float v58 in new[]{n.x,n.y,n.z,wn.x,wn.y,wn.z,uv58.x,uv58.y}){if(!float.IsFinite(v58))throw new InvalidOperationException("58 nonfinite evaluated width carrier");bw58.Write(v58);}}}
   }
'''
 rep(line,line+sidecar)
 # Frozen source settings must still describe the live source; never silently
 # apply the historical colour/width to a user-edited material.
 needle='widthMap40=widthMaterial40.IsKeywordEnabled('
 guard='''if(widthMaterial40.GetFloat("_OutlineWidth")!=width||widthMaterial40.GetFloat("_OutlineLightingMix")!=0||widthMaterial40.GetColor("_OutlineColor").r!=sourceInk.x||widthMaterial40.GetColor("_OutlineColor").g!=sourceInk.y||widthMaterial40.GetColor("_OutlineColor").b!=sourceInk.z)throw new InvalidOperationException("58 live source outline settings differ from provenance; no historical override accepted");'''
 rep(needle,guard+needle)
 rep('["variableThicknessQuantized"]=false','["variableThicknessQuantized"]=false,["width58Capture"]="actual native MToon inverted-hull ON/OFF at8x; normal/UV sidecar; no new width policy or extra draw",["liveOutlineWidthAndColourMatchFrozen"]=true')
 assert 'EvaluateForm115'not in s and'BoundRun115'not in s
 (p/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');b=G/'build';b.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',b/'width58.dll')
 result={'fullExternalCSharp9Compiled':True,'plannedSourceFrames':1,'newShaders':0,'newDraws':0,'newDispatches':0,'addedReadbackPlanes':6,'readbackMaxBytesPerRequest':262144,'widthCarrierPayloadMaxBytes':262144,'sameFrameSourceIdRequired':True,'productDefaultChanged':False,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()}
 (G/'CPU_PREPARED58.json').write_text(json.dumps(result,indent=2),encoding='utf-8');diff=difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='capture57',tofile='capture58');(G/'from57.patch').write_text(''.join(x if x.endswith('\n')else x+'\n\\ No newline at end of file\n'for x in diff),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
