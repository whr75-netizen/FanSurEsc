Shader "FantasySurvival/World/Native Palette Surface 16"
{
    Properties
    {
        _PositionMap("Native local XYZ and validity", 2D) = "black" {}
        _NormalMap("Native local normal and validity", 2D) = "black" {}
        _MaterialMap("Material, intrinsic pattern, edge role, coverage", 2D) = "black" {}
        _PaletteMap("Four columns, ten material rows", 2D) = "white" {}
        [MainColor] _BaseColor("Tint and opacity", Color) = (1,1,1,1)
        _AmbientLightStrength("Existing SH strength", Float) = 1
        _MainLightStrength("Existing main light strength", Float) = 1
        _AdditionalLightStrength("Existing additional light strength", Float) = 1
        _SteppedLocalLightStrength("Existing stepped local light strength", Float) = 0.55
        _LightingBandMaximum("Irradiance at the last palette band", Float) = 1
        [HideInInspector] _MaterialBandCounts0("Material 1 to 4 band counts", Vector) = (4,4,3,4)
        [HideInInspector] _MaterialBandCounts1("Material 5 to 8 band counts", Vector) = (4,4,4,4)
        [HideInInspector] _MaterialBandCounts2("Material 9 to 10 band counts", Vector) = (4,4,0,0)
        [HideInInspector] _NativeGridEnabled("Native grid translation", Float) = 1
        [HideInInspector] _NativeGridAnchorOS("Native grid anchor", Vector) = (0,0,0,0)
        [HideInInspector] _NativeGridTexelUOS("One native texel right", Vector) = (0,0,0,0)
        [HideInInspector] _NativeGridTexelVOS("One native texel up", Vector) = (0,0,0,0)
        [Toggle] _RetainPatternContrast("Material pattern independent of lighting band", Float) = 0
        [Toggle] _ReadableNight("Readable material and shadow palette", Float) = 0
        _NativeEdgeSRGBScale("Material-coloured boundary sRGB scale", Range(0,1)) = 0.8
        [HideInInspector] _ReadableFixtureIrradiance("Readable palette fixture", Vector) = (0.03,0.045,0.085,0)
        [HideInInspector] _ZWrite("Depth write", Float) = 1
        [HideInInspector] _SrcBlend("Source blend", Float) = 1
        [HideInInspector] _DstBlend("Destination blend", Float) = 0
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull", Float) = 0
        [Enum(Lit,0,MaterialOnly,1,Normals,2,Irradiance,3,MainShadow,4,ReferenceFixture,5,ReadableFixture,6,NativeAdditiveLight,7)] _DiagnosticMode("Diagnostic", Float) = 0
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" "DisableBatching"="True" }
        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
        #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"
        #include "Assets/Shaders/World/NativeShade17.hlsl"
        #include "Assets/Shaders/World/NativeReadable18.hlsl"
        #include "Assets/Shaders/World/NativeLight31.hlsl"

        TEXTURE2D(_PositionMap);
        TEXTURE2D(_NormalMap);
        TEXTURE2D(_MaterialMap);
        TEXTURE2D(_PaletteMap);
        CBUFFER_START(UnityPerMaterial)
            float4 _PositionMap_TexelSize;
            float4 _PaletteMap_TexelSize;
            float4 _BaseColor;
            float4 _MaterialBandCounts0;
            float4 _MaterialBandCounts1;
            float4 _MaterialBandCounts2;
            float4 _NativeGridAnchorOS;
            float4 _NativeGridTexelUOS;
            float4 _NativeGridTexelVOS;
            float4 _NativeRenderOffsetWS;
            float _RetainPatternContrast;
            float _ReadableNight;
            float _NativeEdgeSRGBScale;
            float4 _ReadableFixtureIrradiance;
            float _AmbientLightStrength;
            float _MainLightStrength;
            float _AdditionalLightStrength;
            float _SteppedLocalLightStrength;
            float _LightingBandMaximum;
            float _NativeGridEnabled;
            float _ZWrite;
            float _SrcBlend;
            float _DstBlend;
            float _Cull;
            float _DiagnosticMode;
        CBUFFER_END

        struct Attributes
        {
            float3 positionOS : POSITION;
            float2 uv : TEXCOORD0;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };
        struct Varyings
        {
            float4 positionCS : SV_POSITION;
            float2 uv : TEXCOORD0;
            UNITY_VERTEX_INPUT_INSTANCE_ID
            UNITY_VERTEX_OUTPUT_STEREO
        };
        struct CachedSurface
        {
            float3 positionWS;
            float3 normalWS;
            float depth;
            uint material;
            uint pattern;
            uint edge;
            half roughness;
        };
        struct SurfaceOutput
        {
            float4 color : SV_Target;
            float depth : SV_Depth;
        };

        float2 RasterPosition(float4 positionCS)
        {
            float2 ndc = positionCS.xy / positionCS.w;
            ndc.y *= _ProjectionParams.x;
            return (ndc * 0.5 + 0.5) * _ScaledScreenParams.xy;
        }

        float4 SnapNativeGrid(float4 positionCS)
        {
            if (_NativeGridEnabled < 0.5 || unity_OrthoParams.w < 0.5)
                return positionCS;
            float3 anchorWS = TransformObjectToWorld(_NativeGridAnchorOS.xyz);
            float3 texelUWS = mul((float3x3)unity_ObjectToWorld, _NativeGridTexelUOS.xyz);
            float3 texelVWS = mul((float3x3)unity_ObjectToWorld, _NativeGridTexelVOS.xyz);
            float2 texelUVS = mul((float3x3)UNITY_MATRIX_V, texelUWS).xy;
            float2 texelVVS = mul((float3x3)UNITY_MATRIX_V, texelVWS).xy;
            if (texelUVS.x <= 0.000001 || texelVVS.y <= 0.000001 ||
                abs(texelUVS.y) > texelUVS.x * 0.0001 ||
                abs(texelVVS.x) > texelVVS.y * 0.0001 ||
                abs(texelUVS.x - texelVVS.y) > texelUVS.x * 0.0001)
                return positionCS;
            float4 anchorCS = TransformWorldToHClip(anchorWS);
            float2 anchorRaster = RasterPosition(anchorCS);
            float2 uRaster = RasterPosition(TransformWorldToHClip(anchorWS + texelUWS)) - anchorRaster;
            float2 vRaster = RasterPosition(TransformWorldToHClip(anchorWS + texelVWS)) - anchorRaster;
            float integerScale = round(abs(uRaster.x));
            if (integerScale < 1.0 || abs(abs(uRaster.x) - integerScale) > 0.01 ||
                abs(abs(vRaster.y) - integerScale) > 0.01 ||
                abs(uRaster.y) > 0.01 || abs(vRaster.x) > 0.01)
                return positionCS;
            // One rigid visual translation shares the host world/camera phase.
            // Material, surface positions, light queries and depth are unchanged.
            float2 sourceWorld = mul((float3x3)UNITY_MATRIX_V, anchorWS).xy /
                float2(texelUVS.x, texelVVS.y);
            float2 sourceOffset = round(sourceWorld) - sourceWorld;
            float2 worldZeroRaster = RasterPosition(TransformWorldToHClip(float3(0,0,0)));
            float2 cameraOffset = round(worldZeroRaster / integerScale) * integerScale - worldZeroRaster;
            float2 rasterOffset = sourceOffset * float2(uRaster.x, vRaster.y) + cameraOffset;
            positionCS.xy += rasterOffset * (2.0 / _ScaledScreenParams.xy) *
                float2(1.0, _ProjectionParams.x) * positionCS.w;
            return positionCS;
        }

        Varyings Vert(Attributes input)
        {
            Varyings output = (Varyings)0;
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_TRANSFER_INSTANCE_ID(input, output);
            UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
            output.positionCS = _NativeRenderOffsetWS.w > 0.5 ?
                TransformWorldToHClip(TransformObjectToWorld(input.positionOS) + _NativeRenderOffsetWS.xyz) :
                SnapNativeGrid(TransformObjectToHClip(input.positionOS));
            output.uv = input.uv;
            return output;
        }

        CachedSurface ReadSurface(float2 uv)
        {
            // Reject out-of-domain fragments rather than clamp another object's
            // positions or colors into coverage. All maps share one texel index.
            clip(min(min(uv.x, uv.y), min(1.0 - uv.x, 1.0 - uv.y)));
            float2 size = _PositionMap_TexelSize.zw;
            float2 index = min(floor(uv * size), size - 1.0);
            float2 centerUV = (index + 0.5) / size;
            float4 position = SAMPLE_TEXTURE2D_LOD(_PositionMap, sampler_PointClamp, centerUV, 0);
            float4 normal = SAMPLE_TEXTURE2D_LOD(_NormalMap, sampler_PointClamp, centerUV, 0);
            float4 data = SAMPLE_TEXTURE2D_LOD(_MaterialMap, sampler_PointClamp, centerUV, 0);
            clip(min(position.a, min(normal.a, data.a)) - 0.5);
            float4 bytes = round(data * 255.0);
            clip(min(bytes.r - 1.0, 10.0 - bytes.r));
            CachedSurface result;
            result.positionWS = TransformObjectToWorld(position.xyz) + _NativeRenderOffsetWS.xyz;
            result.normalWS = TransformObjectToWorldNormal(normal.xyz);
            float4 surfaceCS = TransformWorldToHClip(result.positionWS);
            result.depth = surfaceCS.z / surfaceCS.w;
            #if defined(SHADER_API_GLCORE) || defined(SHADER_API_GLES) || defined(SHADER_API_GLES3)
                result.depth = result.depth * 0.5 + 0.5;
            #endif
            result.material = (uint)bytes.r;
            result.pattern = (uint)bytes.g;
            result.edge = (uint)bytes.b;
            // Extended palettes opt into packed validity + perceptual roughness.
            // Legacy four-column normal alpha remains validity only.
            result.roughness = _PaletteMap_TexelSize.z > 4.5 ? clamp(normal.a * 2.0 - 1.0, 0.2, 0.9) : 0.9;
            return result;
        }

        half3 PaletteColor(uint material, float column)
        {
            // PNG row zero is material 1; Unity UV zero is the bottom row.
            float width = max(_PaletteMap_TexelSize.z, 4.0);
            float2 uv = float2((clamp(column, 0.0, width - 1.0) + 0.5) / width,
                               1.0 - (material - 0.5) / 10.0);
            return SAMPLE_TEXTURE2D_LOD(_PaletteMap, sampler_PointClamp, uv, 0).rgb;
        }

        float BandCount(uint material)
        {
            uint index = material - 1;
            float count = index < 4 ? _MaterialBandCounts0[index] :
                (index < 8 ? _MaterialBandCounts1[index - 4] : _MaterialBandCounts2[index - 8]);
            return clamp(round(count), 3.0, 4.0);
        }

        half3 DiffuseIncidentLight(Light light, half3 normalWS)
        {
            return light.color * (light.distanceAttenuation * light.shadowAttenuation) *
                saturate(dot(normalWS, light.direction));
        }

        half3 DirectShadowLoss(Light light, half3 normalWS)
        {
            // Reuse this Light's cookie-adjusted color, distance and layer test.
            return light.color * light.distanceAttenuation *
                saturate(dot(normalWS, light.direction)) * (1.0 - saturate(light.shadowAttenuation));
        }

        half3 DirectSurfaceSpecular(Light light, CachedSurface surface)
        {
            if (_PaletteMap_TexelSize.z < 4.5 || surface.edge == 3u) return 0.0;
            BRDFData brdf;
            half alpha = 1.0;
            half3 albedo = PaletteColor(surface.material, (float)surface.pattern);
            InitializeBRDFData(albedo, surface.material == 3u ? 1.0 : 0.0,
                half3(0.04,0.04,0.04), 1.0 - surface.roughness, alpha, brdf);
            // URP's orthographic-aware view direction avoids false panel-wide sheen.
            half3 view = GetWorldSpaceNormalizeViewDir(surface.positionWS);
            return brdf.specular * DirectBRDFSpecular(brdf, surface.normalWS, light.direction, view) *
                DiffuseIncidentLight(light, surface.normalWS);
        }

        half3 SteppedSurfaceSpecular(half3 energy, uint material)
        {
            // Cap the sum, not each source; preserve the actual incident RGB ratios.
            float peak = max(max(energy.r, energy.g), energy.b);
            float cap = material == 3u ? 0.06 : 0.024;
            if (peak < cap / 12.0) return 0.0;
            float step = ceil(saturate(peak / cap) * 3.0) / 3.0;
            return energy / max(peak, 0.000001) * (step * cap);
        }

        half3 IncidentLight(CachedSurface surface, float4 screenPosition,
            out half mainShadow, out half3 nativeAdditiveLight, out half3 directSpecular, out half3 shadowLoss)
        {
            InputData inputData = (InputData)0;
            inputData.positionWS = surface.positionWS;
            inputData.normalWS = surface.normalWS;
            inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(screenPosition);
            inputData.shadowCoord = TransformWorldToShadowCoord(surface.positionWS);
            #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                inputData.shadowCoord = ComputeScreenPos(TransformWorldToHClip(surface.positionWS));
            #endif
            half4 shadowMask = half4(1,1,1,1);
            Light mainLight = GetMainLight(inputData.shadowCoord, surface.positionWS, shadowMask);
            mainShadow = mainLight.shadowAttenuation;
            uint meshLayers = GetMeshRenderingLayer();
            half3 irradiance = max(SampleSH(surface.normalWS), 0.0) * max(_AmbientLightStrength, 0.0);
            directSpecular = 0.0;
            shadowLoss = 0.0;
            #ifdef _LIGHT_LAYERS
            if (IsMatchingLightLayer(mainLight.layerMask, meshLayers))
            #endif
            {
                irradiance += DiffuseIncidentLight(mainLight, surface.normalWS) * max(_MainLightStrength, 0.0);
                shadowLoss += DirectShadowLoss(mainLight, surface.normalWS) * max(_MainLightStrength, 0.0);
                directSpecular += DirectSurfaceSpecular(mainLight, surface) * max(_MainLightStrength, 0.0);
            }
            #if defined(_ADDITIONAL_LIGHTS) || USE_CLUSTER_LIGHT_LOOP
                #if USE_CLUSTER_LIGHT_LOOP
                [loop] for (uint lightIndex = 0; lightIndex < min(URP_FP_DIRECTIONAL_LIGHTS_COUNT, MAX_VISIBLE_LIGHTS); lightIndex++)
                {
                    CLUSTER_LIGHT_LOOP_SUBTRACTIVE_LIGHT_CHECK
                    Light light = GetAdditionalLight(lightIndex, surface.positionWS, shadowMask);
                    #ifdef _LIGHT_LAYERS
                    if (IsMatchingLightLayer(light.layerMask, meshLayers))
                    #endif
                    {
                        irradiance += DiffuseIncidentLight(light, surface.normalWS) * max(_AdditionalLightStrength, 0.0);
                        shadowLoss += DirectShadowLoss(light, surface.normalWS) * max(_AdditionalLightStrength, 0.0);
                        directSpecular += DirectSurfaceSpecular(light, surface) * max(_AdditionalLightStrength, 0.0);
                    }
                }
                #endif
                uint pixelLightCount = GetAdditionalLightsCount();
                LIGHT_LOOP_BEGIN(pixelLightCount)
                    Light light = GetAdditionalLight(lightIndex, surface.positionWS, shadowMask);
                    #ifdef _LIGHT_LAYERS
                    if (IsMatchingLightLayer(light.layerMask, meshLayers))
                    #endif
                    {
                        irradiance += DiffuseIncidentLight(light, surface.normalWS) * max(_AdditionalLightStrength, 0.0);
                        shadowLoss += DirectShadowLoss(light, surface.normalWS) * max(_AdditionalLightStrength, 0.0);
                        directSpecular += DirectSurfaceSpecular(light, surface) * max(_AdditionalLightStrength, 0.0);
                    }
                LIGHT_LOOP_END
            #endif
            half3 regularLocal = EvaluateSteppedLocalLights(
                surface.positionWS, surface.normalWS, 1.0, nativeAdditiveLight);
            float localStrength = max(_SteppedLocalLightStrength, 0.0);
            irradiance += regularLocal * localStrength;
            nativeAdditiveLight *= localStrength;
            return max(irradiance, 0.0);
        }

        half3 MaterialBoundaryColor(half3 surfaceColor)
        {
            // The boundary stays in the lit material's hue, with a single
            // display-space darkening. No coverage, rank or pixel change.
            return SRGBToLinear(LinearToSRGB(max(surfaceColor, 0.0)) *
                saturate(_NativeEdgeSRGBScale));
        }

        half3 Shade(CachedSurface surface, half3 irradiance, half3 nativeAdditiveLight, half3 directSpecular, half3 shadowLoss)
        {
            if (_ReadableNight > 0.5 && (_DiagnosticMode < 4.5 || _DiagnosticMode >= 5.5))
            {
                // Opt-in authored material clusters use the same native rank
                // channel as wood. Existing flag-off furniture stays unchanged.
                float column = surface.material == 1u || _RetainPatternContrast > 0.5 ?
                    (float)surface.pattern : 2.0;
                column = min(column, _PaletteMap_TexelSize.z > 4.5 ? _PaletteMap_TexelSize.z - 1.0 : BandCount(surface.material) - 1.0);
                if (surface.edge == 3u) column = Native17CreaseColumn;
                // Both fields pass through the same actual material reflectance.
                // Never paint raw light RGB over a finished surface or fold the
                // already quantized moving source back into the base ramp.
                half3 finalColor = Native31Readable(
                    PaletteColor(surface.material, column),
                    (float3)irradiance, (float3)shadowLoss, (float3)nativeAdditiveLight);
                if (_PaletteMap_TexelSize.z > 4.5) finalColor += directSpecular;
                return surface.edge == 1u || surface.edge == 2u ?
                    MaterialBoundaryColor(finalColor) : finalColor;
            }
            irradiance += nativeAdditiveLight;
            float luminance = max(dot((float3)irradiance, Native17Luminance), 0.0);
            // No fabricated minimum brightness or fixed midtone when all of
            // the existing engine/environment light contributions are zero.
            if (luminance <= 0.000001)
                return half3(0,0,0);
            float bands = BandCount(surface.material);
            float lightingBand = Native17LightingBand(luminance);
            float column = Native17PaletteColumn(surface.material, surface.pattern, lightingBand, bands);
            // A floor's intrinsic grain must not collapse into one colour when
            // the lowest lighting band clamps all rank offsets to column zero.
            // Keep its albedo rank and apply one of three discrete light levels.
            float patternLight = 1.0;
            if (_PaletteMap_TexelSize.z > 4.5)
            {
                column = (float)surface.pattern;
                patternLight = (lightingBand + 1.0) / 3.0;
            }
            if (_PaletteMap_TexelSize.z < 4.5 && _RetainPatternContrast > 0.5 && surface.material == 1u)
            {
                column = min((float)surface.pattern, bands - 1.0);
                patternLight = (lightingBand + 1.0) / 3.0;
            }
            // Preserve incident RGB ratios; quantize the scalar/ramp only.
            half3 tint = Material27LightTint(irradiance);
            half3 color = PaletteColor(surface.material, column);
            // Creases retain their existing darker material ramp entry.
            if (surface.edge == 3u)
                color = PaletteColor(surface.material, Native17CreaseColumn);
            half3 finalColor = Material27Diffuse(color, tint * patternLight);
            if (_PaletteMap_TexelSize.z > 4.5) finalColor += directSpecular;
            return surface.edge == 1u || surface.edge == 2u ?
                MaterialBoundaryColor(finalColor) : finalColor;
        }

        SurfaceOutput Frag(Varyings input)
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            CachedSurface surface = ReadSurface(input.uv);
            if (_DiagnosticMode >= 8.5 && _DiagnosticMode < 9.5)
            {
                SurfaceOutput positionProbe;
                positionProbe.color = float4(surface.positionWS, 1);
                positionProbe.depth = surface.depth;
                return positionProbe;
            }
            half mainShadow;
            half3 irradiance;
            half3 nativeAdditiveLight = 0.0;
            half3 directSpecular = 0.0;
            half3 shadowLoss = 0.0;
            if (_DiagnosticMode >= 5.5 && _DiagnosticMode < 6.5)
            {
                irradiance = max(_ReadableFixtureIrradiance.rgb, 0.0);
                mainShadow = 1.0;
            }
            else if (_DiagnosticMode >= 4.5 && _DiagnosticMode < 5.5)
            {
                // The fixture is defined in the same local metre basis as the
                // native cache; building yaw rotates both normal and light.
                float3 referenceLightWS = normalize(TransformObjectToWorldDir(Native17ReferenceLightOS));
                irradiance = saturate(dot(surface.normalWS, referenceLightWS)).xxx;
                mainShadow = 1.0;
            }
            else
                irradiance = IncidentLight(surface, input.positionCS, mainShadow, nativeAdditiveLight, directSpecular, shadowLoss);
            directSpecular = SteppedSurfaceSpecular(directSpecular, surface.material);
            half3 color = Shade(surface, irradiance, nativeAdditiveLight, directSpecular, shadowLoss);
            if (_DiagnosticMode > 0.5 && _DiagnosticMode < 1.5)
                color = PaletteColor(surface.material, min((float)surface.pattern,
                    _PaletteMap_TexelSize.z > 4.5 ? _PaletteMap_TexelSize.z - 1.0 : BandCount(surface.material) - 1.0));
            else if (_DiagnosticMode >= 1.5 && _DiagnosticMode < 2.5)
                color = surface.normalWS * 0.5 + 0.5;
            else if (_DiagnosticMode >= 2.5 && _DiagnosticMode < 3.5)
                color = irradiance + nativeAdditiveLight;
            else if (_DiagnosticMode >= 3.5 && _DiagnosticMode < 4.5)
                color = mainShadow.xxx;
            else if (_DiagnosticMode >= 9.5)
                color = directSpecular;
            else if (_DiagnosticMode >= 7.5)
                color = EvaluateSteppedRoomIndirect(surface.positionWS) * max(_SteppedLocalLightStrength, 0.0);
            else if (_DiagnosticMode >= 6.5)
                color = nativeAdditiveLight;
            SurfaceOutput output;
            output.color = half4(color * _BaseColor.rgb, _BaseColor.a);
            output.depth = surface.depth;
            return output;
        }

        SurfaceOutput DepthFrag(Varyings input)
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            clip(_ZWrite - 0.5);
            CachedSurface surface = ReadSurface(input.uv);
            SurfaceOutput output;
            output.color = surface.depth;
            output.depth = surface.depth;
            return output;
        }

        void DepthNormalsFrag(Varyings input, out half4 normalWS : SV_Target0, out float depth : SV_Depth)
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            clip(_ZWrite - 0.5);
            CachedSurface surface = ReadSurface(input.uv);
            depth = surface.depth;
            #if defined(_GBUFFER_NORMALS_OCT)
                float2 octNormal = PackNormalOctQuadEncode(surface.normalWS);
                normalWS = half4(PackFloat2To888(saturate(octNormal * 0.5 + 0.5)), 0.0);
            #else
                normalWS = half4(surface.normalWS, 0.0);
            #endif
        }
        ENDHLSL

        Pass
        {
            Name "NativePaletteForward"
            Tags { "LightMode"="UniversalForwardOnly" }
            Cull [_Cull]
            ZTest LEqual
            ZWrite [_ZWrite]
            Blend [_SrcBlend] [_DstBlend]
            Stencil { Ref 2 ReadMask 2 WriteMask 2 Comp Always Pass Replace }
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile_fragment _ _LIGHT_LAYERS
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            Cull [_Cull]
            ZTest LEqual
            ZWrite [_ZWrite]
            ColorMask R
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing
            ENDHLSL
        }
        Pass
        {
            Name "DepthNormalsOnly"
            Tags { "LightMode"="DepthNormalsOnly" }
            Cull [_Cull]
            ZTest LEqual
            ZWrite [_ZWrite]
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment DepthNormalsFrag
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            ENDHLSL
        }
        // The native display card is never a shadow caster. The importer binds
        // a separate closed semantic mesh using URP's actual shadow pass.
    }
    FallBack Off
}
