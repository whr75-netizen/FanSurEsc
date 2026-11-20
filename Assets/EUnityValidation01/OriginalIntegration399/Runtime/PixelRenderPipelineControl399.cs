using System;
using UnityEngine;
using UnityEngine.InputSystem;

// Centralized modular layer, camera, and performance controller for the E399 pixel presentation.
// Every rendering layer can be toggled on/off sequentially at runtime (Inspector or F8 HUD)
// without throwing exceptions, leaving stale outer cameras, or black-screening gameplay.
[DisallowMultipleComponent]
[DefaultExecutionOrder(-50)]
public sealed class PixelRenderPipelineControl399 : MonoBehaviour
{
    public enum DisplayScaleMode
    {
        SmartFullViewport = 0,
        AspectFit = 1,
        ExactInteger = 2,
        StretchFill = 3
    }

    public enum PixelResolutionMode
    {
        MatchWorld1x = 0,
        HiResCharacter2x = 1,
        HiResBoth2x = 2
    }

    public static PixelRenderPipelineControl399 Active { get; private set; }

    [Header("Stage 0: Master Bypass & Display")]
    [Tooltip("Completely bypasses E399 offscreen pixel cameras and restores standard Main Camera presentation.")]
    public bool bypassPresentation = false;
    [Tooltip("SmartFullViewport fills 16:9 screens edge-to-edge (exact 2x on 1920x1080) over a solid backdrop with zero double-rectangle outer camera.")]
    public DisplayScaleMode displayScaleMode = DisplayScaleMode.SmartFullViewport;
    [Tooltip("MatchWorld1x: world & character both 480x272. HiResCharacter2x: character 2x (960x544 native density) over 480x272 world. HiResBoth2x: both 960x544.")]
    public PixelResolutionMode pixelResolutionMode = PixelResolutionMode.MatchWorld1x;
    [Tooltip("Initializes immediately once Camera.main and Player are ready instead of waiting 90 warmup frames.")]
    public bool fastStartup = true;

    [Header("Camera & GPU Performance")]
    [Tooltip("Renders Main Camera once per frame in Unity's native render loop instead of calling gameCamera.Render() a second time in LateUpdate.")]
    public bool avoidDuplicateWorldRender = true;
    [Tooltip("Prevents localCamera and headCamera from re-rendering the entire 3D world, SSAO, and 13 shadow maps.")]
    public bool cullWorldOnCharacterCameras = true;
    [Tooltip("Replaces 752 sequential 1px flood dispatches (1,504/frame) with 16 groupshared 16x16 tiled flood dispatches.")]
    public bool useFastTiledFlood = true;
    [Tooltip("Prevents OwnerLines333 from dropping outer silhouette outlines on sleeves, cuffs, corners, and arm-torso gaps.")]
    public bool useCleanOuterOutline = true;

    [Header("Sequential Render Layers (Safe to Toggle in Any Order)")]
    [Tooltip("Layer 1: Character pixel capture & world depth composite (_Show395).")]
    public bool enableCharacterPass = true;
    [Tooltip("Layer 2: Separate head-local pixel grid camera (headCamera). Disable for unified single-camera pass.")]
    public bool enableHeadLocalGrid = true;
    [Tooltip("Layer 3: Surface shading & discrete shade boundary regularization (LegacySignals + ShadeBoundary + RestoreStyle335).")]
    public bool enableSurfaceShading = true;
    [Tooltip("Layer 4: Character silhouette & internal part outlines (OwnerLines333).")]
    public bool enableOutlinePass = true;
    [Tooltip("Layer 5: 13-layer base eye rasterization & eye compose (Eyes + EyeCompose333).")]
    public bool enableEyeComposePass = true;
    [Tooltip("Layer 6: 4x4 subpixel eye contour/iris refinement (EyeRenderer367 / EyeFeature348).")]
    public bool enableEyeDetail348Pass = true;
    [Tooltip("Layer 7: Temporal color stability hold (_History395).")]
    public bool enableTemporalHistory = true;
    [Tooltip("Layer 8: 960x544 supersample passes (Native / Metadata960 / LegacySignals960 / ShadeBoundary960). Off by default for real-time speed.")]
    public bool enableNative960Supersample = false;

    [Header("Heavy CPU Diagnostic Layers (Default OFF for Real-Time FPS)")]
    [Tooltip("Layer 9: Exact BigInteger vector clothing union + synchronous GPU readback + CPU triangle raycast (ClothRegion524 / ClothSurface525).")]
    public bool enableClothingRegionCPU = false;
    [Tooltip("Layer 10: Legacy 11x synchronous GPU readbacks + CPU ContourSelect333.")]
    public bool enableOpenContourCPU = false;
    [Tooltip("Layer 11: Legacy 24-RT 4x4 PostView366 / SourceFeature366 / JoinSource367 candidate path.")]
    public bool enablePost366Candidate = false;

    [Header("Clothing Silhouette & Edge Stabilization (Real-Time GPU / Zero-Shrinkage)")]
    [Tooltip("Applies non-destructive Taubin zero-shrinkage low-pass smoothing to baked clothing submeshes (skirt/shoes/coat) while keeping original normals for fold shading.")]
    public bool enableClothMeshSmoothing = true;
    [Range(1, 10)]
    public int clothSmoothIterations = 6;
    [Range(0f, 1f)]
    public float clothSmoothStrength = 0.90f;
    [Tooltip("Keep original baked cloth normals so internal wrinkle shading stays rich while the silhouette is smooth.")]
    public bool clothSmoothKeepOriginalNormals = true;
    [Tooltip("GPU 1-pass spatial silhouette stabilizer (symmetric 1x1/2x1/1x2 protrusion pruning & 1x1/1x2 inward dent filling before outlines).")]
    public bool enableEdgeStabilizationGPU = true;
    [Tooltip("Include legs, torso, and arm concave-dent filling (face, hair, and 1px fingertips stay protected).")]
    public bool edgeStabilizeIncludeBody = true;
    [Tooltip("Actor-local 1-frame boundary debounce (Schmitt hysteresis) to stop 0<->1 clothing edge flickering without ghosting.")]
    public bool enableEdgeHysteresis = true;
    [Tooltip("Quantizes skeleton animation cadence (e.g. 12 FPS) for crisp pixel-art silhouettes while keeping movement & camera smooth at full FPS.")]
    public bool enableSteppedPose = true;
    [Range(6f, 30f)]
    public float steppedPoseFps = 12f;

    [Header("Runtime Debug Overlay (Press F8)")]
    public bool showLayerDebugHUD = false;

    [NonSerialized] public int lastOutlineDispatches;
    [NonSerialized] public int lastFrameWorldRenders;
    [NonSerialized] public int lastFrameCharacterCameraRenders;
    [NonSerialized] public int lastFrameReadbacks;

    private float smoothedDeltaTime = 1f / 60f;
    private int lastConfigVersion;
    private int cachedConfigHash;

    public static PixelRenderPipelineControl399 Ensure(Component host)
    {
        if (Active != null) return Active;
        if (host != null)
        {
            var existing = host.GetComponent<PixelRenderPipelineControl399>();
            if (existing == null) existing = host.gameObject.AddComponent<PixelRenderPipelineControl399>();
            Active = existing;
            return existing;
        }
        return null;
    }

    public static bool BypassPresentation => Active != null && Active.bypassPresentation;
    public static DisplayScaleMode CurrentDisplayScaleMode => Active != null ? Active.displayScaleMode : DisplayScaleMode.SmartFullViewport;
    public static PixelResolutionMode CurrentPixelResolutionMode => Active != null ? Active.pixelResolutionMode : PixelResolutionMode.MatchWorld1x;
    public static int CharacterCellScale => CurrentPixelResolutionMode == PixelResolutionMode.MatchWorld1x ? 2 : 1;
    public static int WorldCellScale => CurrentPixelResolutionMode == PixelResolutionMode.HiResBoth2x ? 1 : 2;
    public static bool FastStartup => Active == null || Active.fastStartup;
    public static bool AvoidDuplicateWorldRender => Active == null || Active.avoidDuplicateWorldRender;
    public static bool CullWorldOnCharacterCameras => Active == null || Active.cullWorldOnCharacterCameras;
    public static bool UseFastTiledFlood => Active == null || Active.useFastTiledFlood;
    public static bool UseCleanOuterOutline => Active == null || Active.useCleanOuterOutline;

    public static bool EnableCharacterPass => Active == null || (!Active.bypassPresentation && Active.enableCharacterPass);
    public static bool EnableHeadLocalGrid => EnableCharacterPass && (Active == null || Active.enableHeadLocalGrid);
    public static bool EnableSurfaceShading => EnableCharacterPass && (Active == null || Active.enableSurfaceShading);
    public static bool EnableOutlinePass => EnableCharacterPass && (Active == null || Active.enableOutlinePass);
    public static bool EnableEyeComposePass => EnableCharacterPass && (Active == null || Active.enableEyeComposePass);
    public static bool EnableEyeDetail348Pass => EnableEyeComposePass && (Active == null || Active.enableEyeDetail348Pass);
    public static bool EnableTemporalHistory => Active == null || Active.enableTemporalHistory;

    public static bool EnableClothingRegionCPU => EnableCharacterPass && Active != null && Active.enableClothingRegionCPU;
    public static bool EnableOpenContourCPU => EnableCharacterPass && Active != null && Active.enableOpenContourCPU;
    public static bool EnablePost366Candidate => EnableCharacterPass && Active != null && Active.enablePost366Candidate;

    public static bool NeedsTwoPassCPU => EnableClothingRegionCPU || EnableOpenContourCPU || EnablePost366Candidate;
    public static bool NeedsNative960 => EnableCharacterPass && ((Active != null && Active.enableNative960Supersample) || EnableClothingRegionCPU || EnableOpenContourCPU);

    public static bool EnableClothMeshSmoothing => Active == null || Active.enableClothMeshSmoothing;
    public static int ClothSmoothIterations => Active != null ? Mathf.Clamp(Active.clothSmoothIterations, 1, 10) : 6;
    public static float ClothSmoothStrength => Active != null ? Mathf.Clamp01(Active.clothSmoothStrength) : 0.90f;
    public static bool ClothSmoothKeepOriginalNormals => Active == null || Active.clothSmoothKeepOriginalNormals;
    public static bool EnableEdgeStabilizationGPU => EnableCharacterPass && (Active == null || Active.enableEdgeStabilizationGPU);
    public static bool EdgeStabilizeIncludeBody => Active == null || Active.edgeStabilizeIncludeBody;
    public static bool EnableEdgeHysteresis => EnableCharacterPass && (Active == null || Active.enableEdgeHysteresis);
    public static bool EnableSteppedPose => Active == null || Active.enableSteppedPose;
    public static float SteppedPoseFps => Active != null ? Mathf.Clamp(Active.steppedPoseFps, 6f, 60f) : 12f;

    public int ConfigVersion => lastConfigVersion;

    public void ApplyFastRealTimePreset()
    {
        bypassPresentation = false;
        displayScaleMode = DisplayScaleMode.SmartFullViewport;
        avoidDuplicateWorldRender = true;
        cullWorldOnCharacterCameras = true;
        useFastTiledFlood = true;
        enableCharacterPass = true;
        enableHeadLocalGrid = true;
        enableSurfaceShading = true;
        enableOutlinePass = true;
        enableEyeComposePass = true;
        enableEyeDetail348Pass = true;
        enableTemporalHistory = true;
        enableNative960Supersample = false;
        enableClothingRegionCPU = false;
        enableOpenContourCPU = false;
        enablePost366Candidate = false;
        enableClothMeshSmoothing = true;
        clothSmoothIterations = 6;
        clothSmoothStrength = 0.90f;
        enableEdgeStabilizationGPU = true;
        edgeStabilizeIncludeBody = true;
        useCleanOuterOutline = true;
        enableEdgeHysteresis = true;
        enableSteppedPose = true;
        steppedPoseFps = 12f;
        MarkConfigDirty();
    }

    public void ApplyMinimumCharacterPreset()
    {
        bypassPresentation = false;
        enableCharacterPass = true;
        enableHeadLocalGrid = false;
        enableSurfaceShading = false;
        enableOutlinePass = false;
        enableEyeComposePass = false;
        enableEyeDetail348Pass = false;
        enableTemporalHistory = false;
        enableNative960Supersample = false;
        enableClothingRegionCPU = false;
        enableOpenContourCPU = false;
        enablePost366Candidate = false;
        enableClothMeshSmoothing = false;
        enableEdgeStabilizationGPU = false;
        enableEdgeHysteresis = false;
        enableSteppedPose = false;
        MarkConfigDirty();
    }

    public void MarkConfigDirty()
    {
        lastConfigVersion++;
    }

    private void OnEnable()
    {
        Active = this;
        cachedConfigHash = ComputeConfigHash();
    }

    private void OnDisable()
    {
        if (Active == this) Active = null;
    }

    private void Update()
    {
        if (!Application.isPlaying) return;
        float dt = Time.unscaledDeltaTime;
        if (dt > 0f && dt < 1f)
            smoothedDeltaTime = Mathf.Lerp(smoothedDeltaTime, dt, 0.1f);

        var keyboard = Keyboard.current;
        if (keyboard != null && keyboard.f8Key.wasPressedThisFrame)
            showLayerDebugHUD = !showLayerDebugHUD;

        int hash = ComputeConfigHash();
        if (hash != cachedConfigHash)
        {
            cachedConfigHash = hash;
            lastConfigVersion++;
        }
    }

    private int ComputeConfigHash()
    {
        unchecked
        {
            int h = 17;
            h = h * 31 + (bypassPresentation ? 1 : 0);
            h = h * 31 + (int)displayScaleMode;
            h = h * 31 + (int)pixelResolutionMode;
            h = h * 31 + (avoidDuplicateWorldRender ? 1 : 0);
            h = h * 31 + (cullWorldOnCharacterCameras ? 1 : 0);
            h = h * 31 + (useFastTiledFlood ? 1 : 0);
            h = h * 31 + (useCleanOuterOutline ? 1 : 0);
            h = h * 31 + (enableCharacterPass ? 1 : 0);
            h = h * 31 + (enableHeadLocalGrid ? 1 : 0);
            h = h * 31 + (enableSurfaceShading ? 1 : 0);
            h = h * 31 + (enableOutlinePass ? 1 : 0);
            h = h * 31 + (enableEyeComposePass ? 1 : 0);
            h = h * 31 + (enableEyeDetail348Pass ? 1 : 0);
            h = h * 31 + (enableTemporalHistory ? 1 : 0);
            h = h * 31 + (enableNative960Supersample ? 1 : 0);
            h = h * 31 + (enableClothingRegionCPU ? 1 : 0);
            h = h * 31 + (enableOpenContourCPU ? 1 : 0);
            h = h * 31 + (enablePost366Candidate ? 1 : 0);
            h = h * 31 + (enableClothMeshSmoothing ? 1 : 0);
            h = h * 31 + clothSmoothIterations;
            h = h * 31 + Mathf.RoundToInt(clothSmoothStrength * 100f);
            h = h * 31 + (clothSmoothKeepOriginalNormals ? 1 : 0);
            h = h * 31 + (enableEdgeStabilizationGPU ? 1 : 0);
            h = h * 31 + (edgeStabilizeIncludeBody ? 1 : 0);
            h = h * 31 + (enableEdgeHysteresis ? 1 : 0);
            h = h * 31 + (enableSteppedPose ? 1 : 0);
            h = h * 31 + Mathf.RoundToInt(steppedPoseFps * 10f);
            return h;
        }
    }

    private void OnGUI()
    {
        if (!Application.isPlaying || !showLayerDebugHUD) return;

        float fps = smoothedDeltaTime > 0.0001f ? 1f / smoothedDeltaTime : 0f;
        float ms = smoothedDeltaTime * 1000f;

        GUI.depth = -1000;
        GUILayout.BeginArea(new Rect(12, 12, 390, 720), "Pixel Render Pipeline Control (F8)", GUI.skin.window);
        GUILayout.Label($"FPS: {fps:F1} ({ms:F1} ms) | Display: {displayScaleMode}");
        GUILayout.Label($"Pixel Res: {pixelResolutionMode} (Char {2 / CharacterCellScale}x / World {2 / WorldCellScale}x)");
        GUILayout.BeginHorizontal();
        if (GUILayout.Button(pixelResolutionMode == PixelResolutionMode.MatchWorld1x ? "[1x Same]" : "1x Same"))
        {
            pixelResolutionMode = PixelResolutionMode.MatchWorld1x;
            MarkConfigDirty();
        }
        if (GUILayout.Button(pixelResolutionMode == PixelResolutionMode.HiResCharacter2x ? "[2x Char Only]" : "2x Char Only"))
        {
            pixelResolutionMode = PixelResolutionMode.HiResCharacter2x;
            MarkConfigDirty();
        }
        if (GUILayout.Button(pixelResolutionMode == PixelResolutionMode.HiResBoth2x ? "[2x Both]" : "2x Both"))
        {
            pixelResolutionMode = PixelResolutionMode.HiResBoth2x;
            MarkConfigDirty();
        }
        GUILayout.EndHorizontal();
        GUILayout.Label($"Mode: {(bypassPresentation ? "BYPASSED (Original Camera)" : NeedsTwoPassCPU ? "2-Pass CPU Diagnostic" : "1-Pass Native GPU Loop")}");
        GUILayout.Label($"Outline Dispatches: {lastOutlineDispatches} | Readbacks: {lastFrameReadbacks}");

        GUILayout.Space(4);
        GUILayout.BeginHorizontal();
        if (GUILayout.Button("Fast Real-Time")) ApplyFastRealTimePreset();
        if (GUILayout.Button("Minimal Base")) ApplyMinimumCharacterPreset();
        if (GUILayout.Button(bypassPresentation ? "Resume E399" : "Bypass E399"))
        {
            bypassPresentation = !bypassPresentation;
            MarkConfigDirty();
        }
        GUILayout.EndHorizontal();

        GUILayout.Space(4);
        bypassPresentation = GUILayout.Toggle(bypassPresentation, "0. Bypass E399 Presentation (Raw Main Camera)");
        enableCharacterPass = GUILayout.Toggle(enableCharacterPass, "1. Character Pixel Pass & World Composite");
        enableHeadLocalGrid = GUILayout.Toggle(enableHeadLocalGrid, "2. Separate Head-Local Grid (headCamera)");
        enableSurfaceShading = GUILayout.Toggle(enableSurfaceShading, "3. Surface Shading & Shade Boundary (335)");
        enableOutlinePass = GUILayout.Toggle(enableOutlinePass, "4. Silhouette & Internal Outlines (OwnerLines)");
        enableEyeComposePass = GUILayout.Toggle(enableEyeComposePass, "5. Base Eye Layers & Compose (333)");
        enableEyeDetail348Pass = GUILayout.Toggle(enableEyeDetail348Pass, "6. 4x4 Subpixel Eye Refinement (348)");
        enableTemporalHistory = GUILayout.Toggle(enableTemporalHistory, "7. Temporal History Lock (_History395)");
        enableNative960Supersample = GUILayout.Toggle(enableNative960Supersample, "8. 960x544 Supersample Passes");

        GUILayout.Space(4);
        GUILayout.Label("--- Clothing Edge Stabilization (Anti-Flicker) ---");
        enableClothMeshSmoothing = GUILayout.Toggle(enableClothMeshSmoothing, $"S1. Taubin Cloth Smooth (iter={clothSmoothIterations}, str={clothSmoothStrength:F2})");
        enableEdgeStabilizationGPU = GUILayout.Toggle(enableEdgeStabilizationGPU, "S2. GPU Spur Prune & 1x1/1x2 Dent Fill");
        edgeStabilizeIncludeBody = GUILayout.Toggle(edgeStabilizeIncludeBody, "S2b. Include Legs/Torso/Arms Body Edge");
        enableEdgeHysteresis = GUILayout.Toggle(enableEdgeHysteresis, "S3. Actor-Local Temporal Edge Hysteresis");
        useCleanOuterOutline = GUILayout.Toggle(useCleanOuterOutline, "S3b. Clean Sleeve/Corner Outer Outlines");
        enableSteppedPose = GUILayout.Toggle(enableSteppedPose, $"S4. Stepped Pixel Pose ({steppedPoseFps:F0} FPS anim / 60 FPS move)");
        if (enableSteppedPose)
        {
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("8 FPS")) steppedPoseFps = 8f;
            if (GUILayout.Button("12 FPS")) steppedPoseFps = 12f;
            if (GUILayout.Button("15 FPS")) steppedPoseFps = 15f;
            if (GUILayout.Button("24 FPS")) steppedPoseFps = 24f;
            GUILayout.EndHorizontal();
        }

        GUILayout.Space(4);
        GUILayout.Label("--- Optimizations & Heavy CPU Paths ---");
        avoidDuplicateWorldRender = GUILayout.Toggle(avoidDuplicateWorldRender, "Opt: Single World Render (Native Loop)");
        cullWorldOnCharacterCameras = GUILayout.Toggle(cullWorldOnCharacterCameras, "Opt: Cull World/Shadows on Char Cameras");
        useFastTiledFlood = GUILayout.Toggle(useFastTiledFlood, "Opt: Fast Tiled Flood (16 vs 752 dispatches)");
        enableClothingRegionCPU = GUILayout.Toggle(enableClothingRegionCPU, "9. [Heavy CPU] ClothRegion524 + Raycast525");
        enableOpenContourCPU = GUILayout.Toggle(enableOpenContourCPU, "10. [Heavy CPU] OpenContour333 (11 Readbacks)");
        enablePost366Candidate = GUILayout.Toggle(enablePost366Candidate, "11. [Heavy] PostView366 (24 RTs)");

        GUILayout.Space(4);
        if (GUILayout.Button($"Cycle Display Mode ({displayScaleMode})"))
        {
            displayScaleMode = (DisplayScaleMode)(((int)displayScaleMode + 1) % 4);
            MarkConfigDirty();
        }
        GUILayout.EndArea();
    }
}
