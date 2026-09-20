using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.EventSystems;

[DisallowMultipleComponent]
[DefaultExecutionOrder(50)] // CameraZoomController applies the current size before clipping/position.
public class CameraFollow : MonoBehaviour
{
    public Transform target;
    public Vector3 offset = new Vector3(0, 10, -5);

    [Header("Inspection Orbit")]
    [SerializeField] private bool enableOrbit;
    [SerializeField, Min(0.01f)] private float orbitDegreesPerPixel = 0.2f;
    [SerializeField, Range(0f, 89f)] private float minPitch = 10f;
    [SerializeField, Range(0f, 89f)] private float maxPitch = 80f;

    private bool initialized;
    private bool orbiting;
    private Vector3 initialOffset;
    private Quaternion initialRotation;
    private Vector3 cameraSpaceOffset;
    private float yaw;
    private float pitch;
    private CursorLockMode previousCursorLock;
    private bool previousCursorVisible;
    private Camera viewCamera;
    private Transform clippingScope;
    private bool hasClippingBounds;
    private Bounds clippingBounds;
    private float originalFarClip;

    public bool IsOrbiting => orbiting;
    public float Pitch => pitch;
    public float MinimumPitch => minPitch;

    private void Awake()
    {
        InitializeOrbit();
    }

    private void InitializeOrbit()
    {
        if (initialized)
            return;

        initialOffset = offset;
        initialRotation = transform.rotation;
        // Rotate the original offset in camera space: the target's framing stays
        // unchanged even when the original camera did not look exactly at it.
        cameraSpaceOffset = Quaternion.Inverse(initialRotation) * offset;
        ReadAnglesFromTransform();
        initialized = true;
    }

    private void Update()
    {
        if (!CanAcceptOrbitInput())
        {
            EndOrbit();
            return;
        }

        if (!orbiting && GameInputBindings.WasPressedThisFrame(GameInputActionId.CameraOrbit))
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
                return;

            previousCursorLock = Cursor.lockState;
            previousCursorVisible = Cursor.visible;
            orbiting = true;
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
            // Ignore the press frame's delta, including any cursor-lock warp.
            return;
        }

        if (!orbiting)
            return;

        if (!GameInputBindings.IsPressed(GameInputActionId.CameraOrbit))
        {
            EndOrbit();
            return;
        }

        RotateBy(GameInputBindings.ReadCameraLookDelta());
    }

    public void RotateBy(Vector2 pointerDelta)
    {
        if (!CanAcceptOrbitInput() || pointerDelta == Vector2.zero)
            return;

        InitializeOrbit();
        // Mouse delta is displacement, not velocity: do not multiply by deltaTime.
        yaw = Mathf.Repeat(yaw + pointerDelta.x * orbitDegreesPerPixel + 180f, 360f) - 180f;
        pitch = Mathf.Clamp(pitch - pointerDelta.y * orbitDegreesPerPixel, minPitch, maxPitch);
        Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
        offset = rotation * cameraSpaceOffset;
        transform.rotation = rotation;
    }

    public void SetViewOrientation(Quaternion rotation)
    {
        InitializeOrbit();
        EndOrbit();
        transform.rotation = rotation;
        offset = rotation * cameraSpaceOffset;
        ReadAnglesFromTransform();
        ApplyPosition();
    }

    public void RestoreViewOrientation(Quaternion rotation, Vector3 restoredOffset)
    {
        InitializeOrbit();
        EndOrbit();
        transform.rotation = rotation;
        offset = restoredOffset;
        cameraSpaceOffset = Quaternion.Inverse(rotation) * restoredOffset;
        ReadAnglesFromTransform();
        ApplyPosition();
    }

    public void SetOrthographicClippingBounds(Transform scope, Bounds worldBounds)
    {
        if (viewCamera == null) viewCamera = GetComponent<Camera>();
        if (!hasClippingBounds) originalFarClip = viewCamera.farClipPlane;
        clippingScope = scope;
        clippingBounds = worldBounds;
        hasClippingBounds = true;
        ApplyPosition();
    }

    public void ClearOrthographicClippingBounds(Transform scope)
    {
        if (!hasClippingBounds || clippingScope != scope) return;
        hasClippingBounds = false;
        clippingScope = null;
        if (viewCamera != null) viewCamera.farClipPlane = originalFarClip;
        ApplyPosition();
    }

    private void ApplyPosition()
    {
        if (target == null) return;
        Vector3 position = target.position + offset;
        if (hasClippingBounds && clippingScope == null) ClearOrthographicClippingBounds(clippingScope);
        if (hasClippingBounds && viewCamera != null && viewCamera.orthographic && transform.forward.y < -0.001f)
        {
            // Parallel translation preserves orthographic screen XY, zoom and the authored offset.
            float downward = -transform.forward.y;
            float verticalExtent = viewCamera.orthographicSize *
                (Mathf.Abs(transform.up.y) + viewCamera.aspect * Mathf.Abs(transform.right.y));
            float nearBottom = position.y - viewCamera.nearClipPlane * downward - verticalExtent;
            float retreat = Mathf.Max(0f, (clippingBounds.max.y + 0.01f - nearBottom) / downward);
            position -= transform.forward * retreat;
            float requiredFar = (position.y + verticalExtent - clippingBounds.min.y + 0.01f) / downward;
            viewCamera.farClipPlane = Mathf.Max(originalFarClip, requiredFar);
        }
        transform.position = position;
    }

    private bool CanAcceptOrbitInput()
    {
        if (!enableOrbit || target == null || Time.timeScale <= 0f)
            return false;

        PersistentGameplayShell shell = PersistentGameplayShell.Instance;
        return shell == null || (!shell.IsTravelPrepared &&
            (shell.EscapeMenu == null || !shell.EscapeMenu.IsOpen) &&
            (shell.InventoryUI == null || !shell.InventoryUI.BlocksGameplayInput));
    }

    private void LateUpdate()
    {
        ApplyPosition();
    }

    [ContextMenu("Reset View")]
    public void ResetView()
    {
        if (!initialized)
            return;

        EndOrbit();
        offset = initialOffset;
        transform.rotation = initialRotation;
        ReadAnglesFromTransform();
        ApplyPosition();
    }

    private void ReadAnglesFromTransform()
    {
        yaw = Mathf.DeltaAngle(0f, transform.eulerAngles.y);
        pitch = Mathf.DeltaAngle(0f, transform.eulerAngles.x);
    }

    private void EndOrbit()
    {
        if (!orbiting)
            return;

        orbiting = false;
        Cursor.lockState = previousCursorLock;
        Cursor.visible = previousCursorVisible;
        // The selected view persists; only cursor capture belongs to the drag.
    }

    private void OnDisable()
    {
        EndOrbit();
    }

    private void OnApplicationFocus(bool hasFocus)
    {
        if (!hasFocus)
            EndOrbit();
    }

    private void OnValidate()
    {
        orbitDegreesPerPixel = Mathf.Max(0.01f, orbitDegreesPerPixel);
        minPitch = Mathf.Clamp(minPitch, 0f, 89f);
        maxPitch = Mathf.Clamp(maxPitch, minPitch, 89f);
    }
}
