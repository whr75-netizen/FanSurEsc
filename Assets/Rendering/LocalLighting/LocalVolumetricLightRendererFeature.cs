using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace FantasySurvival.Rendering
{
    /// <summary>
    /// Renders opted-in Spot Lights and shadow-defined directional sunlight as
    /// participating media. Local lights keep their full-resolution cone
    /// integration; directional light is integrated at half resolution through
    /// world-anchored virtual planes parallel to the main-light direction.
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
        private static readonly int ShaftColorId =
            Shader.PropertyToID("_ShaftColor");
        private static readonly int ShaftIntensityId =
            Shader.PropertyToID("_ShaftIntensity");
        private static readonly int SurfaceFadeDistanceId =
            Shader.PropertyToID("_SurfaceFadeDistance");
        private static readonly int DirectionalVolumeBoundsId =
            Shader.PropertyToID("_DirectionalVolumeBounds");
        private static readonly int DirectionalMediumSettingsId =
            Shader.PropertyToID("_DirectionalMediumSettings");
        private static readonly int DirectionalSampleCountId =
            Shader.PropertyToID("_DirectionalSampleCount");
        private static readonly int DirectionalShellPlaneId =
            Shader.PropertyToID("_DirectionalShellPlane");
        private static readonly int RainMistColorId = Shader.PropertyToID("_RainMistColor");
        private static readonly int RainMistSettingsId = Shader.PropertyToID("_RainMistSettings");

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
        private Shader directionalShader;
        private Material directionalMaterial;
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
            if (volumeMaterial != null)
            {
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

            bool hasDirectionalVolume =
                presentation.TryGetDirectionalVolume(out DirectionalVolumetricLightSettings directionalSettings) &&
                IsUsableMainShadowLight(
                    visibleLights,
                    mainLightIndex,
                    directionalSettings.SourceLight) &&
                EnsureDirectionalMaterial(directionalSettings.Shader);

            bool hasRainMist = presentation.TryGetRainMist(
                out Shader mistShader, out Color mistColor, out Vector4 mistSettings) &&
                EnsureDirectionalMaterial(mistShader);

            if (lightCount <= 0 && !hasDirectionalVolume && !hasRainMist)
            {
                return;
            }

            Material localMaterial = null;
            if (lightCount > 0)
            {
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
                localMaterial = volumeMaterial;
            }

            Material sunMaterial = null;
            if (hasDirectionalVolume)
            {
                directionalMaterial.SetColor(ShaftColorId, directionalSettings.Color);
                directionalMaterial.SetFloat(ShaftIntensityId, directionalSettings.Intensity);
                directionalMaterial.SetFloat(
                    SurfaceFadeDistanceId,
                    directionalSettings.SurfaceFadeDistance);
                directionalMaterial.SetVector(
                    DirectionalVolumeBoundsId,
                    new Vector4(
                        directionalSettings.BaseHeight,
                        directionalSettings.Height,
                        0f,
                        0f));
                directionalMaterial.SetVector(
                    DirectionalMediumSettingsId,
                    new Vector4(
                        directionalSettings.Extinction,
                        directionalSettings.Anisotropy,
                        0f,
                        0f));
                directionalMaterial.SetFloat(
                    DirectionalSampleCountId,
                    Mathf.Clamp(directionalSettings.SampleCount, 4, 32));
                directionalMaterial.SetVector(
                    DirectionalShellPlaneId,
                    BuildDirectionalShellPlane(camera, directionalSettings));
                sunMaterial = directionalMaterial;
            }

            Material mistMaterial = null;
            if (hasRainMist)
            {
                directionalMaterial.SetColor(RainMistColorId, mistColor);
                directionalMaterial.SetVector(RainMistSettingsId, mistSettings);
                mistMaterial = directionalMaterial;
            }

            volumePass.Setup(localMaterial, sunMaterial, mistMaterial);
            renderer.EnqueuePass(volumePass);
        }

        protected override void Dispose(bool disposing)
        {
            volumePass = null;
            CoreUtils.Destroy(directionalMaterial);
            directionalMaterial = null;
            directionalShader = null;
            base.Dispose(disposing);
        }

        private bool EnsureDirectionalMaterial(Shader shader)
        {
            if (shader == null || !shader.isSupported)
            {
                return false;
            }

            if (directionalMaterial != null && directionalShader == shader)
            {
                return true;
            }

            CoreUtils.Destroy(directionalMaterial);
            directionalShader = shader;
            directionalMaterial = CoreUtils.CreateEngineMaterial(shader);
            if (directionalMaterial != null)
            {
                directionalMaterial.name = "Runtime Directional Volumetric Light";
                directionalMaterial.hideFlags = HideFlags.HideAndDontSave;
            }

            return directionalMaterial != null;
        }

        private static bool IsUsableMainShadowLight(
            NativeArray<VisibleLight> visibleLights,
            int mainLightIndex,
            Light sourceLight)
        {
            return sourceLight != null &&
                   sourceLight.shadows != LightShadows.None &&
                   sourceLight.shadowStrength > 0.0001f &&
                   mainLightIndex >= 0 &&
                   mainLightIndex < visibleLights.Length &&
                   visibleLights[mainLightIndex].light == sourceLight;
        }

        private static Vector4 BuildDirectionalShellPlane(
            Camera camera,
            DirectionalVolumetricLightSettings settings)
        {
            Vector3 viewDirection = camera.transform.forward.normalized;
            Vector3 lightDirection = -settings.SourceLight.transform.forward.normalized;
            Vector3 normal = viewDirection -
                lightDirection * Vector3.Dot(viewDirection, lightDirection);
            float perpendicularLength = normal.magnitude;
            Vector3 lightParallelNormal = perpendicularLength > 0.0001f
                ? normal / perpendicularLength
                : viewDirection;
            float exactPlaneWeight = Mathf.SmoothStep(
                0f,
                1f,
                Mathf.InverseLerp(0.03f, 0.10f, perpendicularLength));
            normal = Vector3.Lerp(
                viewDirection,
                lightParallelNormal,
                exactPlaneWeight).normalized;
            float cameraVertical = Mathf.Max(Mathf.Abs(viewDirection.y), 0.02f);
            float fullVolumePath = settings.Height / cameraVertical;
            float projectedPath = fullVolumePath *
                Mathf.Abs(Vector3.Dot(viewDirection, normal));
            float spacing = Mathf.Max(
                projectedPath / Mathf.Max(settings.SampleCount, 1),
                0.02f);
            return new Vector4(normal.x, normal.y, normal.z, spacing);
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
            private static readonly int DirectionalVolumeTextureId =
                Shader.PropertyToID("_DirectionalVolumeTexture");
            private static readonly ProfilingSampler LocalProfilingSampler =
                new("Local Volumetric Lights");
            private static readonly ProfilingSampler DirectionalIntegrationProfilingSampler =
                new("Directional Volumetric Light Integration");
            private static readonly ProfilingSampler DirectionalCompositeProfilingSampler =
                new("Directional Volumetric Light Composite");
            private static readonly ProfilingSampler RainMistProfilingSampler = new("Rain Mist");

            private Material localMaterial;
            private Material directionalMaterial;
            private Material rainMistMaterial;

            internal LocalVolumetricLightPass()
            {
                profilingSampler = LocalProfilingSampler;
                renderPassEvent = RenderPassEvent.BeforeRenderingTransparents;
                ConfigureInput(ScriptableRenderPassInput.Depth);
            }

            internal void Setup(Material newLocalMaterial, Material newDirectionalMaterial, Material newRainMistMaterial)
            {
                localMaterial = newLocalMaterial;
                directionalMaterial = newDirectionalMaterial;
                rainMistMaterial = newRainMistMaterial;
            }

            public override void RecordRenderGraph(
                RenderGraph renderGraph,
                ContextContainer frameData)
            {
                if (localMaterial == null && directionalMaterial == null && rainMistMaterial == null)
                {
                    return;
                }

                UniversalResourceData resources = frameData.Get<UniversalResourceData>();
                if (!resources.activeColorTexture.IsValid() ||
                    !resources.cameraDepthTexture.IsValid())
                {
                    return;
                }

                // Attenuate opaque surfaces first; light scattering and the
                // existing transparent precipitation are drawn afterwards.
                if (rainMistMaterial != null)
                    RecordRainMist(renderGraph, resources);

                if (directionalMaterial != null)
                {
                    UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                    RenderTextureDescriptor descriptor = cameraData.cameraTargetDescriptor;
                    descriptor.width = Mathf.Max(1, descriptor.width / 2);
                    descriptor.height = Mathf.Max(1, descriptor.height / 2);
                    descriptor.depthBufferBits = 0;
                    descriptor.msaaSamples = 1;
                    descriptor.graphicsFormat = GraphicsFormat.R16G16B16A16_SFloat;

                    TextureHandle directionalVolume =
                        UniversalRenderer.CreateRenderGraphTexture(
                            renderGraph,
                            descriptor,
                            "_DirectionalVolumetricLightHalfResolution",
                            true,
                            FilterMode.Bilinear);
                    RecordDirectionalIntegration(
                        renderGraph,
                        resources,
                        directionalVolume);
                    RecordDirectionalComposite(
                        renderGraph,
                        resources,
                        directionalVolume);
                }

                if (localMaterial != null)
                {
                    RecordLocalVolumes(renderGraph, resources);
                }
            }

            private void RecordRainMist(RenderGraph renderGraph, UniversalResourceData resources)
            {
                using IRasterRenderGraphBuilder builder = renderGraph.AddRasterRenderPass<LocalPassData>(
                    "Rain Mist", out LocalPassData passData, RainMistProfilingSampler);
                passData.material = rainMistMaterial;
                builder.UseAllGlobalTextures(true);
                builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);
                builder.SetRenderAttachment(resources.activeColorTexture, 0, AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (LocalPassData data, RasterGraphContext context) =>
                {
                    context.cmd.DrawProcedural(Matrix4x4.identity, data.material, 2,
                        MeshTopology.Triangles, 3, 1);
                });
            }

            private void RecordDirectionalIntegration(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle directionalVolume)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<DirectionalIntegrationPassData>(
                        "Directional Volumetric Light Integration",
                        out DirectionalIntegrationPassData passData,
                        DirectionalIntegrationProfilingSampler);
                passData.material = directionalMaterial;

                builder.UseAllGlobalTextures(true);
                builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);
                if (resources.mainShadowsTexture.IsValid())
                {
                    builder.UseTexture(resources.mainShadowsTexture, AccessFlags.Read);
                }

                builder.SetRenderAttachment(directionalVolume, 0, AccessFlags.Write);
                builder.SetRenderFunc(static (
                    DirectionalIntegrationPassData data,
                    RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(
                        RTClearFlags.Color,
                        Color.clear,
                        1f,
                        0);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        0,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordDirectionalComposite(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle directionalVolume)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<DirectionalCompositePassData>(
                        "Directional Volumetric Light Composite",
                        out DirectionalCompositePassData passData,
                        DirectionalCompositeProfilingSampler);
                passData.material = directionalMaterial;
                passData.directionalVolume = directionalVolume;

                builder.UseAllGlobalTextures(true);
                builder.UseTexture(directionalVolume, AccessFlags.Read);
                builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);
                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (
                    DirectionalCompositePassData data,
                    RasterGraphContext context) =>
                {
                    data.material.SetTexture(
                        DirectionalVolumeTextureId,
                        data.directionalVolume);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        1,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordLocalVolumes(
                RenderGraph renderGraph,
                UniversalResourceData resources)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<LocalPassData>(
                        "Local Volumetric Lights",
                        out LocalPassData passData,
                        LocalProfilingSampler);
                passData.material = localMaterial;

                builder.UseAllGlobalTextures(true);
                builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);

                if (resources.additionalShadowsTexture.IsValid())
                {
                    builder.UseTexture(resources.additionalShadowsTexture, AccessFlags.Read);
                }

                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (LocalPassData data, RasterGraphContext context) =>
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

            private sealed class DirectionalIntegrationPassData
            {
                internal Material material;
            }

            private sealed class DirectionalCompositePassData
            {
                internal Material material;
                internal TextureHandle directionalVolume;
            }

            private sealed class LocalPassData
            {
                internal Material material;
            }
        }
    }
}
