 void Capture(NativePlayer395 n,Gameplay397 gp){
  layer101.AssertRendered();int serial=n.host.main.renderedSerial335,frameIndex=Time.frameCount;var h=n.host.head;var m=n.host.main;var e=n.host.headEyes;
  if(e!=probeEye||e.candidateShader!=oldShader)throw new InvalidOperationException("101 product77 binding changed");
  var hf=Frame(h,"product77-head-and-layer101",serial);var mf=Frame(m,"product77-main",serial);var r=e.roi;var er=new RectInt(r.x,272-r.y-r.height,r.width,r.height);var hr=new RectInt(Math.Max(0,er.x-12),Math.Max(0,er.y-20),r.width+24,r.height+40);var mr=new RectInt(hr.x+n.host.offset.x,hr.y+n.host.offset.y,hr.width,hr.height);
  report["renderPath101"]="product77 control plus isolated Layer0; no old295/348 colour read by candidate; no product replacement";
  report["layer101Source"]=layer101.Source.Info;report["layer101RoleLimits"]="native face is source-unlit diagnostic; socket proxy uses finite source-skin palette; whole-face region resolver and whole-eye forward layer pending";
  report["grid101"]=new Obj58{["headROI"]=new Arr58(hr.x,hr.y,hr.width,hr.height),["mainROI"]=new Arr58(mr.x,mr.y,mr.width,mr.height),["eyeTopLeftROI"]=new Arr58(r.x,r.y,r.width,r.height),["headToMainOffset"]=new Arr58(n.host.offset.x,n.host.offset.y),["sampleScale"]=4,["headView"]=M(h.motion.camera.worldToCameraMatrix),["headProjection"]=M(h.effectiveProjection)};
  foreach(var t in new[]{new{n="H-product77-final",t=h.colour},new{n="H-product77-owner",t=h.owner},new{n="H-before-legacy-eyes",t=h.postLine},new{n="H-sourceMETA",t=h.motion.raw[5]}})Plane(hf,t.n,t.t,hr,"product77 unchanged","control only");
  for(int i=0;i<4;i++){var t=layer101.Fields[i];Plane(hf,"L0-"+new[]{"RGBA","META","UV","LIGHT"}[i],t,new RectInt(0,0,t.rt.width,t.rt.height),"LayerZero101 actual same-camera graph pass","4x clean canvas; no previous eye input");}
  for(int i=0;i<5;i++)foreach(var t in new[]{new{n="rgba",t=e.samples[i].rgba},new{n="meta",t=e.samples[i].meta}})Plane(hf,"S"+i+"-"+t.n,t.t,new RectInt(0,0,t.t.rt.width,t.t.rt.height),"product77 actual current native samples","same frame source geometry and alpha; reference only");
  Plane(mf,"M-product77-final",m.colour,mr,"product77 unchanged","logical full head control");
  report["frameIndex"]=frameIndex;report["mainSerial"]=serial;report["sourceFrame"]=h.motion.sourceFrame;report["evaluatedFrame"]=h.motion.evaluatedFrame;report["layer101Frame"]=layer101.RenderedFrame;report["frameUnchangedDuringReadback"]=Time.frameCount==frameIndex&&n.host.main.renderedSerial335==serial;
  if(!(bool)report["frameUnchangedDuringReadback"])throw new InvalidOperationException("101 frame changed during bounded readback");
  report["packetComplete"]=true;report["planes"]=planes;CreateOnly73.Text(Path.Combine(output,"RAW_MANIFEST.json"),report.ToString());CreateOnly73.Text(Path.Combine(output,"RAW_COMPLETE76.marker"),SHA(Path.Combine(output,"RAW_MANIFEST.json")));Save("layer0-capture-complete");
 }
