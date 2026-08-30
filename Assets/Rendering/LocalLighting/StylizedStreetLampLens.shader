Shader "FantasySurvival/WorldLighting/StylizedStreetLampLens"
{
    Properties
    {
        _OffColor("Unlit Lens", Color) = (0.055, 0.04, 0.025, 1)
        [HDR] _OnColor("Lit Lens", Color) = (1.0, 0.48, 0.16, 1)
        _OnIntensity("Lit Intensity", Range(0, 8)) = 3.2
        [HideInInspector] _LampVisibility("Lamp Visibility", Range(0, 1)) = 0
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
        }

        Pass
        {
            Name "StreetLampLens"
            Tags { "LightMode" = "UniversalForward" }

            ZWrite On
            ZTest LEqual
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _OffColor;
                half4 _OnColor;
                float _OnIntensity;
                float _LampVisibility;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return output;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                float visibility = saturate(_LampVisibility);
                half3 color = lerp(
                    _OffColor.rgb,
                    _OnColor.rgb * _OnIntensity,
                    visibility);
                return half4(color, 1.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
