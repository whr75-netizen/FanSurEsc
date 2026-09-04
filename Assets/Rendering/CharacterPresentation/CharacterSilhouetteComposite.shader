Shader "Hidden/FantasySurvival/Character Silhouette Composite"
{
    Properties
    {
        _OutlineColor("Outline Color", Color) = (0.025, 0.025, 0.03, 1)
        _ArtPixelSize("Screen Pixels Per Art Cell", Range(1, 8)) = 3
        _ScreenPixelSize("Screen-Pixel Body Cell Size", Range(1, 12)) = 5
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
        TEXTURE2D(_CharacterSourceColorInput);
        TEXTURE2D(_CharacterSourceColor);
        TEXTURE2D(_CharacterScreenPixelMask);
        TEXTURE2D(_CharacterScreenPixelResolved);
        TEXTURE2D(_CharacterScreenPixelOutlineDepth);
        TEXTURE2D(_CharacterSceneDepth);

        CBUFFER_START(UnityPerMaterial)
            half4 _OutlineColor;
            float _ArtPixelSize;
            float _ScreenPixelSize;
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

        half4 FragCopySource(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            return LOAD_TEXTURE2D(_CharacterSourceColorInput, pixel);
        }

        half4 FragResolveScreenPixel(Varyings input) : SV_Target
        {
            int2 cellIndex = int2(floor(input.positionCS.xy));
            int screenPixelSize = clamp((int)round(_ScreenPixelSize), 1, 12);
            int2 cellOrigin = cellIndex * screenPixelSize;

            uint sourceWidth;
            uint sourceHeight;
            _CharacterSourceColor.GetDimensions(sourceWidth, sourceHeight);
            int2 sourceDimensions = int2(sourceWidth, sourceHeight);

            // Choose only a visible character fragment. This is deliberately
            // different from snapping UVs: the sample has already passed the
            // material, lighting, shadow, and camera visibility pipeline.
            half3 representativeColor = 0.0h;
            float nearestEyeDepth = 65504.0;
            bool foundVisibleCharacter = false;

            [loop]
            for (int y = 0; y < 12; y++)
            {
                if (y >= screenPixelSize)
                {
                    break;
                }

                [loop]
                for (int x = 0; x < 12; x++)
                {
                    if (x >= screenPixelSize)
                    {
                        break;
                    }

                    int2 sourcePixel = cellOrigin + int2(x, y);
                    if (any(sourcePixel < int2(0, 0)) ||
                        any(sourcePixel >= sourceDimensions))
                    {
                        continue;
                    }

                    half2 maskSample = LOAD_TEXTURE2D(
                        _CharacterScreenPixelMask,
                        sourcePixel).rg;
                    if (maskSample.r < _CoverageThreshold ||
                        maskSample.g <= 0.0h)
                    {
                        continue;
                    }

                    float eyeDepth = (float)maskSample.g;
                    if (!foundVisibleCharacter || eyeDepth < nearestEyeDepth)
                    {
                        nearestEyeDepth = eyeDepth;
                        representativeColor = LOAD_TEXTURE2D(
                            _CharacterSourceColor,
                            sourcePixel).rgb;
                        foundVisibleCharacter = true;
                    }
                }
            }

            if (!foundVisibleCharacter)
            {
                return 0.0h;
            }

            // Alpha carries linear eye depth, not transparency. Zero remains
            // the unoccupied-cell sentinel because visible eye depth is > 0.
            return half4(
                representativeColor,
                (half)nearestEyeDepth);
        }

        bool ScreenCellInBounds(int2 cell)
        {
            uint width;
            uint height;
            _CharacterScreenPixelResolved.GetDimensions(width, height);
            return all(cell >= int2(0, 0)) &&
                all(cell < int2(width, height));
        }

        half4 LoadScreenPixelCell(int2 cell)
        {
            if (!ScreenCellInBounds(cell))
            {
                return 0.0h;
            }

            return LOAD_TEXTURE2D(_CharacterScreenPixelResolved, cell);
        }

        half4 FragResolveScreenPixelOutline(Varyings input) : SV_Target
        {
            int2 cell = int2(floor(input.positionCS.xy));
            if (LoadScreenPixelCell(cell).a > 0.0001h)
            {
                return 0.0h;
            }

            float nearestEyeDepth = 65504.0;
            bool foundNeighbor = false;

            [unroll]
            for (int y = -1; y <= 1; y++)
            {
                [unroll]
                for (int x = -1; x <= 1; x++)
                {
                    if (x == 0 && y == 0)
                    {
                        continue;
                    }

                    float neighborDepth =
                        (float)LoadScreenPixelCell(cell + int2(x, y)).a;
                    if (neighborDepth > 0.0001 &&
                        (!foundNeighbor || neighborDepth < nearestEyeDepth))
                    {
                        nearestEyeDepth = neighborDepth;
                        foundNeighbor = true;
                    }
                }
            }

            return foundNeighbor
                ? half4((half)nearestEyeDepth, 0.0h, 0.0h, 1.0h)
                : 0.0h;
        }

        half4 FragCompositeScreenPixel(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int screenPixelSize = clamp((int)round(_ScreenPixelSize), 1, 12);
            int2 cellIndex = pixel / screenPixelSize;

            uint resolvedWidth;
            uint resolvedHeight;
            _CharacterScreenPixelResolved.GetDimensions(
                resolvedWidth,
                resolvedHeight);
            cellIndex = clamp(
                cellIndex,
                int2(0, 0),
                int2(resolvedWidth, resolvedHeight) - 1);

            half4 resolved = LOAD_TEXTURE2D(
                _CharacterScreenPixelResolved,
                cellIndex);
            float bodyEyeDepth = (float)resolved.a;
            float outlineEyeDepth = (float)LOAD_TEXTURE2D(
                _CharacterScreenPixelOutlineDepth,
                cellIndex).r;
            bool isBody = bodyEyeDepth > 0.0001;
            float characterEyeDepth = isBody
                ? bodyEyeDepth
                : outlineEyeDepth;
            clip(characterEyeDepth - 0.0001);

            float sceneRawDepth = LOAD_TEXTURE2D(
                _CharacterSceneDepth,
                pixel).r;
            float sceneEyeDepth = LinearEyeDepth(
                sceneRawDepth,
                _ZBufferParams);
            float depthTolerance = max(0.002, characterEyeDepth * 0.0005);

            // A coarse cell may extend beyond the original triangle edge, but
            // it must never paint across geometry that is actually nearer.
            clip(sceneEyeDepth + depthTolerance - characterEyeDepth);
            return isBody
                ? half4(resolved.rgb, 1.0h)
                : half4(_OutlineColor.rgb, 1.0h);
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


        Pass
        {
            Name "CharacterScreenPixelSourceCopy"

            Blend One Zero
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragCopySource
            ENDHLSL
        }

        Pass
        {
            Name "CharacterScreenPixelResolve"

            Blend One Zero
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragResolveScreenPixel
            ENDHLSL
        }

        Pass
        {
            Name "CharacterScreenPixelSingleOutline"

            Blend One Zero
            ColorMask R
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragResolveScreenPixelOutline
            ENDHLSL
        }

        Pass
        {
            Name "CharacterScreenPixelComposite"

            Blend One Zero
            ColorMask RGB
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragCompositeScreenPixel
            ENDHLSL
        }
    }

    FallBack Off
}
