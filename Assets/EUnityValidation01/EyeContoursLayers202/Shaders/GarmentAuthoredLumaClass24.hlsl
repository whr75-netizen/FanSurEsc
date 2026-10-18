// Pure input function. A owns texture binding, clone material and compilation.
// Call at existing E151 target selection, before legacyScale/legacyBand.
// Input authoredR is PointClamp linear-data UV0 PNG, not source RGB or alpha.
#ifndef GARMENT_AUTHORED_LUMA_CLASS_24
#define GARMENT_AUTHORED_LUMA_CLASS_24
float B24AuthoredGarmentTarget(uint role, float sourceY, float originalRampTarget,
                             float authoredR, bool authoredEnabled)
{
    if (!authoredEnabled || role != 10u || sourceY < 0.025)
        return originalRampTarget;
    // Preserve original dark bucket: seams, blue trim and dark structural ink.
    if (abs(originalRampTarget - 0.0974143422) < 0.000001)
        return originalRampTarget;
    // EXISTING Role10 ramp values. Assignment only; no palette value changes.
    return authoredR >= 0.5 ? 0.7636518013 : 0.8771414025;
}
#endif
