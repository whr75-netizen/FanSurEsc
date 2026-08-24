using FantasySurvival.Combat;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(EnemyStats))]
public sealed class EnemyDeathHandler : MonoBehaviour
{
    [SerializeField] private EnemyStats stats;
    [SerializeField] private Behaviour[] behavioursToDisable;
    [SerializeField] private Collider[] collidersToDisable;
    [SerializeField] private GameObject[] objectsToHide;
    [SerializeField] private Behaviour[] behavioursToEnableOnDeath;
    [SerializeField] private Collider[] collidersToEnableOnDeath;

    private bool hasHandledDeath;

    public bool HasHandledDeath => hasHandledDeath;

    private void OnEnable()
    {
        if (stats == null)
        {
            stats = GetComponent<EnemyStats>();
        }

        if (stats == null)
        {
            Debug.LogError($"{nameof(EnemyDeathHandler)} on '{name}' requires {nameof(EnemyStats)}.", this);
            enabled = false;
            return;
        }

        stats.Died += HandleDeath;
        if (stats.IsDead)
        {
            HandleDeath(stats, new DamageContext(0f, null, transform.position));
        }
    }

    private void OnDisable()
    {
        if (stats != null)
        {
            stats.Died -= HandleDeath;
        }
    }

    private void HandleDeath(EnemyStats deadStats, DamageContext context)
    {
        if (hasHandledDeath || deadStats != stats)
        {
            return;
        }

        hasHandledDeath = true;

        if (behavioursToDisable != null)
        {
            for (int index = 0; index < behavioursToDisable.Length; index++)
            {
                Behaviour behaviour = behavioursToDisable[index];
                if (behaviour != null && behaviour != this)
                {
                    behaviour.enabled = false;
                }
            }
        }

        if (collidersToDisable != null)
        {
            for (int index = 0; index < collidersToDisable.Length; index++)
            {
                Collider hitbox = collidersToDisable[index];
                if (hitbox != null)
                {
                    hitbox.enabled = false;
                }
            }
        }

        if (objectsToHide != null)
        {
            for (int index = 0; index < objectsToHide.Length; index++)
            {
                GameObject objectToHide = objectsToHide[index];
                if (objectToHide != null && objectToHide != gameObject)
                {
                    objectToHide.SetActive(false);
                }
            }
        }

        if (behavioursToEnableOnDeath != null)
        {
            for (int index = 0; index < behavioursToEnableOnDeath.Length; index++)
            {
                Behaviour behaviour = behavioursToEnableOnDeath[index];
                if (behaviour != null && behaviour != this)
                {
                    behaviour.enabled = true;
                }
            }
        }

        if (collidersToEnableOnDeath == null)
        {
            return;
        }

        for (int index = 0; index < collidersToEnableOnDeath.Length; index++)
        {
            Collider interactionCollider = collidersToEnableOnDeath[index];
            if (interactionCollider != null)
            {
                interactionCollider.enabled = true;
            }
        }
    }

#if UNITY_EDITOR
    private void OnValidate()
    {
        if (stats == null)
        {
            stats = GetComponent<EnemyStats>();
        }
    }
#endif
}
