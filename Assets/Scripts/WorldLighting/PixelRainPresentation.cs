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
        private const int SplashFrameCount = 4;
        private const int SplashFrameWidth = 7;
        private const int SplashFrameHeight = 4;
        private const int MaximumSplashSpawnsPerTick = 4;

        private static readonly int RainIntensityId =
            Shader.PropertyToID("_FantasyRainIntensity");
        private static readonly int RainColorId =
            Shader.PropertyToID("_FantasyRainColor");
        private static readonly int RainVisualTimeId =
            Shader.PropertyToID("_FantasyRainVisualTime");
        private static readonly int RainWorldGridOffsetId =
            Shader.PropertyToID("_FantasyRainWorldGridOffset");
        private static readonly int RainWorldUnitsPerScreenPixelId =
            Shader.PropertyToID("_FantasyRainWorldUnitsPerScreenPixel");
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
        private static readonly int SplashFrameId =
            Shader.PropertyToID("_SplashFrame");

        [Header("Owner")]
        [SerializeField] private PersistentGameplayShell shell;

        [Header("Collider-derived shelter cache")]
        [SerializeField, Range(32, 1024)] private int shelterMaskResolution = 512;
        [SerializeField, Min(8f)] private float shelterMaskWorldSize = 32f;
        [SerializeField, Min(0.5f)] private float shelterMaskRecenterDistance = 8f;
        [SerializeField, Min(0f)] private float shelterClearance = 0.08f;

        [Header("Collider impact splashes")]
        [SerializeField] private Material splashImpactMaterial;
        [SerializeField, Range(4, 64)] private int splashImpactPoolSize = 24;
        [SerializeField, Min(0f)] private float splashImpactsPerSecond = 34f;
        [SerializeField, Range(1f, 30f)] private float splashFramesPerSecond = 20f;
        [SerializeField, Range(1, 4)] private int splashPixelScale = 2;
        [SerializeField, Min(0.0001f)] private float splashWorldUnitsPerAtlasPixel =
            0.0111f;
        [SerializeField, Range(0f, 1f)] private float splashMinimumNormalY = 0.75f;
        [SerializeField, Min(0f)] private float splashSurfaceOffset = 0.015f;
        [SerializeField] private LayerMask splashCollisionMask =
            Physics.DefaultRaycastLayers;

        private readonly List<RainShelterOccluder> shelterOccluders =
            new List<RainShelterOccluder>();
        private readonly RaycastHit[] splashRaycastHits = new RaycastHit[32];
        private Texture2D shelterHeightTexture;
        private float[] shelterHeightBuffer;
        private Mesh splashImpactMesh;
        private SplashImpact[] splashImpacts;
        private MaterialPropertyBlock splashPropertyBlock;
        private float shelterMaskWorldSpan;
        private Scene boundScene;
        private Vector2 shelterMaskCenter;
        private Vector2 weatherWorldWind;
        private float rainIntensity;
        private float rainVisualTime;
        private Color rainColor = Color.white;
        private float splashSpawnAccumulator;
        private uint splashSpawnSequence;
        private bool hasGameplaySceneBinding;
        private bool shelterMaskDirty = true;
        private bool shelterMaskReady;

        private sealed class SplashImpact
        {
            public Transform Transform;
            public MeshRenderer Renderer;
            public Collider SurfaceCollider;
            public Vector3 SurfaceLocalAnchor;
            public float Age;
            public int Frame = -1;
            public bool Active;
        }

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
            DeactivateSplashImpacts();
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

            if (!ShouldRender)
            {
                DeactivateSplashImpacts();
            }

            PublishShaderGlobals();
        }

        internal void Tick(float deltaTime)
        {
            if (!hasGameplaySceneBinding)
            {
                return;
            }

            float safeDeltaTime = Mathf.Max(0f, deltaTime);
            if (ShouldRender)
            {
                rainVisualTime = Mathf.Repeat(
                    rainVisualTime + safeDeltaTime,
                    3600f);
                RefreshShelterMask(false);
                TickSplashImpacts(safeDeltaTime);
            }
            else
            {
                DeactivateSplashImpacts();
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

            ReleaseShelterResources();
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
            float worldUnitsPerScreenPixel = 1f;
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

                if (camera.orthographic)
                {
                    worldUnitsPerScreenPixel =
                        2f * camera.orthographicSize /
                        Mathf.Max(camera.pixelHeight, 1);
                }
            }

            Shader.SetGlobalVector(
                RainWorldGridOffsetId,
                new Vector4(worldGridOffset.x, worldGridOffset.y, 0f, 0f));
            Shader.SetGlobalFloat(
                RainWorldUnitsPerScreenPixelId,
                worldUnitsPerScreenPixel);
            Shader.SetGlobalFloat(RainDirectionId, rainDirection);
            UpdateSplashImpactTransforms(camera);
        }

        private void TickSplashImpacts(float deltaTime)
        {
            UpdateSplashImpactFrames(deltaTime);
            if (splashImpactMaterial == null ||
                splashImpactsPerSecond <= 0f ||
                shell == null ||
                shell.PlayerCamera == null)
            {
                return;
            }

            float requestedSpawns =
                deltaTime * splashImpactsPerSecond * rainIntensity;
            splashSpawnAccumulator = Mathf.Min(
                splashSpawnAccumulator + requestedSpawns,
                MaximumSplashSpawnsPerTick);
            int spawnCount = Mathf.Min(
                Mathf.FloorToInt(splashSpawnAccumulator),
                MaximumSplashSpawnsPerTick);
            splashSpawnAccumulator -= spawnCount;

            for (int index = 0; index < spawnCount; index++)
            {
                TrySpawnSplashImpact(shell.PlayerCamera);
            }
        }

        private void UpdateSplashImpactFrames(float deltaTime)
        {
            if (splashImpacts == null)
            {
                return;
            }

            float framesPerSecond = Mathf.Max(1f, splashFramesPerSecond);
            for (int index = 0; index < splashImpacts.Length; index++)
            {
                SplashImpact impact = splashImpacts[index];
                if (impact == null || !impact.Active)
                {
                    continue;
                }

                impact.Age += deltaTime;
                int frame = Mathf.FloorToInt(impact.Age * framesPerSecond);
                if (frame >= SplashFrameCount)
                {
                    SetSplashImpactActive(impact, false);
                    continue;
                }

                SetSplashImpactFrame(impact, frame);
            }
        }

        private void TrySpawnSplashImpact(Camera camera)
        {
            if (camera == null || !boundScene.IsValid() || !boundScene.isLoaded)
            {
                return;
            }

            EnsureSplashImpactPool();
            if (splashImpacts == null || splashImpacts.Length == 0)
            {
                return;
            }

            uint sequence = ++splashSpawnSequence;
            float viewportX = Mathf.Lerp(
                0.03f,
                0.97f,
                HashToUnit(unchecked(sequence * 0x9E3779B9u + 0x85EBCA6Bu)));
            float viewportY = Mathf.Lerp(
                0.03f,
                0.97f,
                HashToUnit(unchecked(sequence * 0xC2B2AE35u + 0x27D4EB2Fu)));
            Ray cameraRay = camera.ViewportPointToRay(
                new Vector3(viewportX, viewportY, 0f));
            int hitCount = Physics.RaycastNonAlloc(
                cameraRay,
                splashRaycastHits,
                Mathf.Max(camera.farClipPlane, 1f),
                splashCollisionMask,
                QueryTriggerInteraction.Ignore);

            int selectedHit = -1;
            float selectedDistance = float.PositiveInfinity;
            for (int index = 0; index < hitCount; index++)
            {
                RaycastHit hit = splashRaycastHits[index];
                Collider collider = hit.collider;
                if (collider == null ||
                    collider.gameObject.scene != boundScene ||
                    hit.distance >= selectedDistance)
                {
                    continue;
                }

                selectedHit = index;
                selectedDistance = hit.distance;
            }

            if (selectedHit < 0)
            {
                return;
            }

            RaycastHit selected = splashRaycastHits[selectedHit];
            if (selected.normal.y < Mathf.Clamp01(splashMinimumNormalY) ||
                IsPointSheltered(selected.point))
            {
                return;
            }

            ActivateSplashImpact(selected);
        }

        private void ActivateSplashImpact(RaycastHit hit)
        {
            SplashImpact impact = FindAvailableSplashImpact();
            if (impact == null)
            {
                return;
            }

            Vector3 worldAnchor =
                hit.point + hit.normal * Mathf.Max(0f, splashSurfaceOffset);
            impact.SurfaceCollider = hit.collider;
            impact.SurfaceLocalAnchor =
                hit.collider.transform.InverseTransformPoint(worldAnchor);
            impact.Transform.position = worldAnchor;
            impact.Age = 0f;
            impact.Frame = -1;
            SetSplashImpactFrame(impact, 0);
            SetSplashImpactActive(impact, true);
        }

        private SplashImpact FindAvailableSplashImpact()
        {
            SplashImpact oldest = null;
            for (int index = 0; index < splashImpacts.Length; index++)
            {
                SplashImpact impact = splashImpacts[index];
                if (!impact.Active)
                {
                    return impact;
                }

                if (oldest == null || impact.Age > oldest.Age)
                {
                    oldest = impact;
                }
            }

            return oldest;
        }

        private void EnsureSplashImpactPool()
        {
            int requiredSize = Mathf.Clamp(splashImpactPoolSize, 4, 64);
            if (splashImpacts != null &&
                splashImpacts.Length == requiredSize &&
                splashImpactMesh != null)
            {
                return;
            }

            ReleaseSplashImpactResources();
            splashImpactMesh = CreateSplashImpactMesh();
            splashPropertyBlock = new MaterialPropertyBlock();
            splashImpacts = new SplashImpact[requiredSize];
            for (int index = 0; index < requiredSize; index++)
            {
                GameObject splashObject = new GameObject(
                    $"Runtime Rain Splash {index:00}")
                {
                    hideFlags = HideFlags.HideAndDontSave,
                    layer = gameObject.layer
                };
                splashObject.transform.SetParent(transform, false);

                MeshFilter meshFilter = splashObject.AddComponent<MeshFilter>();
                meshFilter.sharedMesh = splashImpactMesh;
                MeshRenderer meshRenderer = splashObject.AddComponent<MeshRenderer>();
                meshRenderer.sharedMaterial = splashImpactMaterial;
                meshRenderer.shadowCastingMode = ShadowCastingMode.Off;
                meshRenderer.receiveShadows = false;
                meshRenderer.lightProbeUsage = LightProbeUsage.Off;
                meshRenderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
                meshRenderer.allowOcclusionWhenDynamic = false;
                meshRenderer.enabled = false;

                splashImpacts[index] = new SplashImpact
                {
                    Transform = splashObject.transform,
                    Renderer = meshRenderer
                };
            }
        }

        private static Mesh CreateSplashImpactMesh()
        {
            Mesh mesh = new Mesh
            {
                name = "Runtime Pixel Rain Splash Quad",
                hideFlags = HideFlags.HideAndDontSave
            };
            mesh.vertices = new[]
            {
                new Vector3(-0.5f, 0f, 0f),
                new Vector3(0.5f, 0f, 0f),
                new Vector3(-0.5f, 1f, 0f),
                new Vector3(0.5f, 1f, 0f)
            };
            mesh.uv = new[]
            {
                new Vector2(0f, 0f),
                new Vector2(1f, 0f),
                new Vector2(0f, 1f),
                new Vector2(1f, 1f)
            };
            mesh.triangles = new[] { 0, 2, 1, 2, 3, 1 };
            mesh.RecalculateBounds();
            return mesh;
        }

        private void UpdateSplashImpactTransforms(Camera camera)
        {
            if (camera == null || splashImpacts == null)
            {
                return;
            }

            int pixelScale = Mathf.Clamp(splashPixelScale, 1, 4);
            float worldUnitsPerAtlasPixel = Mathf.Max(
                0.0001f,
                splashWorldUnitsPerAtlasPixel);
            float width =
                SplashFrameWidth * pixelScale * worldUnitsPerAtlasPixel;
            float height =
                SplashFrameHeight * pixelScale * worldUnitsPerAtlasPixel;
            Quaternion rotation = camera.transform.rotation;
            Vector3 scale = new Vector3(width, height, 1f);
            for (int index = 0; index < splashImpacts.Length; index++)
            {
                SplashImpact impact = splashImpacts[index];
                if (impact == null || !impact.Active)
                {
                    continue;
                }

                Collider surface = impact.SurfaceCollider;
                if (surface == null ||
                    !surface.enabled ||
                    !surface.gameObject.activeInHierarchy ||
                    surface.gameObject.scene != boundScene)
                {
                    SetSplashImpactActive(impact, false);
                    continue;
                }

                Vector3 worldAnchor = surface.transform.TransformPoint(
                    impact.SurfaceLocalAnchor);
                Vector3 screenAnchor = camera.WorldToScreenPoint(worldAnchor);
                if (screenAnchor.z <= 0f)
                {
                    SetSplashImpactActive(impact, false);
                    continue;
                }

                // The impact has a fixed world size now, so its projected width
                // is intentionally fractional at arbitrary smooth zoom levels.
                // Snap only the bottom-center anchor; changing half-pixel parity
                // during zoom would add a visible sideways jump.
                screenAnchor.x = Mathf.Round(screenAnchor.x);
                screenAnchor.y = Mathf.Round(screenAnchor.y);

                impact.Transform.position = camera.ScreenToWorldPoint(screenAnchor);
                impact.Transform.rotation = rotation;
                impact.Transform.localScale = scale;
            }
        }

        private void SetSplashImpactFrame(SplashImpact impact, int frame)
        {
            if (impact.Frame == frame || impact.Renderer == null)
            {
                return;
            }

            impact.Frame = frame;
            splashPropertyBlock ??= new MaterialPropertyBlock();
            impact.Renderer.GetPropertyBlock(splashPropertyBlock);
            splashPropertyBlock.SetFloat(SplashFrameId, frame);
            impact.Renderer.SetPropertyBlock(splashPropertyBlock);
            splashPropertyBlock.Clear();
        }

        private static void SetSplashImpactActive(
            SplashImpact impact,
            bool active)
        {
            impact.Active = active;
            if (!active)
            {
                impact.SurfaceCollider = null;
            }

            if (impact.Renderer != null)
            {
                impact.Renderer.enabled = active;
            }
        }

        private void DeactivateSplashImpacts()
        {
            splashSpawnAccumulator = 0f;
            if (splashImpacts == null)
            {
                return;
            }

            for (int index = 0; index < splashImpacts.Length; index++)
            {
                SplashImpact impact = splashImpacts[index];
                if (impact != null)
                {
                    SetSplashImpactActive(impact, false);
                }
            }
        }

        private static float HashToUnit(uint value)
        {
            value ^= value >> 16;
            value *= 0x7FEB352Du;
            value ^= value >> 15;
            value *= 0x846CA68Bu;
            value ^= value >> 16;
            return (value & 0x00FFFFFFu) / 16777216f;
        }

        private bool IsPointSheltered(Vector3 position)
        {
            if (!shelterMaskReady ||
                shelterHeightBuffer == null ||
                shelterHeightTexture == null ||
                shelterMaskWorldSpan <= 0f)
            {
                return false;
            }

            float worldMinimumX =
                shelterMaskCenter.x - shelterMaskWorldSpan * 0.5f;
            float worldMinimumZ =
                shelterMaskCenter.y - shelterMaskWorldSpan * 0.5f;
            float normalizedX =
                (position.x - worldMinimumX) / shelterMaskWorldSpan;
            float normalizedZ =
                (position.z - worldMinimumZ) / shelterMaskWorldSpan;
            if (normalizedX < 0f || normalizedX > 1f ||
                normalizedZ < 0f || normalizedZ > 1f)
            {
                return false;
            }

            int resolution = shelterHeightTexture.width;
            int x = Mathf.Clamp(
                Mathf.FloorToInt(normalizedX * resolution),
                0,
                resolution - 1);
            int z = Mathf.Clamp(
                Mathf.FloorToInt(normalizedZ * resolution),
                0,
                resolution - 1);
            float roofHeight = shelterHeightBuffer[z * resolution + x];
            return position.y + shelterClearance <= roofHeight;
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
            ReleaseShelterResources();
            ReleaseSplashImpactResources();
        }

        private void ReleaseShelterResources()
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

        private void ReleaseSplashImpactResources()
        {
            if (splashImpacts != null)
            {
                for (int index = 0; index < splashImpacts.Length; index++)
                {
                    SplashImpact impact = splashImpacts[index];
                    if (impact != null && impact.Transform != null)
                    {
                        DestroyRuntimeObject(impact.Transform.gameObject);
                    }
                }
            }

            if (splashImpactMesh != null)
            {
                DestroyRuntimeObject(splashImpactMesh);
            }

            splashImpacts = null;
            splashImpactMesh = null;
            splashPropertyBlock = null;
            splashSpawnAccumulator = 0f;
        }

        private static void DestroyRuntimeObject(Object target)
        {
            if (target == null)
            {
                return;
            }

            if (Application.isPlaying)
            {
                Destroy(target);
            }
            else
            {
                DestroyImmediate(target);
            }
        }

        private static void ResetShaderGlobals()
        {
            Shader.SetGlobalFloat(RainIntensityId, 0f);
            Shader.SetGlobalFloat(RainWorldUnitsPerScreenPixelId, 1f);
            Shader.SetGlobalFloat(ShelterReadyId, 0f);
        }
    }
}
