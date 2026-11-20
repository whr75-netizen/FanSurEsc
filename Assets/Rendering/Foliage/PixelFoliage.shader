Shader "FantasySurvival/PixelFoliage"
{
    Properties
    {
        [MainTexture] _BaseMap("Sprite Atlas (4 Columns, Grass Bottom / Leaves Top)", 2D) = "white" {}
        [MainColor] _BaseColor("Base Color", Color) = (1, 1, 1, 1)
        [Toggle] _SpriteMode("Billboard Sprite (Off = Solid Mesh)", Float) = 1
        _Cutoff("Alpha Cutoff", Range(0, 1)) = 0.5
        _AnimationFps("Sprite Frames Per Second (0.4 = 2.5s Hold)", Range(0, 24)) = 0.4
        _ColorVariation("Per-Tuft Brightness Variation", Range(0, 1)) = 0
        _ShadeSteps("Diffuse Shade Steps", Range(2, 4)) = 2
        _ShadeSoftness("Shade Transition Width", Range(0.001, 0.3)) = 0.06
        _AmbientLightStrength("Ambient Light Strength", Range(0, 2)) = 1
        _MainLightStrength("Main Light Strength", Range(0, 2)) = 1
        _AdditionalLightStrength("Additional Light Strength", Range(0, 2)) = 1
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "TransparentCutout"
            "Queue" = "AlphaTest"
        }
        Cull Off
        ZWrite On
        ZTest LEqual

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_TexelSize;
            half4 _BaseColor;
            float _SpriteMode;
            float _Cutoff;
            float _AnimationFps;
            half _ColorVariation;
            half _ShadeSteps;
            half _ShadeSoftness;
            half _AmbientLightStrength;
            half _MainLightStrength;
            half _AdditionalLightStrength;
        CBUFFER_END

        TEXTURE2D(_BaseMap);
        SamplerState sampler_point_clamp;

        struct Attributes
        {
            // Each quad repeats its source anchor and source surface normal.
            float4 positionOS : POSITION;
            float3 normalOS : NORMAL;
            float2 uv : TEXCOORD0;
            float4 sprite : TEXCOORD1; // world width, height, pivotY, atlas row
            float4 variation : TEXCOORD2; // phase01, brightness multiplier
            half4 color : COLOR;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };

        struct Varyings
        {
            float4 positionCS : SV_POSITION;
            float3 sourceWS : TEXCOORD0;
            float3 normalWS : TEXCOORD1;
            float4 atlas : TEXCOORD2; // local UV, column, row
            half4 color : TEXCOORD3;
            half fogFactor : TEXCOORD4;
            UNITY_VERTEX_INPUT_INSTANCE_ID
            UNITY_VERTEX_OUTPUT_STEREO
        };

        float3 FoliageNormal(float3 normal)
        {
            float lengthSquared = dot(normal, normal);
            return lengthSquared > 0.000001
                ? normal * rsqrt(max(lengthSquared, 0.000001))
                : float3(0.0, 1.0, 0.0);
        }

        Varyings FoliageVertex(Attributes input)
        {
            Varyings output = (Varyings)0;
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_TRANSFER_INSTANCE_ID(input, output);
            UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
            output.sourceWS = TransformObjectToWorld(input.positionOS.xyz);
            output.normalWS = FoliageNormal(
                TransformObjectToWorldNormal(input.normalOS, false));
            float3 positionWS = output.sourceWS;
            output.color = half4(1.0, 1.0, 1.0, 1.0);

            if (_SpriteMode > 0.5)
            {
                float3 cameraRight = UNITY_MATRIX_I_V._m00_m10_m20;
                float3 cameraUp = UNITY_MATRIX_I_V._m01_m11_m21;
                positionWS += cameraRight * ((input.uv.x - 0.5) * input.sprite.x)
                    + cameraUp * ((input.uv.y - input.sprite.z) * input.sprite.y);
                float frame = floor(_Time.y * _AnimationFps + frac(input.variation.x) * 4.0);
                output.atlas = float4(input.uv, frame - floor(frame * 0.25) * 4.0,
                    clamp(round(input.sprite.w), 0.0, 1.0));
                output.color = input.color;
                // Keep neighbouring tufts in the same colour mass when variation
                // is zero; retain the baked seed for optional authoring variation.
                output.color.rgb *= lerp(1.0h, max(input.variation.y, 0.0),
                    saturate(_ColorVariation));
            }

            output.positionCS = TransformWorldToHClip(positionWS);
            output.fogFactor = ComputeFogFactor(output.positionCS.z);
            return output;
        }

        half4 FoliageAlbedo(Varyings input)
        {
            if (_SpriteMode <= 0.5)
                return half4(_BaseColor.rgb, 1.0);

            // Sample exact native texel centers at mip zero. Atlas neighbours
            // cannot bleed across the cutout and zoom changes apparent size.
            float2 framePixels = max(_BaseMap_TexelSize.zw / float2(4.0, 2.0), 1.0);
            float2 pixel = min(floor(saturate(input.atlas.xy) * framePixels), framePixels - 1.0);
            float2 atlasUV = (input.atlas.zw + (pixel + 0.5) / framePixels) / float2(4.0, 2.0);
            // The atlas is a shape mask; authored RGB must not bake a second
            // lighting model into the terrain/crown-derived illumination.
            half alpha = SAMPLE_TEXTURE2D_LOD(_BaseMap, sampler_point_clamp, atlasUV, 0.0).a;
            half4 albedo = _BaseColor * input.color;
            albedo.a *= alpha;
            clip(albedo.a - _Cutoff);
            return albedo;
        }

        half3 FoliageLight(Light light, float3 normalWS)
        {
            if (!IsMatchingLightLayer(light.layerMask, GetMeshRenderingLayer()))
                return half3(0.0, 0.0, 0.0);

            half intervals = max(round(_ShadeSteps) - 1.0h, 1.0h);
            // Quantize cast shadow attenuation together with N.L so pixel leaves
            // show crisp cel shadow bands instead of blurry URP PCF gray smears.
            half shadowBand = smoothstep(0.38h, 0.52h, saturate(light.shadowAttenuation));
            half raw = saturate(dot(normalWS, light.direction)) * shadowBand * saturate(light.distanceAttenuation);
            half diffuse = raw * intervals;
            half transition = min(max(_ShadeSoftness, 0.001h) * intervals, 0.49h);
            half shade = (floor(diffuse) + smoothstep(0.5h - transition,
                0.5h + transition, frac(diffuse))) / intervals;
            return light.color * shade;
        }

        half4 FoliageFragment(Varyings input) : SV_Target
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            half4 albedo = FoliageAlbedo(input);
            float3 normalWS = FoliageNormal(input.normalWS);
            half3 lighting = max(SampleSH(normalWS), 0.0h) * _AmbientLightStrength;
            const half4 shadowMask = half4(1.0, 1.0, 1.0, 1.0);
            // This overload also applies SampleMainLightCookie(sourceWS) once.
            // Neither animated pixels nor camera-facing expansion move sampling.
            Light mainLight = GetMainLight(TransformWorldToShadowCoord(input.sourceWS),
                input.sourceWS, shadowMask);
            lighting += FoliageLight(mainLight, normalWS) * _MainLightStrength;

            #if defined(_ADDITIONAL_LIGHTS) || USE_CLUSTER_LIGHT_LOOP
                InputData inputData = (InputData)0;
                inputData.positionWS = input.sourceWS;
                float4 sourceScreen = ComputeScreenPos(TransformWorldToHClip(input.sourceWS));
                inputData.normalizedScreenSpaceUV = sourceScreen.xy / sourceScreen.w;
                #if USE_CLUSTER_LIGHT_LOOP
                    UNITY_LOOP for (uint lightIndex = 0;
                        lightIndex < min(URP_FP_DIRECTIONAL_LIGHTS_COUNT, MAX_VISIBLE_LIGHTS);
                        lightIndex++)
                    {
                        Light light = GetAdditionalLight(lightIndex, input.sourceWS, shadowMask);
                        lighting += FoliageLight(light, normalWS) * _AdditionalLightStrength;
                    }
                #endif
                uint lightCount = GetAdditionalLightsCount();
                LIGHT_LOOP_BEGIN(lightCount)
                    Light light = GetAdditionalLight(lightIndex, input.sourceWS, shadowMask);
                    lighting += FoliageLight(light, normalWS) * _AdditionalLightStrength;
                LIGHT_LOOP_END
            #endif

            // Registered stepped lights remain owned by the existing fullscreen
            // pass; adding them here would illuminate this material twice.
            return half4(MixFog(albedo.rgb * lighting, input.fogFactor), 1.0);
        }

        half4 FoliageDepthFragment(Varyings input) : SV_Target
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            FoliageAlbedo(input);
            return 0;
        }

        void FoliageNormalsFragment(Varyings input, out half4 normal : SV_Target0
            #ifdef _WRITE_RENDERING_LAYERS
                , out uint renderingLayers : SV_Target1
            #endif
        )
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            FoliageAlbedo(input);
            float3 normalWS = FoliageNormal(input.normalWS);
            #if defined(_GBUFFER_NORMALS_OCT)
                float2 octNormal = PackNormalOctQuadEncode(normalWS);
                normal = half4(PackFloat2To888(saturate(octNormal * 0.5 + 0.5)), 0.0);
            #else
                normal = half4(normalWS, 0.0);
            #endif
            #ifdef _WRITE_RENDERING_LAYERS
                renderingLayers = EncodeMeshRenderingLayer();
            #endif
        }
        ENDHLSL

        Pass
        {
            Name "PixelFoliageForward"
            Tags { "LightMode" = "UniversalForwardOnly" }
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex FoliageVertex
            #pragma fragment FoliageFragment
            #pragma multi_compile_instancing
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ _LIGHT_LAYERS
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
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex FoliageVertex
            #pragma fragment FoliageDepthFragment
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormalsOnly" }
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex FoliageVertex
            #pragma fragment FoliageNormalsFragment
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"
            ENDHLSL
        }
    }
    FallBack Off
}
