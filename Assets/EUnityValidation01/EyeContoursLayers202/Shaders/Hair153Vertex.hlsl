#define MToonVertex E153OriginalMToonVertex
#include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
#undef MToonVertex
Varyings MToonVertex(const Attributes v){
    Varyings output=E153OriginalMToonVertex(v);
#if defined(E202_INDEPENDENT)
output.e202Control=v.apertureControl.xy;output.e202Owner=v.e202SourceOwner.x;
#endif
    if(_E153Enable>.5 && !MToon_IsOutlinePass()){
        if(_E154AnchorActive>.5){
            float3 p=mul(_E154WorldToProxy,float4(output.positionWS,1)).xyz;
            float3 d=p-_E153ProxyCenter.xyz;d.y=max(0,d.y);
            float3 n=normalize(d*_E153ProxyInvSq.xyz);
            output.normalWS=normalize(mul((float3x3)_E154ProxyNormalToWorld,n));
        }else{
            float3 d=v.vertex.xyz-_E153ProxyCenter.xyz;d.y=max(0,d.y);
            float3 n=normalize(d*_E153ProxyInvSq.xyz);
            output.normalWS=MToon_TransformObjectToWorldNormal(n);
        }
    }
    uint e158Role=(uint)round(_E151Role);
    if(_E158Enabled>.5 && !MToon_IsOutlinePass() && (e158Role==1u||e158Role==2u||e158Role==4u||e158Role==6u)){
        bool ocular=e158Role==1u||e158Role==2u;
        float3 a0=ocular?_E158EyeAnchor0.xyz:_E158HeadAnchor0.xyz;
        float3 a1=ocular?_E158EyeAnchor1.xyz:_E158HeadAnchor1.xyz;
        bool right=dot(output.positionWS-a0,output.positionWS-a0)<dot(output.positionWS-a1,output.positionWS-a1);
        float3 anchor=right?a0:a1;
        float scale=ocular?(right?_E158Scales.x:_E158Scales.y):(e158Role==4u?_E158Scales.z:_E158Scales.w);
        output.positionWS=anchor+(output.positionWS-anchor)*scale;
        output.pos=TransformWorldToHClip(output.positionWS);
        output.viewDirWS=MToon_GetWorldSpaceNormalizedViewDir(output.positionWS);
    }
    if(_E162ApertureEnabled>.5 && !MToon_IsOutlinePass() && (e158Role==3u||e158Role==6u)){
        float3 hp=mul(_E162WorldToHead,float4(output.positionWS,1)).xyz;
        bool right=v.apertureControl.x>=v.apertureControl.y;
        float w=right?v.apertureControl.x:v.apertureControl.y;
        float3 centre=right?_E162Centre0.xyz:_E162Centre1.xyz;
        hp.xy+=(hp.xy-centre.xy)*(_E162ApertureScale.xy-1)*w;
        output.positionWS=mul(_E162HeadToWorld,float4(hp,1)).xyz;
        output.pos=TransformWorldToHClip(output.positionWS);
        output.viewDirWS=MToon_GetWorldSpaceNormalizedViewDir(output.positionWS);
    }
    output.semanticMask=e158Role==11u?v.semantic0:e158Role==12u?v.semantic1:e158Role==13u?v.semantic2:e158Role==14u?v.semantic3:float4(0,0,0,0);
    output.ownedUV=v.texcoord1;
    return output;
}
