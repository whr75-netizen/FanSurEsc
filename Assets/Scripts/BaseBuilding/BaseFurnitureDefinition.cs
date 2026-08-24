using FantasySurvival.Inventory;
using UnityEngine;

namespace FantasySurvival.BaseBuilding
{
    [CreateAssetMenu(
        fileName = "BaseFurnitureDefinition",
        menuName = "Fantasy Survival/Base/Base Furniture Definition")]
    public sealed class BaseFurnitureDefinition : ScriptableObject
    {
        [Tooltip("Stable namespaced key used by saves and future mods, for example core:storage_chest.")]
        [SerializeField] private string definitionKey = "core:furniture";
        [SerializeField] private string displayName = "Furniture";

        [Header("Optional storage capability")]
        [SerializeField] private bool hasStorage;
        [SerializeField, Min(1)] private int storageWidth = 1;
        [SerializeField, Min(1)] private int storageHeight = 1;

        public string DefinitionKey => definitionKey;
        public string DisplayName => displayName;
        public bool HasStorage => hasStorage;
        public int StorageWidth => storageWidth;
        public int StorageHeight => storageHeight;

        public bool TryValidate(out string error)
        {
            if (!BaseContentKey.IsValid(definitionKey))
            {
                error = $"Furniture definition key '{definitionKey}' must use a lowercase namespace:path key.";
                return false;
            }

            if (hasStorage && !InventoryGridConstraints.TryValidateDimensions(
                    storageWidth,
                    storageHeight,
                    out error))
            {
                error = $"Furniture definition '{definitionKey}' has invalid storage dimensions: {error}";
                return false;
            }

            error = null;
            return true;
        }

        private void OnValidate()
        {
            storageWidth = Mathf.Max(1, storageWidth);
            storageHeight = Mathf.Max(1, storageHeight);
        }
    }

    public static class BaseContentKey
    {
        public static bool IsValid(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }

            int separator = value.IndexOf(':');
            if (separator <= 0 || separator != value.LastIndexOf(':') || separator >= value.Length - 1)
            {
                return false;
            }

            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                if (character == ':')
                {
                    continue;
                }

                bool isLowerLetter = character >= 'a' && character <= 'z';
                bool isDigit = character >= '0' && character <= '9';
                bool isCommonSeparator = character == '_' || character == '-' || character == '.';
                bool isPathSeparator = character == '/' && index > separator;
                if (!isLowerLetter && !isDigit && !isCommonSeparator && !isPathSeparator)
                {
                    return false;
                }
            }

            return true;
        }
    }
}
