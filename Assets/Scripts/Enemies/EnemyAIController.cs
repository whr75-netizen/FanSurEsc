using System;
using FantasySurvival.AI;
using FantasySurvival.Combat;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.AI;

public enum EnemyAwarenessState
{
    AwaitingNavigation,
    Patrol,
    Investigate,
    SearchLastKnown,
    Combat,
    Dead
}

[DisallowMultipleComponent]
[RequireComponent(typeof(EnemyStats))]
[RequireComponent(typeof(NavMeshAgent))]
public sealed class EnemyAIController : MonoBehaviour
{
    public const string IsMovingParameter = "IsMoving";

    private const int RaycastBufferSize = 16;
    private const int PatrolCandidateAttempts = 8;
    private const int RecentPatrolPointCount = 2;
    private const float ArrivalTolerance = 0.2f;

    [Header("Owned Entity Components")]
    [SerializeField] private EnemyStats stats;
    [SerializeField] private NavMeshAgent agent;
    [SerializeField] private EnemyCombatAction combatAction;
    [SerializeField] private Animator movementAnimator;

    [Header("Scene Queries")]
    [SerializeField] private LayerMask sightAndShotMask = ~0;
    [SerializeField, Min(0f)] private float eyeHeight = 1.5f;
    [SerializeField, Min(0f)] private float targetAimHeight = 0.5f;
    [SerializeField, Min(0.1f)] private float navMeshPlacementRadius = 3f;
    [SerializeField, Min(0f)] private float initialThinkDelay = 0.2f;

    private static readonly int IsMovingHash = Animator.StringToHash(IsMovingParameter);

    private readonly RaycastHit[] raycastHits = new RaycastHit[RaycastBufferSize];
    private readonly Vector3[] recentPatrolPoints = new Vector3[RecentPatrolPointCount];

    private System.Random patrolRandom;
    private NavMeshPath patrolPath;
    private Transform playerTransform;
    private IDamageable playerDamageable;
    private Transform currentTarget;
    private IDamageable currentTargetDamageable;
    private IEnemyPatrolPointSource patrolPointSource;
    private EnemyAISettings settings;
    private Vector3 homePosition;
    private Vector3 lastKnownPosition;
    private Vector3 lastMoveDestination;
    private Vector3 manualFacingTarget;
    private float lastSeenTime = float.NegativeInfinity;
    private float lastHeardTime = float.NegativeInfinity;
    private float nextThinkTime;
    private float nextPerceptionTime;
    private float lastThinkTime;
    private float nextNavigationRetryTime;
    private float nextRepathTime;
    private float patrolWaitUntil;
    private int recentPatrolPointWriteIndex;
    private bool hasPatrolDestination;
    private bool hasMoveDestination;
    private bool hasManualFacing;
    private bool cachedPlayerVisible;
    private bool navigationHomeInitialized;
    private bool movingPresentation;
    private bool configurationValid;
    private bool patrolPointSourceRequired;

    public EnemyAwarenessState State { get; private set; } = EnemyAwarenessState.AwaitingNavigation;
    public EnemyAISettings Settings => settings;
    public Vector3 Position => transform.position;
    public Vector3 LastKnownPosition => lastKnownPosition;
    public Transform CurrentTarget => currentTarget;
    public bool IsNavigationReady => agent != null && agent.enabled && agent.isOnNavMesh;
    public int RangedShotsAttempted { get; private set; }
    public int RangedHitsApplied { get; private set; }
    public bool HasRequiredPatrolPointSourceBinding =>
        patrolPointSourceRequired &&
        patrolPointSource != null &&
        (!(patrolPointSource is UnityEngine.Object sourceObject) || sourceObject != null);

    /// <summary>
    /// Explicitly supplies map-derived patrol points. Procedural maps set
    /// <paramref name="requireSource"/> so an unavailable derived layout cannot be hidden by
    /// unrelated random NavMesh patrol. Fixed maps leave the source unbound and retain the
    /// existing random patrol behavior.
    /// </summary>
    public void BindPatrolPointSource(IEnemyPatrolPointSource source, bool requireSource)
    {
        patrolPointSource = source;
        patrolPointSourceRequired = requireSource;

        if (Application.isPlaying && State == EnemyAwarenessState.Patrol)
        {
            hasPatrolDestination = false;
            patrolWaitUntil = Time.time;
            TryStopAgent();
        }
    }

    private void Awake()
    {
        ResolveLocalReferences();
        configurationValid = ValidateConfiguration();
        if (!configurationValid)
        {
            enabled = false;
            return;
        }

        settings = stats.Definition.AI;
        homePosition = transform.position;
        patrolPath = new NavMeshPath();
        patrolRandom = new System.Random(CreatePatrolSeed());
        ConfigureAgent();
    }

    private void OnEnable()
    {
        if (!configurationValid)
        {
            return;
        }

        // OnEnable can run before another component's Awake during scene loading.
        // Treat only an already-initialized dead entity as permanently inactive.
        if (stats.IsInitialized && !stats.IsAlive)
        {
            State = EnemyAwarenessState.Dead;
            return;
        }

        State = EnemyAwarenessState.AwaitingNavigation;
        hasPatrolDestination = false;
        hasMoveDestination = false;
        hasManualFacing = false;
        cachedPlayerVisible = false;
        patrolWaitUntil = Time.time;

        stats.DamageApplied += HandleDamageApplied;
        stats.Died += HandleDeath;
        WorldStimulusChannel.Emitted += HandleWorldStimulus;

        int entityHash = GetEntityId().GetHashCode();
        float stagger = Mathf.Abs(entityHash % 1000) / 1000f * settings.NonCombatThinkInterval;
        nextThinkTime = Time.time + initialThinkDelay + stagger;
        nextPerceptionTime = nextThinkTime;
        lastThinkTime = nextThinkTime;
    }

    private void OnDisable()
    {
        if (stats != null)
        {
            stats.DamageApplied -= HandleDamageApplied;
            stats.Died -= HandleDeath;
        }

        WorldStimulusChannel.Emitted -= HandleWorldStimulus;
        combatAction?.EndCombat();
        TryStopAgent();
        hasPatrolDestination = false;
        hasMoveDestination = false;
        hasManualFacing = false;
        cachedPlayerVisible = false;
        patrolWaitUntil = 0f;

        if (movingPresentation && movementAnimator != null &&
            movementAnimator.isActiveAndEnabled &&
            movementAnimator.runtimeAnimatorController != null &&
            movementAnimator.isInitialized)
        {
            movementAnimator.SetBool(IsMovingHash, false);
        }

        movingPresentation = false;
    }

    private void Update()
    {
        UpdateManualFacing();
        UpdateMovementPresentation();

        if (!configurationValid || !stats.IsAlive || Time.time < nextThinkTime)
        {
            return;
        }

        float currentTime = Time.time;
        float deltaTime = Mathf.Max(0f, currentTime - lastThinkTime);
        lastThinkTime = currentTime;

        if (!EnsureNavigationReady(currentTime))
        {
            nextThinkTime = currentTime + settings.NonCombatThinkInterval;
            return;
        }

        ResolvePlayerTarget();
        TickPerception(currentTime);

        if (cachedPlayerVisible && playerDamageable != null && playerDamageable.IsAlive)
        {
            AdoptPlayerAsTarget(currentTime, playerTransform.position);
            SetState(EnemyAwarenessState.Combat, currentTime, deltaTime);
            combatAction.TickCombat(new EnemyCombatContext(
                this,
                currentTarget,
                currentTargetDamageable,
                currentTime,
                deltaTime));
        }
        else
        {
            TickWithoutConfirmedSight(currentTime);
        }

        float interval = State == EnemyAwarenessState.Combat ||
                         State == EnemyAwarenessState.SearchLastKnown
            ? settings.CombatThinkInterval
            : settings.NonCombatThinkInterval;
        nextThinkTime = currentTime + interval;
    }

    internal bool NavigateTo(
        Vector3 destination,
        float speed,
        float stoppingDistance,
        float currentTime)
    {
        if (!IsNavigationReady)
        {
            return false;
        }

        Vector3 destinationDelta = destination - lastMoveDestination;
        destinationDelta.y = 0f;
        float refreshDistance = settings.DestinationRefreshDistance;
        bool destinationMoved = !hasMoveDestination ||
                                destinationDelta.sqrMagnitude >= refreshDistance * refreshDistance;
        if (!destinationMoved && currentTime < nextRepathTime)
        {
            return true;
        }

        agent.speed = speed;
        agent.stoppingDistance = Mathf.Max(0f, stoppingDistance);
        agent.isStopped = false;
        hasManualFacing = false;

        if (agent.SetDestination(destination))
        {
            lastMoveDestination = destination;
            hasMoveDestination = true;
            nextRepathTime = currentTime + settings.RepathInterval;
            return true;
        }

        return false;
    }

    internal void StopAndFace(Vector3 targetPosition)
    {
        TryStopAgent();
        manualFacingTarget = targetPosition;
        hasManualFacing = true;
    }

    internal Vector3 GetTargetAimPoint(Transform target)
    {
        return target.position + Vector3.up * targetAimHeight;
    }

    internal bool HasClearLineToTarget(Transform target)
    {
        if (target == null)
        {
            return false;
        }

        Vector3 origin = GetEyePosition();
        Vector3 toTarget = GetTargetAimPoint(target) - origin;
        float distance = toTarget.magnitude;
        if (distance <= 0.001f)
        {
            return true;
        }

        if (!Physics.Raycast(
                origin,
                toTarget / distance,
                out RaycastHit hit,
                distance,
                sightAndShotMask,
                QueryTriggerInteraction.Ignore))
        {
            return true;
        }

        Transform hitTransform = hit.collider != null ? hit.collider.transform : null;
        return hitTransform != null &&
               (hitTransform == target || hitTransform.IsChildOf(target));
    }

    internal bool TryFireRangedShot(
        Vector3 aimPoint,
        IDamageable intendedTarget,
        float range,
        float damage)
    {
        RangedShotsAttempted++;
        Vector3 origin = GetEyePosition();
        Vector3 direction = aimPoint - origin;
        if (direction.sqrMagnitude <= 0.0001f)
        {
            return false;
        }

        direction.Normalize();
        int hitCount = Physics.RaycastNonAlloc(
            origin,
            direction,
            raycastHits,
            range,
            sightAndShotMask,
            QueryTriggerInteraction.Ignore);

        RaycastHit[] hits = raycastHits;
        if (hitCount == raycastHits.Length)
        {
            hits = Physics.RaycastAll(
                origin,
                direction,
                range,
                sightAndShotMask,
                QueryTriggerInteraction.Ignore);
            hitCount = hits.Length;
        }

        float nearestDistance = float.PositiveInfinity;
        RaycastHit nearestHit = default;
        bool foundHit = false;

        for (int index = 0; index < hitCount; index++)
        {
            RaycastHit hit = hits[index];
            Collider hitCollider = hit.collider;
            if (hitCollider == null || hitCollider.transform.IsChildOf(transform) ||
                hit.distance >= nearestDistance)
            {
                continue;
            }

            nearestDistance = hit.distance;
            nearestHit = hit;
            foundHit = true;
        }

        if (!foundHit)
        {
            return false;
        }

        IDamageable hitDamageable = nearestHit.collider.GetComponentInParent<IDamageable>();
        if (!ReferenceEquals(hitDamageable, intendedTarget) || !intendedTarget.IsAlive)
        {
            return false;
        }

        DamageResult result = intendedTarget.ApplyDamage(new DamageContext(
            damage,
            gameObject,
            nearestHit.point));
        if (result.WasApplied)
        {
            RangedHitsApplied++;
        }

        return result.WasApplied;
    }

    private void ResolveLocalReferences()
    {
        if (stats == null)
        {
            stats = GetComponent<EnemyStats>();
        }

        if (agent == null)
        {
            agent = GetComponent<NavMeshAgent>();
        }

        if (combatAction == null)
        {
            combatAction = GetComponent<EnemyCombatAction>();
        }
    }

    private bool ValidateConfiguration()
    {
        if (stats == null || agent == null || combatAction == null ||
            stats.Definition == null || stats.Definition.AI == null)
        {
            Debug.LogError($"{nameof(EnemyAIController)} on '{name}' has missing required references.", this);
            return false;
        }

        if (combatAction.Archetype != stats.Definition.AI.CombatArchetype)
        {
            Debug.LogError(
                $"{nameof(EnemyAIController)} on '{name}' has combat action " +
                $"'{combatAction.Archetype}' but definition expects '{stats.Definition.AI.CombatArchetype}'.",
                this);
            return false;
        }

        return true;
    }

    private void ConfigureAgent()
    {
        agent.speed = settings.PatrolSpeed;
        agent.acceleration = settings.Acceleration;
        agent.angularSpeed = settings.AngularSpeed;
        agent.autoBraking = true;
        agent.updateRotation = true;
    }

    private bool EnsureNavigationReady(float currentTime)
    {
        if (IsNavigationReady)
        {
            return true;
        }

        SetState(EnemyAwarenessState.AwaitingNavigation, currentTime, 0f);
        if (agent == null || currentTime < nextNavigationRetryTime)
        {
            return false;
        }

        nextNavigationRetryTime = currentTime + 0.25f;
        if (!NavMesh.SamplePosition(
                transform.position,
                out NavMeshHit hit,
                navMeshPlacementRadius,
                agent.areaMask))
        {
            return false;
        }

        if (!agent.enabled)
        {
            transform.position = hit.position;
            agent.enabled = true;
        }

        if (!agent.isOnNavMesh && !agent.Warp(hit.position))
        {
            agent.enabled = false;
            return false;
        }

        if (!navigationHomeInitialized)
        {
            homePosition = hit.position;
            navigationHomeInitialized = true;
        }

        SetState(EnemyAwarenessState.Patrol, currentTime, 0f);
        return agent.isOnNavMesh;
    }

    private void ResolvePlayerTarget()
    {
        PersistentGameplayShell shell = PersistentGameplayShell.Instance;
        Transform shellPlayer = shell != null ? shell.PlayerTransform : null;
        if (shellPlayer == playerTransform && playerDamageable != null)
        {
            return;
        }

        playerTransform = shellPlayer;
        playerDamageable = playerTransform != null
            ? playerTransform.GetComponent<IDamageable>()
            : null;

        if (currentTarget != null && currentTarget != playerTransform)
        {
            ClearTarget();
        }
    }

    private void TickPerception(float currentTime)
    {
        if (currentTime < nextPerceptionTime)
        {
            return;
        }

        nextPerceptionTime = currentTime + settings.PerceptionInterval;
        cachedPlayerVisible = CanSeePlayer();
    }

    private bool CanSeePlayer()
    {
        if (playerTransform == null || playerDamageable == null || !playerDamageable.IsAlive)
        {
            return false;
        }

        Vector3 origin = GetEyePosition();
        Vector3 targetPoint = GetTargetAimPoint(playerTransform);
        Vector3 toTarget = targetPoint - origin;
        Vector3 planarDirection = toTarget;
        planarDirection.y = 0f;

        float distanceSquared = planarDirection.sqrMagnitude;
        if (distanceSquared > settings.VisionRange * settings.VisionRange)
        {
            return false;
        }

        if (distanceSquared > settings.ProximityAwarenessRange * settings.ProximityAwarenessRange &&
            settings.VisionAngle < 359.9f)
        {
            float minimumDot = Mathf.Cos(settings.VisionAngle * 0.5f * Mathf.Deg2Rad);
            float facingDot = Vector3.Dot(transform.forward, planarDirection.normalized);
            if (facingDot < minimumDot)
            {
                return false;
            }
        }

        return HasClearLineToTarget(playerTransform);
    }

    private void AdoptPlayerAsTarget(float currentTime, Vector3 observedPosition)
    {
        currentTarget = playerTransform;
        currentTargetDamageable = playerDamageable;
        lastKnownPosition = observedPosition;
        lastSeenTime = currentTime;
    }

    private void TickWithoutConfirmedSight(float currentTime)
    {
        if (currentTargetDamageable != null && !currentTargetDamageable.IsAlive)
        {
            ClearTarget();
        }

        if (currentTarget != null && currentTime - lastSeenTime <= settings.TargetMemorySeconds)
        {
            SetState(EnemyAwarenessState.SearchLastKnown, currentTime, 0f);
            NavigateTo(lastKnownPosition, settings.CombatSpeed, 0.15f, currentTime);
            return;
        }

        if (currentTime - lastHeardTime <= settings.TargetMemorySeconds)
        {
            ClearTarget();
            SetState(EnemyAwarenessState.Investigate, currentTime, 0f);
            NavigateTo(lastKnownPosition, settings.PatrolSpeed, 0.15f, currentTime);
            return;
        }

        ClearTarget();
        SetState(EnemyAwarenessState.Patrol, currentTime, 0f);
        TickPatrol(currentTime);
    }

    private void TickPatrol(float currentTime)
    {
        if (settings.PatrolRadius <= 0f)
        {
            TryStopAgent();
            return;
        }

        if (hasPatrolDestination && HasArrived())
        {
            hasPatrolDestination = false;
            TryStopAgent();
            patrolWaitUntil = currentTime + NextFloat(
                settings.PatrolWaitMinSeconds,
                settings.PatrolWaitMaxSeconds);
            return;
        }

        if (hasPatrolDestination || currentTime < patrolWaitUntil)
        {
            return;
        }

        if (!TryChoosePatrolDestination(out Vector3 destination))
        {
            TryStopAgent();
            patrolWaitUntil = currentTime + settings.PatrolWaitMaxSeconds;
            return;
        }

        RememberPatrolPoint(destination);
        hasPatrolDestination = NavigateTo(
            destination,
            settings.PatrolSpeed,
            0.1f,
            currentTime);
    }

    private bool TryChoosePatrolDestination(out Vector3 destination)
    {
        if (TryGetReadyPatrolPointSource(out IEnemyPatrolPointSource source))
        {
            if (TryChooseProvidedPatrolDestination(source, out destination))
            {
                return true;
            }

            if (patrolPointSourceRequired)
            {
                destination = default;
                return false;
            }
        }
        else if (patrolPointSourceRequired)
        {
            destination = default;
            return false;
        }

        return TryChooseRandomPatrolDestination(out destination);
    }

    private bool TryChooseProvidedPatrolDestination(
        IEnemyPatrolPointSource source,
        out Vector3 destination)
    {
        int candidateCount = source.PatrolPointCount;
        int startIndex = patrolRandom.Next(0, candidateCount);
        int scanDirection = patrolRandom.Next(0, 2) == 0 ? 1 : -1;
        int pathAttemptCount = 0;

        // Cheap radius/recent-point filters may scan the shared immutable cache, but
        // expensive NavMesh path calculations remain capped at the existing attempt budget.
        for (int scanOffset = 0; scanOffset < candidateCount; scanOffset++)
        {
            int candidateIndex = PositiveModulo(
                startIndex + scanOffset * scanDirection,
                candidateCount);
            if (!source.TryGetPatrolPoint(candidateIndex, out Vector3 candidate))
            {
                continue;
            }

            bool valid = TryValidatePatrolDestination(
                candidate,
                enforceHomeRadius: true,
                out destination,
                out bool pathChecked);
            if (valid)
            {
                return true;
            }

            if (pathChecked && ++pathAttemptCount >= PatrolCandidateAttempts)
            {
                break;
            }
        }

        destination = default;
        return false;
    }

    private bool TryChooseRandomPatrolDestination(out Vector3 destination)
    {
        for (int attempt = 0; attempt < PatrolCandidateAttempts; attempt++)
        {
            float angle = NextFloat(0f, Mathf.PI * 2f);
            float radius = Mathf.Sqrt(NextFloat(0f, 1f)) * settings.PatrolRadius;
            Vector3 candidate = homePosition + new Vector3(
                Mathf.Cos(angle) * radius,
                0f,
                Mathf.Sin(angle) * radius);

            if (!NavMesh.SamplePosition(candidate, out NavMeshHit hit, 1.5f, agent.areaMask))
            {
                continue;
            }

            if (!TryValidatePatrolDestination(
                    hit.position,
                    enforceHomeRadius: false,
                    out destination,
                    out _))
            {
                continue;
            }

            return true;
        }

        destination = default;
        return false;
    }

    private bool TryGetReadyPatrolPointSource(out IEnemyPatrolPointSource source)
    {
        source = patrolPointSource;
        if (source == null ||
            (source is UnityEngine.Object sourceObject && sourceObject == null) ||
            !source.IsPatrolPointSourceReady ||
            source.PatrolPointCount <= 0)
        {
            source = null;
            return false;
        }

        return true;
    }

    private bool TryValidatePatrolDestination(
        Vector3 candidate,
        bool enforceHomeRadius,
        out Vector3 destination,
        out bool pathChecked)
    {
        pathChecked = false;
        if (enforceHomeRadius)
        {
            Vector3 fromHome = candidate - homePosition;
            fromHome.y = 0f;
            if (fromHome.sqrMagnitude > settings.PatrolRadius * settings.PatrolRadius)
            {
                destination = default;
                return false;
            }
        }

        Vector3 fromCurrent = candidate - Position;
        fromCurrent.y = 0f;
        if (fromCurrent.sqrMagnitude <
            settings.PatrolMinimumTravel * settings.PatrolMinimumTravel ||
            IsRecentPatrolPoint(candidate))
        {
            destination = default;
            return false;
        }

        pathChecked = true;
        if (!NavMesh.CalculatePath(Position, candidate, agent.areaMask, patrolPath) ||
            patrolPath.status != NavMeshPathStatus.PathComplete)
        {
            destination = default;
            return false;
        }

        destination = candidate;
        return true;
    }

    private static int PositiveModulo(int value, int modulus)
    {
        int remainder = value % modulus;
        return remainder < 0 ? remainder + modulus : remainder;
    }

    private bool IsRecentPatrolPoint(Vector3 candidate)
    {
        float minimumDistance = Mathf.Max(0.5f, settings.PatrolMinimumTravel * 0.5f);
        float minimumDistanceSquared = minimumDistance * minimumDistance;
        for (int index = 0; index < recentPatrolPoints.Length; index++)
        {
            if (recentPatrolPoints[index] == Vector3.zero)
            {
                continue;
            }

            Vector3 delta = recentPatrolPoints[index] - candidate;
            delta.y = 0f;
            if (delta.sqrMagnitude < minimumDistanceSquared)
            {
                return true;
            }
        }

        return false;
    }

    private void RememberPatrolPoint(Vector3 point)
    {
        recentPatrolPoints[recentPatrolPointWriteIndex] = point;
        recentPatrolPointWriteIndex =
            (recentPatrolPointWriteIndex + 1) % recentPatrolPoints.Length;
    }

    private bool HasArrived()
    {
        return IsNavigationReady && !agent.pathPending && agent.hasPath &&
               agent.remainingDistance <= agent.stoppingDistance + ArrivalTolerance;
    }

    private void SetState(EnemyAwarenessState nextState, float currentTime, float deltaTime)
    {
        if (State == nextState)
        {
            return;
        }

        if (State == EnemyAwarenessState.Combat)
        {
            combatAction.EndCombat();
        }

        State = nextState;
        if (nextState == EnemyAwarenessState.Combat && currentTarget != null &&
            currentTargetDamageable != null)
        {
            combatAction.BeginCombat(new EnemyCombatContext(
                this,
                currentTarget,
                currentTargetDamageable,
                currentTime,
                deltaTime));
        }
        else if (nextState == EnemyAwarenessState.Patrol)
        {
            hasPatrolDestination = false;
            patrolWaitUntil = currentTime;
        }
    }

    private void HandleWorldStimulus(WorldStimulus stimulus)
    {
        if (!configurationValid || !stats.IsAlive || !stimulus.IsValid)
        {
            return;
        }

        ResolvePlayerTarget();
        if (!IsPlayerInstigator(stimulus.Instigator))
        {
            return;
        }

        float audibleRadius = stimulus.Radius * settings.HearingMultiplier;
        Vector3 delta = stimulus.Position - Position;
        delta.y = 0f;
        if (delta.sqrMagnitude > audibleRadius * audibleRadius)
        {
            return;
        }

        float currentTime = Time.time;
        lastKnownPosition = stimulus.Position;
        lastHeardTime = currentTime;

        if (stimulus.Response == WorldStimulusResponse.EngageInstigator &&
            playerTransform != null && playerDamageable != null && playerDamageable.IsAlive)
        {
            currentTarget = playerTransform;
            currentTargetDamageable = playerDamageable;
            lastSeenTime = currentTime;
            SetState(EnemyAwarenessState.SearchLastKnown, currentTime, 0f);
        }
        else if (State != EnemyAwarenessState.Combat)
        {
            SetState(EnemyAwarenessState.Investigate, currentTime, 0f);
        }

        nextThinkTime = Mathf.Min(nextThinkTime, currentTime);
    }

    private void HandleDamageApplied(
        EnemyStats damagedStats,
        DamageContext context,
        DamageResult result)
    {
        if (damagedStats != stats || !result.WasApplied || result.CausedDeath)
        {
            return;
        }

        ResolvePlayerTarget();
        if (!IsPlayerInstigator(context.Source) || playerTransform == null ||
            playerDamageable == null || !playerDamageable.IsAlive)
        {
            return;
        }

        float currentTime = Time.time;
        currentTarget = playerTransform;
        currentTargetDamageable = playerDamageable;
        lastKnownPosition = playerTransform.position;
        lastSeenTime = currentTime;
        SetState(EnemyAwarenessState.SearchLastKnown, currentTime, 0f);
        nextThinkTime = Mathf.Min(nextThinkTime, currentTime);
    }

    private void HandleDeath(EnemyStats deadStats, DamageContext context)
    {
        if (deadStats != stats)
        {
            return;
        }

        SetState(EnemyAwarenessState.Dead, Time.time, 0f);
        ClearTarget();
        TryStopAgent();
    }

    private bool IsPlayerInstigator(GameObject instigator)
    {
        if (instigator == null || playerTransform == null)
        {
            return false;
        }

        Transform instigatorTransform = instigator.transform;
        return instigatorTransform == playerTransform ||
               instigatorTransform.IsChildOf(playerTransform) ||
               playerTransform.IsChildOf(instigatorTransform);
    }

    private void ClearTarget()
    {
        currentTarget = null;
        currentTargetDamageable = null;
        cachedPlayerVisible = false;
    }

    private void TryStopAgent()
    {
        hasMoveDestination = false;
        if (agent == null || !agent.enabled || !agent.isOnNavMesh)
        {
            return;
        }

        if (!agent.isStopped)
        {
            agent.isStopped = true;
        }

        if (agent.hasPath)
        {
            agent.ResetPath();
        }
    }

    private Vector3 GetEyePosition()
    {
        return Position + Vector3.up * eyeHeight;
    }

    private void UpdateManualFacing()
    {
        if (!hasManualFacing || !stats.IsAlive)
        {
            return;
        }

        Vector3 direction = manualFacingTarget - Position;
        direction.y = 0f;
        if (direction.sqrMagnitude <= 0.0001f)
        {
            return;
        }

        Quaternion targetRotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        transform.rotation = Quaternion.RotateTowards(
            transform.rotation,
            targetRotation,
            settings.AngularSpeed * Time.deltaTime);
    }

    private void UpdateMovementPresentation()
    {
        bool isMoving = IsNavigationReady && !agent.isStopped &&
                        agent.velocity.sqrMagnitude > 0.01f;
        if (movingPresentation == isMoving)
        {
            return;
        }

        movingPresentation = isMoving;
        if (movementAnimator != null && movementAnimator.isActiveAndEnabled &&
            movementAnimator.runtimeAnimatorController != null && movementAnimator.isInitialized)
        {
            movementAnimator.SetBool(IsMovingHash, isMoving);
        }
    }

    private int CreatePatrolSeed()
    {
        unchecked
        {
            int seed = GetEntityId().GetHashCode();
            seed = seed * 397 ^ Mathf.RoundToInt(homePosition.x * 10f);
            seed = seed * 397 ^ Mathf.RoundToInt(homePosition.z * 10f);
            return seed;
        }
    }

    private float NextFloat(float minimum, float maximum)
    {
        if (maximum <= minimum)
        {
            return minimum;
        }

        return minimum + (float)patrolRandom.NextDouble() * (maximum - minimum);
    }

#if UNITY_EDITOR
    private void OnValidate()
    {
        ResolveLocalReferences();
        eyeHeight = Mathf.Max(0f, eyeHeight);
        targetAimHeight = Mathf.Max(0f, targetAimHeight);
        navMeshPlacementRadius = Mathf.Max(0.1f, navMeshPlacementRadius);
        initialThinkDelay = Mathf.Max(0f, initialThinkDelay);
    }
#endif
}
