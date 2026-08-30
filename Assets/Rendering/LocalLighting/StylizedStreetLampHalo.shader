Shader "FantasySurvival/WorldLighting/StylizedStreetLampHalo"
{
    Properties
    {
        [HDR] _Color("Halo Color", Color) = (1.0, 0.38, 0.10, 1)
        _Intensity("Halo Intensity", Range(0, 4)) = 0.7
        _Bands("Density Bands", Range(2, 8)) = 5
        [HideInInspector] _LampVisibility("Lamp Visibility", Range(0, 1)) = 0
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+10"
        }

        Pass
        {
            Name "StreetLampHalo"
            Tags { "LightMode" = "UniversalForward" }

            ZWrite Off
            ZTest LEqual
            Cull Off
            Blend One One
            ColorMask RGB

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                float _Intensity;
                float _Bands;
                float _LampVisibility;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                float4x4 objectToWorld = GetObjectToWorldMatrix();
                float scaleX = length(float3(
                    objectToWorld._m00,
                    objectToWorld._m10,
                    objectToWorld._m20));
                float scaleY = length(float3(
                    objectToWorld._m01,
                    objectToWorld._m11,
                    objectToWorld._m21));
                float3 cameraRight = normalize(float3(
                    UNITY_MATRIX_I_V._m00,
                    UNITY_MATRIX_I_V._m10,
                    UNITY_MATRIX_I_V._m20));
                float3 cameraUp = normalize(float3(
                    UNITY_MATRIX_I_V._m01,
                    UNITY_MATRIX_I_V._m11,
                    UNITY_MATRIX_I_V._m21));
                float3 centerWS = TransformObjectToWorld(float3(0.0, 0.0, 0.0));
                float3 positionWS = centerWS +
                    cameraRight * input.positionOS.x * scaleX +
                    cameraUp * input.positionOS.y * scaleY;
                output.positionCS = TransformWorldToHClip(positionWS);
                output.uv = input.uv;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                float radius = length((input.uv - 0.5) * 2.0);
                float density = pow(saturate(1.0 - radius), 1.7);
                float intervals = max(round(_Bands) - 1.0, 1.0);
                float steppedDensity = floor(density * intervals + 0.5) / intervals;
                float contribution =
                    steppedDensity * _Intensity * saturate(_LampVisibility);
                return half4(_Color.rgb * contribution, 0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
