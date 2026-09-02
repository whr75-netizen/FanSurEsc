using System;
using FantasySurvival.Combat;
using FantasySurvival.Inventory;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class PlayerStats : MonoBehaviour, IDamageable
{
    [SerializeField, Min(1f)] private float maxHealth = 1000f;
    [SerializeField, Min(0f)] private float currentHealth = 1000f;

    private EquipmentLoadoutData equipmentLoadout;
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
    public int DefensePercent => equipmentLoadout?.DefensePercent ?? 0;

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
        int finalDamage = CombatValueRules.CalculateFinalDamage(
            context.Amount,
            DefensePercent);
        if (healthMutationInProgress || damageBlocked || !IsAlive || finalDamage <= 0)
        {
            return DamageResult.Ignored(currentHealth);
        }

        float previousHealth = currentHealth;
        float nextHealth = Mathf.Clamp(previousHealth - finalDamage, 0f, maxHealth);
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
            SetCurrentHealth(
                currentHealth + CombatValueRules.RoundPositiveToInt(amount));
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

    public void BindEquipmentLoadout(EquipmentLoadoutData loadout)
    {
        equipmentLoadout = loadout;
    }

    public bool CanRestoreCheckpointHealth(
        float savedCurrentHealth,
        float savedMaxHealth,
        out float normalizedCurrentHealth)
    {
        bool valid = CombatValueRules.TryNormalizeSavedHealth(
            savedCurrentHealth,
            savedMaxHealth,
            maxHealth,
            false,
            out int normalized);
        normalizedCurrentHealth = valid ? normalized : 0f;
        return valid;
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

        if (!CanRestoreCheckpointHealth(
                savedCurrentHealth,
                savedMaxHealth,
                out float normalizedCurrentHealth))
        {
            error = "Checkpoint Player health is incompatible with the current Player definition.";
            return false;
        }

        healthMutationInProgress = true;
        try
        {
            isDead = false;
            SetCurrentHealth(normalizedCurrentHealth);
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
        float clamped = Mathf.Clamp(
            CombatValueRules.RoundPositiveToInt(value),
            0f,
            maxHealth);
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
        maxHealth = Mathf.Max(1, CombatValueRules.RoundPositiveToInt(maxHealth));
        currentHealth = Mathf.Clamp(
            CombatValueRules.RoundPositiveToInt(currentHealth),
            0f,
            maxHealth);
        isDead = currentHealth <= 0f;
    }

    private void OnValidate()
    {
        NormalizeHealth();
    }
}
