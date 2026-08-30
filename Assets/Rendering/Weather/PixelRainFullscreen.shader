Shader "Hidden/FantasySurvival/PixelRainFullscreen"
{
    Properties
    {
        _PixelRainPattern("Rain Pattern", 2D) = "black" {}
        _PixelRainSplashAtlas("Splash Atlas", 2D) = "black" {}
        _LogicalPixelSize("Logical Pixel Size", Range(1, 4)) = 1
        _RainFramesPerSecond("Rain Frames Per Second", Range(1, 30)) = 8
        _StreakOpacity("Streak Opacity", Range(0, 1)) = 0.55
        _SplashOpacity("Splash Opacity", Range(0, 1)) = 0.62
        _SplashSpawnRate("Splash Spawn Rate", Range(0, 1)) = 0.62
        _SplashCellWorldSize("Splash Cell World Size", Range(0.5, 4)) = 1.6
        _SplashCycleFrames("Splash Cycle Frames", Range(8, 40)) = 12
        _SplashMinimumNormalY("Splash Minimum Normal Y", Range(0, 1)) = 0.75
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
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

            TEXTURE2D(_PixelRainPattern);
            TEXTURE2D(_PixelRainSplashAtlas);
            TEXTURE2D(_FantasyRainShelterHeight);

            CBUFFER_START(UnityPerMaterial)
                float _LogicalPixelSize;
                float _RainFramesPerSecond;
                float _StreakOpacity;
                float _SplashOpacity;
                float _SplashSpawnRate;
                float _SplashCellWorldSize;
                float _SplashCycleFrames;
                float _SplashMinimumNormalY;
            CBUFFER_END

            float _FantasyRainIntensity;
            float4 _FantasyRainColor;
            float _FantasyRainVisualTime;
            float4 _FantasyRainWorldGridOffset;
            float _FantasyRainDirection;
            float4 _FantasyRainShelterWorldRect;
            float _FantasyRainShelterReady;
            float _FantasyRainShelterClearance;

            struct RainSurface
            {
                float3 positionWS;
                float3 normalWS;
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
                float3 sampledNormal = SampleSceneNormals(uv, sampler_PointClamp);
                surface.normalWS = sampledNormal * rsqrt(
                    max(dot(sampledNormal, sampledNormal), 0.000001));
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
                // Subtracting the projected world origin cancels an orthographic
                // camera's XZ translation. The same rain cell therefore moves
                // across the screen with the world instead of sticking to the UI.
                int2 worldGridOffset = (int2)round(
                    _FantasyRainWorldGridOffset.xy / logicalScale);
                int2 worldGridPixel = logicalPixel + worldGridOffset;
                int2 tileLocal = WrapPatternCoordinate(worldGridPixel);
                int2 tileCoordinate = (worldGridPixel - tileLocal) >> 8;

                int tileFrameOffset = (int)floor(
                    Hash21((float2)tileCoordinate + 41.37) * 4.0);
                int frameIndex = (rainFrame + tileFrameOffset) & 3;

                int2 patternCoordinate = tileLocal;
                if (_FantasyRainDirection < 0.0)
                {
                    patternCoordinate.x = 255 - patternCoordinate.x;
                }

                half4 pattern = LOAD_TEXTURE2D(
                    _PixelRainPattern,
                    patternCoordinate);
                return SelectPatternFrame(pattern, frameIndex);
            }

            float EvaluateSplash(
                int2 logicalPixel,
                float2 logicalScreenSize,
                int rainFrame,
                RainSurface surface,
                float exposed,
                float intensity)
            {
                float upwardSurface = surface.geometryMask *
                    step(_SplashMinimumNormalY, surface.normalWS.y) * exposed;
                if (upwardSurface <= 0.0)
                {
                    return 0.0;
                }

                float cellSize = max(_SplashCellWorldSize, 0.1);
                float2 worldCell = floor(surface.positionWS.xz / cellSize);
                float priority = Hash21(worldCell + 7.31);
                if (priority > intensity * _SplashSpawnRate)
                {
                    return 0.0;
                }

                int cycleFrames = max((int)round(_SplashCycleFrames), 8);
                int phaseOffset = (int)floor(Hash21(worldCell + 31.7) * cycleFrames);
                int splashFrame = (int)floor(fmod(
                    (float)(rainFrame + phaseOffset),
                    (float)cycleFrames));
                if (splashFrame >= 4)
                {
                    return 0.0;
                }

                float2 centerRandom = lerp(
                    float2(0.3, 0.3),
                    float2(0.7, 0.7),
                    Hash22(worldCell + 13.17));
                float2 centerXZ = (worldCell + centerRandom) * cellSize;
                float3 centerWS = float3(
                    centerXZ.x,
                    surface.positionWS.y + 0.02,
                    centerXZ.y);
                float4 centerHClip = TransformWorldToHClip(centerWS);
                float4 centerScreen = ComputeScreenPos(centerHClip);
                float2 centerUv = centerScreen.xy /
                    max(abs(centerScreen.w), 0.000001);
                int2 centerLogicalPixel = (int2)floor(centerUv * logicalScreenSize);
                int2 localPixel = logicalPixel - centerLogicalPixel + int2(3, 1);
                if (localPixel.x < 0 || localPixel.x >= 7 ||
                    localPixel.y < 0 || localPixel.y >= 4)
                {
                    return 0.0;
                }

                int2 atlasCoordinate = int2(
                    splashFrame * 7 + localPixel.x,
                    localPixel.y);
                return LOAD_TEXTURE2D(
                    _PixelRainSplashAtlas,
                    atlasCoordinate).r * upwardSurface;
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
                int rainFrame = (int)floor(
                    _FantasyRainVisualTime * max(_RainFramesPerSecond, 1.0));

                RainSurface surface = SampleRainSurface(sampleUv);
                float sheltered = surface.geometryMask > 0.0
                    ? EvaluateShelter(surface.positionWS)
                    : 0.0;
                float exposed = 1.0 - sheltered;
                float streak = EvaluateStreaks(
                    logicalPixel,
                    logicalScale,
                    rainFrame) *
                    lerp(1.0, exposed, surface.geometryMask);
                float splash = EvaluateSplash(
                    logicalPixel,
                    logicalScreenSize,
                    rainFrame,
                    surface,
                    exposed,
                    intensity);
                float alpha = saturate(max(
                    streak * _StreakOpacity,
                    splash * _SplashOpacity) * intensity * _FantasyRainColor.a);
                return half4(_FantasyRainColor.rgb, alpha);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
