using FantasySurvival.Actions;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(PlayerActionController))]
public class PlayerMovement : MonoBehaviour
{
    public const string LocomotionSpeedParameter = "LocomotionSpeed";

    public float speed = 5f;
    public Vector3 checkSize = new Vector3(0.5f, 0.5f, 0.5f);

    [SerializeField, Min(1f)] private float runSpeedMultiplier = 1.3f;
    [SerializeField] private KeyCode primaryRunKey = KeyCode.LeftShift;
    [SerializeField] private KeyCode secondaryRunKey = KeyCode.RightShift;
    [SerializeField] private Animator characterAnimator;
    [SerializeField, Min(0f)] private float turnSpeedDegreesPerSecond = 1080f;

    private static readonly int LocomotionSpeedHash = Animator.StringToHash(LocomotionSpeedParameter);
    private PlayerActionController actionController;

    public float CurrentMoveSpeed { get; private set; }
    public bool IsRunning { get; private set; }
    public float RunSpeed => speed * runSpeedMultiplier;

    private void Awake()
    {
        actionController = GetComponent<PlayerActionController>();
    }

    void Update()
    {
        float moveX = Input.GetAxisRaw("Horizontal");
        float moveZ = Input.GetAxisRaw("Vertical");
        Vector3 inputDirection = new Vector3(moveX, 0, moveZ).normalized;
        if (inputDirection.sqrMagnitude > 0f)
        {
            actionController.CancelActive(PlayerActionCancelReason.MovementInput);
        }

        UpdateFacingDirection(inputDirection);

        bool runRequested = inputDirection.sqrMagnitude > 0f && IsRunKeyHeld();
        float requestedSpeed = runRequested ? RunSpeed : speed;
        Vector3 movement = inputDirection * requestedSpeed * Time.deltaTime;

        Vector3 startPosition = transform.position;
        Vector3 nextPosition = transform.position;
        if (moveX != 0 && !IsColliding(new Vector3(movement.x, 0, 0)))
        {
            nextPosition.x += movement.x;
        }
        if (moveZ != 0 && !IsColliding(new Vector3(0, 0, movement.z)))
        {
            nextPosition.z += movement.z;
        }
        transform.position = nextPosition;

        bool moved = (nextPosition - startPosition).sqrMagnitude > 0.000001f;
        IsRunning = moved && runRequested;
        CurrentMoveSpeed = moved ? requestedSpeed : 0f;
        UpdateAnimation(moved ? (IsRunning ? runSpeedMultiplier : 1f) : 0f);
    }

    void OnDisable()
    {
        CurrentMoveSpeed = 0f;
        IsRunning = false;
        UpdateAnimation(0f);
    }

    private bool IsRunKeyHeld()
    {
        return Input.GetKey(primaryRunKey) || Input.GetKey(secondaryRunKey);
    }

    private void UpdateFacingDirection(Vector3 inputDirection)
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
            turnSpeedDegreesPerSecond * Time.deltaTime);
    }

    private void UpdateAnimation(float locomotionSpeed)
    {
        if (characterAnimator == null || !characterAnimator.isActiveAndEnabled)
        {
            return;
        }

        characterAnimator.SetFloat(LocomotionSpeedHash, locomotionSpeed);
    }

    bool IsColliding(Vector3 movement)
    {
        Vector3 nextPosition = transform.position + movement;
        Collider[] obstacles = Physics.OverlapBox(nextPosition, checkSize, Quaternion.identity);
        foreach (Collider obstacle in obstacles)
        {
            if (obstacle.CompareTag("Obstacle"))
            {
                return true;
            }
        }
        return false;
    }
}
