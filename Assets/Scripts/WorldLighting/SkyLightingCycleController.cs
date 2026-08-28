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
            RenderSettings.ambientSkyColor = sample.AmbientSkyColor;
            RenderSettings.ambientEquatorColor = sample.AmbientEquatorColor;
            RenderSettings.ambientGroundColor = sample.AmbientGroundColor;
            RenderSettings.ambientIntensity = sample.AmbientIntensity;
            RenderSettings.reflectionIntensity = sample.ReflectionIntensity;
            RenderSettings.sun = sceneDirectionalLight;

            float sunPathPitchDegrees = evaluatedHour / HoursPerDay * 360f - 90f;
            float sunElevationDegrees = EvaluateElevationDegrees(sunPathPitchDegrees);
            bool useSun = sunElevationDegrees > DirectionalLightThreshold;

            float moonPathPitchDegrees = sunPathPitchDegrees + 180f;
            float moonElevationDegrees = Mathf.Max(
                0f,
                EvaluateElevationDegrees(moonPathPitchDegrees));
            Quaternion sunRotation = Quaternion.Euler(
                ClampAboveHorizonPitch(
                    sunPathPitchDegrees,
                    profile.MinimumDirectionalElevationDegrees),
                sunAzimuthDegrees,
                0f);
            Quaternion moonRotation = Quaternion.Euler(
                ClampAboveHorizonPitch(
                    moonPathPitchDegrees,
                    profile.MinimumDirectionalElevationDegrees),
                sunAzimuthDegrees,
                0f);
            float moonDirectionWeight = EvaluateMoonDirectionWeight(
                sunElevationDegrees,
                profile.DirectionTransitionElevationDegrees);
            Quaternion directionalRotation = Quaternion.Slerp(
                sunRotation,
                moonRotation,
                moonDirectionWeight);
            Color directionalColor = Color.Lerp(
                sample.SunColor,
                sample.MoonColor,
                moonDirectionWeight);
            float horizonDirectionalIntensity =
                sample.MoonIntensity * profile.HorizonMoonlightWeight;
            float directionalIntensity;
            float visibleShadowStrength = 0f;

            if (useSun)
            {
                float sunlightWeight = EvaluateElevationWeight(
                    sunElevationDegrees,
                    0f,
                    profile.FullSunlightElevationDegrees);
                float shadowWeight = EvaluateElevationWeight(
                    sunElevationDegrees,
                    profile.NoShadowElevationDegrees,
                    profile.FullShadowElevationDegrees);
                directionalIntensity = Mathf.Lerp(
                    horizonDirectionalIntensity,
                    sample.SunIntensity,
                    sunlightWeight);
                visibleShadowStrength = sample.ShadowStrength * shadowWeight;
            }
            else
            {
                float moonlightWeight = EvaluateElevationWeight(
                    moonElevationDegrees,
                    0f,
                    profile.FullMoonlightElevationDegrees);
                directionalIntensity = Mathf.Lerp(
                    horizonDirectionalIntensity,
                    sample.MoonIntensity,
                    moonlightWeight);
            }

            sceneDirectionalLight.transform.rotation = directionalRotation;
            sceneDirectionalLight.color = directionalColor;
            sceneDirectionalLight.intensity = directionalIntensity;
            sceneDirectionalLight.shadowStrength = visibleShadowStrength;
            sceneDirectionalLight.shadows = useSun &&
                                            directionalIntensity > DirectionalLightThreshold &&
                                            visibleShadowStrength > DirectionalLightThreshold
                ? LightShadows.Hard
                : LightShadows.None;
            sceneDirectionalLight.enabled = directionalIntensity > DirectionalLightThreshold;
            return true;
        }

        private static float EvaluateElevationDegrees(float pathPitchDegrees)
        {
            float incomingVertical = Mathf.Sin(pathPitchDegrees * Mathf.Deg2Rad);
            return Mathf.Asin(Mathf.Clamp(incomingVertical, -1f, 1f)) * Mathf.Rad2Deg;
        }

        private static float ClampAboveHorizonPitch(
            float pathPitchDegrees,
            float minimumElevationDegrees)
        {
            float normalizedPitch = Mathf.Repeat(pathPitchDegrees, 360f);
            if (normalizedPitch <= 180f)
            {
                return Mathf.Clamp(
                    normalizedPitch,
                    minimumElevationDegrees,
                    180f - minimumElevationDegrees);
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
    }
}
