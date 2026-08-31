using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Draws the atmosphere-only sun shafts and exposes the shared visibility
    /// and weather settings consumed by the local-volumetric renderer feature.
    /// It owns only temporary rendering resources and no light state.
    /// </summary>
    [DefaultExecutionOrder(10000)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stylized Light Shaft Presentation")]
    public sealed class StylizedLightShaftPresentation : MonoBehaviour
    {
        private const int MaximumSunSliceCount = 16;
        private const int MaximumLocalEmitterCount = 16;
        private const float MinimumVisibleIntensity = 0.0001f;

        private static readonly int ColorId = Shader.PropertyToID("_ShaftColor");
        private static readonly int IntensityId = Shader.PropertyToID("_ShaftIntensity");
        private static readonly int ShadowThresholdId = Shader.PropertyToID("_ShadowThreshold");
        private static readonly int DensityBandsId = Shader.PropertyToID("_DensityBands");
        private static readonly int NoiseStrengthId = Shader.PropertyToID("_NoiseStrength");
        private static readonly int WorldCellSizeId = Shader.PropertyToID("_WorldCellSize");
        private static readonly int SurfaceFadeDistanceId =
            Shader.PropertyToID("_SurfaceFadeDistance");

        [Header("References")]
        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private Shader shaftShader;

        [Header("Sun Shafts")]
        [SerializeField, Range(4, MaximumSunSliceCount)] private int sunSliceCount = 10;
        [SerializeField, Min(1f)] private float sunVolumeHeight = 6f;
        [SerializeField, Min(0f)] private float sunVolumeMargin = 2.5f;
        [SerializeField] private float sunVolumeBaseHeight = 0.02f;
        [SerializeField, Min(0f)] private float sunIntensityMultiplier = 0.018f;
        [SerializeField, Range(0f, 1f)] private float sunShadowThreshold = 0.52f;
        [SerializeField, Range(2, 8)] private int sunDensityBands = 4;
        [SerializeField, Range(0f, 1f)] private float sunNoiseStrength = 0.16f;
        [SerializeField, Min(0.01f)] private float sunWorldCellSize = 0.22f;
        [SerializeField, Min(0.01f)] private float sunSurfaceFadeDistance = 0.45f;
        [SerializeField, Range(0f, 1f)] private float rainSuppression = 0.92f;

        [Header("Local Volumetric Lights")]
        [SerializeField, Range(1, MaximumLocalEmitterCount)]
        private int visibleLocalEmitterLimit = 8;
        [SerializeField, Range(1f, 2f)] private float localRainScatterMultiplier = 1.35f;

        private Material sunMaterial;
        private Mesh sunSliceMesh;
        private Vector3[] sunVertices;
        private Light sunLight;
        private Color sunColor = Color.white;
        private float sunStrength;
        private float rainIntensity;
        private Camera cachedLayoutCamera;
        private CameraZoomController cachedZoomController;

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

        private void OnEnable()
        {
            if (Application.isPlaying)
            {
                EnsureResources();
            }
        }

        private void OnDisable()
        {
            ReleaseResources();
        }

        private void OnDestroy()
        {
            ReleaseResources();
        }

        private void OnValidate()
        {
            sunSliceCount = Mathf.Clamp(sunSliceCount, 4, MaximumSunSliceCount);
            sunVolumeHeight = Mathf.Max(1f, sunVolumeHeight);
            sunVolumeMargin = Mathf.Max(0f, sunVolumeMargin);
            sunIntensityMultiplier = Mathf.Max(0f, sunIntensityMultiplier);
            sunShadowThreshold = Mathf.Clamp01(sunShadowThreshold);
            sunDensityBands = Mathf.Clamp(sunDensityBands, 2, 8);
            sunNoiseStrength = Mathf.Clamp01(sunNoiseStrength);
            sunWorldCellSize = Mathf.Max(0.01f, sunWorldCellSize);
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

        private void LateUpdate()
        {
            if (!Application.isPlaying || !EnsureResources())
            {
                return;
            }

            Camera camera = shell != null ? shell.PlayerCamera : null;
            if (camera == null || !camera.isActiveAndEnabled)
            {
                return;
            }

            DrawSunShafts(camera);
        }

        private void DrawSunShafts(Camera camera)
        {
            float weatherVisibility = 1f - rainIntensity * rainSuppression;
            float visibleIntensity =
                sunStrength * sunIntensityMultiplier * Mathf.Clamp01(weatherVisibility);
            if (sunLight == null ||
                !sunLight.isActiveAndEnabled ||
                visibleIntensity <= MinimumVisibleIntensity)
            {
                return;
            }

            Vector3 rayDirection = sunLight.transform.forward.normalized;
            if (rayDirection.y >= -0.05f || !UpdateSunSliceMesh(camera, rayDirection))
            {
                return;
            }

            ApplyMaterialProperties(
                sunMaterial,
                sunColor,
                visibleIntensity,
                sunShadowThreshold,
                sunDensityBands,
                sunNoiseStrength,
                sunWorldCellSize,
                sunSurfaceFadeDistance);
            DrawMesh(sunSliceMesh, Matrix4x4.identity, sunMaterial, camera);
        }

        private bool UpdateSunSliceMesh(Camera camera, Vector3 rayDirection)
        {
            Ray centerRay = camera.ViewportPointToRay(new Vector3(0.5f, 0.5f));
            if (Mathf.Abs(centerRay.direction.y) <= 0.0001f)
            {
                return false;
            }

            float groundDistance =
                (sunVolumeBaseHeight - centerRay.origin.y) / centerRay.direction.y;
            if (groundDistance <= 0f)
            {
                return false;
            }

            Vector3 groundCenter = centerRay.origin + centerRay.direction * groundDistance;
            groundCenter.y = sunVolumeBaseHeight;

            Vector3 across = Vector3.Cross(rayDirection, camera.transform.forward);
            across = Vector3.ProjectOnPlane(across, Vector3.up);
            if (across.sqrMagnitude <= 0.0001f)
            {
                across = Vector3.ProjectOnPlane(camera.transform.right, Vector3.up);
            }
            across.Normalize();

            Vector3 planeNormal = Vector3.Cross(across, rayDirection).normalized;
            Vector3 sliceAxis = Vector3.ProjectOnPlane(planeNormal, Vector3.up);
            if (sliceAxis.sqrMagnitude <= 0.0001f)
            {
                sliceAxis = Vector3.Cross(Vector3.up, across);
            }
            sliceAxis.Normalize();

            float layoutOrthographicSize = GetLayoutOrthographicSize(camera);
            float cameraGroundDepth = camera.orthographic
                ? layoutOrthographicSize /
                  Mathf.Max(Mathf.Abs(camera.transform.forward.y), 0.2f)
                : 10f;
            float cameraGroundWidth = camera.orthographic
                ? layoutOrthographicSize * camera.aspect
                : 10f;
            float halfCoverage =
                Mathf.Max(cameraGroundDepth, cameraGroundWidth) + sunVolumeMargin;
            float sliceSpacing = halfCoverage * 2f / Mathf.Max(sunSliceCount - 1, 1);
            float centerCoordinate = Vector3.Dot(groundCenter, sliceAxis);
            float snappedCoordinate =
                Mathf.Round(centerCoordinate / sliceSpacing) * sliceSpacing;
            groundCenter += sliceAxis * (snappedCoordinate - centerCoordinate);

            float rayLength =
                sunVolumeHeight / Mathf.Max(-rayDirection.y, 0.05f);
            Vector3 towardSun = -rayDirection * rayLength;
            float halfWidth = halfCoverage * 1.35f;

            Bounds bounds = new Bounds(groundCenter, Vector3.zero);
            for (int slice = 0; slice < sunSliceCount; slice++)
            {
                float offset = (slice - (sunSliceCount - 1) * 0.5f) * sliceSpacing;
                Vector3 bottomCenter = groundCenter + sliceAxis * offset;
                Vector3 topCenter = bottomCenter + towardSun;
                int vertexIndex = slice * 4;
                sunVertices[vertexIndex] = bottomCenter - across * halfWidth;
                sunVertices[vertexIndex + 1] = bottomCenter + across * halfWidth;
                sunVertices[vertexIndex + 2] = topCenter - across * halfWidth;
                sunVertices[vertexIndex + 3] = topCenter + across * halfWidth;
                bounds.Encapsulate(sunVertices[vertexIndex]);
                bounds.Encapsulate(sunVertices[vertexIndex + 1]);
                bounds.Encapsulate(sunVertices[vertexIndex + 2]);
                bounds.Encapsulate(sunVertices[vertexIndex + 3]);
            }

            sunSliceMesh.SetVertices(sunVertices);
            sunSliceMesh.bounds = bounds;
            return true;
        }

        private float GetLayoutOrthographicSize(Camera camera)
        {
            if (!camera.orthographic)
            {
                return camera.orthographicSize;
            }

            if (cachedLayoutCamera != camera)
            {
                cachedLayoutCamera = camera;
                cachedZoomController = camera.GetComponent<CameraZoomController>();
            }

            return cachedZoomController != null
                ? Mathf.Max(camera.orthographicSize, cachedZoomController.MaxOrthographicSize)
                : camera.orthographicSize;
        }

        private static void ApplyMaterialProperties(
            Material material,
            Color color,
            float intensity,
            float shadowThreshold,
            float densityBands,
            float noiseStrength,
            float worldCellSize,
            float surfaceFadeDistance)
        {
            material.SetColor(ColorId, color);
            material.SetFloat(IntensityId, intensity);
            material.SetFloat(ShadowThresholdId, shadowThreshold);
            material.SetFloat(DensityBandsId, densityBands);
            material.SetFloat(NoiseStrengthId, noiseStrength);
            material.SetFloat(WorldCellSizeId, worldCellSize);
            material.SetFloat(SurfaceFadeDistanceId, surfaceFadeDistance);
        }

        private void DrawMesh(
            Mesh mesh,
            Matrix4x4 matrix,
            Material material,
            Camera camera)
        {
            Graphics.DrawMesh(
                mesh,
                matrix,
                material,
                gameObject.layer,
                camera,
                0,
                null,
                ShadowCastingMode.Off,
                false,
                null,
                LightProbeUsage.Off);
        }

        private bool EnsureResources()
        {
            if (sunMaterial != null &&
                sunMaterial.shader == shaftShader &&
                sunSliceMesh != null &&
                sunVertices != null &&
                sunVertices.Length == sunSliceCount * 4)
            {
                return true;
            }

            ReleaseResources();
            if (shaftShader == null || !shaftShader.isSupported)
            {
                return false;
            }

            sunMaterial = CreateRuntimeMaterial("Runtime Stylized Sun Shafts");
            sunSliceMesh = CreateSunSliceMesh();
            return true;
        }

        private Material CreateRuntimeMaterial(string materialName)
        {
            return new Material(shaftShader)
            {
                name = materialName,
                hideFlags = HideFlags.HideAndDontSave
            };
        }

        private Mesh CreateSunSliceMesh()
        {
            int vertexCount = sunSliceCount * 4;
            sunVertices = new Vector3[vertexCount];
            Vector2[] uvs = new Vector2[vertexCount];
            int[] triangles = new int[sunSliceCount * 6];
            for (int slice = 0; slice < sunSliceCount; slice++)
            {
                int vertexIndex = slice * 4;
                uvs[vertexIndex] = new Vector2(0f, 0f);
                uvs[vertexIndex + 1] = new Vector2(1f, 0f);
                uvs[vertexIndex + 2] = new Vector2(0f, 1f);
                uvs[vertexIndex + 3] = new Vector2(1f, 1f);
                int triangleIndex = slice * 6;
                triangles[triangleIndex] = vertexIndex;
                triangles[triangleIndex + 1] = vertexIndex + 2;
                triangles[triangleIndex + 2] = vertexIndex + 1;
                triangles[triangleIndex + 3] = vertexIndex + 1;
                triangles[triangleIndex + 4] = vertexIndex + 2;
                triangles[triangleIndex + 5] = vertexIndex + 3;
            }

            Mesh mesh = new Mesh
            {
                name = "Runtime Sun Shaft Slices",
                hideFlags = HideFlags.HideAndDontSave
            };
            mesh.MarkDynamic();
            mesh.vertices = sunVertices;
            mesh.uv = uvs;
            mesh.triangles = triangles;
            return mesh;
        }

        private void ReleaseResources()
        {
            DestroyRuntimeObject(sunMaterial);
            DestroyRuntimeObject(sunSliceMesh);
            sunMaterial = null;
            sunSliceMesh = null;
            sunVertices = null;
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
    }
}
