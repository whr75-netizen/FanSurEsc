"""Prepare the minimal owned-source runtime, without executing/importing it."""
from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;G=H/'face33';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def merge(parts):
 header=(H/'face29/physical-fix/RUN_Capture25.cs.txt').read_text().split('namespace Unity.AI.')[0]
 return header+'\n'+('\n'.join(re.sub(r'^using [^\n]*\n','',s,flags=re.M)for s in parts))
def main():
 G.mkdir(exist_ok=True);assets=G/'shaders';assets.mkdir(exist_ok=True);build=G/'build';build.mkdir(exist_ok=True)
 frozen=(H/'face29/physical-fix/RUN_Capture25.cs.txt').read_text(encoding='utf-8');shared=frozen[frozen.index('public class Json58 :'):frozen.index('public static class CpuSourceCapture64')]
 shared='namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'+shared+'\n}\n'
 replacements={'Json58':'Json33','Obj58':'Obj33','Arr58':'Arr33','SerializedContent66':'SerializedContent33','CreateOnly73':'CreateOnly33','NativeSnapshot73':'NativeSnapshot33','GlobalJournal64':'GlobalJournal33','GridBinding30':'GridBinding33','GridSpace30':'GridSpace33','Submission31':'Submission33','ExitCoordinator31':'ExitCoordinator33','PendingViews31':'PendingViews33','QMetaLattice31':'QMetaLattice33','Projection31':'Projection33','ConsumerReads32':'ConsumerReads33','EditorExitRequest32':'EditorExitRequest33','ReadbackPreflight32':'ReadbackPreflight33','SourceOutline31':'SourceOutline33','SourceCaptureHost31':'SourceCaptureHost33','RequestFieldReadback32':'RequestFieldReadback33','RequestClassificationReadback32':'RequestClassificationReadback33'}
 def rename(s):return re.sub(r'\b('+'|'.join(replacements)+r')\b',lambda m:replacements[m[0]],s)
 source=(H/'face32/build/SourceOutline31.review32.cs').read_text();host=(H/'face32/build/SourceCaptureHost31.review32.cs').read_text()
 source=source.replace('Assets/EUnityValidation01/SourceBoundary31/SourceOutline31.shader','Assets/EUnityValidation01/SourceBoundary33/SourceOutline33.shader').replace('Assets/EUnityValidation01/SourceBoundary31/QMeta31.shader','Assets/EUnityValidation01/SourceBoundary33/QMeta33.shader').replace('Assets/EUnityValidation01/SourceBoundary31/LineClass31.compute','Assets/EUnityValidation01/SourceBoundary33/LineClass33.compute')
 def rep(a,b):
  nonlocal source
  assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
 rep('QFields=new RTHandle[5]','QFields=new RTHandle[10]')
 rep('renderPassEvent=RenderPassEvent.AfterRenderingTransparents;','renderPassEvent=(RenderPassEvent)555;')
 rep('int qx=Math.Max(0,left-1),qy=Math.Max(0,top-1),qr=Math.Min(480,right+1),qb=Math.Min(272,bottom+1);','int qx=Math.Max(0,left-3),qy=Math.Max(0,top-3),qr=Math.Min(480,right+3),qb=Math.Min(272,bottom+3);')
 rep('for(int i=0;i<QFields.Length;i++)QFields[i]=Target(QROI.width,QROI.height);','for(int i=0;i<5;i++)QFields[i]=Target(QROI.width,QROI.height);for(int i=0;i<5;i++){var src=LegacyInputs33()[i].rt;if(src.width!=480||src.height!=272)throw new InvalidOperationException("33 existing stage grid must be480x272");ReadbackPreflight32.RequireColourSource(src,0,0,1,1);var t=RTHandles.Alloc(QROI.width,QROI.height,colorFormat:src.graphicsFormat,filterMode:FilterMode.Point,name:"33 immutable same-frame existing stage");owned.Add(t);QFields[5+i]=t;}')
 rep('QFields.Select(t=>new RenderTargetIdentifier(t.rt))','QFields.Take(5).Select(t=>new RenderTargetIdentifier(t.rt))')
 rep('public string QStage=>','public Obj58 FrameInfo33{get;private set;}\n RTHandle[] LegacyInputs33()=>new[]{eye.full.style480[3],eye.full.shadeMask480,eye.full.motion.raw[5],eye.full.motion.raw[2],eye.full.motion.raw[6]};\n public string QStage=>')
 rep('public bool CanRelease=>','public bool ConsumerPending33=>!consumers32.CanRelease;\n public bool CanRelease=>')
 rep('d.owner=this;foreach(var t in Fields.Concat(QFields))','d.owner=this;foreach(var t in LegacyInputs33())b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in Fields.Concat(QFields))')
 rep('cmd.SetComputeTextureParam(classify,kernel,"_Outline29"','for(int i=0;i<5;i++)cmd.CopyTexture(LegacyInputs33()[i].rt,0,0,QROI.x,272-QROI.y-QROI.height,QROI.width,QROI.height,QFields[5+i].rt,0,0,0,0);\n  cmd.SetComputeTextureParam(classify,kernel,"_Outline29"')
 rep('void DrawQ(UnsafeGraphContext context){var f=eye.full;','void DrawQ(UnsafeGraphContext context){var f=eye.full;FrameInfo33=new Obj58{["sourceId"]=FrameKey,["frame"]=frame,["model"]=model,["view"]=viewKey,["headRegionEnabled"]=HeadRegion502.Enabled,["headRegionReady"]=HeadRegion502.Ready,["headRegionStatus"]=HeadRegion502.Status,["layeredSurface"]=f.layeredSurface,["styleEnabled"]=f.styleEnabled,["shadeCurvature"]=f.shadeCurvature,["shadeLayer"]=f.shadeLayer,["faceSteps"]=f.faceShadeSteps,["surfaceSteps"]=f.surfaceShadeSteps,["worldPixel"]=f.motion.camera.orthographicSize*2/272,["existingMaterialShaders"]=new Arr58(qOriginals.Select(m=>m.shader.name)),["copiedStageFormats"]=new Arr58(LegacyInputs33().Select(t=>t.rt.graphicsFormat.ToString())),["legacyInputs"]=new Arr58("existing class afterApply","proposal.R/initialQ.G/depth.B/role.A","raw role-owner-depth-alpha","raw normal","raw UV")};')
 # The command-buffer end receipt remains native16B; diagnostic strips use the
 # previously used explicit RGBAFloat expansion, without colour interpolation.
 rep('rect.height,0,1,r=>{','rect.height,0,1,TextureFormat.RGBAFloat,r=>{')
 preflight=(H/'ReadbackPreflight32.cs').read_text().replace('target.graphicsFormat!=GraphicsFormat.R32G32B32A32_SFloat','(target.graphicsFormat!=GraphicsFormat.R32G32B32A32_SFloat&&target.graphicsFormat!=GraphicsFormat.R16G16B16A16_SFloat)')
 contracts=(H/'ProducerContracts30.cs').read_text().split('public sealed class FailureBoundary30')[0]
 parts=[shared,contracts,(H/'ProducerLifetime31.cs').read_text(),(H/'ConsumerReads32.cs').read_text(),preflight,(H/'Projection31.cs').read_text(),source,host]
 body=rename(merge(parts));(build/'COMMON33.cs').write_text(body,encoding='utf-8',newline='\n')
 # Shader source only. Import is a separate explicit relay phase.
 s=(H/'face31/SourceOutline31.shader').read_text().replace('EValidation/SourceBoundary31','EValidation/SourceBoundary33');(assets/'SourceOutline33.shader').write_text(s,encoding='utf-8',newline='\n')
 s=(H/'face31/QMeta31.shader').read_text().replace('EValidation/QMeta31','EValidation/QMeta33');(assets/'QMeta33.shader').write_text(s,encoding='utf-8',newline='\n')
 (assets/'LineClass33.compute').write_bytes((H/'face31/LineClass31.compute').read_bytes())
 for phase in ['import','capture']:
  p=G/phase;p.mkdir(exist_ok=True);template=H/('Import33.cs.txt'if phase=='import'else'Capture33.cs.txt');code=body+'\n'+template.read_text(encoding='utf-8');code=re.sub(r'(?<![\w.])Object.ReferenceEquals', 'System.Object.ReferenceEquals',code)
  assert'EvaluateForm115'not in code and'BoundRun115'not in code
  out=p/'RUN.cs.txt'
  if(p/'REQUEST.json').exists():
   assert out.read_bytes()==code.encode('utf-8'),'Executed command is immutable; prepare a distinct version instead'
  else:out.write_text(code,encoding='utf-8',newline='\n')
  compile_source([out],build/(phase+'33.dll'))
 manifest={'shaders':{p.name:sha(p)for p in assets.iterdir()},'commands':{phase:sha(G/phase/'RUN.cs.txt')for phase in ['import','capture']},'CPUCompile':'passed','actualImportPlayGPU':False,'noOldEyeForwardAssembly':True,'existingQStageCopies':5,'sameFrameSourceOutputFrozen':True}
 (G/'PREPARED33.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n');print(json.dumps(manifest))
if __name__=='__main__':main()
