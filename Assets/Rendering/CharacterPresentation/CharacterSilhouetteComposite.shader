Shader "Hidden/FantasySurvival/Character Silhouette Composite"
{
    Properties
    {
        _OutlineColor("Outline Color", Color) = (0.025, 0.025, 0.03, 1)
        _ArtPixelSize("Screen Pixels Per Art Cell", Range(1, 8)) = 3
        _ScreenPixelSize("Screen-Pixel Body Cell Size", Range(1, 12)) = 5
        _CoverageThreshold("Mask Threshold", Range(0.05, 0.95)) = 0.35
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
        TEXTURE2D(_CharacterCellSourceColor);
        TEXTURE2D(_CharacterCellSourceMeta);

        CBUFFER_START(UnityPerMaterial)
            half4 _OutlineColor;
            float _ArtPixelSize;
            float _ScreenPixelSize;
            float _CoverageThreshold;
            float _CharacterCellSearchSize;
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

        int LoadVisibleGroup(int2 pixel)
        {
            if (!PixelInBounds(pixel))
                return 0;
            // A sub-cell eye or eyebrow is real artwork, not an error to erase
            // with the cell's majority color. Use its actual visible boundary.
            half4 raw = LOAD_TEXTURE2D(_CharacterSilhouetteMask, pixel);
            if (raw.r >= _CoverageThreshold)
                return (int)round(raw.g * 255.0h);
            return (int)round(LOAD_TEXTURE2D(_CharacterSilhouetteQuantizedMask, pixel).g * 255.0h);
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

        bool IsSourceOccluded(int2 sourcePixel, int2 destinationPixel)
        {
            float sourceRawDepth = LOAD_TEXTURE2D(_CharacterSceneDepth, sourcePixel).r;
            float sceneRawDepth = LOAD_TEXTURE2D(_CharacterSceneDepth, destinationPixel).r;
            float sourceDepth = unity_OrthoParams.w > 0.5 ?
                LinearDepthToEyeDepth(sourceRawDepth) : LinearEyeDepth(sourceRawDepth, _ZBufferParams);
            float sceneDepth = unity_OrthoParams.w > 0.5 ?
                LinearDepthToEyeDepth(sceneRawDepth) : LinearEyeDepth(sceneRawDepth, _ZBufferParams);
            float depthTolerance = max(0.002, sourceDepth * 0.0005);
            return sceneDepth + depthTolerance < sourceDepth;
        }

        half4 FragExpand(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int artPixelSize = clamp((int)round(_ArtPixelSize), 1, 8);
            int searchRadius = artPixelSize - 1;
            int searchSize = searchRadius * 2 + 1;
            // Each group votes by actual visible area, not by its numeric ID.
            // Retain a source coordinate, not an averaged color: correction
            // pixels must inherit this part's real texture and spatial lighting.
            int counts[5] = { 0, 0, 0, 0, 0 };
            float distances[5] = { 1e9, 1e9, 1e9, 1e9, 1e9 };
            int2 sources[5];
            [unroll]
            for (int group = 0; group < 5; group++)
                sources[group] = pixel;

            [loop]
            for (int y = 0; y < 15; y++)
            {
                if (y >= searchSize)
                {
                    break;
                }

                [loop]
                for (int x = 0; x < 15; x++)
                {
                    if (x >= searchSize)
                    {
                        break;
                    }

                    int2 sourcePixel = pixel + int2(x - searchRadius, y - searchRadius);
                    if (!PixelInBounds(sourcePixel))
                        continue;
                    half4 raw = LOAD_TEXTURE2D(_CharacterSilhouetteMask, sourcePixel);
                    if (raw.r < _CoverageThreshold)
                        continue;

                    int2 cellMinimum = sourcePixel - int2(round(raw.ba * 255.0h));
                    if (any(pixel < cellMinimum) || any(pixel >= cellMinimum + artPixelSize))
                        continue;

                    int group = clamp((int)round(raw.g * 255.0h), 0, 4);
                    counts[group]++;
                    float2 fromCenter = sourcePixel -
                        (cellMinimum + (artPixelSize - 1) * 0.5);
                    float distanceSquared = dot(fromCenter, fromCenter);
                    if (distanceSquared < distances[group])
                    {
                        distances[group] = distanceSquared;
                        sources[group] = sourcePixel;
                    }
                }
            }

            int winner = 0;
            [unroll]
            for (int candidate = 1; candidate < 5; candidate++)
            {
                if (counts[candidate] > counts[winner] ||
                    (counts[candidate] == counts[winner] &&
                        distances[candidate] < distances[winner]))
                    winner = candidate;
            }

            if (counts[winner] == 0)
                return 0;

            // Visibility is part of the resolved mask, BEFORE extracting ink.
            // Clipping only the final line punches holes into an already built
            // ring at walls and grazing floor views instead of tracing its edge.
            half rawCoverage = LOAD_TEXTURE2D(_CharacterSilhouetteMask, pixel).r;
            if (rawCoverage < _CoverageThreshold && IsSourceOccluded(sources[winner], pixel))
                return 0;

            // Coverage remains conservative: no already-rendered rounded body
            // may protrude past the final stepped edge. Its extra area is COLOR,
            // not a full-cell black band. Offset encoding is exact in RGBA8.
            int2 sourceOffset = sources[winner] - pixel + searchRadius;
            return half4(1, winner / 255.0h, sourceOffset / 255.0h);
        }

        bool HasInkBoundary(int2 pixel, int centerGroup)
        {
            // Four-connected, ONE native texel. Art-cell size controls the
            // staircase cadence, never the width of the ink. Diagonal erosion
            // and whole-cell group bands blackened narrow eyes, wrists and hair.
            const int2 offsets[4] = {
                int2(-1, 0), int2(1, 0), int2(0, -1), int2(0, 1)
            };
            [unroll]
            for (int index = 0; index < 4; index++)
            {
                int2 neighbor = pixel + offsets[index];
                if (LoadQuantizedOccupancy(neighbor) < 0.5h)
                    return true;

                int neighborGroup = LoadVisibleGroup(neighbor);
                // Group ID owns a shared stroke on ONE side only. It does not
                // choose which surface occupies the cell (area voting does).
                if (neighborGroup > 0 && neighborGroup < centerGroup)
                    return true;
            }
            return false;
        }

        half4 FragComposite(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int artPixelSize = clamp((int)round(_ArtPixelSize), 1, 8);

            half4 cell = LOAD_TEXTURE2D(_CharacterSilhouetteQuantizedMask, pixel);
            if (cell.r < _CoverageThreshold)
                return 0;

            int2 sourcePixel = pixel + int2(round(cell.ba * 255.0h)) - (artPixelSize - 1);
            half4 raw = LOAD_TEXTURE2D(_CharacterSilhouetteMask, pixel);
            bool hasOriginalSurface = raw.r >= _CoverageThreshold;
            int group = (int)round((hasOriginalSurface ? raw.g : cell.g) * 255.0h);

            if (HasInkBoundary(pixel, group))
                return half4(_OutlineColor.rgb, _OutlineColor.a);

            // Preserve all native interior pixels. Only the boundary correction
            // band uses the winning part's visible, already-lit source color.
            return hasOriginalSurface ? half4(0, 0, 0, 0) :
                half4(LOAD_TEXTURE2D(_CharacterSourceColor, sourcePixel).rgb, 1);
        }

        half4 FragCopySource(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            return LOAD_TEXTURE2D(_CharacterSourceColorInput, pixel);
        }

        half4 FragResolveScreenPixel(Varyings input) : SV_Target
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            int screenPixelSize = clamp((int)round(_ScreenPixelSize), 1, 12);
            int firstOffset = -(screenPixelSize >> 1);

            uint sourceWidth;
            uint sourceHeight;
            _CharacterSourceColor.GetDimensions(sourceWidth, sourceHeight);
            int2 sourceDimensions = int2(sourceWidth, sourceHeight);

            // ScreenPixelMask contains one source point per cell, aligned to
            // each subject's presentation root. Expand that point here instead
            // of repartitioning the visible body with a viewport-fixed grid.
            // Rigid character motion therefore translates a stable color cell;
            // only actual surface deformation can change its source sample.
            half3 representativeColor = 0.0h;
            float nearestEyeDepth = 65504.0;
            bool foundVisibleSeed = false;

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

                    int2 expansionOffset = int2(
                        firstOffset + x,
                        firstOffset + y);
                    int2 sourcePixel = pixel - expansionOffset;
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
                    if (!foundVisibleSeed || eyeDepth < nearestEyeDepth)
                    {
                        nearestEyeDepth = eyeDepth;
                        representativeColor = LOAD_TEXTURE2D(
                            _CharacterSourceColor,
                            sourcePixel).rgb;
                        foundVisibleSeed = true;
                    }
                }
            }

            if (!foundVisibleSeed)
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
            int2 pixel = int2(floor(input.positionCS.xy));
            int screenPixelSize = clamp((int)round(_ScreenPixelSize), 1, 12);
            if (LoadScreenPixelCell(pixel).a > 0.0001h)
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
                        (float)LoadScreenPixelCell(
                            pixel + int2(x, y) * screenPixelSize).a;
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
            half4 resolved = LOAD_TEXTURE2D(
                _CharacterScreenPixelResolved,
                pixel);
            float bodyEyeDepth = (float)resolved.a;
            float outlineEyeDepth = (float)LOAD_TEXTURE2D(
                _CharacterScreenPixelOutlineDepth,
                pixel).r;
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
        struct PixelCellSample
        {
            float4 colorDepth;
            int2 seed;
            int subject;
            int group;
            int size;
        };

        bool IsPixelCellVisibleAt(PixelCellSample cell, int2 center)
        {
            if (!PixelInBounds(center))
                return false;
            float rawDepth = LOAD_TEXTURE2D(_CharacterSceneDepth, center).r;
            float worldDepth = unity_OrthoParams.w > 0.5 ?
                LinearDepthToEyeDepth(rawDepth) : LinearEyeDepth(rawDepth, _ZBufferParams);
            float tolerance = max(0.002, cell.colorDepth.a * 0.0005);
            return cell.colorDepth.a > 0.0 && worldDepth + tolerance >= cell.colorDepth.a;
        }

        PixelCellSample ReadCellSeed(int2 seed)
        {
            PixelCellSample cell = (PixelCellSample)0;
            cell.seed = seed;
            if (!PixelInBounds(seed))
                return cell;
            float4 meta = LOAD_TEXTURE2D(_CharacterCellSourceMeta, seed);
            cell.subject = (int)round(meta.r * 255.0) + (int)round(meta.a * 255.0) * 256;
            if (cell.subject == 0)
                return cell;
            cell.group = (int)round(meta.g * 255.0);
            cell.size = clamp((int)round(meta.b * 255.0), 1, 8);
            cell.colorDepth = LOAD_TEXTURE2D(_CharacterCellSourceColor, seed);

            // The WHOLE cell takes its visibility from the same center sample.
            // Native per-fragment depth cuts would split it back into teeth.
            if (!IsPixelCellVisibleAt(cell, seed))
                cell.subject = 0;
            return cell;
        }

        PixelCellSample ResolvePixelCell(int2 pixel)
        {
            PixelCellSample best = (PixelCellSample)0;
            int searchSize = clamp((int)round(_CharacterCellSearchSize), 1, 8);
            int first = -(searchSize - 1 - (searchSize >> 1));
            [loop]
            for (int y = 0; y < searchSize; y++)
            {
                [loop]
                for (int x = 0; x < searchSize; x++)
                {
                    PixelCellSample candidate = ReadCellSeed(pixel + int2(first + x, first + y));
                    if (candidate.subject == 0)
                        continue;
                    int2 minimum = candidate.seed - (candidate.size >> 1);
                    if (any(pixel < minimum) || any(pixel >= minimum + candidate.size))
                        continue;
                    if (best.subject == 0 || candidate.colorDepth.a < best.colorDepth.a ||
                        (candidate.colorDepth.a == best.colorDepth.a && candidate.subject < best.subject))
                        best = candidate;
                }
            }
            // No center hit means EMPTY. No occupancy dilation or native body
            // survives underneath this result: its normal pass is excluded.
            return best;
        }

        PixelCellSample ResolveOuterPixelCell(int2 pixel)
        {
            PixelCellSample best = (PixelCellSample)0;
            int searchSize = clamp((int)round(_CharacterCellSearchSize), 1, 8);
            int first = -(searchSize - 1 - (searchSize >> 1)) - searchSize;
            // One logical cell in each of the eight directions. Search source
            // seeds, not the outline output, so a ring can never grow recursively.
            [loop]
            for (int y = 0; y < searchSize * 3; y++)
            {
                [loop]
                for (int x = 0; x < searchSize * 3; x++)
                {
                    PixelCellSample candidate = ReadCellSeed(pixel + int2(first + x, first + y));
                    if (candidate.subject == 0)
                        continue;
                    int2 cellOffset = int2(floor(
                        (float2(pixel - candidate.seed) + (candidate.size >> 1)) / candidate.size));
                    if (max(abs(cellOffset.x), abs(cellOffset.y)) != 1)
                        continue;
                    int2 outlineCenter = candidate.seed + cellOffset * candidate.size;
                    // Visibility of the supplying body is not enough: the NEW
                    // outer cell must also stay behind nearer world geometry.
                    if (!IsPixelCellVisibleAt(candidate, outlineCenter))
                        continue;
                    if (best.subject == 0 || candidate.colorDepth.a < best.colorDepth.a ||
                        (candidate.colorDepth.a == best.colorDepth.a && candidate.subject < best.subject))
                        best = candidate;
                }
            }
            return best;
        }

        bool IsPixelCellInternalInk(PixelCellSample center)
        {
            const int2 neighbors[4] = {int2(-1, 0), int2(1, 0), int2(0, -1), int2(0, 1)};
            [unroll]
            for (int i = 0; i < 4; i++)
            {
                PixelCellSample neighbor = ReadCellSeed(center.seed + neighbors[i] * center.size);
                // Part boundaries are separate from the exterior silhouette.
                // An EMPTY neighbor must never turn a hand/body cell into ink.
                if (neighbor.subject == center.subject && neighbor.size == center.size &&
                    neighbor.group > 0 && neighbor.group < center.group)
                    return true;
            }
            return false;
        }

        struct PixelCellOutput
        {
            half4 color : SV_Target;
            float resolvedDepth : SV_Target1;
            float depth : SV_Depth;
        };

        PixelCellOutput FragPixelCell(Varyings input)
        {
            int2 pixel = int2(floor(input.positionCS.xy));
            PixelCellSample cell = ResolvePixelCell(pixel);
            bool isBody = cell.subject != 0;
            if (!isBody)
                cell = ResolveOuterPixelCell(pixel);
            clip(cell.subject - 0.5);
            PixelCellOutput output;
            bool isInk = !isBody || IsPixelCellInternalInk(cell);
            output.color = half4(isInk ? _OutlineColor.rgb : cell.colorDepth.rgb, 1);
            if (unity_OrthoParams.w > 0.5)
            {
                output.depth = (cell.colorDepth.a - _ProjectionParams.y) /
                    (_ProjectionParams.z - _ProjectionParams.y);
                #if UNITY_REVERSED_Z
                    output.depth = 1.0 - output.depth;
                #endif
            }
            else
                output.depth = (rcp(cell.colorDepth.a) - _ZBufferParams.w) / _ZBufferParams.z;
            output.resolvedDepth = output.depth;
            return output;
        }

        struct CellDepthOutput
        {
            float color : SV_Target;
            float depth : SV_Depth;
        };

        CellDepthOutput FragCopyCellDepth(Varyings input)
        {
            CellDepthOutput output;
            output.color = LOAD_TEXTURE2D(_CharacterSceneDepth, int2(floor(input.positionCS.xy))).r;
            output.depth = output.color;
            return output;
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

        Pass
        {
            Name "CharacterPixelCellComposite"
            Blend One Zero
            Cull Off
            ZWrite On
            // Visibility was resolved ONCE at the cell center above.
            ZTest Always
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragPixelCell
            ENDHLSL
        }

        Pass
        {
            Name "CharacterPixelCellDepthCopy"
            Blend One Zero
            Cull Off
            ZWrite On
            ZTest Always

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragCopyCellDepth
            ENDHLSL
        }
    }

    FallBack Off
}
