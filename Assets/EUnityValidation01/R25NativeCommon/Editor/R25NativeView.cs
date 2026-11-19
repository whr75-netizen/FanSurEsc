using System;
using System.Collections.Generic;
using Unity.Mathematics;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.EditorTools.NativeGridR25
{
    internal sealed class R25NativeView : NativeWorldFeature395.IEditorTrial, IDisposable
    {
        public static readonly RectInt Crop = new RectInt(384, 0, 192, 352);
        const int Width = 960, Height = 544;
        readonly NativePlayer395 view;
        readonly ComputeShader shader;
        readonly IntegratedCanvas154 canvas;
        readonly SplitDirectionalShadow154 shadows;
        readonly R25EyeAtlas eyeAtlas;
        readonly Texture2D palette;
        readonly GraphicsBuffer proof, owners, receipts;
        readonly NativeOwnerGraph154 selection;
        readonly HeadPass headPass;
        GraphicsBuffer candidates;
        bool worldPlanned, worldIssued, worldDone, headPlanned, headIssued, headDone, finalPlanned, finalIssued;
        int finalCallbacks;
        const int ReadbackCount = 4;
        public Vector2 Phase { get; private set; }
        public RectInt Window { get; private set; }
        public bool ReadyForDisposal => (!worldIssued || worldDone) && (!headIssued || headDone) &&
            (!finalPlanned || FinalComplete);
        public bool FinalComplete => finalCallbacks == ReadbackCount;
        public int Ticket => selection.Ticket;
        public uint4[] Receipt { get; private set; }
        public uint4 Owner { get; private set; }
        public Color[] Colour { get; private set; }
        public Color[] Depth { get; private set; }
        public RectInt DepthArea { get; private set; }
        public Vector2Int AddressShift { get; private set; }
        public string Error { get; private set; }

        public R25NativeView(NativePlayer395 view, ComputeShader shader, IntegratedCanvas154 canvas,
            SplitDirectionalShadow154 shadows, StaticPalette154 source, Shader eyeShader, Texture2D palette)
        {
            this.view = view;
            this.shader = shader;
            this.canvas = canvas;
            this.shadows = shadows;
            this.palette = palette;
            int cells = Crop.width * Crop.height;
            try
            {
                eyeAtlas = new R25EyeAtlas(view.host.headEyes, source, eyeShader);
                proof = CreateBuffer(1);
                owners = CreateBuffer(cells);
                receipts = CreateBuffer(3 * cells);
                receipts.SetData(new uint4[3 * cells]);
                selection = new NativeOwnerGraph154(view, eyeAtlas, shader, Crop, proof, owners);
                headPass = new HeadPass(this);
            }
            catch
            {
                Dispose();
                throw;
            }
        }

        static GraphicsBuffer CreateBuffer(int count) => new GraphicsBuffer(GraphicsBuffer.Target.Structured, count, 16);

        public void EnqueueHeadPass(ScriptableRenderer renderer, Camera camera)
        {
            if (camera == view.host.headCamera && Time.frameCount == selection.Frame)
                renderer.EnqueuePass(headPass);
        }

        sealed class HeadPass : ScriptableRenderPass
        {
            readonly R25NativeView owner;
            public HeadPass(R25NativeView owner)
            {
                this.owner = owner;
                renderPassEvent = (RenderPassEvent)552;
            }
            public override void RecordRenderGraph(RenderGraph graph, ContextContainer frame) => owner.RecordHead(graph, frame);
        }

        sealed class PassData
        {
            public R25NativeView owner;
            public Camera camera;
            public TextureHandle colour, depth;
            public Vector2 phase;
        }

        public bool RecordWorld(RenderGraph graph, ContextContainer frame, NativePlayer395 player)
        {
            var camera = frame.Get<UniversalCameraData>().camera;
            if (view != player || !selection.ForWorldCapture(camera))
                return false;
            if (worldPlanned || Time.frameCount != selection.Frame)
                throw new InvalidOperationException("R25 duplicated or stale world production");
            worldPlanned = true;
            var resources = frame.Get<UniversalResourceData>();
            var size = graph.GetTextureDesc(resources.activeColorTexture);
            if (size.width != Width || size.height != Height)
                throw new InvalidOperationException("R25 world target must be 960x544");
            using var pass = graph.AddUnsafePass<PassData>("R25 stamp normal world colour/depth", out var data);
            data.owner = this;
            data.camera = camera;
            data.colour = resources.activeColorTexture;
            data.depth = resources.cameraDepthTexture.IsValid() ? resources.cameraDepthTexture : resources.activeDepthTexture;
            pass.UseTexture(data.colour);
            pass.UseTexture(data.depth);
            pass.UseTexture(graph.ImportTexture(view.world), AccessFlags.Write);
            pass.UseTexture(graph.ImportTexture(view.worldDepth), AccessFlags.Write);
            pass.UseBuffer(graph.ImportBuffer(proof), AccessFlags.Write);
            pass.AllowPassCulling(false);
            pass.AllowGlobalStateModification(true);
            pass.SetRenderFunc(static (PassData d, UnsafeGraphContext context) => d.owner.CaptureWorld(d, context));
            return true;
        }

        void CaptureWorld(PassData data, UnsafeGraphContext context)
        {
            var cmd = CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
            int kernel = selection.BindStampedCapture(cmd);
            RTHandle colour = data.colour, depth = data.depth;
            cmd.SetComputeTextureParam(shader, kernel, "_MainSource395", colour.rt);
            cmd.SetComputeTextureParam(shader, kernel, "_MainDepth395", depth.rt);
            cmd.SetComputeTextureParam(shader, kernel, "_WorldRW395", view.world.rt);
            cmd.SetComputeTextureParam(shader, kernel, "_WorldDepthRW395", view.worldDepth.rt);
            worldIssued = true;
            cmd.DispatchCompute(shader, kernel, 120, 68, 1);
            cmd.RequestAsyncReadback(proof, result => worldDone = result.done && !result.hasError);
            view.worldView = data.camera.worldToCameraMatrix;
            view.worldProjection = data.camera.projectionMatrix;
            view.worldSerial++;
        }

        void RecordHead(RenderGraph graph, ContextContainer frame)
        {
            if (!worldIssued || headPlanned || frame.Get<UniversalCameraData>().camera != view.host.headCamera)
                throw new InvalidOperationException("R25 eye producer has no unique current world witness");
            headPlanned = true;
            var head = view.host.head;
            var face = head.motion.surface.outputs[1];
            var vertices = face.sharedMesh.vertices;
            if (vertices.Length != 4060)
                throw new InvalidOperationException("R25 original canthus topology changed");
            var first = face.transform.TransformPoint((vertices[2520] + vertices[2487]) * .5f);
            var second = face.transform.TransformPoint((vertices[1986] + vertices[1996]) * .5f);
            Vector2 WorldPixel(Vector3 point)
            {
                var clip = view.worldProjection * view.worldView * new Vector4(point.x, point.y, point.z, 1);
                return new Vector2((clip.x / clip.w * .5f + .5f) * Width, (clip.y / clip.w * .5f + .5f) * Height);
            }
            var a = WorldPixel(first);
            var b = WorldPixel(second);
            var h0 = head.Project(first);
            var h1 = head.Project(second);
            var projection = head.motion.camera.projectionMatrix;
            float flip = GL.GetGPUProjectionMatrix(projection, true).m11 / projection.m11;
            Vector4 shift = head.nativeShift - head.motion.clipShift;
            var residue = new Vector2(480 * shift.x, 272 * shift.y / flip);
            var map = new Vector2(h0.x, 272 - h0.y) * 2 + residue - a;
            if ((new Vector2(h1.x, 272 - h1.y) * 2 + residue - b - map).sqrMagnitude > .0001f)
                throw new InvalidOperationException("R25 head witness pitch differs from the native screen");
            int x0 = Mathf.FloorToInt(Mathf.Min(a.x, b.x)) - 19, x1 = Mathf.CeilToInt(Mathf.Max(a.x, b.x)) + 19;
            int y0 = Mathf.FloorToInt(Mathf.Min(a.y, b.y)) - 13, y1 = Mathf.CeilToInt(Mathf.Max(a.y, b.y)) + 13;
            Window = new RectInt(x0, y0, x1 - x0, y1 - y0);
            if (x0 < Crop.x || x1 > Crop.xMax || y0 < Crop.y || y1 > Crop.yMax ||
                x1 <= x0 || y1 <= y0 || (long)Window.width * Window.height > 2048)
                throw new InvalidOperationException("R25 eye window exceeds the native crop or 2048-pixel budget");
            candidates = CreateBuffer(Window.width * Window.height * 4);
            eyeAtlas.Record(graph, frame, layer =>
            {
                headIssued = true;
                selection.OnEyeLayerIssued(eyeAtlas, layer);
            });
            var roi = eyeAtlas.Roi;
            selection.SetLocalLayout(Window, new RectInt(roi.x, 272 - roi.yMax, roi.width, roi.height),
                new Vector3(map.x, map.y, view.host.depthOffset), candidates);
            // A head-only failure can still retire its resources without a final dispatch.
            using var pass = graph.AddUnsafePass<PassData>("R25 eye production completion", out var data);
            data.owner = this;
            foreach (var layer in eyeAtlas.Layers)
            {
                pass.UseTexture(graph.ImportTexture(layer.meta), AccessFlags.Read);
                pass.UseTexture(graph.ImportTexture(layer.shade), AccessFlags.Read);
            }
            pass.AllowPassCulling(false);
            pass.AllowGlobalStateModification(true);
            pass.SetRenderFunc(static (PassData d, UnsafeGraphContext context) =>
            {
                var x = d.owner;
                CommandBufferHelpers.GetNativeCommandBuffer(context.cmd).RequestAsyncReadback(x.eyeAtlas.Layers[4].shade.rt,
                    0, 0, 1, 0, 1, 0, 1, result => x.headDone = result.done && !result.hasError);
            });
        }

        public bool RecordFinal(RenderGraph graph, ContextContainer frame, NativePlayer395 player)
        {
            if (player != view || !view.host.main.contourReady)
                return false; // Ordinary 397 preparation still uses the existing renderer.
            if (!headIssued || finalPlanned || Time.frameCount != selection.Frame || view.presentSerial + 1 != selection.Ticket)
            {
                // The ordinary preparation present also increments the native serial.
                // The bridge reserves a ticket for the one final presentation only.
                throw new InvalidOperationException("R25 final present does not match the armed world/eye certificate");
            }
            int before = shadows.RecordedBatches;
            try { shadows.Record(graph, frame); }
            catch
            {
                // Before a shadow pass is recorded there is nothing in this
                // camera to retire. The earlier producers have their own receipts.
                finalPlanned = shadows.RecordedBatches != before;
                throw;
            }
            finalPlanned = true;
            canvas.BindDirectionalShadows(shadows.World, shadows.Self, shadows.WorldToShadow, shadows.SelfToShadow);
            var resources = frame.Get<UniversalResourceData>();
            canvas.Record(graph, resources);
            selection.Record(graph, canvas.fields[1], canvas.fields[3]);
            using var pass = graph.AddUnsafePass<PassData>("R25 one final native character commit", out var data);
            data.owner = this;
            data.phase = Phase = view.manualDelta ? view.delta : view.host.main.motion.composeDelta;
            // The integer translation for a one-pixel cell follows the same
            // floor rule as the kernel, including exact half-cell ties.
            AddressShift = new Vector2Int(Mathf.FloorToInt(.5f - 2 * Phase.x), Mathf.FloorToInt(.5f - 2 * Phase.y));
            var min = Vector2Int.Max(Crop.min - AddressShift, Vector2Int.zero);
            var max = Vector2Int.Min(Crop.max - AddressShift, new Vector2Int(Width, Height));
            DepthArea = new RectInt(min, max - min);
            if (DepthArea.width <= 0 || DepthArea.height <= 0)
                throw new InvalidOperationException("R25 crop has no on-screen pixels");
            data.camera = view.gameCamera;
            foreach (var target in new[] { view.world, view.worldDepth, canvas.fields[0], canvas.fields[1], canvas.fields[2], canvas.fields[3] })
                pass.UseTexture(graph.ImportTexture(target), AccessFlags.Read);
            foreach (var layer in eyeAtlas.Layers)
            {
                pass.UseTexture(graph.ImportTexture(layer.meta), AccessFlags.Read);
                pass.UseTexture(graph.ImportTexture(layer.shade), AccessFlags.Read);
            }
            foreach (var target in new[] { view.output, view.owner, view.cellID, view.depthAudit })
                pass.UseTexture(graph.ImportTexture(target), AccessFlags.WriteAll);
            pass.UseBuffer(graph.ImportBuffer(owners), AccessFlags.Read);
            pass.UseBuffer(graph.ImportBuffer(receipts), AccessFlags.ReadWrite);
            pass.AllowPassCulling(false);
            pass.AllowGlobalStateModification(true);
            pass.SetRenderFunc(static (PassData d, UnsafeGraphContext context) => d.owner.Present(d, context));
            resources.cameraColor = graph.ImportTexture(view.output);
            return true;
        }

        void Present(PassData data, UnsafeGraphContext context)
        {
            selection.ConsumeOnce();
            var cmd = CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
            int k = shader.FindKernel("PresentNativeCommon154");
            void Bind(string name, RTHandle target) => cmd.SetComputeTextureParam(shader, k, name, target.rt);
            Bind("_World395", view.world);
            Bind("_WorldDepth395", view.worldDepth);
            Bind("_Output395", view.output);
            Bind("_Owner395", view.owner);
            Bind("_CellID395", view.cellID);
            Bind("_DepthAudit395", view.depthAudit);
            Bind("_IntegratedColour154", canvas.fields[0]);
            Bind("_IntegratedMeta154", canvas.fields[1]);
            Bind("_IntegratedSource154", canvas.fields[2]);
            Bind("_IntegratedLight154", canvas.fields[3]);
            string[] names = { "Skin", "White", "Iris", "Lash", "Hair" };
            for (int i = 0; i < names.Length; i++)
            {
                Bind(i == 0 ? "_LivePhysicalSkinMeta348" : "_Cell" + names[i] + "Meta154", eyeAtlas.Layers[i].meta);
                Bind("_Cell" + names[i] + "Input154", eyeAtlas.Layers[i].shade);
            }
            cmd.SetComputeTextureParam(shader, k, "_CellPalette154", palette);
            cmd.SetComputeBufferParam(shader, k, "_NativeConnectedOwners154", owners);
            cmd.SetComputeBufferParam(shader, k, "_CellReceipt154", receipts);
            cmd.SetComputeIntParams(shader, "_NativeCharacterCrop154", Crop.x, Crop.y, Crop.width, Crop.height);
            cmd.SetComputeIntParams(shader, "_Origin395", view.origin.x, view.origin.y);
            cmd.SetComputeIntParam(shader, "_NativeOwnerTicket154", selection.Ticket);
            cmd.SetComputeVectorParam(shader, "_Delta395", new Vector4(data.phase.x, data.phase.y, 0, 0));
            cmd.SetComputeVectorParam(shader, "_NearFar395", new Vector4(data.camera.nearClipPlane,
                data.camera.farClipPlane, SystemInfo.usesReversedZBuffer ? 1 : 0, 0));
            finalIssued = true;
            cmd.DispatchCompute(shader, k, 120, 68, 1);
            view.deliveredDelta = data.phase;
            view.presentSerial++;
            cmd.RequestAsyncReadback(owners, 16, 0, request => Complete(request, r => Owner = r.GetData<uint4>()[0]));
            cmd.RequestAsyncReadback(receipts, request => Complete(request, r => Receipt = r.GetData<uint4>().ToArray()));
            cmd.RequestAsyncReadback(view.output.rt, 0, request => Complete(request, r => Colour = r.GetData<Color>().ToArray()));
            cmd.RequestAsyncReadback(view.depthAudit.rt, 0, DepthArea.x, DepthArea.width, DepthArea.y, DepthArea.height, 0, 1,
                request => Complete(request, r => Depth = r.GetData<Color>().ToArray()));
        }

        void Complete(AsyncGPUReadbackRequest request, Action<AsyncGPUReadbackRequest> copy)
        {
            if (request.hasError || !request.done)
            {
                Error = "R25 readback error. Final resource use requires positive completion evidence.";
                return;
            }
            try { copy(request); }
            catch (Exception error) { Error = error.Message; }
            finally { finalCallbacks++; }
        }

        public void RequireFinalSubmission()
        {
            if (!finalIssued)
                throw new InvalidOperationException("R25 final pass was never issued");
        }

        public IEnumerable<UnityEngine.Object> OwnedTextures() =>
            eyeAtlas?.OwnedTextures() ?? Array.Empty<UnityEngine.Object>();

        public void Dispose()
        {
            eyeAtlas?.Dispose();
            candidates?.Dispose();
            receipts?.Dispose();
            owners?.Dispose();
            proof?.Dispose();
            foreach (var buffer in new[] { candidates, receipts, owners, proof })
                if (buffer != null && buffer.IsValid())
                    throw new InvalidOperationException("R25 still owns a valid graphics buffer after disposal");
        }
    }
}
