using UnityEngine;

namespace FantasySurvival.Combat
{
    public static class CombatValueRules
    {
        public const int AttackPowerStep = 10;
        public const int MaximumDefensePercent = 100;
        public const int LegacyHealthScaleMultiplier = 10;

        public static int RoundPositiveToInt(float value)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value <= 0f)
            {
                return 0;
            }

            return Mathf.Max(0, Mathf.FloorToInt(value + 0.5f));
        }

        public static int NormalizeAttackPower(float value)
        {
            int whole = RoundPositiveToInt(value);
            if (whole == 0)
            {
                return 0;
            }

            return Mathf.Max(
                AttackPowerStep,
                ((whole + AttackPowerStep / 2) / AttackPowerStep) * AttackPowerStep);
        }

        public static bool IsAttackPowerValid(float value)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value < 0f)
            {
                return false;
            }

            int whole = RoundPositiveToInt(value);
            return Mathf.Approximately(value, whole) && whole % AttackPowerStep == 0;
        }

        public static int CalculateFinalDamage(float rawAmount, int defensePercent)
        {
            int rawDamage = RoundPositiveToInt(rawAmount);
            if (rawDamage == 0)
            {
                return 0;
            }

            int clampedDefense = Mathf.Clamp(
                defensePercent,
                0,
                MaximumDefensePercent);
            long scaledDamage = (long)rawDamage * (100 - clampedDefense);
            return (int)((scaledDamage + 50L) / 100L);
        }

        public static bool TryNormalizeSavedHealth(
            float savedCurrentHealth,
            float savedMaxHealth,
            float expectedMaxHealth,
            bool allowZeroCurrent,
            out int normalizedCurrentHealth)
        {
            normalizedCurrentHealth = 0;
            int savedMaximum = RoundPositiveToInt(savedMaxHealth);
            int expectedMaximum = RoundPositiveToInt(expectedMaxHealth);
            if (savedMaximum <= 0 || expectedMaximum <= 0 ||
                float.IsNaN(savedCurrentHealth) || float.IsInfinity(savedCurrentHealth) ||
                savedCurrentHealth < 0f || savedCurrentHealth > savedMaxHealth)
            {
                return false;
            }

            int savedCurrent = RoundPositiveToInt(savedCurrentHealth);
            if ((!allowZeroCurrent && savedCurrent <= 0) || savedCurrent > savedMaximum)
            {
                return false;
            }

            if (savedMaximum == expectedMaximum)
            {
                normalizedCurrentHealth = savedCurrent;
                return true;
            }

            // The prototype's combat scale changed once from 100-based health to
            // 1000-based health. Accept that exact legacy ratio so an active raid
            // keeps the same health percentage instead of becoming corrupt.
            if ((long)savedMaximum * LegacyHealthScaleMultiplier == expectedMaximum)
            {
                normalizedCurrentHealth = Mathf.Clamp(
                    savedCurrent * LegacyHealthScaleMultiplier,
                    0,
                    expectedMaximum);
                return allowZeroCurrent || normalizedCurrentHealth > 0;
            }

            return false;
        }
    }

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
