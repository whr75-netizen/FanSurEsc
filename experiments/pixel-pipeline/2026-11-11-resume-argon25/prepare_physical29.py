"""CPU-only correction after29 failed. No Unity/import/GPU/Play action."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face29';D=G/'physical-fix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=G/'run/RUN_Capture25.cs.txt';s=original.read_text(encoding='utf-8');assert sha(original)=='9a21259f9296550b5f373245cf98999889c6e5fcc7e85f8a59754bb139ceea34'
 tag='namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n// Owns only cloned materials';at=s.index(tag);s=s[:at]+'namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'+(D/'SourceOutline29.cs').read_text(encoding='utf-8')+'\n}\n'
 s=s.replace('const string Root=@"'+str(G/'run')+'";','const string Root=@"'+str(G/'physical-run')+'";')
 s=s.replace('new SourceOutline29(probeEye,forward102,@"'+str(H/'producer/support/surface27/FACE_INPUT27.json')+'")','new SourceOutline29(probeEye,@"'+str(H/'producer/support/surface27/FACE_INPUT27.json')+'",@"'+str(H.parent/'renderer-family59/SOURCE_REGISTRY59.json')+'")')
 s=s.replace('for(int i=0;i<4;i++){var t=outline29.Fields[i];','for(int i=0;i<8;i++){var t=outline29.Fields[i];')
 assert s.count('   if(renderError89!=null)')==1
 s=s.replace('   if(renderError89!=null)','   outline29?.CheckFailure();if(renderError89!=null)')
 assert 'joint.DenseNative'not in s[at:]and s.count('outline29?.CheckFailure();')==1
 out=D/'RUN_Capture25.cs.txt';out.write_text(s,encoding='utf-8',newline='\n');sys.path.insert(0,str(H/'producer'));from prepare_live import compile_cs;compile_cs(out)
 shader=(G/'SourceOutline29.shader').read_text(encoding='utf-8');a=shader.index('            #pragma target 4.5');b=shader.index('float4 Depth29(');common=shader[a:b]
 pigment='''Pass{Name "SourcePigment29" Cull [_M_CullMode] ZWrite Off ZTest LEqual Blend One Zero
HLSLPROGRAM
#pragma fragment Pigment29
'''+common+'''struct OutPigment29{float4 colour:SV_Target0;float4 meta:SV_Target1;};
OutPigment29 Pigment29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;float materialAlpha=Alpha29(v);if(src.a<=1e-6)discard;OutPigment29 o;o.colour=src;o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,uv,materialAlpha);return o;}
ENDHLSL
}
'''
 assert shader.endswith('}\n}\n');shader=shader[:-4]+pigment+'}\n}\n';shader=shader.replace('Name "SourceDepth29" Cull [_M_CullMode] ZWrite On','Name "SourceDepth29" Cull [_M_CullMode] ZWrite [_M_ZWrite]')
 p=D/'SourceOutline29.shader';p.write_text(shader,encoding='utf-8',newline='\n')
 result={'CPUHostCompile':'passed','hostSHA256':sha(out),'proposedShaderSHA256':sha(p),'shaderImport':False,'GPUExecution':False,'appliedAssets':False,'fixes':['Remove canonical DenseNative as physical sample supplier; native source pigment has own physical8x pass on the exact same source grid as outline.','Use source material depth-write/discard and preserve raw pigment alpha separately from material alpha.','Validate before recording, defer own failures outside RenderGraph; never throw own guard through URP graph recording.','Cache native topology/material identities per view; own all targets/materials/classifier and never dispose borrowed renderer buffers.'],'stillUnverified':['Native source outline/pigment raster output and class CPU/GPU equivalence.','Partial transparent occlusion and full face colour-region mapping.','New failures no longer abort URP graph in real Editor; only CPU compile inspected.','Same-object material/texture content edits need source-generation invalidation before production use.','URP ZBinning job public Edit stability does not prove all internal jobs released; no new render performed.'],'ownedRTWorstBytes':262144*(8*16+4)+4096*16,'dynamicGPUArraysBVH115':False}
 (D/'CPU_PHYSICAL29.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
