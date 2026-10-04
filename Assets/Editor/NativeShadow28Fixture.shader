Shader "Hidden/NativeShadow28Fixture"
{
    Properties { _NativeRenderOffsetWS("Shared render translation", Vector) = (0,0,0,0) }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "DisableBatching"="True" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            ZWrite On Cull Back
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial) float4 _NativeRenderOffsetWS; CBUFFER_END
            struct A { float3 p:POSITION; };
            struct V { float4 p:SV_POSITION; float3 world:TEXCOORD0; };
            V Vert(A a) { V v; v.world=TransformObjectToWorld(a.p)+_NativeRenderOffsetWS.xyz; v.p=TransformWorldToHClip(v.world); return v; }
            float4 Frag(V v):SV_Target { return float4(v.world,1); }
            ENDHLSL
        }
    }
}
