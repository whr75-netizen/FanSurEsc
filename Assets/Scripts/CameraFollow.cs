using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.EventSystems;

[DisallowMultipleComponent]
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

    public bool IsOrbiting => orbiting;
    public float Pitch => pitch;

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
        if (target != null)
            transform.position = target.position + offset;
    }

    public void RestoreViewOrientation(Quaternion rotation, Vector3 restoredOffset)
    {
        InitializeOrbit();
        EndOrbit();
        transform.rotation = rotation;
        offset = restoredOffset;
        cameraSpaceOffset = Quaternion.Inverse(rotation) * restoredOffset;
        ReadAnglesFromTransform();
        if (target != null)
            transform.position = target.position + offset;
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
        if (target != null)
            transform.position = target.position + offset;
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
        if (target != null)
            transform.position = target.position + offset;
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
