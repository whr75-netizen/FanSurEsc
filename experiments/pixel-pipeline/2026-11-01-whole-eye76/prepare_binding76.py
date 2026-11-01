"""Reuse actual public Dispatch bindings for a write-isolated original replay."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
s=(repo/'Assets/EUnityValidation01/HeadLocal367/Runtime/EyeRenderer367.cs').read_text();a=s.index('public static void Dispatch');b=s.index('  k=cs.FindKernel("UnpackA")',a);binding=s[a:b];binding=binding[binding.index('{')+1:]
binding=binding.replace('var cs=e.candidateShader','var cs=probeShader').replace('int stage19=0','int stage19=1').replace('stage19==0?"CountFeatures19":"Evaluate"','"OriginalEvaluate76"').replace('"_RecordsWrite348",e.records','"_RecordsWrite348",owned')
binding=binding.replace('cmd.DispatchCompute(cs,k,60,34,1)','cmd.DispatchCompute(cs,k,(probeROI.width+7)/8,(probeROI.height+7)/8,1)')
binding=binding.replace('cmd.SetComputeBufferParam(cs,k,"_RecordsWrite348",owned);','cmd.SetComputeBufferParam(cs,k,"_RecordsWrite348",owned);cmd.SetComputeBufferParam(cs,k,"_Baseline76",probeBuffer);')
assert 'UnpackA'not in binding and 'e.records'not in binding
method=''' void FrozenOriginal76(EyeFeature348 e,CpuSourceCapture64.Frame frame){
  using(var owned=new ComputeBuffer(probeROI.width*probeROI.height,256)){
   var cmd=CommandBufferPool.Get("76 frozen original, owned record output only");
   try{
'''+binding+'''
    Graphics.ExecuteCommandBuffer(cmd);
   }finally{CommandBufferPool.Release(cmd);}
   var rows=new PixelReadback70.Pixel348[probeROI.width*probeROI.height];owned.GetData(rows);
   using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"original76.buffer"),FileMode.CreateNew,FileAccess.Write,FileShare.Read))){
    w.Write("original76/v1");w.Write(sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);w.Write(probeROI.x);w.Write(probeROI.y);w.Write(probeROI.width);w.Write(probeROI.height);w.Write(256);
    foreach(var r in rows)foreach(var v in new[]{r.colour,r.owner,r.intrinsic,r.visible,r.histA,r.histB,r.surface,r.pigment,r.audit,r.domain,r.bary,r.globalOwner,r.preparedMeta,r.preparedUV,r.control,r.supportMeta}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}
   }
  }
  report["frozenOriginal76"]=new Obj58{["sameFrame"]=Time.frameCount==frame.frameIndex&&native.host.main.renderedSerial335==frame.renderSerial,["actualCountsAndSampleBindings"]=true,["ownedOutputBytes"]=probeROI.width*probeROI.height*256,["borrowedTexturesWritten"]=0};
 }
'''
(HERE/'FrozenOriginal76.cs').write_text(method,encoding='utf-8');print('Prepared scoped binding reuse; no Unity call')
