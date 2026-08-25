using System;
using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class PlayerStats : MonoBehaviour, IDamageable
{
    [SerializeField, Min(1f)] private float maxHealth = 100f;
    [SerializeField, Min(0f)] private float currentHealth = 100f;

    private bool damageBlocked;

    public event Action<float, float> HealthChanged;
    public event Action<PlayerStats, DamageContext> Died;

    public float MaxHealth => maxHealth;
    public float CurrentHealth => currentHealth;
    public bool IsAlive => currentHealth > 0f;
    public bool DamageBlocked => damageBlocked;

    private void Awake()
    {
        NormalizeHealth();
    }

    public void ApplyDamage(float amount)
    {
        ApplyDamage(new DamageContext(amount, null, transform.position));
    }

    public DamageResult ApplyDamage(DamageContext context)
    {
        if (damageBlocked || !IsAlive || context.Amount <= 0f || float.IsNaN(context.Amount))
        {
            return DamageResult.Ignored(currentHealth);
        }

        float previousHealth = currentHealth;
        SetCurrentHealth(currentHealth - context.Amount);
        bool causedDeath = previousHealth > 0f && currentHealth <= 0f;
        var result = new DamageResult(
            true,
            previousHealth,
            currentHealth,
            causedDeath);
        if (causedDeath)
        {
            Died?.Invoke(this, context);
        }

        return result;
    }

    public void RestoreHealth(float amount)
    {
        if (amount <= 0f)
        {
            return;
        }

        SetCurrentHealth(currentHealth + amount);
    }

    public void ResetHealth()
    {
        SetCurrentHealth(maxHealth);
    }

    public void SetDamageBlocked(bool blocked)
    {
        damageBlocked = blocked;
    }

    public bool TryRestoreCheckpointHealth(
        float savedCurrentHealth,
        float savedMaxHealth,
        out string error)
    {
        if (float.IsNaN(savedCurrentHealth) || float.IsInfinity(savedCurrentHealth) ||
            float.IsNaN(savedMaxHealth) || float.IsInfinity(savedMaxHealth) ||
            savedMaxHealth <= 0f ||
            !Mathf.Approximately(savedMaxHealth, maxHealth) ||
            savedCurrentHealth <= 0f ||
            savedCurrentHealth > maxHealth)
        {
            error = "Checkpoint Player health is incompatible with the current Player definition.";
            return false;
        }

        SetCurrentHealth(savedCurrentHealth);
        error = null;
        return true;
    }

    private void SetCurrentHealth(float value)
    {
        float clamped = Mathf.Clamp(value, 0f, maxHealth);
        if (Mathf.Approximately(currentHealth, clamped))
        {
            return;
        }

        currentHealth = clamped;
        HealthChanged?.Invoke(currentHealth, maxHealth);
    }

    private void NormalizeHealth()
    {
        maxHealth = Mathf.Max(1f, maxHealth);
        currentHealth = Mathf.Clamp(currentHealth, 0f, maxHealth);
    }

    private void OnValidate()
    {
        NormalizeHealth();
    }
}
