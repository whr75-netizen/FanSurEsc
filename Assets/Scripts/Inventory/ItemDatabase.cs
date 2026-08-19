using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.Inventory
{
    [CreateAssetMenu(
        fileName = "ItemDatabase",
        menuName = "Fantasy Survival/Inventory/Item Database")]
    public sealed class ItemDatabase : ScriptableObject
    {
        [SerializeField] private List<ItemDefinition> items = new List<ItemDefinition>();

        private Dictionary<int, ItemDefinition> itemsById;

        public IReadOnlyList<ItemDefinition> Items => items;

        public bool TryGet(int id, out ItemDefinition definition)
        {
            EnsureIndex();
            return itemsById.TryGetValue(id, out definition);
        }

        private void OnEnable()
        {
            BuildIndex(false);
        }

        private void OnValidate()
        {
            BuildIndex(true);
        }

        private void EnsureIndex()
        {
            if (itemsById == null)
            {
                BuildIndex(false);
            }
        }

        private void BuildIndex(bool logErrors)
        {
            itemsById = new Dictionary<int, ItemDefinition>();

            foreach (var definition in items)
            {
                if (definition == null)
                {
                    if (logErrors)
                    {
                        Debug.LogError($"[{name}] Item Database contains an empty entry.", this);
                    }

                    continue;
                }

                if (itemsById.ContainsKey(definition.Id))
                {
                    if (logErrors)
                    {
                        Debug.LogError(
                            $"[{name}] Duplicate item ID {definition.Id}: {definition.DisplayName}",
                            this);
                    }

                    continue;
                }

                itemsById.Add(definition.Id, definition);
            }
        }
    }
}
