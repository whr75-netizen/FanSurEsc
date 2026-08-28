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

    private Camera controlledCamera;
    private float targetOrthographicSize;
    private float zoomVelocity;
    private float accumulatedScrollDelta;

    public float MinOrthographicSize => minOrthographicSize;
    public float MaxOrthographicSize => maxOrthographicSize;
    public float TargetOrthographicSize => targetOrthographicSize;

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
    }

    private void ApplyZoom()
    {
        if (controlledCamera == null || !controlledCamera.orthographic)
        {
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

    private void OnValidate()
    {
        minOrthographicSize = Mathf.Max(0.01f, minOrthographicSize);
        maxOrthographicSize = Mathf.Max(minOrthographicSize, maxOrthographicSize);
        zoomStep = Mathf.Max(0.01f, zoomStep);
        scrollDeltaPerStep = Mathf.Max(0.01f, scrollDeltaPerStep);
        zoomSmoothTime = Mathf.Max(0f, zoomSmoothTime);
    }
}
