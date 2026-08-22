using UnityEngine;

namespace FantasySurvival.Combat
{
    public readonly struct DamageContext
    {
        public DamageContext(float amount, GameObject source, Vector3 hitPoint)
        {
            Amount = amount;
            Source = source;
            HitPoint = hitPoint;
        }

        public float Amount { get; }
        public GameObject Source { get; }
        public Vector3 HitPoint { get; }
    }

    public readonly struct DamageResult
    {
        public DamageResult(
            bool wasApplied,
            float previousHealth,
            float currentHealth,
            bool causedDeath)
        {
            WasApplied = wasApplied;
            PreviousHealth = previousHealth;
            CurrentHealth = currentHealth;
            CausedDeath = causedDeath;
        }

        public bool WasApplied { get; }
        public float PreviousHealth { get; }
        public float CurrentHealth { get; }
        public bool CausedDeath { get; }

        public static DamageResult Ignored(float currentHealth)
        {
            return new DamageResult(false, currentHealth, currentHealth, false);
        }
    }

    public interface IDamageable
    {
        bool IsAlive { get; }
        DamageResult ApplyDamage(DamageContext context);
    }
}
