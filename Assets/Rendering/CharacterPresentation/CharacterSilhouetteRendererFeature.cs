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
        private const int RequiredCompositePassCount = 8;
        private const int ExpandPassIndex = 0;
        private const int ClassicOutlinePassIndex = 1;
        private const int ScreenSourceCopyPassIndex = 2;
        private const int ScreenResolvePassIndex = 3;
        private const int ScreenOutlinePassIndex = 4;
        private const int ScreenCompositePassIndex = 5;
        private const int PixelCellCompositePassIndex = 6;
        private const int PixelCellDepthCopyPassIndex = 7;

        [System.Serializable]
        public sealed class Settings
        {
            public Material maskMaterial;
            public Material compositeMaterial;
            public RenderPassEvent injectionPoint = RenderPassEvent.BeforeRenderingPostProcessing;
        }

        [SerializeField] private Settings settings = new Settings();

        private CharacterSilhouettePass pass;
        private CharacterSilhouettePass pixelCellPass;

        public override void Create()
        {
            pass = new CharacterSilhouettePass(false);
            pass.renderPassEvent = settings.injectionPoint;
            pixelCellPass = new CharacterSilhouettePass(true);
            pixelCellPass.renderPassEvent = (RenderPassEvent)((int)RenderPassEvent.AfterRenderingOpaques + 1);
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

            if (CharacterSilhouetteSubject.HasActivePixelCellSubject)
            {
                pixelCellPass.Setup(settings.maskMaterial, settings.compositeMaterial);
                pixelCellPass.ConfigureInput(ScriptableRenderPassInput.Depth);
                pixelCellPass.requiresIntermediateTexture = true;
                renderer.EnqueuePass(pixelCellPass);
            }

            pass.Setup(settings.maskMaterial, settings.compositeMaterial);
            pass.ConfigureInput(ScriptableRenderPassInput.Depth);
            // Both outline paths sample the already lit camera color and resolved
            // depth. Keep cameraColor sampleable instead of using the backbuffer.
            pass.requiresIntermediateTexture = true;
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
            private static readonly int CameraDepthTextureId =
                Shader.PropertyToID("_CameraDepthTexture");
            private static readonly int ArtPixelSizeId =
                Shader.PropertyToID("_ArtPixelSize");
            private static readonly int CellSourceColorTextureId =
                Shader.PropertyToID("_CharacterCellSourceColor");
            private static readonly int CellSourceMetaTextureId =
                Shader.PropertyToID("_CharacterCellSourceMeta");
            private static readonly int CellSearchSizeId =
                Shader.PropertyToID("_CharacterCellSearchSize");
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
            private static readonly List<ShaderTagId> PixelCellShaderTags = new List<ShaderTagId>
            {
                new ShaderTagId("CharacterPixelCellSource")
            };

            private Material maskMaterial;
            private Material compositeMaterial;
            private readonly bool cellOnly;

            public CharacterSilhouettePass(bool cellOnly)
            {
                this.cellOnly = cellOnly;
            }

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
                    !resources.activeDepthTexture.IsValid() ||
                    !resources.cameraColor.IsValid() ||
                    !resources.cameraDepthTexture.IsValid())
                {
                    return;
                }

                if (cellOnly)
                {
                    if (CharacterSilhouetteSubject.HasActivePixelCellSubject)
                        RecordPixelCellSurface(renderGraph, frameData, resources, cameraData);
                    return;
                }

                RenderTextureDescriptor descriptor = cameraData.cameraTargetDescriptor;
                descriptor.depthBufferBits = 0;
                descriptor.msaaSamples = 1;
                // R is visible coverage, G the group ID, and B/A the covered
                // fragment's integer remainder inside its presentation-root cell.
                descriptor.graphicsFormat = GraphicsFormat.R8G8B8A8_UNorm;

                TextureHandle mask = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph,
                    descriptor,
                    "_CharacterSilhouetteMask",
                    true,
                    FilterMode.Point);

                RenderTextureDescriptor quantizedDescriptor = descriptor;
                // R/G retain coverage/group; B/A carry integer source-pixel
                // offsets biased by the search radius for edge reconstruction.
                quantizedDescriptor.graphicsFormat = GraphicsFormat.R8G8B8A8_UNorm;
                TextureHandle quantizedMask = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph,
                    quantizedDescriptor,
                    "_CharacterSilhouetteQuantizedMask",
                    true,
                    FilterMode.Point);

                RecordMaskPass(renderGraph, frameData, resources, mask);
                RecordExpansionPass(renderGraph, mask, quantizedMask, resources.cameraDepthTexture);

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

                // Preserve one native-resolution lit source before either path
                // composites into camera color.
                RecordSourceCopyPass(
                    renderGraph,
                    resources.cameraColor,
                    sourceColor);

                if (CharacterSilhouetteSubject.HasActiveScreenPixelSubject)
                {
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

                RecordCompositePass(
                    renderGraph,
                    resources,
                    mask,
                    quantizedMask,
                    sourceColor);

            }

            private void RecordPixelCellSurface(
                RenderGraph renderGraph,
                ContextContainer frameData,
                UniversalResourceData resources,
                UniversalCameraData cameraData)
            {
                RenderTextureDescriptor descriptor = cameraData.cameraTargetDescriptor;
                descriptor.depthBufferBits = 0;
                descriptor.depthStencilFormat = GraphicsFormat.None;
                descriptor.msaaSamples = 1;
                descriptor.bindMS = false;
                descriptor.graphicsFormat = GraphicsFormat.R32_SFloat;
                TextureHandle resolvedCellDepth = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph, descriptor, "_CharacterCellResolvedDepth", true, FilterMode.Point);
                TextureHandle sceneDepth = resources.cameraDepthTexture;
                RecordPixelCellDepthCopyPass(renderGraph, sceneDepth, resolvedCellDepth);

                // Lit RGB and positive eye depth; no native camera-color copy.
                descriptor.graphicsFormat = GraphicsFormat.R16G16B16A16_SFloat;
                TextureHandle cellColor = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph, descriptor, "_CharacterCellSourceColor", true, FilterMode.Point);

                // R/A split the 16-bit subject ID; G is group, B is cell size.
                descriptor.graphicsFormat = GraphicsFormat.R8G8B8A8_UNorm;
                TextureHandle cellMeta = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph, descriptor, "_CharacterCellSourceMeta", true, FilterMode.Point);

                descriptor.graphicsFormat = GraphicsFormat.None;
                descriptor.depthStencilFormat = GraphicsFormat.D32_SFloat;
                TextureHandle cellDepth = UniversalRenderer.CreateRenderGraphTexture(
                    renderGraph, descriptor, "_CharacterCellSourceDepth", true, FilterMode.Point);

                RecordPixelCellSourcePass(renderGraph, frameData, resources, cellColor, cellMeta, cellDepth);
                RecordPixelCellCompositePass(renderGraph, resources, cellColor, cellMeta,
                    sceneDepth, resolvedCellDepth);
                // Keep URP's original handle: both explicit resource readers and
                // global depth consumers must see cells before lighting/weather.
                RecordPixelCellDepthCopyPass(renderGraph, resolvedCellDepth, sceneDepth, true);
            }

            private void RecordPixelCellDepthCopyPass(
                RenderGraph renderGraph,
                TextureHandle sceneDepth,
                TextureHandle targetDepth,
                bool publishDepth = false)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<PixelCellDepthCopyPassData>(
                        publishDepth ? "Character Pixel Cell Depth Publish" : "Character Pixel Cell World Depth Copy",
                        out PixelCellDepthCopyPassData passData);
                passData.sceneDepth = sceneDepth;
                passData.material = compositeMaterial;
                builder.UseTexture(sceneDepth, AccessFlags.Read);
                if (GraphicsFormatUtility.IsDepthFormat(renderGraph.GetTextureDesc(targetDepth).format))
                    builder.SetRenderAttachmentDepth(targetDepth, AccessFlags.Write);
                else
                    builder.SetRenderAttachment(targetDepth, 0, AccessFlags.Write);
                if (publishDepth)
                {
                    builder.AllowGlobalStateModification(true);
                    builder.SetGlobalTextureAfterPass(targetDepth, CameraDepthTextureId);
                }
                builder.SetRenderFunc(static (PixelCellDepthCopyPassData data, RasterGraphContext context) =>
                {
                    data.material.SetTexture(SceneDepthTextureId, data.sceneDepth);
                    context.cmd.DrawProcedural(Matrix4x4.identity, data.material,
                        PixelCellDepthCopyPassIndex, MeshTopology.Triangles, 3, 1);
                });
            }

            private void RecordPixelCellSourcePass(
                RenderGraph renderGraph,
                ContextContainer frameData,
                UniversalResourceData resources,
                TextureHandle cellColor,
                TextureHandle cellMeta,
                TextureHandle cellDepth)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<PixelCellSourcePassData>(
                        "Character Pixel Cell Source", out PixelCellSourcePassData passData);

                UniversalRenderingData renderingData = frameData.Get<UniversalRenderingData>();
                UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                UniversalLightData lightData = frameData.Get<UniversalLightData>();
                DrawingSettings drawingSettings = RenderingUtils.CreateDrawingSettings(
                    PixelCellShaderTags, renderingData, cameraData, lightData,
                    cameraData.defaultOpaqueSortFlags);
                // Keep URP's per-object lighting/probe data and each material's
                // own lit pass. This is not an override-material mask draw.
                drawingSettings.perObjectData = renderingData.perObjectData;
                FilteringSettings filteringSettings = new FilteringSettings(
                    RenderQueueRange.opaque, -1, CharacterSilhouetteSubject.PixelCellRenderingLayerMask);
                passData.rendererList = renderGraph.CreateRendererList(new RendererListParams(
                    renderingData.cullResults, drawingSettings, filteringSettings));

                if (!passData.rendererList.IsValid())
                    return;

                builder.UseRendererList(passData.rendererList);
                builder.UseAllGlobalTextures(true);
                if (resources.mainShadowsTexture.IsValid())
                    builder.UseTexture(resources.mainShadowsTexture, AccessFlags.Read);
                if (resources.additionalShadowsTexture.IsValid())
                    builder.UseTexture(resources.additionalShadowsTexture, AccessFlags.Read);
                builder.SetRenderAttachment(cellColor, 0, AccessFlags.Write);
                builder.SetRenderAttachment(cellMeta, 1, AccessFlags.Write);
                // Self-occlusion only; world visibility is resolved against the
                // untouched camera depth by the cell-surface composite.
                builder.SetRenderAttachmentDepth(cellDepth, AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (PixelCellSourcePassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.All, Color.clear, 1f, 0);
                    context.cmd.DrawRendererList(data.rendererList);
                });
            }

            private void RecordPixelCellCompositePass(
                RenderGraph renderGraph,
                UniversalResourceData resources,
                TextureHandle cellColor,
                TextureHandle cellMeta,
                TextureHandle sceneDepth,
                TextureHandle resolvedCellDepth)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<PixelCellCompositePassData>(
                        "Character Pixel Cell Surface", out PixelCellCompositePassData passData);

                passData.cellColor = cellColor;
                passData.cellMeta = cellMeta;
                passData.sceneDepth = sceneDepth;
                passData.searchSize = CharacterSilhouetteSubject.MaximumPixelCellSize;
                passData.material = compositeMaterial;
                builder.UseTexture(cellColor, AccessFlags.Read);
                builder.UseTexture(cellMeta, AccessFlags.Read);
                builder.UseTexture(sceneDepth, AccessFlags.Read);
                builder.SetRenderAttachment(resources.activeColorTexture, 0, AccessFlags.ReadWrite);
                builder.SetRenderAttachment(resolvedCellDepth, 1, AccessFlags.ReadWrite);
                builder.SetRenderAttachmentDepth(resources.activeDepthTexture, AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (PixelCellCompositePassData data, RasterGraphContext context) =>
                {
                    data.material.SetTexture(CellSourceColorTextureId, data.cellColor);
                    data.material.SetTexture(CellSourceMetaTextureId, data.cellMeta);
                    data.material.SetTexture(SceneDepthTextureId, data.sceneDepth);
                    data.material.SetFloat(CellSearchSizeId, data.searchSize);
                    context.cmd.DrawProcedural(Matrix4x4.identity, data.material,
                        PixelCellCompositePassIndex, MeshTopology.Triangles, 3, 1);
                });
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

                if (!passData.rawRendererList.IsValid())
                {
                    return;
                }

                builder.UseRendererList(passData.rawRendererList);
                builder.SetRenderAttachment(mask, 0, AccessFlags.Write);
                builder.SetRenderAttachmentDepth(resources.activeDepthTexture, AccessFlags.Read);
                builder.SetRenderFunc((MaskPassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.Color, Color.clear, 1, 0);
                    context.cmd.DrawRendererList(data.rawRendererList);
                });
            }

            private void RecordSourceCopyPass(
                RenderGraph renderGraph,
                TextureHandle sourceInput,
                TextureHandle sourceColor)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<SourceCopyPassData>(
                        "Character Lit Source Copy",
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
                TextureHandle quantizedMask,
                TextureHandle sceneDepth)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<ExpansionPassData>(
                        "Character Silhouette Pixel Expansion",
                        out ExpansionPassData passData);

                passData.mask = mask;
                passData.sceneDepth = sceneDepth;
                passData.material = compositeMaterial;

                builder.UseTexture(mask, AccessFlags.Read);
                builder.UseTexture(sceneDepth, AccessFlags.Read);
                builder.SetRenderAttachment(quantizedMask, 0, AccessFlags.Write);
                builder.SetRenderFunc((ExpansionPassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.Color, Color.clear, 1, 0);
                    data.material.SetTexture(MaskTextureId, data.mask);
                    data.material.SetTexture(SceneDepthTextureId, data.sceneDepth);
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
                TextureHandle quantizedMask,
                TextureHandle sourceColor)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<CompositePassData>(
                        "Character Silhouette Composite",
                        out CompositePassData passData);

                passData.mask = mask;
                passData.quantizedMask = quantizedMask;
                passData.sourceColor = sourceColor;
                passData.material = compositeMaterial;

                builder.UseTexture(mask, AccessFlags.Read);
                builder.UseTexture(quantizedMask, AccessFlags.Read);
                builder.UseTexture(sourceColor, AccessFlags.Read);
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
                    data.material.SetTexture(SourceColorTextureId, data.sourceColor);
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
            }

            private sealed class PixelCellSourcePassData
            {
                public RendererListHandle rendererList;
            }

            private sealed class PixelCellDepthCopyPassData
            {
                public TextureHandle sceneDepth;
                public Material material;
            }

            private sealed class PixelCellCompositePassData
            {
                public TextureHandle cellColor;
                public TextureHandle cellMeta;
                public TextureHandle sceneDepth;
                public int searchSize;
                public Material material;
            }

            private sealed class ExpansionPassData
            {
                public TextureHandle mask;
                public TextureHandle sceneDepth;
                public Material material;
            }

            private sealed class CompositePassData
            {
                public TextureHandle mask;
                public TextureHandle quantizedMask;
                public TextureHandle sourceColor;
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
