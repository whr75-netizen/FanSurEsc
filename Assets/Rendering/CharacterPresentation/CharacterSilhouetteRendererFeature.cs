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
        private const int RequiredMaskPassCount = 4;
        private const int RequiredCompositePassCount = 6;
        private const int ExpandPassIndex = 0;
        private const int ClassicOutlinePassIndex = 1;
        private const int ScreenSourceCopyPassIndex = 2;
        private const int ScreenResolvePassIndex = 3;
        private const int ScreenOutlinePassIndex = 4;
        private const int ScreenCompositePassIndex = 5;

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
                settings.compositeMaterial == null ||
                settings.maskMaterial.passCount < RequiredMaskPassCount ||
                settings.compositeMaterial.passCount < RequiredCompositePassCount)
            {
                return;
            }

            bool needsScreenPixelColor =
                CharacterSilhouetteSubject.HasActiveScreenPixelSubject;

            pass.Setup(settings.maskMaterial, settings.compositeMaterial);
            pass.ConfigureInput(
                needsScreenPixelColor
                    ? ScriptableRenderPassInput.Depth
                    : ScriptableRenderPassInput.None);
            // The screen-pixel path samples the already lit camera color. Force
            // URP to render through cameraColor instead of a platform backbuffer;
            // this is the same contract used by URP's Full Screen Pass when it
            // fetches color.
            pass.requiresIntermediateTexture = needsScreenPixelColor;
            renderer.EnqueuePass(pass);
        }

        private sealed class CharacterSilhouettePass : ScriptableRenderPass
        {
            private static readonly int MaskTextureId =
                Shader.PropertyToID("_CharacterSilhouetteMask");
            private static readonly int QuantizedMaskTextureId =
                Shader.PropertyToID("_CharacterSilhouetteQuantizedMask");
            private static readonly int SourceColorInputTextureId =
                Shader.PropertyToID("_CharacterSourceColorInput");
            private static readonly int SourceColorTextureId =
                Shader.PropertyToID("_CharacterSourceColor");
            private static readonly int ScreenPixelMaskTextureId =
                Shader.PropertyToID("_CharacterScreenPixelMask");
            private static readonly int ScreenPixelResolvedTextureId =
                Shader.PropertyToID("_CharacterScreenPixelResolved");
            private static readonly int ScreenPixelOutlineDepthTextureId =
                Shader.PropertyToID("_CharacterScreenPixelOutlineDepth");
            private static readonly int SceneDepthTextureId =
                Shader.PropertyToID("_CharacterSceneDepth");
            private static readonly int ArtPixelSizeId =
                Shader.PropertyToID("_ArtPixelSize");
            private static readonly int ScreenPixelSizeId =
                Shader.PropertyToID("_ScreenPixelSize");
            private static readonly int CharacterArtPixelSizeId =
                Shader.PropertyToID("_CharacterArtPixelSize");
            private static readonly int CharacterScreenPixelSizeId =
                Shader.PropertyToID("_CharacterScreenPixelSize");

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
                descriptor.graphicsFormat = GraphicsFormat.R8G8_UNorm;

                TextureHandle mask = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph,
                    descriptor,
                    "_CharacterSilhouetteMask",
                    true,
                    FilterMode.Point);

                RenderTextureDescriptor quantizedDescriptor = descriptor;
                quantizedDescriptor.graphicsFormat = GraphicsFormat.R8_UNorm;
                TextureHandle quantizedMask = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph,
                    quantizedDescriptor,
                    "_CharacterSilhouetteQuantizedMask",
                    true,
                    FilterMode.Point);

                RecordMaskPass(renderGraph, frameData, resources, mask);
                RecordExpansionPass(renderGraph, mask, quantizedMask);

                if (CharacterSilhouetteSubject.HasActiveScreenPixelSubject &&
                    resources.cameraColor.IsValid() &&
                    resources.cameraDepthTexture.IsValid())
                {
                    RenderTextureDescriptor sourceDescriptor =
                        cameraData.cameraTargetDescriptor;
                    sourceDescriptor.depthBufferBits = 0;
                    sourceDescriptor.msaaSamples = 1;
                    TextureHandle sourceColor =
                        UniversalRenderer.CreateRenderGraphTexture(
                            renderGraph,
                            sourceDescriptor,
                            "_CharacterSourceColor",
                            true,
                            FilterMode.Point);

                    RenderTextureDescriptor screenMaskDescriptor = descriptor;
                    screenMaskDescriptor.graphicsFormat =
                        GraphicsFormat.R16G16_SFloat;
                    TextureHandle screenPixelMask =
                        UniversalRenderer.CreateRenderGraphTexture(
                            renderGraph,
                            screenMaskDescriptor,
                            "_CharacterScreenPixelMask",
                            true,
                            FilterMode.Point);

                    // Character-local seed cells can have a different screen
                    // phase for every subject. Keep this intermediate at native
                    // resolution so each expanded cell remains attached to its
                    // owner instead of being forced into one viewport grid.
                    RenderTextureDescriptor resolvedDescriptor = sourceDescriptor;
                    resolvedDescriptor.graphicsFormat =
                        GraphicsFormat.R16G16B16A16_SFloat;
                    TextureHandle screenPixelResolved =
                        UniversalRenderer.CreateRenderGraphTexture(
                            renderGraph,
                            resolvedDescriptor,
                            "_CharacterScreenPixelResolved",
                            true,
                            FilterMode.Point);

                    RenderTextureDescriptor outlineDescriptor =
                        resolvedDescriptor;
                    outlineDescriptor.graphicsFormat = GraphicsFormat.R16_SFloat;
                    TextureHandle screenPixelOutlineDepth =
                        UniversalRenderer.CreateRenderGraphTexture(
                            renderGraph,
                            outlineDescriptor,
                            "_CharacterScreenPixelOutlineDepth",
                            true,
                            FilterMode.Point);

                    RecordSourceCopyPass(
                        renderGraph,
                        resources.cameraColor,
                        sourceColor);
                    RecordScreenPixelMaskPass(
                        renderGraph,
                        frameData,
                        resources,
                        screenPixelMask);
                    RecordScreenPixelResolvePass(
                        renderGraph,
                        sourceColor,
                        screenPixelMask,
                        screenPixelResolved);
                    RecordScreenPixelOutlinePass(
                        renderGraph,
                        screenPixelResolved,
                        screenPixelOutlineDepth);
                    RecordScreenPixelCompositePass(
                        renderGraph,
                        resources,
                        screenPixelResolved,
                        screenPixelOutlineDepth);
                }

                RecordCompositePass(renderGraph, resources, mask, quantizedMask);
            }

            private int GetArtPixelSize()
            {
                return Mathf.Clamp(
                    Mathf.RoundToInt(compositeMaterial.GetFloat(ArtPixelSizeId)),
                    1,
                    8);
            }

            private int GetScreenPixelSize()
            {
                return Mathf.Clamp(
                    Mathf.RoundToInt(
                        compositeMaterial.GetFloat(ScreenPixelSizeId)),
                    1,
                    12);
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
                maskMaterial.SetFloat(
                    CharacterArtPixelSizeId,
                    GetArtPixelSize());

                DrawingSettings rawDrawingSettings = RenderingUtils.CreateDrawingSettings(
                    ShaderTags,
                    renderingData,
                    cameraData,
                    lightData,
                    cameraData.defaultOpaqueSortFlags);
                rawDrawingSettings.overrideMaterial = maskMaterial;
                rawDrawingSettings.overrideMaterialPassIndex = 0;
                rawDrawingSettings.perObjectData = PerObjectData.None;

                DrawingSettings seedDrawingSettings = RenderingUtils.CreateDrawingSettings(
                    ShaderTags,
                    renderingData,
                    cameraData,
                    lightData,
                    cameraData.defaultOpaqueSortFlags);
                seedDrawingSettings.overrideMaterial = maskMaterial;
                seedDrawingSettings.overrideMaterialPassIndex = 1;
                seedDrawingSettings.perObjectData = PerObjectData.None;

                FilteringSettings filteringSettings = new FilteringSettings(
                    RenderQueueRange.opaque,
                    -1,
                    CharacterSilhouetteSubject.ClassicOutlineRenderingLayerMask);

                RendererListParams rawRendererListParams = new RendererListParams(
                    renderingData.cullResults,
                    rawDrawingSettings,
                    filteringSettings);
                passData.rawRendererList = renderGraph.CreateRendererList(
                    rawRendererListParams);

                RendererListParams seedRendererListParams = new RendererListParams(
                    renderingData.cullResults,
                    seedDrawingSettings,
                    filteringSettings);
                passData.seedRendererList = renderGraph.CreateRendererList(
                    seedRendererListParams);

                if (!passData.rawRendererList.IsValid() ||
                    !passData.seedRendererList.IsValid())
                {
                    return;
                }

                builder.UseRendererList(passData.rawRendererList);
                builder.UseRendererList(passData.seedRendererList);
                builder.SetRenderAttachment(mask, 0, AccessFlags.Write);
                builder.SetRenderAttachmentDepth(resources.activeDepthTexture, AccessFlags.Read);
                builder.SetRenderFunc((MaskPassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.Color, Color.clear, 1, 0);
                    context.cmd.DrawRendererList(data.rawRendererList);
                    context.cmd.DrawRendererList(data.seedRendererList);
                });
            }

            private void RecordSourceCopyPass(
                RenderGraph renderGraph,
                TextureHandle sourceInput,
                TextureHandle sourceColor)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<SourceCopyPassData>(
                        "Character Screen Pixel Source Copy",
                        out SourceCopyPassData passData);

                passData.sourceInput = sourceInput;
                passData.material = compositeMaterial;

                builder.UseTexture(sourceInput, AccessFlags.Read);
                builder.SetRenderAttachment(sourceColor, 0, AccessFlags.Write);
                builder.SetRenderFunc(static (
                    SourceCopyPassData data,
                    RasterGraphContext context) =>
                {
                    data.material.SetTexture(
                        SourceColorInputTextureId,
                        data.sourceInput);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ScreenSourceCopyPassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordScreenPixelMaskPass(
                RenderGraph renderGraph,
                ContextContainer frameData,
                UniversalResourceData resources,
                TextureHandle screenPixelMask)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ScreenPixelMaskPassData>(
                        "Character Screen Pixel Visible Mask",
                        out ScreenPixelMaskPassData passData);

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
                drawingSettings.overrideMaterial = maskMaterial;
                drawingSettings.overrideMaterialPassIndex =
                    RequiredMaskPassCount - 1;
                drawingSettings.perObjectData = PerObjectData.None;

                FilteringSettings filteringSettings = new FilteringSettings(
                    RenderQueueRange.opaque,
                    -1,
                    CharacterSilhouetteSubject.ScreenPixelRenderingLayerMask);
                RendererListParams rendererListParams = new RendererListParams(
                    renderingData.cullResults,
                    drawingSettings,
                    filteringSettings);
                passData.rendererList = renderGraph.CreateRendererList(
                    rendererListParams);
                maskMaterial.SetFloat(
                    CharacterScreenPixelSizeId,
                    GetScreenPixelSize());
                if (!passData.rendererList.IsValid())
                {
                    return;
                }

                builder.UseRendererList(passData.rendererList);
                builder.SetRenderAttachment(
                    screenPixelMask,
                    0,
                    AccessFlags.Write);
                builder.SetRenderAttachmentDepth(
                    resources.activeDepthTexture,
                    AccessFlags.Read);
                builder.SetRenderFunc(static (
                    ScreenPixelMaskPassData data,
                    RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(
                        RTClearFlags.Color,
                        Color.clear,
                        1,
                        0);
                    context.cmd.DrawRendererList(data.rendererList);
                });
            }

            private void RecordScreenPixelResolvePass(
                RenderGraph renderGraph,
                TextureHandle sourceColor,
                TextureHandle screenPixelMask,
                TextureHandle screenPixelResolved)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ScreenPixelResolvePassData>(
                        "Character Screen Pixel Resolve",
                        out ScreenPixelResolvePassData passData);

                passData.sourceColor = sourceColor;
                passData.screenPixelMask = screenPixelMask;
                passData.material = compositeMaterial;

                builder.UseTexture(sourceColor, AccessFlags.Read);
                builder.UseTexture(screenPixelMask, AccessFlags.Read);
                builder.SetRenderAttachment(
                    screenPixelResolved,
                    0,
                    AccessFlags.Write);
                builder.SetRenderFunc(static (
                    ScreenPixelResolvePassData data,
                    RasterGraphContext context) =>
                {
                    data.material.SetTexture(
                        SourceColorTextureId,
                        data.sourceColor);
                    data.material.SetTexture(
                        ScreenPixelMaskTextureId,
                        data.screenPixelMask);
                    context.cmd.ClearRenderTarget(
                        RTClearFlags.Color,
                        Color.clear,
                        1,
                        0);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ScreenResolvePassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordScreenPixelOutlinePass(
                RenderGraph renderGraph,
                TextureHandle screenPixelResolved,
                TextureHandle screenPixelOutlineDepth)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ScreenPixelOutlinePassData>(
                        "Character Screen Pixel Single Outline",
                        out ScreenPixelOutlinePassData passData);

                passData.screenPixelResolved = screenPixelResolved;
                passData.material = compositeMaterial;

                builder.UseTexture(screenPixelResolved, AccessFlags.Read);
                builder.SetRenderAttachment(
                    screenPixelOutlineDepth,
                    0,
                    AccessFlags.Write);
                builder.SetRenderFunc(static (
                    ScreenPixelOutlinePassData data,
                    RasterGraphContext context) =>
                {
                    data.material.SetTexture(
                        ScreenPixelResolvedTextureId,
                        data.screenPixelResolved);
                    context.cmd.ClearRenderTarget(
                        RTClearFlags.Color,
                        Color.clear,
                        1,
                        0);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ScreenOutlinePassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordScreenPixelCompositePass(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle screenPixelResolved,
                TextureHandle screenPixelOutlineDepth)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ScreenPixelCompositePassData>(
                        "Character Screen Pixel Composite",
                        out ScreenPixelCompositePassData passData);

                passData.screenPixelResolved = screenPixelResolved;
                passData.screenPixelOutlineDepth = screenPixelOutlineDepth;
                // Sample URP's resolved camera-depth texture. activeDepthTexture
                // remains the attachment used while drawing the visibility mask,
                // but is not guaranteed to be safely sampleable on every backend.
                passData.sceneDepth = resources.cameraDepthTexture;
                passData.material = compositeMaterial;

                builder.UseTexture(screenPixelResolved, AccessFlags.Read);
                builder.UseTexture(screenPixelOutlineDepth, AccessFlags.Read);
                builder.UseTexture(resources.cameraDepthTexture, AccessFlags.Read);
                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (
                    ScreenPixelCompositePassData data,
                    RasterGraphContext context) =>
                {
                    data.material.SetTexture(
                        ScreenPixelResolvedTextureId,
                        data.screenPixelResolved);
                    data.material.SetTexture(
                        ScreenPixelOutlineDepthTextureId,
                        data.screenPixelOutlineDepth);
                    data.material.SetTexture(
                        SceneDepthTextureId,
                        data.sceneDepth);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ScreenCompositePassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordExpansionPass(
                RenderGraph renderGraph,
                TextureHandle mask,
                TextureHandle quantizedMask)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ExpansionPassData>(
                        "Character Silhouette Pixel Expansion",
                        out ExpansionPassData passData);

                passData.mask = mask;
                passData.material = compositeMaterial;

                builder.UseTexture(mask, AccessFlags.Read);
                builder.SetRenderAttachment(quantizedMask, 0, AccessFlags.Write);
                builder.SetRenderFunc((ExpansionPassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.Color, Color.clear, 1, 0);
                    data.material.SetTexture(MaskTextureId, data.mask);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ExpandPassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private void RecordCompositePass(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle mask,
                TextureHandle quantizedMask)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<CompositePassData>(
                        "Character Silhouette Composite",
                        out CompositePassData passData);

                passData.mask = mask;
                passData.quantizedMask = quantizedMask;
                passData.material = compositeMaterial;

                builder.UseTexture(mask, AccessFlags.Read);
                builder.UseTexture(quantizedMask, AccessFlags.Read);
                builder.SetRenderAttachment(
                    resources.activeColorTexture,
                    0,
                    AccessFlags.ReadWrite);
                builder.SetRenderFunc((CompositePassData data, RasterGraphContext context) =>
                {
                    data.material.SetTexture(MaskTextureId, data.mask);
                    data.material.SetTexture(
                        QuantizedMaskTextureId,
                        data.quantizedMask);
                    context.cmd.DrawProcedural(
                        Matrix4x4.identity,
                        data.material,
                        ClassicOutlinePassIndex,
                        MeshTopology.Triangles,
                        3,
                        1);
                });
            }

            private sealed class MaskPassData
            {
                public RendererListHandle rawRendererList;
                public RendererListHandle seedRendererList;
            }

            private sealed class ExpansionPassData
            {
                public TextureHandle mask;
                public Material material;
            }

            private sealed class CompositePassData
            {
                public TextureHandle mask;
                public TextureHandle quantizedMask;
                public Material material;
            }

            private sealed class SourceCopyPassData
            {
                public TextureHandle sourceInput;
                public Material material;
            }

            private sealed class ScreenPixelMaskPassData
            {
                public RendererListHandle rendererList;
            }

            private sealed class ScreenPixelResolvePassData
            {
                public TextureHandle sourceColor;
                public TextureHandle screenPixelMask;
                public Material material;
            }

            private sealed class ScreenPixelOutlinePassData
            {
                public TextureHandle screenPixelResolved;
                public Material material;
            }

            private sealed class ScreenPixelCompositePassData
            {
                public TextureHandle screenPixelResolved;
                public TextureHandle screenPixelOutlineDepth;
                public TextureHandle sceneDepth;
                public Material material;
            }
        }
    }
}
