using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.EditorTools.NativeGridR25
{
    // Supplies the existing exact selector's same-ray tile. The normal eye
    // renderer keeps ownership of its own atlas and deferred candidate pass.
    internal sealed class R25EyeAtlas : IDisposable
    {
        internal sealed class Layer
        {
            public RTHandle meta, shade;
        }

        static readonly int[] faceSubmeshes = { 3, 4, 1, 6, 5 };
        readonly Material[] materials = new Material[9];
        readonly RTHandle[] scratch = new RTHandle[3];
        readonly EyeFeature348 eye;
        RTHandle depth;
        public readonly Layer[] Layers = new Layer[5];
        public RectInt Roi { get; private set; }

        public R25EyeAtlas(EyeFeature348 eye, StaticPalette154 palette, Shader shader)
        {
            this.eye = eye;
            try
            {
                for (int i = 0; i < materials.Length; i++)
                {
                    bool hair = i >= 5;
                    int slot = hair ? i - 5 : faceSubmeshes[i];
                    var original = hair ? eye.materials[11 + slot] : i == 0 ? eye.skinMaterial : eye.materials[4 + slot];
                    var material = materials[i] = new Material(original) { shader = shader, hideFlags = HideFlags.HideAndDontSave };
                    var binding = palette.Get(hair ? 2 : 1, slot);
                    material.SetFloat("_Auto245Role", binding.material);
                    palette.Bind(material, hair ? 2 : 1, slot);
                    ShaderUtil.CompilePass(material, 0, true);
                    if (!ShaderUtil.IsPassCompiled(material, 0) || ShaderUtil.ShaderHasError(shader))
                        throw new InvalidOperationException("R25 same-sample material variant failed before RT allocation");
                }
            }
            catch
            {
                Dispose();
                throw;
            }
        }

        sealed class DrawData
        {
            public R25EyeAtlas atlas;
            public int layer;
            public Matrix4x4 view, projection, restore;
            public Vector2 phase;
            public Action<int> issued;
        }

        public void Record(RenderGraph graph, ContextContainer frame, Action<int> issued)
        {
            Roi = eye.roi;
            if (depth != null || Roi.width <= 0 || Roi.height <= 0 || (long)Roi.width * Roi.height > 512)
                throw new InvalidOperationException("R25 eye atlas requires one prepared, bounded ROI");
            // Match the archive ABI, which reads tile four in a horizontally packed atlas.
            int width = Roi.width * 20;
            int height = Roi.height * 4;
            RTHandle Colour(string name) => RTHandles.Alloc(width, height, colorFormat: GraphicsFormat.R32G32B32A32_SFloat,
                filterMode: FilterMode.Point, name: "R25 owned " + name);
            for (int i = 0; i < scratch.Length; i++)
                scratch[i] = Colour("eye scratch " + i);
            depth = RTHandles.Alloc(width, height, depthBufferBits: DepthBits.Depth32, name: "R25 owned eye depth");

            var camera = frame.Get<UniversalCameraData>().camera;
            var full = eye.full;
            var cameraProjection = camera.projectionMatrix;
            float flip = GL.GetGPUProjectionMatrix(cameraProjection, true).m11 / cameraProjection.m11;
            Vector4 shift = full.nativeShift - full.motion.clipShift;
            Vector2 phase = new Vector2(.125f - 240 * shift.x, .125f - 136 * shift.y / flip);
            var projection = eye.cropProjection;
            projection.SetRow(0, projection.GetRow(0) - projection.GetRow(3) * (2 * phase.x / Roi.width));
            projection.SetRow(1, projection.GetRow(1) - projection.GetRow(3) * (2 * phase.y / Roi.height));

            var resources = frame.Get<UniversalResourceData>();
            for (int i = 0; i < Layers.Length; i++)
            {
                var layer = Layers[i] = new Layer();
                layer.meta = Colour("eye role/depth " + i);
                layer.shade = Colour("eye palette input " + i);
                using var pass = graph.AddRasterRenderPass<DrawData>("R25 current eye evidence " + i, out var data);
                data.atlas = this;
                data.layer = i;
                data.view = camera.worldToCameraMatrix;
                data.projection = projection;
                data.restore = cameraProjection;
                data.phase = phase;
                data.issued = issued;
                pass.SetRenderAttachment(graph.ImportTexture(scratch[0]), 0, AccessFlags.WriteAll);
                pass.SetRenderAttachment(graph.ImportTexture(layer.meta), 1, AccessFlags.WriteAll);
                pass.SetRenderAttachment(graph.ImportTexture(scratch[1]), 2, AccessFlags.WriteAll);
                pass.SetRenderAttachment(graph.ImportTexture(scratch[2]), 3, AccessFlags.WriteAll);
                pass.SetRenderAttachment(graph.ImportTexture(layer.shade), 4, AccessFlags.WriteAll);
                pass.SetRenderAttachmentDepth(graph.ImportTexture(depth), AccessFlags.WriteAll);
                pass.UseAllGlobalTextures(true);
                if (resources.mainShadowsTexture.IsValid())
                    pass.UseTexture(resources.mainShadowsTexture);
                if (resources.additionalShadowsTexture.IsValid())
                    pass.UseTexture(resources.additionalShadowsTexture);
                pass.AllowPassCulling(false);
                pass.AllowGlobalStateModification(true);
                pass.SetRenderFunc(static (DrawData d, RasterGraphContext ctx) => d.atlas.Draw(d, ctx.cmd));
            }
        }

        void Draw(DrawData d, RasterCommandBuffer cmd)
        {
            d.issued(d.layer);
            var full = eye.full;
            var surfaces = full.motion.surface.outputs;
            int atlasX = Roi.width * 16;
            cmd.ClearRenderTarget(RTClearFlags.All, Color.clear, 1, 0);
            cmd.SetViewport(new Rect(atlasX, 0, Roi.width * 4, Roi.height * 4));
            cmd.SetViewProjectionMatrices(d.view, d.projection);
            cmd.SetGlobalMatrix("_WorldToHead348", eye.headMatrix.inverse);
            cmd.SetGlobalInt("_SupportKind348", d.layer);
            cmd.SetGlobalVector("_ROI348", new Vector4(Roi.x + d.phase.x - atlasX * .25f,
                272 - Roi.yMax + d.phase.y, Roi.width, Roi.height));
            cmd.SetGlobalVector("_ClipShift333", Vector4.zero);
            cmd.SetGlobalVector("_Profile333", full.motion.animation.shadeProfile);
            cmd.SetGlobalVector("_SurfaceInvRaster335", new Vector4(1f / 480, 1f / 272, 0, 0));
            cmd.SetGlobalFloat("_SurfaceOwnShade335", full.motion.animation.shadeProfile.x);
            cmd.SetGlobalFloat("_ShadeLayer335", full.shadeLayer ? 1 : 0);
            cmd.SetGlobalFloat("_SurfaceShadeSteps335", full.surfaceShadeSteps);
            try
            {
                cmd.DrawMesh(eye.sampleFace, surfaces[1].transform.localToWorldMatrix,
                    materials[d.layer], faceSubmeshes[d.layer], 0);
                if (d.layer == 4)
                    for (int slot = 0; slot < 4; slot++)
                        cmd.DrawMesh(surfaces[2].sharedMesh, surfaces[2].transform.localToWorldMatrix, materials[5 + slot], slot, 0);
            }
            finally
            {
                cmd.SetViewport(eye.full.motion.camera.pixelRect);
                cmd.SetViewProjectionMatrices(d.view, d.restore);
                cmd.SetGlobalVector("_ClipShift333", full.motion.clipShift);
            }
        }

        public IEnumerable<UnityEngine.Object> OwnedTextures()
        {
            foreach (var t in scratch)
                if (t != null) yield return t.rt;
            foreach (var layer in Layers)
            {
                if (layer?.meta != null) yield return layer.meta.rt;
                if (layer?.shade != null) yield return layer.shade.rt;
            }
            if (depth != null) yield return depth.rt;
        }

        public void Dispose()
        {
            foreach (var material in materials)
                if (material)
                    UnityEngine.Object.DestroyImmediate(material);
            foreach (var texture in scratch)
                texture?.Release();
            foreach (var layer in Layers)
            {
                layer?.meta?.Release();
                layer?.shade?.Release();
            }
            depth?.Release();
        }
    }
}
