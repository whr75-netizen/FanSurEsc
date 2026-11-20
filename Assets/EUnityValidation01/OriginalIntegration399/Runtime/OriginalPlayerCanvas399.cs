using UnityEngine;
using UnityEngine.UI;
using FantasySurvival.CharacterPresentation;

// Displays the validated native render texture cleanly across the full viewport
// beneath the existing screen-space HUD, with an opaque backdrop so stale outer
// camera frames can never appear as a double-rectangle frame-in-frame.
[DefaultExecutionOrder(900)]
public sealed class OriginalPlayerCanvas399 : MonoBehaviour
{
    private Gameplay397 gameplay;
    private NativePlayer395 player;
    private PixelRenderPipelineControl399 control;
    private Canvas canvas;
    private Image backdrop;
    private RawImage image;
    private int previousWidth, previousHeight, previousTexWidth, previousTexHeight;
    private PixelRenderPipelineControl399.DisplayScaleMode previousScaleMode = (PixelRenderPipelineControl399.DisplayScaleMode)(-1);
    private CharacterSilhouetteSubject legacy;
    private Renderer[] legacyRenderers;
    private bool legacySuppressed;

    private void Awake()
    {
        control = PixelRenderPipelineControl399.Ensure(this);
        if (Application.isPlaying && !PixelRenderPipelineControl399.BypassPresentation)
            SetLegacyVisualSuppressed(true);
    }

    private void CacheLegacyVisual()
    {
        if (legacy) return;
        foreach (var candidate in FindObjectsByType<CharacterSilhouetteSubject>(FindObjectsInactive.Include))
            if (candidate.name == "CharacterSilhouettePlayerVisual")
            {
                legacy = candidate;
                legacyRenderers = legacy.GetComponentsInChildren<Renderer>(true);
                break;
            }
    }

    private void SetLegacyVisualSuppressed(bool suppress)
    {
        CacheLegacyVisual();
        if (!legacy) return;
        if (suppress)
        {
            if (legacy.enabled) legacy.enabled = false;
            if (legacyRenderers != null)
                foreach (var r in legacyRenderers)
                    if (r && r.enabled) r.enabled = false;
        }
        else if (legacySuppressed)
        {
            legacy.enabled = true;
            if (legacyRenderers != null)
                foreach (var r in legacyRenderers)
                    if (r) r.enabled = true;
        }
        legacySuppressed = suppress;
    }

    private void OnDisable()
    {
        if (canvas) canvas.enabled = false;
        if (backdrop) backdrop.enabled = false;
        if (image) image.enabled = false;
    }

    private void EnsureCanvas()
    {
        if (canvas) return;
        if (player)
        {
            foreach (var preview in GetComponentsInChildren<Camera>(true))
                if (preview != player.gameCamera && preview != player.localCamera &&
                    (!player.host || preview != player.host.headCamera))
                    preview.enabled = false;
        }

        var root = new GameObject("Native character and world display", typeof(RectTransform), typeof(Canvas));
        root.transform.SetParent(transform, false);
        canvas = root.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = short.MinValue;
        canvas.pixelPerfect = false;

        // Opaque full-screen backdrop eliminates any stale outer camera / double-rectangle edges.
        var bg = new GameObject("Viewport backdrop", typeof(RectTransform), typeof(Image));
        bg.transform.SetParent(root.transform, false);
        backdrop = bg.GetComponent<Image>();
        backdrop.color = Color.black;
        backdrop.raycastTarget = false;
        backdrop.rectTransform.anchorMin = Vector2.zero;
        backdrop.rectTransform.anchorMax = Vector2.one;
        backdrop.rectTransform.offsetMin = Vector2.zero;
        backdrop.rectTransform.offsetMax = Vector2.zero;

        var picture = new GameObject("Native pixels", typeof(RectTransform), typeof(RawImage));
        picture.transform.SetParent(root.transform, false);
        image = picture.GetComponent<RawImage>();
        image.color = Color.white;
        image.raycastTarget = false;
        image.rectTransform.anchorMin = image.rectTransform.anchorMax = new Vector2(0.5f, 0.5f);
        image.rectTransform.pivot = new Vector2(0.5f, 0.5f);
        image.rectTransform.anchoredPosition = Vector2.zero;
    }

    private void UpdateDisplayLayout(int texWidth, int texHeight, PixelRenderPipelineControl399.DisplayScaleMode mode)
    {
        int sw = Mathf.Max(1, Screen.width);
        int sh = Mathf.Max(1, Screen.height);
        float scaleX = (float)sw / texWidth;
        float scaleY = (float)sh / texHeight;
        float targetW, targetH;

        switch (mode)
        {
            case PixelRenderPipelineControl399.DisplayScaleMode.StretchFill:
                targetW = sw;
                targetH = sh;
                break;

            case PixelRenderPipelineControl399.DisplayScaleMode.ExactInteger:
            {
                int intScale = Mathf.Max(1, Mathf.FloorToInt(Mathf.Min(scaleX, scaleY)));
                targetW = texWidth * intScale;
                targetH = texHeight * intScale;
                break;
            }

            case PixelRenderPipelineControl399.DisplayScaleMode.AspectFit:
            {
                float fit = Mathf.Min(scaleX, scaleY);
                targetW = Mathf.Round(texWidth * fit);
                targetH = Mathf.Round(texHeight * fit);
                break;
            }

            default: // SmartFullViewport
            {
                // Prefer exact integer scaling when it cleanly fills the screen within 3% overscan
                // (e.g. 960x544 at 2x = 1920x1088 on 1920x1080 -> crisp 2:1 integer pixels, zero border).
                int nearestInt = Mathf.Max(1, Mathf.RoundToInt(Mathf.Max(scaleX, scaleY)));
                float intW = texWidth * nearestInt;
                float intH = texHeight * nearestInt;
                bool cleanIntegerFill = intW >= sw * 0.995f && intH >= sh * 0.995f &&
                                        intW <= sw * 1.035f && intH <= sh * 1.035f;
                if (cleanIntegerFill)
                {
                    targetW = intW;
                    targetH = intH;
                }
                else
                {
                    float screenAspect = (float)sw / sh;
                    float texAspect = (float)texWidth / texHeight;
                    float aspectDiff = Mathf.Abs(screenAspect - texAspect) / texAspect;
                    // On 16:9 screens (1280x720, 1600x900, 2560x1440), fill edge-to-edge cleanly.
                    // On ultrawide/square windows, aspect-fit cleanly over solid black backdrop.
                    float scale = aspectDiff <= 0.05f ? Mathf.Max(scaleX, scaleY) : Mathf.Min(scaleX, scaleY);
                    targetW = Mathf.Round(texWidth * scale);
                    targetH = Mathf.Round(texHeight * scale);
                }
                break;
            }
        }

        image.rectTransform.sizeDelta = new Vector2(targetW, targetH);
        image.rectTransform.anchoredPosition = Vector2.zero;
    }

    private void LateUpdate()
    {
        if (!control) control = PixelRenderPipelineControl399.Ensure(this);
        if (!gameplay) gameplay = GetComponent<Gameplay397>();
        if (!player) player = GetComponent<NativePlayer395>();

        if (PixelRenderPipelineControl399.BypassPresentation)
        {
            SetLegacyVisualSuppressed(false);
            if (canvas) canvas.enabled = false;
            if (backdrop) backdrop.enabled = false;
            if (image) image.enabled = false;
            return;
        }

        SetLegacyVisualSuppressed(true);

        bool prepared = gameplay && player && gameplay.connected && player.ready &&
            string.IsNullOrEmpty(gameplay.failure) && string.IsNullOrEmpty(player.failure) &&
            player.presentSerial > 0 && player.localCamera && player.localCamera.targetTexture;

        if (!prepared)
        {
            if (canvas) canvas.enabled = false;
            if (backdrop) backdrop.enabled = false;
            if (image) image.enabled = false;
            return;
        }

        EnsureCanvas();
        canvas.enabled = true;
        backdrop.enabled = true;
        image.texture = player.localCamera.targetTexture;
        image.enabled = true;

        var mode = PixelRenderPipelineControl399.CurrentDisplayScaleMode;
        int texW = image.texture.width;
        int texH = image.texture.height;
        if (previousWidth != Screen.width || previousHeight != Screen.height ||
            previousTexWidth != texW || previousTexHeight != texH ||
            previousScaleMode != mode)
        {
            previousWidth = Screen.width;
            previousHeight = Screen.height;
            previousTexWidth = texW;
            previousTexHeight = texH;
            previousScaleMode = mode;
            UpdateDisplayLayout(texW, texH, mode);
        }
    }
}
