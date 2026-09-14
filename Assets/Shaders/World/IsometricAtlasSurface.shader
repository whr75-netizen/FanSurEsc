Shader "FantasySurvival/World/Isometric Atlas Surface"
{
    Properties
    {
        [MainTexture] _BaseMap("Source Atlas", 2D) = "white" {}
        _MaskMap("Source Component Mask", 2D) = "white" {}
        [MainColor] _BaseColor("Tint and Opacity", Color) = (1,1,1,1)
        _Homography0("Homography Row 0", Vector) = (1,0,0,0)
        _Homography1("Homography Row 1", Vector) = (0,1,0,0)
        _Homography2("Homography Row 2", Vector) = (0,0,1,0)
        [HideInInspector] _VertexAtlasUv("Homogeneous Atlas UV in Vertex", Float) = 0
        [HideInInspector] _MetricLighting("Real Surface Lighting", Float) = 0
        [HideInInspector] _ZWrite("Depth Write", Float) = 1
        [HideInInspector] _SrcBlend("Source Blend", Float) = 1
        [HideInInspector] _DstBlend("Destination Blend", Float) = 0
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
        Pass
        {
            Name "IsometricAtlasSurface"
            Tags { "LightMode"="UniversalForward" }
            Cull Off
            ZTest LEqual
            ZWrite [_ZWrite]
            Blend [_SrcBlend] [_DstBlend]

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_BaseMap);
            TEXTURE2D(_MaskMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float4 _Homography0;
                float4 _Homography1;
                float4 _Homography2;
                float _VertexAtlasUv;
                float _MetricLighting;
            CBUFFER_END

            struct Attributes
            {
                float3 positionOS : POSITION;
                float3 uv : TEXCOORD0;
                float3 normalOS : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 uv : TEXCOORD0;
                half3 light : TEXCOORD1;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS);
                output.uv = input.uv;
                half3 n = TransformObjectToWorldNormal(input.normalOS);
                Light mainLight = GetMainLight();
                output.light = SampleSH(n) + LightingLambert(mainLight.color, mainLight.direction, n);
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                // Each physical tile or wall module supplies a unit-square UV domain.
                float3 projected;
                if (_VertexAtlasUv > 0.5)
                    projected = input.uv;
                else
                {
                    clip(min(min(input.uv.x, input.uv.y), min(1.0 - input.uv.x, 1.0 - input.uv.y)) + 1e-5);
                    float3 canonical = float3(saturate(input.uv.xy), 1.0);
                    projected = float3(dot(_Homography0.xyz, canonical),
                        dot(_Homography1.xyz, canonical), dot(_Homography2.xyz, canonical));
                }
                clip(projected.z - 1e-6);
                float2 atlasUv = projected.xy / projected.z;
                half component = SAMPLE_TEXTURE2D(_MaskMap, sampler_PointClamp, atlasUv).r;
                clip(component - 0.5h);
                half4 source = SAMPLE_TEXTURE2D(_BaseMap, sampler_PointClamp, atlasUv);
                // Clip the source mask, not the fader opacity: a faded roof may intentionally be below 0.1.
                clip(source.a - 0.1h);
                source.rgb *= lerp(half3(1,1,1), input.light, _MetricLighting);
                return source * _BaseColor;
            }
            ENDHLSL
        }
    }
}
