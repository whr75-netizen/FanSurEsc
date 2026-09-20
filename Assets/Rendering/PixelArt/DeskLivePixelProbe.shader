Shader "FantasySurvival/PixelArt/Desk Live Pixel Probe"
{
    Properties
    {
        [MainTexture] _BaseMap("Unshaded grain palette (sRGB)", 2D) = "white" {}
        _EdgeMask("D21 geometry-only edge mask", 2D) = "black" {}
        _TexelMeters("Canonical wood texel size (m)", Float) = 0.024
        _PartCenter("Canonical Blender part center", Vector) = (0, 0, 0, 0)
        _PartDimensions("Canonical Blender part dimensions", Vector) = (1, 1, 1, 0)
        [IntRange] _CellPartId("Canonical box part ID", Range(0, 11)) = 0
        _IsLeg("Vertical leg grain", Float) = 0
        _ScreenOrigin("D21 top-down pixel origin", Vector) = (-87, -109, 0, 0)
        _RasterSize("D21 native raster size", Vector) = (174, 155, 0, 0)
        _PixelsPerMeter("Canonical pixels per meter", Float) = 96
        _EdgeColor("Geometry boundary color", Color) = (0.2705882353, 0.1490196078, 0.0862745098, 1)
        _SteppedLocalLightStrength("Existing character local light strength", Float) = 0.55
        [Enum(Live,0,AlbedoOnly,1,MainShadow,2)] _DiagnosticMode("Diagnostic output", Float) = 0

        // The standard opaque URP/Lit auxiliary passes use these properties.
        // The visible pass uses the character's existing matte URP PBR source.
        [HideInInspector] _BaseColor("Base Color", Color) = (1, 1, 1, 1)
        [HideInInspector] _Cutoff("Alpha cutoff", Float) = 0.5
        [HideInInspector] _Cull("Cull", Float) = 2
        [HideInInspector] _ZWrite("Z Write", Float) = 1
        [HideInInspector] _Surface("Surface", Float) = 0
        [HideInInspector] _BumpScale("Normal scale", Float) = 1
        [HideInInspector] _Smoothness("Smoothness", Float) = 0
        [HideInInspector] _Metallic("Metallic", Float) = 0
        [HideInInspector] _OcclusionStrength("Occlusion strength", Float) = 1
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "RenderType" = "Opaque" "Queue" = "Geometry" }

        HLSLINCLUDE
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            // Keep UnityPerMaterial identical to the reused URP/Lit shadow pass.
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitInput.hlsl"
            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            TEXTURE2D(_EdgeMask);
            float _TexelMeters;
            float4 _PartCenter;
            float4 _PartDimensions;
            float _CellPartId;
            float _IsLeg;
            float4 _ScreenOrigin;
            float4 _RasterSize;
            float _PixelsPerMeter;
            float4 _EdgeColor;
            float _SteppedLocalLightStrength;
            float _DiagnosticMode;
            // Supplied by the existing CharacterSilhouetteSubject MPB. Its
            // renderer feature owns cell expansion, depth and grid anchoring.
            float _CharacterCellSurface;
            float _CharacterCellSize;
            float4 _CharacterPixelGridAnchorWS;
            float _CharacterOutlineGroup;
            float _CharacterCellSubjectId;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float3 positionCD : TEXCOORD2;
                float3 normalCD : TEXCOORD3;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                // Canonical D21 is Blender X/right, Y/back, Z/up. The source is
                // a Unity unit cube; placement/rotation never alter its grain.
                output.positionCD = _PartCenter.xyz + input.positionOS.xzy * _PartDimensions.xyz;
                output.normalCD = input.normalOS.xzy;
                return output;
            }

            float3 SampleGrain(float3 positionCD, float3 normalCD)
            {
                float3 a = abs(normalCD);
                // Match numpy.argmax: the first component wins an exact tie.
                int axis = a.x >= a.y && a.x >= a.z ? 0 : (a.y >= a.z ? 1 : 2);
                float2 coordinates;
                if (_IsLeg > 0.5 && axis != 2)
                    coordinates = float2(positionCD.z, axis == 1 ? positionCD.x : positionCD.y);
                else if (axis == 0)
                    coordinates = positionCD.yz;
                else if (axis == 1)
                    coordinates = positionCD.xz;
                else
                    coordinates = positionCD.xy;

                float2 sampleCoordinates = coordinates / max(_TexelMeters, 0.000001);
                float2 size = max(_BaseMap_TexelSize.zw, 1.0);
                float2 index = floor(float2(sampleCoordinates.x, -sampleCoordinates.y));
                // Positive modulo reproduces the numpy modulo of negative coordinates.
                index -= floor(index / size) * size;
                float2 uv = (index + 0.5) / size;
                // numpy grain rows and the PNG are top-down; imported Unity UVs
                // start at the bottom. No interpolation, mip or final-color bake.
                uv.y = 1.0 - uv.y;
                return SAMPLE_TEXTURE2D_LOD(_BaseMap, sampler_PointClamp, uv, 0).rgb;
            }

            float GeometryEdge(float3 positionCD)
            {
                const float3 rightCD = float3(0.707106781186548, 0.707106781186548, 0.0);
                const float3 upCD = float3(-0.353553390593274, 0.353553390593274, 0.866025403784439);
                float2 topDown = float2(dot(positionCD, rightCD), -dot(positionCD, upCD));
                float2 index = floor(topDown * _PixelsPerMeter - _ScreenOrigin.xy);
                if (any(index < 0.0) || any(index >= _RasterSize.xy))
                    return 0.0;
                float2 uv = (index + 0.5) / _RasterSize.xy;
                uv.y = 1.0 - uv.y;
                return step(0.5, SAMPLE_TEXTURE2D_LOD(_EdgeMask, sampler_PointClamp, uv, 0).r);
            }

            float4 EvaluateDeskColor(Varyings input, bool includeFixedViewEdges)
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float3 albedo = SampleGrain(input.positionCD, input.normalCD);
                if (_DiagnosticMode > 0.5 && _DiagnosticMode < 1.5)
                    return float4(albedo, 1.0);

                // Retain the old fixed-view mask only for non-cell comparisons.
                // Cell outlines use the visible box-face group at the same seed
                // as color/depth, so rotations never reuse a baked camera edge.
                if (includeFixedViewEdges)
                    albedo = lerp(albedo, _EdgeColor.rgb, GeometryEdge(input.positionCD));
                InputData d = (InputData)0;
                d.positionWS = input.positionWS;
                d.positionCS = input.positionCS;
                d.normalWS = NormalizeNormalPerPixel(input.normalWS);
                d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
                d.shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                    d.shadowCoord = ComputeScreenPos(TransformWorldToHClip(input.positionWS));
                #endif
                d.bakedGI = SampleSH(d.normalWS);
                d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                d.shadowMask = half4(1, 1, 1, 1);
                if (_DiagnosticMode >= 1.5 && _DiagnosticMode < 2.5)
                {
                    Light mainLight = GetMainLight(d.shadowCoord, input.positionWS, d.shadowMask);
                    return float4(mainLight.shadowAttenuation.xxx, 1.0);
                }

                // Same continuous matte source as Spatial Flat Lit's adaptive
                // character path: URP owns the normal, RGB, SH, sun, additional
                // lights, cookies and shadows. No desk-specific light equation,
                // scalar color conversion, fixed bands or minimum brightness.
                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo;
                s.alpha = 1;
                s.normalTS = half3(0, 0, 1);
                s.occlusion = 1;
                s.metallic = 0;
                s.smoothness = 0;
                half4 color = UniversalFragmentPBR(d, s);
                color.rgb += s.albedo * EvaluateSteppedLocalLights(
                    input.positionWS, d.normalWS, 0.0) * _SteppedLocalLightStrength;
                return color;
            }

            float4 Frag(Varyings input) : SV_Target
            {
                clip(0.5 - _CharacterCellSurface);
                return EvaluateDeskColor(input, true);
            }

            struct CellSourceOutput
            {
                half4 colorDepth : SV_Target0;
                half4 subjectGroupSize : SV_Target1;
            };

            // Exact source contract used by CharacterFlatUnlit.shader. The
            // existing CharacterSilhouetteRendererFeature resolves these cells.
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
                half4 color = EvaluateDeskColor(input, false);
                float eyeDepth = unity_OrthoParams.w > 0.5 ?
                    LinearDepthToEyeDepth(input.positionCS.z) :
                    LinearEyeDepth(input.positionCS.z, _ZBufferParams);
                uint subjectId = (uint)clamp(round(_CharacterCellSubjectId), 1.0, 65535.0);
                // Current geometry is twelve flat-normal boxes. IDs 1..72
                // identify (part, canonical face); 0 remains the empty group.
                // The existing composite gives each boundary one owner through
                // neighbor.group < center.group, without adding a second grid.
                float3 a = abs(input.normalCD);
                int axis = a.x >= a.y && a.x >= a.z ? 0 : (a.y >= a.z ? 1 : 2);
                int faceId = axis * 2 + (input.normalCD[axis] < 0.0 ? 1 : 0);
                float group = 1.0 + clamp(round(_CellPartId), 0.0, 11.0) * 6.0 + faceId;
                CellSourceOutput output;
                output.colorDepth = half4(color.rgb, max(eyeDepth, 0.0001));
                output.subjectGroupSize = half4(
                    (subjectId & 255u) / 255.0, group / 255.0,
                    cellSize / 255.0, (subjectId >> 8) / 255.0);
                return output;
            }

            half4 DepthFrag(Varyings input) : SV_Target
            {
                clip(0.5 - _CharacterCellSurface);
                return 0;
            }

            half4 DepthNormalsFrag(Varyings input) : SV_Target
            {
                clip(0.5 - _CharacterCellSurface);
                float3 normalWS = NormalizeNormalPerPixel(input.normalWS);
                #if defined(_GBUFFER_NORMALS_OCT)
                    float2 octNormalWS = PackNormalOctQuadEncode(normalWS);
                    float2 remappedOctNormalWS = saturate(octNormalWS * 0.5 + 0.5);
                    return half4(PackFloat2To888(remappedOctNormalWS), 0.0);
                #else
                    return half4(normalWS, 0.0);
                #endif
            }
        ENDHLSL

        Pass
        {
            Name "DeskLiveForward"
            Tags { "LightMode" = "UniversalForwardOnly" }
            Cull Back
            ZWrite On
            ZTest LEqual
            Blend One Zero
            // Local light is already included by the material. The existing
            // fullscreen light pass excludes stencil bit 2.
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
            ENDHLSL
        }

        Pass
        {
            Name "CharacterPixelCellSource"
            Tags { "LightMode" = "CharacterPixelCellSource" }
            Cull Back
            ZWrite On
            ZTest LEqual
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment FragCellSource
            #pragma multi_compile_instancing
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
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
            Cull Back
            ZWrite On
            ZTest LEqual
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            Cull Back
            ZWrite On
            ZTest LEqual
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment DepthNormalsFrag
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            ENDHLSL
        }

        // Cast shadows from the actual mesh even when its visible presentation
        // uses the existing cell renderer. No hidden native color/depth remains.
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
    }
    FallBack Off
}
