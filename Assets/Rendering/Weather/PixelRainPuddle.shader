Shader "FantasySurvival/Weather/PixelRainPuddle"
{
    Properties
    {
        _WaterColor("Water Color", Color) = (0.055, 0.14, 0.20, 0.52)
        _EdgeColor("Pixel Edge Color", Color) = (0.22, 0.46, 0.58, 0.72)
        _RippleColor("Rain Ripple Color", Color) = (1.0, 1.0, 1.0, 1.0)
        _PixelGrid("Puddle Pixel Grid", Vector) = (48, 24, 0, 0)
        _WorldPixelSize("Ripple World Pixel Size", Range(0.005, 0.12)) = 0.01
        _LightingBands("Lighting Bands", Range(2, 12)) = 6
        _RippleInterval("Ripple Interval", Range(0.6, 3.0)) = 3.0
        _RippleDuration("Ripple Duration", Range(0.2, 1.5)) = 0.72
        _RippleMaxRadius("Ripple Maximum Radius", Range(0.08, 0.8)) = 0.38
        _RippleThickness("Ripple Thickness", Range(0.001, 0.12)) = 0.005
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "Queue" = "Transparent+20"
            "RenderType" = "Transparent"
        }

        Pass
        {
            Name "PixelRainPuddle"
            Tags { "LightMode" = "UniversalForward" }

            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _WaterColor;
                half4 _EdgeColor;
                half4 _RippleColor;
                float4 _PixelGrid;
                float _WorldPixelSize;
                float _LightingBands;
                float _RippleInterval;
                float _RippleDuration;
                float _RippleMaxRadius;
                float _RippleThickness;
            CBUFFER_END

            float _FantasyRainIntensity;
            float _FantasyRainVisualTime;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                UNITY_VERTEX_OUTPUT_STEREO
            };

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

            float2 QuantizePuddleUv(float2 uv)
            {
                float2 grid = max(round(_PixelGrid.xy), float2(4.0, 4.0));
                return (floor(saturate(uv) * grid) + 0.5) / grid;
            }

            float EvaluatePuddleMask(float2 uv, out float edge)
            {
                float2 pixelUv = QuantizePuddleUv(uv);
                float2 centered = pixelUv - 0.5;
                float angle = atan2(centered.y, centered.x);
                float irregularEdge =
                    0.455 +
                    sin(angle * 3.0 + 0.7) * 0.022 +
                    sin(angle * 7.0 - 1.3) * 0.012;
                float radius = length(centered);
                float2 grid = max(round(_PixelGrid.xy), float2(4.0, 4.0));
                float edgeWidth = max(1.0 / grid.x, 1.0 / grid.y) * 1.35;
                float mask = step(radius, irregularEdge);
                float inner = step(radius, irregularEdge - edgeWidth);
                edge = mask * (1.0 - inner);
                return mask;
            }

            float EvaluateRainRipple(
                float3 positionWS,
                float2 objectSeed,
                float channel)
            {
                float interval = max(_RippleInterval, 0.01);
                float duration = min(max(_RippleDuration, 0.01), interval);
                float channelTime =
                    max(_FantasyRainVisualTime, 0.0) +
                    channel * interval * 0.25;
                float cycle = floor(channelTime / interval);
                float ageSeconds = channelTime - cycle * interval;
                float active = 1.0 - step(duration, ageSeconds);
                float age = saturate(ageSeconds / duration);

                float2 random = Hash22(
                    float2(cycle + channel * 17.31, dot(objectSeed, float2(0.37, 0.73))));
                float angle = random.x * 6.28318530718;
                float centerRadius = sqrt(random.y) * 0.25;
                float2 centerUv = 0.5 + float2(cos(angle), sin(angle)) * centerRadius;
                float3 centerWS = TransformObjectToWorld(
                    float3(centerUv.x - 0.5, 0.0, centerUv.y - 0.5));

                float pixelSize = max(_WorldPixelSize, 0.001);
                float3 pixelPositionWS =
                    floor(positionWS / pixelSize + 0.5) * pixelSize;
                float radius = age * max(_RippleMaxRadius, pixelSize);
                float ringDistance = abs(distance(pixelPositionWS, centerWS) - radius);
                float ring = 1.0 - step(max(_RippleThickness, pixelSize * 0.5), ringDistance);
                float lifetimeFade =
                    smoothstep(0.0, 0.08, age) *
                    (1.0 - smoothstep(0.58, 1.0, age));
                return ring * lifetimeFade * active;
            }

            half3 EvaluateSteppedLighting(float3 positionWS, half3 normalWS)
            {
                half3 normal = normalize(normalWS);
                Light mainLight = GetMainLight(TransformWorldToShadowCoord(positionWS));
                half direct = saturate(dot(normal, mainLight.direction)) *
                    mainLight.distanceAttenuation * mainLight.shadowAttenuation;
                half3 lighting = max(
                    SampleSH(normal) + mainLight.color * direct,
                    half3(0.0, 0.0, 0.0));
                half brightness = max(lighting.r, max(lighting.g, lighting.b));
                half bands = max(round(_LightingBands), 2.0);
                half steppedBrightness =
                    floor(saturate(brightness) * bands + 0.5) / bands;
                return brightness > 0.0001
                    ? lighting * (steppedBrightness / brightness)
                    : half3(0.0, 0.0, 0.0);
            }

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                VertexPositionInputs positionInputs =
                    GetVertexPositionInputs(input.positionOS.xyz);
                output.positionHCS = positionInputs.positionCS;
                output.positionWS = positionInputs.positionWS;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.uv = input.uv;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float edge;
                float puddleMask = EvaluatePuddleMask(input.uv, edge);
                clip(puddleMask - 0.5);

                float3 objectCenterWS = TransformObjectToWorld(float3(0.0, 0.0, 0.0));
                float2 objectSeed = objectCenterWS.xz;
                float ripple = 0.0;
                [unroll]
                for (int channel = 0; channel < 4; channel++)
                {
                    ripple = max(
                        ripple,
                        EvaluateRainRipple(input.positionWS, objectSeed, (float)channel));
                }
                ripple *= saturate(_FantasyRainIntensity);

                half3 lighting = EvaluateSteppedLighting(
                    input.positionWS,
                    input.normalWS);
                half edgeBlend = saturate(edge * _EdgeColor.a);
                half3 surfaceColor = lerp(
                    _WaterColor.rgb,
                    _EdgeColor.rgb,
                    edgeBlend);
                surfaceColor = lerp(
                    surfaceColor,
                    _RippleColor.rgb,
                    saturate(ripple * _RippleColor.a));
                surfaceColor *= lighting;

                half alpha = saturate(
                    _WaterColor.a +
                    edge * _EdgeColor.a * 0.22 +
                    ripple * _RippleColor.a * 0.35);
                return half4(surfaceColor, alpha);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
