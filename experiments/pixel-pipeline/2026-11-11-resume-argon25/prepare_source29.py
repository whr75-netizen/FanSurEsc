"""Prepare a native MToon-outline producer; no import/Play/dispatch here."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face29';REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True)
 shader=(REPO/'Assets/EUnityValidation01/MinimalRestore335/Shaders/LegacySignals335.shader').read_text(encoding='utf-8-sig')
 properties=shader[shader.index('    Properties'):shader.index('    // Shader Model')]
 common='''
            #pragma target 4.5
            #pragma vertex Vertex29
            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _MTOON_PARAMETERMAP
            #define MTOON_URP
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_uv.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_alpha.hlsl"
            float4x4 _ProbeGPUVP29,_ProbeView29;float4 _SourceOutline29;
            Varyings Vertex29(Attributes v){Varyings o=MToonVertex(v);o.pos=mul(_ProbeGPUVP29,float4(o.positionWS,1));return o;}
            float Alpha29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half a=GetMToonGeometry_Alpha(src);if(a<=1e-6)discard;return a;}
'''
 depth='''
        Pass{Name "SourceDepth29" Cull [_M_CullMode] ZWrite On ZTest LEqual Blend One Zero ColorMask 0
        HLSLPROGRAM
        #pragma fragment Depth29
'''+common+'''float4 Depth29(Varyings v):SV_Target{Alpha29(v);return 0;}
        ENDHLSL
        }
'''
 outline='''
        Pass{Name "SourceOutline29" Cull Front ZWrite On ZTest LEqual Offset 1,1 Blend One Zero
        HLSLPROGRAM
        #pragma fragment Outline29
        #define MTOON_PASS_OUTLINE
        #define _MTOON_OUTLINE_WORLD
'''+common+'''struct Out29{float4 colour:SV_Target0;float4 meta:SV_Target1;};
        Out29 Outline29(Varyings v){float a=Alpha29(v);Out29 o;o.colour=float4(_SourceOutline29.rgb,a);o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,v.uv,1);return o;}
        ENDHLSL
        }
'''
 source='Shader "EValidation/SourceBoundary29"{\n'+properties+'SubShader{Tags{"RenderPipeline"="UniversalPipeline"}\n'+depth+outline+'}\n}\n'
 p=G/'SourceOutline29.shader';p.write_text(source,encoding='utf-8',newline='\n')
 old=H/'face28/capture-stages/RUN_Capture25.cs.txt';s=old.read_text(encoding='utf-8');target=G/'run';target.mkdir(exist_ok=True)
 assert not(target/'PHASE_REQUEST.json').exists(),'Submitted source is immutable'
 token='const string Root=@"'+str(H/'face28/capture-stages')+'";';assert s.count(token)==1;s=s.replace(token,'const string Root=@"'+str(target)+'";')
 token=' void Arm76(NativePlayer395 n){';assert s.count(token)==1;s=s.replace(token,' SourceOutline29 outline29;\n'+token)
 token='calibrated89=true;armed102=true;';assert s.count(token)==1
 s=s.replace(token,'outline29=new SourceOutline29(probeEye,forward102,@"'+str(H/'producer/support/surface27/FACE_INPUT27.json')+'");layer102.AfterCanvas+=outline29.Record;'+token)
 token='void Release76(){';assert s.count(token)==1;s=s.replace(token,token+'if(layer102!=null&&outline29!=null)layer102.AfterCanvas-=outline29.Record;outline29?.Dispose();report["sourceOutlineDisposed29"]=outline29==null||outline29.Disposed;outline29=null;')
 token='  CaptureStages28(n,hf);CaptureColumns26();';assert s.count(token)==1
 s=s.replace(token,'''  outline29.AssertRendered();report["sourceOutline29"]=outline29.Info;
  for(int i=0;i<4;i++){var t=outline29.Fields[i];for(int y=0;y<t.rt.height;y+=16)Plane(hf,"OUTLINE29-"+i+"-y"+y.ToString("D4"),t,new RectInt(0,y,t.rt.width,Math.Min(16,t.rt.height-y)),"native evaluated mesh/MToon source world outline; actual depth occluders","source outline RGB/alpha or linear depth/UV; hair ON/OFF pairs");}
  var cr29=outline29.ROI;var class29=outline29.Classification;Plane(hf,"CLASS29",class29,new RectInt(0,0,cr29.width,cr29.height),"actual GPU29 typed source evidence","silhouette coverage/native pigment support/Q transition/provenance bits");
  var qr29=new RectInt(Math.Max(0,cr29.x-1),Math.Max(0,272-cr29.y-cr29.height-1),Math.Min(480,cr29.x+cr29.width+1)-Math.Max(0,cr29.x-1),Math.Min(272,272-cr29.y+1)-Math.Max(0,272-cr29.y-cr29.height-1));
  Plane(hf,"Q29",n.host.head.style480[3],qr29,"same-frame existing550 independent shade classifier","Q/continuous g/linear depth/alpha");
  Plane(hf,"META29",n.host.head.native[5],new RectInt(2*qr29.x,2*qr29.y,2*qr29.width,2*qr29.height),"same-frame native550 metadata","physical960 depth/role/side/primitive");
  CaptureStages28(n,hf);CaptureColumns26();''')
 s+='\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'+(H/'SourceOutline29.cs').read_text(encoding='utf-8')+'\n}\n'
 assert 'EvaluateForm115'not in s and 'BoundRun115'not in s
 out=target/'RUN_Capture25.cs.txt';out.write_text(s,encoding='utf-8',newline='\n')
 import shutil;shutil.copyfile(H/'face28/capture-stages/GLOBAL_NAMES66.json',target/'GLOBAL_NAMES66.json')
 sys.path.insert(0,str(H/'producer'));from prepare_live import compile_cs
 compile_cs(out)
 result={'externalHostSHA256':sha(out),'shaderSHA256':sha(p),'newComputeKernels':1,'newComputeDispatches':1,'boundedClassifier':'max4096 logical cells,64 samples+4neighbours/thread; no BVH/dynamic arrays/enumeration/history','scope':'native world-mode outline producer; separate clone/offscreen, source-backed direct ink','maxOffscreenSubsamples':262144,'shaderDrawPasses':2,'hairVariants':2,'maxReadbackBytes':4096*16*16,'product77Changed':False,'hostCPUCompile':'passed','shaderUnityImport':'not done','sourceOutlineIsRasterizedPigment':'No; actual normal-extruded source silhouette geometry','regionPartition':'separate; no unresolved colour field classified by RGB darkness'}
 (G/'PREPARED29.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
