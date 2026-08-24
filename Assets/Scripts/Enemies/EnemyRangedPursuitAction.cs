using UnityEngine;

[DisallowMultipleComponent]
public sealed class EnemyRangedPursuitAction : EnemyCombatAction
{
    private float nextAttackTime;
    private float focusedSeconds;
    private float driftPhaseX;
    private float driftPhaseZ;
    private Vector3 trackedAimPoint;
    private bool hasTrackedAimPoint;
    private bool isFirstCombatTick;

    public override EnemyCombatArchetype Archetype => EnemyCombatArchetype.RangedPursuit;

    private void Awake()
    {
        int seed = GetEntityId().GetHashCode();
        driftPhaseX = Mathf.Abs(seed % 997) * 0.019f;
        driftPhaseZ = Mathf.Abs(seed % 619) * 0.027f + 1.7f;
    }

    public override void BeginCombat(in EnemyCombatContext context)
    {
        focusedSeconds = 0f;
        trackedAimPoint = context.Owner.GetTargetAimPoint(context.Target);
        hasTrackedAimPoint = true;
        isFirstCombatTick = true;
    }

    public override void TickCombat(in EnemyCombatContext context)
    {
        EnemyAISettings settings = context.Owner.Settings;
        float aimDeltaTime = isFirstCombatTick ? 0f : context.DeltaTime;
        isFirstCombatTick = false;
        Vector3 toTarget = context.Target.position - context.Owner.Position;
        toTarget.y = 0f;
        float distanceSquared = toTarget.sqrMagnitude;
        bool isApproaching = distanceSquared > settings.PreferredRange * settings.PreferredRange;

        if (isApproaching)
        {
            context.Owner.NavigateTo(
                context.Target.position,
                settings.CombatSpeed,
                settings.PreferredRange,
                context.CurrentTime);
        }
        else
        {
            context.Owner.StopAndFace(context.Target.position);
        }

        Vector3 desiredAimPoint = context.Owner.GetTargetAimPoint(context.Target);
        if (!hasTrackedAimPoint)
        {
            trackedAimPoint = desiredAimPoint;
            hasTrackedAimPoint = true;
        }
        else
        {
            trackedAimPoint = Vector3.MoveTowards(
                trackedAimPoint,
                desiredAimPoint,
                settings.AimTrackingSpeed * aimDeltaTime);
        }

        focusedSeconds += aimDeltaTime;
        float settle = settings.AimSettleSeconds <= 0f
            ? 1f
            : Mathf.Clamp01(focusedSeconds / settings.AimSettleSeconds);
        float errorRadius = Mathf.Lerp(
            settings.InitialAimErrorRadius,
            settings.SettledAimErrorRadius,
            settle);
        if (isApproaching)
        {
            errorRadius += settings.MovingAimErrorPenalty;
        }

        if (distanceSquared > settings.AttackRange * settings.AttackRange ||
            context.CurrentTime < nextAttackTime ||
            !context.TargetDamageable.IsAlive)
        {
            return;
        }

        nextAttackTime = context.CurrentTime + settings.AttackCooldownSeconds;
        float driftTime = context.CurrentTime * settings.AimDriftFrequency;
        Vector3 smoothDrift = new Vector3(
            Mathf.Sin(driftTime + driftPhaseX),
            0f,
            Mathf.Sin(driftTime * 0.83f + driftPhaseZ)) * errorRadius;

        context.Owner.TryFireRangedShot(
            trackedAimPoint + smoothDrift,
            context.TargetDamageable,
            settings.AttackRange,
            settings.AttackDamage);
    }

    public override void EndCombat()
    {
        focusedSeconds = 0f;
        hasTrackedAimPoint = false;
        isFirstCombatTick = false;
    }
}
