Shader "Hidden/FantasySurvival/Character Silhouette Composite"
{
    Properties
    {
        _OutlineColor("Outline Color", Color) = (0.025, 0.025, 0.03, 1)
        _ArtPixelSize("Screen Pixels Per Art Cell", Range(1, 8)) = 3
        _CoverageThreshold("Mask Threshold", Range(0.05, 0.95)) = 0.35
        _InnerOverlapPixels("Inner Overlap (Screen Pixels)", Range(0, 3)) = 1
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+100"
        }

        Pass
        {
            Name "CharacterSilhouetteComposite"

            Blend SrcAlpha OneMinusSrcAlpha
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_CharacterSilhouetteMask);

            CBUFFER_START(UnityPerMaterial)
                half4 _OutlineColor;
                float _ArtPixelSize;
                float _CoverageThreshold;
                float _InnerOverlapPixels;
            CBUFFER_END

            struct Attributes
            {
                uint vertexID : SV_VertexID;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            half Occupancy(float2 cell, float2 gridSize)
            {
                float2 sampleUv = saturate((cell + 0.5) / gridSize);
                half mask = SAMPLE_TEXTURE2D(_CharacterSilhouetteMask, sampler_PointClamp, sampleUv).r;
                return step(_CoverageThreshold, mask);
            }

            half RawOccupancy(float2 uv)
            {
                half mask = SAMPLE_TEXTURE2D(
                    _CharacterSilhouetteMask,
                    sampler_PointClamp,
                    saturate(uv)).r;
                return step(_CoverageThreshold, mask);
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float artPixelSize = max(1.0, round(_ArtPixelSize));
                float2 gridSize = max(floor(_ScreenParams.xy / artPixelSize), 1.0);
                float2 cell = floor(saturate(input.uv) * gridSize);

                half center = Occupancy(cell, gridSize);
                half neighbor00 = Occupancy(cell + float2(-1, -1), gridSize);
                half neighbor10 = Occupancy(cell + float2( 0, -1), gridSize);
                half neighbor20 = Occupancy(cell + float2( 1, -1), gridSize);
                half neighbor01 = Occupancy(cell + float2(-1,  0), gridSize);
                half neighbor21 = Occupancy(cell + float2( 1,  0), gridSize);
                half neighbor02 = Occupancy(cell + float2(-1,  1), gridSize);
                half neighbor12 = Occupancy(cell + float2( 0,  1), gridSize);
                half neighbor22 = Occupancy(cell + float2( 1,  1), gridSize);

                half nearest = max(
                    max(max(neighbor00, neighbor10), max(neighbor20, neighbor01)),
                    max(max(neighbor21, neighbor02), max(neighbor12, neighbor22)));

                half outerSilhouette = nearest * (1.0h - center);
                half cellDilated = max(center, nearest);
                if (cellDilated < 0.5h)
                {
                    return half4(_OutlineColor.rgb, 0);
                }

                // A center-sampled art cell can be classified as occupied even when
                // the original mesh ends before the cell boundary. Fill that exposed
                // part of the boundary cell, then cover one full-resolution pixel of
                // the mesh itself so the stepped outline and body cannot separate.
                float overlapPixels = max(0.0, round(_InnerOverlapPixels));
                if (overlapPixels < 0.5)
                {
                    return half4(_OutlineColor.rgb, _OutlineColor.a * outerSilhouette);
                }

                float2 overlapUv = overlapPixels / max(_ScreenParams.xy, 1.0);
                half rawInterior = RawOccupancy(input.uv);
                rawInterior *= RawOccupancy(input.uv + float2(-overlapUv.x, 0));
                rawInterior *= RawOccupancy(input.uv + float2( overlapUv.x, 0));
                rawInterior *= RawOccupancy(input.uv + float2(0, -overlapUv.y));
                rawInterior *= RawOccupancy(input.uv + float2(0,  overlapUv.y));

                half silhouette = cellDilated * (1.0h - rawInterior);
                return half4(_OutlineColor.rgb, _OutlineColor.a * silhouette);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
