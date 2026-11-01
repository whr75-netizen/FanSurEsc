from pathlib import Path
import re,sys,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'run';OUT=HERE/'run87';OUT.mkdir(exist_ok=True);assert not list(OUT.glob('*_REQUEST.json'))
assert all(r['equal']is True for r in json.loads((HERE/'import87/IMPORTED87.json').read_text())['nativeComparisons'])
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
m=(OLD/'MotionScope86.cs').read_text().replace('MotionScope86','MotionScope87').replace('TotalFrames=24','TotalFrames=29')
m=m.replace('index<PhaseFrames+WalkFrames?"walk":"sweep"','index<PhaseFrames+WalkFrames?"walk":index<24?"sweep":"blink"')
m=m.replace('index-PhaseFrames:index-PhaseFrames-WalkFrames','index-PhaseFrames:index<24?index-PhaseFrames-WalkFrames:index-24')
m=m.replace('Stage=="sweep"?input.sqrMagnitude>1e-8f','(Stage=="sweep"||Stage=="blink")?input.sqrMagnitude>1e-8f')
m=m.replace(' void BeginSweep86(){',(HERE/'Blink87.cs.part').read_text()+'\n void BeginSweep86(){')
m=m.replace('else if(index>PhaseFrames+WalkFrames){SetSweep86(index-PhaseFrames-WalkFrames);}','else if(index>PhaseFrames+WalkFrames&&index<24){SetSweep86(index-PhaseFrames-WalkFrames);}else if(index==24){BeginBlink87();}else if(index>24){requestedBlink87=new float[]{0,50,100,100,0}[index-24];}')
m=m.replace('Try(()=>RestoreSweep86());','Try(()=>RestoreBlink87());Try(()=>RestoreSweep86());');(OUT/'MotionScope87.cs').write_bytes(m.encode())
s=(OLD/'Capture86.cs').read_text();s=re.sub(r'const string Root=@"[^"]+";',lambda _:'const string Root=@"'+str(OUT)+'";',s,count=1).replace('MotionScope86','MotionScope87').replace('STATE86-','STATE87-').replace('TRACE86-','TRACE87-').replace('eye86-','eye87-')
s=s.replace(' MotionScope87 motion82;',' ComposeComparison87 comparison87;\n MotionScope87 motion82;')
s=s.replace('motion82=new MotionScope87(n,output);','comparison87=new ComposeComparison87(n.host.head);report["original333Calibration87"]=comparison87.Calibrate(probeROI);Save("old333-replay-calibration");if(!(bool)report["original333Calibration87"]["pass"])throw new InvalidOperationException("Original333 replay does not match live input; no candidate install");comparison87.Install();motion82=new MotionScope87(n,output);')
s=s.replace('motion82?.Dispose();report["motionRestoration82"]','comparison87?.Dispose();report["composeRestoration87"]=comparison87?.RestoreReport;motion82?.Dispose();report["motionRestoration82"]')
s=s.replace('InputVerify81();','InputVerify81();') # retain tested restore function name
s=s.replace('InputVerify82();report["observerRemoved"]','InputVerify82();if(comparison87!=null&&!comparison87.Restored)throw new InvalidOperationException("Compose candidate ownership restoration failed");report["observerRemoved"]')
# Remove per-plane full-JSON breadcrumb duplication; per-frame manifests and
# failure/exit states still contain every completed plane, with commit markers.
s=s.replace('Save("capturing-"+name);','')
s=s.replace('report["packetComplete"]=true;CreateOnly73.Text', 'report["packetComplete"]=true;report["planes"]=planes;CreateOnly73.Text')
needle='  report["frameIndex"]=frameIndex;report["mainSerial"]=serial;'
extra='''  if(!comparison87.InstalledAndActive)throw new InvalidOperationException("Cached source role candidate not active");comparison87.ReplayOriginal();for(int i=0;i<4;i++)Plane(frame,"original333-"+i,comparison87.outputs[i],probeROI,"same-frame original333 offscreen replay","colour/owner/intrinsic/audit; no borrowed output writes");
  var sky=UnityEngine.Object.FindObjectsByType<FantasySurvival.WorldLighting.SkyLightingCycleController>(FindObjectsSortMode.None).FirstOrDefault(x=>x.isActiveAndEnabled);if(sky){var sun=sky.SceneDirectionalLight;report["sky87"]=new Obj58{["hour"]=sky.CurrentHour,["auto"]=sky.IsAdvancingAutomatically,["phase"]=sky.CurrentPhase.ToString(),["cloudOpacity"]=sky.CurrentCloudShadowOpacity,["cloudSoftness"]=sky.CurrentCloudShadowSoftnessMip,["sunId"]=sun?(Json58)sun.GetEntityId().ToString():null,["sunForward"]=sun?V(sun.transform.forward):null,["sunColor"]=sun?V(new Vector4(sun.color.r,sun.color.g,sun.color.b,sun.intensity)):null,["shadowStrength"]=sun?(Json58)sun.shadowStrength:null};}
  int scale87=n.nativePixelsPerCell;var origin87=n.origin;var shift87=n.host.offset;var delta87=n.deliveredDelta;int nx87=Math.Max(0,(int)Math.Floor(origin87.x+(probeROI.x+shift87.x+delta87.x)*scale87)-2),ny87=Math.Max(0,(int)Math.Floor(origin87.y+(probeROI.y+shift87.y+delta87.y)*scale87)-2);int ex87=Math.Min(n.output.rt.width,(int)Math.Ceiling(origin87.x+(probeROI.xMax+shift87.x+delta87.x)*scale87)+2),ey87=Math.Min(n.output.rt.height,(int)Math.Ceiling(origin87.y+(probeROI.yMax+shift87.y+delta87.y)*scale87)+2);var nativeROI87=new RectInt(nx87,ny87,ex87-nx87,ey87-ny87);var nativeFrame87=Frame(main,"native-final",serial);foreach(var t in new[]{new{n="native-final-rgba",t=n.output},new{n="native-final-cell",t=n.cellID},new{n="native-final-owner",t=n.owner},new{n="native-final-depth",t=n.depthAudit}})Plane(nativeFrame87,t.n,t.t,nativeROI87,"actual Native395 final ROI","not offscreen simulation");report["candidate87"]=new Obj58{["active"]=comparison87.InstalledAndActive,["asset"]=ComposeComparison87.CandidateAsset,["nativeROI"]=new Arr58(nx87,ny87,nativeROI87.width,nativeROI87.height),["origin"]=new Arr58(origin87.x,origin87.y),["scale"]=scale87};
'''
assert s.count(needle)==1;s=s.replace(needle,extra+needle)
s=s.replace('newly candidate','newly candidate');(OUT/'Capture87.cs').write_bytes(s.encode())
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',HERE/'ComposeComparison87.cs',OUT/'MotionScope87.cs']
bundle(deps+[OUT/'Capture87.cs'],OUT/'RUN_Capture87.cs.txt');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("87 calibrated cached-role candidate observer compiled only");return;}\n void Prepared87(ExecutionResult result)\n {',1);(OUT/'Compile87.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile87.cs'],OUT/'RUN_Compile87.cs.txt')
for mode,prev,filename in [('Read87','Read86','CURRENT87.json'),('Post87','Post86','POST87.json')]:
 c=(OLD/(prev+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT86.json',filename).replace('POST86.json',filename);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
c=(OLD/'Verify86.cs').read_text().replace(str(OLD),str(OUT)).replace('VERIFY86.json','VERIFY87.json');(OUT/'Verify87.cs').write_bytes(c.encode());bundle([B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',OUT/'Verify87.cs'],OUT/'RUN_Verify87.cs.txt')
r=(OLD/'relay76.py').read_text().replace("'Verify86')","'Verify86','Read87','Compile87','Capture87','Post87','Verify87')");(OUT/'relay76.py').write_bytes(r.encode());(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
assert 'TotalFrames=29' in m and 'BeginBlink87();'in m and s.count('comparison87.Install()')==1 and 'Save("capturing-"+name)'not in s
assert not re.search(r'InputSystem\.settings\s*=(?!=)',s+m)
print('87 prepared: same-frame original calibration before candidate,29 actual ROI frames incl0/50/100/100/0 source blink, resource restore')
