using System;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;

namespace FantasySurvival.Rendering
{
    /// <summary>
    /// Records the opt-in, single-subject GPU tone experiment between the existing
    /// cell source and composite. All GPU resources belong to this RenderGraph;
    /// this object caches only kernel indices and never reads back a frame.
    /// </summary>
    public sealed class CharacterAdaptiveTonePass
    {
        public const int MaximumSourcePixels = 4_194_304;
        public const int MaximumGroups = 160;
        public const int GlobalStatusIndex = MaximumGroups;
        public const int StatusCount = MaximumGroups + 1;

        private const int HistogramBins = 32;
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
            [Range(0.005f, 1f)] public float chromaError = 0.06f;
            [Range(0.0001f, 1f)] public float contrastRetention = 0.65f;
            [Range(0.0001f, 1f)] public float minimumContrast = 0.025f;
            [Range(0.0001f, 1f)] public float highlightMinimumContrast = 0.025f;
            [Tooltip("Hair only: partition actual incident diffuse light, retaining observed source RGB. Off preserves the previous algorithm.")]
            public bool hairLighting;
            [Range(0.0001f, 1f)] public float hairRelativeError = 0.10f;
            [Range(0.0001f, 1f)] public float hairIlluminationFloor = 0.02f;
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
            new KernelDefinition("Resolve", Buffers.Groups | Buffers.Palette | Buffers.Supports |
                Buffers.Solutions | Buffers.Status,
                Textures.CellColor | Textures.CellMeta | Textures.Output, 8, 8)
        };

        private static readonly int SourceColorId = Shader.PropertyToID("_ToneSourceColor");
        private static readonly int SourceMetaId = Shader.PropertyToID("_ToneSourceMeta");
        private static readonly int SourceLightingId = Shader.PropertyToID("_ToneSourceLighting");
        private static readonly int HairLightingEnabledId = Shader.PropertyToID("_ToneHairLightingEnabled");
        private static readonly int HairRelativeErrorId = Shader.PropertyToID("_ToneHairRelativeError");
        private static readonly int HairIlluminationFloorId = Shader.PropertyToID("_ToneHairIlluminationFloor");
        private static readonly int CellColorId = Shader.PropertyToID("_ToneCellColor");
        private static readonly int CellMetaId = Shader.PropertyToID("_ToneCellMeta");
        private static readonly int OutputId = Shader.PropertyToID("_ToneOutput");
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
            ValidateUnitSetting(settings.chromaError, nameof(settings.chromaError));
            if (settings.chromaError < 0.005f)
                throw new ArgumentOutOfRangeException(nameof(settings.chromaError),
                    "The GPU prototype supports chromaError in [0.005, 1].");
            ValidateUnitSetting(settings.contrastRetention, nameof(settings.contrastRetention));
            ValidateUnitSetting(settings.minimumContrast, nameof(settings.minimumContrast));
            ValidateUnitSetting(settings.highlightMinimumContrast, nameof(settings.highlightMinimumContrast));
            if (settings.hairLighting)
            {
                if (SystemInfo.supportedRenderTargetCount < 3)
                    throw new NotSupportedException("Hair illumination analysis requires three simultaneous render targets.");
                ValidateUnitSetting(settings.hairRelativeError, nameof(settings.hairRelativeError));
                ValidateUnitSetting(settings.hairIlluminationFloor, nameof(settings.hairIlluminationFloor));
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
            validationStatus = BufferHandle.nullHandle;
            if (renderGraph == null)
                throw new ArgumentNullException(nameof(renderGraph));
            ValidateConfiguration(computeShader, subjectId, width, height, settings);
            if (!settings.enabled)
                return cellColor;

            ValidateTexture(renderGraph, sourceNativeColor, width, height, ColorFormat, nameof(sourceNativeColor));
            ValidateTexture(renderGraph, sourceNativeMeta, width, height, MetaFormat, nameof(sourceNativeMeta));
            if (settings.hairLighting)
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
            validationStatus = buffers.status;
            ToneValues values = new ToneValues(settings);

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
                if (index != 0) data.textureMask |= Textures.SourceLighting;
                if (definition.name == "Resolve") data.textureMask |= Textures.SourceMeta;
                data.buffers = buffers;
                data.sourceColor = sourceNativeColor;
                data.sourceMeta = sourceNativeMeta;
                data.sourceLighting = settings.hairLighting ? sourceNativeLighting : sourceNativeColor;
                data.cellColor = cellColor;
                data.cellMeta = cellMeta;
                data.output = output;
                data.width = width;
                data.height = height;
                data.subjectId = subjectId;
                data.values = values;
                data.groupsX = index == 0 ? (ClearElements + 63) / 64 :
                    definition.threadsX == 32 ? MaximumGroups : (width + 7) / 8;
                data.groupsY = definition.threadsY == 8 ? (height + 7) / 8 : 1;
                DeclareResources(builder, data, index == 0, definition.name == "SolveTones");
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
            cmd.SetComputeFloatParam(shader, ChromaErrorId, data.values.chromaError);
            cmd.SetComputeFloatParam(shader, ContrastRetentionId, data.values.contrastRetention);
            cmd.SetComputeFloatParam(shader, MinimumContrastId, data.values.minimumContrast);
            cmd.SetComputeFloatParam(shader, HighlightMinimumContrastId, data.values.highlightMinimumContrast);
            cmd.SetComputeIntParam(shader, HairLightingEnabledId, data.values.hairLighting ? 1 : 0);
            cmd.SetComputeFloatParam(shader, HairRelativeErrorId, data.values.hairRelativeError);
            cmd.SetComputeFloatParam(shader, HairIlluminationFloorId, data.values.hairIlluminationFloor);
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
        }

        private struct BufferSet
        {
            public BufferHandle groups, histogram, tiles, tileHistogram, supports;
            public BufferHandle highlightHistogram, status, palette, solutions;
        }

        private readonly struct ToneValues
        {
            public readonly float error, chromaError, contrastRetention, minimumContrast, highlightMinimumContrast;
            public readonly bool hairLighting;
            public readonly float hairRelativeError, hairIlluminationFloor;

            public ToneValues(Settings settings)
            {
                error = settings.toneError;
                chromaError = settings.chromaError;
                contrastRetention = settings.contrastRetention;
                minimumContrast = settings.minimumContrast;
                highlightMinimumContrast = settings.highlightMinimumContrast;
                hairLighting = settings.hairLighting;
                hairRelativeError = settings.hairRelativeError;
                hairIlluminationFloor = settings.hairIlluminationFloor;
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
        }
    }
}
