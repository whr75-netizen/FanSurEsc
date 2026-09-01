Shader "FantasySurvival/Character/Uniform Flat Lit"
{
    Properties
    {
        [MainColor] _BaseColor("Base Color", Color) = (0.91, 0.89, 0.84, 1)
        _AmbientLightStrength("Ambient Light Strength", Range(0, 2)) = 1
        _MainLightStrength("Main Light Strength", Range(0, 2)) = 0.45
        _AdditionalLightStrength("Additional Light Strength", Range(0, 2)) = 0.18
        _SteppedLocalLightStrength("Stepped Local Light Strength", Range(0, 2)) = 0.55
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
            Name "CharacterUniformFlatLit"
            Tags { "LightMode" = "UniversalForward" }

            Cull Back
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/CommonMaterial.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                half _AmbientLightStrength;
                half _MainLightStrength;
                half _AdditionalLightStrength;
                half _SteppedLocalLightStrength;
            CBUFFER_END

            float4 _CharacterLightingAnchorWS;

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return output;
            }

            half3 EvaluateUniformRealtimeLight(Light light, half strength)
            {
                if (!IsMatchingLightLayer(light.layerMask, GetMeshRenderingLayer()))
                {
                    return half3(0.0, 0.0, 0.0);
                }

                return light.color *
                    (light.distanceAttenuation * light.shadowAttenuation * strength);
            }

            half3 EvaluateUniformCharacterLighting(float3 anchorPositionWS)
            {
                const half3 flatAmbientDirection = half3(0.0, 1.0, 0.0);
                half3 lighting =
                    max(SampleSH(flatAmbientDirection), 0.0) *
                    _AmbientLightStrength;

                InputData inputData = (InputData)0;
                float4 anchorPositionCS = TransformWorldToHClip(anchorPositionWS);
                inputData.positionWS = anchorPositionWS;
                inputData.normalWS = flatAmbientDirection;
                inputData.viewDirectionWS =
                    GetWorldSpaceNormalizeViewDir(anchorPositionWS);
                inputData.shadowCoord = TransformWorldToShadowCoord(anchorPositionWS);
                inputData.normalizedScreenSpaceUV =
                    GetNormalizedScreenSpaceUV(anchorPositionCS);

                const half4 shadowMask = half4(1.0, 1.0, 1.0, 1.0);
                Light mainLight = GetMainLight(
                    inputData.shadowCoord,
                    anchorPositionWS,
                    shadowMask);
                lighting += EvaluateUniformRealtimeLight(
                    mainLight,
                    _MainLightStrength);

                #if defined(_ADDITIONAL_LIGHTS) || USE_CLUSTER_LIGHT_LOOP
                    #if USE_CLUSTER_LIGHT_LOOP
                        UNITY_LOOP for (
                            uint lightIndex = 0;
                            lightIndex < min(
                                URP_FP_DIRECTIONAL_LIGHTS_COUNT,
                                MAX_VISIBLE_LIGHTS);
                            lightIndex++)
                        {
                            Light additionalLight = GetAdditionalLight(
                                lightIndex,
                                anchorPositionWS,
                                shadowMask);
                            lighting += EvaluateUniformRealtimeLight(
                                additionalLight,
                                _AdditionalLightStrength);
                        }
                    #endif

                    uint pixelLightCount = GetAdditionalLightsCount();
                    LIGHT_LOOP_BEGIN(pixelLightCount)
                        Light additionalLight = GetAdditionalLight(
                            lightIndex,
                            anchorPositionWS,
                            shadowMask);
                        lighting += EvaluateUniformRealtimeLight(
                            additionalLight,
                            _AdditionalLightStrength);
                    LIGHT_LOOP_END
                #endif

                // This uses the exact same light definition as the world pass,
                // but normal influence is zero and every fragment uses the
                // subject anchor. Curved 3D surfaces therefore cannot appear.
                lighting += EvaluateSteppedLocalLights(
                    anchorPositionWS,
                    flatAmbientDirection,
                    0.0) * _SteppedLocalLightStrength;
                return lighting;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float3 anchorPositionWS = _CharacterLightingAnchorWS.w > 0.5
                    ? _CharacterLightingAnchorWS.xyz
                    : TransformObjectToWorld(float3(0.0, 2.0, 0.0));
                half3 lighting = EvaluateUniformCharacterLighting(anchorPositionWS);
                return half4(_BaseColor.rgb * lighting, _BaseColor.a);
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }

            ColorMask 0
            Cull Back
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings DepthVert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return output;
            }

            half4 DepthFrag(Varyings input) : SV_Target
            {
                return 0;
            }
            ENDHLSL
        }
    }

    FallBack Off
}
