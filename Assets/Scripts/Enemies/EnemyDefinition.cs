using UnityEngine;

[CreateAssetMenu(
    fileName = "EnemyDefinition",
    menuName = "Fantasy Survival/Enemies/Enemy Definition")]
public sealed class EnemyDefinition : ScriptableObject
{
    [SerializeField, Min(1f)] private float maxHealth = 100f;

    public float MaxHealth => Mathf.Max(1f, maxHealth);

    private void OnValidate()
    {
        maxHealth = Mathf.Max(1f, maxHealth);
    }
}
