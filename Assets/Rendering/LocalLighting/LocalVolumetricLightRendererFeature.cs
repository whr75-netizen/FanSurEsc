using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace FantasySurvival.Rendering
{
    /// <summary>
    /// Renders opted-in Spot Lights as continuous participating media. The pass
    /// reconstructs camera rays in world space, clips them against each finite
    /// light cone and the scene depth, then integrates the same URP light cookie
    /// and additional-light shadow map used by the source Light.
    /// </summary>
    [DisallowMultipleRendererFeature("Local Volumetric Lights (Game Camera)")]
    public sealed class LocalVolumetricLightRendererFeature : ScriptableRendererFeature
    {
        private const int MaximumLightCount = 16;

        private static readonly int LightCountId =
            Shader.PropertyToID("_LocalVolumeLightCount");
        private static readonly int OriginsAndRangesId =
            Shader.PropertyToID("_LocalVolumeOriginsAndRanges");
        private static readonly int DirectionsAndRadiiId =
            Shader.PropertyToID("_LocalVolumeDirectionsAndRadii");
        private static readonly int MediumSettingsId =
            Shader.PropertyToID("_LocalVolumeMediumSettings");
        private static readonly int SamplingSettingsId =
            Shader.PropertyToID("_LocalVolumeSamplingSettings");

        [SerializeField] private Material volumeMaterial;
        [Tooltip("Full-resolution integration samples per visible light cone. Higher values reduce banding at proportional GPU cost.")]
        [SerializeField, Range(8, 32)] private int sampleCount = 24;

        private readonly StylizedLightShaftEmitter[] selectedEmitters =
            new StylizedLightShaftEmitter[MaximumLightCount];
        private readonly float[] selectionDistances = new float[MaximumLightCount];
        private readonly Plane[] frustumPlanes = new Plane[6];
        private readonly Vector4[] originsAndRanges = new Vector4[MaximumLightCount];
        private readonly Vector4[] directionsAndRadii = new Vector4[MaximumLightCount];
        private readonly Vector4[] mediumSettings = new Vector4[MaximumLightCount];

        private bool limitWarningReported;
        private LocalVolumetricLightPass volumePass;

        public override void Create()
        {
            volumePass = new LocalVolumetricLightPass();
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
                volumeMaterial == null ||
                volumePass == null ||
                !shell.TryGetComponent(out StylizedLightShaftPresentation presentation))
            {
                return;
            }

            GeometryUtility.CalculateFrustumPlanes(camera, frustumPlanes);
            int selectedCount = StylizedLightShaftEmitter.FillVisibleEmitters(
                selectedEmitters,
                selectionDistances,
                camera,
                frustumPlanes,
                SceneManager.GetActiveScene(),
                shell.transform,
                Mathf.Min(presentation.VisibleLocalEmitterLimit, MaximumLightCount),
                out bool truncated);

            NativeArray<VisibleLight> visibleLights = renderingData.lightData.visibleLights;
            int mainLightIndex = renderingData.lightData.mainLightIndex;
            int packedLightLimit = renderingData.lightData.additionalLightsCount;
            int lightCount = 0;
            for (int index = 0; index < selectedCount; index++)
            {
                StylizedLightShaftEmitter emitter = selectedEmitters[index];
                Light source = emitter.SourceLight;
                int packedLightIndex = FindPackedAdditionalLightIndex(
                    visibleLights,
                    mainLightIndex,
                    packedLightLimit,
                    source);
                if (packedLightIndex < 0)
                {
                    continue;
                }

                Vector3 direction = emitter.DirectionWorld;
                originsAndRanges[lightCount] = new Vector4(
                    emitter.OriginWorld.x,
                    emitter.OriginWorld.y,
                    emitter.OriginWorld.z,
                    emitter.Length);
                directionsAndRadii[lightCount] = new Vector4(
                    direction.x,
                    direction.y,
                    direction.z,
                    emitter.EndRadius);
                mediumSettings[lightCount] = new Vector4(
                    emitter.IntensityMultiplier * presentation.LocalWeatherScatterMultiplier,
                    emitter.ExtinctionCoefficient,
                    emitter.Anisotropy,
                    packedLightIndex);
                lightCount++;
            }

            if ((truncated || lightCount < selectedCount) && !limitWarningReported)
            {
                Debug.LogWarning(
                    "Some opted-in volumetric Spot Lights were outside the URP visible " +
                    "additional-light set or exceeded the configured local volume limit.",
                    this);
                limitWarningReported = true;
            }
            else if (!truncated && lightCount == selectedCount)
            {
                limitWarningReported = false;
            }

            if (lightCount <= 0)
            {
                return;
            }

            volumeMaterial.SetInteger(LightCountId, lightCount);
            volumeMaterial.SetVectorArray(OriginsAndRangesId, originsAndRanges);
            volumeMaterial.SetVectorArray(DirectionsAndRadiiId, directionsAndRadii);
            volumeMaterial.SetVectorArray(MediumSettingsId, mediumSettings);
            volumeMaterial.SetVector(
                SamplingSettingsId,
                new Vector4(
                    Mathf.Clamp(sampleCount, 8, 32),
                    0f,
                    0f,
                    0f));
            volumePass.Setup(volumeMaterial);
            renderer.EnqueuePass(volumePass);
        }

        private static int FindPackedAdditionalLightIndex(
            NativeArray<VisibleLight> visibleLights,
            int mainLightIndex,
            int packedLightLimit,
            Light source)
        {
            if (source == null || packedLightLimit <= 0)
            {
                return -1;
            }

            int packedIndex = 0;
            for (int visibleIndex = 0; visibleIndex < visibleLights.Length; visibleIndex++)
            {
                if (visibleIndex == mainLightIndex)
                {
                    continue;
                }

                if (packedIndex >= packedLightLimit)
                {
                    break;
                }

                if (visibleLights[visibleIndex].light == source)
                {
                    return packedIndex;
                }

                packedIndex++;
            }

            return -1;
        }

        private sealed class LocalVolumetricLightPass : ScriptableRenderPass
        {
            private static readonly ProfilingSampler PassProfilingSampler =
                new("Local Volumetric Lights");

            private Material material;

            internal LocalVolumetricLightPass()
            {
                profilingSampler = PassProfilingSampler;
                renderPassEvent = RenderPassEvent.BeforeRenderingTransparents;
                ConfigureInput(ScriptableRenderPassInput.Depth);
            }

            internal void Setup(Material passMaterial)
            {
                material = passMaterial;
            }

            public override void RecordRenderGraph(
                RenderGraph renderGraph,
                ContextContainer frameData)
            {
                if (material == null)
                {
                    return;
                }

                UniversalResourceData resources = frameData.Get<UniversalResourceData>();
                using var builder = renderGraph.AddRasterRenderPass<PassData>(
                    "Local Volumetric Lights",
                    out PassData passData,
                    PassProfilingSampler);
                passData.material = material;

                builder.UseAllGlobalTextures(true);
                if (resources.cameraDepthTexture.IsValid())
                {
                    builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);
                }

                if (resources.additionalShadowsTexture.IsValid())
                {
                    builder.UseTexture(resources.additionalShadowsTexture, AccessFlags.Read);
                }

                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (PassData data, RasterGraphContext context) =>
                {
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        0,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private sealed class PassData
            {
                internal Material material;
            }
        }
    }
}
