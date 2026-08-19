using UnityEngine;

namespace FantasySurvival.Inventory
{
    public enum ItemDefinitionKind
    {
        Standard,
        Container
    }

    [CreateAssetMenu(
        fileName = "ItemDefinition",
        menuName = "Fantasy Survival/Inventory/Item Definition")]
    public sealed class ItemDefinition : ScriptableObject
    {
        [SerializeField, Min(1)] private int id = 1;
        [SerializeField] private string displayName;
        [SerializeField, TextArea] private string description;

        [Header("Inventory Presentation")]
        [SerializeField, Min(1)] private int width = 1;
        [SerializeField, Min(1)] private int height = 1;
        [SerializeField] private Texture2D icon;

        [Header("Container")]
        [SerializeField] private ItemDefinitionKind kind;
        [SerializeField, Min(1)] private int containerWidth = 1;
        [SerializeField, Min(1)] private int containerHeight = 1;

        public int Id => id;
        public string DisplayName => displayName;
        public string Description => description;
        public int Width => width;
        public int Height => height;
        public Texture2D Icon => icon;
        public ItemDefinitionKind Kind => kind;
        public bool IsContainer => kind == ItemDefinitionKind.Container;
        public int ContainerWidth => containerWidth;
        public int ContainerHeight => containerHeight;

        private void OnValidate()
        {
            id = Mathf.Max(1, id);
            width = Mathf.Max(1, width);
            height = Mathf.Max(1, height);
            containerWidth = Mathf.Max(1, containerWidth);
            containerHeight = Mathf.Max(1, containerHeight);
        }
    }
}
