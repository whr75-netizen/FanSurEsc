using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace FantasySurvival.Rendering
{
    [DisallowMultipleRendererFeature("Stepped Local Lights (Game Camera)")]
    public sealed class SteppedLocalLightRendererFeature : FullScreenPassRendererFeature
    {
        private const int MaximumLightCount = 16;
        private static readonly int LightCountId =
            Shader.PropertyToID("_SteppedLocalLightCount");
        private static readonly int PositionsAndRadiiId =
            Shader.PropertyToID("_SteppedLocalLightPositionsAndRadii");
        private static readonly int ColorsAndIntensitiesId =
            Shader.PropertyToID("_SteppedLocalLightColorsAndIntensities");
        private static readonly int QuantizationSettingsId =
            Shader.PropertyToID("_SteppedLocalLightQuantizationSettings");
        private static readonly int WorldCellSizesId =
            Shader.PropertyToID("_SteppedLocalLightWorldCellSizes");
        private static readonly int HaloRadiusMultipliersId =
            Shader.PropertyToID("_SteppedLocalLightHaloRadiusMultipliers");

        [Tooltip("Render only this many nearest visible lights from the gameplay scene and persistent gameplay shell.")]
        [SerializeField, Range(1, MaximumLightCount)] private int visibleLightLimit = 8;

        private readonly Vector4[] positionsAndRadii = new Vector4[MaximumLightCount];
        private readonly Vector4[] colorsAndIntensities = new Vector4[MaximumLightCount];
        private readonly Vector4[] quantizationSettings = new Vector4[MaximumLightCount];
        private readonly float[] worldCellSizes = new float[MaximumLightCount];
        private readonly float[] haloRadiusMultipliers = new float[MaximumLightCount];
        private readonly float[] selectionDistances = new float[MaximumLightCount];
        private readonly Plane[] frustumPlanes = new Plane[6];
        private bool limitWarningReported;

        public override void Create()
        {
            injectionPoint = InjectionPoint.BeforeRenderingTransparents;
            fetchColorBuffer = false;
            requirements = ScriptableRenderPassInput.Depth | ScriptableRenderPassInput.Normal;
            passIndex = 0;
            bindDepthStencilAttachment = false;
            base.Create();
        }

        public override void AddRenderPasses(
            ScriptableRenderer renderer,
            ref RenderingData renderingData)
        {
            Camera camera = renderingData.cameraData.camera;
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (!Application.isPlaying ||
                renderingData.cameraData.cameraType != CameraType.Game ||
                shell == null ||
                shell.PlayerCamera != camera ||
                passMaterial == null)
            {
                return;
            }

            GeometryUtility.CalculateFrustumPlanes(camera, frustumPlanes);
            int lightCount = SteppedLocalLight.FillShaderData(
                positionsAndRadii,
                colorsAndIntensities,
                quantizationSettings,
                worldCellSizes,
                haloRadiusMultipliers,
                selectionDistances,
                camera,
                frustumPlanes,
                SceneManager.GetActiveScene(),
                shell.transform,
                Mathf.Clamp(visibleLightLimit, 1, MaximumLightCount),
                out bool truncated);
            if (truncated && !limitWarningReported)
            {
                Debug.LogWarning(
                    $"Stepped local lights exceed the visible limit of {visibleLightLimit}. " +
                    "Only the nearest visible lights are rendered.",
                    this);
                limitWarningReported = true;
            }
            else if (!truncated)
            {
                limitWarningReported = false;
            }

            if (lightCount <= 0)
            {
                return;
            }

            passMaterial.SetInteger(LightCountId, lightCount);
            passMaterial.SetVectorArray(PositionsAndRadiiId, positionsAndRadii);
            passMaterial.SetVectorArray(ColorsAndIntensitiesId, colorsAndIntensities);
            passMaterial.SetVectorArray(QuantizationSettingsId, quantizationSettings);
            passMaterial.SetFloatArray(WorldCellSizesId, worldCellSizes);
            passMaterial.SetFloatArray(HaloRadiusMultipliersId, haloRadiusMultipliers);
            base.AddRenderPasses(renderer, ref renderingData);
        }
    }
}
