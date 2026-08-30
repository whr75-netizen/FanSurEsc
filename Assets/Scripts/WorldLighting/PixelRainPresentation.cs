using System.Collections.Generic;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Owns only rain rendering resources derived from the authoritative weather
    /// state and roof colliders. It never changes time, weather, or scene lighting.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    public sealed class PixelRainPresentation : MonoBehaviour
    {
        private const float NoShelterHeight = -10000f;
        private const float MinimumVisibleRain = 0.001f;

        private static readonly int RainIntensityId =
            Shader.PropertyToID("_FantasyRainIntensity");
        private static readonly int RainColorId =
            Shader.PropertyToID("_FantasyRainColor");
        private static readonly int RainVisualTimeId =
            Shader.PropertyToID("_FantasyRainVisualTime");
        private static readonly int RainWorldGridOffsetId =
            Shader.PropertyToID("_FantasyRainWorldGridOffset");
        private static readonly int RainDirectionId =
            Shader.PropertyToID("_FantasyRainDirection");
        private static readonly int ShelterHeightTextureId =
            Shader.PropertyToID("_FantasyRainShelterHeight");
        private static readonly int ShelterWorldRectId =
            Shader.PropertyToID("_FantasyRainShelterWorldRect");
        private static readonly int ShelterReadyId =
            Shader.PropertyToID("_FantasyRainShelterReady");
        private static readonly int ShelterClearanceId =
            Shader.PropertyToID("_FantasyRainShelterClearance");

        [Header("Owner")]
        [SerializeField] private PersistentGameplayShell shell;

        [Header("Collider-derived shelter cache")]
        [SerializeField, Range(32, 1024)] private int shelterMaskResolution = 512;
        [SerializeField, Min(8f)] private float shelterMaskWorldSize = 32f;
        [SerializeField, Min(0.5f)] private float shelterMaskRecenterDistance = 8f;
        [SerializeField, Min(0f)] private float shelterClearance = 0.08f;

        private readonly List<RainShelterOccluder> shelterOccluders =
            new List<RainShelterOccluder>();
        private Texture2D shelterHeightTexture;
        private float[] shelterHeightBuffer;
        private float shelterMaskWorldSpan;
        private Scene boundScene;
        private Vector2 shelterMaskCenter;
        private Vector2 weatherWorldWind;
        private float rainIntensity;
        private float rainVisualTime;
        private Color rainColor = Color.white;
        private bool hasGameplaySceneBinding;
        private bool shelterMaskDirty = true;
        private bool shelterMaskReady;

        public bool IsConfigured => shell != null;
        public bool ShouldRender =>
            hasGameplaySceneBinding && rainIntensity > MinimumVisibleRain;
        public float CurrentRainIntensity => rainIntensity;
        public bool IsShelterMaskReady => shelterMaskReady;
        public int RegisteredShelterCount => shelterOccluders.Count;

        private void Awake()
        {
            if (shell == null)
            {
                shell = GetComponent<PersistentGameplayShell>();
            }

            if (shell == null)
            {
                Debug.LogError("PixelRainPresentation requires the persistent gameplay shell.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            RainShelterOccluder.Registered += HandleShelterRegistered;
            RainShelterOccluder.Unregistered += HandleShelterUnregistered;
            RainShelterOccluder.GeometryChanged += HandleShelterGeometryChanged;
            RenderPipelineManager.beginCameraRendering += HandleBeginCameraRendering;
        }

        private void OnDisable()
        {
            RainShelterOccluder.Registered -= HandleShelterRegistered;
            RainShelterOccluder.Unregistered -= HandleShelterUnregistered;
            RainShelterOccluder.GeometryChanged -= HandleShelterGeometryChanged;
            RenderPipelineManager.beginCameraRendering -= HandleBeginCameraRendering;
            UnbindGameplayScene();
            ReleaseRuntimeResources();
            ResetShaderGlobals();
        }

        internal void BindGameplayScene(Scene scene)
        {
            boundScene = scene;
            hasGameplaySceneBinding = scene.IsValid() && scene.isLoaded;
            shelterOccluders.Clear();
            if (hasGameplaySceneBinding)
            {
                GameObject[] roots = scene.GetRootGameObjects();
                for (int index = 0; index < roots.Length; index++)
                {
                    RainShelterOccluder[] found =
                        roots[index].GetComponentsInChildren<RainShelterOccluder>(true);
                    for (int foundIndex = 0; foundIndex < found.Length; foundIndex++)
                    {
                        AddShelter(found[foundIndex]);
                    }
                }
            }

            InvalidateShelterMask();
            PublishShaderGlobals();
        }

        internal void UnbindGameplayScene()
        {
            boundScene = default;
            hasGameplaySceneBinding = false;
            shelterOccluders.Clear();
            shelterMaskReady = false;
            shelterMaskDirty = true;
            Shader.SetGlobalFloat(ShelterReadyId, 0f);
            Shader.SetGlobalFloat(RainIntensityId, 0f);
        }

        internal void ApplyWeather(
            SkyWeatherSample weather,
            Vector2 worldWind,
            bool forceShelterRefresh)
        {
            bool rainStarted =
                rainIntensity <= MinimumVisibleRain &&
                weather.PrecipitationIntensity > MinimumVisibleRain;
            rainIntensity = Mathf.Clamp01(weather.PrecipitationIntensity);
            rainColor = weather.PrecipitationColor;
            weatherWorldWind = worldWind;

            if (rainStarted)
            {
                InvalidateShelterMask();
            }

            if (ShouldRender && (forceShelterRefresh || rainStarted))
            {
                RefreshShelterMask(true);
            }

            PublishShaderGlobals();
        }

        internal void Tick(float deltaTime)
        {
            if (!hasGameplaySceneBinding)
            {
                return;
            }

            if (ShouldRender)
            {
                rainVisualTime = Mathf.Repeat(
                    rainVisualTime + Mathf.Max(0f, deltaTime),
                    3600f);
                RefreshShelterMask(false);
            }

            PublishShaderGlobals();
        }

        internal void InvalidateShelterMask()
        {
            shelterMaskDirty = true;
            shelterMaskReady = false;
            Shader.SetGlobalFloat(ShelterReadyId, 0f);
        }

        private void RefreshShelterMask(bool force)
        {
            if (!ShouldRender || shell == null || shell.PlayerTransform == null)
            {
                return;
            }

            int resolution = Mathf.Clamp(shelterMaskResolution, 32, 1024);
            RemoveInvalidShelters();
            if (shelterOccluders.Count == 0)
            {
                shelterMaskDirty = false;
                shelterMaskReady = false;
                Shader.SetGlobalFloat(ShelterReadyId, 0f);
                return;
            }

            float worldSize = CalculateShelterWorldSize();
            float cellSize = worldSize / resolution;
            Vector3 playerPosition = shell.PlayerTransform.position;
            Vector2 desiredCenter = new Vector2(
                Mathf.Round(playerPosition.x / cellSize) * cellSize,
                Mathf.Round(playerPosition.z / cellSize) * cellSize);
            bool centerMoved =
                !shelterMaskReady ||
                Vector2.Distance(desiredCenter, shelterMaskCenter) >=
                shelterMaskRecenterDistance;
            bool spanChanged =
                !Mathf.Approximately(worldSize, shelterMaskWorldSpan);
            if (!force && !shelterMaskDirty && !centerMoved && !spanChanged)
            {
                return;
            }

            EnsureShelterTexture(resolution);
            for (int index = 0; index < shelterHeightBuffer.Length; index++)
            {
                shelterHeightBuffer[index] = NoShelterHeight;
            }

            shelterMaskCenter = desiredCenter;
            shelterMaskWorldSpan = worldSize;
            float worldMinX = shelterMaskCenter.x - worldSize * 0.5f;
            float worldMinZ = shelterMaskCenter.y - worldSize * 0.5f;
            // Geometry authors can move or resize a roof and immediately call
            // NotifyGeometryChanged. Synchronize once per cache rebuild so the
            // collider authority is current before any top-height raycasts.
            Physics.SyncTransforms();
            for (int index = shelterOccluders.Count - 1; index >= 0; index--)
            {
                RainShelterOccluder shelter = shelterOccluders[index];
                shelter.RasterizeTopHeights(
                    worldMinX,
                    worldMinZ,
                    cellSize,
                    resolution,
                    shelterHeightBuffer);
            }

            shelterHeightTexture.SetPixelData(shelterHeightBuffer, 0);
            shelterHeightTexture.Apply(false, false);
            Shader.SetGlobalTexture(ShelterHeightTextureId, shelterHeightTexture);
            Shader.SetGlobalVector(
                ShelterWorldRectId,
                new Vector4(worldMinX, worldMinZ, 1f / worldSize, 1f / worldSize));
            shelterMaskDirty = false;
            shelterMaskReady = true;
            Shader.SetGlobalFloat(ShelterReadyId, 1f);
        }

        private void EnsureShelterTexture(int resolution)
        {
            if (shelterHeightTexture != null &&
                shelterHeightTexture.width == resolution &&
                shelterHeightTexture.height == resolution &&
                shelterHeightBuffer != null &&
                shelterHeightBuffer.Length == resolution * resolution)
            {
                return;
            }

            ReleaseRuntimeResources();
            shelterHeightTexture = new Texture2D(
                resolution,
                resolution,
                TextureFormat.RFloat,
                false,
                true)
            {
                name = "Runtime Rain Shelter Heights",
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
                hideFlags = HideFlags.HideAndDontSave
            };
            shelterHeightBuffer = new float[resolution * resolution];
        }

        private void PublishShaderGlobals()
        {
            float visibleIntensity = hasGameplaySceneBinding ? rainIntensity : 0f;
            Shader.SetGlobalFloat(RainIntensityId, visibleIntensity);
            Shader.SetGlobalColor(RainColorId, rainColor);
            Shader.SetGlobalFloat(RainVisualTimeId, rainVisualTime);
            Shader.SetGlobalFloat(ShelterClearanceId, shelterClearance);
            PublishCameraShaderGlobals(shell != null ? shell.PlayerCamera : null);
        }

        private void HandleBeginCameraRendering(
            ScriptableRenderContext context,
            Camera camera)
        {
            if (camera != null && shell != null && camera == shell.PlayerCamera)
            {
                // Camera follow and smooth zoom finish in LateUpdate. Re-publish
                // the camera-derived coordinates at the render boundary so the
                // rain pattern never uses the previous frame's camera transform.
                PublishCameraShaderGlobals(camera);
            }
        }

        private void PublishCameraShaderGlobals(Camera camera)
        {
            float rainDirection = 1f;
            Vector2 worldGridOffset = Vector2.zero;
            if (camera != null && shell != null && shell.PlayerTransform != null)
            {
                Vector3 projectedWorldOrigin = camera.WorldToScreenPoint(Vector3.zero);
                worldGridOffset = new Vector2(
                    -projectedWorldOrigin.x,
                    -projectedWorldOrigin.y);

                Vector3 origin = shell.PlayerTransform.position;
                Vector3 displaced = origin +
                    new Vector3(weatherWorldWind.x, 0f, weatherWorldWind.y);
                float screenDeltaX =
                    camera.WorldToScreenPoint(displaced).x -
                    camera.WorldToScreenPoint(origin).x;
                if (Mathf.Abs(screenDeltaX) > 0.05f)
                {
                    rainDirection = screenDeltaX > 0f ? 1f : -1f;
                }
            }

            Shader.SetGlobalVector(
                RainWorldGridOffsetId,
                new Vector4(worldGridOffset.x, worldGridOffset.y, 0f, 0f));
            Shader.SetGlobalFloat(RainDirectionId, rainDirection);
        }

        private float CalculateShelterWorldSize()
        {
            float configuredSize = Mathf.Max(8f, shelterMaskWorldSize);
            Camera camera = shell != null ? shell.PlayerCamera : null;
            if (camera == null || !camera.orthographic)
            {
                return configuredSize;
            }

            float maximumOrthographicSize = camera.orthographicSize;
            CameraZoomController zoom = camera.GetComponent<CameraZoomController>();
            if (zoom != null)
            {
                maximumOrthographicSize = Mathf.Max(
                    maximumOrthographicSize,
                    zoom.MaxOrthographicSize);
            }

            Vector3 forward = camera.transform.forward;
            float forwardY = forward.y;
            if (Mathf.Abs(forwardY) <= 0.01f)
            {
                return configuredSize;
            }

            // Project the orthographic viewport basis onto the Player's XZ
            // plane along the camera ray. Summing absolute corner extents gives
            // the axis-aligned footprint even when the quarter-view camera has yaw.
            Vector3 right = camera.transform.right;
            Vector3 up = camera.transform.up;
            Vector3 groundRight = right - forward * (right.y / forwardY);
            Vector3 groundUp = up - forward * (up.y / forwardY);
            float halfWidth =
                maximumOrthographicSize * Mathf.Max(1f, camera.aspect);
            float halfHeight = maximumOrthographicSize;
            float groundSpanX = 2f * (
                Mathf.Abs(groundRight.x) * halfWidth +
                Mathf.Abs(groundUp.x) * halfHeight);
            float groundSpanZ = 2f * (
                Mathf.Abs(groundRight.z) * halfWidth +
                Mathf.Abs(groundUp.z) * halfHeight);
            float requiredSpan =
                Mathf.Max(groundSpanX, groundSpanZ) +
                2f * Mathf.Max(0f, shelterMaskRecenterDistance);
            return Mathf.Max(configuredSize, requiredSpan);
        }

        private void RemoveInvalidShelters()
        {
            for (int index = shelterOccluders.Count - 1; index >= 0; index--)
            {
                RainShelterOccluder shelter = shelterOccluders[index];
                if (shelter == null ||
                    !shelter.isActiveAndEnabled ||
                    shelter.gameObject.scene != boundScene)
                {
                    shelterOccluders.RemoveAt(index);
                }
            }
        }

        private void HandleShelterRegistered(RainShelterOccluder shelter)
        {
            if (shelter != null &&
                hasGameplaySceneBinding &&
                shelter.gameObject.scene == boundScene)
            {
                AddShelter(shelter);
                InvalidateShelterMask();
            }
        }

        private void HandleShelterUnregistered(RainShelterOccluder shelter)
        {
            if (shelterOccluders.Remove(shelter))
            {
                InvalidateShelterMask();
            }
        }

        private void HandleShelterGeometryChanged(RainShelterOccluder shelter)
        {
            if (shelter != null && shelterOccluders.Contains(shelter))
            {
                InvalidateShelterMask();
            }
        }

        private void AddShelter(RainShelterOccluder shelter)
        {
            if (shelter != null &&
                shelter.isActiveAndEnabled &&
                !shelterOccluders.Contains(shelter))
            {
                shelterOccluders.Add(shelter);
            }
        }

        private void ReleaseRuntimeResources()
        {
            if (shelterHeightTexture != null)
            {
                if (Application.isPlaying)
                {
                    Destroy(shelterHeightTexture);
                }
                else
                {
                    DestroyImmediate(shelterHeightTexture);
                }
            }

            shelterHeightTexture = null;
            shelterHeightBuffer = null;
            shelterMaskReady = false;
        }

        private static void ResetShaderGlobals()
        {
            Shader.SetGlobalFloat(RainIntensityId, 0f);
            Shader.SetGlobalFloat(ShelterReadyId, 0f);
        }
    }
}
