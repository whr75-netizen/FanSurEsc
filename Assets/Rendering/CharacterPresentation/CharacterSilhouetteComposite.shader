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

        HLSLINCLUDE
        #pragma target 3.5

        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        TEXTURE2D(_CharacterSilhouetteMask);
        TEXTURE2D(_CharacterSilhouetteQuantizedMask);

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
        };

        Varyings Vert(Attributes input)
        {
            Varyings output;
            output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
            return output;
        }

        bool PixelInBounds(int2 pixel)
        {
            int2 dimensions = int2(_ScaledScreenParams.xy);
            return all(pixel >= int2(0, 0)) && all(pixel < dimensions);
        }

        half LoadRawOccupancy(int2 pixel)
        {
            if (!PixelInBounds(pixel))
            {
                return 0;
            }

            half mask = LOAD_TEXTURE2D(_CharacterSilhouetteMask, pixel).r;
            return step(_CoverageThreshold, mask);
        }

        half LoadSeed(int2 pixel)
        {
            if (!PixelInBounds(pixel))
            {
                return 0;
            }

            return LOAD_TEXTURE2D(_CharacterSilhouetteMask, pixel).g;
        }

        half LoadQuantizedOccupancy(int2 pixel)
        {
            if (!PixelInBounds(pixel))
            {
                return 0;
            }

            half mask = LOAD_TEXTURE2D(_CharacterSilhouetteQuantizedMask, pixel).r;
            return step(_CoverageThreshold, mask);
        }

        half4 FragExpand(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int artPixelSize = clamp((int)round(_ArtPixelSize), 1, 8);
            int firstOffset = -(artPixelSize >> 1);
            half occupied = 0;

            [loop]
            for (int y = 0; y < 8; y++)
            {
                if (y >= artPixelSize)
                {
                    break;
                }

                [loop]
                for (int x = 0; x < 8; x++)
                {
                    if (x >= artPixelSize)
                    {
                        break;
                    }

                    int2 expansionOffset = int2(
                        firstOffset + x,
                        firstOffset + y);
                    occupied = max(
                        occupied,
                        LoadSeed(pixel - expansionOffset));
                }
            }

            return half4(occupied, 0, 0, 1);
        }

        half4 FragComposite(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int artPixelSize = clamp((int)round(_ArtPixelSize), 1, 8);

            half center = LoadQuantizedOccupancy(pixel);
            half neighbor00 = LoadQuantizedOccupancy(
                pixel + int2(-artPixelSize, -artPixelSize));
            half neighbor10 = LoadQuantizedOccupancy(
                pixel + int2(0, -artPixelSize));
            half neighbor20 = LoadQuantizedOccupancy(
                pixel + int2(artPixelSize, -artPixelSize));
            half neighbor01 = LoadQuantizedOccupancy(
                pixel + int2(-artPixelSize, 0));
            half neighbor21 = LoadQuantizedOccupancy(
                pixel + int2(artPixelSize, 0));
            half neighbor02 = LoadQuantizedOccupancy(
                pixel + int2(-artPixelSize, artPixelSize));
            half neighbor12 = LoadQuantizedOccupancy(
                pixel + int2(0, artPixelSize));
            half neighbor22 = LoadQuantizedOccupancy(
                pixel + int2(artPixelSize, artPixelSize));

            half nearest = max(
                max(max(neighbor00, neighbor10), max(neighbor20, neighbor01)),
                max(max(neighbor21, neighbor02), max(neighbor12, neighbor22)));

            half outerSilhouette = nearest * (1.0h - center);
            half cellDilated = max(center, nearest);
            if (cellDilated < 0.5h)
            {
                return half4(_OutlineColor.rgb, 0);
            }

            // Keep the existing one-native-pixel inward overlap so a stepped cell
            // cannot expose a gap between the full-resolution body and its outline.
            int overlapPixels = max(0, (int)round(_InnerOverlapPixels));
            if (overlapPixels < 1)
            {
                return half4(_OutlineColor.rgb, _OutlineColor.a * outerSilhouette);
            }

            half rawInterior = LoadRawOccupancy(pixel);
            rawInterior *= LoadRawOccupancy(pixel + int2(-overlapPixels, 0));
            rawInterior *= LoadRawOccupancy(pixel + int2(overlapPixels, 0));
            rawInterior *= LoadRawOccupancy(pixel + int2(0, -overlapPixels));
            rawInterior *= LoadRawOccupancy(pixel + int2(0, overlapPixels));

            half silhouette = cellDilated * (1.0h - rawInterior);
            return half4(_OutlineColor.rgb, _OutlineColor.a * silhouette);
        }
        ENDHLSL

        Pass
        {
            Name "CharacterSilhouetteExpand"

            Blend One Zero
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragExpand
            ENDHLSL
        }

        Pass
        {
            Name "CharacterSilhouetteComposite"

            Blend SrcAlpha OneMinusSrcAlpha
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragComposite
            ENDHLSL
        }
    }

    FallBack Off
}
