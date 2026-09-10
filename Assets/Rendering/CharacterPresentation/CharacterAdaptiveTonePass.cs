using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;

namespace FantasySurvival.Rendering
{
    /// <summary>
    /// One explicitly requested rendered frame. Byte arrays own copies of GPU
    /// readback memory; no RenderGraph handles survive in the delivered packet.
    /// Color/lighting/output textures are RGBA16F, metadata is RGBA8, uint
    /// buffers have stride 4, and palette/solutions contain float4 values.
    /// </summary>
    [Serializable]
    public sealed class AdaptiveToneCapture
    {
        public string captureId, cameraId, settingsJson;
        public int frame, width, height, subjectId;
        public string error;
        public readonly Dictionary<string, byte[]> data = new Dictionary<string, byte[]>();

        internal AdaptiveToneCapture(string captureId, int frame, int width, int height,
            int subjectId, string cameraId, string settingsJson)
        {
            this.captureId = captureId;
            this.frame = frame;
            this.width = width;
            this.height = height;
            this.subjectId = subjectId;
            this.cameraId = cameraId;
            this.settingsJson = settingsJson;
        }
    }

    /// <summary>
    /// Records the opt-in, single-subject GPU tone experiment between the existing
    /// cell source and composite. Analysis belongs to RenderGraph; this owner
    /// retains partition/contour state per camera, never a previous color image.
    /// </summary>
    public sealed class CharacterAdaptiveTonePass : IDisposable
    {
        public const int MaximumSourcePixels = 4_194_304;
        public const int MaximumGroups = 160;
        public const int GlobalStatusIndex = MaximumGroups;
        public const int StatusCount = MaximumGroups + 1;

        private const int HistogramBins = 32;
        public const int HistoryRowsPerGroup = HistogramBins + 2;
        public const int RegionRowsPerGroup = 8 + 63 * 3;
        private const double MaximumRegionRenderGapSeconds = 0.5;
        private const int SpatialTiles = 16;
        private const int ClearElements = MaximumGroups * SpatialTiles * HistogramBins;
        private const GraphicsFormat ColorFormat = GraphicsFormat.R16G16B16A16_SFloat;
        private const GraphicsFormat MetaFormat = GraphicsFormat.R8G8B8A8_UNorm;

        [Serializable]
        public sealed class Settings
        {
            [Tooltip("Prototype only. Requires exactly one opted-in pixel-cell subject.")]
            public bool enabled;

            [Range(0.0001f, 1f)] public float toneError = 0.06f;
            [Tooltip("Oklab L groups only: scale error and contrast limits by mean lightness. Does not normalize output RGB or stabilize spatial regions. Hair/Skin illumination modes take precedence.")]
            public bool relativeLightness;
            [Range(0.0001f, 1f)] public float lightnessRelativeError = 0.10f;
            [Range(0.0001f, 1f), Tooltip("Oklab L floor for relative error/contrast limits; not an illumination Y floor.")]
            public float lightnessBlackFloor = 0.02f;
            [Range(0.005f, 1f)] public float chromaError = 0.06f;
            [Range(0.0001f, 1f)] public float contrastRetention = 0.65f;
            [Range(0.0001f, 1f)] public float minimumContrast = 0.025f;
            [Range(0.0001f, 1f)] public float highlightMinimumContrast = 0.025f;
            [Tooltip("Hair only: partition actual incident diffuse light, retaining observed source RGB. Off preserves the previous algorithm.")]
            public bool hairLighting;
            [Range(0.0001f, 1f)] public float hairRelativeError = 0.10f;
            [Range(0.0001f, 1f)] public float hairIlluminationFloor = 0.02f;
            [Tooltip("Skin only: partition actual incident diffuse light, retaining observed source RGB. Off preserves the previous algorithm.")]
            public bool skinLighting;
            [Range(0.0001f, 1f)] public float skinRelativeError = 0.10f;
            [Range(0.0001f, 1f)] public float skinIlluminationFloor = 0.02f;
            [Tooltip("Legacy path, used when Region Transitions is off: retain partitions only within CURRENT error/contrast bounds and select current observed colors.")]
            public bool temporalStability = true;
            [Range(0f, 0.5f), Tooltip("Relative error headroom required to reduce tone count. Increasing detail uses the original limit.")]
            public float shrinkMargin = 0.10f;
            [Tooltip("Move persistent illumination contours and their representative region colors over time. Does not accumulate screen pixels.")]
            public bool regionTransitions;
            [Range(0.02f, 2f), Tooltip("Game-time response duration for contour and representative-region changes.")]
            public float regionTransitionSeconds = 0.25f;
        }

        /// <summary>
        /// Last available Unity recorder totals for the compute kernels only;
        /// excludes dense rasterization, graph recording and the final composite.
        /// GPU recorder results may lag CPU results. A null cost is unmeasured,
        /// unsupported or incomplete, never evidence of a zero-cost pass.
        /// </summary>
        public readonly struct ProfilingCost
        {
            public bool RecordingEnabled { get; }
            public float? CpuMilliseconds { get; }
            public float? GpuMilliseconds { get; }
            public float? InlineCpuMilliseconds { get; }

            internal ProfilingCost(bool enabled, float? cpu, float? gpu, float? inlineCpu)
            {
                RecordingEnabled = enabled;
                CpuMilliseconds = cpu;
                GpuMilliseconds = gpu;
                InlineCpuMilliseconds = inlineCpu;
            }
        }

        [Flags]
        private enum Buffers
        {
            None = 0,
            Groups = 1 << 0,
            Histogram = 1 << 1,
            Tiles = 1 << 2,
            TileHistogram = 1 << 3,
            Supports = 1 << 4,
            HighlightHistogram = 1 << 5,
            Status = 1 << 6,
            Palette = 1 << 7,
            Solutions = 1 << 8,
            All = (1 << 9) - 1
        }

        [Flags]
        private enum Textures
        {
            None = 0,
            SourceColor = 1 << 0,
            SourceMeta = 1 << 1,
            CellColor = 1 << 2,
            CellMeta = 1 << 3,
            Output = 1 << 4,
            SourceLighting = 1 << 5
        }

        private readonly struct KernelDefinition
        {
            public readonly string name;
            public readonly string passName;
            public readonly Buffers buffers;
            public readonly Textures textures;
            public readonly uint threadsX;
            public readonly uint threadsY;

            public KernelDefinition(string name, Buffers buffers, Textures textures,
                uint threadsX, uint threadsY)
            {
                this.name = name;
                passName = "Character Adaptive Tone " + name;
                this.buffers = buffers;
                this.textures = textures;
                this.threadsX = threadsX;
                this.threadsY = threadsY;
            }
        }

        private static readonly KernelDefinition[] KernelDefinitions =
        {
            // Keep Clear within D3D11's eight UAV slots. SolveTones initializes
            // every palette/solution slot before it can return early.
            new KernelDefinition("Clear", Buffers.All & ~(Buffers.Palette | Buffers.Solutions),
                Textures.None, 64, 1),
            new KernelDefinition("GatherGroups", Buffers.Groups | Buffers.Status,
                Textures.SourceColor | Textures.SourceMeta, 8, 8),
            new KernelDefinition("GatherHistogram", Buffers.Groups | Buffers.Histogram |
                Buffers.Tiles | Buffers.TileHistogram | Buffers.Status,
                Textures.SourceColor | Textures.SourceMeta, 8, 8),
            new KernelDefinition("SolveTones", Buffers.Groups | Buffers.Histogram |
                Buffers.Tiles | Buffers.TileHistogram | Buffers.Supports | Buffers.Palette |
                Buffers.Solutions | Buffers.Status, Textures.SourceColor, 32, 1),
            new KernelDefinition("GatherHighlights", Buffers.Groups | Buffers.Palette |
                Buffers.Supports | Buffers.Solutions | Buffers.HighlightHistogram | Buffers.Status,
                Textures.SourceColor | Textures.SourceMeta, 8, 8),
            new KernelDefinition("SolveHighlights", Buffers.Groups | Buffers.Histogram |
                Buffers.HighlightHistogram | Buffers.Solutions | Buffers.Status,
                Textures.SourceColor, 32, 1),
            new KernelDefinition("UpdateRegions", Buffers.Groups | Buffers.Histogram |
                Buffers.Palette | Buffers.Solutions | Buffers.Status | Buffers.Supports, Textures.None, 32, 1),
            new KernelDefinition("Resolve", Buffers.Groups | Buffers.Palette | Buffers.Supports |
                Buffers.Solutions | Buffers.Status,
                Textures.CellColor | Textures.CellMeta | Textures.Output, 8, 8),
            // Separate store keeps SolveTones within D3D11's eight UAV limit.
            new KernelDefinition("StoreHistory", Buffers.Groups | Buffers.Histogram |
                Buffers.Status | Buffers.Palette | Buffers.Solutions, Textures.None, 32, 1)
        };

        private static readonly int SourceColorId = Shader.PropertyToID("_ToneSourceColor");
        private static readonly int SourceMetaId = Shader.PropertyToID("_ToneSourceMeta");
        private static readonly int SourceLightingId = Shader.PropertyToID("_ToneSourceLighting");
        private static readonly int RelativeLightnessId = Shader.PropertyToID("_ToneRelativeLightness");
        private static readonly int LightnessRelativeErrorId = Shader.PropertyToID("_ToneLightnessRelativeError");
        private static readonly int LightnessBlackFloorId = Shader.PropertyToID("_ToneLightnessBlackFloor");
        private static readonly int HairLightingEnabledId = Shader.PropertyToID("_ToneHairLightingEnabled");
        private static readonly int HairRelativeErrorId = Shader.PropertyToID("_ToneHairRelativeError");
        private static readonly int HairIlluminationFloorId = Shader.PropertyToID("_ToneHairIlluminationFloor");
        private static readonly int SkinLightingEnabledId = Shader.PropertyToID("_ToneSkinLightingEnabled");
        private static readonly int SkinRelativeErrorId = Shader.PropertyToID("_ToneSkinRelativeError");
        private static readonly int SkinIlluminationFloorId = Shader.PropertyToID("_ToneSkinIlluminationFloor");
        private static readonly int CellColorId = Shader.PropertyToID("_ToneCellColor");
        private static readonly int CellMetaId = Shader.PropertyToID("_ToneCellMeta");
        private static readonly int OutputId = Shader.PropertyToID("_ToneOutput");
        private static readonly int PreviousHistoryId = Shader.PropertyToID("_TonePreviousHistory");
        private static readonly int NextHistoryId = Shader.PropertyToID("_ToneNextHistory");
        private static readonly int HistoryValidId = Shader.PropertyToID("_ToneHistoryValid");
        private static readonly int TemporalStabilityId = Shader.PropertyToID("_ToneTemporalStability");
        private static readonly int ShrinkMarginId = Shader.PropertyToID("_ToneShrinkMargin");
        private static readonly int PreviousRegionsId = Shader.PropertyToID("_TonePreviousRegions");
        private static readonly int NextRegionsId = Shader.PropertyToID("_ToneNextRegions");
        private static readonly int DisplayRegionsId = Shader.PropertyToID("_ToneDisplayRegions");
        private static readonly int RegionTransitionsId = Shader.PropertyToID("_ToneRegionTransitions");
        private static readonly int RegionHistoryValidId = Shader.PropertyToID("_ToneRegionHistoryValid");
        private static readonly int RegionDeltaTimeId = Shader.PropertyToID("_ToneRegionDeltaTime");
        private static readonly int RegionSecondsId = Shader.PropertyToID("_ToneRegionSeconds");
        private static readonly int GroupsId = Shader.PropertyToID("_ToneGroups");
        private static readonly int HistogramId = Shader.PropertyToID("_ToneHistogram");
        private static readonly int TilesId = Shader.PropertyToID("_ToneTiles");
        private static readonly int TileHistogramId = Shader.PropertyToID("_ToneTileHistogram");
        private static readonly int SupportsId = Shader.PropertyToID("_ToneSupports");
        private static readonly int HighlightHistogramId = Shader.PropertyToID("_ToneHighlightHistogram");
        private static readonly int StatusId = Shader.PropertyToID("_ToneStatus");
        private static readonly int PaletteId = Shader.PropertyToID("_TonePalette");
        private static readonly int SolutionsId = Shader.PropertyToID("_ToneSolutions");
        private static readonly int WidthId = Shader.PropertyToID("_ToneWidth");
        private static readonly int HeightId = Shader.PropertyToID("_ToneHeight");
        private static readonly int SubjectId = Shader.PropertyToID("_ToneSubjectId");
        private static readonly int ErrorId = Shader.PropertyToID("_ToneError");
        private static readonly int ChromaErrorId = Shader.PropertyToID("_ToneChromaError");
        private static readonly int ContrastRetentionId = Shader.PropertyToID("_ToneContrastRetention");
        private static readonly int MinimumContrastId = Shader.PropertyToID("_ToneMinimumContrast");
        private static readonly int HighlightMinimumContrastId =
            Shader.PropertyToID("_ToneHighlightMinimumContrast");

        private ComputeShader cachedShader;
        private readonly int[] kernels = new int[KernelDefinitions.Length];
        private readonly ProfilingSampler[] samplers = new ProfilingSampler[KernelDefinitions.Length];
        private static int nextProfilingInstance;
        private bool profilingEnabled;
        private readonly Dictionary<Camera, HistoryState> histories = new Dictionary<Camera, HistoryState>();
        private readonly List<Camera> expiredCameras = new List<Camera>();
        private GraphicsBuffer emptyHistory;
        private GraphicsBuffer emptyRegions;

        public void Dispose()
        {
            SetProfilingEnabled(false);
            foreach (HistoryState history in histories.Values) history.Dispose();
            histories.Clear();
            emptyHistory?.Dispose();
            emptyHistory = null;
            emptyRegions?.Dispose();
            emptyRegions = null;
        }

        public void ResetHistory(Camera camera = null)
        {
            if (camera != null)
            {
                if (histories.TryGetValue(camera, out HistoryState state)) state.Invalidate();
                return;
            }
            foreach (HistoryState state in histories.Values) state.Invalidate();
        }

        public CharacterAdaptiveTonePass()
        {
            // Named Unity recorders can be shared. Give each helper instance a
            // separate identity so another camera/feature cannot toggle ours.
            int identity = System.Threading.Interlocked.Increment(ref nextProfilingInstance);
            for (int index = 0; index < samplers.Length; index++)
                samplers[index] = new ProfilingSampler(
                    KernelDefinitions[index].passName + " #" + identity);
        }

        public void SetProfilingEnabled(bool enabled)
        {
            if (profilingEnabled == enabled)
                return;
            profilingEnabled = enabled;
            foreach (ProfilingSampler sampler in samplers)
                sampler.enableRecording = enabled;
        }

        public ProfilingCost LastCost => new ProfilingCost(profilingEnabled,
            SumRecordedCost(0), SumRecordedCost(1), SumRecordedCost(2));

        private float? SumRecordedCost(int metric)
        {
            if (!profilingEnabled)
                return null;
            float total = 0f;
            int expectedCount = -1;
            foreach (ProfilingSampler sampler in samplers)
            {
                int count = metric == 0 ? sampler.cpuSampleCount :
                    metric == 1 ? sampler.gpuSampleCount : sampler.inlineCpuSampleCount;
                float milliseconds = metric == 0 ? sampler.cpuElapsedTime :
                    metric == 1 ? sampler.gpuElapsedTime : sampler.inlineCpuElapsedTime;
                if (count <= 0 || (expectedCount >= 0 && count != expectedCount) ||
                    float.IsNaN(milliseconds) || float.IsInfinity(milliseconds) || milliseconds <= 0f)
                    return null;
                expectedCount = count;
                total += milliseconds;
            }
            return total;
        }

        /// <summary>
        /// May be called before allocating/rendering dense native input. An enabled
        /// experiment with invalid configuration is an error, not a silent bypass.
        /// </summary>
        public void ValidateConfiguration(ComputeShader computeShader, int subjectId,
            int width, int height, Settings settings)
        {
            if (settings == null)
                throw new ArgumentNullException(nameof(settings));
            if (!settings.enabled)
                return;
            if (computeShader == null)
                throw new InvalidOperationException("Adaptive tone experiment needs its ComputeShader reference.");
            if (!SystemInfo.supportsComputeShaders)
                throw new NotSupportedException("Adaptive tone experiment requires compute shader support.");
            if (!SystemInfo.IsFormatSupported(ColorFormat,
                    GraphicsFormatUsage.Sample | GraphicsFormatUsage.LoadStore))
                throw new NotSupportedException("Adaptive tone experiment requires RGBA16F compute texture access.");
            if (subjectId < 1 || subjectId > ushort.MaxValue)
                throw new ArgumentOutOfRangeException(nameof(subjectId), "Exactly one active subject ID is required.");
            if (width < 1 || height < 1 || width > SystemInfo.maxTextureSize ||
                height > SystemInfo.maxTextureSize || (long)width * height > MaximumSourcePixels)
                throw new ArgumentOutOfRangeException(nameof(width),
                    "Adaptive tone source must fit the 4,194,304-pixel representative-index bound.");
            ValidateUnitSetting(settings.toneError, nameof(settings.toneError));
            if (settings.relativeLightness)
            {
                ValidateUnitSetting(settings.lightnessRelativeError, nameof(settings.lightnessRelativeError));
                ValidateUnitSetting(settings.lightnessBlackFloor, nameof(settings.lightnessBlackFloor));
            }
            ValidateUnitSetting(settings.chromaError, nameof(settings.chromaError));
            if (settings.chromaError < 0.005f)
                throw new ArgumentOutOfRangeException(nameof(settings.chromaError),
                    "The GPU prototype supports chromaError in [0.005, 1].");
            ValidateUnitSetting(settings.contrastRetention, nameof(settings.contrastRetention));
            ValidateUnitSetting(settings.minimumContrast, nameof(settings.minimumContrast));
            ValidateUnitSetting(settings.highlightMinimumContrast, nameof(settings.highlightMinimumContrast));
            if (float.IsNaN(settings.shrinkMargin) || settings.shrinkMargin < 0f || settings.shrinkMargin > 0.5f)
                throw new ArgumentOutOfRangeException(nameof(settings.shrinkMargin));
            if (settings.regionTransitions && (float.IsNaN(settings.regionTransitionSeconds) ||
                settings.regionTransitionSeconds < 0.02f || settings.regionTransitionSeconds > 2f))
                throw new ArgumentOutOfRangeException(nameof(settings.regionTransitionSeconds));
            if ((settings.hairLighting || settings.skinLighting || settings.regionTransitions) &&
                SystemInfo.supportedRenderTargetCount < 3)
                throw new NotSupportedException("Incident illumination analysis requires three simultaneous render targets.");
            if (settings.hairLighting)
            {
                ValidateUnitSetting(settings.hairRelativeError, nameof(settings.hairRelativeError));
                ValidateUnitSetting(settings.hairIlluminationFloor, nameof(settings.hairIlluminationFloor));
            }
            if (settings.skinLighting)
            {
                ValidateUnitSetting(settings.skinRelativeError, nameof(settings.skinRelativeError));
                ValidateUnitSetting(settings.skinIlluminationFloor, nameof(settings.skinIlluminationFloor));
            }

            if (cachedShader == computeShader)
                return;
            // Clear first: a failed replacement must not leave partially changed
            // kernel indices associated with the previously cached shader.
            cachedShader = null;
            for (int index = 0; index < KernelDefinitions.Length; index++)
            {
                KernelDefinition definition = KernelDefinitions[index];
                if (!computeShader.HasKernel(definition.name))
                    throw new InvalidOperationException("Adaptive tone kernel is missing: " + definition.name);
                int kernel = computeShader.FindKernel(definition.name);
                computeShader.GetKernelThreadGroupSizes(kernel, out uint x, out uint y, out uint z);
                if (x != definition.threadsX || y != definition.threadsY || z != 1)
                    throw new InvalidOperationException("Adaptive tone kernel thread dimensions changed: " + definition.name);
                kernels[index] = kernel;
            }
            cachedShader = computeShader;
        }

        public TextureHandle Record(RenderGraph renderGraph,
            TextureHandle sourceNativeColor, TextureHandle sourceNativeMeta,
            TextureHandle cellColor, TextureHandle cellMeta, ComputeShader computeShader,
            int subjectId, int width, int height, Settings settings)
        {
            return Record(renderGraph, sourceNativeColor, sourceNativeMeta, cellColor, cellMeta,
                computeShader, subjectId, width, height, settings, out _);
        }

        /// <summary>
        /// validationStatus is a borrowed, current-graph handle, with one uint per
        /// group and the global uint at GlobalStatusIndex. It is not a completion
        /// signal. A separate diagnostic pass may read it back for a requested test;
        /// this runtime recorder does not claim success from dispatch alone.
        /// </summary>
        public TextureHandle Record(RenderGraph renderGraph,
            TextureHandle sourceNativeColor, TextureHandle sourceNativeMeta,
            TextureHandle cellColor, TextureHandle cellMeta, ComputeShader computeShader,
            int subjectId, int width, int height, Settings settings, out BufferHandle validationStatus,
            TextureHandle sourceNativeLighting = default)
        {
            return Record(renderGraph, sourceNativeColor, sourceNativeMeta, cellColor, cellMeta,
                computeShader, subjectId, width, height, settings, out validationStatus,
                out _, sourceNativeLighting);
        }

        /// <summary>
        /// captureBuffers contains borrowed handles to this invocation's actual
        /// dispatch buffers, including imported region state. A caller may read
        /// them in a dependent diagnostic pass in the same graph; the handles
        /// must never be cached across frames. Legacy stateless fixtures must
        /// explicitly disable settings.regionTransitions.
        /// </summary>
        public TextureHandle Record(RenderGraph renderGraph,
            TextureHandle sourceNativeColor, TextureHandle sourceNativeMeta,
            TextureHandle cellColor, TextureHandle cellMeta, ComputeShader computeShader,
            int subjectId, int width, int height, Settings settings, out BufferHandle validationStatus,
            out BufferSet captureBuffers, TextureHandle sourceNativeLighting = default,
            Camera historyCamera = null, UnityEngine.Object historySubject = null, int cellSize = 0)
        {
            validationStatus = BufferHandle.nullHandle;
            captureBuffers = default;
            if (renderGraph == null)
                throw new ArgumentNullException(nameof(renderGraph));
            ValidateConfiguration(computeShader, subjectId, width, height, settings);
            if (!settings.enabled)
                return cellColor;

            ValidateTexture(renderGraph, sourceNativeColor, width, height, ColorFormat, nameof(sourceNativeColor));
            ValidateTexture(renderGraph, sourceNativeMeta, width, height, MetaFormat, nameof(sourceNativeMeta));
            if (settings.hairLighting || settings.skinLighting || settings.regionTransitions)
            {
                ValidateTexture(renderGraph, sourceNativeLighting, width, height, ColorFormat, nameof(sourceNativeLighting));
            }
            TextureDesc outputDescriptor = ValidateTexture(
                renderGraph, cellColor, width, height, ColorFormat, nameof(cellColor));
            ValidateTexture(renderGraph, cellMeta, width, height, MetaFormat, nameof(cellMeta));

            outputDescriptor.name = "_CharacterAdaptiveToneCellColor";
            outputDescriptor.enableRandomWrite = true;
            outputDescriptor.msaaSamples = MSAASamples.None;
            outputDescriptor.bindTextureMS = false;
            outputDescriptor.clearBuffer = false;
            outputDescriptor.filterMode = FilterMode.Point;
            outputDescriptor.wrapMode = TextureWrapMode.Clamp;
            TextureHandle output = renderGraph.CreateTexture(outputDescriptor);
            BufferSet buffers = CreateBuffers(renderGraph);
            captureBuffers = buffers;
            validationStatus = buffers.status;
            ToneValues values = new ToneValues(settings);
            HistoryState history = PrepareHistory(historyCamera, historySubject, subjectId,
                cellSize, width, height, computeShader, values);
            // Stateless fixture callers cannot consume or overwrite gameplay history.
            if (emptyHistory == null)
            {
                emptyHistory = NewHistoryBuffer("Character Tone Empty History");
                emptyHistory.SetData(new Vector4[MaximumGroups * HistoryRowsPerGroup]);
            }
            BufferHandle previousHistory = renderGraph.ImportBuffer(history != null ? history.Previous : emptyHistory);
            BufferHandle nextHistory = history != null ? renderGraph.ImportBuffer(history.Next) :
                CreateBuffer(renderGraph, "Character Tone Stateless History", MaximumGroups * HistoryRowsPerGroup, 16);
            if (emptyRegions == null)
            {
                emptyRegions = NewRegionBuffer("Character Tone Empty Regions");
                emptyRegions.SetData(new Vector4[MaximumGroups * RegionRowsPerGroup]);
            }
            bool persistentRegions = history != null && values.regionTransitions;
            BufferHandle previousRegions = renderGraph.ImportBuffer(
                persistentRegions ? history.PreviousRegions : emptyRegions);
            BufferHandle nextRegions = persistentRegions ? renderGraph.ImportBuffer(history.NextRegions) :
                CreateBuffer(renderGraph, "Character Tone Stateless Regions", MaximumGroups * RegionRowsPerGroup, 16);
            buffers.previousRegions = previousRegions;
            buffers.nextRegions = nextRegions;
            captureBuffers = buffers;

            for (int index = 0; index < KernelDefinitions.Length; index++)
            {
                KernelDefinition definition = KernelDefinitions[index];
                using IComputeRenderGraphBuilder builder = renderGraph.AddComputePass<PassData>(
                    definition.passName, out PassData data, samplers[index]);
                data.shader = computeShader;
                data.kernel = kernels[index];
                data.bufferMask = definition.buffers;
                data.textureMask = definition.textures;
                // All analysis/resolve kernels reference this resource. With the
                // switch off the shader branch is inert, but D3D11 still needs a
                // declared/bound SRV. Reuse the existing source for old callers.
                if (index != 0 && definition.name != "StoreHistory" && definition.name != "UpdateRegions")
                    data.textureMask |= Textures.SourceLighting;
                if (definition.name == "Resolve") data.textureMask |= Textures.SourceMeta;
                data.buffers = buffers;
                data.sourceColor = sourceNativeColor;
                data.sourceMeta = sourceNativeMeta;
                data.sourceLighting = settings.hairLighting || settings.skinLighting || settings.regionTransitions ?
                    sourceNativeLighting : sourceNativeColor;
                data.cellColor = cellColor;
                data.cellMeta = cellMeta;
                data.output = output;
                data.width = width;
                data.height = height;
                data.subjectId = subjectId;
                data.values = values;
                data.solveHistory = definition.name == "SolveTones";
                data.storeHistory = definition.name == "StoreHistory";
                data.previousHistory = previousHistory;
                data.nextHistory = nextHistory;
                data.historyValid = history != null && history.readValid;
                data.history = history;
                data.frame = Time.frameCount;
                data.historyWriteIndex = history != null ? history.writeIndex : 0;
                data.updateRegions = definition.name == "UpdateRegions";
                data.displayRegions = definition.name == "Resolve";
                data.previousRegions = previousRegions;
                data.nextRegions = nextRegions;
                data.regionHistoryValid = persistentRegions && history.regionReadValid;
                data.regionDeltaTime = persistentRegions ? history.regionDeltaTime : 0f;
                data.regionWriteIndex = persistentRegions ? history.regionWriteIndex : 0;
                data.regionTime = persistentRegions ? history.regionPreparedTime : 0.0;
                data.regionUnscaledTime = persistentRegions ? history.regionPreparedUnscaledTime : 0.0;
                data.groupsX = index == 0 ? (ClearElements + 63) / 64 :
                    definition.threadsX == 32 ? MaximumGroups : (width + 7) / 8;
                data.groupsY = definition.threadsY == 8 ? (height + 7) / 8 : 1;
                DeclareResources(builder, data, index == 0, definition.name == "SolveTones");
                if (data.solveHistory) builder.UseBuffer(previousHistory, AccessFlags.Read);
                if (data.storeHistory)
                {
                    builder.UseBuffer(nextHistory, AccessFlags.WriteAll);
                    if (history != null) builder.AllowPassCulling(false);
                }
                if (data.updateRegions)
                {
                    builder.UseBuffer(previousRegions, AccessFlags.Read);
                    builder.UseBuffer(nextRegions, AccessFlags.WriteAll);
                    if (persistentRegions) builder.AllowPassCulling(false);
                }
                if (data.displayRegions) builder.UseBuffer(nextRegions, AccessFlags.Read);
                builder.SetRenderFunc(static (PassData passData, ComputeGraphContext context) =>
                    Execute(passData, context.cmd));
            }
            return output;
        }

        private static void ValidateUnitSetting(float value, string name)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value <= 0f || value > 1f)
                throw new ArgumentOutOfRangeException(name, "Adaptive tone controls must be finite in (0, 1].");
        }

        private static TextureDesc ValidateTexture(RenderGraph graph, TextureHandle texture,
            int width, int height, GraphicsFormat format, string name)
        {
            if (!texture.IsValid())
                throw new ArgumentException("Adaptive tone input texture is invalid.", name);
            TextureDesc descriptor = texture.GetDescriptor(graph);
            if (descriptor.width != width || descriptor.height != height ||
                descriptor.dimension != TextureDimension.Tex2D || descriptor.slices != 1 ||
                descriptor.msaaSamples != MSAASamples.None || descriptor.format != format)
                throw new ArgumentException(
                    "Adaptive tone inputs must be equal-sized non-MSAA 2D textures with the agreed color/meta format.", name);
            return descriptor;
        }

        private static BufferSet CreateBuffers(RenderGraph graph)
        {
            return new BufferSet
            {
                groups = CreateBuffer(graph, "_ToneGroups", MaximumGroups * 8, sizeof(uint)),
                histogram = CreateBuffer(graph, "_ToneHistogram", MaximumGroups * HistogramBins * 6, sizeof(uint)),
                tiles = CreateBuffer(graph, "_ToneTiles", MaximumGroups * SpatialTiles * 3, sizeof(uint)),
                tileHistogram = CreateBuffer(graph, "_ToneTileHistogram",
                    MaximumGroups * SpatialTiles * HistogramBins, sizeof(uint)),
                supports = CreateBuffer(graph, "_ToneSupports", MaximumGroups * 2, sizeof(uint)),
                highlightHistogram = CreateBuffer(graph, "_ToneHighlightHistogram",
                    MaximumGroups * HistogramBins * 5, sizeof(uint)),
                status = CreateBuffer(graph, "_ToneStatus", StatusCount, sizeof(uint)),
                palette = CreateBuffer(graph, "_TonePalette", MaximumGroups * HistogramBins, sizeof(float) * 4),
                solutions = CreateBuffer(graph, "_ToneSolutions", MaximumGroups * 3, sizeof(float) * 4)
            };
        }

        private static BufferHandle CreateBuffer(RenderGraph graph, string name, int count, int stride)
        {
            return graph.CreateBuffer(new BufferDesc(count, stride, GraphicsBuffer.Target.Structured) { name = name });
        }

        private static void DeclareResources(IComputeRenderGraphBuilder builder, PassData data,
            bool clear, bool initializePalette)
        {
            AccessFlags access = clear ? AccessFlags.Write : AccessFlags.ReadWrite;
            AccessFlags paletteAccess = initializePalette ? AccessFlags.Write : access;
            if ((data.bufferMask & Buffers.Groups) != 0) builder.UseBuffer(data.buffers.groups, access);
            if ((data.bufferMask & Buffers.Histogram) != 0) builder.UseBuffer(data.buffers.histogram, access);
            if ((data.bufferMask & Buffers.Tiles) != 0) builder.UseBuffer(data.buffers.tiles, access);
            if ((data.bufferMask & Buffers.TileHistogram) != 0) builder.UseBuffer(data.buffers.tileHistogram, access);
            if ((data.bufferMask & Buffers.Supports) != 0) builder.UseBuffer(data.buffers.supports, access);
            if ((data.bufferMask & Buffers.HighlightHistogram) != 0) builder.UseBuffer(data.buffers.highlightHistogram, access);
            if ((data.bufferMask & Buffers.Status) != 0) builder.UseBuffer(data.buffers.status, access);
            if ((data.bufferMask & Buffers.Palette) != 0) builder.UseBuffer(data.buffers.palette, paletteAccess);
            if ((data.bufferMask & Buffers.Solutions) != 0) builder.UseBuffer(data.buffers.solutions, paletteAccess);
            if ((data.textureMask & Textures.SourceColor) != 0) builder.UseTexture(data.sourceColor, AccessFlags.Read);
            if ((data.textureMask & Textures.SourceMeta) != 0) builder.UseTexture(data.sourceMeta, AccessFlags.Read);
            if ((data.textureMask & Textures.SourceLighting) != 0) builder.UseTexture(data.sourceLighting, AccessFlags.Read);
            if ((data.textureMask & Textures.CellColor) != 0) builder.UseTexture(data.cellColor, AccessFlags.Read);
            if ((data.textureMask & Textures.CellMeta) != 0) builder.UseTexture(data.cellMeta, AccessFlags.Read);
            if ((data.textureMask & Textures.Output) != 0) builder.UseTexture(data.output, AccessFlags.WriteAll);
        }

        private static void Execute(PassData data, ComputeCommandBuffer cmd)
        {
            ComputeShader shader = data.shader;
            int kernel = data.kernel;
            cmd.SetComputeIntParam(shader, WidthId, data.width);
            cmd.SetComputeIntParam(shader, HeightId, data.height);
            cmd.SetComputeIntParam(shader, SubjectId, data.subjectId);
            cmd.SetComputeFloatParam(shader, ErrorId, data.values.error);
            cmd.SetComputeIntParam(shader, RelativeLightnessId, data.values.relativeLightness ? 1 : 0);
            cmd.SetComputeFloatParam(shader, LightnessRelativeErrorId, data.values.lightnessRelativeError);
            cmd.SetComputeFloatParam(shader, LightnessBlackFloorId, data.values.lightnessBlackFloor);
            cmd.SetComputeFloatParam(shader, ChromaErrorId, data.values.chromaError);
            cmd.SetComputeFloatParam(shader, ContrastRetentionId, data.values.contrastRetention);
            cmd.SetComputeFloatParam(shader, MinimumContrastId, data.values.minimumContrast);
            cmd.SetComputeFloatParam(shader, HighlightMinimumContrastId, data.values.highlightMinimumContrast);
            cmd.SetComputeIntParam(shader, HairLightingEnabledId, data.values.hairLighting ? 1 : 0);
            cmd.SetComputeFloatParam(shader, HairRelativeErrorId, data.values.hairRelativeError);
            cmd.SetComputeFloatParam(shader, HairIlluminationFloorId, data.values.hairIlluminationFloor);
            cmd.SetComputeIntParam(shader, SkinLightingEnabledId, data.values.skinLighting ? 1 : 0);
            cmd.SetComputeFloatParam(shader, SkinRelativeErrorId, data.values.skinRelativeError);
            cmd.SetComputeFloatParam(shader, SkinIlluminationFloorId, data.values.skinIlluminationFloor);
            // Contour transitions own display continuity. The existing solver
            // supplies today's target partition without a second history policy.
            cmd.SetComputeIntParam(shader, TemporalStabilityId,
                data.values.temporalStability && !data.values.regionTransitions ? 1 : 0);
            cmd.SetComputeIntParam(shader, HistoryValidId, data.historyValid ? 1 : 0);
            cmd.SetComputeFloatParam(shader, ShrinkMarginId, data.values.shrinkMargin);
            cmd.SetComputeIntParam(shader, RegionTransitionsId, data.values.regionTransitions ? 1 : 0);
            cmd.SetComputeIntParam(shader, RegionHistoryValidId, data.regionHistoryValid ? 1 : 0);
            cmd.SetComputeFloatParam(shader, RegionDeltaTimeId, data.regionDeltaTime);
            cmd.SetComputeFloatParam(shader, RegionSecondsId, data.values.regionTransitionSeconds);
            if (data.solveHistory) cmd.SetComputeBufferParam(shader, kernel, PreviousHistoryId, data.previousHistory);
            if (data.storeHistory) cmd.SetComputeBufferParam(shader, kernel, NextHistoryId, data.nextHistory);
            if (data.updateRegions)
            {
                cmd.SetComputeBufferParam(shader, kernel, PreviousRegionsId, data.previousRegions);
                cmd.SetComputeBufferParam(shader, kernel, NextRegionsId, data.nextRegions);
            }
            if (data.displayRegions) cmd.SetComputeBufferParam(shader, kernel, DisplayRegionsId, data.nextRegions);
            if ((data.bufferMask & Buffers.Groups) != 0) cmd.SetComputeBufferParam(shader, kernel, GroupsId, data.buffers.groups);
            if ((data.bufferMask & Buffers.Histogram) != 0) cmd.SetComputeBufferParam(shader, kernel, HistogramId, data.buffers.histogram);
            if ((data.bufferMask & Buffers.Tiles) != 0) cmd.SetComputeBufferParam(shader, kernel, TilesId, data.buffers.tiles);
            if ((data.bufferMask & Buffers.TileHistogram) != 0) cmd.SetComputeBufferParam(shader, kernel, TileHistogramId, data.buffers.tileHistogram);
            if ((data.bufferMask & Buffers.Supports) != 0) cmd.SetComputeBufferParam(shader, kernel, SupportsId, data.buffers.supports);
            if ((data.bufferMask & Buffers.HighlightHistogram) != 0) cmd.SetComputeBufferParam(shader, kernel, HighlightHistogramId, data.buffers.highlightHistogram);
            if ((data.bufferMask & Buffers.Status) != 0) cmd.SetComputeBufferParam(shader, kernel, StatusId, data.buffers.status);
            if ((data.bufferMask & Buffers.Palette) != 0) cmd.SetComputeBufferParam(shader, kernel, PaletteId, data.buffers.palette);
            if ((data.bufferMask & Buffers.Solutions) != 0) cmd.SetComputeBufferParam(shader, kernel, SolutionsId, data.buffers.solutions);
            if ((data.textureMask & Textures.SourceColor) != 0) cmd.SetComputeTextureParam(shader, kernel, SourceColorId, data.sourceColor);
            if ((data.textureMask & Textures.SourceMeta) != 0) cmd.SetComputeTextureParam(shader, kernel, SourceMetaId, data.sourceMeta);
            if ((data.textureMask & Textures.SourceLighting) != 0) cmd.SetComputeTextureParam(shader, kernel, SourceLightingId, data.sourceLighting);
            if ((data.textureMask & Textures.CellColor) != 0) cmd.SetComputeTextureParam(shader, kernel, CellColorId, data.cellColor);
            if ((data.textureMask & Textures.CellMeta) != 0) cmd.SetComputeTextureParam(shader, kernel, CellMetaId, data.cellMeta);
            if ((data.textureMask & Textures.Output) != 0) cmd.SetComputeTextureParam(shader, kernel, OutputId, data.output);
            cmd.DispatchCompute(shader, kernel, data.groupsX, data.groupsY, 1);
            if (data.storeHistory && data.history != null)
            {
                data.history.lastWrittenFrame = data.frame;
                data.history.lastWrittenIndex = data.historyWriteIndex;
            }
            if (data.updateRegions && data.history != null && data.values.regionTransitions)
            {
                data.history.regionLastWrittenFrame = data.frame;
                data.history.regionLastWrittenIndex = data.regionWriteIndex;
                data.history.regionLastWrittenTime = data.regionTime;
                data.history.regionLastWrittenUnscaledTime = data.regionUnscaledTime;
            }
        }

        /// <summary>Borrowed current-graph buffers, not persistent GPU state.</summary>
        public struct BufferSet
        {
            public BufferHandle groups, histogram, tiles, tileHistogram, supports;
            public BufferHandle highlightHistogram, status, palette, solutions;
            public BufferHandle previousRegions, nextRegions;
        }

        private readonly struct ToneValues
        {
            public readonly float error, chromaError, contrastRetention, minimumContrast, highlightMinimumContrast;
            public readonly bool relativeLightness;
            public readonly float lightnessRelativeError, lightnessBlackFloor;
            public readonly bool hairLighting;
            public readonly float hairRelativeError, hairIlluminationFloor;
            public readonly bool skinLighting;
            public readonly float skinRelativeError, skinIlluminationFloor;
            public readonly bool temporalStability;
            public readonly float shrinkMargin;
            public readonly bool regionTransitions;
            public readonly float regionTransitionSeconds;

            public ToneValues(Settings settings)
            {
                error = settings.toneError;
                relativeLightness = settings.relativeLightness;
                lightnessRelativeError = settings.lightnessRelativeError;
                lightnessBlackFloor = settings.lightnessBlackFloor;
                chromaError = settings.chromaError;
                contrastRetention = settings.contrastRetention;
                minimumContrast = settings.minimumContrast;
                highlightMinimumContrast = settings.highlightMinimumContrast;
                hairLighting = settings.hairLighting;
                hairRelativeError = settings.hairRelativeError;
                hairIlluminationFloor = settings.hairIlluminationFloor;
                skinLighting = settings.skinLighting;
                skinRelativeError = settings.skinRelativeError;
                skinIlluminationFloor = settings.skinIlluminationFloor;
                temporalStability = settings.temporalStability;
                shrinkMargin = settings.shrinkMargin;
                regionTransitions = settings.regionTransitions;
                regionTransitionSeconds = settings.regionTransitionSeconds;
            }

            public bool SameConfiguration(ToneValues other) =>
                error == other.error && chromaError == other.chromaError &&
                relativeLightness == other.relativeLightness &&
                lightnessRelativeError == other.lightnessRelativeError && lightnessBlackFloor == other.lightnessBlackFloor &&
                contrastRetention == other.contrastRetention && minimumContrast == other.minimumContrast &&
                highlightMinimumContrast == other.highlightMinimumContrast &&
                hairLighting == other.hairLighting && hairRelativeError == other.hairRelativeError &&
                hairIlluminationFloor == other.hairIlluminationFloor && skinLighting == other.skinLighting &&
                skinRelativeError == other.skinRelativeError && skinIlluminationFloor == other.skinIlluminationFloor &&
                temporalStability == other.temporalStability && shrinkMargin == other.shrinkMargin &&
                regionTransitions == other.regionTransitions && regionTransitionSeconds == other.regionTransitionSeconds;
        }

        private static GraphicsBuffer NewHistoryBuffer(string name) => new GraphicsBuffer(
            GraphicsBuffer.Target.Structured, MaximumGroups * HistoryRowsPerGroup, 16) { name = name };

        private static GraphicsBuffer NewRegionBuffer(string name) => new GraphicsBuffer(
            GraphicsBuffer.Target.Structured, MaximumGroups * RegionRowsPerGroup, 16) { name = name };

        private HistoryState PrepareHistory(Camera camera, UnityEngine.Object subject, int subjectId,
            int cellSize, int width, int height, ComputeShader shader, ToneValues values)
        {
            if (camera == null || subject == null || (!values.temporalStability && !values.regionTransitions))
            {
                if (camera != null) ResetHistory(camera);
                return null;
            }
            expiredCameras.Clear();
            foreach (var entry in histories)
                if (entry.Key == null) expiredCameras.Add(entry.Key);
            foreach (Camera expired in expiredCameras)
            {
                histories[expired].Dispose();
                histories.Remove(expired);
            }
            if (!histories.TryGetValue(camera, out HistoryState state))
            {
                state = new HistoryState();
                histories.Add(camera, state);
            }
            Matrix4x4 projection = camera.nonJitteredProjectionMatrix;
            Vector3 position = camera.transform.position;
            Quaternion rotation = camera.transform.rotation;
            // Contours are not stored in screen pixels. A zoom/resolution change
            // resets the legacy partition cache only, not the region lifetime.
            float cutDistance = camera.orthographic ? Mathf.Max(1f, camera.orthographicSize) * 2f : 10f;
            bool changed = state.subject != subject || state.subjectId != subjectId ||
                state.shader != shader || state.playing != Application.isPlaying ||
                !state.values.SameConfiguration(values) ||
                Vector3.SqrMagnitude(state.position - position) > cutDistance * cutDistance ||
                Quaternion.Angle(state.rotation, rotation) > 60f;
            if (changed) state.Invalidate();
            else if (state.width != width || state.height != height || state.cellSize != cellSize ||
                state.projection != projection) state.InvalidateHistory();
            state.subject = subject;
            state.subjectId = subjectId;
            state.width = width;
            state.height = height;
            state.cellSize = cellSize;
            state.shader = shader;
            state.playing = Application.isPlaying;
            state.values = values;
            state.projection = projection;
            state.position = position;
            state.rotation = rotation;
            if (state.preparedFrame != Time.frameCount)
            {
                state.preparedFrame = Time.frameCount;
                state.readValid = state.lastWrittenFrame == Time.frameCount - 1;
                state.writeIndex = 1 - state.lastWrittenIndex;
            }
            if (values.regionTransitions)
            {
                state.EnsureRegions();
                if (state.regionPreparedFrame != Time.frameCount)
                {
                    state.regionPreparedFrame = Time.frameCount;
                    // Game time stops during pause. Unscaled time is used only
                    // to distinguish a short render gap from a stale camera.
                    double unscaledTime = Application.isPlaying ?
                        Time.unscaledTimeAsDouble : Time.realtimeSinceStartupAsDouble;
                    double gameTime = Application.isPlaying ? Time.timeAsDouble : unscaledTime;
                    double renderGap = unscaledTime - state.regionLastWrittenUnscaledTime;
                    state.regionReadValid = state.regionLastWrittenFrame >= 0 && renderGap >= 0.0 &&
                        renderGap <= MaximumRegionRenderGapSeconds && gameTime >= state.regionLastWrittenTime;
                    state.regionDeltaTime = state.regionReadValid ?
                        (float)(gameTime - state.regionLastWrittenTime) : 0f;
                    state.regionPreparedTime = gameTime;
                    state.regionPreparedUnscaledTime = unscaledTime;
                    state.regionWriteIndex = 1 - state.regionLastWrittenIndex;
                }
                // Further renders in the same frame reuse these exact reads,
                // writes and elapsed time; they cannot advance a transition twice.
            }
            return state;
        }

        private sealed class HistoryState : IDisposable
        {
            private readonly GraphicsBuffer[] buffers = {
                NewHistoryBuffer("Character Tone History A"), NewHistoryBuffer("Character Tone History B") };
            private GraphicsBuffer[] regionBuffers;
            public int subjectId, width, height, cellSize;
            public int preparedFrame = -1, lastWrittenFrame = -2, lastWrittenIndex, writeIndex;
            public int regionPreparedFrame = -1, regionLastWrittenFrame = -2;
            public int regionLastWrittenIndex, regionWriteIndex;
            public double regionLastWrittenTime, regionLastWrittenUnscaledTime;
            public double regionPreparedTime, regionPreparedUnscaledTime;
            public float regionDeltaTime;
            public bool regionReadValid;
            public bool readValid, playing;
            public UnityEngine.Object subject;
            public ComputeShader shader;
            public ToneValues values;
            public Matrix4x4 projection;
            public Vector3 position;
            public Quaternion rotation;
            public GraphicsBuffer Previous => buffers[1 - writeIndex];
            public GraphicsBuffer Next => buffers[writeIndex];
            public GraphicsBuffer PreviousRegions => regionBuffers[1 - regionWriteIndex];
            public GraphicsBuffer NextRegions => regionBuffers[regionWriteIndex];
            public void EnsureRegions()
            {
                if (regionBuffers == null)
                    regionBuffers = new[] { NewRegionBuffer("Character Tone Regions A"),
                        NewRegionBuffer("Character Tone Regions B") };
            }
            public void InvalidateHistory() { preparedFrame = -1; lastWrittenFrame = -2; readValid = false; }
            public void Invalidate()
            {
                InvalidateHistory();
                regionPreparedFrame = -1;
                regionLastWrittenFrame = -2;
                regionReadValid = false;
                regionDeltaTime = 0f;
            }
            public void Dispose()
            {
                foreach (GraphicsBuffer buffer in buffers) buffer.Dispose();
                if (regionBuffers != null)
                {
                    foreach (GraphicsBuffer buffer in regionBuffers) buffer.Dispose();
                    regionBuffers = null;
                }
            }
        }

        private sealed class PassData
        {
            public ComputeShader shader;
            public int kernel, width, height, subjectId, groupsX, groupsY;
            public Buffers bufferMask;
            public Textures textureMask;
            public BufferSet buffers;
            public ToneValues values;
            public TextureHandle sourceColor, sourceMeta, sourceLighting, cellColor, cellMeta, output;
            public BufferHandle previousHistory, nextHistory;
            public bool solveHistory, storeHistory, historyValid;
            public BufferHandle previousRegions, nextRegions;
            public bool updateRegions, displayRegions, regionHistoryValid;
            public float regionDeltaTime;
            public double regionTime, regionUnscaledTime;
            public HistoryState history;
            public int frame, historyWriteIndex;
            public int regionWriteIndex;
        }
    }
}
