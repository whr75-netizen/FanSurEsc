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

    public enum SkyWeatherType
    {
        Clear,
        Rain
    }

    [Serializable]
    public struct SkyWeatherPreset
    {
        [SerializeField] private SkyWeatherType weatherType;
        [SerializeField] private Color ambientTint;
        [SerializeField, Min(0f)] private float ambientIntensityMultiplier;
        [SerializeField] private Color directionalTint;
        [SerializeField, Min(0f)] private float directionalIntensityMultiplier;
        [SerializeField, Range(0f, 1f)] private float shadowStrengthMultiplier;
        [SerializeField, Range(0f, 2f)] private float cloudShadowOpacityMultiplier;
        [SerializeField, Range(-3f, 3f)] private float cloudShadowSoftnessOffset;
        [SerializeField, Range(0f, 1f)] private float precipitationIntensity;
        [SerializeField] private Color precipitationColor;

        public SkyWeatherType WeatherType => weatherType;
        public Color AmbientTint => ambientTint;
        public float AmbientIntensityMultiplier => ambientIntensityMultiplier;
        public Color DirectionalTint => directionalTint;
        public float DirectionalIntensityMultiplier => directionalIntensityMultiplier;
        public float ShadowStrengthMultiplier => shadowStrengthMultiplier;
        public float CloudShadowOpacityMultiplier => cloudShadowOpacityMultiplier;
        public float CloudShadowSoftnessOffset => cloudShadowSoftnessOffset;
        public float PrecipitationIntensity => precipitationIntensity;
        public Color PrecipitationColor => precipitationColor;

        public SkyWeatherPreset(
            SkyWeatherType weatherType,
            Color ambientTint,
            float ambientIntensityMultiplier,
            Color directionalTint,
            float directionalIntensityMultiplier,
            float shadowStrengthMultiplier,
            float cloudShadowOpacityMultiplier,
            float cloudShadowSoftnessOffset,
            float precipitationIntensity,
            Color precipitationColor)
        {
            this.weatherType = weatherType;
            this.ambientTint = ambientTint;
            this.ambientIntensityMultiplier = ambientIntensityMultiplier;
            this.directionalTint = directionalTint;
            this.directionalIntensityMultiplier = directionalIntensityMultiplier;
            this.shadowStrengthMultiplier = shadowStrengthMultiplier;
            this.cloudShadowOpacityMultiplier = cloudShadowOpacityMultiplier;
            this.cloudShadowSoftnessOffset = cloudShadowSoftnessOffset;
            this.precipitationIntensity = precipitationIntensity;
            this.precipitationColor = precipitationColor;
        }
    }

    public readonly struct SkyWeatherSample
    {
        public Color AmbientTint { get; }
        public float AmbientIntensityMultiplier { get; }
        public Color DirectionalTint { get; }
        public float DirectionalIntensityMultiplier { get; }
        public float ShadowStrengthMultiplier { get; }
        public float CloudShadowOpacityMultiplier { get; }
        public float CloudShadowSoftnessOffset { get; }
        public float PrecipitationIntensity { get; }
        public Color PrecipitationColor { get; }

        private SkyWeatherSample(
            Color ambientTint,
            float ambientIntensityMultiplier,
            Color directionalTint,
            float directionalIntensityMultiplier,
            float shadowStrengthMultiplier,
            float cloudShadowOpacityMultiplier,
            float cloudShadowSoftnessOffset,
            float precipitationIntensity,
            Color precipitationColor)
        {
            AmbientTint = ambientTint;
            AmbientIntensityMultiplier = ambientIntensityMultiplier;
            DirectionalTint = directionalTint;
            DirectionalIntensityMultiplier = directionalIntensityMultiplier;
            ShadowStrengthMultiplier = shadowStrengthMultiplier;
            CloudShadowOpacityMultiplier = cloudShadowOpacityMultiplier;
            CloudShadowSoftnessOffset = cloudShadowSoftnessOffset;
            PrecipitationIntensity = precipitationIntensity;
            PrecipitationColor = precipitationColor;
        }

        public static SkyWeatherSample FromPreset(SkyWeatherPreset preset)
        {
            return new SkyWeatherSample(
                preset.AmbientTint,
                preset.AmbientIntensityMultiplier,
                preset.DirectionalTint,
                preset.DirectionalIntensityMultiplier,
                preset.ShadowStrengthMultiplier,
                preset.CloudShadowOpacityMultiplier,
                preset.CloudShadowSoftnessOffset,
                preset.PrecipitationIntensity,
                preset.PrecipitationColor);
        }

        public static SkyWeatherSample Interpolate(
            SkyWeatherSample from,
            SkyWeatherSample to,
            float t)
        {
            float easedT = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t));
            return new SkyWeatherSample(
                Color.Lerp(from.AmbientTint, to.AmbientTint, easedT),
                Mathf.Lerp(
                    from.AmbientIntensityMultiplier,
                    to.AmbientIntensityMultiplier,
                    easedT),
                Color.Lerp(from.DirectionalTint, to.DirectionalTint, easedT),
                Mathf.Lerp(
                    from.DirectionalIntensityMultiplier,
                    to.DirectionalIntensityMultiplier,
                    easedT),
                Mathf.Lerp(
                    from.ShadowStrengthMultiplier,
                    to.ShadowStrengthMultiplier,
                    easedT),
                Mathf.Lerp(
                    from.CloudShadowOpacityMultiplier,
                    to.CloudShadowOpacityMultiplier,
                    easedT),
                Mathf.Lerp(
                    from.CloudShadowSoftnessOffset,
                    to.CloudShadowSoftnessOffset,
                    easedT),
                Mathf.Lerp(
                    from.PrecipitationIntensity,
                    to.PrecipitationIntensity,
                    easedT),
                Color.Lerp(from.PrecipitationColor, to.PrecipitationColor, easedT));
        }
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
        private const float DefaultMinimumAmbientIntensity = 0.38f;
        private const float DefaultMinimumDirectionalIntensity = 0.12f;
        private const float DefaultDuskLightOverlapWeight = 0.50f;
        private const float DefaultLowElevationCloudShadowSoftnessMip = 1.25f;
        private const float DefaultHighElevationCloudShadowSoftnessMip = 0.25f;
        private const float DefaultLowElevationCloudShadowOpacity = 0.55f;
        private const float DefaultHighElevationCloudShadowOpacity = 0.90f;
        private static readonly Color DefaultMinimumLightColor =
            new Color(0.15f, 0.20f, 0.40f, 1f);

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
        [Tooltip("Linear repeating cookie with mipmaps and Trilinear filtering.")]
        [SerializeField] private Texture2D cloudShadowCookie;
        [SerializeField] private Shader cloudShadowFilterShader;
        [Tooltip("Desired size of one cookie repeat on horizontal ground.")]
        [SerializeField] private Vector2 cloudShadowCookieSize = new Vector2(24f, 24f);
        [FormerlySerializedAs("cloudShadowVelocity")]
        [Tooltip("World X/Z units per real second. Positive X moves west to east.")]
        [SerializeField] private Vector2 cloudShadowWorldVelocity = new Vector2(0.75f, 0f);
        [Tooltip("Cookie mip level used near the horizon. Higher values produce softer edges.")]
        [SerializeField, Range(0f, 3f)] private float lowElevationCloudShadowSoftnessMip =
            DefaultLowElevationCloudShadowSoftnessMip;
        [Tooltip("Cookie mip level used when the active sun or moon is high.")]
        [SerializeField, Range(0f, 3f)] private float highElevationCloudShadowSoftnessMip =
            DefaultHighElevationCloudShadowSoftnessMip;
        [Tooltip("Cloud shadow opacity near the horizon.")]
        [SerializeField, Range(0f, 1f)] private float lowElevationCloudShadowOpacity =
            DefaultLowElevationCloudShadowOpacity;
        [Tooltip("Cloud shadow opacity when the active sun or moon is high.")]
        [SerializeField, Range(0f, 1f)] private float highElevationCloudShadowOpacity =
            DefaultHighElevationCloudShadowOpacity;
        [Header("Weather Presets")]
        [SerializeField, Min(0.01f)] private float weatherTransitionSeconds = 0.75f;
        [SerializeField] private SkyWeatherPreset[] weatherPresets = CreateWeatherDefaults();
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
        public Shader CloudShadowFilterShader => cloudShadowFilterShader;
        public Vector2 CloudShadowCookieSize => cloudShadowCookieSize;
        public Vector2 CloudShadowWorldVelocity => cloudShadowWorldVelocity;
        public float LowElevationCloudShadowSoftnessMip =>
            lowElevationCloudShadowSoftnessMip;
        public float HighElevationCloudShadowSoftnessMip =>
            highElevationCloudShadowSoftnessMip;
        public float LowElevationCloudShadowOpacity => lowElevationCloudShadowOpacity;
        public float HighElevationCloudShadowOpacity => highElevationCloudShadowOpacity;
        public float WeatherTransitionSeconds => weatherTransitionSeconds;

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

        public bool TryGetWeatherPreset(
            SkyWeatherType weatherType,
            out SkyWeatherPreset preset)
        {
            if (weatherPresets != null)
            {
                for (int index = 0; index < weatherPresets.Length; index++)
                {
                    if (weatherPresets[index].WeatherType == weatherType)
                    {
                        preset = weatherPresets[index];
                        return true;
                    }
                }
            }

            preset = default;
            return false;
        }

        public bool TryValidate(out string error)
        {
            if (keyframes == null || keyframes.Length < 2)
            {
                error = "Sky lighting profile requires at least two keyframes.";
                return false;
            }

            if (weatherPresets == null || weatherPresets.Length < 2)
            {
                error = "Sky lighting profile requires Clear and Rain weather presets.";
                return false;
            }

            bool hasClearWeather = false;
            bool hasRainWeather = false;
            for (int index = 0; index < weatherPresets.Length; index++)
            {
                SkyWeatherPreset preset = weatherPresets[index];
                if (!IsValidWeatherPreset(preset))
                {
                    error = $"Weather preset {index} contains invalid lighting or precipitation values.";
                    return false;
                }

                if (preset.WeatherType == SkyWeatherType.Clear)
                {
                    if (hasClearWeather)
                    {
                        error = "Sky lighting profile contains more than one Clear weather preset.";
                        return false;
                    }

                    hasClearWeather = true;
                }
                else if (preset.WeatherType == SkyWeatherType.Rain)
                {
                    if (hasRainWeather)
                    {
                        error = "Sky lighting profile contains more than one Rain weather preset.";
                        return false;
                    }

                    hasRainWeather = true;
                }
            }

            if (!hasClearWeather || !hasRainWeather ||
                !IsFinite(weatherTransitionSeconds) ||
                weatherTransitionSeconds <= 0f)
            {
                error = "Sky lighting profile requires one valid Clear preset, one valid Rain preset, and a positive transition duration.";
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

            if (cloudShadowCookie != null && cloudShadowFilterShader == null)
            {
                error = "Cloud shadow cookie requires its prefilter shader.";
                return false;
            }

            if (cloudShadowCookie != null &&
                (cloudShadowCookie.mipmapCount <= 1 ||
                 cloudShadowCookie.filterMode != FilterMode.Trilinear))
            {
                error = "Cloud shadow cookie requires mipmaps and Trilinear filtering.";
                return false;
            }

            if (!IsFiniteNonNegative(lowElevationCloudShadowSoftnessMip) ||
                !IsFiniteNonNegative(highElevationCloudShadowSoftnessMip) ||
                lowElevationCloudShadowSoftnessMip > 3f ||
                highElevationCloudShadowSoftnessMip > 3f ||
                !IsFiniteNonNegative(lowElevationCloudShadowOpacity) ||
                !IsFiniteNonNegative(highElevationCloudShadowOpacity) ||
                lowElevationCloudShadowOpacity > 1f ||
                highElevationCloudShadowOpacity > 1f)
            {
                error = "Cloud shadow softness and opacity values are invalid.";
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

        private static bool IsValidWeatherPreset(SkyWeatherPreset preset)
        {
            return IsFiniteNonNegative(preset.AmbientTint) &&
                   IsFiniteNonNegative(preset.DirectionalTint) &&
                   IsFiniteNonNegative(preset.PrecipitationColor) &&
                   IsFiniteNonNegative(preset.AmbientIntensityMultiplier) &&
                   IsFiniteNonNegative(preset.DirectionalIntensityMultiplier) &&
                   IsFiniteNonNegative(preset.ShadowStrengthMultiplier) &&
                   preset.ShadowStrengthMultiplier <= 1f &&
                   IsFiniteNonNegative(preset.CloudShadowOpacityMultiplier) &&
                   preset.CloudShadowOpacityMultiplier <= 2f &&
                   IsFinite(preset.CloudShadowSoftnessOffset) &&
                   preset.CloudShadowSoftnessOffset >= -3f &&
                   preset.CloudShadowSoftnessOffset <= 3f &&
                   IsFiniteNonNegative(preset.PrecipitationIntensity) &&
                   preset.PrecipitationIntensity <= 1f;
        }

        public static float NormalizeHour(float hour)
        {
            float normalized = hour % 24f;
            return normalized < 0f ? normalized + 24f : normalized;
        }

        private static SkyLightingKeyframe[] CreateClearSkyDefaults()
        {
            // Keep neutral daylight isolated from the short, art-directed
            // sunrise and sunset palettes. Wide warm keyframe spans make the
            // entire morning or afternoon look yellow instead of producing a
            // readable golden-hour transition.
            return new[]
            {
                new SkyLightingKeyframe(
                    0f,
                    SkyTimePhase.Night,
                    new Color(0.055f, 0.075f, 0.16f),
                    new Color(0.035f, 0.05f, 0.105f),
                    new Color(0.014f, 0.022f, 0.045f),
                    0.40f,
                    0.12f,
                    new Color(0.54f, 0.62f, 0.82f),
                    0f,
                    new Color(0.62f, 0.72f, 1f),
                    0.18f,
                    0f),
                new SkyLightingKeyframe(
                    4.75f,
                    SkyTimePhase.Night,
                    new Color(0.075f, 0.105f, 0.22f),
                    new Color(0.045f, 0.07f, 0.15f),
                    new Color(0.018f, 0.03f, 0.065f),
                    0.43f,
                    0.15f,
                    new Color(1f, 0.72f, 0.50f),
                    0f,
                    new Color(0.62f, 0.72f, 1f),
                    0.24f,
                    0f),
                new SkyLightingKeyframe(
                    5.75f,
                    SkyTimePhase.Morning,
                    new Color(0.205f, 0.16f, 0.17f),
                    new Color(0.285f, 0.145f, 0.085f),
                    new Color(0.065f, 0.042f, 0.038f),
                    0.46f,
                    0.19f,
                    new Color(1f, 0.70f, 0.46f),
                    0.08f,
                    new Color(0.62f, 0.72f, 1f),
                    0.26f,
                    0.30f),
                new SkyLightingKeyframe(
                    6.5f,
                    SkyTimePhase.Morning,
                    new Color(0.325f, 0.265f, 0.235f),
                    new Color(0.39f, 0.225f, 0.125f),
                    new Color(0.105f, 0.068f, 0.050f),
                    0.51f,
                    0.25f,
                    new Color(1f, 0.78f, 0.58f),
                    0.30f,
                    new Color(0.62f, 0.72f, 1f),
                    0.22f,
                    0.66f),
                new SkyLightingKeyframe(
                    7.5f,
                    SkyTimePhase.Morning,
                    new Color(0.430f, 0.420f, 0.405f),
                    new Color(0.355f, 0.345f, 0.330f),
                    new Color(0.112f, 0.108f, 0.102f),
                    0.57f,
                    0.32f,
                    new Color(1f, 0.95f, 0.90f),
                    0.58f,
                    new Color(0.62f, 0.72f, 1f),
                    0.08f,
                    0.78f),
                new SkyLightingKeyframe(
                    10f,
                    SkyTimePhase.Day,
                    new Color(0.57616234f, 0.57616234f, 0.57616234f),
                    new Color(0.42567363f, 0.42567363f, 0.42567363f),
                    new Color(0.15839440f, 0.15839440f, 0.15839440f),
                    0.68f,
                    0.48f,
                    Color.white,
                    1.0294983f,
                    new Color(0.62f, 0.72f, 1f),
                    0f,
                    0.86f),
                new SkyLightingKeyframe(
                    16f,
                    SkyTimePhase.Day,
                    new Color(0.49820304f, 0.49820304f, 0.49820304f),
                    new Color(0.36759195f, 0.36759195f, 0.36759195f),
                    new Color(0.13154575f, 0.13154575f, 0.13154575f),
                    0.58f,
                    0.40f,
                    Color.white,
                    0.48230505f,
                    new Color(0.62f, 0.72f, 1f),
                    0.04f,
                    0.80f),
                new SkyLightingKeyframe(
                    17.5f,
                    SkyTimePhase.Day,
                    new Color(0.440f, 0.410f, 0.370f),
                    new Color(0.355f, 0.300f, 0.235f),
                    new Color(0.112f, 0.095f, 0.075f),
                    0.56f,
                    0.35f,
                    new Color(1f, 0.92f, 0.82f),
                    0.38f,
                    new Color(0.62f, 0.72f, 1f),
                    0.10f,
                    0.76f),
                new SkyLightingKeyframe(
                    18.25f,
                    SkyTimePhase.Night,
                    new Color(0.245f, 0.175f, 0.185f),
                    new Color(0.335f, 0.165f, 0.095f),
                    new Color(0.078f, 0.048f, 0.045f),
                    0.50f,
                    0.26f,
                    new Color(1f, 0.68f, 0.44f),
                    0.13f,
                    new Color(0.62f, 0.72f, 1f),
                    0.26f,
                    0.42f),
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
                    0f),
                new SkyLightingKeyframe(
                    22f,
                    SkyTimePhase.Night,
                    new Color(0.075f, 0.10f, 0.20f),
                    new Color(0.048f, 0.065f, 0.13f),
                    new Color(0.018f, 0.029f, 0.058f),
                    0.46f,
                    0.16f,
                    new Color(0.56f, 0.64f, 0.84f),
                    0f,
                    new Color(0.62f, 0.72f, 1f),
                    0.24f,
                    0f)
            };
        }

        private static SkyWeatherPreset[] CreateWeatherDefaults()
        {
            return new[]
            {
                new SkyWeatherPreset(
                    SkyWeatherType.Clear,
                    Color.white,
                    1f,
                    Color.white,
                    1f,
                    1f,
                    1f,
                    0f,
                    0f,
                    new Color(0.72f, 0.82f, 0.95f, 1f)),
                new SkyWeatherPreset(
                    SkyWeatherType.Rain,
                    new Color(0.72f, 0.79f, 0.88f, 1f),
                    0.78f,
                    new Color(0.68f, 0.76f, 0.88f, 1f),
                    0.52f,
                    0.42f,
                    0f,
                    0.65f,
                    1f,
                    new Color(0.36f, 0.50f, 0.68f, 0.62f))
            };
        }
    }
}
