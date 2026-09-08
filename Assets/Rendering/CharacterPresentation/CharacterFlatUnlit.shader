Shader "FantasySurvival/Character/Spatial Flat Lit"
{
    Properties
    {
        [MainTexture] _BaseMap("Base Map", 2D) = "white" {}
        [MainColor] _BaseColor("Base Color", Color) = (0.9686275, 0.8431373, 0.7294118, 1)
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull Mode", Float) = 2
        _BaseMapPixelGrid("Base Map Pixel Grid (0 = Native)", Range(0, 256)) = 0
        _EnvironmentExposure("Environment Exposure (Clear Noon Reference)", Range(0.5, 3)) = 1.66
        _AmbientLightStrength("Ambient Light Strength", Range(0, 2)) = 1
        _MainLightStrength("Main Light Strength", Range(0, 2)) = 0.45
        _AdditionalLightStrength("Additional Light Strength", Range(0, 2)) = 0.18
        _SteppedLocalLightStrength("Stepped Local Light Strength", Range(0, 2)) = 0.55
        [IntRange] _PaletteCount("Albedo Palette Colors (0 = Disabled)", Range(0, 8)) = 0
        _Palette0("Albedo Palette 0", Color) = (0, 0, 0, 1)
        _Palette1("Albedo Palette 1", Color) = (1, 1, 1, 1)
        _Palette2("Albedo Palette 2", Color) = (1, 1, 1, 1)
        _Palette3("Albedo Palette 3", Color) = (1, 1, 1, 1)
        _Palette4("Albedo Palette 4", Color) = (1, 1, 1, 1)
        _Palette5("Albedo Palette 5", Color) = (1, 1, 1, 1)
        _Palette6("Albedo Palette 6", Color) = (1, 1, 1, 1)
        _Palette7("Albedo Palette 7", Color) = (1, 1, 1, 1)
        [IntRange] _LightingBandCount("Lighting Bands (0 = Disabled, 2-16)", Range(0, 16)) = 0
        _LightingBandMaximum("Lighting Band Range (Above = Unchanged)", Float) = 1
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
        }

        HLSLINCLUDE
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/CommonMaterial.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half _BaseMapPixelGrid;
                half _EnvironmentExposure;
                half _AmbientLightStrength;
                half _MainLightStrength;
                half _AdditionalLightStrength;
                half _SteppedLocalLightStrength;
                half _PaletteCount;
                half4 _Palette0;
                half4 _Palette1;
                half4 _Palette2;
                half4 _Palette3;
                half4 _Palette4;
                half4 _Palette5;
                half4 _Palette6;
                half4 _Palette7;
                half _LightingBandCount;
                float _LightingBandMaximum;
            CBUFFER_END

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);
            SamplerState sampler_point_repeat;

            // Pixel snapping moves only the presentation hierarchy. This offset
            // restores the unsnapped world position used by spatial lighting so
            // camera movement cannot drag the character through light boundaries.
            float4 _CharacterLightingPositionOffsetWS;

            // One presentation subject supplies these values through its MPB.
            // Unassigned renderers default to the original native surface path.
            float _CharacterCellSurface;
            float _CharacterCellSize;
            float4 _CharacterPixelGridAnchorWS;
            float _CharacterOutlineGroup;
            float _CharacterCellSubjectId;
            float _CharacterAdaptiveToneSource;
            float _CharacterHairLightingAnalysis;
            float _CharacterToneCaptureLighting;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
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

            half3 EvaluateSpatialFlatCharacterLighting(
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

                // Sky ambient and the single sun/moon key light cover the whole
                // flat character. Preserve their luminance, not their full RGB
                // chroma, so a blue night profile changes visibility without
                // replacing the neutral base color. Spatial local lights below
                // keep their authored color where they actually overlap.
                // The authored base color is the clear-noon reference color.
                // The flat lighting estimator intentionally omits N.L and BRDF,
                // so calibrate its neutral environment luminance once instead of
                // replacing the authored color with a palette or an overlay.
                half environmentBrightness =
                    Luminance(environmentLighting) * _EnvironmentExposure;
                half3 lighting = environmentBrightness.xxx;

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
                            lighting += EvaluateSurfaceNeutralRealtimeLight(
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
                        lighting += EvaluateSurfaceNeutralRealtimeLight(
                            additionalLight,
                            _AdditionalLightStrength);
                    LIGHT_LOOP_END
                #endif

                // Spatial attenuation is evaluated per visible character pixel,
                // while normal influence stays at zero. Light boundaries can
                // cross the silhouette without revealing the mesh curvature.
                lighting += EvaluateSteppedLocalLights(
                    positionWS,
                    flatAmbientDirection,
                    0.0) * _SteppedLocalLightStrength;
                return lighting;
            }

            float3 PaletteComparisonColor(half3 color)
            {
                // Material Color properties and sampled albedo share the active
                // working space. Compare both in sRGB so dark iris colors do
                // not collapse merely because their linear values are close.
                #if defined(UNITY_COLORSPACE_GAMMA)
                    return color;
                #else
                    return LinearToSRGB(color);
                #endif
            }

            half3 SelectAlbedoPalette(half3 albedo)
            {
                int paletteCount = clamp((int)round(_PaletteCount), 0, 8);
                if (paletteCount == 0)
                    return albedo;

                half3 palette[8] = {
                    _Palette0.rgb, _Palette1.rgb, _Palette2.rgb, _Palette3.rgb,
                    _Palette4.rgb, _Palette5.rgb, _Palette6.rgb, _Palette7.rgb
                };
                float3 comparisonColor = PaletteComparisonColor(albedo);
                float nearestDistance = 1e30;
                half3 selected = albedo;
                [unroll]
                for (int index = 0; index < 8; index++)
                {
                    if (index < paletteCount)
                    {
                        float3 difference = comparisonColor -
                            PaletteComparisonColor(palette[index]);
                        float distanceSquared = dot(difference, difference);
                        if (distanceSquared < nearestDistance)
                        {
                            nearestDistance = distanceSquared;
                            selected = palette[index];
                        }
                    }
                }
                // Select one authored source color; never average the palette.
                // Its alpha is not a replacement for source texture coverage.
                return selected;
            }

            half3 ApplyLightingBands(half3 lighting)
            {
                int bandCount = clamp((int)round(_LightingBandCount), 0, 16);
                if (bandCount < 2 || _LightingBandMaximum <= 0.0)
                    return lighting;

                float brightness = Luminance(lighting);
                if (brightness <= 0.0 || brightness >= _LightingBandMaximum)
                    return lighting;

                // N equally spaced levels include zero and the range endpoint.
                // Beyond that endpoint retain the original HDR light, rather
                // than cap it. A shared scalar preserves colored local lights.
                float intervals = bandCount - 1;
                float bandBrightness = round(
                    brightness / _LightingBandMaximum * intervals) *
                    (_LightingBandMaximum / intervals);
                return lighting * (bandBrightness / brightness);
            }

            half4 EvaluateCharacterColor(Varyings input)
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float3 lightingPositionWS = input.positionWS +
                    _CharacterLightingPositionOffsetWS.xyz;
                half4 baseSample = half4(1, 1, 1, 1);
                if (_BaseMapPixelGrid >= 1.0h)
                {
                    float2 pixelUv =
                        (floor(input.uv * _BaseMapPixelGrid) + 0.5) /
                        _BaseMapPixelGrid;
                    baseSample = SAMPLE_TEXTURE2D_LOD(
                        _BaseMap,
                        sampler_point_repeat,
                        pixelUv,
                        0.0);
                }
                else
                {
                    baseSample = SAMPLE_TEXTURE2D(
                        _BaseMap,
                        sampler_BaseMap,
                        input.uv);
                }
                half4 evaluatedColor = baseSample * _BaseColor;
                if (_CharacterAdaptiveToneSource > 0.5)
                {
                    // Analysis needs the continuous matte source that was used
                    // in the offline experiment. This opt-in does not change
                    // classic subjects or their authored palettes/light bands.
                    InputData d = (InputData)0;
                    d.positionWS = lightingPositionWS;
                    d.positionCS = input.positionCS;
                    d.normalWS = NormalizeNormalPerPixel(input.normalWS);
                    d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(lightingPositionWS);
                    d.shadowCoord = TransformWorldToShadowCoord(lightingPositionWS);
                    d.bakedGI = SampleSH(d.normalWS);
                    d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                    d.shadowMask = half4(1, 1, 1, 1);
                    SurfaceData s = (SurfaceData)0;
                    s.albedo = baseSample.rgb * _BaseColor.rgb;
                    s.alpha = baseSample.a * _BaseColor.a;
                    s.normalTS = half3(0, 0, 1);
                    s.occlusion = 1;
                    s.metallic = 0;
                    s.smoothness = 0;
                    evaluatedColor = UniversalFragmentPBR(d, s);
                    evaluatedColor.rgb += s.albedo * EvaluateSteppedLocalLights(
                        lightingPositionWS, d.normalWS, 0.0) * _SteppedLocalLightStrength;
                }
                else
                {
                    half3 lighting = EvaluateSpatialFlatCharacterLighting(
                        lightingPositionWS, input.positionCS);
                    half3 albedo = SelectAlbedoPalette(baseSample.rgb * _BaseColor.rgb);
                    evaluatedColor = half4(albedo * ApplyLightingBands(lighting), baseSample.a * _BaseColor.a);
                }
                return evaluatedColor;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                // A cell-surface subject must not leave rounded native color or
                // depth behind; empty cells are supplied by the actual scene.
                clip(0.5 - _CharacterCellSurface);
                return EvaluateCharacterColor(input);
            }

            struct CellSourceOutput
            {
                half4 colorDepth : SV_Target0;
                half4 subjectGroupSize : SV_Target1;
            };

            // Analysis-only diffuse irradiance, before albedo and specular.
            // Follow the installed URP light loops (including Forward+, cookies,
            // shadow attenuation and SH). The visible PBR source is unchanged.
            half3 DiffuseIncidentLight(Light light, half3 normalWS)
            {
                return light.color * (light.distanceAttenuation * light.shadowAttenuation) *
                    saturate(dot(normalWS, light.direction));
            }

            float IncidentLuminance(Varyings input)
            {
                InputData inputData = (InputData)0;
                inputData.positionWS = input.positionWS + _CharacterLightingPositionOffsetWS.xyz;
                inputData.positionCS = input.positionCS;
                inputData.normalWS = NormalizeNormalPerPixel(input.normalWS);
                inputData.viewDirectionWS = GetWorldSpaceNormalizeViewDir(inputData.positionWS);
                inputData.shadowCoord = TransformWorldToShadowCoord(inputData.positionWS);
                inputData.bakedGI = SampleSH(inputData.normalWS);
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                inputData.shadowMask = half4(1, 1, 1, 1);
                SurfaceData surface = (SurfaceData)0;
                surface.occlusion = 1;
                half4 shadowMask = CalculateShadowMask(inputData);
                AmbientOcclusionFactor ao = CreateAmbientOcclusionFactor(inputData, surface);
                uint meshLayers = GetMeshRenderingLayer();
                Light mainLight = GetMainLight(inputData, shadowMask, ao);
                MixRealtimeAndBakedGI(mainLight, inputData.normalWS, inputData.bakedGI);
                half3 irradiance = inputData.bakedGI * ao.indirectAmbientOcclusion;
                #ifdef _LIGHT_LAYERS
                if (IsMatchingLightLayer(mainLight.layerMask, meshLayers))
                #endif
                    irradiance += DiffuseIncidentLight(mainLight, inputData.normalWS);
                #if defined(_ADDITIONAL_LIGHTS)
                uint pixelLightCount = GetAdditionalLightsCount();
                #if USE_CLUSTER_LIGHT_LOOP
                [loop] for (uint lightIndex = 0; lightIndex < min(URP_FP_DIRECTIONAL_LIGHTS_COUNT, MAX_VISIBLE_LIGHTS); lightIndex++)
                {
                    CLUSTER_LIGHT_LOOP_SUBTRACTIVE_LIGHT_CHECK
                    Light light = GetAdditionalLight(lightIndex, inputData, shadowMask, ao);
                    #ifdef _LIGHT_LAYERS
                    if (IsMatchingLightLayer(light.layerMask, meshLayers))
                    #endif
                        irradiance += DiffuseIncidentLight(light, inputData.normalWS);
                }
                #endif
                LIGHT_LOOP_BEGIN(pixelLightCount)
                    Light light = GetAdditionalLight(lightIndex, inputData, shadowMask, ao);
                    #ifdef _LIGHT_LAYERS
                    if (IsMatchingLightLayer(light.layerMask, meshLayers))
                    #endif
                        irradiance += DiffuseIncidentLight(light, inputData.normalWS);
                LIGHT_LOOP_END
                #endif
                irradiance += EvaluateSteppedLocalLights(inputData.positionWS,
                    inputData.normalWS, 0.0) * _SteppedLocalLightStrength;
                return max(Luminance(irradiance), 0.0);
            }

            struct ToneNativeOutput
            {
                half4 colorDepth : SV_Target0;
                half4 subjectGroupSize : SV_Target1;
                half4 incidentLighting : SV_Target2;
            };

            ToneNativeOutput FragToneNativeSource(Varyings input)
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                clip(_CharacterAdaptiveToneSource - 0.5);
                clip(_CharacterCellSurface - 0.5);
                half4 color = EvaluateCharacterColor(input);
                float eyeDepth = unity_OrthoParams.w > 0.5 ?
                    LinearDepthToEyeDepth(input.positionCS.z) :
                    LinearEyeDepth(input.positionCS.z, _ZBufferParams);
                uint subjectId = (uint)clamp(round(_CharacterCellSubjectId), 1.0, 65535.0);
                ToneNativeOutput output;
                output.colorDepth = half4(color.rgb, max(eyeDepth, 0.0001));
                output.subjectGroupSize = half4((subjectId & 255u) / 255.0,
                    clamp(round(_CharacterOutlineGroup), 0.0, 255.0) / 255.0,
                    clamp(round(_CharacterCellSize), 1.0, 8.0) / 255.0,
                    (subjectId >> 8) / 255.0);
                output.incidentLighting = 0;
                if (_CharacterToneCaptureLighting > 0.5 ||
                    (_CharacterHairLightingAnalysis > 0.5 && round(_CharacterOutlineGroup) == 3.0))
                    output.incidentLighting = half4(IncidentLuminance(input), 0, 0, 1);
                return output;
            }

            CellSourceOutput FragCellSource(Varyings input)
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                clip(_CharacterCellSurface - 0.5);
                clip(_CharacterCellSubjectId - 0.5);

                float cellSize = clamp(round(_CharacterCellSize), 1.0, 8.0);
                float2 fragmentUv = GetNormalizedScreenSpaceUV(input.positionCS.xy);
                float2 anchorUv = ComputeNormalizedDeviceCoordinates(
                    _CharacterPixelGridAnchorWS.xyz, UNITY_MATRIX_VP);
                float2 pixelOffset = floor(fragmentUv * _ScaledScreenParams.xy) -
                    floor(anchorUv * _ScaledScreenParams.xy);
                float2 remainder = pixelOffset - floor(pixelOffset / cellSize) * cellSize;
                clip(0.5 - max(remainder.x, remainder.y));

                // Only covered cell centers participate in the isolated native
                // self-depth test. The source is opaque, just like Forward.
                half4 color = EvaluateCharacterColor(input);
                float eyeDepth = unity_OrthoParams.w > 0.5 ?
                    LinearDepthToEyeDepth(input.positionCS.z) :
                    LinearEyeDepth(input.positionCS.z, _ZBufferParams);
                uint subjectId = (uint)clamp(round(_CharacterCellSubjectId), 1.0, 65535.0);
                float group = clamp(round(_CharacterOutlineGroup), 0.0, 255.0);

                CellSourceOutput output;
                output.colorDepth = half4(color.rgb, max(eyeDepth, 0.0001));
                output.subjectGroupSize = half4(
                    (subjectId & 255u) / 255.0, group / 255.0,
                    cellSize / 255.0, (subjectId >> 8) / 255.0);
                return output;
            }
        ENDHLSL

        Pass
        {
            Name "CharacterSpatialFlatLit"
            Tags { "LightMode" = "UniversalForward" }

            Cull [_Cull]
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
            ENDHLSL
        }

        Pass
        {
            Name "CharacterToneNativeSource"
            Tags { "LightMode" = "CharacterToneNativeSource" }
            Cull [_Cull]
            ZWrite On
            ZTest LEqual
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment FragToneNativeSource
            #pragma editor_sync_compilation
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }

            ColorMask 0
            Cull [_Cull]
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing

            struct DepthAttributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct DepthVaryings
            {
                float4 positionCS : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            DepthVaryings DepthVert(DepthAttributes input)
            {
                DepthVaryings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return output;
            }

            half4 DepthFrag(DepthVaryings input) : SV_Target
            {
                clip(0.5 - _CharacterCellSurface);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "CharacterPixelCellSource"
            Tags { "LightMode" = "CharacterPixelCellSource" }

            Cull [_Cull]
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment FragCellSource
            #pragma editor_sync_compilation
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            ENDHLSL
        }
    }

    FallBack Off
}
