Shader "FantasySurvival/PixelArt/Desk Live Pixel Probe"
{
    Properties
    {
        [MainTexture] _BaseMap("Unshaded grain palette (sRGB)", 2D) = "white" {}
        _EdgeMask("D21 geometry-only edge mask", 2D) = "black" {}
        _TexelMeters("Canonical wood texel size (m)", Float) = 0.024
        _PartCenter("Canonical Blender part center", Vector) = (0, 0, 0, 0)
        _PartDimensions("Canonical Blender part dimensions", Vector) = (1, 1, 1, 0)
        _IsLeg("Vertical leg grain", Float) = 0
        _ScreenOrigin("D21 top-down pixel origin", Vector) = (-87, -109, 0, 0)
        _RasterSize("D21 native raster size", Vector) = (174, 155, 0, 0)
        _PixelsPerMeter("Canonical pixels per meter", Float) = 96
        _EdgeColor("Geometry boundary color", Color) = (0.2705882353, 0.1490196078, 0.0862745098, 1)
        _MainLightStrength("Linear irradiance multiplier (1 = unchanged Unity units)", Float) = 1
        _AmbientLightStrength("Six-direction SH average strength", Float) = 0
        _SteppedLocalLightStrength("Existing stepped local irradiance scale", Float) = 1
        [Enum(Live,0,AlbedoOnly,1,MainShadow,2,Incident,3)] _DiagnosticMode("Diagnostic output", Float) = 0

        // The standard opaque URP/Lit auxiliary passes use these properties.
        // The visible pass has no specular, smoothness, normal-map or emission term.
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

        Pass
        {
            Name "DeskLiveForward"
            Tags { "LightMode" = "UniversalForwardOnly" }
            Cull Back
            ZWrite On
            ZTest LEqual
            Blend One Zero

            // The visible fragment already evaluates the existing stepped local
            // lights. Their fullscreen pass excludes bit 2, avoiding double light.
            Stencil
            {
                Ref 2
                ReadMask 2
                WriteMask 2
                Comp Always
                Pass Replace
            }

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            // Keep UnityPerMaterial identical to the three reused URP/Lit passes.
            #include "Packages/com.unity.render-pipelines.universal/Shaders/LitInput.hlsl"
            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            TEXTURE2D(_EdgeMask);
            float _TexelMeters;
            float4 _PartCenter;
            float4 _PartDimensions;
            float _IsLeg;
            float4 _ScreenOrigin;
            float4 _RasterSize;
            float _PixelsPerMeter;
            float4 _EdgeColor;
            float _MainLightStrength;
            float _AmbientLightStrength;
            float _SteppedLocalLightStrength;
            float _DiagnosticMode;

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

            float LuminanceLinear(float3 color)
            {
                return dot(max(color, 0.0), float3(0.2126, 0.7152, 0.0722));
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

            float AverageAmbientLuminance()
            {
                // A declared, direction-independent SH mean. It is disabled by
                // default: the minimum D21 gain 0.42 supplies the NPR shadow floor.
                float3 averageSH = (
                    SampleSH(float3(1, 0, 0)) + SampleSH(float3(-1, 0, 0)) +
                    SampleSH(float3(0, 1, 0)) + SampleSH(float3(0, -1, 0)) +
                    SampleSH(float3(0, 0, 1)) + SampleSH(float3(0, 0, -1))) / 6.0;
                return LuminanceLinear(averageSH) * _AmbientLightStrength;
            }

            float4 Frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float3 albedo = SampleGrain(input.positionCD, input.normalCD);
                if (_DiagnosticMode > 0.5 && _DiagnosticMode < 1.5)
                    return float4(albedo, 1.0);

                float3 normalWS = normalize(input.normalWS);
                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                    shadowCoord = ComputeScreenPos(TransformWorldToHClip(input.positionWS));
                #endif
                Light mainLight = GetMainLight(shadowCoord, input.positionWS, half4(1, 1, 1, 1));
                if (_DiagnosticMode >= 1.5 && _DiagnosticMode < 2.5)
                    return float4(mainLight.shadowAttenuation.xxx, 1.0);

                float lambert = saturate(dot(normalWS, mainLight.direction));
                // Unity's light color already contains its actual intensity.
                // The first probe's 0.5 reference multiplier unnecessarily halved
                // the base scene's irradiance into the lowest-band dead zone.
                // One preserves Unity input units; a failed response must be
                // diagnosed from that input, never fitted by increasing this value.
                float incident = LuminanceLinear(mainLight.color) *
                    mainLight.distanceAttenuation * mainLight.shadowAttenuation *
                    lambert * _MainLightStrength;
                incident += AverageAmbientLuminance();
                // These are the existing scene's stepped presentation lights,
                // not Unity shadow-casting Lights. Their evaluator has NO occlusion.
                // Both colored sources select the NPR band by luminance; they do
                // not tint the four wood colors or add unrestricted output shades.
                incident += LuminanceLinear(EvaluateSteppedLocalLights(
                    input.positionWS, normalWS, 1.0)) * _SteppedLocalLightStrength;

                if (_DiagnosticMode >= 2.5 && _DiagnosticMode < 3.5)
                {
                    float visibleIncident = saturate(incident);
                    return float4(visibleIncident.xxx, 1.0);
                }

                float gain = incident < 0.32 ? 0.42 : (incident < 0.72 ? 0.72 : 1.0);
                float3 color = albedo * gain;
                color = lerp(color, _EdgeColor.rgb, GeometryEdge(input.positionCD));
                // The edge mask contains geometry decisions only. All live
                // illumination is evaluated above, independently of the material.
                return float4(color, 1.0);
            }
            ENDHLSL
        }

        // Geometry stays genuinely 3D for URP light shadows, depth and normals.
        // This opaque probe never enables alpha clipping or normal-map keywords.
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
        UsePass "Universal Render Pipeline/Lit/DepthNormals"
    }
    FallBack Off
}
