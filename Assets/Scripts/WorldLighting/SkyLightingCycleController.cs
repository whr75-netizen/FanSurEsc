using System.Collections.Generic;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Owns time of day and weather for one gameplay session. The persistent
    /// gameplay shell carries this component between gameplay scenes, while each
    /// loaded scene keeps ownership of its own Directional Light.
    /// </summary>
    [DefaultExecutionOrder(-9990)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    [RequireComponent(typeof(PixelRainPresentation))]
    [RequireComponent(typeof(StylizedLightShaftPresentation))]
    public sealed class SkyLightingCycleController : MonoBehaviour
    {
        private const float HoursPerDay = 24f;
        private const float MinutesPerHour = 60f;
        private const float DirectionalLightThreshold = 0.001f;
        private const float MinimumCookieProjectionScale = 0.001f;
        private const int CloudShadowFilterKeyMaximum = 255;
        private static readonly int CloudShadowSoftnessMipId =
            Shader.PropertyToID("_SoftnessMip");
        private static readonly int CloudShadowOpacityId =
            Shader.PropertyToID("_Opacity");
        [Header("Definition")]
        [SerializeField] private SkyLightingProfile profile;
        [SerializeField] private PixelRainPresentation rainPresentation;
        [SerializeField] private StylizedLightShaftPresentation lightShaftPresentation;

        [Header("Runtime Clock")]
        [SerializeField, Range(0f, HoursPerDay)] private float initialHour = 8f;
        [SerializeField] private bool advanceAutomatically = true;
        [SerializeField, Min(1f)] private float realSecondsPerDay = 60f;
        [SerializeField, Min(0.1f)] private float lightingStepMinutes = 1f;

        [Header("Runtime Weather")]
        [SerializeField] private SkyWeatherType initialWeather = SkyWeatherType.Clear;

        [Header("Sun Path")]
        [SerializeField, Range(0f, 360f)] private float sunAzimuthDegrees = 290f;

        [Header("Night-Activated Lights")]
        [SerializeField, Range(0f, 1f)] private float nightLightFadeStartWeight = 0.35f;
        [SerializeField, Range(0f, 1f)] private float nightLightFullyOnWeight = 0.75f;

        private readonly List<Light> sceneLights = new List<Light>();
        private PersistentGameplayShell shell;
        private Light sceneDirectionalLight;
        private UniversalAdditionalLightData sceneDirectionalLightData;
        private Material cloudShadowFilterMaterial;
        private RenderTexture filteredCloudShadowCookie;
        private Texture2D cloudShadowFilterSource;
        private Shader cloudShadowFilterShader;
        private Vector2 cloudShadowWorldOffset;
        private float currentHour;
        private float lastAppliedHour = float.NaN;
        private int lastCloudShadowFilterKey = -1;
        private float currentCloudShadowSoftnessMip;
        private float currentCloudShadowOpacity;
        private bool hasGameplaySceneBinding;
        private bool profileValid;
        private SkyTimePhase currentPhase;
        private SkyWeatherType currentWeatherType;
        private SkyWeatherSample weatherFromSample;
        private SkyWeatherSample weatherToSample;
        private SkyWeatherSample currentWeatherSample;
        private float weatherTransitionElapsed;
        private bool weatherTransitionActive;
        private float currentNightActivatedLightVisibility;

        public float CurrentHour => currentHour;
        public SkyTimePhase CurrentPhase => currentPhase;
        public bool IsAdvancingAutomatically => advanceAutomatically;
        public bool HasGameplaySceneBinding =>
            hasGameplaySceneBinding && sceneDirectionalLight != null;
        public Light SceneDirectionalLight => sceneDirectionalLight;
        public Light SceneSun => sceneDirectionalLight;
        public float CurrentCloudShadowSoftnessMip => currentCloudShadowSoftnessMip;
        public float CurrentCloudShadowOpacity => currentCloudShadowOpacity;
        public SkyWeatherType CurrentWeatherType => currentWeatherType;
        public float CurrentRainIntensity => currentWeatherSample.PrecipitationIntensity;
        public bool IsWeatherTransitioning => weatherTransitionActive;
        public float CurrentNightActivatedLightVisibility =>
            currentNightActivatedLightVisibility;

        public event System.Action<float> NightActivatedLightVisibilityChanged;

        private void Awake()
        {
            shell = GetComponent<PersistentGameplayShell>();
            if (rainPresentation == null)
            {
                rainPresentation = GetComponent<PixelRainPresentation>();
            }

            if (lightShaftPresentation == null)
            {
                lightShaftPresentation = GetComponent<StylizedLightShaftPresentation>();
            }

            currentHour = SkyLightingProfile.NormalizeHour(initialHour);
            profileValid = ValidateProfile();
            if (profileValid)
            {
                profileValid = InitializeWeather(initialWeather);
            }
        }

        private void OnEnable()
        {
            SceneManager.sceneLoaded += HandleSceneLoaded;
            BindActiveGameplayScene();
        }

        private void OnDisable()
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
            DetachFilteredCloudShadowCookie();
            ReleaseCloudShadowFilterResources();
            sceneDirectionalLight = null;
            sceneDirectionalLightData = null;
            hasGameplaySceneBinding = false;
            lastAppliedHour = float.NaN;
            rainPresentation?.UnbindGameplayScene();
            lightShaftPresentation?.UnbindGameplayScene();
            ApplyNightActivatedLightVisibility(0f, true);
        }

        private void Update()
        {
            if (!profileValid)
            {
                return;
            }

            float environmentVisualDeltaTime =
                IsEnvironmentTestPreviewActive()
                    ? Time.unscaledDeltaTime
                    : Time.deltaTime;
            bool weatherChanged =
                AdvanceWeatherTransition(environmentVisualDeltaTime);

            if (!HasGameplaySceneBinding)
            {
                rainPresentation?.Tick(environmentVisualDeltaTime);
                return;
            }

            if (advanceAutomatically)
            {
                float hoursPerSecond = HoursPerDay / Mathf.Max(1f, realSecondsPerDay);
                currentHour = SkyLightingProfile.NormalizeHour(
                    currentHour + Time.deltaTime * hoursPerSecond);
            }

            if (weatherChanged)
            {
                lastAppliedHour = float.NaN;
            }

            ApplyLightingIfStepChanged();
            AdvanceCloudShadow(environmentVisualDeltaTime);
            rainPresentation?.Tick(environmentVisualDeltaTime);
        }

        private bool IsEnvironmentTestPreviewActive()
        {
            return shell != null &&
                   shell.EscapeMenu != null &&
                   shell.EscapeMenu.IsEnvironmentTestOpen;
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

        public bool SetWeather(SkyWeatherType weatherType, bool immediate = false)
        {
            if (!profileValid ||
                !profile.TryGetWeatherPreset(weatherType, out SkyWeatherPreset preset))
            {
                return false;
            }

            weatherFromSample = currentWeatherSample;
            weatherToSample = SkyWeatherSample.FromPreset(preset);
            currentWeatherType = weatherType;
            weatherTransitionElapsed = 0f;
            weatherTransitionActive = !immediate;
            if (immediate)
            {
                currentWeatherSample = weatherToSample;
            }

            lastAppliedHour = float.NaN;
            lastCloudShadowFilterKey = -1;
            if (HasGameplaySceneBinding)
            {
                ApplyCurrentLighting(immediate);
            }
            else
            {
                rainPresentation?.ApplyWeather(
                    currentWeatherSample,
                    profile.CloudShadowWorldVelocity,
                    immediate);
            }
            return true;
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

            ReleaseCloudShadowFilterResources();
            profile = replacement;
            profileValid = true;
            if (!InitializeWeather(currentWeatherType))
            {
                return false;
            }
            lastAppliedHour = float.NaN;
            ApplyCloudShadowConfiguration();
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

        [ContextMenu("Preview Clear Weather")]
        private void PreviewClearWeather()
        {
            SetWeather(SkyWeatherType.Clear, true);
        }

        [ContextMenu("Preview Rain Weather")]
        private void PreviewRainWeather()
        {
            SetWeather(SkyWeatherType.Rain, true);
        }

        private bool ValidateProfile()
        {
            if (rainPresentation == null)
            {
                Debug.LogError("SkyLightingCycleController requires PixelRainPresentation.", this);
                return false;
            }

            if (lightShaftPresentation == null)
            {
                Debug.LogError(
                    "SkyLightingCycleController requires StylizedLightShaftPresentation.",
                    this);
                return false;
            }

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
            DetachFilteredCloudShadowCookie();
            rainPresentation?.UnbindGameplayScene();
            lightShaftPresentation?.UnbindGameplayScene();
            sceneDirectionalLight = null;
            sceneDirectionalLightData = null;
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

            if (!directionalLight.TryGetComponent(out sceneDirectionalLightData))
            {
                Debug.LogError(
                    $"Gameplay scene '{scene.path}' Directional Light requires " +
                    "UniversalAdditionalLightData for cloud shadow cookies.",
                    directionalLight);
                return;
            }

            sceneDirectionalLight = directionalLight;
            hasGameplaySceneBinding = true;
            RenderSettings.sun = sceneDirectionalLight;
            rainPresentation?.BindGameplayScene(scene);
            ApplyCloudShadowConfiguration();
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

        private bool ApplyCurrentLighting(bool forceShelterRefresh = false)
        {
            if (!profileValid || !HasGameplaySceneBinding)
            {
                return false;
            }

            return ApplyLighting(currentHour, forceShelterRefresh);
        }

        private void ApplyCloudShadowConfiguration()
        {
            if (!profileValid || !HasGameplaySceneBinding)
            {
                return;
            }

            Texture2D cookie = profile.CloudShadowCookie;
            if (sceneDirectionalLightData == null)
            {
                return;
            }

            if (cookie == null)
            {
                sceneDirectionalLight.cookie = null;
                sceneDirectionalLightData.lightCookieOffset = Vector2.zero;
                ReleaseCloudShadowFilterResources();
                return;
            }

            if (!EnsureCloudShadowFilterResources(cookie))
            {
                sceneDirectionalLight.cookie = null;
                return;
            }

            sceneDirectionalLight.cookie = filteredCloudShadowCookie;

            ApplyCloudShadowProjection();
        }

        private bool EnsureCloudShadowFilterResources(Texture2D source)
        {
            Shader filterShader = profile.CloudShadowFilterShader;
            if (filterShader == null)
            {
                Debug.LogError("Cloud shadow prefilter shader is missing.", profile);
                return false;
            }

            bool resourcesMatch =
                cloudShadowFilterMaterial != null &&
                filteredCloudShadowCookie != null &&
                filteredCloudShadowCookie.IsCreated() &&
                cloudShadowFilterSource == source &&
                cloudShadowFilterShader == filterShader &&
                filteredCloudShadowCookie.width == source.width &&
                filteredCloudShadowCookie.height == source.height;
            if (resourcesMatch)
            {
                return true;
            }

            ReleaseCloudShadowFilterResources();

            cloudShadowFilterMaterial = new Material(filterShader)
            {
                name = "Runtime Cloud Shadow Prefilter",
                hideFlags = HideFlags.HideAndDontSave
            };
            filteredCloudShadowCookie = new RenderTexture(
                source.width,
                source.height,
                0,
                RenderTextureFormat.ARGB32,
                RenderTextureReadWrite.Linear)
            {
                name = "Runtime Filtered Cloud Shadow Cookie",
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Repeat,
                useMipMap = false,
                autoGenerateMips = false,
                hideFlags = HideFlags.HideAndDontSave
            };

            if (!filteredCloudShadowCookie.Create())
            {
                Debug.LogError("Failed to create the cloud shadow prefilter texture.", this);
                ReleaseCloudShadowFilterResources();
                return false;
            }

            cloudShadowFilterSource = source;
            cloudShadowFilterShader = filterShader;
            lastCloudShadowFilterKey = -1;
            return true;
        }

        private void UpdateCloudShadowFilter(
            float elevationWeight,
            SkyWeatherSample weather)
        {
            if (cloudShadowFilterMaterial == null ||
                filteredCloudShadowCookie == null ||
                cloudShadowFilterSource == null)
            {
                return;
            }

            float filteredElevationWeight = Mathf.Clamp01(elevationWeight);
            float desiredSoftnessMip = Mathf.Clamp(
                Mathf.Lerp(
                    profile.LowElevationCloudShadowSoftnessMip,
                    profile.HighElevationCloudShadowSoftnessMip,
                    filteredElevationWeight) +
                weather.CloudShadowSoftnessOffset,
                0f,
                3f);
            float desiredOpacity = Mathf.Clamp01(
                Mathf.Lerp(
                    profile.LowElevationCloudShadowOpacity,
                    profile.HighElevationCloudShadowOpacity,
                    filteredElevationWeight) *
                weather.CloudShadowOpacityMultiplier);
            int softnessKey = Mathf.RoundToInt(
                desiredSoftnessMip / 3f * CloudShadowFilterKeyMaximum);
            int opacityKey = Mathf.RoundToInt(
                desiredOpacity * CloudShadowFilterKeyMaximum);
            int filterKey = (softnessKey << 8) | opacityKey;
            if (filterKey == lastCloudShadowFilterKey)
            {
                return;
            }

            currentCloudShadowSoftnessMip =
                softnessKey / (float)CloudShadowFilterKeyMaximum * 3f;
            currentCloudShadowOpacity =
                opacityKey / (float)CloudShadowFilterKeyMaximum;

            cloudShadowFilterMaterial.SetFloat(
                CloudShadowSoftnessMipId,
                currentCloudShadowSoftnessMip);
            cloudShadowFilterMaterial.SetFloat(
                CloudShadowOpacityId,
                currentCloudShadowOpacity);
            Graphics.Blit(
                cloudShadowFilterSource,
                filteredCloudShadowCookie,
                cloudShadowFilterMaterial,
                0);
            lastCloudShadowFilterKey = filterKey;
        }

        private void DetachFilteredCloudShadowCookie()
        {
            if (sceneDirectionalLight != null &&
                sceneDirectionalLight.cookie == filteredCloudShadowCookie)
            {
                sceneDirectionalLight.cookie = null;
            }
        }

        private void ReleaseCloudShadowFilterResources()
        {
            DetachFilteredCloudShadowCookie();

            if (filteredCloudShadowCookie != null)
            {
                filteredCloudShadowCookie.Release();
                DestroyRuntimeObject(filteredCloudShadowCookie);
            }

            if (cloudShadowFilterMaterial != null)
            {
                DestroyRuntimeObject(cloudShadowFilterMaterial);
            }

            filteredCloudShadowCookie = null;
            cloudShadowFilterMaterial = null;
            cloudShadowFilterSource = null;
            cloudShadowFilterShader = null;
            lastCloudShadowFilterKey = -1;
            currentCloudShadowSoftnessMip = 0f;
            currentCloudShadowOpacity = 0f;
        }

        private static void DestroyRuntimeObject(Object runtimeObject)
        {
            if (runtimeObject == null)
            {
                return;
            }

            if (Application.isPlaying)
            {
                Destroy(runtimeObject);
            }
            else
            {
                DestroyImmediate(runtimeObject);
            }
        }

        private void AdvanceCloudShadow(float deltaTime)
        {
            if (deltaTime <= 0f ||
                profile.CloudShadowCookie == null ||
                sceneDirectionalLightData == null)
            {
                return;
            }

            cloudShadowWorldOffset += profile.CloudShadowWorldVelocity * deltaTime;
            ApplyCloudShadowOffset();
        }

        private void ApplyCloudShadowOffset()
        {
            if (sceneDirectionalLight == null ||
                sceneDirectionalLightData == null ||
                profile.CloudShadowCookie == null)
            {
                return;
            }

            // Profile X/Z are map east/north. Convert the accumulated world wind
            // displacement into the current light plane so the projected pattern
            // keeps travelling west-to-east while the sun/moon key light rotates.
            Vector3 worldAnchor = new Vector3(
                cloudShadowWorldOffset.x,
                0f,
                cloudShadowWorldOffset.y);
            Matrix4x4 worldToLight =
                sceneDirectionalLight.transform.worldToLocalMatrix;
            Vector3 lightPlaneAnchor = worldToLight.MultiplyPoint3x4(worldAnchor);
            Vector2 lightPlaneOffset = new Vector2(
                lightPlaneAnchor.x,
                lightPlaneAnchor.y);
            sceneDirectionalLightData.lightCookieOffset = WrapCloudShadowOffset(
                lightPlaneOffset,
                sceneDirectionalLightData.lightCookieSize);
        }

        private void ApplyCloudShadowProjection()
        {
            if (sceneDirectionalLight == null ||
                sceneDirectionalLightData == null ||
                profile.CloudShadowCookie == null)
            {
                return;
            }

            // A directional cookie is defined on the plane perpendicular to
            // the light. A fixed light-plane size therefore stretches across
            // horizontal ground as the key light approaches the horizon.
            // Scale each cookie axis by its horizontal projection so one repeat
            // keeps the profile's world footprint while the light pitch changes.
            Matrix4x4 worldToLight =
                sceneDirectionalLight.transform.worldToLocalMatrix;
            Vector2 horizontalProjectionScale = new Vector2(
                Mathf.Sqrt(
                    worldToLight.m00 * worldToLight.m00 +
                    worldToLight.m02 * worldToLight.m02),
                Mathf.Sqrt(
                    worldToLight.m10 * worldToLight.m10 +
                    worldToLight.m12 * worldToLight.m12));
            horizontalProjectionScale.x = Mathf.Max(
                MinimumCookieProjectionScale,
                horizontalProjectionScale.x);
            horizontalProjectionScale.y = Mathf.Max(
                MinimumCookieProjectionScale,
                horizontalProjectionScale.y);
            sceneDirectionalLightData.lightCookieSize = Vector2.Scale(
                profile.CloudShadowCookieSize,
                horizontalProjectionScale);
            ApplyCloudShadowOffset();
        }

        private static Vector2 WrapCloudShadowOffset(Vector2 offset, Vector2 cookieSize)
        {
            return new Vector2(
                Mathf.Repeat(offset.x, cookieSize.x),
                Mathf.Repeat(offset.y, cookieSize.y));
        }

        private bool ApplyLighting(
            float evaluatedHour,
            bool forceShelterRefresh = false)
        {
            if (!profile.TryEvaluate(evaluatedHour, out SkyLightingSample sample))
            {
                return false;
            }

            lastAppliedHour = evaluatedHour;
            currentPhase = sample.Phase;

            RenderSettings.ambientMode = AmbientMode.Trilight;
            Color minimumLightColor = profile.MinimumLightColor;
            RenderSettings.ambientSkyColor = MultiplyRgb(
                MaxRgb(
                    sample.AmbientSkyColor,
                    ScaleRgb(minimumLightColor, 0.35f)),
                currentWeatherSample.AmbientTint);
            RenderSettings.ambientEquatorColor = MultiplyRgb(
                MaxRgb(
                    sample.AmbientEquatorColor,
                    ScaleRgb(minimumLightColor, 0.22f)),
                currentWeatherSample.AmbientTint);
            RenderSettings.ambientGroundColor = MultiplyRgb(
                MaxRgb(
                    sample.AmbientGroundColor,
                    ScaleRgb(minimumLightColor, 0.12f)),
                currentWeatherSample.AmbientTint);
            RenderSettings.ambientIntensity =
                Mathf.Max(sample.AmbientIntensity, profile.MinimumAmbientIntensity) *
                currentWeatherSample.AmbientIntensityMultiplier;
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
            ApplyNightActivatedLightVisibility(
                EvaluateNightActivatedLightVisibility(moonContributionWeight));
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
            directionalIntensity *=
                currentWeatherSample.DirectionalIntensityMultiplier;
            directionalColor = MultiplyRgb(
                directionalColor,
                currentWeatherSample.DirectionalTint);

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
            float visibleShadowStrength =
                Mathf.Max(celestialShadowStrength, profile.MinimumShadowStrength) *
                currentWeatherSample.ShadowStrengthMultiplier;
            float cloudShadowElevationWeight = Mathf.Clamp01(
                sunShadowWeight * sunContributionWeight +
                moonShadowWeight * moonContributionWeight);

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
            UpdateCloudShadowFilter(
                cloudShadowElevationWeight,
                currentWeatherSample);
            ApplyCloudShadowProjection();
            rainPresentation?.ApplyWeather(
                currentWeatherSample,
                profile.CloudShadowWorldVelocity,
                forceShelterRefresh);
            lightShaftPresentation?.ApplySunlight(
                sceneDirectionalLight,
                MultiplyRgb(sample.SunColor, currentWeatherSample.DirectionalTint),
                sunContribution *
                currentWeatherSample.DirectionalIntensityMultiplier *
                currentWeatherSample.ShadowStrengthMultiplier,
                currentWeatherSample.PrecipitationIntensity);
            return true;
        }

        private float EvaluateNightActivatedLightVisibility(float nightWeight)
        {
            float fadeStart = Mathf.Clamp01(Mathf.Min(
                nightLightFadeStartWeight,
                nightLightFullyOnWeight));
            float fullyOn = Mathf.Clamp01(Mathf.Max(
                nightLightFadeStartWeight,
                nightLightFullyOnWeight));
            if (fullyOn - fadeStart <= 0.0001f)
            {
                return nightWeight >= fullyOn ? 1f : 0f;
            }

            float normalized = Mathf.InverseLerp(fadeStart, fullyOn, nightWeight);
            return normalized * normalized * (3f - 2f * normalized);
        }

        private void ApplyNightActivatedLightVisibility(
            float visibility,
            bool forceNotification = false)
        {
            float clampedVisibility = Mathf.Clamp01(visibility);
            bool changed = Mathf.Abs(
                currentNightActivatedLightVisibility - clampedVisibility) > 0.0001f;
            currentNightActivatedLightVisibility = clampedVisibility;
            if (changed || forceNotification)
            {
                NightActivatedLightVisibilityChanged?.Invoke(
                    currentNightActivatedLightVisibility);
            }
        }

        private bool InitializeWeather(SkyWeatherType weatherType)
        {
            if (!profile.TryGetWeatherPreset(weatherType, out SkyWeatherPreset preset))
            {
                Debug.LogError(
                    $"Sky lighting profile has no {weatherType} weather preset.",
                    profile);
                return false;
            }

            currentWeatherType = weatherType;
            currentWeatherSample = SkyWeatherSample.FromPreset(preset);
            weatherFromSample = currentWeatherSample;
            weatherToSample = currentWeatherSample;
            weatherTransitionElapsed = profile.WeatherTransitionSeconds;
            weatherTransitionActive = false;
            rainPresentation?.ApplyWeather(
                currentWeatherSample,
                profile.CloudShadowWorldVelocity,
                true);
            return true;
        }

        private bool AdvanceWeatherTransition(float deltaTime)
        {
            if (!weatherTransitionActive)
            {
                return false;
            }

            weatherTransitionElapsed += Mathf.Max(0f, deltaTime);
            float transitionDuration = Mathf.Max(0.01f, profile.WeatherTransitionSeconds);
            float progress = Mathf.Clamp01(weatherTransitionElapsed / transitionDuration);
            currentWeatherSample = SkyWeatherSample.Interpolate(
                weatherFromSample,
                weatherToSample,
                progress);
            if (progress >= 1f)
            {
                currentWeatherSample = weatherToSample;
                weatherTransitionActive = false;
            }

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

        private static Color MultiplyRgb(Color value, Color multiplier)
        {
            return new Color(
                value.r * multiplier.r,
                value.g * multiplier.g,
                value.b * multiplier.b,
                1f);
        }
    }
}
