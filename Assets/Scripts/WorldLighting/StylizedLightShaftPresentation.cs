using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Serialization;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Stores directional participating-medium settings consumed by the shared
    /// volumetric renderer feature. Time, weather and light ownership remain in
    /// <see cref="SkyLightingCycleController"/>; this component owns no light
    /// state and allocates no rendering resources.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stylized Light Shaft Presentation")]
    public sealed class StylizedLightShaftPresentation : MonoBehaviour
    {
        private const int MaximumSunSampleCount = 16;
        private const int MaximumLocalEmitterCount = 16;
        private const float MinimumVisibleIntensity = 0.0001f;
        private const float MinimumSunContribution = 0.08f;

        [Header("References")]
        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private Shader shaftShader;

        [Header("Directional Sun Volume")]
        [FormerlySerializedAs("sunSliceCount")]
        [SerializeField, Range(4, MaximumSunSampleCount)]
        private int sunSampleCount = 10;
        [SerializeField, Min(1f)] private float sunVolumeHeight = 12f;
        [SerializeField] private float sunVolumeBaseHeight = 0.02f;
        [SerializeField, Min(0f)] private float sunIntensityMultiplier = 0.018f;
        [SerializeField, Range(0f, 1f)] private float sunExtinction = 0.16f;
        [SerializeField, Range(-0.85f, 0.85f)] private float sunAnisotropy = 0.22f;
        [SerializeField, Min(0.01f)] private float sunSurfaceFadeDistance = 0.45f;
        [SerializeField, Range(0f, 1f)] private float rainSuppression = 0.92f;

        [Header("Local Volumetric Lights")]
        [SerializeField, Range(1, MaximumLocalEmitterCount)]
        private int visibleLocalEmitterLimit = 8;
        [SerializeField, Range(1f, 2f)] private float localRainScatterMultiplier = 1.35f;

        private Light sunLight;
        private Color sunColor = Color.white;
        private float sunStrength;
        private float rainIntensity;

        internal int VisibleLocalEmitterLimit => Mathf.Clamp(
            visibleLocalEmitterLimit,
            1,
            MaximumLocalEmitterCount);

        internal float LocalWeatherScatterMultiplier => Mathf.Lerp(
            1f,
            localRainScatterMultiplier,
            rainIntensity);

        private void Awake()
        {
            if (shell == null)
            {
                shell = GetComponent<PersistentGameplayShell>();
            }
        }

        private void OnValidate()
        {
            sunSampleCount = Mathf.Clamp(sunSampleCount, 4, MaximumSunSampleCount);
            sunVolumeHeight = Mathf.Max(1f, sunVolumeHeight);
            sunIntensityMultiplier = Mathf.Max(0f, sunIntensityMultiplier);
            sunExtinction = Mathf.Clamp01(sunExtinction);
            sunAnisotropy = Mathf.Clamp(sunAnisotropy, -0.85f, 0.85f);
            sunSurfaceFadeDistance = Mathf.Max(0.01f, sunSurfaceFadeDistance);
            rainSuppression = Mathf.Clamp01(rainSuppression);
            visibleLocalEmitterLimit = Mathf.Clamp(
                visibleLocalEmitterLimit,
                1,
                MaximumLocalEmitterCount);
            localRainScatterMultiplier = Mathf.Clamp(
                localRainScatterMultiplier,
                1f,
                2f);
        }

        internal void ApplySunlight(
            Light directionalLight,
            Color color,
            float strength,
            float precipitationIntensity)
        {
            sunLight = directionalLight;
            sunColor = color.linear;
            sunStrength = Mathf.Max(0f, strength);
            rainIntensity = Mathf.Clamp01(precipitationIntensity);
        }

        internal void UnbindGameplayScene()
        {
            sunLight = null;
            sunStrength = 0f;
        }

        internal bool TryGetDirectionalVolume(
            out DirectionalVolumetricLightSettings settings)
        {
            float weatherVisibility = 1f - rainIntensity * rainSuppression;
            float visibleIntensity =
                sunStrength * sunIntensityMultiplier * Mathf.Clamp01(weatherVisibility);
            if (shaftShader == null ||
                !shaftShader.isSupported ||
                sunLight == null ||
                !sunLight.isActiveAndEnabled ||
                sunStrength < MinimumSunContribution ||
                visibleIntensity <= MinimumVisibleIntensity)
            {
                settings = default;
                return false;
            }

            settings = new DirectionalVolumetricLightSettings(
                shaftShader,
                sunLight,
                sunColor,
                visibleIntensity,
                sunVolumeBaseHeight,
                sunVolumeHeight,
                sunSampleCount,
                sunExtinction,
                sunAnisotropy,
                sunSurfaceFadeDistance);
            return true;
        }
    }

    internal readonly struct DirectionalVolumetricLightSettings
    {
        internal DirectionalVolumetricLightSettings(
            Shader shader,
            Light sourceLight,
            Color color,
            float intensity,
            float baseHeight,
            float height,
            int sampleCount,
            float extinction,
            float anisotropy,
            float surfaceFadeDistance)
        {
            Shader = shader;
            SourceLight = sourceLight;
            Color = color;
            Intensity = intensity;
            BaseHeight = baseHeight;
            Height = height;
            SampleCount = sampleCount;
            Extinction = extinction;
            Anisotropy = anisotropy;
            SurfaceFadeDistance = surfaceFadeDistance;
        }

        internal Shader Shader { get; }
        internal Light SourceLight { get; }
        internal Color Color { get; }
        internal float Intensity { get; }
        internal float BaseHeight { get; }
        internal float Height { get; }
        internal int SampleCount { get; }
        internal float Extinction { get; }
        internal float Anisotropy { get; }
        internal float SurfaceFadeDistance { get; }
    }
}
