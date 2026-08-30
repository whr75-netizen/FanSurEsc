Shader "Hidden/FantasySurvival/PixelRainFullscreen"
{
    Properties
    {
        _PixelRainPattern("Rain Pattern", 2D) = "black" {}
        _LogicalPixelSize("Logical Pixel Size", Range(1, 4)) = 1
        _RainFramesPerSecond("Rain Frames Per Second", Range(1, 30)) = 20
        _RainPatternPixelsPerWorld("Rain Pattern Pixels Per World Unit", Range(8, 96)) = 48
        _StreakOpacity("Streak Opacity", Range(0, 1)) = 0.48
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        Blend SrcAlpha OneMinusSrcAlpha
        ColorMask RGB

        Pass
        {
            Name "PixelRainFullscreen"

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            TEXTURE2D(_PixelRainPattern);
            TEXTURE2D(_FantasyRainShelterHeight);

            CBUFFER_START(UnityPerMaterial)
                float _LogicalPixelSize;
                float _RainFramesPerSecond;
                float _RainPatternPixelsPerWorld;
                float _StreakOpacity;
            CBUFFER_END

            float _FantasyRainIntensity;
            float4 _FantasyRainColor;
            float _FantasyRainVisualTime;
            float4 _FantasyRainWorldGridOffset;
            float _FantasyRainWorldUnitsPerScreenPixel;
            float _FantasyRainDirection;
            float4 _FantasyRainShelterWorldRect;
            float _FantasyRainShelterReady;
            float _FantasyRainShelterClearance;
            float _FantasyRainShelterMaximumHeight;

            struct RainSurface
            {
                float3 positionWS;
                float geometryMask;
            };

            int2 WrapPatternCoordinate(int2 value)
            {
                // The pattern is exactly 256x256, so a bit mask gives the same
                // positive wrap for negative coordinates without integer modulus.
                return int2(value.x & 255, value.y & 255);
            }

            float Hash21(float2 value)
            {
                float3 p3 = frac(float3(value.xyx) * 0.1031);
                p3 += dot(p3, p3.yzx + 33.33);
                return frac((p3.x + p3.y) * p3.z);
            }

            float2 Hash22(float2 value)
            {
                float first = Hash21(value);
                return float2(first, Hash21(value + first + 19.19));
            }

            RainSurface SampleRainSurface(float2 uv)
            {
                RainSurface surface;
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                #if UNITY_REVERSED_Z
                    float deviceDepth = rawDepth;
                    surface.geometryMask = step(0.000001, rawDepth);
                #else
                    float deviceDepth = lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                    surface.geometryMask = 1.0 - step(0.999999, rawDepth);
                #endif

                surface.positionWS = ComputeWorldSpacePosition(
                    uv,
                    deviceDepth,
                    UNITY_MATRIX_I_VP);
                return surface;
            }

            float EvaluateShelter(float3 positionWS)
            {
                float2 uv =
                    (positionWS.xz - _FantasyRainShelterWorldRect.xy) *
                    _FantasyRainShelterWorldRect.zw;
                float inside =
                    step(0.0, uv.x) * step(0.0, uv.y) *
                    step(uv.x, 1.0) * step(uv.y, 1.0);
                float roofHeight = SAMPLE_TEXTURE2D_LOD(
                    _FantasyRainShelterHeight,
                    sampler_PointClamp,
                    saturate(uv),
                    0).r;
                return inside * _FantasyRainShelterReady *
                    step(positionWS.y + _FantasyRainShelterClearance, roofHeight);
            }

            float EvaluateShelterVolume(float3 surfacePositionWS)
            {
                if (_FantasyRainShelterReady <= 0.0)
                {
                    return 0.0;
                }

                float sheltered = EvaluateShelter(surfacePositionWS);
                float maximumSampleHeight =
                    _FantasyRainShelterMaximumHeight -
                    _FantasyRainShelterClearance;
                float verticalSpan = maximumSampleHeight - surfacePositionWS.y;
                float3 viewDirectionWS =
                    GetWorldSpaceNormalizeViewDir(surfacePositionWS);
                if (sheltered > 0.0 ||
                    verticalSpan <= 0.0 ||
                    viewDirectionWS.y <= 0.0001)
                {
                    return sheltered;
                }

                // Fullscreen rain has no per-drop world depth. March the visible
                // surface toward the orthographic camera through the cached roof
                // height field. This projects the dry volume from the floor up to
                // the roof instead of cutting only the roof's ground footprint.
                const int sampleCount = 12;
                float viewDistance = verticalSpan / viewDirectionWS.y;
                [unroll]
                for (int index = 1; index <= sampleCount; index++)
                {
                    float sampleRatio = (float)index / (float)sampleCount;
                    float3 samplePositionWS = surfacePositionWS +
                        viewDirectionWS * viewDistance * sampleRatio;
                    if (EvaluateShelter(samplePositionWS) > 0.0)
                    {
                        return 1.0;
                    }
                }

                return 0.0;
            }

            float SelectPatternFrame(half4 pattern, int frameIndex)
            {
                if (frameIndex == 0)
                {
                    return pattern.r;
                }

                if (frameIndex == 1)
                {
                    return pattern.g;
                }

                if (frameIndex == 2)
                {
                    return pattern.b;
                }

                return pattern.a;
            }

            float EvaluateStreaks(
                int2 logicalPixel,
                float logicalScale,
                int rainFrame)
            {
                // The projected world-origin offset cancels camera translation.
                // Converting screen pixels through 2*orthoSize/screenHeight then
                // keeps the same rain cell at the same world phase while zooming.
                float2 screenPixel =
                    ((float2)logicalPixel + 0.5) * logicalScale;
                float2 worldGridCoordinate =
                    (screenPixel + _FantasyRainWorldGridOffset.xy) *
                    max(_FantasyRainWorldUnitsPerScreenPixel, 0.000001) *
                    max(_RainPatternPixelsPerWorld, 0.001);
                int2 worldGridPixel = (int2)floor(worldGridCoordinate);
                int2 tileLocal = WrapPatternCoordinate(worldGridPixel);
                int2 tileCoordinate = (worldGridPixel - tileLocal) >> 8;

                int tileFrameOffset = (int)floor(
                    Hash21((float2)tileCoordinate + 41.37) * 4.0);
                int frameIndex = (rainFrame + tileFrameOffset) & 3;

                // RGBA stores four frames, but repeating them at 20 FPS would
                // reveal the same four locations every 0.2 seconds. Advance a
                // deterministic global spatial phase after each four-frame loop
                // so rainfall appears non-repeating without CPU particle state.
                int loopIndex = rainFrame >> 2;
                float2 loopRandom = Hash22(
                    float2((float)loopIndex + 73.19, 11.83));
                int2 loopOffset = (int2)floor(loopRandom * 256.0);
                int2 patternCoordinate = WrapPatternCoordinate(
                    tileLocal + loopOffset);
                if (_FantasyRainDirection < 0.0)
                {
                    patternCoordinate.x = 255 - patternCoordinate.x;
                }

                half4 pattern = LOAD_TEXTURE2D(
                    _PixelRainPattern,
                    patternCoordinate);
                return SelectPatternFrame(pattern, frameIndex);
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float intensity = saturate(_FantasyRainIntensity);
                if (intensity <= 0.0001)
                {
                    return half4(0.0, 0.0, 0.0, 0.0);
                }

                float logicalScale = max(round(_LogicalPixelSize), 1.0);
                float2 screenSize = max(_ScaledScreenParams.xy, float2(1.0, 1.0));
                float2 logicalScreenSize = max(
                    floor(screenSize / logicalScale),
                    float2(1.0, 1.0));
                int2 logicalPixel = (int2)floor(
                    saturate(input.texcoord) * logicalScreenSize);
                float2 sampleUv =
                    ((float2)logicalPixel + 0.5) / logicalScreenSize;
                int streakFrame = (int)floor(
                    _FantasyRainVisualTime * max(_RainFramesPerSecond, 1.0));

                float streak = EvaluateStreaks(
                    logicalPixel,
                    logicalScale,
                    streakFrame);
                if (streak <= 0.0)
                {
                    return half4(0.0, 0.0, 0.0, 0.0);
                }

                RainSurface surface = SampleRainSurface(sampleUv);
                float sheltered = surface.geometryMask > 0.0
                    ? EvaluateShelterVolume(surface.positionWS)
                    : 0.0;
                streak *= lerp(1.0, 1.0 - sheltered, surface.geometryMask);
                float alpha = saturate(
                    streak * _StreakOpacity *
                    intensity * _FantasyRainColor.a);
                return half4(_FantasyRainColor.rgb, alpha);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
