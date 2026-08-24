using FantasySurvival.Combat;
using UnityEngine;

public readonly struct EnemyCombatContext
{
    public EnemyCombatContext(
        EnemyAIController owner,
        Transform target,
        IDamageable targetDamageable,
        float currentTime,
        float deltaTime)
    {
        Owner = owner;
        Target = target;
        TargetDamageable = targetDamageable;
        CurrentTime = currentTime;
        DeltaTime = deltaTime;
    }

    public EnemyAIController Owner { get; }
    public Transform Target { get; }
    public IDamageable TargetDamageable { get; }
    public float CurrentTime { get; }
    public float DeltaTime { get; }
}

/// <summary>
/// Tactic-specific runtime state. It never owns health, awareness, target memory, or navigation.
/// </summary>
public abstract class EnemyCombatAction : MonoBehaviour
{
    public abstract EnemyCombatArchetype Archetype { get; }

    public virtual void BeginCombat(in EnemyCombatContext context)
    {
    }

    public abstract void TickCombat(in EnemyCombatContext context);

    public virtual void EndCombat()
    {
    }
}
