using System;
using System.Collections.Generic;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    [Serializable]
    public sealed class LootTableEntry
    {
        [SerializeField, Min(1)] private int itemDefinitionId = 1;
        [SerializeField, Range(0f, 100f)] private float dropChancePercent = 100f;

        public int ItemDefinitionId => itemDefinitionId;
        public float DropChancePercent => dropChancePercent;
    }

    [CreateAssetMenu(
        fileName = "LootTableDefinition",
        menuName = "Fantasy Survival/Inventory/Loot Table Definition")]
    public sealed class LootTableDefinition : ScriptableObject
    {
        [SerializeField] private List<LootTableEntry> entries = new List<LootTableEntry>();

        public IReadOnlyList<LootTableEntry> Entries => entries;

        public bool TryValidate(ItemDatabase itemDatabase, out string error)
        {
            if (itemDatabase == null)
            {
                error = $"Loot table '{name}' requires an ItemDatabase.";
                return false;
            }

            if (entries == null || entries.Count == 0)
            {
                error = $"Loot table '{name}' has no entries.";
                return false;
            }

            var itemIds = new HashSet<int>();
            long totalChanceBasisPoints = 0;
            for (int index = 0; index < entries.Count; index++)
            {
                LootTableEntry entry = entries[index];
                if (entry == null || entry.ItemDefinitionId <= 0 ||
                    float.IsNaN(entry.DropChancePercent) ||
                    float.IsInfinity(entry.DropChancePercent) ||
                    entry.DropChancePercent < 0f || entry.DropChancePercent > 100f)
                {
                    error = $"Loot table '{name}' entry {index} is invalid.";
                    return false;
                }

                if (!itemIds.Add(entry.ItemDefinitionId))
                {
                    error =
                        $"Loot table '{name}' contains duplicate item ID {entry.ItemDefinitionId}.";
                    return false;
                }

                if (!itemDatabase.TryGet(entry.ItemDefinitionId, out ItemDefinition definition))
                {
                    error =
                        $"Loot table '{name}' references missing item ID {entry.ItemDefinitionId}.";
                    return false;
                }

                if (!definition.TryValidateInventoryShape(out string definitionError))
                {
                    error =
                        $"Loot table '{name}' item ID {entry.ItemDefinitionId} is invalid: " +
                        definitionError;
                    return false;
                }

                totalChanceBasisPoints += LootTableRoller.PercentToBasisPoints(
                    entry.DropChancePercent);
                if (totalChanceBasisPoints > LootTableRoller.ChanceBasisPointCount)
                {
                    error =
                        $"Loot table '{name}' chance total exceeds 100%. " +
                        "The remaining percentage is reserved for no drop.";
                    return false;
                }
            }

            error = null;
            return true;
        }
    }

    /// <summary>
    /// Converts immutable loot definitions into one container-owned runtime grid.
    /// Entries form one cumulative percentage roll and therefore produce at most
    /// one item. A total below 100% leaves the remainder as no drop. Randomness is
    /// local to map seed + stable container ID, so opening order and unrelated
    /// UnityEngine.Random calls cannot change the result.
    /// </summary>
    public static class LootTableRoller
    {
        public const int AlgorithmVersion = 1;
        public const int ChanceBasisPointCount = 10000;

        public static bool TryCreateInventory(
            LootTableDefinition lootTable,
            ItemDatabase itemDatabase,
            int mapSeed,
            string stableContainerId,
            int width,
            int height,
            out StandardStashViewData inventory,
            out string error)
        {
            inventory = null;
            if (!InventoryGridConstraints.TryValidateDimensions(width, height, out error))
            {
                return false;
            }

            if (lootTable == null || !lootTable.TryValidate(itemDatabase, out error))
            {
                if (lootTable == null)
                {
                    error = "Loot table is missing.";
                }
                return false;
            }

            if (!TryRollDefinitionIds(
                    lootTable,
                    mapSeed,
                    stableContainerId,
                    out List<int> rolledItemIds,
                    out error))
            {
                return false;
            }

            var candidate = new StandardStashViewData(width, height);
            for (int index = 0; index < rolledItemIds.Count; index++)
            {
                int itemId = rolledItemIds[index];
                if (!itemDatabase.TryGet(itemId, out ItemDefinition definition))
                {
                    error = $"Rolled item ID {itemId} is missing from the ItemDatabase.";
                    return false;
                }

                if (!InventoryItemDataFactory.TryCreate(
                        definition,
                        out IVariableInventoryCellData item,
                        out string itemError))
                {
                    error = $"Rolled item ID {itemId} could not be created: {itemError}";
                    return false;
                }

                int? slot = candidate.GetInsertableId(item);
                if (!slot.HasValue)
                {
                    error =
                        $"Rolled item ID {itemId} does not fit in the {width}x{height} loot container. " +
                        "The container remains unchanged.";
                    return false;
                }

                candidate.InsertInventoryItem(slot.Value, item);
            }

            inventory = candidate;
            error = null;
            return true;
        }

        public static bool TryRollDefinitionIds(
            LootTableDefinition lootTable,
            int mapSeed,
            string stableContainerId,
            out List<int> rolledItemIds,
            out string error)
        {
            rolledItemIds = new List<int>();
            if (lootTable == null || lootTable.Entries == null ||
                lootTable.Entries.Count == 0)
            {
                error = "Loot table has no entries.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(stableContainerId))
            {
                error = "Loot roll requires a stable container ID.";
                return false;
            }

            var seenItemIds = new HashSet<int>();
            long totalChanceBasisPoints = 0;
            for (int index = 0; index < lootTable.Entries.Count; index++)
            {
                LootTableEntry entry = lootTable.Entries[index];
                if (entry == null || entry.ItemDefinitionId <= 0 ||
                    float.IsNaN(entry.DropChancePercent) ||
                    float.IsInfinity(entry.DropChancePercent) ||
                    entry.DropChancePercent < 0f || entry.DropChancePercent > 100f ||
                    !seenItemIds.Add(entry.ItemDefinitionId))
                {
                    error = $"Loot table entry {index} is invalid or duplicates an item ID.";
                    rolledItemIds.Clear();
                    return false;
                }

                int chanceBasisPoints = PercentToBasisPoints(entry.DropChancePercent);
                totalChanceBasisPoints += chanceBasisPoints;
                if (totalChanceBasisPoints > ChanceBasisPointCount)
                {
                    error =
                        "Loot table chance total exceeds 100%; the roll was not performed.";
                    rolledItemIds.Clear();
                    return false;
                }
            }

            int roll = RollBasisPoints(mapSeed, stableContainerId);
            int cumulative = 0;
            for (int index = 0; index < lootTable.Entries.Count; index++)
            {
                LootTableEntry entry = lootTable.Entries[index];
                cumulative += PercentToBasisPoints(entry.DropChancePercent);
                if (roll < cumulative)
                {
                    rolledItemIds.Add(entry.ItemDefinitionId);
                    break;
                }
            }

            error = null;
            return true;
        }

        public static int PercentToBasisPoints(float percent)
        {
            return Mathf.Clamp(
                Mathf.RoundToInt(percent * (ChanceBasisPointCount / 100f)),
                0,
                ChanceBasisPointCount);
        }

        private static int RollBasisPoints(int mapSeed, string stableContainerId)
        {
            uint state = 2166136261u;
            AddInt(ref state, AlgorithmVersion);
            AddInt(ref state, mapSeed);
            AddString(ref state, stableContainerId);

            state = AdvanceState(state);

            uint range = ChanceBasisPointCount;
            uint rejectionThreshold = unchecked(0u - range) % range;
            while (state < rejectionThreshold)
            {
                state = AdvanceState(state);
            }

            return (int)(state % range);
        }

        private static uint AdvanceState(uint state)
        {
            if (state == 0u)
            {
                state = 0x6D2B79F5u;
            }

            state ^= state << 13;
            state ^= state >> 17;
            state ^= state << 5;
            return state == 0u ? 0x6D2B79F5u : state;
        }

        private static void AddInt(ref uint hash, int value)
        {
            unchecked
            {
                hash ^= (byte)value;
                hash *= 16777619u;
                hash ^= (byte)(value >> 8);
                hash *= 16777619u;
                hash ^= (byte)(value >> 16);
                hash *= 16777619u;
                hash ^= (byte)(value >> 24);
                hash *= 16777619u;
            }
        }

        private static void AddString(ref uint hash, string value)
        {
            unchecked
            {
                for (int index = 0; index < value.Length; index++)
                {
                    char character = value[index];
                    hash ^= (byte)character;
                    hash *= 16777619u;
                    hash ^= (byte)(character >> 8);
                    hash *= 16777619u;
                }
            }
        }
    }
}
