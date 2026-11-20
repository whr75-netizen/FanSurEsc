using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using UniVRM10;
using UnityEngine;
using UnityEngine.InputSystem;

// Runtime VRM model switcher and quick selector bar (F7 toggle; also accessible inside F8 HUD).
// Preserves the default scene avatar (AvatarSample_A) losslessly and dynamically loads/caches
// any .vrm files placed in Assets/StreamingAssets/CharacterModels/ (e.g. AvatarSample_B/C/M).
[DisallowMultipleComponent]
[DefaultExecutionOrder(850)]
public sealed class CharacterModelSwitcher399 : MonoBehaviour
{
    public static CharacterModelSwitcher399 Active { get; private set; }

    [Header("Model Selector UI (F7 Toggle)")]
    public bool showQuickBar = true;

    public sealed class ModelEntry
    {
        public string displayName;
        public string vrmPath;
        public bool isDefault;
        public GameObject root;
        public Animator animator;
        public SkinnedMeshRenderer[] sources; // [0]=Body, [1]=Face, [2]=Hair
        public int[][] roles;
        public float sourceHeight;
    }

    private readonly List<ModelEntry> entries = new();
    private int activeIndex;
    private bool loading;
    private string statusMessage;
    private bool defaultCaptured;

    private Gameplay397 gameplay;
    private NativePlayer395 player;
    private PixelRenderPipelineControl399 control;
    private Mesh placeholderMesh;
    private Material placeholderMat;

    public IReadOnlyList<ModelEntry> Entries => entries;
    public int ActiveIndex => activeIndex;
    public bool IsLoading => loading;
    public string StatusMessage => statusMessage;

    public static CharacterModelSwitcher399 Ensure(Component host)
    {
        if (Active != null) return Active;
        if (host != null)
        {
            var existing = host.GetComponent<CharacterModelSwitcher399>();
            if (existing == null) existing = host.gameObject.AddComponent<CharacterModelSwitcher399>();
            Active = existing;
            return existing;
        }
        return null;
    }

    private void OnEnable()
    {
        Active = this;
    }

    private void OnDisable()
    {
        if (Active == this) Active = null;
    }

    private void OnDestroy()
    {
        if (Active == this) Active = null;
        for (int i = 0; i < entries.Count; i++)
        {
            var e = entries[i];
            if (!e.isDefault && e.root)
                Destroy(e.root);
        }
        if (placeholderMesh) Destroy(placeholderMesh);
        if (placeholderMat) Destroy(placeholderMat);
    }

    private void Update()
    {
        if (!Application.isPlaying) return;
        var keyboard = Keyboard.current;
        if (keyboard != null && keyboard.f7Key.wasPressedThisFrame)
            showQuickBar = !showQuickBar;

        if (!defaultCaptured) TryCaptureDefaultAndScan();
    }

    private void TryCaptureDefaultAndScan()
    {
        if (!gameplay) gameplay = GetComponent<Gameplay397>();
        if (!player) player = GetComponent<NativePlayer395>();
        if (!control) control = PixelRenderPipelineControl399.Ensure(this);

        if (!gameplay || !player || !gameplay.connected || !player.ready || !player.host || !player.host.main)
            return;

        var surface = player.host.main.motion ? player.host.main.motion.surface : null;
        if (!surface || surface.source == null || surface.source.Length < 3 || !player.avatar)
            return;

        entries.Clear();
        entries.Add(new ModelEntry
        {
            displayName = "AvatarSample_A (기본)",
            vrmPath = null,
            isDefault = true,
            root = player.avatar.gameObject,
            animator = gameplay.ActiveAnimator,
            sources = (SkinnedMeshRenderer[])surface.source.Clone(),
            roles = null,
            sourceHeight = player.sourceHeight
        });

        string modelsDir = Path.Combine(Application.streamingAssetsPath, "CharacterModels");
        if (Directory.Exists(modelsDir))
        {
            var files = Directory.GetFiles(modelsDir, "*.vrm", SearchOption.TopDirectoryOnly);
            Array.Sort(files, StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < files.Length; i++)
            {
                string file = files[i];
                string name = Path.GetFileNameWithoutExtension(file);
                if (string.Equals(name, "AvatarSample_A", StringComparison.OrdinalIgnoreCase)) continue;
                entries.Add(new ModelEntry
                {
                    displayName = name,
                    vrmPath = file,
                    isDefault = false
                });
            }
        }

        activeIndex = 0;
        defaultCaptured = true;
        statusMessage = null;
    }

    public void SelectModel(int index)
    {
        if (!defaultCaptured) TryCaptureDefaultAndScan();
        if (loading || index < 0 || index >= entries.Count || index == activeIndex) return;
        _ = SwitchModelAsync(index);
    }

    private async Task SwitchModelAsync(int targetIndex)
    {
        var target = entries[targetIndex];
        loading = true;
        statusMessage = $"로딩 중: {target.displayName}...";
        try
        {
            if (!target.isDefault && !target.root)
            {
                await LoadVrmEntryAsync(target);
            }

            if (!this || !isActiveAndEnabled || !target.root)
            {
                statusMessage = "모델 로드 실패";
                return;
            }

            ApplyModelEntry(targetIndex);
            statusMessage = null;
        }
        catch (Exception ex)
        {
            statusMessage = $"로드 오류: {ex.Message}";
            Debug.LogException(ex, this);
        }
        finally
        {
            loading = false;
        }
    }

    private static Task<Vrm10Instance> InvokeVrm10LoadPathAsync(string path)
    {
        // Invoke via reflection so Assembly-CSharp does not require a direct compile reference
        // to UniGLTF.Utils (which sets autoReferenced: false in com.vrmc.gltf).
        var method = typeof(Vrm10).GetMethod("LoadPathAsync", BindingFlags.Public | BindingFlags.Static);
        if (method == null)
            throw new MissingMethodException("UniVRM10.Vrm10", "LoadPathAsync");

        var pars = method.GetParameters();
        var args = new object[pars.Length];
        for (int i = 0; i < pars.Length; i++)
        {
            var p = pars[i];
            if (p.Name == "path") args[i] = path;
            else if (p.Name == "canLoadVrm0X") args[i] = true;
            else if (p.Name == "controlRigGenerationOption") args[i] = ControlRigGenerationOption.None;
            else if (p.Name == "showMeshes") args[i] = true;
            else if (p.Name == "materialGenerator") args[i] = new UrpVrm10MaterialDescriptorGenerator();
            else if (p.ParameterType == typeof(CancellationToken)) args[i] = CancellationToken.None;
            else if (p.HasDefaultValue) args[i] = p.DefaultValue;
            else args[i] = null;
        }
        return (Task<Vrm10Instance>)method.Invoke(null, args);
    }

    private async Task LoadVrmEntryAsync(ModelEntry entry)
    {
        var vrmInstance = await InvokeVrm10LoadPathAsync(entry.vrmPath);

        if (!vrmInstance)
            throw new InvalidOperationException($"Vrm10.LoadPathAsync returned null for {entry.vrmPath}");

        // Keep SpringBones disabled under stepped pixel pose so hair/skirts match the exact stepped cadence.
        vrmInstance.UpdateType = Vrm10Instance.UpdateTypes.None;

        var root = vrmInstance.gameObject;
        root.name = "RuntimeVRM_" + entry.displayName;
        root.transform.SetParent(player.feet, false);
        root.transform.localPosition = Vector3.zero;
        root.transform.localRotation = player.avatarRotation;
        root.transform.localScale = Vector3.one;

        var anim = root.GetComponent<Animator>();
        if (!anim) throw new InvalidOperationException($"{entry.displayName}: Humanoid Animator missing");

        var skins = root.GetComponentsInChildren<SkinnedMeshRenderer>(true);
        SkinnedMeshRenderer body = null, face = null, hair = null;
        for (int i = 0; i < skins.Length; i++)
        {
            var s = skins[i];
            if (!s || !s.sharedMesh) continue;
            string n = s.name;
            if (!body && n.IndexOf("Body", StringComparison.OrdinalIgnoreCase) >= 0) body = s;
            else if (!face && n.IndexOf("Face", StringComparison.OrdinalIgnoreCase) >= 0) face = s;
            else if (!hair && n.IndexOf("Hair", StringComparison.OrdinalIgnoreCase) >= 0) hair = s;
        }
        // Fallback by remaining renderers if names differ on custom VRMs
        for (int i = 0; i < skins.Length; i++)
        {
            var s = skins[i];
            if (!s || !s.sharedMesh || s == body || s == face || s == hair) continue;
            if (!body) body = s;
            else if (!face) face = s;
            else if (!hair) hair = s;
        }
        if (!body) throw new InvalidOperationException($"{entry.displayName}: Body SkinnedMeshRenderer not found");
        if (!face) face = CreateEmptyPlaceholderSkin(root.transform, "PlaceholderFace");
        if (!hair) hair = CreateEmptyPlaceholderSkin(root.transform, "PlaceholderHair");

        foreach (var s in skins)
        {
            if (!s) continue;
            s.forceMatrixRecalculationPerRender = true;
            s.updateWhenOffscreen = true;
            s.enabled = false;
        }

        // Measure rest height cleanly from mesh bounds (always valid even before renderer enable)
        float minY = float.MaxValue, maxY = float.MinValue;
        foreach (var s in new[] { body, face, hair })
        {
            if (!s || !s.sharedMesh || s.sharedMesh.vertexCount == 0) continue;
            var mb = s.sharedMesh.bounds;
            if (mb.size.y > 0.01f)
            {
                Vector3 c = s.transform.TransformPoint(mb.center) - root.transform.position;
                float halfY = mb.extents.y;
                minY = Mathf.Min(minY, c.y - halfY);
                maxY = Mathf.Max(maxY, c.y + halfY);
            }
        }
        float measuredHeight = (maxY > minY && (maxY - minY) > 0.5f && (maxY - minY) < 3.0f)
            ? (maxY - minY)
            : player.sourceHeight;

        var sources = new[] { body, face, hair };
        entry.root = root;
        entry.animator = anim;
        entry.sources = sources;
        entry.roles = ClassifySubmeshRoles(sources);
        entry.sourceHeight = measuredHeight;
        root.SetActive(false);
    }

    private SkinnedMeshRenderer CreateEmptyPlaceholderSkin(Transform parent, string name)
    {
        if (!placeholderMesh)
        {
            placeholderMesh = new Mesh { name = "399 Empty Placeholder Skin", hideFlags = HideFlags.DontSave };
            placeholderMesh.vertices = new[] { Vector3.zero, Vector3.zero, Vector3.zero };
            placeholderMesh.normals = new[] { Vector3.up, Vector3.up, Vector3.up };
            placeholderMesh.uv = new[] { Vector2.zero, Vector2.zero, Vector2.zero };
            placeholderMesh.SetTriangles(new[] { 0, 1, 2 }, 0);
        }
        if (!placeholderMat)
        {
            var sh = Shader.Find("Universal Render Pipeline/Unlit") ?? Shader.Find("Hidden/InternalErrorShader");
            placeholderMat = new Material(sh) { name = "399 Empty Placeholder Mat", hideFlags = HideFlags.DontSave };
        }
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var smr = go.AddComponent<SkinnedMeshRenderer>();
        smr.sharedMesh = placeholderMesh;
        smr.sharedMaterials = new[] { placeholderMat };
        smr.enabled = false;
        return smr;
    }

    public static int[][] ClassifySubmeshRoles(SkinnedMeshRenderer[] sources)
    {
        var result = new int[3][];
        for (int r = 0; r < 3; r++)
        {
            var s = sources[r];
            var mats = s ? s.sharedMaterials : Array.Empty<Material>();
            int count = (s && s.sharedMesh) ? Mathf.Min(s.sharedMesh.subMeshCount, mats.Length) : 0;
            result[r] = new int[count];
            for (int sm = 0; sm < count; sm++)
            {
                string mn = mats[sm] ? mats[sm].name : string.Empty;
                result[r][sm] = ClassifyRole(r, sm, mn);
            }
        }
        return result;
    }

    public static int ClassifyRole(int rendererIndex, int submeshIndex, string materialName)
    {
        string n = materialName ?? string.Empty;
        if (rendererIndex == 0)
        {
            if (n.IndexOf("HAIR", StringComparison.OrdinalIgnoreCase) >= 0) return 11;
            if (n.IndexOf("SKIN", StringComparison.OrdinalIgnoreCase) >= 0 &&
                n.IndexOf("CLOTH", StringComparison.OrdinalIgnoreCase) < 0) return 7;
            if (n.IndexOf("SHOE", StringComparison.OrdinalIgnoreCase) >= 0) return 9;
            if (n.IndexOf("BOTTOM", StringComparison.OrdinalIgnoreCase) >= 0 ||
                n.IndexOf("ONEPIECE", StringComparison.OrdinalIgnoreCase) >= 0 ||
                n.IndexOf("SKIRT", StringComparison.OrdinalIgnoreCase) >= 0) return 8;
            return 10;
        }
        if (rendererIndex == 1)
        {
            if (n.IndexOf("Mouth", StringComparison.OrdinalIgnoreCase) >= 0) return 0;
            if (n.IndexOf("EyeIris", StringComparison.OrdinalIgnoreCase) >= 0) return 1;
            if (n.IndexOf("EyeHighlight", StringComparison.OrdinalIgnoreCase) >= 0) return 2;
            if (n.IndexOf("EyeWhite", StringComparison.OrdinalIgnoreCase) >= 0) return 4;
            if (n.IndexOf("Brow", StringComparison.OrdinalIgnoreCase) >= 0) return 5;
            if (n.IndexOf("Eyeline", StringComparison.OrdinalIgnoreCase) >= 0) return 6;
            if (n.IndexOf("Face", StringComparison.OrdinalIgnoreCase) >= 0) return 3;
            return Mathf.Clamp(submeshIndex, 0, 6);
        }
        return 11 + (submeshIndex % 4);
    }

    private void ApplyModelEntry(int targetIndex)
    {
        var prev = entries[activeIndex];
        var next = entries[targetIndex];
        Quaternion preservedRot = prev.root ? prev.root.transform.rotation : (player.player ? player.player.rotation * player.avatarRotation : Quaternion.identity);

        if (prev.root) prev.root.SetActive(false);

        next.root.SetActive(true);
        next.root.transform.SetParent(player.feet, false);
        next.root.transform.position = player.feet.position;
        next.root.transform.rotation = preservedRot;
        next.root.transform.localScale = Vector3.one * (player.bodyHeight / Mathf.Max(0.25f, next.sourceHeight));

        foreach (var s in next.sources)
        {
            if (!s) continue;
            s.forceMatrixRecalculationPerRender = true;
            s.updateWhenOffscreen = true;
            s.enabled = false;
        }

        player.avatar = next.root.transform;
        player.sourceHeight = next.sourceHeight;
        gameplay.BindRuntimeAnimator(next.animator);

        var surface = player.host.main.motion.surface;
        surface.source = (SkinnedMeshRenderer[])next.sources.Clone();

        player.bake.RebuildForActiveModel();
        player.host.RebindModel(!next.isDefault, next.roles);

        activeIndex = targetIndex;
        if (control) control.MarkConfigDirty();
    }

    private void OnGUI()
    {
        if (!Application.isPlaying || !showQuickBar || !defaultCaptured || entries.Count == 0) return;

        float width = 265f;
        float height = 104f + entries.Count * 26f + (string.IsNullOrEmpty(statusMessage) ? 0f : 22f);
        float x = Mathf.Max(12f, Screen.width - width - 12f);
        float y = 12f;

        GUI.depth = -1001;
        GUILayout.BeginArea(new Rect(x, y, width, height), "Character Model / Res (F7)", GUI.skin.window);

        for (int i = 0; i < entries.Count; i++)
        {
            bool selected = i == activeIndex;
            string label = selected ? $"● {entries[i].displayName}" : $"   {entries[i].displayName}";
            GUI.enabled = !loading;
            if (GUILayout.Button(label))
                SelectModel(i);
            GUI.enabled = true;
        }

        if (!string.IsNullOrEmpty(statusMessage))
            GUILayout.Label(statusMessage);

        GUILayout.Space(4);
        if (control)
        {
            var mode = control.pixelResolutionMode;
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(mode == PixelRenderPipelineControl399.PixelResolutionMode.MatchWorld1x ? "[1x]" : "1x"))
            {
                control.pixelResolutionMode = PixelRenderPipelineControl399.PixelResolutionMode.MatchWorld1x;
                control.MarkConfigDirty();
            }
            if (GUILayout.Button(mode == PixelRenderPipelineControl399.PixelResolutionMode.HiResCharacter2x ? "[2x Char]" : "2x Char"))
            {
                control.pixelResolutionMode = PixelRenderPipelineControl399.PixelResolutionMode.HiResCharacter2x;
                control.MarkConfigDirty();
            }
            if (GUILayout.Button(mode == PixelRenderPipelineControl399.PixelResolutionMode.HiResBoth2x ? "[2x Both]" : "2x Both"))
            {
                control.pixelResolutionMode = PixelRenderPipelineControl399.PixelResolutionMode.HiResBoth2x;
                control.MarkConfigDirty();
            }
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            if (GUILayout.Button(control.showLayerDebugHUD ? "Close F8" : "Open F8"))
                control.showLayerDebugHUD = !control.showLayerDebugHUD;
            if (GUILayout.Button("Hide (F7)"))
                showQuickBar = false;
            GUILayout.EndHorizontal();
        }

        GUILayout.EndArea();
    }
}
