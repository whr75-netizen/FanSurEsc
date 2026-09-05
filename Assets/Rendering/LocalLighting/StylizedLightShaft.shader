Shader "Hidden/FantasySurvival/StylizedLightShaft"
{
    Properties
    {
        [HideInInspector][HDR] _ShaftColor("Shaft Color", Color) = (1, 1, 1, 1)
        [HideInInspector] _ShaftIntensity("Shaft Intensity", Float) = 0
        [HideInInspector] _SurfaceFadeDistance("Surface Fade Distance", Float) = 0.45
        [HideInInspector] _DirectionalVolumeBounds("Volume Bounds", Vector) = (0.02, 12, 0, 0)
        [HideInInspector] _DirectionalMediumSettings("Medium Settings", Vector) = (0.16, 0.22, 0, 0)
        [HideInInspector] _DirectionalSampleCount("Sample Count", Float) = 24
        [HideInInspector] _DirectionalShellPlane("Shell Plane", Vector) = (0, 0, 0, 0)
        [HideInInspector] _DirectionalVolumeTexture("Directional Volume", 2D) = "black" {}
        [HideInInspector] _RainMistColor("Rain Mist Color", Color) = (0, 0, 0, 1)
        [HideInInspector] _RainMistSettings("Rain Mist Density Height Start", Vector) = (0, 8, 2, 0)
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+20"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        ColorMask RGB

        Pass
        {
            Name "DirectionalVolumeIntegration"
            Blend One Zero
            ColorMask RGBA

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _LIGHT_COOKIES

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            #define DIRECTIONAL_VOLUME_MAXIMUM_SAMPLES 32
            #define DIRECTIONAL_VOLUME_MAXIMUM_SEGMENTS 33

            CBUFFER_START(UnityPerMaterial)
                half4 _ShaftColor;
                float _ShaftIntensity;
                float _SurfaceFadeDistance;
                float4 _DirectionalVolumeBounds;
                float4 _DirectionalMediumSettings;
                float _DirectionalSampleCount;
                float4 _DirectionalShellPlane;
            CBUFFER_END

            struct Attributes
            {
                uint vertexID : SV_VertexID;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            float3 VolumeSafeNormalize(float3 value)
            {
                return value * rsqrt(max(dot(value, value), 0.0000001));
            }

            float ToDeviceDepth(float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    return rawDepth;
                #else
                    return lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif
            }

            void ReconstructCameraRay(
                float2 uv,
                out float3 rayOriginWS,
                out float3 rayDirectionWS,
                out float sceneDistance,
                out float sceneViewDepth)
            {
                #if UNITY_REVERSED_Z
                    const float nearDeviceDepth = 1.0;
                    const float farDeviceDepth = 0.0;
                #else
                    const float nearDeviceDepth = UNITY_NEAR_CLIP_VALUE;
                    const float farDeviceDepth = 1.0;
                #endif

                float3 nearWS = ComputeWorldSpacePosition(
                    uv,
                    nearDeviceDepth,
                    UNITY_MATRIX_I_VP);
                float3 farWS = ComputeWorldSpacePosition(
                    uv,
                    farDeviceDepth,
                    UNITY_MATRIX_I_VP);
                rayOriginWS = nearWS;
                rayDirectionWS = VolumeSafeNormalize(farWS - nearWS);

                // Half-res centers can land exactly between full-res texels.
                // Choose the same floor-indexed source texel as the compositor,
                // then sample its center so GPU point-sampler ties cannot choose
                // a different depth row than the upsample plane prediction.
                float2 depthPixel = clamp(floor(uv * _CameraDepthTexture_TexelSize.zw),
                    0.0, _CameraDepthTexture_TexelSize.zw - 1.0);
                float2 depthUV = (depthPixel + 0.5) * _CameraDepthTexture_TexelSize.xy;
                float rawSceneDepth = SampleSceneDepth(depthUV, sampler_PointClamp);
                float3 sceneWS = ComputeWorldSpacePosition(
                    uv,
                    ToDeviceDepth(rawSceneDepth),
                    UNITY_MATRIX_I_VP);
                sceneDistance = max(
                    dot(sceneWS - rayOriginWS, rayDirectionWS),
                    0.0);
                // Store axial view depth, not distance along a perspective ray,
                // so adjacent rays use the same metric during depth upsampling.
                sceneViewDepth = max(-TransformWorldToView(sceneWS).z, 0.0);
            }

            bool IntersectHeightVolume(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float sceneDistance,
                out float entry,
                out float exit)
            {
                if (abs(rayDirectionWS.y) <= 0.00001)
                {
                    entry = 0.0;
                    exit = 0.0;
                    return false;
                }

                float baseHeight = _DirectionalVolumeBounds.x;
                float topHeight = baseHeight + max(_DirectionalVolumeBounds.y, 0.001);
                float baseHit = (baseHeight - rayOriginWS.y) / rayDirectionWS.y;
                float topHit = (topHeight - rayOriginWS.y) / rayDirectionWS.y;
                entry = max(min(baseHit, topHit), 0.0);
                exit = min(max(baseHit, topHit), sceneDistance);
                return exit > entry + 0.0001;
            }

            float SampleMainShadow(float3 positionWS)
            {
                #if defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                float4 shadowCoord = TransformWorldToShadowCoord(positionWS);
                if (BEYOND_SHADOW_FAR(shadowCoord))
                {
                    return 1.0;
                }

                half4 shadowParams = GetMainLightShadowParams();
                // One comparison per world cell. Depth-aware reconstruction
                // smooths matching surfaces without mixing foreground/background.
                real attenuation = SAMPLE_TEXTURE2D_SHADOW(
                    _MainLightShadowmapTexture,
                    sampler_LinearClampCompare,
                    shadowCoord.xyz);
                attenuation = LerpWhiteTo(attenuation, shadowParams.x);
                return lerp(
                    attenuation,
                    1.0,
                    GetMainLightShadowFade(positionWS));
                #else
                return 1.0;
                #endif
            }

            float PhaseFunction(float anisotropy, float cosineTheta)
            {
                float g = clamp(anisotropy, -0.85, 0.85);
                float gSquared = g * g;
                float denominator = max(
                    1.0 + gSquared - 2.0 * g * cosineTheta,
                    0.0001);
                return (1.0 - gSquared) /
                    max(pow(denominator, 1.5), 0.0001);
            }

            float3 IntegrateDirectionalVolume(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float sceneDistance,
                float entry,
                float exit)
            {
                int sampleCount = clamp(
                    (int)round(_DirectionalSampleCount),
                    1,
                    DIRECTIONAL_VOLUME_MAXIMUM_SAMPLES);
                float safeExtinction = max(_DirectionalMediumSettings.x, 0.0);
                float transmittance = 1.0;
                float3 accumulated = 0.0;

                Light mainLight = GetMainLight();
                float3 lightDirection = VolumeSafeNormalize(mainLight.direction);
                float phase = PhaseFunction(
                    _DirectionalMediumSettings.y,
                    dot(rayDirectionWS, lightDirection));
                float baseHeight = _DirectionalVolumeBounds.x;
                float volumeHeight = max(_DirectionalVolumeBounds.y, 0.001);
                float pathLength = exit - entry;
                float3 planeNormal = _DirectionalShellPlane.xyz;
                float planeRate = dot(rayDirectionWS, planeNormal);
                float planeLengthSquared = dot(planeNormal, planeNormal);

                float firstSegmentLength;
                float regularSegmentLength;
                bool useWorldCells =
                    planeLengthSquared > 0.5 && abs(planeRate) > 0.0001;
                if (useWorldCells)
                {
                    float spacing = max(_DirectionalShellPlane.w, 0.02);
                    float entryCoordinate = dot(
                        rayOriginWS + rayDirectionWS * entry,
                        planeNormal);
                    float phaseInCell = entryCoordinate -
                        floor(entryCoordinate / spacing) * spacing;
                    float projectedToBoundary = planeRate >= 0.0
                        ? spacing - phaseInCell
                        : phaseInCell;
                    if (projectedToBoundary <= spacing * 0.0001)
                    {
                        projectedToBoundary = spacing;
                    }

                    firstSegmentLength = min(
                        projectedToBoundary / abs(planeRate),
                        pathLength);
                    regularSegmentLength = spacing / abs(planeRate);
                }
                else
                {
                    // Defensive fallback for an invalid plane contract. The C# path
                    // normally blends through the sun/view parallel singularity.
                    firstSegmentLength = pathLength /
                        max((float)sampleCount, 1.0);
                    regularSegmentLength = firstSegmentLength;
                }

                float currentDistance = entry;
                int segmentLimit = useWorldCells
                    ? min(sampleCount + 1, DIRECTIONAL_VOLUME_MAXIMUM_SEGMENTS)
                    : sampleCount;

                [loop]
                for (int segmentIndex = 0;
                     segmentIndex < DIRECTIONAL_VOLUME_MAXIMUM_SEGMENTS;
                     segmentIndex++)
                {
                    if (segmentIndex >= segmentLimit ||
                        currentDistance >= exit - 0.0001)
                    {
                        break;
                    }

                    float remainingLength = exit - currentDistance;
                    float segmentLength = min(
                        segmentIndex == 0
                            ? firstSegmentLength
                            : regularSegmentLength,
                        remainingLength);
                    if (segmentLength <= 0.0001)
                    {
                        break;
                    }

                    float distanceAlongRay = currentDistance +
                        segmentLength * 0.5;
                    float3 samplePositionWS =
                        rayOriginWS + rayDirectionWS * distanceAlongRay;
                    float3 visibility = SampleMainShadow(samplePositionWS).xxx;
                    #if defined(_LIGHT_COOKIES)
                        // The same world-projected cookie that shades opaque
                        // surfaces attenuates incident sunlight exactly once.
                        visibility *= SampleMainLightCookie(samplePositionWS);
                    #endif

                    float normalizedHeight = saturate(
                        (samplePositionWS.y - baseHeight) / volumeHeight);
                    float volumeEdgeFade =
                        smoothstep(0.0, 0.04, normalizedHeight) *
                        (1.0 - smoothstep(0.94, 1.0, normalizedHeight));
                    float surfaceFade = smoothstep(
                        0.0,
                        max(_SurfaceFadeDistance, 0.001),
                        sceneDistance - distanceAlongRay);
                    float segmentTransmittance = exp(
                        -safeExtinction * segmentLength);
                    float integratedSegment = safeExtinction > 0.00001
                        ? (1.0 - segmentTransmittance) / safeExtinction
                        : segmentLength;

                    accumulated += transmittance * visibility * phase *
                        volumeEdgeFade * surfaceFade * integratedSegment;
                    transmittance *= segmentTransmittance;
                    currentDistance += segmentLength;
                    if (transmittance < 0.001)
                    {
                        break;
                    }
                }

                return accumulated;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float2 uv = saturate(input.uv);
                float3 rayOriginWS;
                float3 rayDirectionWS;
                float sceneDistance;
                float sceneViewDepth;
                ReconstructCameraRay(
                    uv,
                    rayOriginWS,
                    rayDirectionWS,
                    sceneDistance,
                    sceneViewDepth);

                float entry;
                float exit;
                if (sceneDistance <= 0.0001 ||
                    !IntersectHeightVolume(
                        rayOriginWS,
                        rayDirectionWS,
                        sceneDistance,
                        entry,
                        exit))
                {
                    return half4(0.0, 0.0, 0.0, sceneViewDepth);
                }

                float3 scattering = IntegrateDirectionalVolume(
                    rayOriginWS,
                    rayDirectionWS,
                    sceneDistance,
                    entry,
                    exit);
                return half4(
                    _ShaftColor.rgb * (_ShaftIntensity * scattering),
                    sceneViewDepth);
            }
            ENDHLSL
        }

        Pass
        {
            Name "DirectionalVolumeComposite"
            Blend One One

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            TEXTURE2D_X(_DirectionalVolumeTexture);
            float4 _DirectionalVolumeTexture_TexelSize;

            struct Attributes
            {
                uint vertexID : SV_VertexID;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            float SceneViewDepth(float2 uv)
            {
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                #if UNITY_REVERSED_Z
                    float deviceDepth = rawDepth;
                #else
                    float deviceDepth = lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif
                float3 sceneWS = ComputeWorldSpacePosition(uv, deviceDepth, UNITY_MATRIX_I_VP);
                return max(-TransformWorldToView(sceneWS).z, 0.0);
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float2 uv = saturate(input.uv);
                float targetDepth = SceneViewDepth(uv);
                float2 samplePosition = uv * _DirectionalVolumeTexture_TexelSize.zw - 0.5;
                float2 firstPixel = floor(samplePosition);
                float2 blend = frac(samplePosition);
                float depthTolerance = max(0.05, targetDepth * 0.002);
                float2 depthPixelSize = _CameraDepthTexture_TexelSize.xy;
                float2 before = targetDepth - float2(
                    SceneViewDepth(saturate(uv - float2(depthPixelSize.x, 0.0))),
                    SceneViewDepth(saturate(uv - float2(0.0, depthPixelSize.y))));
                float2 after = float2(
                    SceneViewDepth(saturate(uv + float2(depthPixelSize.x, 0.0))),
                    SceneViewDepth(saturate(uv + float2(0.0, depthPixelSize.y)))) - targetDepth;
                // A continuous plane has matching one-sided depth slopes. A
                // silhouette does not: keep its original narrow rejection range.
                float2 planar = step(abs(after - before), depthTolerance.xx);
                float2 depthSlope = (before + after) * 0.5 * planar;
                float2 targetPixel = uv * _CameraDepthTexture_TexelSize.zw - 0.5;
                float3 weightedVolume = 0.0;
                float totalWeight = 0.0;
                [unroll]
                for (int y = 0; y < 2; y++)
                {
                    [unroll]
                    for (int x = 0; x < 2; x++)
                    {
                        float2 tapUV = (firstPixel + float2(x, y) + 0.5) *
                            _DirectionalVolumeTexture_TexelSize.xy;
                        half4 tap = SAMPLE_TEXTURE2D_X(
                            _DirectionalVolumeTexture, sampler_PointClamp, tapUV);
                        float bilinearWeight = (x == 0 ? 1.0 - blend.x : blend.x) *
                            (y == 0 ? 1.0 - blend.y : blend.y);
                        // Integration point-samples full-res depth. Predict the
                        // plane at that exact source texel, not the low-res center.
                        float2 sourcePixel = clamp(floor(tapUV * _CameraDepthTexture_TexelSize.zw),
                            0.0, _CameraDepthTexture_TexelSize.zw - 1.0);
                        float expectedDepth = targetDepth + dot(depthSlope, sourcePixel - targetPixel);
                        float depthWeight = saturate(1.0 - abs((float)tap.a - expectedDepth) /
                            depthTolerance);
                        float weight = bilinearWeight * depthWeight;
                        weightedVolume += tap.rgb * weight;
                        totalWeight += weight;
                    }
                }
                // A subpixel foreground object may have no half-res match.
                // Reject unrelated air behind it instead of leaking that light.
                return half4(weightedVolume / max(totalWeight, 0.00001), 0.0);
            }
            ENDHLSL
        }
        Pass
        {
            Name "RainMistComposite"
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex MistVert
            #pragma fragment MistFrag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            half4 _RainMistColor;
            float4 _RainMistSettings; // extinction per metre, height, clear near distance

            struct MistVaryings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            MistVaryings MistVert(uint vertexID : SV_VertexID)
            {
                MistVaryings output;
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = GetFullScreenTriangleVertexPosition(vertexID);
                output.uv = GetFullScreenTriangleTexCoord(vertexID);
                return output;
            }

            half4 MistFrag(MistVaryings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float2 uv = saturate(input.uv);
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                #if UNITY_REVERSED_Z
                    const float nearDepth = 1.0;
                    float deviceDepth = rawDepth;
                #else
                    const float nearDepth = UNITY_NEAR_CLIP_VALUE;
                    float deviceDepth = lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif
                // Near-plane origins support the game's orthographic camera as
                // well as perspective; depth clips mist against real surfaces.
                float3 originWS = ComputeWorldSpacePosition(uv, nearDepth, UNITY_MATRIX_I_VP);
                float3 sceneWS = ComputeWorldSpacePosition(uv, deviceDepth, UNITY_MATRIX_I_VP);
                float3 toSurface = sceneWS - originWS;
                float sceneDistance = length(toSurface);
                float3 rayDirection = toSurface / max(sceneDistance, 0.00001);
                float entry = max(_RainMistSettings.z, 0.0);
                float exit = sceneDistance;
                if (abs(rayDirection.y) > 0.00001)
                {
                    float baseHit = -originWS.y / rayDirection.y;
                    float topHit = (_RainMistSettings.y - originWS.y) / rayDirection.y;
                    entry = max(entry, min(baseHit, topHit));
                    exit = min(exit, max(baseHit, topHit));
                }
                else if (originWS.y < 0.0 || originWS.y > _RainMistSettings.y)
                    return 0;

                float pathLength = max(exit - entry, 0.0);
                half opacity = 1.0 - exp(-max(_RainMistSettings.x, 0.0) * pathLength);
                return half4(_RainMistColor.rgb, opacity);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
