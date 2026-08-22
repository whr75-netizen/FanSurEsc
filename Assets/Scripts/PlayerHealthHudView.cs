using UnityEngine;
using UnityEngine.UI;

[DisallowMultipleComponent]
public sealed class PlayerHealthHudView : MonoBehaviour
{
    [SerializeField] private PlayerStats playerStats;
    [SerializeField] private Slider healthSlider;
    [SerializeField] private Text healthText;

    private void OnEnable()
    {
        if (playerStats == null)
        {
            Debug.LogError("PlayerHealthHudView is missing PlayerStats.", this);
            return;
        }

        playerStats.HealthChanged += HandleHealthChanged;
        Refresh(playerStats.CurrentHealth, playerStats.MaxHealth);
    }

    private void OnDisable()
    {
        if (playerStats != null)
        {
            playerStats.HealthChanged -= HandleHealthChanged;
        }
    }

    private void HandleHealthChanged(float currentHealth, float maxHealth)
    {
        Refresh(currentHealth, maxHealth);
    }

    private void Refresh(float currentHealth, float maxHealth)
    {
        if (healthSlider != null)
        {
            healthSlider.minValue = 0f;
            healthSlider.maxValue = Mathf.Max(1f, maxHealth);
            healthSlider.value = Mathf.Clamp(currentHealth, 0f, healthSlider.maxValue);
        }

        if (healthText != null)
        {
            healthText.text = $"HP {Mathf.CeilToInt(currentHealth)} / {Mathf.CeilToInt(maxHealth)}";
        }
    }
}
