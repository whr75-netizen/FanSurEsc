float4x4 _ProbeGPUVP91;float _RasterScale91;float4 _ROI348;
float4 _ClipShift333,_Profile333;float _Eye253Part,_Eye253Tag;
int _Proxy101,_Steps101;float4 _Palette101[16];
Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;o.e202Owner=v.e202SourceOwner.x;o.pos=mul(_ProbeGPUVP91,float4(o.positionWS,1));return o;}
struct O333{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 uv:SV_Target2;float4 light:SV_Target3;};
O333 Eye333Fragment(const Varyings input,uint primitiveID:SV_PrimitiveID,bool facing:SV_IsFrontFace){
 Varyings v=input;v.pos.xy=_ROI348.xy+input.pos.xy/_RasterScale91;
 float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;
 half alpha=GetMToonGeometry_Alpha(src);if(alpha<=1e-6)discard;
 MToonInput material;material.uv=uv;material.normalWS=GetMToonGeometry_Normal(v,facing?1:-1,uv);material.viewDirWS=normalize(v.viewDirWS);material.litColor=src.rgb;material.alpha=alpha;
 float g=ContinuousSurfaceLight335(v,material);int k=clamp((int)floor(saturate(g)*(_Steps101-1)+.5),0,_Steps101-1);
 int eye=clamp((int)round(v.e202Owner),1,2);float3 c=src.rgb;
 // Native face is an UNLIT source diagnostic in this first stage, not a
 // completed source-region resolver. Only socket skin has an explicit palette.
 if(_Proxy101!=0)c=_Palette101[(eye-1)*8+k].rgb;
 O333 o;o.rgba=float4(c,1);o.meta=float4(-TransformWorldToView(v.positionWS).z,_Proxy101,eye,alpha);o.uv=float4(uv,primitiveID+1,round(_Auto245Role));o.light=float4(g,k,_Steps101,_Proxy101);return o;
}
