using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class EnemyMeleeRushAction : EnemyCombatAction
{
    private float nextAttackTime;

    public override EnemyCombatArchetype Archetype => EnemyCombatArchetype.MeleeRush;

    public override void TickCombat(in EnemyCombatContext context)
    {
        EnemyAISettings settings = context.Owner.Settings;
        Vector3 toTarget = context.Target.position - context.Owner.Position;
        toTarget.y = 0f;

        if (toTarget.sqrMagnitude > settings.AttackRange * settings.AttackRange)
        {
            context.Owner.NavigateTo(
                context.Target.position,
                settings.CombatSpeed,
                Mathf.Max(0.05f, settings.AttackRange * 0.8f),
                context.CurrentTime);
            return;
        }

        context.Owner.StopAndFace(context.Target.position);
        if (context.CurrentTime < nextAttackTime || !context.TargetDamageable.IsAlive ||
            !context.Owner.HasClearLineToTarget(context.Target))
        {
            return;
        }

        nextAttackTime = context.CurrentTime + settings.AttackCooldownSeconds;
        context.TargetDamageable.ApplyDamage(new DamageContext(
            settings.AttackDamage,
            context.Owner.gameObject,
            context.Target.position));
    }
}
