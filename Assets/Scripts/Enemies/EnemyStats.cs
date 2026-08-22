using System;
using UnityEngine;

[DisallowMultipleComponent]
public sealed class EnemyStats : MonoBehaviour
{
    [SerializeField] private EnemyDefinition definition;

    private float currentHealth;
    private bool isInitialized;

    public event Action<float, float> HealthChanged;

    public EnemyDefinition Definition => definition;
    public float MaxHealth => definition != null ? definition.MaxHealth : 0f;
    public float CurrentHealth => currentHealth;
    public bool IsInitialized => isInitialized;
    public bool IsAlive => isInitialized && currentHealth > 0f;

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
        if (sourceDefinition == null)
        {
            return false;
        }

        definition = sourceDefinition;
        isInitialized = true;
        SetCurrentHealth(definition.MaxHealth, true);
        return true;
    }

    public void ApplyDamage(float amount)
    {
        if (!isInitialized || amount <= 0f)
        {
            return;
        }

        SetCurrentHealth(currentHealth - amount);
    }

    public void RestoreHealth(float amount)
    {
        if (!isInitialized || amount <= 0f)
        {
            return;
        }

        SetCurrentHealth(currentHealth + amount);
    }

    public void ResetHealth()
    {
        if (!isInitialized)
        {
            return;
        }

        SetCurrentHealth(MaxHealth);
    }

    private void SetCurrentHealth(float value, bool forceNotification = false)
    {
        float clamped = Mathf.Clamp(value, 0f, MaxHealth);
        if (!forceNotification && Mathf.Approximately(currentHealth, clamped))
        {
            return;
        }

        currentHealth = clamped;
        HealthChanged?.Invoke(currentHealth, MaxHealth);
    }
}
