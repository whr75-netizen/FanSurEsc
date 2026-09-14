using FantasySurvival.Actions;
using FantasySurvival.Controls;
using FantasySurvival.SceneFlow;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(PlayerActionController))]
[RequireComponent(typeof(CharacterController))]
public class PlayerMovement : MonoBehaviour
{
    public const string LocomotionSpeedParameter = "LocomotionSpeed";

    public float speed = 10f;

    [SerializeField, Min(1f)] private float runSpeedMultiplier = 1.3f;
    [SerializeField] private Animator characterAnimator;
    [SerializeField, Min(0f)] private float turnSpeedDegreesPerSecond = 1080f;

    private static readonly int LocomotionSpeedHash = Animator.StringToHash(LocomotionSpeedParameter);
    private const float GroundedVerticalVelocity = -2f;
    private PlayerActionController actionController;
    private CharacterController characterController;
    private float verticalVelocity;
    private Camera movementCamera;
    private Transform movementCameraTransform;

    public float CurrentMoveSpeed { get; private set; }
    public bool IsRunning { get; private set; }
    public float RunSpeed => speed * runSpeedMultiplier;

    private void Awake()
    {
        actionController = GetComponent<PlayerActionController>();
        if (!TryResolveController(out string error))
        {
            Debug.LogError(error, this);
            enabled = false;
        }
    }

    void Update()
    {
        StepMove(GameInputBindings.ReadMovement(), Time.deltaTime, IsRunKeyHeld());
    }

    /// <summary>Uses the same input, movement and collision path as Update; disabled movement stays locked.</summary>
    public void StepMove(Vector2 moveInput, float deltaTime, bool runRequested)
    {
        if (!isActiveAndEnabled)
        {
            return;
        }

        if (float.IsNaN(deltaTime) || float.IsInfinity(deltaTime) || deltaTime < 0f)
        {
            throw new System.ArgumentOutOfRangeException(nameof(deltaTime));
        }

        if (!TryResolveController(out string error))
        {
            Debug.LogError(error, this);
            enabled = false;
            return;
        }
        if (!characterController.enabled)
        {
            ResetMotion();
            return;
        }
        if (deltaTime == 0f)
        {
            return;
        }

        Transform cameraTransform = ResolveMovementCamera();
        Vector3 inputDirection = cameraTransform != null
            ? CalculateCameraRelativeDirection(moveInput, cameraTransform.rotation)
            : Vector3.zero;
        if (inputDirection.sqrMagnitude > 0f)
        {
            actionController.CancelActive(PlayerActionCancelReason.MovementInput);
        }

        UpdateFacingDirection(inputDirection, deltaTime);

        runRequested &= inputDirection.sqrMagnitude > 0f;
        float requestedSpeed = runRequested ? RunSpeed : speed;
        Vector3 movement = inputDirection * requestedSpeed * deltaTime;
        if (characterController.isGrounded && verticalVelocity <= 0f)
        {
            verticalVelocity = GroundedVerticalVelocity;
        }
        verticalVelocity += Physics.gravity.y * deltaTime;
        movement.y = verticalVelocity * deltaTime;

        Vector3 startPosition = transform.position;
        CollisionFlags collisions = characterController.Move(movement);
        if ((collisions & CollisionFlags.Below) != 0 && verticalVelocity < 0f)
        {
            verticalVelocity = GroundedVerticalVelocity;
        }
        if ((collisions & CollisionFlags.Above) != 0 && verticalVelocity > 0f)
        {
            verticalVelocity = 0f;
        }

        // Settling onto the ground must not play the walking animation.
        Vector3 horizontalDisplacement = transform.position - startPosition;
        horizontalDisplacement.y = 0f;
        bool moved = inputDirection.sqrMagnitude > 0f && horizontalDisplacement.sqrMagnitude > 0.000001f;
        IsRunning = moved && runRequested;
        CurrentMoveSpeed = moved ? requestedSpeed : 0f;
        UpdateAnimation(moved ? (IsRunning ? runSpeedMultiplier : 1f) : 0f);
    }

    /// <summary>
    /// Moves the same Player at a scene/checkpoint boundary and resets the controller's
    /// motion state. Movement and controller enable states remain owned by their callers.
    /// </summary>
    public bool TryTeleport(Vector3 position, Quaternion rotation, out string error)
    {
        float rotationLengthSquared = Quaternion.Dot(rotation, rotation);
        if (!IsFinite(position.x) || !IsFinite(position.y) || !IsFinite(position.z) ||
            !IsFinite(rotation.x) || !IsFinite(rotation.y) || !IsFinite(rotation.z) ||
            !IsFinite(rotation.w) || !IsFinite(rotationLengthSquared) || rotationLengthSquared <= 0f)
        {
            error = "Player teleport requires a finite position and a valid rotation.";
            return false;
        }
        if (!TryResolveController(out error))
        {
            Debug.LogError(error, this);
            enabled = false;
            return false;
        }

        bool controllerWasEnabled = characterController.enabled;
        characterController.enabled = false;
        try
        {
            ResetMotion();
            transform.SetPositionAndRotation(position, rotation);
            Rigidbody body = GetComponent<Rigidbody>();
            if (body != null && !body.isKinematic)
            {
                body.linearVelocity = Vector3.zero;
                body.angularVelocity = Vector3.zero;
            }
            Physics.SyncTransforms();
        }
        finally
        {
            characterController.enabled = controllerWasEnabled;
        }

        error = null;
        return true;
    }

    /// <summary>
    /// Converts screen-relative input into a unit XZ direction. Camera pitch does not
    /// change ground speed. The gameplay camera's supported pitch is 10 to 80 degrees;
    /// an unavailable/degenerate ground basis produces no movement, not a world-axis fallback.
    /// </summary>
    public static Vector3 CalculateCameraRelativeDirection(Vector2 input, Quaternion cameraRotation)
    {
        if (input.sqrMagnitude <= 0f || float.IsNaN(input.x) || float.IsNaN(input.y) ||
            float.IsInfinity(input.x) || float.IsInfinity(input.y))
        {
            return Vector3.zero;
        }

        Vector3 right = Vector3.ProjectOnPlane(cameraRotation * Vector3.right, Vector3.up);
        if (!(right.sqrMagnitude > 0.000001f))
        {
            return Vector3.zero;
        }
        right.Normalize();

        Vector3 forward = Vector3.ProjectOnPlane(cameraRotation * Vector3.forward, Vector3.up);
        forward -= right * Vector3.Dot(forward, right);
        if (!(forward.sqrMagnitude > 0.000001f))
        {
            return Vector3.zero;
        }
        forward.Normalize();
        return (right * input.x + forward * input.y).normalized;
    }

    private Transform ResolveMovementCamera()
    {
        PersistentGameplayShell shell = PersistentGameplayShell.Instance;
        Camera currentCamera = shell != null ? shell.PlayerCamera : null;
        if (movementCamera != currentCamera)
        {
            movementCamera = currentCamera;
            movementCameraTransform = currentCamera != null ? currentCamera.transform : null;
        }
        return movementCamera != null && movementCamera.isActiveAndEnabled ? movementCameraTransform : null;
    }

    void OnDisable()
    {
        ResetMotion();
    }

    private void ResetMotion()
    {
        verticalVelocity = 0f;
        CurrentMoveSpeed = 0f;
        IsRunning = false;
        UpdateAnimation(0f);
    }

    private bool IsRunKeyHeld()
    {
        return GameInputBindings.IsPressed(GameInputActionId.Run);
    }

    private void UpdateFacingDirection(Vector3 inputDirection, float deltaTime)
    {
        if (inputDirection.sqrMagnitude <= 0f)
        {
            return;
        }

        if (characterAnimator == null)
        {
            return;
        }

        Transform characterTransform = characterAnimator.transform;
        Quaternion targetRotation = Quaternion.LookRotation(inputDirection, Vector3.up);
        characterTransform.rotation = Quaternion.RotateTowards(
            characterTransform.rotation,
            targetRotation,
            turnSpeedDegreesPerSecond * deltaTime);
    }

    private void UpdateAnimation(float locomotionSpeed)
    {
        if (characterAnimator == null || !characterAnimator.isActiveAndEnabled)
        {
            return;
        }

        characterAnimator.SetFloat(LocomotionSpeedHash, locomotionSpeed);
    }

    private bool TryResolveController(out string error)
    {
        if (characterController == null)
        {
            characterController = GetComponent<CharacterController>();
        }
        error = characterController != null
            ? null
            : "PlayerMovement requires a CharacterController on the same Player. Movement is disabled.";
        return characterController != null;
    }

    private static bool IsFinite(float value)
    {
        return !float.IsNaN(value) && !float.IsInfinity(value);
    }
}
