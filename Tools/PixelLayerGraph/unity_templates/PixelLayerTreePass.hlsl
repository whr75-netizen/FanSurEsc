// CLEAN-ROOM TEMPLATE (Staged outside Assets/ until user approves Unity import)
// Target clean-room destination: Assets/Rendering/PixelLayerTree/Shaders/PixelLayerTreePass.hlsl
// Implements the 4 zero-double-operation mathematical primitives from 목표.md & Argon4.0.md:
//   1. Single root-phase-locked logical grid projection (zero 960->480->960 resampling)
//   2. Nested parent-mask clipping (zero frog-eyes, zero physical 3D mesh pull-forward)
//   3. Physical front-surface depth (z_front) 1px silhouette (handles chin-over-neck naturally)
//   4. Single finite palette LUT lookup FinalRGB = P[r, q] (zero double RGB multiplication)

#ifndef FANTASY_PIXEL_LAYER_TREE_PASS_INCLUDED
#define FANTASY_PIXEL_LAYER_TREE_PASS_INCLUDED

// 1. [G2a] Root-Phase-Locked Clip Shift
// Cancels the exact character-root sub-pixel fractional phase deltaRoot in [-0.5, 0.5)
// uniformly across Body, Head, Hair, and Eyes on one logical pixel grid.
float4 ApplyRootPhaseSnapCS(float4 positionCS, float2 deltaRootLogicalPx, float2 logicalResolution)
{
    float2 ndcShift = -(2.0 * deltaRootLogicalPx / max(logicalResolution, float2(1.0, 1.0)));
    positionCS.xy += ndcShift * positionCS.w;
    return positionCS;
}

// 2. [G4] Explicit Float32 Threshold Shade Quantization (Zero RGB Multiply)
// Returns discrete shade index q in [0, levels - 1] without modifying RGB.
int QuantizeShadeExplicit(float g, int levels, float4 cutsA, float4 cutsB)
{
    int q = 0;
    float gs = saturate(g);
    [unroll]
    for (int i = 0; i < 7; i++)
    {
        if (i < levels - 1)
        {
            float t = (i < 4) ? cutsA[min(i, 3)] : cutsB[max(i - 4, 0)];
            q += (gs >= t) ? 1 : 0;
        }
    }
    return q;
}

// 3. [G5] Nested Parent-Mask Clipping Primitive (Order-by-Construction)
// Any child layer (e.g. 3-2-2 Sclera, 3-2-3 Iris, 3-2-3-1 Pupil) is clipped strictly
// to its parent visible window (e.g. 3-2-1 M_eye_visible). Frog-eyes are structurally impossible.
bool ClipToParentMask(float childAlpha, float parentMaskAlpha)
{
    return (childAlpha > 0.5) && (parentMaskAlpha > 0.5);
}

// 4. [G7] Physical Front-Surface Depth (z_front) 1px Silhouette Detector
// Detects outer character boundary AND internal self-overlap (e.g. chin over neck even with
// identical skin ID!) purely from physical camera-space depth z_front + tau_z < z_back.
// No artificial layer-order hacks needed.
// internalOnFrontSide: configurable toggle for [미정] visual review (front rim vs recessed shadow cell).
bool IsPhysicalFrontSilhouette1px(
    int2 cell,
    int2 gridSize,
    Texture2D<float4> gbufferRQNZ, // (r, q, nodeId, linearDepthZ)
    float depthThresholdTauZ,
    bool protectCurrentCell,
    bool internalOnFrontSide)
{
    if (protectCurrentCell) return false;
    float4 center = gbufferRQNZ.Load(int3(cell, 0));
    if (center.z <= 0.5) return false; // empty background

    float zCenter = center.w;
    int2 dirs[4] = { int2(-1, 0), int2(1, 0), int2(0, -1), int2(0, 1) };

    [unroll]
    for (int i = 0; i < 4; i++)
    {
        int2 n = cell + dirs[i];
        bool inBounds = all(n >= 0) && all(n < gridSize);
        if (!inBounds) return true; // outer silhouette

        float4 nb = gbufferRQNZ.Load(int3(n, 0));
        if (nb.z <= 0.5) return true; // touches empty background -> outer 1px silhouette

        float zNb = nb.w;
        if (internalOnFrontSide)
        {
            // Mark the physically closer surface rim (z_front + tau_z < z_back)
            if (zCenter + depthThresholdTauZ < zNb) return true;
        }
        else
        {
            // Mark the recessed/occluded neighbor cell (preserves thin foreground parts)
            if (zNb + depthThresholdTauZ < zCenter) return true;
        }
    }
    return false;
}

// 5. [G7] Single Finite Palette LUT Lookup (Zero Double RGB Multiplication)
float3 ResolveFinitePaletteLUT(Texture2D<float4> paletteLUT, int regionR, int shadeQ)
{
    return paletteLUT.Load(int3(max(shadeQ, 0), max(regionR, 0), 0)).rgb;
}

#endif
