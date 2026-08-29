using System.Collections.Generic;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Owns the clear-sky time of day for one gameplay session. The persistent
    /// gameplay shell carries this component between gameplay scenes, while each
    /// loaded scene keeps ownership of its own Directional Light.
    /// </summary>
    [DefaultExecutionOrder(-9990)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    public sealed class SkyLightingCycleController : MonoBehaviour
    {
        private const float HoursPerDay = 24f;
        private const float MinutesPerHour = 60f;
        private const float DirectionalLightThreshold = 0.001f;

        [Header("Definition")]
        [SerializeField] private SkyLightingProfile profile;

        [Header("Runtime Clock")]
        [SerializeField, Range(0f, HoursPerDay)] private float initialHour = 8f;
        [SerializeField] private bool advanceAutomatically = true;
        [SerializeField, Min(1f)] private float realSecondsPerDay = 60f;
        [SerializeField, Min(0.1f)] private float lightingStepMinutes = 1f;

        [Header("Sun Path")]
        [SerializeField, Range(0f, 360f)] private float sunAzimuthDegrees = 290f;

        private readonly List<Light> sceneLights = new List<Light>();
        private Light sceneDirectionalLight;
        private float currentHour;
        private float lastAppliedHour = float.NaN;
        private bool hasGameplaySceneBinding;
        private bool profileValid;
        private SkyTimePhase currentPhase;

        public float CurrentHour => currentHour;
        public SkyTimePhase CurrentPhase => currentPhase;
        public bool IsAdvancingAutomatically => advanceAutomatically;
        public bool HasGameplaySceneBinding =>
            hasGameplaySceneBinding && sceneDirectionalLight != null;
        public Light SceneDirectionalLight => sceneDirectionalLight;
        public Light SceneSun => sceneDirectionalLight;

        private void Awake()
        {
            currentHour = SkyLightingProfile.NormalizeHour(initialHour);
            profileValid = ValidateProfile();
        }

        private void OnEnable()
        {
            SceneManager.sceneLoaded += HandleSceneLoaded;
            BindActiveGameplayScene();
        }

        private void OnDisable()
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
            sceneDirectionalLight = null;
            hasGameplaySceneBinding = false;
            lastAppliedHour = float.NaN;
        }

        private void Update()
        {
            if (!profileValid || !HasGameplaySceneBinding)
            {
                return;
            }

            if (advanceAutomatically)
            {
                float hoursPerSecond = HoursPerDay / Mathf.Max(1f, realSecondsPerDay);
                currentHour = SkyLightingProfile.NormalizeHour(
                    currentHour + Time.deltaTime * hoursPerSecond);
            }

            ApplyLightingIfStepChanged();
        }

        public bool SetTimeHours(float hour)
        {
            currentHour = SkyLightingProfile.NormalizeHour(hour);
            lastAppliedHour = float.NaN;
            return ApplyCurrentLighting();
        }

        public bool SetPhase(SkyTimePhase phase)
        {
            if (!profileValid)
            {
                return false;
            }

            return SetTimeHours(profile.GetPreviewHour(phase));
        }

        public void SetAutomaticAdvance(bool shouldAdvance)
        {
            advanceAutomatically = shouldAdvance;
        }

        public bool SetProfile(SkyLightingProfile replacement)
        {
            if (replacement == null)
            {
                Debug.LogError("Cannot apply a missing sky lighting profile.", this);
                return false;
            }

            if (!replacement.TryValidate(out string error))
            {
                Debug.LogError(error, replacement);
                return false;
            }

            profile = replacement;
            profileValid = true;
            lastAppliedHour = float.NaN;
            return ApplyCurrentLighting();
        }

        [ContextMenu("Preview Morning")]
        private void PreviewMorning()
        {
            SetPhase(SkyTimePhase.Morning);
        }

        [ContextMenu("Preview Day")]
        private void PreviewDay()
        {
            SetPhase(SkyTimePhase.Day);
        }

        [ContextMenu("Preview Night")]
        private void PreviewNight()
        {
            SetPhase(SkyTimePhase.Night);
        }

        private bool ValidateProfile()
        {
            if (profile == null)
            {
                Debug.LogError("SkyLightingCycleController requires a SkyLightingProfile.", this);
                return false;
            }

            if (profile.TryValidate(out string error))
            {
                return true;
            }

            Debug.LogError(error, profile);
            return false;
        }

        private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (scene != SceneManager.GetActiveScene())
            {
                return;
            }

            BindScene(scene);
        }

        private void BindActiveGameplayScene()
        {
            Scene activeScene = SceneManager.GetActiveScene();
            if (activeScene.IsValid() && activeScene.isLoaded)
            {
                BindScene(activeScene);
            }
        }

        private void BindScene(Scene scene)
        {
            sceneDirectionalLight = null;
            hasGameplaySceneBinding = false;
            lastAppliedHour = float.NaN;

            if (!ContainsGameplayBootstrap(scene))
            {
                return;
            }

            if (!TryFindDirectionalLight(scene, out Light directionalLight, out string error))
            {
                Debug.LogError(error, this);
                return;
            }

            sceneDirectionalLight = directionalLight;
            hasGameplaySceneBinding = true;
            RenderSettings.sun = sceneDirectionalLight;
            ApplyCurrentLighting();
        }

        private static bool ContainsGameplayBootstrap(Scene scene)
        {
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                if (roots[index].GetComponentInChildren<GameplayShellBootstrap>(true) != null)
                {
                    return true;
                }
            }

            return false;
        }

        private bool TryFindDirectionalLight(
            Scene scene,
            out Light directionalLight,
            out string error)
        {
            directionalLight = null;
            sceneLights.Clear();

            GameObject[] roots = scene.GetRootGameObjects();
            int directionalCount = 0;
            Light renderSettingsSun = RenderSettings.sun;
            for (int index = 0; index < roots.Length; index++)
            {
                sceneLights.Clear();
                roots[index].GetComponentsInChildren(true, sceneLights);
                for (int lightIndex = 0; lightIndex < sceneLights.Count; lightIndex++)
                {
                    Light candidate = sceneLights[lightIndex];
                    if (candidate == null || candidate.type != LightType.Directional)
                    {
                        continue;
                    }

                    directionalCount++;
                    if (candidate == renderSettingsSun)
                    {
                        directionalLight = candidate;
                    }
                    else if (directionalLight == null)
                    {
                        directionalLight = candidate;
                    }
                }
            }

            sceneLights.Clear();
            if (directionalCount == 1)
            {
                error = null;
                return true;
            }

            if (directionalCount == 0)
            {
                directionalLight = null;
                error = $"Gameplay scene '{scene.path}' requires one Directional Light for sky lighting.";
                return false;
            }

            if (renderSettingsSun != null &&
                renderSettingsSun.type == LightType.Directional &&
                renderSettingsSun.gameObject.scene == scene)
            {
                directionalLight = renderSettingsSun;
                error = null;
                return true;
            }

            directionalLight = null;
            error = $"Gameplay scene '{scene.path}' has {directionalCount} Directional Lights. " +
                    "Assign RenderSettings.sun explicitly so the sky lighting owner is unambiguous.";
            return false;
        }

        private void ApplyLightingIfStepChanged()
        {
            float stepHours = Mathf.Max(0.1f, lightingStepMinutes) / MinutesPerHour;
            float steppedHour = SkyLightingProfile.NormalizeHour(
                Mathf.Floor(currentHour / stepHours) * stepHours);
            if (!float.IsNaN(lastAppliedHour) &&
                Mathf.Abs(Mathf.DeltaAngle(lastAppliedHour * 15f, steppedHour * 15f)) < 0.001f)
            {
                return;
            }

            ApplyLighting(steppedHour);
        }

        private bool ApplyCurrentLighting()
        {
            if (!profileValid || !HasGameplaySceneBinding)
            {
                return false;
            }

            return ApplyLighting(currentHour);
        }

        private bool ApplyLighting(float evaluatedHour)
        {
            if (!profile.TryEvaluate(evaluatedHour, out SkyLightingSample sample))
            {
                return false;
            }

            lastAppliedHour = evaluatedHour;
            currentPhase = sample.Phase;

            RenderSettings.ambientMode = AmbientMode.Trilight;
            Color minimumLightColor = profile.MinimumLightColor;
            RenderSettings.ambientSkyColor = MaxRgb(
                sample.AmbientSkyColor,
                ScaleRgb(minimumLightColor, 0.35f));
            RenderSettings.ambientEquatorColor = MaxRgb(
                sample.AmbientEquatorColor,
                ScaleRgb(minimumLightColor, 0.22f));
            RenderSettings.ambientGroundColor = MaxRgb(
                sample.AmbientGroundColor,
                ScaleRgb(minimumLightColor, 0.12f));
            RenderSettings.ambientIntensity = Mathf.Max(
                sample.AmbientIntensity,
                profile.MinimumAmbientIntensity);
            RenderSettings.reflectionIntensity = sample.ReflectionIntensity;
            RenderSettings.sun = sceneDirectionalLight;

            float sunPathPitchDegrees = evaluatedHour / HoursPerDay * 360f - 90f;
            float signedSunElevationDegrees = EvaluateElevationDegrees(sunPathPitchDegrees);
            float sunElevationDegrees = Mathf.Max(0f, signedSunElevationDegrees);

            // This is the art-directed night shadow path, not a visible moon
            // ephemeris. Mirroring the pitch joins sunset and sunrise without
            // rotating the single shadow map through the opposite horizon.
            float moonPathPitchDegrees = 360f - sunPathPitchDegrees;
            float moonElevationDegrees = Mathf.Max(
                0f,
                EvaluateElevationDegrees(moonPathPitchDegrees));
            Quaternion sunRotation = Quaternion.Euler(
                EvaluateAboveHorizonPitch(
                    sunPathPitchDegrees,
                    profile.MinimumDirectionalElevationDegrees),
                sunAzimuthDegrees,
                0f);
            Quaternion moonRotation = Quaternion.Euler(
                EvaluateAboveHorizonPitch(
                    moonPathPitchDegrees,
                    profile.MinimumDirectionalElevationDegrees),
                sunAzimuthDegrees,
                0f);
            float moonDirectionWeight = EvaluateMoonDirectionWeight(
                signedSunElevationDegrees,
                profile.DirectionTransitionElevationDegrees);
            Quaternion directionalRotation = Quaternion.Slerp(
                sunRotation,
                moonRotation,
                moonDirectionWeight);
            float sunContributionWeight = EvaluateSunContributionWeight(
                signedSunElevationDegrees,
                profile.FullMoonlightElevationDegrees,
                profile.FullSunlightElevationDegrees);
            float moonContributionWeight = 1f - sunContributionWeight;
            float duskLightOverlapWeight = EvaluateDuskLightOverlapWeight(
                sunPathPitchDegrees,
                profile.DuskLightOverlapWeight);
            float sunLightContributionWeight = Mathf.Lerp(
                sunContributionWeight,
                1f,
                duskLightOverlapWeight);
            float moonLightContributionWeight = Mathf.Lerp(
                moonContributionWeight,
                1f,
                duskLightOverlapWeight);
            float sunContribution = sample.SunIntensity * sunLightContributionWeight;
            float moonContribution = sample.MoonIntensity * moonLightContributionWeight;
            float configuredDirectionalFloor = Mathf.Max(
                profile.MinimumDirectionalIntensity,
                sample.MoonIntensity * profile.HorizonMoonlightWeight);
            float floorContribution = Mathf.Max(
                0f,
                configuredDirectionalFloor - sunContribution - moonContribution);
            float directionalIntensity =
                sunContribution + moonContribution + floorContribution;
            Color directionalColor = BlendWeightedColor(
                sample.SunColor,
                sunContribution,
                sample.MoonColor,
                moonContribution,
                minimumLightColor,
                floorContribution,
                directionalIntensity);

            float sunShadowWeight = EvaluateElevationWeight(
                sunElevationDegrees,
                profile.NoShadowElevationDegrees,
                profile.FullShadowElevationDegrees);
            float moonShadowWeight = EvaluateElevationWeight(
                moonElevationDegrees,
                profile.NoShadowElevationDegrees,
                profile.FullShadowElevationDegrees);
            float celestialShadowStrength =
                sample.ShadowStrength * sunShadowWeight * sunContributionWeight +
                profile.MoonShadowStrength * moonShadowWeight * moonContributionWeight;
            float visibleShadowStrength = Mathf.Max(
                celestialShadowStrength,
                profile.MinimumShadowStrength);

            sceneDirectionalLight.transform.rotation = directionalRotation;
            sceneDirectionalLight.color = directionalColor;
            sceneDirectionalLight.intensity = directionalIntensity;
            sceneDirectionalLight.shadowStrength = Mathf.Clamp01(visibleShadowStrength);
            sceneDirectionalLight.shadows =
                directionalIntensity > DirectionalLightThreshold &&
                visibleShadowStrength > DirectionalLightThreshold
                ? LightShadows.Soft
                : LightShadows.None;
            sceneDirectionalLight.enabled = directionalIntensity > DirectionalLightThreshold;
            return true;
        }

        private static float EvaluateElevationDegrees(float pathPitchDegrees)
        {
            float incomingVertical = Mathf.Sin(pathPitchDegrees * Mathf.Deg2Rad);
            return Mathf.Asin(Mathf.Clamp(incomingVertical, -1f, 1f)) * Mathf.Rad2Deg;
        }

        private static float EvaluateAboveHorizonPitch(
            float pathPitchDegrees,
            float minimumElevationDegrees)
        {
            float normalizedPitch = Mathf.Repeat(pathPitchDegrees, 360f);
            if (normalizedPitch <= 180f)
            {
                // Keep the configured length limit, but ease into each end so
                // the shadow never sits on a hard-clamped rotation plateau.
                float normalizedArc = normalizedPitch / 180f;
                float easedArc = Mathf.SmoothStep(0f, 1f, normalizedArc);
                return Mathf.Lerp(
                    minimumElevationDegrees,
                    180f - minimumElevationDegrees,
                    easedArc);
            }

            bool nearestHorizonIsEast =
                Mathf.Cos(pathPitchDegrees * Mathf.Deg2Rad) >= 0f;
            return nearestHorizonIsEast
                ? minimumElevationDegrees
                : 180f - minimumElevationDegrees;
        }

        private static float EvaluateElevationWeight(
            float elevationDegrees,
            float zeroAtDegrees,
            float fullAtDegrees)
        {
            float normalized = Mathf.InverseLerp(
                zeroAtDegrees,
                fullAtDegrees,
                elevationDegrees);
            return Mathf.SmoothStep(0f, 1f, normalized);
        }

        private static float EvaluateMoonDirectionWeight(
            float sunElevationDegrees,
            float transitionElevationDegrees)
        {
            float normalized = Mathf.Clamp01(
                (transitionElevationDegrees - sunElevationDegrees) /
                (transitionElevationDegrees * 2f));
            return Mathf.SmoothStep(0f, 1f, normalized);
        }

        private static float EvaluateSunContributionWeight(
            float signedSunElevationDegrees,
            float fullMoonlightElevationDegrees,
            float fullSunlightElevationDegrees)
        {
            float normalized = Mathf.InverseLerp(
                -fullMoonlightElevationDegrees,
                fullSunlightElevationDegrees,
                signedSunElevationDegrees);
            return Mathf.SmoothStep(0f, 1f, normalized);
        }

        private static float EvaluateDuskLightOverlapWeight(
            float sunPathPitchDegrees,
            float maximumOverlapWeight)
        {
            // The profile already fades sunlight down while bringing moonlight
            // up. Restore part of the otherwise double-faded light only while
            // the sun is descending, so the existing dawn curve is untouched.
            float descendingWeight = Mathf.Clamp01(
                -Mathf.Cos(sunPathPitchDegrees * Mathf.Deg2Rad));
            return maximumOverlapWeight *
                   Mathf.SmoothStep(0f, 1f, descendingWeight);
        }

        private static Color BlendWeightedColor(
            Color sunColor,
            float sunWeight,
            Color moonColor,
            float moonWeight,
            Color minimumColor,
            float minimumWeight,
            float totalWeight)
        {
            if (totalWeight <= DirectionalLightThreshold)
            {
                minimumColor.a = 1f;
                return minimumColor;
            }

            Color blended =
                (sunColor * sunWeight +
                 moonColor * moonWeight +
                 minimumColor * minimumWeight) / totalWeight;
            blended.a = 1f;
            return blended;
        }

        private static Color ScaleRgb(Color color, float multiplier)
        {
            return new Color(
                color.r * multiplier,
                color.g * multiplier,
                color.b * multiplier,
                1f);
        }

        private static Color MaxRgb(Color value, Color minimum)
        {
            return new Color(
                Mathf.Max(value.r, minimum.r),
                Mathf.Max(value.g, minimum.g),
                Mathf.Max(value.b, minimum.b),
                1f);
        }
    }
}
