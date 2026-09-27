using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(Camera))]
public sealed class CameraZoomController : MonoBehaviour
{
    [Header("Limited Orthographic Zoom")]
    [SerializeField, Min(0.01f)] private float minOrthographicSize = 3.5f;
    [SerializeField, Min(0.01f)] private float maxOrthographicSize = 8f;
    [SerializeField, Min(0.01f)] private float zoomStep = 0.5f;
    [Tooltip("Normalized mouse-wheel delta required for one zoom step.")]
    [SerializeField, Min(0.01f)] private float scrollDeltaPerStep = 1f;
    [Tooltip("Set to 0 for immediate stepped zoom, which is useful for pixel-perfect rendering.")]
    [SerializeField, Min(0f)] private float zoomSmoothTime = 0.08f;

    [Header("Native Sprite Display (Opt In)")]
    [Tooltip("Use SetNativePixelGrid for the current native-art scene. Original zoom settings are restored by ClearNativePixelGrid.")]
    [SerializeField] private bool nativePixelGrid;
    [SerializeField, Min(0.01f)] private float nativePixelsPerUnit = 22.627417f;

    private Camera controlledCamera;
    private float targetOrthographicSize;
    private float zoomVelocity;
    private float accumulatedScrollDelta;
    private float originalTargetOrthographicSize;
    private bool hasOriginalZoomTarget;

    public float MinOrthographicSize => minOrthographicSize;
    public float MaxOrthographicSize => maxOrthographicSize;
    public float TargetOrthographicSize => targetOrthographicSize;
    public bool NativePixelGridEnabled => nativePixelGrid;
    public float NativePixelsPerUnit => nativePixelsPerUnit;
    public int NativeIntegerScale { get; private set; }
    public bool NativeGridFitsZoomLimits { get; private set; } = true;

    public void SetNativePixelGrid(float pixelsPerUnit)
    {
        if (float.IsNaN(pixelsPerUnit) || float.IsInfinity(pixelsPerUnit) || pixelsPerUnit <= 0f)
            throw new System.ArgumentOutOfRangeException(nameof(pixelsPerUnit));
        if (controlledCamera == null) controlledCamera = GetComponent<Camera>();
        if (!hasOriginalZoomTarget)
        {
            originalTargetOrthographicSize = targetOrthographicSize > 0f
                ? targetOrthographicSize : controlledCamera.orthographicSize;
            hasOriginalZoomTarget = true;
        }
        nativePixelsPerUnit = pixelsPerUnit;
        nativePixelGrid = true;
        zoomVelocity = 0f;
        accumulatedScrollDelta = 0f;
        ApplyZoom();
    }

    public void ClearNativePixelGrid()
    {
        if (!nativePixelGrid && !hasOriginalZoomTarget) return;
        nativePixelGrid = false;
        if (hasOriginalZoomTarget)
            targetOrthographicSize = Mathf.Clamp(originalTargetOrthographicSize,
                minOrthographicSize, maxOrthographicSize);
        hasOriginalZoomTarget = false;
        NativeIntegerScale = 0;
        NativeGridFitsZoomLimits = true;
        zoomVelocity = 0f;
        accumulatedScrollDelta = 0f;
        if (controlledCamera != null && controlledCamera.orthographic)
            controlledCamera.orthographicSize = targetOrthographicSize;
    }

    private void Awake()
    {
        controlledCamera = GetComponent<Camera>();
        InitializeFromCamera();
    }

    private void OnEnable()
    {
        if (controlledCamera == null)
        {
            controlledCamera = GetComponent<Camera>();
        }

        InitializeFromCamera();
    }

    private void Update()
    {
        if (!CanAcceptZoomInput())
        {
            accumulatedScrollDelta = 0f;
            return;
        }

        ApplyScrollDelta(GameInputBindings.ReadCameraZoomDelta());
    }

    private void ApplyScrollDelta(float scrollDelta)
    {
        if (Mathf.Approximately(scrollDelta, 0f))
        {
            return;
        }

        accumulatedScrollDelta += scrollDelta;
        int stepCount = Mathf.FloorToInt(
            Mathf.Abs(accumulatedScrollDelta) / scrollDeltaPerStep);
        if (stepCount <= 0)
        {
            return;
        }

        float direction = Mathf.Sign(accumulatedScrollDelta);
        accumulatedScrollDelta -= direction * stepCount * scrollDeltaPerStep;
        if (nativePixelGrid)
        {
            float sizeAtOnePixel = NativeSizeAtOnePixel();
            GetNativeScaleRange(sizeAtOnePixel, out int minimumScale, out int maximumScale);
            int currentScale = Mathf.Clamp(Mathf.RoundToInt(sizeAtOnePixel /
                Mathf.Max(0.01f, targetOrthographicSize)), minimumScale, maximumScale);
            int nextScale = Mathf.Clamp(currentScale + (int)direction * stepCount,
                minimumScale, maximumScale);
            targetOrthographicSize = sizeAtOnePixel / nextScale;
            return;
        }
        targetOrthographicSize = Mathf.Clamp(
            targetOrthographicSize - direction * zoomStep * stepCount,
            minOrthographicSize,
            maxOrthographicSize);
    }

    private void LateUpdate()
    {
        ApplyZoom();
    }

    private bool CanAcceptZoomInput()
    {
        if (controlledCamera == null || !controlledCamera.orthographic)
        {
            return false;
        }

        PersistentGameplayShell shell = PersistentGameplayShell.Instance;
        if (shell == null)
        {
            return true;
        }

        return !shell.IsTravelPrepared &&
               (shell.EscapeMenu == null || !shell.EscapeMenu.IsOpen) &&
               (shell.InventoryUI == null || !shell.InventoryUI.BlocksGameplayInput);
    }

    private void InitializeFromCamera()
    {
        if (controlledCamera == null)
        {
            return;
        }

        targetOrthographicSize = Mathf.Clamp(
            controlledCamera.orthographicSize,
            minOrthographicSize,
            maxOrthographicSize);
        controlledCamera.orthographicSize = targetOrthographicSize;
        zoomVelocity = 0f;
        accumulatedScrollDelta = 0f;
        if (nativePixelGrid) SetNativePixelGrid(nativePixelsPerUnit);
    }

    private void ApplyZoom()
    {
        if (controlledCamera == null || !controlledCamera.orthographic)
        {
            return;
        }

        if (nativePixelGrid)
        {
            float sizeAtOnePixel = NativeSizeAtOnePixel();
            GetNativeScaleRange(sizeAtOnePixel, out int minimumScale, out int maximumScale);
            NativeIntegerScale = Mathf.Clamp(Mathf.RoundToInt(sizeAtOnePixel /
                Mathf.Max(0.01f, targetOrthographicSize)), minimumScale, maximumScale);
            targetOrthographicSize = sizeAtOnePixel / NativeIntegerScale;
            controlledCamera.orthographicSize = targetOrthographicSize;
            NativeGridFitsZoomLimits = targetOrthographicSize >= minOrthographicSize - 0.0001f &&
                targetOrthographicSize <= maxOrthographicSize + 0.0001f;
            zoomVelocity = 0f;
            return;
        }

        if (zoomSmoothTime <= 0f)
        {
            controlledCamera.orthographicSize = targetOrthographicSize;
            zoomVelocity = 0f;
            return;
        }

        controlledCamera.orthographicSize = Mathf.SmoothDamp(
            controlledCamera.orthographicSize,
            targetOrthographicSize,
            ref zoomVelocity,
            zoomSmoothTime,
            Mathf.Infinity,
            Time.unscaledDeltaTime);

        if (Mathf.Abs(controlledCamera.orthographicSize - targetOrthographicSize) < 0.001f)
        {
            controlledCamera.orthographicSize = targetOrthographicSize;
            zoomVelocity = 0f;
        }
    }

    private float NativeSizeAtOnePixel()
    {
        // Render scale is 1 in the current pipeline. Dynamic-resolution pixel height is
        // used so no smooth intermediate zoom or texture resampling is introduced here.
        return Mathf.Max(1, controlledCamera.scaledPixelHeight) / (2f * nativePixelsPerUnit);
    }

    private void GetNativeScaleRange(float sizeAtOnePixel, out int minimumScale, out int maximumScale)
    {
        minimumScale = Mathf.Max(1, Mathf.CeilToInt(sizeAtOnePixel / maxOrthographicSize - 0.00001f));
        maximumScale = Mathf.Max(minimumScale,
            Mathf.FloorToInt(sizeAtOnePixel / minOrthographicSize + 0.00001f));
        // A tiny viewport may have no integer scale inside the old size interval.
        // Preserve native texels at >= 1x; expose the conflict instead of downsampling.
    }

    private void OnValidate()
    {
        minOrthographicSize = Mathf.Max(0.01f, minOrthographicSize);
        maxOrthographicSize = Mathf.Max(minOrthographicSize, maxOrthographicSize);
        zoomStep = Mathf.Max(0.01f, zoomStep);
        scrollDeltaPerStep = Mathf.Max(0.01f, scrollDeltaPerStep);
        zoomSmoothTime = Mathf.Max(0f, zoomSmoothTime);
        nativePixelsPerUnit = Mathf.Max(0.01f, nativePixelsPerUnit);
    }
}
