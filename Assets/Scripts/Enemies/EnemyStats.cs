using System;
using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class EnemyStats : MonoBehaviour, IDamageable
{
    [SerializeField] private EnemyDefinition definition;

    private float currentHealth;
    private bool isInitialized;
    private bool isDead;

    public event Action<float, float> HealthChanged;
    public event Action<EnemyStats, DamageContext, DamageResult> DamageApplied;
    public event Action<EnemyStats, DamageContext> Died;

    public EnemyDefinition Definition => definition;
    public float MaxHealth => definition != null ? definition.MaxHealth : 0f;
    public float CurrentHealth => currentHealth;
    public bool IsInitialized => isInitialized;
    public bool IsAlive => isInitialized && !isDead;
    public bool IsDead => isInitialized && isDead;

    private void Awake()
    {
        if (definition != null)
        {
            Initialize(definition);
        }
    }

    private void Start()
    {
        if (!isInitialized)
        {
            Debug.LogError($"{nameof(EnemyStats)} on '{name}' requires an {nameof(EnemyDefinition)}.", this);
        }
    }

    public bool Initialize(EnemyDefinition sourceDefinition)
    {
        if (sourceDefinition == null || isInitialized)
        {
            return false;
        }

        definition = sourceDefinition;
        isInitialized = true;
        isDead = false;
        SetCurrentHealth(definition.MaxHealth, true);
        return true;
    }

    public void ApplyDamage(float amount)
    {
        ApplyDamage(new DamageContext(amount, null, transform.position));
    }

    public DamageResult ApplyDamage(DamageContext context)
    {
        int finalDamage = CombatValueRules.CalculateFinalDamage(context.Amount, 0);
        if (!IsAlive || finalDamage <= 0)
        {
            return DamageResult.Ignored(currentHealth);
        }

        float previousHealth = currentHealth;
        float nextHealth = Mathf.Clamp(currentHealth - finalDamage, 0f, MaxHealth);
        bool causedDeath = previousHealth > 0f && nextHealth <= 0f;

        currentHealth = nextHealth;
        if (causedDeath)
        {
            isDead = true;
        }

        var result = new DamageResult(true, previousHealth, currentHealth, causedDeath);
        HealthChanged?.Invoke(currentHealth, MaxHealth);
        DamageApplied?.Invoke(this, context, result);
        if (causedDeath)
        {
            Died?.Invoke(this, context);
        }

        return result;
    }

    public void RestoreHealth(float amount)
    {
        if (!IsAlive || amount <= 0f)
        {
            return;
        }

        SetCurrentHealth(
            currentHealth + CombatValueRules.RoundPositiveToInt(amount));
    }

    public void ResetHealth()
    {
        if (!IsAlive)
        {
            return;
        }

        SetCurrentHealth(MaxHealth);
    }

    public bool TryRestoreCheckpointHealth(
        float savedCurrentHealth,
        float savedMaxHealth,
        out string error)
    {
        if (!isInitialized || isDead)
        {
            error = "Enemy must be a freshly initialized living entity before checkpoint restore.";
            return false;
        }

        if (!CanRestoreCheckpointHealth(
                savedCurrentHealth,
                savedMaxHealth,
                out float normalizedCurrentHealth))
        {
            error = "Checkpoint Enemy health is incompatible with the current Enemy definition.";
            return false;
        }

        if (normalizedCurrentHealth <= 0f)
        {
            DamageResult result = ApplyDamage(
                new DamageContext(MaxHealth, null, transform.position));
            if (!result.CausedDeath || !IsDead)
            {
                error = "Checkpoint Enemy death transition did not complete.";
                return false;
            }
        }
        else
        {
            SetCurrentHealth(normalizedCurrentHealth, true);
        }

        error = null;
        return true;
    }

    public bool CanRestoreCheckpointHealth(
        float savedCurrentHealth,
        float savedMaxHealth,
        out float normalizedCurrentHealth)
    {
        bool valid = CombatValueRules.TryNormalizeSavedHealth(
            savedCurrentHealth,
            savedMaxHealth,
            MaxHealth,
            true,
            out int normalized);
        normalizedCurrentHealth = valid ? normalized : 0f;
        return valid;
    }

    private void SetCurrentHealth(float value, bool forceNotification = false)
    {
        float clamped = Mathf.Clamp(
            CombatValueRules.RoundPositiveToInt(value),
            0f,
            MaxHealth);
        if (!forceNotification && Mathf.Approximately(currentHealth, clamped))
        {
            return;
        }

        currentHealth = clamped;
        HealthChanged?.Invoke(currentHealth, MaxHealth);
    }
}
