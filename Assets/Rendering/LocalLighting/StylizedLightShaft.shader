Shader "Hidden/FantasySurvival/StylizedLightShaft"
{
    Properties
    {
        [HideInInspector] _ShaftSourceMode("Source Mode", Float) = 0
        [HideInInspector][HDR] _ShaftColor("Shaft Color", Color) = (1, 1, 1, 1)
        [HideInInspector] _ShaftIntensity("Shaft Intensity", Float) = 0
        [HideInInspector] _ShadowThreshold("Shadow Threshold", Range(0, 1)) = 0.52
        [HideInInspector] _DensityBands("Density Bands", Float) = 4
        [HideInInspector] _NoiseStrength("Noise Strength", Range(0, 1)) = 0.16
        [HideInInspector] _WorldCellSize("World Cell Size", Float) = 0.22
        [HideInInspector] _SurfaceFadeDistance("Surface Fade Distance", Float) = 0.45
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+20"
        }

        ZTest LEqual
        ZWrite Off
        Cull Off
        Blend One One
        ColorMask RGB

        Pass
        {
            Name "StylizedLightShaft"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _LIGHT_COOKIES

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _ShaftSourceMode;
                half4 _ShaftColor;
                float _ShaftIntensity;
                float _ShadowThreshold;
                float _DensityBands;
                float _NoiseStrength;
                float _WorldCellSize;
                float _SurfaceFadeDistance;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs positions = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = positions.positionCS;
                output.positionWS = positions.positionWS;
                output.uv = input.uv;
                return output;
            }

            float Hash31(float3 value)
            {
                value = frac(value * 0.1031);
                value += dot(value, value.yzx + 33.33);
                return frac((value.x + value.y) * value.z);
            }

            float Quantize01(float value, float bands)
            {
                float intervals = max(round(bands) - 1.0, 1.0);
                return floor(saturate(value) * intervals + 0.5) / intervals;
            }

            float SampleSunTransmission(float3 positionWS)
            {
                float4 shadowCoord = TransformWorldToShadowCoord(positionWS);
                Light baseLight = GetMainLight();
                Light sampledLight = GetMainLight(
                    shadowCoord,
                    positionWS,
                    half4(1.0, 1.0, 1.0, 1.0));
                float baseLuminance = max(
                    dot(baseLight.color, half3(0.2126, 0.7152, 0.0722)),
                    0.0001);
                float sampledLuminance = dot(
                    sampledLight.color,
                    half3(0.2126, 0.7152, 0.0722));
                float cookieAttenuation = saturate(sampledLuminance / baseLuminance);
                return sampledLight.shadowAttenuation * cookieAttenuation;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                float2 screenUV = input.positionCS.xy / _ScaledScreenParams.xy;
                float rawSceneDepth = SampleSceneDepth(screenUV, sampler_PointClamp);
                float sceneEyeDepth = unity_OrthoParams.w == 0.0
                    ? LinearEyeDepth(rawSceneDepth, _ZBufferParams)
                    : LinearDepthToEyeDepth(rawSceneDepth);
                float fragmentEyeDepth = -TransformWorldToView(input.positionWS).z;
                float surfaceFade = saturate(
                    (sceneEyeDepth - fragmentEyeDepth) /
                    max(_SurfaceFadeDistance, 0.001));

                float sourceMode = step(0.5, _ShaftSourceMode);
                float lightVisibility = 1.0;
                UNITY_BRANCH
                if (_ShaftSourceMode < 0.5)
                {
                    float sunTransmission = SampleSunTransmission(input.positionWS);
                    lightVisibility = step(_ShadowThreshold, sunTransmission);
                }

                float safeCellSize = max(_WorldCellSize, 0.001);
                float3 snappedCell = floor(input.positionWS / safeCellSize + 0.5);
                float noise = Hash31(snappedCell);
                float noisyDensity = lerp(1.0 - _NoiseStrength, 1.0, noise);
                float density = Quantize01(noisyDensity, _DensityBands);

                float endFade =
                    smoothstep(0.0, 0.055, input.uv.y) *
                    (1.0 - smoothstep(0.82, 1.0, input.uv.y));
                float localLateralFade = pow(
                    saturate(1.0 - abs(input.uv.x * 2.0 - 1.0)),
                    0.65);
                float lateralFade = lerp(1.0, localLateralFade, sourceMode);
                float contribution =
                    _ShaftIntensity * lightVisibility * density *
                    endFade * lateralFade * surfaceFade;

                return half4(_ShaftColor.rgb * contribution, 0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
