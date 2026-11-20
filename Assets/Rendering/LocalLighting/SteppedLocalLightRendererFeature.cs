using System.Collections.Generic;
using FantasySurvival.CharacterPresentation;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace FantasySurvival.Rendering
{
    [DisallowMultipleRendererFeature("Stepped Local Lights (Game Camera)")]
    public sealed class SteppedLocalLightRendererFeature : FullScreenPassRendererFeature
    {
        private const int MaximumLightCount = 16;
        private const int CharacterStencilPassIndex = 2;
        private const string CharacterStencilShaderName =
            "Hidden/FantasySurvival/Character Silhouette Mask";
        private static readonly int LightCountId =
            Shader.PropertyToID("_SteppedLocalLightCount");
        private static readonly int PositionsAndRadiiId =
            Shader.PropertyToID("_SteppedLocalLightPositionsAndRadii");
        private static readonly int ColorsAndIntensitiesId =
            Shader.PropertyToID("_SteppedLocalLightColorsAndIntensities");
        private static readonly int QuantizationSettingsId =
            Shader.PropertyToID("_SteppedLocalLightQuantizationSettings");
        private static readonly int RoomLightingSettingsId =
            Shader.PropertyToID("_SteppedLocalLightRoomSettings");
        private static readonly int WorldCellSizesId =
            Shader.PropertyToID("_SteppedLocalLightWorldCellSizes");
        private static readonly int HaloRadiusMultipliersId =
            Shader.PropertyToID("_SteppedLocalLightHaloRadiusMultipliers");
        private static readonly int VolumeWorldToLocalId =
            Shader.PropertyToID("_SteppedLocalLightVolumeWorldToLocal");
        private static readonly int VolumeCentersId =
            Shader.PropertyToID("_SteppedLocalLightVolumeCenters");
        private static readonly int VolumeExtentsId =
            Shader.PropertyToID("_SteppedLocalLightVolumeExtents");
        private static readonly int Volume2WorldToLocalId =
            Shader.PropertyToID("_SteppedLocalLightVolume2WorldToLocal");
        private static readonly int Volume2CentersId =
            Shader.PropertyToID("_SteppedLocalLightVolume2Centers");
        private static readonly int Volume2ExtentsId =
            Shader.PropertyToID("_SteppedLocalLightVolume2Extents");

        [Tooltip("Render only this many nearest visible lights from the gameplay scene and persistent gameplay shell.")]
        [SerializeField, Range(1, MaximumLightCount)] private int visibleLightLimit = 8;

        private readonly Vector4[] positionsAndRadii = new Vector4[MaximumLightCount];
        private readonly Vector4[] colorsAndIntensities = new Vector4[MaximumLightCount];
        private readonly Vector4[] quantizationSettings = new Vector4[MaximumLightCount];
        private readonly Vector4[] roomLightingSettings = new Vector4[MaximumLightCount];
        private readonly float[] worldCellSizes = new float[MaximumLightCount];
        private readonly float[] haloRadiusMultipliers = new float[MaximumLightCount];
        private readonly float[] selectionDistances = new float[MaximumLightCount];
        private readonly Matrix4x4[] volumeWorldToLocal = new Matrix4x4[MaximumLightCount];
        private readonly Vector4[] volumeCenters = new Vector4[MaximumLightCount];
        private readonly Vector4[] volumeExtents = new Vector4[MaximumLightCount];
        private readonly Matrix4x4[] volume2WorldToLocal = new Matrix4x4[MaximumLightCount];
        private readonly Vector4[] volume2Centers = new Vector4[MaximumLightCount];
        private readonly Vector4[] volume2Extents = new Vector4[MaximumLightCount];
        private readonly Plane[] frustumPlanes = new Plane[6];
        private CharacterVisibleStencilPass characterStencilPass;
        private Material characterStencilMaterial;
        private bool limitWarningReported;

        public override void Create()
        {
            injectionPoint = InjectionPoint.BeforeRenderingTransparents;
            fetchColorBuffer = false;
            requirements = ScriptableRenderPassInput.Depth | ScriptableRenderPassInput.Normal;
            passIndex = 0;
            bindDepthStencilAttachment = true;
            base.Create();

            EnsureCharacterStencilResources();
        }

        public override void AddRenderPasses(
            ScriptableRenderer renderer,
            ref RenderingData renderingData)
        {
            Camera camera = renderingData.cameraData.camera;
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            bool sceneView = renderingData.cameraData.cameraType == CameraType.SceneView;
            if (camera == null || (!sceneView && (!Application.isPlaying ||
                renderingData.cameraData.cameraType != CameraType.Game)))
            {
                return;
            }

            if ((!sceneView && (shell == null || shell.PlayerCamera != camera)) ||
                passMaterial == null)
            {
                // Do not clobber global stepped light state when non-player offscreen cameras render.
                if (shell == null || passMaterial == null)
                    Shader.SetGlobalInteger(LightCountId, 0);
                return;
            }

            GeometryUtility.CalculateFrustumPlanes(camera, frustumPlanes);
            int lightCount = SteppedLocalLight.FillShaderData(
                positionsAndRadii,
                colorsAndIntensities,
                quantizationSettings,
                roomLightingSettings,
                worldCellSizes,
                haloRadiusMultipliers,
                selectionDistances,
                volumeWorldToLocal,
                volumeCenters,
                volumeExtents,
                volume2WorldToLocal,
                volume2Centers,
                volume2Extents,
                camera,
                frustumPlanes,
                SceneManager.GetActiveScene(),
                shell != null ? shell.transform : null,
                Mathf.Clamp(visibleLightLimit, 1, MaximumLightCount),
                out bool truncated);
            ApplyGlobalLightData(lightCount);
            // Editor native surface shaders need current data while designing
            // the room. Scene View does not receive the game's fullscreen light
            // or character stencil pass, and uses no parallel light authority.
            if (sceneView)
            {
                return;
            }
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

            EnsureCharacterStencilResources();
            if (characterStencilPass != null &&
                characterStencilMaterial != null &&
                CharacterSilhouetteSubject.HasActiveSubject)
            {
                characterStencilPass.Setup(characterStencilMaterial);
                renderer.EnqueuePass(characterStencilPass);
            }

            passMaterial.SetInteger(LightCountId, lightCount);
            passMaterial.SetVectorArray(PositionsAndRadiiId, positionsAndRadii);
            passMaterial.SetVectorArray(ColorsAndIntensitiesId, colorsAndIntensities);
            passMaterial.SetVectorArray(QuantizationSettingsId, quantizationSettings);
            passMaterial.SetVectorArray(RoomLightingSettingsId, roomLightingSettings);
            passMaterial.SetFloatArray(WorldCellSizesId, worldCellSizes);
            passMaterial.SetFloatArray(HaloRadiusMultipliersId, haloRadiusMultipliers);
            passMaterial.SetMatrixArray(VolumeWorldToLocalId, volumeWorldToLocal);
            passMaterial.SetVectorArray(VolumeCentersId, volumeCenters);
            passMaterial.SetVectorArray(VolumeExtentsId, volumeExtents);
            passMaterial.SetMatrixArray(Volume2WorldToLocalId, volume2WorldToLocal);
            passMaterial.SetVectorArray(Volume2CentersId, volume2Centers);
            passMaterial.SetVectorArray(Volume2ExtentsId, volume2Extents);
            base.AddRenderPasses(renderer, ref renderingData);
        }

        protected override void Dispose(bool disposing)
        {
            characterStencilPass = null;
            CoreUtils.Destroy(characterStencilMaterial);
            characterStencilMaterial = null;
            base.Dispose(disposing);
        }

        private void EnsureCharacterStencilResources()
        {
            if (characterStencilPass == null)
            {
                characterStencilPass = new CharacterVisibleStencilPass
                {
                    // Run after all opaque depth is final and immediately before
                    // this feature's fullscreen light pass at the next event.
                    renderPassEvent = (RenderPassEvent)(
                        (int)RenderPassEvent.BeforeRenderingTransparents - 1)
                };
            }

            if (characterStencilMaterial != null)
            {
                return;
            }

            Shader stencilShader = Shader.Find(CharacterStencilShaderName);
            if (stencilShader != null)
            {
                characterStencilMaterial = CoreUtils.CreateEngineMaterial(
                    stencilShader);
            }
        }

        private void ApplyGlobalLightData(int lightCount)
        {
            Shader.SetGlobalInteger(LightCountId, lightCount);
            if (lightCount <= 0)
            {
                return;
            }

            // The fullscreen world-light pass keeps its material-local values.
            // Character flat-light shaders consume the same derived list as
            // globals and evaluate it at each visible fragment without using
            // the mesh normal.
            Shader.SetGlobalVectorArray(PositionsAndRadiiId, positionsAndRadii);
            Shader.SetGlobalVectorArray(ColorsAndIntensitiesId, colorsAndIntensities);
            Shader.SetGlobalVectorArray(
                QuantizationSettingsId,
                quantizationSettings);
            Shader.SetGlobalVectorArray(RoomLightingSettingsId, roomLightingSettings);
            Shader.SetGlobalFloatArray(WorldCellSizesId, worldCellSizes);
            Shader.SetGlobalFloatArray(
                HaloRadiusMultipliersId,
                haloRadiusMultipliers);
            Shader.SetGlobalMatrixArray(VolumeWorldToLocalId, volumeWorldToLocal);
            Shader.SetGlobalVectorArray(VolumeCentersId, volumeCenters);
            Shader.SetGlobalVectorArray(VolumeExtentsId, volumeExtents);
            Shader.SetGlobalMatrixArray(Volume2WorldToLocalId, volume2WorldToLocal);
            Shader.SetGlobalVectorArray(Volume2CentersId, volume2Centers);
            Shader.SetGlobalVectorArray(Volume2ExtentsId, volume2Extents);
        }

        private sealed class CharacterVisibleStencilPass : ScriptableRenderPass
        {
            private static readonly List<ShaderTagId> ShaderTags = new()
            {
                new ShaderTagId("UniversalForwardOnly"),
                new ShaderTagId("UniversalForward"),
                new ShaderTagId("SRPDefaultUnlit"),
                new ShaderTagId("LightweightForward")
            };

            private Material stencilMaterial;

            public void Setup(Material material)
            {
                stencilMaterial = material;
            }

            public override void RecordRenderGraph(
                RenderGraph renderGraph,
                ContextContainer frameData)
            {
                UniversalResourceData resources =
                    frameData.Get<UniversalResourceData>();
                if (stencilMaterial == null ||
                    stencilMaterial.passCount <= CharacterStencilPassIndex ||
                    !resources.activeDepthTexture.IsValid())
                {
                    return;
                }

                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<PassData>(
                        "Character Visible Stencil",
                        out PassData passData);

                UniversalRenderingData renderingData =
                    frameData.Get<UniversalRenderingData>();
                UniversalCameraData cameraData =
                    frameData.Get<UniversalCameraData>();
                UniversalLightData lightData =
                    frameData.Get<UniversalLightData>();
                DrawingSettings drawingSettings =
                    RenderingUtils.CreateDrawingSettings(
                        ShaderTags,
                        renderingData,
                        cameraData,
                        lightData,
                        cameraData.defaultOpaqueSortFlags);
                drawingSettings.overrideMaterial = stencilMaterial;
                drawingSettings.overrideMaterialPassIndex =
                    CharacterStencilPassIndex;
                drawingSettings.perObjectData = PerObjectData.None;

                FilteringSettings filteringSettings = new FilteringSettings(
                    RenderQueueRange.opaque,
                    -1,
                    CharacterSilhouetteSubject.RenderingLayerMask);
                RendererListParams rendererListParams = new RendererListParams(
                    renderingData.cullResults,
                    drawingSettings,
                    filteringSettings);
                passData.rendererList = renderGraph.CreateRendererList(
                    rendererListParams);
                if (!passData.rendererList.IsValid())
                {
                    return;
                }

                builder.UseRendererList(passData.rendererList);
                builder.SetRenderAttachmentDepth(
                    resources.activeDepthTexture,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (
                    PassData data,
                    RasterGraphContext context) =>
                {
                    context.cmd.DrawRendererList(data.rendererList);
                });
            }

            private sealed class PassData
            {
                public RendererListHandle rendererList;
            }
        }
    }
}
