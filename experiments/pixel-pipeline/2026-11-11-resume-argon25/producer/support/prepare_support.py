"""Connect existing successful shaders to a complete candidate output domain.
No Unity/import/GPU execution. Refuse to overwrite a submitted host.
"""
from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;PRE=H.parent;R=PRE.parents[1]
sys.path.insert(0,str(PRE));from prepare_live import compile_cs,body

def replace(s,a,b,count=1):
 assert s.count(a)==count,(a[:100],s.count(a),count)
 return s.replace(a,b)

def main():
 run=H/'phase-run';run.mkdir(parents=True,exist_ok=True)
 assert not(run/'PHASE_REQUEST.json').exists()and not(run/'CAPTURE_STARTED76.json').exists(),'Submitted host is immutable'
 host=(PRE/'phase-run/RUN_Capture25.cs.txt').read_text()
 old=body(PRE/'Forward113_HeadHair25.cs');assert host.count(old)==1
 f=old
 f=replace(f,'public readonly HeadHair25 HeadHair;','public readonly HeadHair25 HeadHair;public readonly HeadHair25 PhysicalHair;public RectInt OutputROI=>canvas.ROI;')
 f=replace(f,'if(canvas.AfterCanvas!=null)','if(canvas.AfterCanvas!=null||canvas.BeforeCanvas!=null)')
 f=replace(f,'HeadHair=new HeadHair25(e);Region=new RegionDriver113(e);','HeadHair=new HeadHair25(e);PhysicalHair=new HeadHair25(e);Region=new RegionDriver113(e);Region.OutputROI=()=>OutputROI;')
 f=replace(f,'canvas.AfterCanvas=Record;','canvas.BeforeCanvas=PrepareCanvas;canvas.AfterCanvas=Record;')
 f=f.replace('HeadHair?.Dispose();','PhysicalHair?.Dispose();HeadHair?.Dispose();')
 f=replace(f,'int w=eye.roi.width,h=eye.roi.height;','int w=OutputROI.width,h=OutputROI.height;')
 split='HeadHair.Record(graph,resources,native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y),engine.Width,engine.Height);Targets();using var b='
 new='''HeadHair.Record(graph,resources,native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y),engine.Width,engine.Height);
  canvas.ROI=OutputSupport26.Union(eye.roi,HeadHair.Origin,engine.Width,engine.Height);
  PhysicalHair.Record(graph,resources,new Vector2(OutputROI.x,OutputROI.y),OutputROI.width*4,OutputROI.height*4);
 }
 void Record(RenderGraph graph,UniversalResourceData resources){var engine=Source.Engine;Targets();using var b='''
 f=replace(f,split,new)
 f=replace(f,'void Record(RenderGraph graph,UniversalResourceData resources){if(Disposed)','void PrepareCanvas(RenderGraph graph,UniversalResourceData resources){if(Disposed)')
 # All output/query/dispatch dimensions belong to the candidate domain. The
 # only remaining eye.roi use is the original rectangle passed to Union.
 for name in ['width','height','x','y']:f=f.replace('eye.roi.'+name,'OutputROI.'+name)
 f=f.replace('eye.samples[4].rgba.rt','PhysicalHair.Fields[0].rt').replace('eye.samples[4].meta.rt','PhysicalHair.Fields[1].rt')
 f=replace(f,'foreach(var t in new[]{eye.samples[4].rgba,eye.samples[4].meta})','foreach(var t in PhysicalHair.Fields)')
 f=replace(f,'canvas.AssertRendered();HeadHair.AssertRendered();','canvas.AssertRendered();HeadHair.AssertRendered();PhysicalHair.AssertRendered();')
 f=replace(f,'if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;','if(canvas.BeforeCanvas==PrepareCanvas)canvas.BeforeCanvas=null;if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;')
 f=replace(f,'["headHair25"]=','["outputROI26"]=new Arr58(OutputROI.x,OutputROI.y,OutputROI.width,OutputROI.height),["originalROI26"]=new Arr58(eye.roi.x,eye.roi.y,eye.roi.width,eye.roi.height),["physicalHair26"]=new Obj58{["frame"]=PhysicalHair.RenderedFrame,["ownedBytes"]=PhysicalHair.OwnedBytes},["headHair25"]=')
 host=replace(host,old,body(H/'OutputSupport26.cs')+'\n'+f)
 # Patch only the owned clean-canvas class, leaving all product and native
 # source camera/ROI paths intact.
 a=host.index('sealed class LayerZero101:');b=host.index('\npublic sealed class NativeRetarget96:',a)
 block=host[a:b]
 block=replace(block,'public Action<RenderGraph,UniversalResourceData> AfterCanvas;','public Action<RenderGraph,UniversalResourceData> BeforeCanvas,AfterCanvas;public RectInt ROI{get;set;}')
 block=replace(block,'Targets();foreach(var m in mats)Bind(m);var r=frame.Get<UniversalResourceData>();','ROI=eye.roi;var r=frame.Get<UniversalResourceData>();BeforeCanvas?.Invoke(graph,r);Targets();foreach(var m in mats)Bind(m);')
 block=block.replace('eye.roi.','ROI.')
 block=replace(block,'GL.GetGPUProjectionMatrix(eye.cropProjection,true)','GL.GetGPUProjectionMatrix(OutputSupport26.Crop(ROI,f.effectiveProjection),true)')
 block=replace(block,'AfterCanvas=null;Release();','BeforeCanvas=null;AfterCanvas=null;Release();')
 host=host[:a]+block+host[b:]
 # Existing per-view driver receives the same complete output domain.
 a=host.index('public sealed class RegionDriver113:');b=host.index('\npublic sealed class HeadHair25',a)
 block=host[a:b];block=replace(block,'readonly EyeFeature348 eye;','readonly EyeFeature348 eye;public Func<RectInt> OutputROI;RectInt R=>OutputROI==null?eye.roi:OutputROI();')
 block=block.replace('eye.roi.','R.')
 host=host[:a]+block+host[b:]
 # Observer records candidate extent explicitly; S4 remains the original
 # independently sized product control, and is never relabelled.
 host=replace(host,'var hf=Frame(h,"product77-control-and-isolated-live113",serial);var r=e.roi;','var hf=Frame(h,"product77-control-and-isolated-live113",serial);var r=forward102.OutputROI;')
 host=replace(host,'int physical24=e.roi.width*e.roi.height*16;','int physical24=forward102.OutputROI.width*forward102.OutputROI.height*16;')
 oldTile='e.roi.x+Mathf.RoundToInt(n.host.offset.x),272-e.roi.y-e.roi.height+Mathf.RoundToInt(n.host.offset.y),e.roi.width,e.roi.height'
 newTile='forward102.OutputROI.x+Mathf.RoundToInt(n.host.offset.x),272-forward102.OutputROI.y-forward102.OutputROI.height+Mathf.RoundToInt(n.host.offset.y),forward102.OutputROI.width,forward102.OutputROI.height'
 host=replace(host,oldTile,newTile)
 host=host.replace(str(PRE/'phase-run'),str(run))
 # Same two consecutive phase inputs first; no automatic additional trials.
 extra='''for(int ph26=0;ph26<2;ph26++){var t26=forward102.PhysicalHair.Fields[ph26];Plane(hf,"PH26-"+new[]{"rgba","meta"}[ph26],t26,new RectInt(0,0,t26.rt.width,t26.rt.height),"same-frame original S4 on expanded physical candidate ROI","original product S4 control untouched");}
'''
 host=replace(host,'   for(int ch25=0;ch25<5;ch25++)',extra+'   for(int ch25=0;ch25<5;ch25++)')
 for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in host,bad
 assert not re.search(r'InputSystem\.settings\s*=(?!=)',host)
 source=run/'RUN_Capture25.cs.txt';source.write_text(host,encoding='utf-8',newline='\n');compile_cs(source)
 (run/'GLOBAL_NAMES66.json').write_bytes((PRE/'phase-run/GLOBAL_NAMES66.json').read_bytes())
 (H/'Forward113_Support26.cs.txt').write_text(f,encoding='utf-8',newline='\n')
 result={'captureSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'source':str(source),
   'compiled':True,'newShaderAssets':0,'changedComputeBytecode':False,'GPUOrUnityExecuted':False,
   'maximumOutputCells':512,'destinationSamplesMaximum':8192,'extraPhysicalHairMeshDraws':4,
   'originalEyeROIMutated':False,'actualFramesBound':2,'noAutomaticNextTrial':True}
 (H/'PREPARED26.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
