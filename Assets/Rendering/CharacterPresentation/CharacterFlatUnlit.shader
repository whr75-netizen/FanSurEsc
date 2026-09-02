Shader "FantasySurvival/Character/Spatial Flat Lit"
{
    Properties
    {
        [MainColor] _BaseColor("Palette Light Color", Color) = (0.9843137, 0.9294118, 0.8784314, 1)
        _PaletteMidColor("Palette Mid Color", Color) = (0.9019608, 0.7215686, 0.6235294, 1)
        _PaletteShadowColor("Palette Shadow Color", Color) = (0.7254902, 0.4705882, 0.4078431, 1)
        _PaletteDarkColor("Palette Dark Color", Color) = (0.4196078, 0.2745098, 0.3137255, 1)
        _PaletteReferenceBrightness("Palette Reference Brightness", Range(0.05, 2)) = 0.65
        _PaletteFeather("Palette Transition Feather", Range(0.001, 0.1)) = 0.025
        _LocalLightTintInfluence("Local Light Tint Influence", Range(0, 1)) = 0.18
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
            Name "CharacterSpatialFlatLit"
            Tags { "LightMode" = "UniversalForward" }

            Cull Back
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma editor_sync_compilation
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/CommonMaterial.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                half4 _PaletteMidColor;
                half4 _PaletteShadowColor;
                half4 _PaletteDarkColor;
                half _PaletteReferenceBrightness;
                half _PaletteFeather;
                half _LocalLightTintInfluence;
                half _AmbientLightStrength;
                half _MainLightStrength;
                half _AdditionalLightStrength;
                half _SteppedLocalLightStrength;
            CBUFFER_END

            // Pixel snapping moves only the presentation hierarchy. This offset
            // restores the unsnapped world position used by spatial lighting so
            // camera movement cannot drag the character through light boundaries.
            float4 _CharacterLightingPositionOffsetWS;

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            struct CharacterLightingSample
            {
                half environmentBrightness;
                half3 spatialLighting;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                return output;
            }

            half3 EvaluateSurfaceNeutralRealtimeLight(Light light, half strength)
            {
                if (!IsMatchingLightLayer(light.layerMask, GetMeshRenderingLayer()))
                {
                    return half3(0.0, 0.0, 0.0);
                }

                return light.color *
                    (light.distanceAttenuation * light.shadowAttenuation * strength);
            }

            CharacterLightingSample EvaluateSpatialFlatCharacterLighting(
                float3 positionWS,
                float4 fragmentPositionCS)
            {
                const half3 flatAmbientDirection = half3(0.0, 1.0, 0.0);
                half3 environmentLighting =
                    max(SampleSH(flatAmbientDirection), 0.0) *
                    _AmbientLightStrength;

                InputData inputData = (InputData)0;
                inputData.positionWS = positionWS;
                inputData.normalWS = flatAmbientDirection;
                inputData.viewDirectionWS =
                    GetWorldSpaceNormalizeViewDir(positionWS);
                inputData.shadowCoord = TransformWorldToShadowCoord(positionWS);
                inputData.normalizedScreenSpaceUV =
                    GetNormalizedScreenSpaceUV(fragmentPositionCS);

                const half4 shadowMask = half4(1.0, 1.0, 1.0, 1.0);
                Light mainLight = GetMainLight(
                    inputData.shadowCoord,
                    positionWS,
                    shadowMask);
                environmentLighting += EvaluateSurfaceNeutralRealtimeLight(
                    mainLight,
                    _MainLightStrength);

                CharacterLightingSample sample;
                // Sky ambient and the sun/moon choose a palette stage through
                // luminance only. This keeps weather and time-of-day visibility
                // without painting the whole flat character blue.
                sample.environmentBrightness = max(
                    Luminance(environmentLighting),
                    0.0);
                sample.spatialLighting = half3(0.0, 0.0, 0.0);

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
                                positionWS,
                                shadowMask);
                            sample.spatialLighting += EvaluateSurfaceNeutralRealtimeLight(
                                additionalLight,
                                _AdditionalLightStrength);
                        }
                    #endif

                    uint pixelLightCount = GetAdditionalLightsCount();
                    LIGHT_LOOP_BEGIN(pixelLightCount)
                        Light additionalLight = GetAdditionalLight(
                            lightIndex,
                            positionWS,
                            shadowMask);
                        sample.spatialLighting += EvaluateSurfaceNeutralRealtimeLight(
                            additionalLight,
                            _AdditionalLightStrength);
                    LIGHT_LOOP_END
                #endif

                // Spatial attenuation is evaluated per visible character pixel,
                // while normal influence stays at zero. Light boundaries can
                // cross the silhouette without revealing the mesh curvature.
                sample.spatialLighting += EvaluateSteppedLocalLights(
                    positionWS,
                    flatAmbientDirection,
                    0.0) * _SteppedLocalLightStrength;
                return sample;
            }

            half EvaluatePaletteTransition(
                half normalizedBrightness,
                half threshold)
            {
                half feather = max(_PaletteFeather, 0.001);
                return smoothstep(
                    threshold - feather,
                    threshold + feather,
                    normalizedBrightness);
            }

            half3 EvaluateCharacterPalette(half normalizedBrightness)
            {
                half3 paletteColor = _PaletteDarkColor.rgb;
                paletteColor = lerp(
                    paletteColor,
                    _PaletteShadowColor.rgb,
                    EvaluatePaletteTransition(normalizedBrightness, 0.28));
                paletteColor = lerp(
                    paletteColor,
                    _PaletteMidColor.rgb,
                    EvaluatePaletteTransition(normalizedBrightness, 0.52));
                paletteColor = lerp(
                    paletteColor,
                    _BaseColor.rgb,
                    EvaluatePaletteTransition(normalizedBrightness, 0.76));
                return paletteColor;
            }

            half3 ApplyLimitedSpatialLightTint(
                half3 paletteColor,
                half3 spatialLighting,
                half totalBrightness)
            {
                half spatialBrightness = max(Luminance(spatialLighting), 0.0);
                if (spatialBrightness <= 0.0001 ||
                    _LocalLightTintInfluence <= 0.0001)
                {
                    return paletteColor;
                }

                // Local light hue may identify a lamp, but it must not replace
                // the authored palette or reveal the underlying 3D curvature.
                half highestChannel = max(
                    max(spatialLighting.r, spatialLighting.g),
                    spatialLighting.b);
                half3 localHue = spatialLighting / max(highestChannel, 0.0001);
                half3 tintedPalette = paletteColor * localHue;
                half paletteLuminance = max(Luminance(paletteColor), 0.0001);
                half tintedLuminance = max(Luminance(tintedPalette), 0.0001);
                tintedPalette *= paletteLuminance / tintedLuminance;

                half spatialShare = saturate(
                    spatialBrightness / max(totalBrightness, 0.0001));
                return saturate(lerp(
                    paletteColor,
                    tintedPalette,
                    _LocalLightTintInfluence * spatialShare));
            }

            half4 Frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float3 lightingPositionWS = input.positionWS +
                    _CharacterLightingPositionOffsetWS.xyz;
                CharacterLightingSample lighting =
                    EvaluateSpatialFlatCharacterLighting(
                    lightingPositionWS,
                    input.positionCS);
                half spatialBrightness = max(
                    Luminance(lighting.spatialLighting),
                    0.0);
                half totalBrightness = max(
                    lighting.environmentBrightness + spatialBrightness,
                    0.0);
                half normalizedBrightness = saturate(
                    totalBrightness / max(_PaletteReferenceBrightness, 0.0001));
                half3 paletteColor = EvaluateCharacterPalette(
                    normalizedBrightness);
                paletteColor = ApplyLimitedSpatialLightTint(
                    paletteColor,
                    lighting.spatialLighting,
                    totalBrightness);
                return half4(paletteColor, _BaseColor.a);
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
