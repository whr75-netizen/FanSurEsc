using System;
using Unity.Collections;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;

internal sealed class ClothRequestBits525 : IDisposable
{
    const int Width = 480, Height = 272, WordCapacity = Width * Height / 32;
    internal const string ResourcePath = "ClothRequestBits525";

    internal readonly struct Result
    {
        readonly NativeArray<uint> words;
        internal readonly int LeftWord, Top, RowWords, Rows;
        internal Result(NativeArray<uint> words, int leftWord, int top, int rowWords, int rows)
        {
            this.words = words;
            LeftWord = leftWord;
            Top = top;
            RowWords = rowWords;
            Rows = rows;
        }

        internal bool Valid => words.IsCreated;

        internal bool Wants(int x, int y)
        {
            int xWord = (x >> 5) - LeftWord;
            int row = y - Top;
            return (uint)xWord < (uint)RowWords && (uint)row < (uint)Rows &&
                   (words[row * RowWords + xWord] & (1u << (x & 31))) != 0;
        }
    }

    readonly Full319View335 view;
    ComputeShader shader;
    ComputeBuffer buffer;
    CommandBuffer commands;
    int kernel;
    bool disabled, submitted;
    internal string Failure { get; private set; }

    internal ClothRequestBits525(Full319View335 view) => this.view = view;

    static bool IsInput(RenderTexture t) =>
        t && t.IsCreated() && t.width == Width && t.height == Height && t.antiAliasing == 1 &&
        t.graphicsFormat == GraphicsFormat.R32G32B32A32_SFloat;

    internal bool TryRead(out Result result)
    {
        result = default;
        if (disabled || submitted || !view || view.contourReady || !ClothRegion524.Ready(view) ||
            ClothRegion524.PartBits540 != 14)
            return false;
        int frame = Time.frameCount, serial = view.renderedSerial335;
        var centre = view.motion.raw[5].rt;
        var owner = view.owner.rt;
        var atlas = ClothRegion524.Atlas540;
        if (!IsInput(centre) || !IsInput(owner) || !atlas || atlas.width != Width || atlas.height != Height ||
            atlas.graphicsFormat != GraphicsFormat.R32G32B32A32_SFloat)
        {
            Failure = "Unexpected prepared input size or format";
            return false;
        }

        int left = Width, right = 0, top = Height, bottom = 0;
        foreach (var part in ClothRegion524.Parts540)
        {
            if (!ClothRegion524.Active540(part.submesh)) continue;
            var bounds = part.bounds;
            if (bounds.xMin < 0 || bounds.yMin < 0 || bounds.xMax > Width || bounds.yMax > Height ||
                bounds.width <= 0 || bounds.height <= 0 || part.selected == null ||
                part.selected.Length != bounds.width * bounds.height)
                return false;
            left = Math.Min(left, bounds.xMin);
            right = Math.Max(right, bounds.xMax);
            top = Math.Min(top, bounds.yMin);
            bottom = Math.Max(bottom, bounds.yMax);
        }

        int leftWord = left >> 5, rowWords = ((right + 31) >> 5) - leftWord, rows = bottom - top;
        int count = rowWords * rows;
        if (count <= 0 || count > WordCapacity)
            return false;
        try
        {
            if (!shader)
            {
                shader = Resources.Load<ComputeShader>(ResourcePath);
                if (!shader || !shader.HasKernel("Gather"))
                {
                    Failure = "Cloth request compute kernel unavailable";
                    disabled = true;
                    return false;
                }
                kernel = shader.FindKernel("Gather");
            }
            buffer ??= new ComputeBuffer(WordCapacity, sizeof(uint), ComputeBufferType.Structured);
            commands ??= new CommandBuffer {name="525 same-frame cloth request bits"};
            commands.SetComputeIntParam(shader, "_LeftWord", leftWord);
            commands.SetComputeIntParam(shader, "_Top", top);
            commands.SetComputeIntParam(shader, "_RowWords", rowWords);
            commands.SetComputeIntParam(shader, "_WordCount", count);
            commands.SetComputeTextureParam(shader, kernel, "_Centre", centre);
            commands.SetComputeTextureParam(shader, kernel, "_Owner", owner);
            commands.SetComputeTextureParam(shader, kernel, "_Selected", atlas);
            commands.SetComputeBufferParam(shader, kernel, "_Words", buffer);
            commands.DispatchCompute(shader, kernel, (count + 63) / 64, 1, 1);

            submitted = true;
            Graphics.ExecuteCommandBuffer(commands);
            var read = AsyncGPUReadback.Request(buffer, count * sizeof(uint), 0);
            read.WaitForCompletion();
            if (!read.done || read.hasError)
                throw new InvalidOperationException("Clothing bit readback did not complete successfully");
            submitted = false;
            var data = read.GetData<uint>();
            if (frame != Time.frameCount || serial != view.renderedSerial335 || view.contourReady ||
                !ClothRegion524.Ready(view) || view.motion.raw[5].rt != centre || view.owner.rt != owner ||
                ClothRegion524.Atlas540 != atlas || data.Length != count)
                throw new InvalidOperationException("Clothing bit readback no longer matches the prepared frame");
            result = new Result(data, leftWord, top, rowWords, rows);
            return true;
        }
        catch (Exception e)
        {
            Failure = e.GetType().Name + ": " + e.Message;
            disabled = true;
            return false;
        }
        finally { commands?.Clear(); }
    }

    // Both legacy transfers were submitted and completed after the failed compute on the same graphics queue.
    internal void ObserveCompletedFallback() => submitted = false;

    internal bool CanRelease => !submitted;

    public void Dispose()
    {
        if (!CanRelease)
            throw new InvalidOperationException("Clothing bit buffer still has unverified graphics use");
        commands?.Release();
        commands = null;
        buffer?.Release();
        buffer = null;
    }
}
