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
            public ComputeShader adaptiveToneCompute;
            public CharacterAdaptiveTonePass.Settings adaptiveTones = new CharacterAdaptiveTonePass.Settings();
        }

        [SerializeField] private Settings settings = new Settings();

        private CharacterSilhouettePass pass;
        private CharacterSilhouettePass pixelCellPass;
        private ToneCaptureRequest pendingToneCapture;

        public CharacterAdaptiveTonePass.Settings AdaptiveTones => settings.adaptiveTones;
        public uint[] LastAdaptiveToneDiagnostics => pixelCellPass?.lastToneDiagnostics;
        public CharacterAdaptiveTonePass.ProfilingCost AdaptiveToneCost =>
            pixelCellPass != null ? pixelCellPass.ToneCost : default;

        public void SetAdaptiveToneProfilingEnabled(bool enabled)
        {
            if (pixelCellPass == null)
                throw new System.InvalidOperationException("Character render passes have not been created.");
            pixelCellPass.SetToneProfilingEnabled(enabled);
        }

        public void ConfigureAdaptiveToneExperiment(ComputeShader compute, bool enabled)
        {
            settings.adaptiveToneCompute = compute;
            settings.adaptiveTones.enabled = enabled;
        }

        /// <summary>Call after a scripted camera cut or restoring a controlled pose/light capture.</summary>
        public void ResetAdaptiveToneHistory(Camera camera = null) => pixelCellPass?.ResetToneHistory(camera);

        public void RequestAdaptiveToneDiagnostics()
        {
            if (pixelCellPass == null)
                throw new System.InvalidOperationException("Character render passes have not been created.");
            pixelCellPass.captureToneDiagnostics = true;
        }

        /// <summary>
        /// Capture one actual render of targetCamera. The callback receives
        /// owned raw bytes after all 17 readbacks complete. A queued/in-flight
        /// request cannot be replaced. No diagnostic resources exist otherwise.
        /// </summary>
        public void RequestAdaptiveToneCapture(Camera targetCamera, string captureId,
            System.Action<AdaptiveToneCapture> callback)
        {
            if (targetCamera == null) throw new System.ArgumentNullException(nameof(targetCamera));
            if (string.IsNullOrWhiteSpace(captureId)) throw new System.ArgumentException("A capture ID is required.", nameof(captureId));
            if (callback == null) throw new System.ArgumentNullException(nameof(callback));
            if (pendingToneCapture != null) throw new System.InvalidOperationException("An adaptive tone capture is already queued or in flight.");
            if (pixelCellPass == null || !isActive || settings.adaptiveTones == null || !settings.adaptiveTones.enabled)
                throw new System.InvalidOperationException("Adaptive tone rendering must be active before requesting a capture.");
            if (targetCamera.cameraType != CameraType.Game)
                throw new System.ArgumentException("The capture target must be a Game camera.", nameof(targetCamera));
            if (!CharacterSilhouetteSubject.TryGetAdaptiveToneSubject(out _))
                throw new System.InvalidOperationException("A capture requires the existing opted-in pixel-cell subject.");
            if (!SystemInfo.supportsAsyncGPUReadback || SystemInfo.supportedRenderTargetCount < 3)
                throw new System.NotSupportedException("Adaptive tone capture requires async GPU readback and three render targets.");
            pendingToneCapture = new ToneCaptureRequest(this, targetCamera, captureId, callback,
                JsonUtility.ToJson(settings.adaptiveTones));
        }

        private ToneCaptureRequest CaptureFor(Camera camera)
        {
            ToneCaptureRequest request = pendingToneCapture;
            return request != null && !request.recorded && request.targetCamera == camera ? request : null;
        }

        private void FailCaptureFor(Camera camera, string error)
        {
            CaptureFor(camera)?.Cancel(error);
        }

        private void DeliverCapture(ToneCaptureRequest request)
        {
            if (ReferenceEquals(pendingToneCapture, request)) pendingToneCapture = null;
            try { request.callback(request.packet); }
            catch (System.Exception exception) { Debug.LogException(exception); }
        }

        public override void Create()
        {
            pendingToneCapture?.Cancel("Renderer feature was recreated before the capture completed.");
            pass?.DisposeToneResources();
            pixelCellPass?.DisposeToneResources();
            pass = new CharacterSilhouettePass(false, this);
            pass.renderPassEvent = settings.injectionPoint;
            pixelCellPass = new CharacterSilhouettePass(true, this);
            pixelCellPass.renderPassEvent = (RenderPassEvent)((int)RenderPassEvent.AfterRenderingOpaques + 1);
        }

        protected override void Dispose(bool disposing)
        {
            pendingToneCapture?.Cancel("Renderer feature was disposed before the capture completed.");
            pass?.DisposeToneResources();
            pixelCellPass?.DisposeToneResources();
            base.Dispose(disposing);
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
                FailCaptureFor(renderingData.cameraData.camera,
                    "Target camera could not enqueue the character rendering passes.");
                return;
            }

            if (CharacterSilhouetteSubject.HasActivePixelCellSubject)
            {
                pixelCellPass.Setup(settings.maskMaterial, settings.compositeMaterial,
                    settings.adaptiveToneCompute, settings.adaptiveTones);
                pixelCellPass.ConfigureInput(ScriptableRenderPassInput.Depth);
                pixelCellPass.requiresIntermediateTexture = true;
                renderer.EnqueuePass(pixelCellPass);
            }
            else
            {
                FailCaptureFor(renderingData.cameraData.camera, "Target camera has no active pixel-cell subject.");
            }

            pass.Setup(settings.maskMaterial, settings.compositeMaterial,
                settings.adaptiveToneCompute, settings.adaptiveTones);
            pass.ConfigureInput(ScriptableRenderPassInput.Depth);
            // Both outline paths sample the already lit camera color and resolved
            // depth. Keep cameraColor sampleable instead of using the backbuffer.
            pass.requiresIntermediateTexture = true;
            renderer.EnqueuePass(pass);
        }

        private sealed class ToneCaptureRequest
        {
            private const int ReadbackCount = 17;
            public readonly Camera targetCamera;
            public readonly System.Action<AdaptiveToneCapture> callback;
            public AdaptiveToneCapture packet;
            public bool recorded;
            private readonly CharacterSilhouetteRendererFeature owner;
            private readonly object gate = new object();
            private readonly HashSet<string> received = new HashSet<string>();
            private bool started, sealedRequests, delivered;

            public ToneCaptureRequest(CharacterSilhouetteRendererFeature owner, Camera camera,
                string captureId, System.Action<AdaptiveToneCapture> callback, string settingsJson)
            {
                this.owner = owner;
                targetCamera = camera;
                this.callback = callback;
                packet = new AdaptiveToneCapture(captureId, -1, 0, 0, 0,
                    camera.name + "#" + camera.GetEntityId(), settingsJson);
            }

            public void RecordFrame(int width, int height, int subjectId, string settingsJson)
            {
                recorded = true;
                packet = new AdaptiveToneCapture(packet.captureId, Time.frameCount, width, height,
                    subjectId, packet.cameraId, settingsJson);
            }

            public bool BeginReadbacks()
            {
                lock (gate)
                {
                    if (delivered || started) return false;
                    started = true;
                    return true;
                }
            }

            public void Receive(string key, AsyncGPUReadbackRequest request)
            {
                byte[] bytes = null;
                string error = null;
                try
                {
                    if (request.hasError) error = key + ": GPU readback failed.";
                    else bytes = request.GetData<byte>().ToArray();
                }
                catch (System.Exception exception) { error = key + ": " + exception.Message; }
                FinishResource(key, bytes, error);
            }

            public void FailedResource(string key, System.Exception exception)
            {
                FinishResource(key, null, key + ": " + exception.Message);
            }

            private void FinishResource(string key, byte[] bytes, string error)
            {
                bool publish;
                lock (gate)
                {
                    if (delivered || !received.Add(key)) return;
                    if (bytes != null) packet.data.Add(key, bytes);
                    AppendError(error);
                    publish = sealedRequests && received.Count == ReadbackCount;
                    if (publish) delivered = true;
                }
                if (publish) owner.DeliverCapture(this);
            }

            public void SealReadbacks()
            {
                bool publish;
                lock (gate)
                {
                    if (delivered) return;
                    sealedRequests = true;
                    publish = received.Count == ReadbackCount;
                    if (publish) delivered = true;
                }
                if (publish) owner.DeliverCapture(this);
            }

            public void Cancel(string error)
            {
                bool publish;
                lock (gate)
                {
                    if (delivered) return;
                    AppendError(error);
                    // Already queued GPU copies still complete before delivery.
                    publish = !started;
                    if (publish) delivered = true;
                }
                if (publish) owner.DeliverCapture(this);
            }

            private void AppendError(string error)
            {
                if (string.IsNullOrEmpty(error)) return;
                packet.error = string.IsNullOrEmpty(packet.error) ? error : packet.error + "\n" + error;
            }
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
            private static readonly int HairLightingAnalysisId =
                Shader.PropertyToID("_CharacterHairLightingAnalysis");
            private static readonly int SkinLightingAnalysisId =
                Shader.PropertyToID("_CharacterSkinLightingAnalysis");
            private static readonly int CaptureLightingId =
                Shader.PropertyToID("_CharacterToneCaptureLighting");
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
            private static readonly List<ShaderTagId> ToneNativeShaderTags = new List<ShaderTagId>
            {
                new ShaderTagId("CharacterToneNativeSource")
            };

            private Material maskMaterial;
            private Material compositeMaterial;
            private readonly bool cellOnly;
            private readonly CharacterSilhouetteRendererFeature owner;
            private ComputeShader adaptiveToneCompute;
            private CharacterAdaptiveTonePass.Settings adaptiveToneSettings;
            private readonly CharacterAdaptiveTonePass adaptiveTonePass = new CharacterAdaptiveTonePass();
            public bool captureToneDiagnostics;
            public uint[] lastToneDiagnostics;
            public CharacterAdaptiveTonePass.ProfilingCost ToneCost => adaptiveTonePass.LastCost;
            public void SetToneProfilingEnabled(bool enabled) => adaptiveTonePass.SetProfilingEnabled(enabled);
            public void DisposeToneResources() => adaptiveTonePass.Dispose();
            public void ResetToneHistory(Camera camera) => adaptiveTonePass.ResetHistory(camera);

            public CharacterSilhouettePass(bool cellOnly, CharacterSilhouetteRendererFeature owner)
            {
                this.cellOnly = cellOnly;
                this.owner = owner;
            }

            public void Setup(Material newMaskMaterial, Material newCompositeMaterial,
                ComputeShader toneCompute, CharacterAdaptiveTonePass.Settings toneSettings)
            {
                maskMaterial = newMaskMaterial;
                compositeMaterial = newCompositeMaterial;
                adaptiveToneCompute = toneCompute;
                adaptiveToneSettings = toneSettings;
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
                    if (cellOnly) owner.FailCaptureFor(cameraData.camera,
                        "Target camera render graph lacks the required color/depth resources.");
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
                ToneCaptureRequest capture = owner.CaptureFor(cameraData.camera);
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

                // Only this opt-in color branch changes. The original sparse
                // seeds, metadata, coverage, outline and scene depth still own
                // all geometry decisions made by the existing cell composite.
                if (adaptiveToneSettings != null && adaptiveToneSettings.enabled &&
                    CharacterSilhouetteSubject.TryGetAdaptiveToneSubject(out int toneSubjectId, out var toneSubject))
                {
                    int width = cameraData.cameraTargetDescriptor.width;
                    int height = cameraData.cameraTargetDescriptor.height;
                    adaptiveTonePass.ValidateConfiguration(adaptiveToneCompute, toneSubjectId,
                        width, height, adaptiveToneSettings);
                    descriptor.graphicsFormat = GraphicsFormat.R16G16B16A16_SFloat;
                    descriptor.depthStencilFormat = GraphicsFormat.None;
                    TextureHandle nativeColor = UniversalRenderer.CreateRenderGraphTexture(
                        renderGraph, descriptor, "_CharacterToneNativeColor", true, FilterMode.Point);
                    TextureHandle nativeLighting = adaptiveToneSettings.hairLighting || adaptiveToneSettings.skinLighting ||
                        adaptiveToneSettings.regionTransitions || capture != null ?
                        UniversalRenderer.CreateRenderGraphTexture(renderGraph, descriptor,
                            "_CharacterToneNativeLighting", true, FilterMode.Point) : TextureHandle.nullHandle;
                    descriptor.graphicsFormat = GraphicsFormat.R8G8B8A8_UNorm;
                    TextureHandle nativeMeta = UniversalRenderer.CreateRenderGraphTexture(
                        renderGraph, descriptor, "_CharacterToneNativeMeta", true, FilterMode.Point);
                    descriptor.graphicsFormat = GraphicsFormat.None;
                    descriptor.depthStencilFormat = GraphicsFormat.D32_SFloat;
                    TextureHandle nativeDepth = UniversalRenderer.CreateRenderGraphTexture(
                        renderGraph, descriptor, "_CharacterToneNativeDepth", true, FilterMode.Point);
                    RecordPixelCellSourcePass(renderGraph, frameData, resources,
                        nativeColor, nativeMeta, nativeDepth, true, nativeLighting, capture != null);
                    TextureHandle originalCellColor = cellColor;
                    cellColor = adaptiveTonePass.Record(renderGraph, nativeColor, nativeMeta,
                        cellColor, cellMeta, adaptiveToneCompute, toneSubjectId, width, height,
                        adaptiveToneSettings, out BufferHandle toneStatus,
                        out CharacterAdaptiveTonePass.BufferSet toneBuffers, nativeLighting,
                        cameraData.camera, toneSubject, toneSubject.PixelCellSize);
                    if (capture != null)
                    {
                        capture.RecordFrame(width, height, toneSubjectId, JsonUtility.ToJson(adaptiveToneSettings));
                        RecordToneCaptureReadback(renderGraph, capture, toneBuffers,
                            nativeColor, nativeMeta, nativeLighting, originalCellColor, cellMeta, cellColor);
                    }
                    if (captureToneDiagnostics)
                    {
                        captureToneDiagnostics = false;
                        RecordToneDiagnosticReadback(renderGraph, toneStatus);
                    }
                }
                else if (capture != null)
                {
                    capture.Cancel("Adaptive tone analysis or its opted-in subject was unavailable in the target frame.");
                }
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
                    // These two draws copy in opposite directions using one material.
                    // Capture each source in the draw command; changing the shared
                    // material lets the final publish replace the initial copy's input.
                    data.properties.Clear();
                    data.properties.SetTexture(SceneDepthTextureId, data.sceneDepth);
                    context.cmd.DrawProcedural(Matrix4x4.identity, data.material,
                        PixelCellDepthCopyPassIndex, MeshTopology.Triangles, 3, 1, data.properties);
                });
            }

            private void RecordPixelCellSourcePass(
                RenderGraph renderGraph,
                ContextContainer frameData,
                UniversalResourceData resources,
                TextureHandle cellColor,
                TextureHandle cellMeta,
                TextureHandle cellDepth,
                bool nativeToneSource = false, TextureHandle nativeLighting = default,
                bool captureLighting = false)
            {
                using IRasterRenderGraphBuilder builder =
                    renderGraph.AddRasterRenderPass<PixelCellSourcePassData>(
                        nativeToneSource ? "Character Adaptive Tone Native Source" : "Character Pixel Cell Source",
                        out PixelCellSourcePassData passData);

                UniversalRenderingData renderingData = frameData.Get<UniversalRenderingData>();
                UniversalCameraData cameraData = frameData.Get<UniversalCameraData>();
                UniversalLightData lightData = frameData.Get<UniversalLightData>();
                DrawingSettings drawingSettings = RenderingUtils.CreateDrawingSettings(
                    nativeToneSource ? ToneNativeShaderTags : PixelCellShaderTags,
                    renderingData, cameraData, lightData,
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
                if (nativeLighting.IsValid()) builder.SetRenderAttachment(nativeLighting, 2, AccessFlags.Write);
                passData.hairLighting = nativeToneSource && adaptiveToneSettings != null && adaptiveToneSettings.hairLighting;
                passData.skinLighting = nativeToneSource && adaptiveToneSettings != null && adaptiveToneSettings.skinLighting;
                passData.captureLighting = nativeToneSource && captureLighting;
                builder.AllowGlobalStateModification(true);
                // Self-occlusion only; world visibility is resolved against the
                // untouched camera depth by the cell-surface composite.
                builder.SetRenderAttachmentDepth(cellDepth, AccessFlags.ReadWrite);
                builder.SetRenderFunc(static (PixelCellSourcePassData data, RasterGraphContext context) =>
                {
                    context.cmd.ClearRenderTarget(RTClearFlags.All, Color.clear, 1f, 0);
                    context.cmd.SetGlobalFloat(HairLightingAnalysisId, data.hairLighting ? 1f : 0f);
                    context.cmd.SetGlobalFloat(SkinLightingAnalysisId, data.skinLighting ? 1f : 0f);
                    if (data.captureLighting) context.cmd.SetGlobalFloat(CaptureLightingId, 1f);
                    context.cmd.DrawRendererList(data.rendererList);
                    if (data.captureLighting) context.cmd.SetGlobalFloat(CaptureLightingId, 0f);
                    context.cmd.SetGlobalFloat(HairLightingAnalysisId, 0f);
                    context.cmd.SetGlobalFloat(SkinLightingAnalysisId, 0f);
                });
            }

            private sealed class ToneDiagnosticReadbackData
            {
                public BufferHandle status;
                public CharacterSilhouettePass owner;
            }

            private sealed class ToneCaptureReadbackData
            {
                public ToneCaptureRequest request;
                public CharacterAdaptiveTonePass.BufferSet buffers;
                public TextureHandle nativeColor, nativeMeta, nativeLighting, cellColor, cellMeta, output;
            }

            private static void RecordToneCaptureReadback(RenderGraph renderGraph,
                ToneCaptureRequest request, CharacterAdaptiveTonePass.BufferSet buffers,
                TextureHandle nativeColor, TextureHandle nativeMeta, TextureHandle nativeLighting,
                TextureHandle cellColor, TextureHandle cellMeta, TextureHandle output)
            {
                using var builder = renderGraph.AddUnsafePass<ToneCaptureReadbackData>(
                    "Character Adaptive Tone Frame Capture", out var data);
                data.request = request;
                data.buffers = buffers;
                data.nativeColor = nativeColor;
                data.nativeMeta = nativeMeta;
                data.nativeLighting = nativeLighting;
                data.cellColor = cellColor;
                data.cellMeta = cellMeta;
                data.output = output;
                builder.UseBuffer(buffers.groups, AccessFlags.Read);
                builder.UseBuffer(buffers.histogram, AccessFlags.Read);
                builder.UseBuffer(buffers.tiles, AccessFlags.Read);
                builder.UseBuffer(buffers.tileHistogram, AccessFlags.Read);
                builder.UseBuffer(buffers.supports, AccessFlags.Read);
                builder.UseBuffer(buffers.highlightHistogram, AccessFlags.Read);
                builder.UseBuffer(buffers.status, AccessFlags.Read);
                builder.UseBuffer(buffers.palette, AccessFlags.Read);
                builder.UseBuffer(buffers.solutions, AccessFlags.Read);
                builder.UseTexture(nativeColor, AccessFlags.Read);
                builder.UseBuffer(buffers.previousRegions, AccessFlags.Read);
                builder.UseBuffer(buffers.nextRegions, AccessFlags.Read);
                builder.UseTexture(nativeMeta, AccessFlags.Read);
                builder.UseTexture(nativeLighting, AccessFlags.Read);
                builder.UseTexture(cellColor, AccessFlags.Read);
                builder.UseTexture(cellMeta, AccessFlags.Read);
                builder.UseTexture(output, AccessFlags.Read);
                builder.AllowPassCulling(false);
                builder.SetRenderFunc(static (ToneCaptureReadbackData passData, UnsafeGraphContext context) =>
                {
                    // Copy references before queuing callbacks. RenderGraph pass
                    // data and handles cannot be retained by a later callback.
                    ToneCaptureRequest capture = passData.request;
                    if (!capture.BeginReadbacks()) return;
                    QueueCaptureBuffer(context.cmd, capture, "groups", passData.buffers.groups);
                    QueueCaptureBuffer(context.cmd, capture, "histogram", passData.buffers.histogram);
                    QueueCaptureBuffer(context.cmd, capture, "tiles", passData.buffers.tiles);
                    QueueCaptureBuffer(context.cmd, capture, "tileHistogram", passData.buffers.tileHistogram);
                    QueueCaptureBuffer(context.cmd, capture, "supports", passData.buffers.supports);
                    QueueCaptureBuffer(context.cmd, capture, "highlightHistogram", passData.buffers.highlightHistogram);
                    QueueCaptureBuffer(context.cmd, capture, "status", passData.buffers.status);
                    QueueCaptureBuffer(context.cmd, capture, "palette", passData.buffers.palette);
                    QueueCaptureBuffer(context.cmd, capture, "solutions", passData.buffers.solutions);
                    QueueCaptureBuffer(context.cmd, capture, "previousRegions", passData.buffers.previousRegions);
                    QueueCaptureBuffer(context.cmd, capture, "nextRegions", passData.buffers.nextRegions);
                    QueueCaptureTexture(context.cmd, capture, "nativeColor", passData.nativeColor);
                    QueueCaptureTexture(context.cmd, capture, "nativeMeta", passData.nativeMeta);
                    QueueCaptureTexture(context.cmd, capture, "nativeLighting", passData.nativeLighting);
                    QueueCaptureTexture(context.cmd, capture, "cellColor", passData.cellColor);
                    QueueCaptureTexture(context.cmd, capture, "cellMeta", passData.cellMeta);
                    QueueCaptureTexture(context.cmd, capture, "output", passData.output);
                    capture.SealReadbacks();
                });
            }

            private static void QueueCaptureBuffer(UnsafeCommandBuffer cmd, ToneCaptureRequest capture,
                string key, BufferHandle handle)
            {
                try { cmd.RequestAsyncReadback((GraphicsBuffer)handle, request => capture.Receive(key, request)); }
                catch (System.Exception exception) { capture.FailedResource(key, exception); }
            }

            private static void QueueCaptureTexture(UnsafeCommandBuffer cmd, ToneCaptureRequest capture,
                string key, TextureHandle handle)
            {
                // No destination format conversion: preserve RGBA16F/RGBA8 bytes.
                try { cmd.RequestAsyncReadback((Texture)handle, 0, request => capture.Receive(key, request)); }
                catch (System.Exception exception) { capture.FailedResource(key, exception); }
            }

            private void RecordToneDiagnosticReadback(RenderGraph renderGraph, BufferHandle status)
            {
                // Explicit one-shot diagnostics only: normal rendering never
                // reads pixels or GPU analysis buffers back to the CPU.
                using var builder = renderGraph.AddUnsafePass<ToneDiagnosticReadbackData>(
                    "Character Adaptive Tone Diagnostic Readback", out var data);
                data.status = status;
                data.owner = this;
                builder.UseBuffer(status, AccessFlags.Read);
                builder.AllowPassCulling(false);
                builder.SetRenderFunc(static (ToneDiagnosticReadbackData passData, UnsafeGraphContext context) =>
                {
                    CharacterSilhouettePass owner = passData.owner;
                    context.cmd.RequestAsyncReadback((GraphicsBuffer)passData.status, request =>
                    {
                        if (request.hasError)
                        {
                            Debug.LogError("Adaptive tone diagnostic GPU readback failed.");
                            return;
                        }
                        owner.lastToneDiagnostics = request.GetData<uint>().ToArray();
                    });
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
                public bool hairLighting;
                public bool skinLighting;
                public bool captureLighting;
                public RendererListHandle rendererList;
            }

            private sealed class PixelCellDepthCopyPassData
            {
                public TextureHandle sceneDepth;
                public Material material;
                public readonly MaterialPropertyBlock properties = new MaterialPropertyBlock();
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
