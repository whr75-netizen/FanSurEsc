using System;
using FantasySurvival.Combat;
using UnityEngine;

public enum EnemyCombatArchetype
{
    MeleeRush,
    RangedPursuit
}

[Serializable]
public sealed class EnemyAISettings
{
    [Header("Archetype")]
    [SerializeField] private EnemyCombatArchetype combatArchetype;

    [Header("Perception And Memory")]
    [SerializeField, Min(0.1f)] private float visionRange = 12f;
    [SerializeField, Range(0f, 360f)] private float visionAngle = 180f;
    [SerializeField, Min(0f)] private float proximityAwarenessRange = 2.5f;
    [SerializeField, Min(0.05f)] private float perceptionInterval = 0.2f;
    [SerializeField, Min(0f)] private float targetMemorySeconds = 5f;
    [SerializeField, Min(0f)] private float hearingMultiplier = 1f;

    [Header("Patrol")]
    [SerializeField, Min(0f)] private float patrolRadius = 6f;
    [SerializeField, Min(0f)] private float patrolMinimumTravel = 2f;
    [SerializeField, Min(0f)] private float patrolWaitMinSeconds = 0.5f;
    [SerializeField, Min(0f)] private float patrolWaitMaxSeconds = 1.5f;
    [SerializeField, Min(0.05f)] private float nonCombatThinkInterval = 0.5f;

    [Header("Navigation")]
    [SerializeField, Min(0f)] private float patrolSpeed = 1.5f;
    [SerializeField, Min(0f)] private float combatSpeed = 3.2f;
    [SerializeField, Min(0f)] private float acceleration = 14f;
    [SerializeField, Min(0f)] private float angularSpeed = 720f;
    [SerializeField, Min(0.05f)] private float combatThinkInterval = 0.15f;
    [SerializeField, Min(0.05f)] private float repathInterval = 0.2f;
    [SerializeField, Min(0f)] private float destinationRefreshDistance = 0.5f;

    [Header("Attack")]
    [SerializeField, Min(0.1f)] private float attackRange = 1.35f;
    [SerializeField, Min(0f)] private float preferredRange = 1f;
    [SerializeField, Min(0f)] private float attackDamage = 10f;
    [SerializeField, Min(0.05f)] private float attackCooldownSeconds = 1f;

    [Header("Ranged Virtual Aim")]
    [SerializeField, Min(0f)] private float aimTrackingSpeed = 7f;
    [SerializeField, Min(0f)] private float aimSettleSeconds = 0.8f;
    [SerializeField, Min(0f)] private float initialAimErrorRadius = 1.4f;
    [SerializeField, Min(0f)] private float settledAimErrorRadius = 0.15f;
    [SerializeField, Min(0f)] private float movingAimErrorPenalty = 0.55f;
    [SerializeField, Min(0.01f)] private float aimDriftFrequency = 0.7f;

    public EnemyCombatArchetype CombatArchetype => combatArchetype;
    public float VisionRange => visionRange;
    public float VisionAngle => visionAngle;
    public float ProximityAwarenessRange => proximityAwarenessRange;
    public float PerceptionInterval => perceptionInterval;
    public float TargetMemorySeconds => targetMemorySeconds;
    public float HearingMultiplier => hearingMultiplier;
    public float PatrolRadius => patrolRadius;
    public float PatrolMinimumTravel => patrolMinimumTravel;
    public float PatrolWaitMinSeconds => patrolWaitMinSeconds;
    public float PatrolWaitMaxSeconds => patrolWaitMaxSeconds;
    public float NonCombatThinkInterval => nonCombatThinkInterval;
    public float PatrolSpeed => patrolSpeed;
    public float CombatSpeed => combatSpeed;
    public float Acceleration => acceleration;
    public float AngularSpeed => angularSpeed;
    public float CombatThinkInterval => combatThinkInterval;
    public float RepathInterval => repathInterval;
    public float DestinationRefreshDistance => destinationRefreshDistance;
    public float AttackRange => attackRange;
    public float PreferredRange => preferredRange;
    public float AttackDamage => attackDamage;
    public float AttackCooldownSeconds => attackCooldownSeconds;
    public float AimTrackingSpeed => aimTrackingSpeed;
    public float AimSettleSeconds => aimSettleSeconds;
    public float InitialAimErrorRadius => initialAimErrorRadius;
    public float SettledAimErrorRadius => settledAimErrorRadius;
    public float MovingAimErrorPenalty => movingAimErrorPenalty;
    public float AimDriftFrequency => aimDriftFrequency;

    public void Normalize()
    {
        visionRange = Mathf.Max(0.1f, visionRange);
        visionAngle = Mathf.Clamp(visionAngle, 0f, 360f);
        proximityAwarenessRange = Mathf.Clamp(proximityAwarenessRange, 0f, visionRange);
        perceptionInterval = Mathf.Max(0.05f, perceptionInterval);
        targetMemorySeconds = Mathf.Max(0f, targetMemorySeconds);
        hearingMultiplier = Mathf.Max(0f, hearingMultiplier);
        patrolRadius = Mathf.Max(0f, patrolRadius);
        patrolMinimumTravel = Mathf.Clamp(patrolMinimumTravel, 0f, patrolRadius);
        patrolWaitMinSeconds = Mathf.Max(0f, patrolWaitMinSeconds);
        patrolWaitMaxSeconds = Mathf.Max(patrolWaitMinSeconds, patrolWaitMaxSeconds);
        nonCombatThinkInterval = Mathf.Max(0.05f, nonCombatThinkInterval);
        patrolSpeed = Mathf.Max(0f, patrolSpeed);
        combatSpeed = Mathf.Max(0f, combatSpeed);
        acceleration = Mathf.Max(0f, acceleration);
        angularSpeed = Mathf.Max(0f, angularSpeed);
        combatThinkInterval = Mathf.Max(0.05f, combatThinkInterval);
        repathInterval = Mathf.Max(0.05f, repathInterval);
        destinationRefreshDistance = Mathf.Max(0f, destinationRefreshDistance);
        attackRange = Mathf.Max(0.1f, attackRange);
        preferredRange = Mathf.Clamp(preferredRange, 0f, attackRange);
        attackDamage = CombatValueRules.NormalizeAttackPower(attackDamage);
        attackCooldownSeconds = Mathf.Max(0.05f, attackCooldownSeconds);
        aimTrackingSpeed = Mathf.Max(0f, aimTrackingSpeed);
        aimSettleSeconds = Mathf.Max(0f, aimSettleSeconds);
        initialAimErrorRadius = Mathf.Max(0f, initialAimErrorRadius);
        settledAimErrorRadius = Mathf.Clamp(settledAimErrorRadius, 0f, initialAimErrorRadius);
        movingAimErrorPenalty = Mathf.Max(0f, movingAimErrorPenalty);
        aimDriftFrequency = Mathf.Max(0.01f, aimDriftFrequency);
    }
}

[CreateAssetMenu(
    fileName = "EnemyDefinition",
    menuName = "Fantasy Survival/Enemies/Enemy Definition")]
public sealed class EnemyDefinition : ScriptableObject
{
    [SerializeField, Min(1f)] private float maxHealth = 1000f;
    [SerializeField] private EnemyAISettings ai = new EnemyAISettings();

    public float MaxHealth => Mathf.Max(
        1,
        CombatValueRules.RoundPositiveToInt(maxHealth));
    public EnemyAISettings AI => ai;

    private void OnValidate()
    {
        maxHealth = Mathf.Max(
            1,
            CombatValueRules.RoundPositiveToInt(maxHealth));
        if (ai == null)
        {
            ai = new EnemyAISettings();
        }

        ai.Normalize();
    }
}
