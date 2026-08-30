using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Draws atmosphere-only light shafts derived from the authoritative sky
    /// and opted-in local Spot Lights. It owns only temporary rendering resources.
    /// </summary>
    [DefaultExecutionOrder(10000)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PersistentGameplayShell))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stylized Light Shaft Presentation")]
    public sealed class StylizedLightShaftPresentation : MonoBehaviour
    {
        private const int MaximumSunSliceCount = 16;
        private const int MaximumLocalEmitterCount = 16;
        private const int LocalVolumeSliceCount = 9;
        private const float MinimumVisibleIntensity = 0.0001f;

        private static readonly int SourceModeId = Shader.PropertyToID("_ShaftSourceMode");
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

        [Header("Local Shafts")]
        [SerializeField, Range(1, MaximumLocalEmitterCount)]
        private int visibleLocalEmitterLimit = 8;
        [SerializeField, Min(0.01f)] private float localSurfaceFadeDistance = 0.2f;
        [SerializeField, Range(1f, 2f)] private float localRainScatterMultiplier = 1.35f;

        private readonly StylizedLightShaftEmitter[] selectedLocalEmitters =
            new StylizedLightShaftEmitter[MaximumLocalEmitterCount];
        private readonly float[] localSelectionDistances =
            new float[MaximumLocalEmitterCount];
        private readonly Plane[] frustumPlanes = new Plane[6];

        private Material sunMaterial;
        private Material[] localMaterials;
        private Mesh sunSliceMesh;
        private Mesh localBeamMesh;
        private Vector3[] sunVertices;
        private Light sunLight;
        private Color sunColor = Color.white;
        private float sunStrength;
        private float rainIntensity;
        private bool localLimitWarningReported;
        private Camera cachedLayoutCamera;
        private CameraZoomController cachedZoomController;

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
            localSurfaceFadeDistance = Mathf.Max(0.01f, localSurfaceFadeDistance);
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
            DrawLocalShafts(camera);
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
                0f,
                sunColor,
                visibleIntensity,
                sunShadowThreshold,
                sunDensityBands,
                sunNoiseStrength,
                sunWorldCellSize,
                sunSurfaceFadeDistance);
            DrawMesh(sunSliceMesh, Matrix4x4.identity, sunMaterial, camera);
        }

        private void DrawLocalShafts(Camera camera)
        {
            GeometryUtility.CalculateFrustumPlanes(camera, frustumPlanes);
            int emitterCount = StylizedLightShaftEmitter.FillVisibleEmitters(
                selectedLocalEmitters,
                localSelectionDistances,
                camera,
                frustumPlanes,
                SceneManager.GetActiveScene(),
                shell != null ? shell.transform : null,
                Mathf.Clamp(visibleLocalEmitterLimit, 1, MaximumLocalEmitterCount),
                out bool truncated);

            if (truncated && !localLimitWarningReported)
            {
                Debug.LogWarning(
                    $"Stylized local light shafts exceed the visible limit of " +
                    $"{visibleLocalEmitterLimit}. Only the nearest visible emitters are drawn.",
                    this);
                localLimitWarningReported = true;
            }
            else if (!truncated)
            {
                localLimitWarningReported = false;
            }

            for (int index = 0; index < emitterCount; index++)
            {
                StylizedLightShaftEmitter emitter = selectedLocalEmitters[index];
                Light source = emitter.SourceLight;
                Color linearColor = source.color.linear;
                float visibleIntensity =
                    source.intensity * emitter.IntensityMultiplier *
                    Mathf.Lerp(1f, localRainScatterMultiplier, rainIntensity);
                if (visibleIntensity <= MinimumVisibleIntensity)
                {
                    continue;
                }

                Matrix4x4 matrix = BuildViewAlignedVolumeMatrix(
                    camera,
                    emitter.OriginWorld,
                    emitter.DirectionWorld,
                    emitter.Length,
                    emitter.EndRadius);

                Material localMaterial = localMaterials[index];
                ApplyMaterialProperties(
                    localMaterial,
                    1f,
                    linearColor,
                    visibleIntensity / LocalVolumeSliceCount,
                    0f,
                    emitter.DensityBands,
                    emitter.NoiseStrength,
                    emitter.WorldCellSize,
                    localSurfaceFadeDistance);
                DrawMesh(localBeamMesh, matrix, localMaterial, camera);
            }
        }

        private static Matrix4x4 BuildViewAlignedVolumeMatrix(
            Camera camera,
            Vector3 origin,
            Vector3 direction,
            float length,
            float endRadius)
        {
            Vector3 across = Vector3.Cross(direction, camera.transform.forward);
            if (across.sqrMagnitude <= 0.0001f)
            {
                across = Vector3.Cross(direction, camera.transform.up);
            }
            if (across.sqrMagnitude <= 0.0001f)
            {
                across = camera.transform.right;
            }
            across.Normalize();

            Vector3 normal = Vector3.Cross(across, direction).normalized;
            Matrix4x4 matrix = Matrix4x4.identity;
            matrix.SetColumn(0, new Vector4(
                across.x * endRadius,
                across.y * endRadius,
                across.z * endRadius,
                0f));
            matrix.SetColumn(1, new Vector4(
                direction.x * length,
                direction.y * length,
                direction.z * length,
                0f));
            matrix.SetColumn(2, new Vector4(normal.x, normal.y, normal.z, 0f));
            matrix.SetColumn(3, new Vector4(origin.x, origin.y, origin.z, 1f));
            return matrix;
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
            float sourceMode,
            Color color,
            float intensity,
            float shadowThreshold,
            float densityBands,
            float noiseStrength,
            float worldCellSize,
            float surfaceFadeDistance)
        {
            material.SetFloat(SourceModeId, sourceMode);
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
            int requiredLocalMaterialCount = Mathf.Clamp(
                visibleLocalEmitterLimit,
                1,
                MaximumLocalEmitterCount);
            if (sunMaterial != null &&
                sunMaterial.shader == shaftShader &&
                localMaterials != null &&
                localMaterials.Length == requiredLocalMaterialCount &&
                sunSliceMesh != null &&
                localBeamMesh != null &&
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
            localMaterials = new Material[requiredLocalMaterialCount];
            for (int index = 0; index < localMaterials.Length; index++)
            {
                localMaterials[index] = CreateRuntimeMaterial(
                    $"Runtime Stylized Local Shaft {index + 1}");
            }
            sunSliceMesh = CreateSunSliceMesh();
            localBeamMesh = CreateLocalBeamMesh();
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

        private static Mesh CreateLocalBeamMesh()
        {
            const float topRadiusRatio = 0.10f;
            Vector3[] vertices = new Vector3[LocalVolumeSliceCount * 4];
            Vector2[] uvs = new Vector2[vertices.Length];
            int[] triangles = new int[LocalVolumeSliceCount * 6];
            for (int slice = 0; slice < LocalVolumeSliceCount; slice++)
            {
                // The planes are view-aligned samples of one world-space cone,
                // not independent billboards. Their circular cross-sections keep
                // the visible envelope fixed while the camera rotates.
                float sliceOffset =
                    ((slice + 0.5f) / LocalVolumeSliceCount) * 2f - 1f;
                float absoluteOffset = Mathf.Abs(sliceOffset);
                float startY = absoluteOffset <= topRadiusRatio
                    ? 0f
                    : (absoluteOffset - topRadiusRatio) / (1f - topRadiusRatio);
                float startRadius = Mathf.Lerp(topRadiusRatio, 1f, startY);
                float startHalfWidth = Mathf.Sqrt(Mathf.Max(
                    0f,
                    startRadius * startRadius - sliceOffset * sliceOffset));
                float endHalfWidth = Mathf.Sqrt(Mathf.Max(
                    0f,
                    1f - sliceOffset * sliceOffset));

                int vertexIndex = slice * 4;
                vertices[vertexIndex] =
                    new Vector3(-startHalfWidth, startY, sliceOffset);
                vertices[vertexIndex + 1] =
                    new Vector3(startHalfWidth, startY, sliceOffset);
                vertices[vertexIndex + 2] =
                    new Vector3(-endHalfWidth, 1f, sliceOffset);
                vertices[vertexIndex + 3] =
                    new Vector3(endHalfWidth, 1f, sliceOffset);
                uvs[vertexIndex] = new Vector2(0f, startY);
                uvs[vertexIndex + 1] = new Vector2(1f, startY);
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
                name = "Runtime Local Light Shaft",
                hideFlags = HideFlags.HideAndDontSave,
                vertices = vertices,
                uv = uvs,
                triangles = triangles,
                bounds = new Bounds(
                    new Vector3(0f, 0.5f, 0f),
                    new Vector3(2f, 1f, 2f))
            };
            return mesh;
        }

        private void ReleaseResources()
        {
            DestroyRuntimeObject(sunMaterial);
            if (localMaterials != null)
            {
                for (int index = 0; index < localMaterials.Length; index++)
                {
                    DestroyRuntimeObject(localMaterials[index]);
                }
            }
            DestroyRuntimeObject(sunSliceMesh);
            DestroyRuntimeObject(localBeamMesh);
            sunMaterial = null;
            localMaterials = null;
            sunSliceMesh = null;
            localBeamMesh = null;
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
