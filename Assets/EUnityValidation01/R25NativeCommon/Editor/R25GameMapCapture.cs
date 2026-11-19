using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace FantasySurvival.EditorTools.NativeGridR25
{
    internal sealed class R25GameMapCapture
    {
        const string Menu = "Tools/Pixel Rendering/R25 GameMap1 Front and Quarter";
        const string AssetRoot = "Assets/EUnityValidation01/R25NativeCommon/Editor/";
        const string ScenePath = "Assets/Scenes/GameMap1.unity";
        const string PipelinePath = "Assets/EUnityValidation01/MatchedPlayer397/Candidate/Run12/Matched397Pipeline.asset";
        const string Configuration = "LocalOnly/R25_NATIVE_COMMON_CONFIG.json";
        const int Width = 960, Height = 544;
        static R25GameMapCapture running;

        readonly Gameplay397 game;
        readonly NativePlayer395 player;
        readonly string destination;
        readonly Dictionary<string, string> guard;
        ComputeShader compute;
        StaticPalette154 source;
        IntegratedCanvas154 canvas;
        SplitDirectionalShadow154 shadows;
        Shader eyeShader;
        Texture2D palette;
        R25NativeView capture;
        int index, submittedFrame;
        bool aborted, released;
        double submitTime;
        Quaternion headFront;
        Matrix4x4[] pose;

        [MenuItem(Menu)]
        public static void StartPair()
        {
            RequireEditorState();
            if (running != null || NativeWorldFeature395.EditorTrial != null)
                throw new InvalidOperationException("R25 has an existing owner");
            var config = JObject.Parse(File.ReadAllText(Configuration));
            string cache = Path.GetFullPath((string)config["cache"]);
            string registry = Path.GetFullPath((string)config["registry"]);
            var state = JObject.Parse(File.ReadAllText(Path.GetFullPath((string)config["state"])));
            var guard = state["guard128"].ToDictionary(row => (string)row["path"], row => (string)row["sha256"]);
            if (guard.Count != 128 || !guard.ContainsKey(ScenePath))
                throw new InvalidOperationException("R25 requires the existing 128-file protection manifest");
            VerifyGuard(guard);
            var game = Object.FindAnyObjectByType<Gameplay397>();
            var player = NativePlayer395.Active;
            var matched = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>(PipelinePath);
            if (!game || !player || game.gameObject.scene.path != ScenePath || !game.isActiveAndEnabled ||
                !game.connected || (game.runInputTest && !game.testFinished) || game.player != player ||
                !player.ready || player.pipeline != matched || GraphicsSettings.currentRenderPipeline != matched ||
                !player.gameCamera || !player.gameCamera.orthographic ||
                Mathf.Abs(player.gameCamera.orthographicSize - 1.502602f) > .0001f ||
                !player.host.headReady || player.host.headEyes == null || !player.host.main.stockMember ||
                player.nativePixelsPerCell != 2 || player.origin != Vector2Int.zero || player.manualDelta ||
                SystemInfo.graphicsDeviceType != GraphicsDeviceType.Direct3D11 || !SystemInfo.supportsAsyncGPUReadback)
                throw new InvalidOperationException("R25 requires the ready original GameMap1/Gameplay397 DX11 product path at native2");
            var root = Path.Combine("LocalOnly", "Runtime399", "R25NativeCommon");
            Directory.CreateDirectory(root);
            string output = Path.Combine(root, DateTime.UtcNow.ToString("yyyyMMddTHHmmss") + "-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(output);
            var session = new R25GameMapCapture(game, player, output, guard);
            try
            {
                session.Prepare(cache, registry);
                File.WriteAllText(Path.Combine(output, "START.json"), JsonConvert.SerializeObject(new
                {
                    scene = ScenePath, pipeline = PipelinePath, productScale = 2,
                    characterPitch = 1, worldPitch = 2, crop = R25NativeView.Crop.ToString(), views = 2
                }));
                running = session;
                EditorApplication.update += session.Update;
                Debug.Log("R25 two-view run armed at " + output);
            }
            catch
            {
                session.DisposeResources();
                throw;
            }
        }

        R25GameMapCapture(Gameplay397 game, NativePlayer395 player, string destination, Dictionary<string, string> guard)
        {
            this.game = game;
            this.player = player;
            this.destination = destination;
            this.guard = guard;
        }

        static void RequireEditorState()
        {
            var scene = SceneManager.GetActiveScene();
            if (!EditorApplication.isPlaying || EditorApplication.isCompiling ||
                scene.path != ScenePath || scene.isDirty || SceneManager.sceneCount != 1)
                throw new InvalidOperationException("R25 requires a single clean GameMap1 in Play Mode");
        }

        static void VerifyGuard(Dictionary<string, string> guard)
        {
            using var sha = SHA256.Create();
            foreach (var file in guard)
            {
                using var content = File.OpenRead(file.Key);
                if (!string.Equals(BitConverter.ToString(sha.ComputeHash(content)).Replace("-", ""),
                    file.Value, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("R25 protected file changed: " + file.Key);
            }
        }

        Shader RequiredShader(string name)
        {
            var shader = AssetDatabase.LoadAssetAtPath<Shader>(AssetRoot + name + ".shader");
            if (!shader || !shader.isSupported || ShaderUtil.ShaderHasError(shader))
                throw new InvalidOperationException("R25 imported shader unavailable: " + name);
            return shader;
        }

        void Prepare(string cache, string registry)
        {
            compute = Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>(AssetRoot + "T3_NativeAperture154.compute"));
            compute.hideFlags = HideFlags.HideAndDontSave;
            foreach (string kernel in new[] { "PresentNativeCommon154", "CaptureWorldStamped154", "PrepareNativeOwnerRays154", "SelectConnectedOwners154" })
                if (!compute.HasKernel(kernel))
                    throw new InvalidOperationException("R25 missing compute kernel " + kernel);
            if (ShaderUtil.GetComputeShaderMessages(compute).Any(m => m.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error))
                throw new InvalidOperationException("R25 imported compute failed");
            eyeShader = RequiredShader("CommonCellProducer");
            var bodyShader = RequiredShader("T2_ActorBody154");
            var toonShader = RequiredShader("T2_ActorToon154");
            var surfaceShader = RequiredShader("T2_DirectionalProbe154");
            var eye = player.host.headEyes;
            source = new StaticPalette154(eye, cache, new SkinSource101(eye, registry));
            canvas = new IntegratedCanvas154(eye, source, lightTrace: true, validationShader: surfaceShader, deferTargets: true);
            canvas.AllocateTargets(R25NativeView.Crop);
            shadows = new SplitDirectionalShadow154(player, bodyShader, toonShader, mapSize: 1024);
            int rows = Math.Max(72, source.RegionCount + 1);
            var packed = new Vector4[8 * rows];
            foreach (var binding in source.bindings)
                for (int family = 0; family < binding.palette.height; family++)
                    for (int q = 0; q < binding.levels; q++)
                    {
                        int start = 4 * (family * binding.levels + q);
                        packed[(binding.regionBase + 1 + family) * 8 + q] =
                            new Vector4(binding.paletteLinear[start], binding.paletteLinear[start + 1], binding.paletteLinear[start + 2], 1);
                    }
            palette = new Texture2D(8, rows, TextureFormat.RGBAFloat, false, true)
            {
                name = "R25 owned finite LUT", hideFlags = HideFlags.HideAndDontSave, filterMode = FilterMode.Point
            };
            palette.SetPixelData(packed, 0);
            palette.Apply(false, true);
            compute.SetInt("_CellPaletteRows154", rows);
            var cutsA = new Vector4[9];
            var cutsB = new Vector4[9];
            for (int levels = 2; levels <= 8; levels++)
                for (int k = 0; k < levels - 1; k++)
                {
                    float cut = (float)((k + .5) / (levels - 1));
                    if (k < 4) cutsA[levels][k] = cut;
                    else cutsB[levels][k - 4] = cut;
                }
            compute.SetVectorArray("_CellCutsA154", cutsA);
            compute.SetVectorArray("_CellCutsB154", cutsB);
        }

        void Update()
        {
            try
            {
                if (aborted)
                {
                    if (capture == null || capture.ReadyForDisposal)
                        Finish(false);
                    return;
                }
                if (capture != null)
                {
                    if (capture.Error != null)
                        throw new InvalidOperationException(capture.Error);
                    if (!capture.FinalComplete || !capture.ReadyForDisposal)
                    {
                        if (EditorApplication.timeSinceStartup - submitTime > 30)
                            throw new TimeoutException("R25 last-use proof did not arrive");
                        return;
                    }
                    SaveView();
                    retired.AddRange(capture.OwnedTextures());
                    capture.Dispose();
                    capture = null;
                    if (++index == 2)
                    {
                        Finish(true);
                        return;
                    }
                }
                if (submittedFrame != Time.frameCount)
                    SubmitOne();
            }
            catch (Exception error)
            {
                aborted = true;
                Debug.LogError(error);
                File.WriteAllText(Path.Combine(destination, "FAILURE.txt"), error.ToString());
                if (capture != null && !capture.ReadyForDisposal)
                    File.WriteAllText(Path.Combine(destination, "OWNER_RETAINED"),
                        "The R25 owner is kept until ordered GPU completion can be confirmed.");
            }
        }

        void SubmitOne()
        {
            RequireEditorState();
            if (!game || !game.connected || !player.ready || NativeWorldFeature395.EditorTrial != null)
                throw new InvalidOperationException("R25 readiness changed before submission");
            var cam = player.gameCamera;
            var animator = player.host.main.motion.animation.target;
            var state = animator.GetCurrentAnimatorStateInfo(0);
            if (animator.IsInTransition(0) || !animator.GetCurrentAnimatorClipInfo(0).Any(c => c.clip.name == "Rig|Idle_Loop"))
                throw new InvalidOperationException("R25 fixed matching idle pose is unavailable");
            var actor = player.avatar;
            var root = player.player;
            Vector3 oldRoot = root.position, oldCamera = cam.transform.position;
            Quaternion oldActor = actor.rotation, oldCameraRotation = cam.transform.rotation;
            float oldTime = Time.timeScale;
            var follow = cam.GetComponent<CameraFollow>();
            if (!follow)
                throw new InvalidOperationException("R25 original camera follow is unavailable");
            bool oldFollow = follow.enabled;
            bool oldHistory = player.host.main.motion.resetHistory;
            var renderErrors = new List<string>();
            void Observe(string message, string _, LogType kind)
            {
                if (kind == LogType.Error || kind == LogType.Exception)
                    renderErrors.Add(message);
            }
            try
            {
                Time.timeScale = 0;
                follow.enabled = false;
                root.position = new Vector3(0, .55f, -4);
                actor.SetPositionAndRotation(player.feet.position, Quaternion.identity);
                animator.Play(state.fullPathHash, 0, .5f);
                animator.Update(0);
                var poseNow = animator.GetComponentsInChildren<Transform>(true)
                    .Select(bone => Matrix4x4.TRS(bone.localPosition, bone.localRotation, bone.localScale)).ToArray();
                var head = animator.GetBoneTransform(HumanBodyBones.Head);
                if (index == 0)
                {
                    pose = poseNow;
                    var right = Vector3.Dot(head.right, Vector3.left) < 0 ? -head.right : head.right;
                    headFront = Quaternion.LookRotation(Vector3.Cross(right, head.up), head.up);
                }
                else if (!pose.SequenceEqual(poseNow))
                    throw new InvalidOperationException("R25 second camera evaluated a different animation pose");
                var rotation = index == 0 ? headFront : Quaternion.Euler(30, 170, 0);
                cam.transform.SetPositionAndRotation(root.position + Vector3.up * .91f - rotation * Vector3.forward * 1.9f, rotation);
                player.host.main.motion.resetHistory = true;
                capture = new R25NativeView(player, compute, canvas, shadows, source, eyeShader, palette);
                shadows.BindCasterMaterials();
                submittedFrame = Time.frameCount;
                submitTime = EditorApplication.timeSinceStartup;
                NativeWorldFeature395.EditorTrial = capture;
                Application.logMessageReceived += Observe;
                game.SendMessage("Present", SendMessageOptions.RequireReceiver);
                if (renderErrors.Count > 0)
                    throw new InvalidOperationException("R25 captured Unity error: " + renderErrors[0]);
                capture.RequireFinalSubmission();
            }
            finally
            {
                Application.logMessageReceived -= Observe;
                NativeWorldFeature395.EditorTrial = null;
                try
                {
                    shadows.RestoreCasterMaterials();
                    root.position = oldRoot;
                    actor.SetPositionAndRotation(player.feet.position, oldActor);
                    animator.Play(state.fullPathHash, 0, state.normalizedTime);
                    animator.Update(0);
                }
                finally
                {
                    cam.transform.SetPositionAndRotation(oldCamera, oldCameraRotation);
                    follow.enabled = oldFollow;
                    player.host.main.motion.resetHistory = oldHistory;
                    Time.timeScale = oldTime;
                }
            }
        }

        void SaveView()
        {
            var packet = capture.Owner;
            if (packet.x == 0 || packet.w != capture.Ticket)
                throw new InvalidOperationException("R25 connected selector rejected the frame. Reason " + packet.y);
            var crop = R25NativeView.Crop;
            var counts = new int[6];
            var stockingCodes = new HashSet<uint>();
            int committed = 0, worldHidden = 0, intrusion = 0;
            var area = capture.DepthArea;
            var shift = capture.AddressShift;
            for (int i = 0; i < capture.Receipt.Length; i += 3)
            {
                var writes = capture.Receipt[i];
                if (writes.x > 1 || writes.y != 0 || writes.z != 0)
                    throw new InvalidOperationException("R25 invalid palette address, duplicate or later write at cell " + (i / 3));
                int cell = i / 3;
                var pixel = new Vector2Int(crop.x + cell % crop.width, crop.y + cell / crop.width) - shift;
                if (!area.Contains(pixel))
                    continue;
                if (writes.x != 1)
                    throw new InvalidOperationException("R25 expected one committed cell at " + pixel);
                committed++;
                var data = capture.Receipt[i + 1];
                int slot = (int)((data.z >> 8) & 255);
                var depth = capture.Depth[(pixel.y - area.y) * area.width + pixel.x - area.x];
                bool visible = depth.b > .5f && depth.g <= depth.r + .0001f;
                if ((depth.a > .5f) != visible)
                    intrusion++;
                if (depth.b > .5f && !visible)
                    worldHidden++;
                if (!visible)
                    continue;
                if (slot < counts.Length)
                    counts[slot]++;
                if ((data.y >> 8) == 71)
                    stockingCodes.Add(data.y & 255);
            }
            string name = index == 0 ? "front" : "quarter";
            bool hasEyeRoles = counts[1] > 0 && counts[2] > 0 && counts[3] > 0;
            File.WriteAllText(Path.Combine(destination, name + ".json"), JsonConvert.SerializeObject(new
            {
                capture.Ticket, committed, worldHidden, intrusion, slots = counts, stockingCodes,
                phase = new[] { capture.Phase.x, capture.Phase.y }, actorPitch = 1, worldPitch = 2, hasEyeRoles
            }));
            var rgb = Array.ConvertAll(capture.Colour, raw => new Color(Mathf.LinearToGammaSpace(raw.r),
                Mathf.LinearToGammaSpace(raw.g), Mathf.LinearToGammaSpace(raw.b), 1));
            var image = new Texture2D(Width, Height, TextureFormat.RGBA32, false);
            try
            {
                image.SetPixels(rgb);
                image.Apply();
                string suffix = intrusion == 0 && hasEyeRoles ? "_1X.png" : "_FAILED_1X.png";
                File.WriteAllBytes(Path.Combine(destination, name + suffix), image.EncodeToPNG());
            }
            finally
            {
                Object.DestroyImmediate(image);
            }
            if (intrusion != 0 || !hasEyeRoles)
                throw new InvalidOperationException("R25 depth or visible eye-role acceptance failed. Refer to " + name + ".json");
        }

        void Finish(bool success)
        {
            DisposeResources();
            if (!OwnedObjectsDestroyed())
                return;
            EditorApplication.update -= Update;
            running = null;
            VerifyGuard(guard);
            if (NativeWorldFeature395.EditorTrial != null)
                throw new InvalidOperationException("R25 editor trial binding is still active");
            File.WriteAllText(Path.Combine(destination, "RESULT.json"),
                JsonConvert.SerializeObject(new { success, released = true, completedViews = index, protectedFiles = guard.Count }));
        }

        readonly List<Object> retired = new List<Object>();
        bool OwnedObjectsDestroyed() => retired.All(resource => !resource);

        void DisposeResources()
        {
            if (released)
                return;
            retired.AddRange((canvas?.OwnedTextures() ?? Enumerable.Empty<Object>())
                .Concat(shadows?.OwnedTextures() ?? Enumerable.Empty<Object>())
                .Concat(source?.OwnedTextures() ?? Enumerable.Empty<Object>())
                .Concat(capture?.OwnedTextures() ?? Enumerable.Empty<Object>()).Concat(new Object[] { palette, compute }));
            capture?.Dispose();
            shadows?.Dispose();
            canvas?.Dispose();
            source?.Dispose();
            if (palette) Object.DestroyImmediate(palette);
            if (compute) Object.DestroyImmediate(compute);
            released = true;
        }
    }
}
