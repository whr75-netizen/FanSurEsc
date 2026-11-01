from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent;P76=HERE.parent/'whole-eye76';sys.path.insert(0,str(P76));from probe_source76 import HEADER,HOOK
s=(HERE/'BaselineProbe77.compute').read_text()
s=s.replace('StructuredBuffer<float4> _RestTriangles348;','RWStructuredBuffer<float4> _RestTriangles348;')
start=s.index('// w metadata is source component identity.');end=s.index('FeatureSample583 NativeSample77',start);s=s[:start]+(HERE/'NativeCacheGPU77.hlsl').read_text()+'\n'+s[end:]
s=s.replace('if(component<=0)return r;','if(component<=0||NativeEye77(component)!=owner)return r;')
start=s.index('FeaturePacket19 Packet19(');end=s.index('#define NATIVE_TRI_LIMIT77',start)
# Preserve declarations before Packet19; only replace that function body.
tail=s.index('\n// Owned per-renderer source cache.',start)
old=s[start:tail]
new='''FeaturePacket19 Packet19(int2 p,int eye){if(!InEyeROI19(p))return (FeaturePacket19)0;FeaturePacket19 r=_FeatureCounts19[PacketIndex19(p,eye)];bool legacy77;
#ifdef ORIGINAL77
 legacy77=true;
#else
 legacy77=!NativeSourceReady77();
#endif
 if(legacy77){r.uv.z=round(r.uv.z)==1?1:0;r.uv.w=0;}return r;}
'''
s=s[:start]+new+s[tail:]
start=s.index('[numthreads(8,8,1)]void CountFeatures19');end=s.index('bool BeforeIris19',start)
s=s[:start]+'''[numthreads(8,8,1)]void CountFeatures19(uint3 id:SV_DispatchThreadID){
 if(any(id.xy>=(uint2)_ROI348.zw)||id.z>=2)return;
 // No other Count thread reads W metadata. The next dispatch consumes it.
 if(id.x==0&&id.y==0&&id.z==0)NativeInit77();
 int2 p=_ROI348.xy+(int2)id.xy;FeaturePacket19 packet76=CountPacket19(p,id.z);
 int eye77,feature77,sample77;float weight77;packet76.uv.zw=0;float4 owner77=_BaselineOwner348.Load(int3(p,0));
 if(ComposedSource76(p,_BaselineColour348.Load(int3(p,0)),owner77,_BaselineDomain348.Load(int3(p,0)).x>.5,eye77,feature77,weight77,sample77)&&eye77==(int)round(_Centres348[id.z].w)){
  packet76.uv.z=feature77==5?1:feature77==1?3:2;packet76.uv.w=feature77==5?sample77+1:0;
 }
 _FeatureCounts19[PacketIndex19(p,id.z)]=packet76;
}
'''+s[end:]
old='area+=c.uv.w/16;if(round(c.uv.z)==1)reserved++;';assert s.count(old)==1
s=s.replace(old,'''area+=NativeIntrinsic77(int2(x77,y77),eye)/16;if(round(c.uv.z)==1){int sample77=(int)round(c.uv.w)-1;int2 q77=(int2(x77,y77)-_ROI348.xy)*4+int2(sample77&3,sample77>>2);if(sample77>=0&&NativeComponent77((int)round(U(3,q77).z))>0)reserved++;}''')
start=s.index('float area=0;int reserved=0;for(int y77=');end=s.index('int budget=',start);s=s[:start]+s[start:end].replace('y77','areaY77').replace('x77','areaX77')+s[end:]
start=s.index('bool NativeLineAllocated19(');end=s.index('int ChooseLayers19(',start);legacy=s[start:end];guard='#ifndef ORIGINAL77\n if(NativeSourceReady77())return NativeAllocated77(p,eye);\n#endif\n';assert guard in legacy;legacy=legacy.replace(guard,'',1).replace('bool NativeLineAllocated19(','bool LegacyNativeLineAllocated76(',1);wrapper='''bool NativeLineAllocated19(int2 p,int eye){bool selected77=false;
#ifdef ORIGINAL77
 selected77=LegacyNativeLineAllocated76(p,eye);
#else
 if(NativeSourceReady77())selected77=NativeAllocated77(p,eye);else selected77=LegacyNativeLineAllocated76(p,eye);
#endif
 return selected77;
}
''';s=s[:start]+legacy+wrapper+s[end:]
core=s[s.index(HEADER)+len(HEADER):];start=core.rfind('[numthreads',0,core.index('void OriginalEvaluate76'));core=core[:start];core=core.replace(HOOK,'',1).rstrip()+'\n';assert 'OriginalEvaluate76'not in core and '_Baseline76['not in core
(HERE/'Product77GPU.inline.compute').write_bytes(core.encode())
(HERE/'BaselineProbe77GPU.compute').write_bytes(s.encode())
(HERE/'BaselineProbe77GPU.compute').write_bytes(('#pragma kernel SourceCache77\n'+s+'\n[numthreads(1,1,1)]void SourceCache77(){NativeInit77();}\n').encode())
rest0=s.index('// Owned per-renderer source cache.');rest1=s.index('FeatureSample583 NativeSample77',rest0);rest2=s.index('FeaturePacket19 CountPacket19',rest1)
cache=s[rest0:rest1];selection=s[rest1:rest2];(HERE/'NativeSourceSelection77.hlsl').write_bytes(selection.encode())
cachePath='Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCacheGPU77.hlsl';selectionPath='Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeSourceSelection77.hlsl'
linked=core.replace(cache,'#include "'+cachePath+'"\n',1).replace(selection,'#include "'+selectionPath+'"\n',1);assert linked!=core
(HERE/'Product77GPU.linked.compute').write_bytes(linked.encode())
linkedProbe=s.replace(cache,'#include "'+cachePath+'"\n',1).replace(selection,'#include "'+selectionPath+'"\n',1);(HERE/'BaselineProbe77GPU.linked.compute').write_bytes(linkedProbe.encode())
(HERE/'GPU_SOURCE77.json').write_text(json.dumps({'product76SHA':json.loads((P76/'PATCH_FINAL76.json').read_text())['afterSHA256'],'candidateInlineSHA':hashlib.sha256(s.encode()).hexdigest(),'productLinkedSHA':hashlib.sha256(linked.encode()).hexdigest(),'countMetadataProducer':'one thread, CountFeatures19, before subsequent Evaluate dispatch','countConsumers':'CountPacket19/ComposedSource76 do not read rest metadata; no cross-group spin or barrier assumption','cacheLifetime':'same owned restTriangles as existing renderer, cleared by existing disposal/reinitialization','immutable':'every XYZ and original feature count a/b, meanUV.xy','metadata':'W only: header0=77/-77; sparse source component owner/centre prefix; signed native triangle component labels','unsupported':'native triangles outside1..256, insufficient prefix, degenerate/ambiguous components or !=1 upper component per eye =>76 fallback'},indent=2)+'\n');print('Prepared bounded GPU source cache, no Assets/C# changes')
