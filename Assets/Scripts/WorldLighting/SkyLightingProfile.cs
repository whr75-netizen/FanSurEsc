using System;
using UnityEngine;
using UnityEngine.Serialization;

namespace FantasySurvival.WorldLighting
{
    public enum SkyTimePhase
    {
        Morning,
        Day,
        Night
    }

    [Serializable]
    public struct SkyLightingKeyframe
    {
        [SerializeField, Range(0f, 24f)] private float hour;
        [SerializeField] private SkyTimePhase phase;
        [SerializeField] private Color ambientSkyColor;
        [SerializeField] private Color ambientEquatorColor;
        [SerializeField] private Color ambientGroundColor;
        [SerializeField, Min(0f)] private float ambientIntensity;
        [SerializeField, Range(0f, 1f)] private float reflectionIntensity;
        [SerializeField] private Color sunColor;
        [SerializeField, Min(0f)] private float sunIntensity;
        [SerializeField] private Color moonColor;
        [SerializeField, Min(0f)] private float moonIntensity;
        [SerializeField, Range(0f, 1f)] private float shadowStrength;

        public float Hour => hour;
        public SkyTimePhase Phase => phase;
        public Color AmbientSkyColor => ambientSkyColor;
        public Color AmbientEquatorColor => ambientEquatorColor;
        public Color AmbientGroundColor => ambientGroundColor;
        public float AmbientIntensity => ambientIntensity;
        public float ReflectionIntensity => reflectionIntensity;
        public Color SunColor => sunColor;
        public float SunIntensity => sunIntensity;
        public Color MoonColor => moonColor;
        public float MoonIntensity => moonIntensity;
        public float ShadowStrength => shadowStrength;

        public SkyLightingKeyframe(
            float hour,
            SkyTimePhase phase,
            Color ambientSkyColor,
            Color ambientEquatorColor,
            Color ambientGroundColor,
            float ambientIntensity,
            float reflectionIntensity,
            Color sunColor,
            float sunIntensity,
            Color moonColor,
            float moonIntensity,
            float shadowStrength)
        {
            this.hour = hour;
            this.phase = phase;
            this.ambientSkyColor = ambientSkyColor;
            this.ambientEquatorColor = ambientEquatorColor;
            this.ambientGroundColor = ambientGroundColor;
            this.ambientIntensity = ambientIntensity;
            this.reflectionIntensity = reflectionIntensity;
            this.sunColor = sunColor;
            this.sunIntensity = sunIntensity;
            this.moonColor = moonColor;
            this.moonIntensity = moonIntensity;
            this.shadowStrength = shadowStrength;
        }
    }

    public readonly struct SkyLightingSample
    {
        public SkyTimePhase Phase { get; }
        public Color AmbientSkyColor { get; }
        public Color AmbientEquatorColor { get; }
        public Color AmbientGroundColor { get; }
        public float AmbientIntensity { get; }
        public float ReflectionIntensity { get; }
        public Color SunColor { get; }
        public float SunIntensity { get; }
        public Color MoonColor { get; }
        public float MoonIntensity { get; }
        public float ShadowStrength { get; }

        private SkyLightingSample(
            SkyTimePhase phase,
            Color ambientSkyColor,
            Color ambientEquatorColor,
            Color ambientGroundColor,
            float ambientIntensity,
            float reflectionIntensity,
            Color sunColor,
            float sunIntensity,
            Color moonColor,
            float moonIntensity,
            float shadowStrength)
        {
            Phase = phase;
            AmbientSkyColor = ambientSkyColor;
            AmbientEquatorColor = ambientEquatorColor;
            AmbientGroundColor = ambientGroundColor;
            AmbientIntensity = ambientIntensity;
            ReflectionIntensity = reflectionIntensity;
            SunColor = sunColor;
            SunIntensity = sunIntensity;
            MoonColor = moonColor;
            MoonIntensity = moonIntensity;
            ShadowStrength = shadowStrength;
        }

        public static SkyLightingSample Interpolate(
            SkyLightingKeyframe from,
            SkyLightingKeyframe to,
            float t)
        {
            float easedT = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t));
            SkyTimePhase phase = easedT < 0.5f ? from.Phase : to.Phase;
            return new SkyLightingSample(
                phase,
                Color.Lerp(from.AmbientSkyColor, to.AmbientSkyColor, easedT),
                Color.Lerp(from.AmbientEquatorColor, to.AmbientEquatorColor, easedT),
                Color.Lerp(from.AmbientGroundColor, to.AmbientGroundColor, easedT),
                Mathf.Lerp(from.AmbientIntensity, to.AmbientIntensity, easedT),
                Mathf.Lerp(from.ReflectionIntensity, to.ReflectionIntensity, easedT),
                Color.Lerp(from.SunColor, to.SunColor, easedT),
                Mathf.Lerp(from.SunIntensity, to.SunIntensity, easedT),
                Color.Lerp(from.MoonColor, to.MoonColor, easedT),
                Mathf.Lerp(from.MoonIntensity, to.MoonIntensity, easedT),
                Mathf.Lerp(from.ShadowStrength, to.ShadowStrength, easedT));
        }
    }

    [CreateAssetMenu(
        fileName = "SkyLightingProfile",
        menuName = "Fantasy Survival/World Lighting/Sky Lighting Profile")]
    public sealed class SkyLightingProfile : ScriptableObject
    {
        private const float DefaultMoonShadowStrength = 0.50f;
        private const float DefaultMinimumShadowStrength = 0.10f;
        private const float DefaultMinimumAmbientIntensity = 0.62f;
        private const float DefaultMinimumDirectionalIntensity = 0.18f;
        private const float DefaultDuskLightOverlapWeight = 0.50f;
        private static readonly Color DefaultMinimumLightColor =
            new Color(0.42f, 0.54f, 0.90f, 1f);

        [SerializeField, Range(0f, 24f)] private float morningPreviewHour = 7.5f;
        [SerializeField, Range(0f, 24f)] private float dayPreviewHour = 12f;
        [SerializeField, Range(0f, 24f)] private float nightPreviewHour = 22f;
        [SerializeField, Range(1f, 45f)] private float minimumDirectionalElevationDegrees = 31f;
        [SerializeField, Range(1f, 45f)] private float fullSunlightElevationDegrees = 15f;
        [SerializeField, Range(0f, 30f)] private float noShadowElevationDegrees = 0f;
        [SerializeField, Range(1f, 45f)] private float fullShadowElevationDegrees = 31f;
        [SerializeField, Range(1f, 45f)] private float fullMoonlightElevationDegrees = 15f;
        [SerializeField, Range(0.1f, 15f)] private float directionTransitionElevationDegrees = 15f;
        [SerializeField, Range(0.01f, 1f)] private float horizonMoonlightWeight = 0.5f;
        [SerializeField, Range(0f, 1f)] private float duskLightOverlapWeight =
            DefaultDuskLightOverlapWeight;
        [SerializeField, Range(0f, 1f)] private float moonShadowStrength =
            DefaultMoonShadowStrength;
        [FormerlySerializedAs("minimumTransitionShadowStrength")]
        [SerializeField, Range(0f, 1f)] private float minimumShadowStrength =
            DefaultMinimumShadowStrength;
        [SerializeField] private Color minimumLightColor = DefaultMinimumLightColor;
        [SerializeField, Min(0f)] private float minimumAmbientIntensity =
            DefaultMinimumAmbientIntensity;
        [SerializeField, Min(0f)] private float minimumDirectionalIntensity =
            DefaultMinimumDirectionalIntensity;
        [SerializeField] private Texture2D cloudShadowCookie;
        [SerializeField] private Vector2 cloudShadowCookieSize = new Vector2(24f, 24f);
        [FormerlySerializedAs("cloudShadowVelocity")]
        [Tooltip("World X/Z units per real second. Positive X moves west to east.")]
        [SerializeField] private Vector2 cloudShadowWorldVelocity = new Vector2(0.75f, 0f);
        [SerializeField] private SkyLightingKeyframe[] keyframes = CreateClearSkyDefaults();

        public float MinimumDirectionalElevationDegrees => minimumDirectionalElevationDegrees;
        public float FullSunlightElevationDegrees => fullSunlightElevationDegrees;
        public float NoShadowElevationDegrees => noShadowElevationDegrees;
        public float FullShadowElevationDegrees => fullShadowElevationDegrees;
        public float FullMoonlightElevationDegrees => fullMoonlightElevationDegrees;
        public float DirectionTransitionElevationDegrees => directionTransitionElevationDegrees;
        public float HorizonMoonlightWeight => horizonMoonlightWeight;
        public float DuskLightOverlapWeight => duskLightOverlapWeight;
        public float MoonShadowStrength => moonShadowStrength;
        public float MinimumShadowStrength => minimumShadowStrength;
        public Color MinimumLightColor => minimumLightColor;
        public float MinimumAmbientIntensity => minimumAmbientIntensity;
        public float MinimumDirectionalIntensity => minimumDirectionalIntensity;
        public Texture2D CloudShadowCookie => cloudShadowCookie;
        public Vector2 CloudShadowCookieSize => cloudShadowCookieSize;
        public Vector2 CloudShadowWorldVelocity => cloudShadowWorldVelocity;

        public bool TryEvaluate(float hour, out SkyLightingSample sample)
        {
            sample = default;
            if (!TryValidate(out _))
            {
                return false;
            }

            float normalizedHour = NormalizeHour(hour);
            int previousIndex = keyframes.Length - 1;
            for (int index = 0; index < keyframes.Length; index++)
            {
                if (normalizedHour < keyframes[index].Hour)
                {
                    break;
                }

                previousIndex = index;
            }

            int nextIndex = (previousIndex + 1) % keyframes.Length;
            float previousHour = keyframes[previousIndex].Hour;
            float nextHour = keyframes[nextIndex].Hour;
            float evaluationHour = normalizedHour;

            if (nextIndex == 0)
            {
                nextHour += 24f;
                if (evaluationHour < previousHour)
                {
                    evaluationHour += 24f;
                }
            }

            float duration = nextHour - previousHour;
            float t = duration > Mathf.Epsilon
                ? (evaluationHour - previousHour) / duration
                : 0f;
            sample = SkyLightingSample.Interpolate(
                keyframes[previousIndex],
                keyframes[nextIndex],
                t);
            return true;
        }

        public float GetPreviewHour(SkyTimePhase phase)
        {
            return phase switch
            {
                SkyTimePhase.Morning => morningPreviewHour,
                SkyTimePhase.Day => dayPreviewHour,
                SkyTimePhase.Night => nightPreviewHour,
                _ => dayPreviewHour
            };
        }

        public bool TryValidate(out string error)
        {
            if (keyframes == null || keyframes.Length < 2)
            {
                error = "Sky lighting profile requires at least two keyframes.";
                return false;
            }

            if (minimumDirectionalElevationDegrees <= 0f ||
                minimumDirectionalElevationDegrees >= 90f)
            {
                error = "Minimum directional elevation must be between 0 and 90 degrees.";
                return false;
            }

            if (fullSunlightElevationDegrees <= 0f ||
                fullMoonlightElevationDegrees <= 0f)
            {
                error = "Sunlight and moonlight fade elevations must be greater than zero.";
                return false;
            }

            if (directionTransitionElevationDegrees <= 0f ||
                horizonMoonlightWeight <= 0f ||
                horizonMoonlightWeight > 1f)
            {
                error = "Twilight direction transition and moonlight floor must be positive.";
                return false;
            }

            if (noShadowElevationDegrees < 0f ||
                fullShadowElevationDegrees <= noShadowElevationDegrees)
            {
                error = "Full shadow elevation must be greater than the no-shadow elevation.";
                return false;
            }

            if (cloudShadowCookie != null &&
                (!IsFinite(cloudShadowCookieSize) ||
                 cloudShadowCookieSize.x <= 0f ||
                 cloudShadowCookieSize.y <= 0f ||
                 !IsFinite(cloudShadowWorldVelocity)))
            {
                error = "Cloud shadow cookie size must be positive and its world velocity must be finite.";
                return false;
            }

            if (float.IsNaN(moonShadowStrength) ||
                float.IsInfinity(moonShadowStrength) ||
                moonShadowStrength < 0f ||
                moonShadowStrength > 1f ||
                !IsFiniteNonNegative(duskLightOverlapWeight) ||
                duskLightOverlapWeight > 1f ||
                !IsFiniteNonNegative(minimumShadowStrength) ||
                minimumShadowStrength > 1f ||
                !IsFiniteNonNegative(minimumAmbientIntensity) ||
                !IsFiniteNonNegative(minimumDirectionalIntensity) ||
                !IsFiniteNonNegative(minimumLightColor))
            {
                error = "Dusk overlap, minimum blue light, and moon shadow values are invalid.";
                return false;
            }

            float previousHour = -1f;
            for (int index = 0; index < keyframes.Length; index++)
            {
                float hour = keyframes[index].Hour;
                if (hour < 0f || hour >= 24f)
                {
                    error = $"Sky lighting keyframe {index} must be in the range [0, 24).";
                    return false;
                }

                if (hour <= previousHour)
                {
                    error = "Sky lighting keyframes must use unique hours in ascending order.";
                    return false;
                }

                previousHour = hour;
            }

            error = null;
            return true;
        }

        private static bool IsFiniteNonNegative(float value)
        {
            return IsFinite(value) && value >= 0f;
        }

        private static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
        }

        private static bool IsFinite(Vector2 value)
        {
            return IsFinite(value.x) && IsFinite(value.y);
        }

        private static bool IsFiniteNonNegative(Color value)
        {
            return IsFiniteNonNegative(value.r) &&
                   IsFiniteNonNegative(value.g) &&
                   IsFiniteNonNegative(value.b) &&
                   IsFiniteNonNegative(value.a);
        }

        public static float NormalizeHour(float hour)
        {
            float normalized = hour % 24f;
            return normalized < 0f ? normalized + 24f : normalized;
        }

        private static SkyLightingKeyframe[] CreateClearSkyDefaults()
        {
            return new[]
            {
                new SkyLightingKeyframe(
                    0f,
                    SkyTimePhase.Night,
                    new Color(0.085f, 0.11f, 0.22f),
                    new Color(0.055f, 0.075f, 0.15f),
                    new Color(0.022f, 0.032f, 0.065f),
                    0.50f,
                    0.18f,
                    new Color(0.54f, 0.62f, 0.82f),
                    0f,
                    new Color(0.62f, 0.72f, 1f),
                    0.24f,
                    0f),
                new SkyLightingKeyframe(
                    6.5f,
                    SkyTimePhase.Morning,
                    new Color(0.38f, 0.39f, 0.48f),
                    new Color(0.43f, 0.31f, 0.26f),
                    new Color(0.12f, 0.10f, 0.11f),
                    0.52f,
                    0.28f,
                    new Color(1f, 0.56f, 0.30f),
                    0.7f,
                    new Color(0.62f, 0.72f, 1f),
                    0.26f,
                    0.72f),
                new SkyLightingKeyframe(
                    10f,
                    SkyTimePhase.Day,
                    new Color(0.50f, 0.58f, 0.72f),
                    new Color(0.38f, 0.43f, 0.50f),
                    new Color(0.14f, 0.16f, 0.19f),
                    0.68f,
                    0.48f,
                    new Color(1f, 0.95f, 0.82f),
                    1.15f,
                    new Color(0.62f, 0.72f, 1f),
                    0f,
                    0.86f),
                new SkyLightingKeyframe(
                    16f,
                    SkyTimePhase.Day,
                    new Color(0.44f, 0.50f, 0.62f),
                    new Color(0.40f, 0.36f, 0.34f),
                    new Color(0.13f, 0.13f, 0.15f),
                    0.58f,
                    0.40f,
                    new Color(1f, 0.74f, 0.46f),
                    0.82f,
                    new Color(0.62f, 0.72f, 1f),
                    0.04f,
                    0.80f),
                new SkyLightingKeyframe(
                    19.5f,
                    SkyTimePhase.Night,
                    new Color(0.10f, 0.13f, 0.24f),
                    new Color(0.065f, 0.085f, 0.16f),
                    new Color(0.025f, 0.038f, 0.075f),
                    0.52f,
                    0.22f,
                    new Color(0.60f, 0.68f, 0.88f),
                    0f,
                    new Color(0.62f, 0.72f, 1f),
                    0.32f,
                    0f)
            };
        }
    }
}
