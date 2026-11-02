// Unimported scalar helper proposal, NOT a compiled or connected GPU pass.
// Caller must supply a valid selected feature identity and actual source depth.
// Existing known sub-sample depths remain individual; this fills holes only.
// Caller must query external face/hair at the SAME destination sample positions.
bool AssignedDepthFallback24(float selectedSourceDepth, float sumKnownDepth,
                             uint knownCount, out float fillDepth)
{
    fillDepth = 0;
    if (knownCount > 16u) return false;
    if (knownCount > 0u) fillDepth = sumKnownDepth / (float)knownCount;
    else fillDepth = selectedSourceDepth;
    return isfinite(fillDepth) && fillDepth > 0;
}

// A false result is unknown/unsupported, never permission to remove an occluder.
bool SocketExempt24(bool registeredUnilateralOwnComponent,
                    float cameraDepthGap, float evaluatedWorldRingDiameter)
{
    return registeredUnilateralOwnComponent && isfinite(evaluatedWorldRingDiameter)
        && evaluatedWorldRingDiameter > 0 && cameraDepthGap >= 0
        && cameraDepthGap <= evaluatedWorldRingDiameter;
}

// Returns one actual clipped segment's midpoint/depth and screen arc length.
// Accumulate length-weighted moments once per column. A multi-segment mean is
// NOT automatically on a pigment carrier: actual source alpha/UV and a matched
// destination visibility query are required before creating a palette pixel.
bool ClipColumnMid24(float4 a, float4 b, int column,
                      out float3 midXYZ, out float arcLength)
{
    midXYZ = 0; arcLength = 0;
    float3 delta = b.xyz - a.xyz;
    float low = 0, high = 1;
    if (abs(delta.x) < 1e-12)
    {
        if (a.x < column || a.x > column + 1) return false;
    }
    else
    {
        float p = (column - a.x) / delta.x;
        float q = (column + 1 - a.x) / delta.x;
        low = max(0, min(p, q)); high = min(1, max(p, q));
        if (high <= low) return false;
    }
    float3 first = a.xyz + low * delta, last = a.xyz + high * delta;
    midXYZ = (first + last) * .5; arcLength = length(last.xy - first.xy);
    return arcLength > 0 && all(isfinite(midXYZ));
}
