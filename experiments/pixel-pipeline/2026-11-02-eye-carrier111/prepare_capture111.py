"""Prepare NEW external C# bundles. No Assets import, Play, or package changes."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;R=H.parent;D=H/'capture';P=R/'joint-lid107'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
def create(p,s):
    with p.open('x',encoding='utf8',newline='\n')as f:f.write(s)
def replace(s,a,b,count=1):
    assert s.count(a)==count,(a[:100],s.count(a),count)
    return s.replace(a,b)
def main():
    s=(P/'NativeDense107.cs').read_text(encoding='utf8').replace('NativeDense107','NativeCarrier111')
    s=replace(s,'mat.SetInt("_UseBank89",control==0?1:0);','mat.SetInt("_UseBank89",0);')
    create(H/'NativeCarrier111.cs',s)
    s=(P/'WholeEye107.cs').read_text(encoding='utf8')
    export='''
 public void ExportSource111(string file,string sourceId,int frame,int serial){Check();using(var w=new BinaryWriter(new FileStream(file,FileMode.CreateNew,FileAccess.Write,FileShare.Read))){
  w.Write("feature-source-geometry111/v1");w.Write(sourceId);w.Write(frame);w.Write(serial);w.Write(Scope);w.Write(VertexCount);foreach(var vs in new[]{cpuWorld107,cpuRest107})foreach(var v in vs){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}foreach(var v in cpuUV107){w.Write(v.x);w.Write(v.y);}w.Write(TriangleCount);foreach(var t in cpuTriangles107){foreach(var v in new[]{t.v.x,t.v.y,t.v.z,t.v.w,t.source.x,t.source.y,t.source.z,t.source.w})w.Write(v);w.Write(t.eye.x);w.Write(t.eye.y);w.Write(t.eye.z);w.Write(t.eye.w);}w.Write(MaterialCount);foreach(var m in cpuMaterials107)foreach(var v in new[]{m.atlas,m.alphaCullWrap,m.uvWrap}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}w.Write(PrimitiveStride);w.Write(cpuParts107.Length);foreach(var v in cpuParts107)w.Write(v);
 }}
'''
    s=replace(s,' void Check(){if(disposed)',export+'\n void Check(){if(disposed)')
    create(H/'WholeEye111.cs',s)
    s=(P/'ForwardCanvas107.cs').read_text(encoding='utf8').replace('ForwardCanvas107','ForwardCanvas111')
    s=replace(s,'public readonly LiveSurface107 Source;','public readonly NativeCarrier111 CarrierNative;public readonly LiveSurface107 CarrierSource; public readonly LiveSurface107 Source;')
    needle='canvas.AfterCanvas=Record;'
    s=replace(s,needle,'CarrierNative=new NativeCarrier111(e,regPath,diag+"-carrier111");CarrierSource=new LiveSurface107(e,AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye107.compute"),ids,px,py);'+needle)
    s=s.replace('catch{DenseSource?.Dispose();','catch{CarrierSource?.Dispose();CarrierNative?.Dispose();DenseSource?.Dispose();')
    s=replace(s,'DenseNative.RecordGraph(graph,resources);','DenseNative.RecordGraph(graph,resources);CarrierNative.RecordGraph(graph,resources);CarrierSource.Update();CarrierSource.Engine.Resize(CarrierNative.currentWidth,CarrierNative.currentHeight,CarrierSource.Scope);')
    s=replace(s,'foreach(var buffer in DenseSource.Engine.Buffers)', 'foreach(var buffer in CarrierSource.Engine.Buffers)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);foreach(var a in CarrierNative.Handles96)foreach(var t in a)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var buffer in DenseSource.Engine.Buffers)')
    s=replace(s,'var e=Source.Engine;for(int p=0;p<4;p++)e.Pack','for(int p=0;p<4;p++)CarrierSource.Engine.Pack(cmd,p,CarrierNative.layers[p],true);CarrierSource.Engine.Dispatch(cmd,data.view,data.projection,false,0);var e=Source.Engine;for(int p=0;p<4;p++)e.Pack')
    s=replace(s,'canvas.AssertRendered();native.AssertRendered();','canvas.AssertRendered();native.AssertRendered();DenseNative.AssertRendered();CarrierNative.AssertRendered();')
    s=s.replace('canvas.AfterCanvas=null;DenseSource?.Dispose();','canvas.AfterCanvas=null;CarrierSource?.Dispose();CarrierNative?.Dispose();DenseSource?.Dispose();')
    create(H/'ForwardCanvas111.cs',s)
    s=(P/'capture-final/CaptureFinal107.cs').read_text(encoding='utf8').replace(str(P/'capture-final'),str(D)).replace('ForwardCanvas107','ForwardCanvas111').replace('Sequence107','Sequence111').replace('eye107-','eye111-').replace('STATE107-','STATE111-').replace('TRACE107-','TRACE111-')
    s=replace(s,'forward102.AssertRendered();int serial=', 'forward102.AssertRendered();int serial=') # checked context, unchanged
    s=replace(s,'if(!(bool)report["frameUnchangedDuringReadback"])', 'CaptureCarrier111(hf,e);if(!(bool)report["frameUnchangedDuringReadback"])')
    cleanup='report["ownedProbeReleased76"]=true;'
    s=replace(s,cleanup,cleanup+'report["carrierSourceDisposed111"]=forward102==null||forward102.CarrierSource.Engine.Disposed;report["carrierNativeDisposed111"]=forward102==null||forward102.CarrierNative.Disposed;forward102=null;layer102=null;motion82=null;')
    # Snapshot of the stimulus restoration must precede clearing its reference.
    s=s.replace('if(motion82!=null&&!motion82.Restored)', 'if(report["motionRestoration82"]!=null&&!(bool)report["motionRestoration82"]["allRestored"])')
    s=replace(s,'report["observerRemoved"]=true;', 'report["observerRemoved"]=true;')
    extra='''
 void CaptureCarrier111(CpuSourceCapture64.Frame f,EyeFeature348 e){
  int w=forward102.CarrierNative.currentWidth,h=forward102.CarrierNative.currentHeight;
  if(w!=forward102.DenseNative.currentWidth||h!=forward102.DenseNative.currentHeight||forward102.CarrierNative.Anchor96!=forward102.DenseNative.Anchor96||forward102.CarrierNative.Bounds96!=forward102.DenseNative.Bounds96)throw new InvalidOperationException("111 carrier/source grid mismatch");
  foreach(int part in new[]{1,2})foreach(var c in new[]{new{n="rgba",i=0},new{n="rest",i=2},new{n="uv",i=3}}){var t=forward102.DenseNative.Handles96[part][c.i];Plane(f,"D-part"+part+"-"+c.n,t,new RectInt(0,0,w,h),"111 actual same-frame8x authored bank source","source rest/UV/colour, not interpolated from4x");}
  foreach(int part in new[]{1,2,3})foreach(var c in new[]{new{n="rgba",i=0},new{n="meta",i=1},new{n="rest",i=2},new{n="uv",i=3}}){var t=forward102.CarrierNative.Handles96[part][c.i];Plane(f,"C-part"+part+"-"+c.n,t,new RectInt(0,0,w,h),"111 same-frame native carrier with BANK gate disabled on OWNED materials","actual source material alpha, current geometry/depth/UV; not a colour supplier");}
  JointSlice107("carrier-three-part-visibility",forward102.CarrierSource.Engine.Visibility,w*h,w*h*3);JointSlice107("carrier-three-part-query-proof",forward102.CarrierSource.Engine.Evidence107,w*h*2,w*h*6);
  forward102.DenseSource.Engine.ExportSource111(Path.Combine(output,"SOURCE_GEOMETRY111.bin"),sourceId,Time.frameCount,native.host.main.renderedSerial335);
  var inv=new Arr58();for(int i=0;i<e.full.eyeInverse.Length;i++){var m=e.full.eyeInverse[i];m.m33=1;if(Mathf.Abs(m.determinant)<1e-12f)throw new InvalidOperationException("111 current homography singular");inv.Add(M(m.inverse));}
  CreateOnly73.Text(Path.Combine(output,"SOURCE_TRANSFORMS111.json"),new Obj58{["sourceId"]=sourceId,["frame"]=Time.frameCount,["serial"]=native.host.main.renderedSerial335,["headMatrix"]=M(e.headMatrix),["authoredToHead"]=inv,["eyeCentres"]=new Arr58(e.centres.Select(v=>V(v))),["currentPhysicalView"]=M(e.full.motion.camera.worldToCameraMatrix),["currentPhysicalProjection"]=M(e.full.motion.camera.projectionMatrix),["carrier"]=forward102.CarrierNative.Info,["bankUVSource"]=@"C:\\Users\\15352\\Documents\\Codex\\2026-10-27\\task-2\\render-fix21\\native-feature89\\REGISTRATION89.json"}.ToString());
  report["extraContract111"]=new Obj58{["sourceId"]=sourceId,["exactCurrentCPUWorldAndSourceRestUV"]=true,["direct8xBankRestRGBAUV"]=true,["nativeCarrierBankGateDisabledOnlyOnOwnedMaterials"]=true,["carrierGeometryQueryOnGPU"]=true,["footprintResolvesFinalRGB"]=false,["runtime2_2AllocatorImplemented"]=false,["borrowedBufferDisposed"]=false,["newAssetsImported"]=0};
 }
'''
    pos=s.rfind('\n}');s=s[:pos]+extra+s[pos:];create(D/'Capture111.cs',s)
    compileSource=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result){result.Log("111 complete external observer compiled; no Play");}\n void Prepared111(ExecutionResult result)\n {',1);assert compileSource!=s;create(D/'Compile111.cs',compileSource)
    base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',P/'NativeDense107.cs',H/'NativeCarrier111.cs',P/'LiveSurface107.cs',H/'WholeEye111.cs',P/'HairDrawScope107.cs',R/'live-curve106/SourceCurves106.cs',H/'ForwardCanvas111.cs',R/'live-curve106/MotionClose106.cs',P/'HoldMorph107.cs',H/'Sequence111.cs']
    for mode in ['Compile','Capture']:
        target=D/('RUN_'+mode+'111.cs.txt');assert not target.exists();bundle(deps+[D/(mode+'111.cs')],target)
    create(D/'GLOBAL_NAMES66.json',(P/'capture-final/GLOBAL_NAMES66.json').read_text())
    (H/'CAPTURE_CONTRACT111.json').write_text(json.dumps({'purpose':'Resolve Close75 source-key versus destination carrier/visibility, not add guessed white pixels','PlayPlanned':1,'expectedCapturedStates':12,'expectedSourceMorphChecks':'existing owned BakeMesh comparison <=2e-6','AssetsImport':0,'product77Changes':0,'InputSettingsReplacement':False,'sourceIdPolicy':'new unique sourceId per frame','sourceAdded':['actual dense8x iris/white rest, UV, bank RGBA','evaluated current world/rest/UV/indices/material table from OWNED CPU arrays','exact current head/canonical/physical transforms','bank-independent native carrier fields and existing GPU face visibility/evidence'],'readbackMaxSingleBytes':2*1024*1024,'runtimeAllocatorProductApplied':False},indent=2)+'\n')
    print('Prepared compile/capture111 external bundles; no execution in this script')
if __name__=='__main__':main()
