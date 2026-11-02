"""Produce apply_patch edits for the new external115 capture only."""
from pathlib import Path
import json,difflib
H=Path(__file__).resolve().parent
old=(H/'Capture115.cs').read_text(encoding='utf8');new=old
rules=[(r'argon23-runtime113\attempt5',r'gpu-form115'),('Forward113','Forward115'),('Shaders/ForwardEye114.compute','Shaders/ForwardEye115.compute'),('eye113-','eye115-'),('STATE113-','STATE115-'),('TRACE113-','TRACE115-'),('algorithmValid113','algorithmValid115'),('regionErrorFlags113','regionErrorFlags115'),('computeAsset113','computeAsset115'),('computeSHA113','computeSHA115'),('runtimeShaderName113','runtimeShaderName115'),('REGION113-','REGION115-'),('legacy106-','baseline113-')]
for a,b in rules:
 assert a in new,(a,'missing capture input token');new=new.replace(a,b)
new=new.replace('106 current deformed source curve, same-input GPU102 comparison; product77 unchanged','115 complete source-form and paired4x destination; actual same-input113 baseline; product77 unchanged')
# Export both actual live whole-character alternatives from the same frame.
needle='FullStrips113(hf,"FULL-candidate113",rt,'
assert needle in new;new=new.replace(needle,'FullStrips113(hf,"FULL-candidate115",rt,')
new=new.replace('JointBuffer102("REGION115-cells",forward102.Region.cells);','Extra115();FullBaseline113(hf,n,e);JointBuffer102("REGION115-cells",forward102.Region.cells);')
# Add exact typed diagnostics for source moments, complete primary pool and
# source-form interval metrics; counts/strides remain explicit and bounded.
extra=r'''
 struct StatRead115{public Vector4 low,high;}
 struct MetricRead115{public Vector4 low0,high0,low1,high1,info;}
 void WriteV115(BinaryWriter w,Vector4 v){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}
 void Stats115(string name,GraphicsBuffer b,int count){if(b.stride!=32||count>b.count||count*32>245760)throw new InvalidOperationException("115 bounded typed statistics");var data=new StatRead115[count];b.GetData(data,0,0,count);using(var w=new BinaryWriter(new FileStream(Path.Combine(output,name+".f32"),FileMode.CreateNew))){w.Write(count*2);w.Write(16);foreach(var s in data){WriteV115(w,s.low);WriteV115(w,s.high);}}}
 void Group115(string name,GraphicsBuffer b){if(b.count!=2||b.stride!=48)throw new InvalidOperationException("115 group layout");var data=new GroupRead113[2];b.GetData(data);using(var w=new BinaryWriter(new FileStream(Path.Combine(output,name+".f32"),FileMode.CreateNew))){w.Write(6);w.Write(16);foreach(var s in data){WriteV115(w,s.score);WriteV115(w,s.masks);WriteV115(w,s.tail);}}}
 void Extra115(){var r=forward102.Region;int cells=forward102.DenseSource.Engine.Width/8*(forward102.DenseSource.Engine.Height/8);Stats115("FORM115-cell-key",r.moments,cells*r.Cells.keys.count);Stats115("FORM115-reference",r.references,r.references.count);JointBuffer102("FORM115-state",r.state);JointBuffer102("FORM115-candidates",r.candidates);Group115("FORM115-primary",r.primary);JointBuffer102("BASE113-frame",forward102.Baseline113.frame);Group115("BASE113-best",forward102.Baseline113.best);
  var data=new MetricRead115[r.metrics.count];r.metrics.GetData(data);using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"FORM115-metrics.f32"),FileMode.CreateNew))){w.Write(data.Length*5);w.Write(16);foreach(var s in data){WriteV115(w,s.low0);WriteV115(w,s.high0);WriteV115(w,s.low1);WriteV115(w,s.high1);WriteV115(w,s.info);}}
  var survivors=new uint[r.survivors.count];r.survivors.GetData(survivors);using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"FORM115-survivors.u32"),FileMode.CreateNew))){w.Write(survivors.Length);w.Write(4);foreach(uint v in survivors)w.Write(v);}
  int bw=forward102.BaselineCarrierNative.currentWidth,bh=forward102.BaselineCarrierNative.currentHeight;foreach(int part in new[]{1,2,3})foreach(var c in new[]{new{n="rgba",i=0},new{n="meta",i=1},new{n="rest",i=2},new{n="uv",i=3}})Plane(null,"BC-part"+part+"-"+c.n,forward102.BaselineCarrierNative.Handles96[part][c.i],new RectInt(0,0,bw,bh),"115 same-frame baseline113 native8x carrier","original113 path");JointSlice107("baseline113-carrier-visibility",forward102.BaselineCarrierSource.Engine.Visibility,bw*bh,bw*bh*3);
  report["sourceForm115"]=r.Info;report["actualBaseline113SameFrame115"]=true;report["sourceForm115RuntimeLayoutInputReplay"]=false;
 }
 void FullBaseline113(CpuSourceCapture64.Frame hf,NativePlayer395 n,EyeFeature348 e){var rt=RTHandles.Alloc(480,272,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"115 owned full113 control");var cmd=CommandBufferPool.Get("115 same-frame actual113 full character");try{var cs=forward102.Source.Engine.Shader;int k=cs.FindKernel("ComposeWhole113");cmd.SetComputeTextureParam(cs,k,"_FullBase113",n.host.main.colour.rt);cmd.SetComputeTextureParam(cs,k,"_CandidateTile113",forward102.LegacyFields[2].rt);cmd.SetComputeTextureParam(cs,k,"_FullOut113",rt.rt);cmd.SetComputeIntParams(cs,"_TileRect113",e.roi.x+Mathf.RoundToInt(n.host.offset.x),272-e.roi.y-e.roi.height+Mathf.RoundToInt(n.host.offset.y),e.roi.width,e.roi.height);cmd.DispatchCompute(cs,k,60,34,1);Graphics.ExecuteCommandBuffer(cmd);FullStrips113(hf,"FULL-baseline113",rt,"same frame actual old113 selection +8x destination","115 control");}finally{CommandBufferPool.Release(cmd);rt.Release();}}
'''
pos=new.rfind('\n}');new=new[:pos]+extra+new[pos:]
diff=list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=1,lineterm=''));patch='*** Begin Patch\n*** Update File: '+str((H/'Capture115.cs').resolve())+'\n'+'\n'.join('@@'if l.startswith('@@')else l for l in diff[2:])+'\n*** End Patch';print(json.dumps(patch))
