using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.Inventory
{
    public sealed class ItemDatabase : ScriptableObject
    {
        [SerializeField] private List<ItemDefinition> items = new List<ItemDefinition>();
        [SerializeField, HideInInspector, Min(1)] private int nextDefinitionId = 1;

        private Dictionary<int, ItemDefinition> itemsById;

        public IReadOnlyList<ItemDefinition> Items => items;
        public int NextDefinitionId => Mathf.Max(1, nextDefinitionId);

        public bool TryGet(int id, out ItemDefinition definition)
        {
            EnsureIndex();
            return itemsById.TryGetValue(id, out definition);
        }

        public bool TryValidate(out string error)
        {
            itemsById = null;
            var definitionsById = new Dictionary<int, ItemDefinition>();
            int maximumId = 0;

            if (items == null)
            {
                error = $"[{name}] Item Database item list is missing.";
                return false;
            }

            for (int index = 0; index < items.Count; index++)
            {
                ItemDefinition definition = items[index];
                if (definition == null)
                {
                    error = $"[{name}] Item Database entry {index} is empty.";
                    return false;
                }

                if (!definition.TryValidateInventoryShape(out string definitionError))
                {
                    error =
                        $"[{name}] Item definition ID {definition.Id} is invalid: " +
                        definitionError;
                    return false;
                }

                if (!definitionsById.TryAdd(definition.Id, definition))
                {
                    error =
                        $"[{name}] Duplicate item ID {definition.Id}: " +
                        definition.DisplayName;
                    return false;
                }

                maximumId = Mathf.Max(maximumId, definition.Id);
            }

            if (maximumId < int.MaxValue && nextDefinitionId <= maximumId)
            {
                error =
                    $"[{name}] Next item definition ID {nextDefinitionId} must be " +
                    $"greater than the current maximum ID {maximumId}.";
                return false;
            }

            foreach (ItemDefinition definition in definitionsById.Values)
            {
                if (!definition.IsWeapon)
                {
                    continue;
                }

                if (!definitionsById.TryGetValue(
                        definition.AmmunitionDefinitionId,
                        out ItemDefinition ammunition) ||
                    !ammunition.IsAmmunition)
                {
                    error =
                        $"[{name}] Weapon item ID {definition.Id} references invalid " +
                        $"ammunition item ID {definition.AmmunitionDefinitionId}.";
                    return false;
                }
            }

            itemsById = definitionsById;
            error = null;
            return true;
        }

        private void OnEnable()
        {
            EnsureNextDefinitionId();
            BuildIndex(false);
        }

        private void OnValidate()
        {
            EnsureNextDefinitionId();
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

            if (items == null)
            {
                if (logErrors)
                {
                    Debug.LogError($"[{name}] Item Database item list is missing.", this);
                }

                return;
            }

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

            foreach (ItemDefinition definition in itemsById.Values)
            {
                if (!definition.IsWeapon)
                {
                    continue;
                }

                if (!itemsById.TryGetValue(
                        definition.AmmunitionDefinitionId,
                        out ItemDefinition ammunition) ||
                    !ammunition.IsAmmunition)
                {
                    if (logErrors)
                    {
                        Debug.LogError(
                            $"[{name}] Weapon item ID {definition.Id} references invalid " +
                            $"ammunition item ID {definition.AmmunitionDefinitionId}.",
                            definition);
                    }
                }
            }
        }

        private void EnsureNextDefinitionId()
        {
            int maximumId = 0;
            if (items != null)
            {
                for (int index = 0; index < items.Count; index++)
                {
                    ItemDefinition definition = items[index];
                    if (definition != null)
                    {
                        maximumId = Mathf.Max(maximumId, definition.Id);
                    }
                }
            }

            int minimumNextId = maximumId == int.MaxValue
                ? int.MaxValue
                : maximumId + 1;
            nextDefinitionId = Mathf.Max(
                1,
                Mathf.Max(nextDefinitionId, minimumNextId));
        }
    }
}
