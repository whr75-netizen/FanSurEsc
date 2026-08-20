using UnityEngine;

[DisallowMultipleComponent]
public sealed class EnemyPatrol : MonoBehaviour
{
    public const string IsMovingParameter = "IsMoving";

    [SerializeField] private Transform agent;
    [SerializeField] private Animator animator;
    [SerializeField] private Vector3[] localWaypoints =
    {
        new Vector3(-2f, 0f, 0f),
        new Vector3(2f, 0f, 0f)
    };
    [SerializeField, Min(0f)] private float moveSpeed = 1.5f;
    [SerializeField, Min(0f)] private float turnSpeedDegreesPerSecond = 540f;
    [SerializeField, Min(0f)] private float arrivalDistance = 0.05f;
    [SerializeField, Min(0f)] private float waypointWaitSeconds = 0.5f;

    private static readonly int IsMovingHash = Animator.StringToHash(IsMovingParameter);

    private int currentWaypointIndex;
    private float waitSecondsRemaining;

    public Transform Agent => agent;
    public int CurrentWaypointIndex => currentWaypointIndex;
    public bool IsMoving { get; private set; }

    private void Awake()
    {
        if (!HasValidConfiguration())
        {
            enabled = false;
            return;
        }

        currentWaypointIndex = FindNearestWaypointIndex(agent.localPosition);
    }

    private void OnEnable()
    {
        waitSecondsRemaining = 0f;
        SetMoving(false);
    }

    private void Update()
    {
        if (waitSecondsRemaining > 0f)
        {
            waitSecondsRemaining = Mathf.Max(0f, waitSecondsRemaining - Time.deltaTime);
            SetMoving(false);
            return;
        }

        Vector3 targetPosition = localWaypoints[currentWaypointIndex];
        Vector3 toTarget = targetPosition - agent.localPosition;
        toTarget.y = 0f;

        if (toTarget.sqrMagnitude <= arrivalDistance * arrivalDistance)
        {
            agent.localPosition = targetPosition;
            currentWaypointIndex = (currentWaypointIndex + 1) % localWaypoints.Length;
            waitSecondsRemaining = waypointWaitSeconds;
            SetMoving(false);
            return;
        }

        Vector3 direction = toTarget.normalized;
        Quaternion targetRotation = Quaternion.LookRotation(direction, Vector3.up);
        agent.localRotation = Quaternion.RotateTowards(
            agent.localRotation,
            targetRotation,
            turnSpeedDegreesPerSecond * Time.deltaTime);

        agent.localPosition = Vector3.MoveTowards(
            agent.localPosition,
            targetPosition,
            moveSpeed * Time.deltaTime);
        SetMoving(true);
    }

    private void OnDisable()
    {
        SetMoving(false);
    }

    private bool HasValidConfiguration()
    {
        if (agent == null)
        {
            Debug.LogError($"{nameof(EnemyPatrol)} on '{name}' requires an agent Transform.", this);
            return false;
        }

        if (localWaypoints == null || localWaypoints.Length < 2)
        {
            Debug.LogError($"{nameof(EnemyPatrol)} on '{name}' requires at least two local waypoints.", this);
            return false;
        }

        return true;
    }

    private int FindNearestWaypointIndex(Vector3 position)
    {
        int nearestIndex = 0;
        float nearestDistanceSquared = float.PositiveInfinity;

        for (int index = 0; index < localWaypoints.Length; index++)
        {
            float distanceSquared = (localWaypoints[index] - position).sqrMagnitude;
            if (distanceSquared < nearestDistanceSquared)
            {
                nearestIndex = index;
                nearestDistanceSquared = distanceSquared;
            }
        }

        return nearestIndex;
    }

    private void SetMoving(bool moving)
    {
        IsMoving = moving;
        if (animator != null && animator.isActiveAndEnabled)
        {
            animator.SetBool(IsMovingHash, moving);
        }
    }
}
