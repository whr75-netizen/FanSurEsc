using System;
using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class PlayerStats : MonoBehaviour, IDamageable
{
    [SerializeField, Min(1f)] private float maxHealth = 100f;
    [SerializeField, Min(0f)] private float currentHealth = 100f;

    public event Action<float, float> HealthChanged;

    public float MaxHealth => maxHealth;
    public float CurrentHealth => currentHealth;
    public bool IsAlive => currentHealth > 0f;

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
        if (!IsAlive || context.Amount <= 0f || float.IsNaN(context.Amount))
        {
            return DamageResult.Ignored(currentHealth);
        }

        float previousHealth = currentHealth;
        SetCurrentHealth(currentHealth - context.Amount);
        return new DamageResult(
            true,
            previousHealth,
            currentHealth,
            previousHealth > 0f && currentHealth <= 0f);
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
