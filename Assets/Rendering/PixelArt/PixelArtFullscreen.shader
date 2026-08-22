Shader "Hidden/Fantasy Survival Escape Game/Pixel Art Fullscreen"
{
    Properties
    {
        _PixelSize("Pixel Size", Range(1, 12)) = 6
        _DepthThreshold("Depth Edge Threshold", Range(0.001, 0.5)) = 0.06
        _DepthSoftness("Depth Edge Softness", Range(0.001, 0.5)) = 0.04
        _NormalThreshold("Normal Edge Threshold", Range(0.001, 1)) = 0.18
        _NormalSoftness("Normal Edge Softness", Range(0.001, 1)) = 0.08
        _OutlineColor("Outline Color", Color) = (0.035, 0.045, 0.06, 1)
        _OutlineStrength("Outline Strength", Range(0, 1)) = 0.72
        _NormalHighlight("Normal Highlight", Range(0, 0.5)) = 0.12
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
        }

        ZTest Always
        ZWrite Off
        Cull Off

        Pass
        {
            Name "PixelArtFullscreen"

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _PixelSize;
                float _DepthThreshold;
                float _DepthSoftness;
                float _NormalThreshold;
                float _NormalSoftness;
                half4 _OutlineColor;
                float _OutlineStrength;
                float _NormalHighlight;
            CBUFFER_END

            struct SurfaceSample
            {
                float eyeDepth;
                float3 normalWS;
                float geometryMask;
            };

            float GeometryMask(float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    return step(0.000001, rawDepth);
                #else
                    return 1.0 - step(0.999999, rawDepth);
                #endif
            }

            float3 PixelArtSafeNormalize(float3 value)
            {
                return value * rsqrt(max(dot(value, value), 0.000001));
            }

            SurfaceSample SampleSurface(float2 uv)
            {
                SurfaceSample surface;
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                surface.eyeDepth = unity_OrthoParams.w == 0.0
                    ? LinearEyeDepth(rawDepth, _ZBufferParams)
                    : LinearDepthToEyeDepth(rawDepth);
                surface.normalWS = PixelArtSafeNormalize(SampleSceneNormals(uv, sampler_PointClamp));
                surface.geometryMask = GeometryMask(rawDepth);
                return surface;
            }

            float GetDepthDifference(SurfaceSample center, SurfaceSample neighbor)
            {
                float relativeDifference = max(neighbor.eyeDepth - center.eyeDepth, 0.0)
                    / max(center.eyeDepth, 0.01);
                return relativeDifference * center.geometryMask;
            }

            float GetNormalDifference(SurfaceSample center, SurfaceSample neighbor)
            {
                float relativeDepthDifference = abs(neighbor.eyeDepth - center.eyeDepth)
                    / max(center.eyeDepth, 0.01);
                float sameSurface = 1.0 - smoothstep(
                    _DepthThreshold * 0.5,
                    _DepthThreshold * 2.0 + _DepthSoftness,
                    relativeDepthDifference);
                float directionDifference = 1.0 - saturate(dot(center.normalWS, neighbor.normalWS));

                return directionDifference
                    * sameSurface
                    * center.geometryMask
                    * neighbor.geometryMask;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float pixelSize = max(round(_PixelSize), 1.0);
                float2 screenSize = max(_ScreenParams.xy, float2(1.0, 1.0));
                float2 virtualSize = max(floor(screenSize / pixelSize), float2(1.0, 1.0));
                float2 virtualTexelSize = rcp(virtualSize);
                float2 pixelUv = (floor(saturate(input.texcoord.xy) * virtualSize) + 0.5)
                    * virtualTexelSize;

                half4 sourceColor = SAMPLE_TEXTURE2D_X_LOD(
                    _BlitTexture,
                    sampler_PointClamp,
                    pixelUv,
                    0);

                SurfaceSample center = SampleSurface(pixelUv);
                SurfaceSample down = SampleSurface(saturate(pixelUv + float2(0.0, -virtualTexelSize.y)));
                SurfaceSample up = SampleSurface(saturate(pixelUv + float2(0.0, virtualTexelSize.y)));
                SurfaceSample right = SampleSurface(saturate(pixelUv + float2(virtualTexelSize.x, 0.0)));
                SurfaceSample left = SampleSurface(saturate(pixelUv + float2(-virtualTexelSize.x, 0.0)));

                float depthDifference = max(
                    max(GetDepthDifference(center, down), GetDepthDifference(center, up)),
                    max(GetDepthDifference(center, right), GetDepthDifference(center, left)));
                float depthEdge = smoothstep(
                    _DepthThreshold,
                    _DepthThreshold + _DepthSoftness,
                    depthDifference);

                float normalDifference = max(
                    max(GetNormalDifference(center, down), GetNormalDifference(center, up)),
                    max(GetNormalDifference(center, right), GetNormalDifference(center, left)));
                float normalEdge = smoothstep(
                    _NormalThreshold,
                    _NormalThreshold + _NormalSoftness,
                    normalDifference);

                half3 result = lerp(
                    sourceColor.rgb,
                    _OutlineColor.rgb,
                    saturate(depthEdge * _OutlineStrength));
                result += normalEdge * _NormalHighlight * (1.0 - depthEdge);

                return half4(result, sourceColor.a);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
