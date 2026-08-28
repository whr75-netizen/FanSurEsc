using System;
using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class PlayerStats : MonoBehaviour, IDamageable
{
    [SerializeField, Min(1f)] private float maxHealth = 100f;
    [SerializeField, Min(0f)] private float currentHealth = 100f;

    private bool damageBlocked;
    private bool isDead;
    private bool healthMutationInProgress;

    public event Action<float, float> HealthChanged;
    public event Action<PlayerStats, DamageContext, DamageResult> DamageApplied;
    public event Action<PlayerStats, DamageContext> Died;

    public float MaxHealth => maxHealth;
    public float CurrentHealth => currentHealth;
    public bool IsAlive => !isDead && currentHealth > 0f;
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
        if (healthMutationInProgress || damageBlocked || !IsAlive ||
            context.Amount <= 0f || float.IsNaN(context.Amount))
        {
            return DamageResult.Ignored(currentHealth);
        }

        float previousHealth = currentHealth;
        float nextHealth = Mathf.Clamp(previousHealth - context.Amount, 0f, maxHealth);
        bool causedDeath = previousHealth > 0f && nextHealth <= 0f;
        if (causedDeath)
        {
            isDead = true;
        }

        healthMutationInProgress = true;
        try
        {
            SetCurrentHealth(nextHealth);
            var result = new DamageResult(
                true,
                previousHealth,
                currentHealth,
                causedDeath);
            NotifyDamageApplied(context, result);
            if (causedDeath)
            {
                NotifyDied(context);
            }

            return result;
        }
        finally
        {
            healthMutationInProgress = false;
        }
    }

    public void RestoreHealth(float amount)
    {
        if (healthMutationInProgress || !IsAlive || amount <= 0f)
        {
            return;
        }

        healthMutationInProgress = true;
        try
        {
            SetCurrentHealth(currentHealth + amount);
        }
        finally
        {
            healthMutationInProgress = false;
        }
    }

    public void ResetHealth()
    {
        if (healthMutationInProgress)
        {
            return;
        }

        healthMutationInProgress = true;
        try
        {
            isDead = false;
            SetCurrentHealth(maxHealth);
        }
        finally
        {
            healthMutationInProgress = false;
        }
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
        if (healthMutationInProgress)
        {
            error = "Player health cannot be restored while a health mutation is being notified.";
            return false;
        }

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

        healthMutationInProgress = true;
        try
        {
            isDead = false;
            SetCurrentHealth(savedCurrentHealth);
            error = null;
            return true;
        }
        finally
        {
            healthMutationInProgress = false;
        }
    }

    private void SetCurrentHealth(float value)
    {
        float clamped = Mathf.Clamp(value, 0f, maxHealth);
        if (Mathf.Approximately(currentHealth, clamped))
        {
            return;
        }

        currentHealth = clamped;
        NotifyHealthChanged();
    }

    private void NotifyHealthChanged()
    {
        Action<float, float> handlers = HealthChanged;
        if (handlers == null)
        {
            return;
        }

        foreach (Action<float, float> handler in handlers.GetInvocationList())
        {
            try
            {
                handler(currentHealth, maxHealth);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
            }
        }
    }

    private void NotifyDamageApplied(DamageContext context, DamageResult result)
    {
        Action<PlayerStats, DamageContext, DamageResult> handlers = DamageApplied;
        if (handlers == null)
        {
            return;
        }

        foreach (Action<PlayerStats, DamageContext, DamageResult> handler in
                 handlers.GetInvocationList())
        {
            try
            {
                handler(this, context, result);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
            }
        }
    }

    private void NotifyDied(DamageContext context)
    {
        Action<PlayerStats, DamageContext> handlers = Died;
        if (handlers == null)
        {
            return;
        }

        foreach (Action<PlayerStats, DamageContext> handler in handlers.GetInvocationList())
        {
            try
            {
                handler(this, context);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
            }
        }
    }

    private void NormalizeHealth()
    {
        maxHealth = Mathf.Max(1f, maxHealth);
        currentHealth = Mathf.Clamp(currentHealth, 0f, maxHealth);
        isDead = currentHealth <= 0f;
    }

    private void OnValidate()
    {
        NormalizeHealth();
    }
}
