using System.Collections.Generic;
using FantasySurvival.CharacterPresentation;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.Rendering
{
    [DisallowMultipleRendererFeature("Character Silhouette Outline")]
    public sealed class CharacterSilhouetteRendererFeature : ScriptableRendererFeature
    {
        [System.Serializable]
        public sealed class Settings
        {
            public Material maskMaterial;
            public Material compositeMaterial;
            public RenderPassEvent injectionPoint = RenderPassEvent.BeforeRenderingPostProcessing;
        }

        [SerializeField] private Settings settings = new Settings();

        private CharacterSilhouettePass pass;

        public override void Create()
        {
            pass = new CharacterSilhouettePass();
            pass.renderPassEvent = settings.injectionPoint;
        }

        public void Configure(Material maskMaterial, Material compositeMaterial)
        {
            settings.maskMaterial = maskMaterial;
            settings.compositeMaterial = compositeMaterial;
            Create();
        }

        public override void AddRenderPasses(
            ScriptableRenderer renderer,
            ref RenderingData renderingData)
        {
            if (renderingData.cameraData.cameraType != CameraType.Game ||
                (Application.isPlaying && !CharacterSilhouetteSubject.HasActiveSubject) ||
                settings.maskMaterial == null ||
                settings.compositeMaterial == null)
            {
                return;
            }

            pass.Setup(settings.maskMaterial, settings.compositeMaterial);
            renderer.EnqueuePass(pass);
        }

        private sealed class CharacterSilhouettePass : ScriptableRenderPass
        {
            private static readonly int MaskTextureId =
                Shader.PropertyToID("_CharacterSilhouetteMask");

            private static readonly List<ShaderTagId> ShaderTags = new List<ShaderTagId>
            {
                new ShaderTagId("UniversalForwardOnly"),
                new ShaderTagId("UniversalForward"),
                new ShaderTagId("SRPDefaultUnlit"),
                new ShaderTagId("LightweightForward")
            };

            private Material maskMaterial;
            private Material compositeMaterial;

            public void Setup(Material newMaskMaterial, Material newCompositeMaterial)
            {
                maskMaterial = newMaskMaterial;
                compositeMaterial = newCompositeMaterial;
            }

            public override void RecordRenderGraph(
                RenderGraph renderGraph,
                ContextContainer frameData)
            {
                UniversalResourceData resources = frameData.Get<UniversalResourceData>();
                UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                if (!resources.activeColorTexture.IsValid() ||
                    !resources.activeDepthTexture.IsValid())
                {
                    return;
                }

                RenderTextureDescriptor descriptor = cameraData.cameraTargetDescriptor;
                descriptor.depthBufferBits = 0;
                descriptor.msaaSamples = 1;
                descriptor.graphicsFormat = GraphicsFormat.R8_UNorm;

                TextureHandle mask = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph,
                    descriptor,
                    "_CharacterSilhouetteMask",
                    true,
                    FilterMode.Point);

                RecordMaskPass(renderGraph, frameData, resources, mask);
                RecordCompositePass(renderGraph, resources, mask);
            }

            private void RecordMaskPass(
                RenderGraph renderGraph,
                ContextContainer frameData,
                UniversalResourceData resources,
                TextureHandle mask)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<MaskPassData>(
                        "Character Silhouette Mask",
                        out MaskPassData passData);

                UniversalRenderingData renderingData = frameData.Get<UniversalRenderingData>();
                UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                UniversalLightData lightData = frameData.Get<UniversalLightData>();

                DrawingSettings drawingSettings = RenderingUtils.CreateDrawingSettings(
                    ShaderTags,
                    renderingData,
                    cameraData,
                    lightData,
                    cameraData.defaultOpaqueSortFlags);
                drawingSettings.overrideMaterial = maskMaterial;
                drawingSettings.overrideMaterialPassIndex = 0;
                drawingSettings.perObjectData = PerObjectData.None;

                FilteringSettings filteringSettings = new FilteringSettings(
                    RenderQueueRange.opaque,
                    -1,
                    CharacterSilhouetteSubject.RenderingLayerMask);

                RendererListParams rendererListParams = new RendererListParams(
                    renderingData.cullResults,
                    drawingSettings,
                    filteringSettings);
                passData.rendererList = renderGraph.CreateRendererList(rendererListParams);

                if (!passData.rendererList.IsValid())
                {
                    return;
                }

                builder.UseRendererList(passData.rendererList);
                builder.SetRenderAttachment(mask, 0, AccessFlags.Write);
                builder.SetRenderAttachmentDepth(resources.activeDepthTexture, AccessFlags.Read);
                builder.SetRenderFunc((MaskPassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.Color, Color.clear, 1, 0);
                    context.cmd.DrawRendererList(data.rendererList);
                });
            }

            private void RecordCompositePass(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle mask)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<CompositePassData>(
                        "Character Silhouette Composite",
                        out CompositePassData passData);

                passData.mask = mask;
                passData.material = compositeMaterial;

                builder.UseTexture(mask, AccessFlags.Read);
                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc((CompositePassData data, RasterGraphContext context) =>
                {
                    data.material.SetTexture(MaskTextureId, data.mask);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        0,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private sealed class MaskPassData
            {
                public RendererListHandle rendererList;
            }

            private sealed class CompositePassData
            {
                public TextureHandle mask;
                public Material material;
            }
        }
    }
}
