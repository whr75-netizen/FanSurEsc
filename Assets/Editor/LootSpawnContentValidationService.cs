using System;
using System.Collections.Generic;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using UnityEditor;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.EditorTools
{
    public enum LootSpawnValidationSeverity
    {
        Warning,
        Error
    }

    public sealed class LootSpawnValidationIssue
    {
        public LootSpawnValidationIssue(
            LootSpawnValidationSeverity severity,
            string message,
            UnityEngine.Object context = null)
        {
            Severity = severity;
            Message = message;
            Context = context;
        }

        public LootSpawnValidationSeverity Severity { get; }
        public string Message { get; }
        public UnityEngine.Object Context { get; }
    }

    public sealed class LootSpawnContentValidationReport
    {
        private readonly List<LootSpawnValidationIssue> issues =
            new List<LootSpawnValidationIssue>();
        private readonly List<LootTableDefinition> lootTables;
        private readonly List<RaidSpawnCatalogDefinition> spawnCatalogs;

        internal LootSpawnContentValidationReport(
            ItemDatabase itemDatabase,
            List<LootTableDefinition> lootTables,
            List<RaidSpawnCatalogDefinition> spawnCatalogs)
        {
            ItemDatabase = itemDatabase;
            this.lootTables = lootTables;
            this.spawnCatalogs = spawnCatalogs;
        }

        public ItemDatabase ItemDatabase { get; }
        public IReadOnlyList<LootTableDefinition> LootTables => lootTables;
        public IReadOnlyList<RaidSpawnCatalogDefinition> SpawnCatalogs => spawnCatalogs;
        public IReadOnlyList<LootSpawnValidationIssue> Issues => issues;
        public int SpawnEntryCount { get; internal set; }
        public int ErrorCount { get; private set; }
        public int WarningCount { get; private set; }
        public bool IsValid => ErrorCount == 0;

        internal void AddError(string message, UnityEngine.Object context = null)
        {
            Add(LootSpawnValidationSeverity.Error, message, context);
        }

        internal void AddWarning(string message, UnityEngine.Object context = null)
        {
            Add(LootSpawnValidationSeverity.Warning, message, context);
        }

        public string GetSummary()
        {
            return
                $"Loot tables {lootTables.Count}, spawn catalogs {spawnCatalogs.Count}, " +
                $"spawn entries {SpawnEntryCount}, errors {ErrorCount}, " +
                $"warnings {WarningCount}";
        }

        private void Add(
            LootSpawnValidationSeverity severity,
            string message,
            UnityEngine.Object context)
        {
            issues.Add(new LootSpawnValidationIssue(severity, message, context));
            if (severity == LootSpawnValidationSeverity.Error)
            {
                ErrorCount++;
            }
            else
            {
                WarningCount++;
            }
        }
    }

    /// <summary>
    /// Read-only project scan for the existing loot and raid-spawn definitions.
    /// Runtime validators remain the single source of truth; this service only
    /// aggregates their results and checks the authored cross-references.
    /// </summary>
    public static class LootSpawnContentValidationService
    {
        public static LootSpawnContentValidationReport ValidateProject()
        {
            ItemDatabase itemDatabase =
                ItemContentAuthoringService.LoadDefaultDatabase();
            List<LootTableDefinition> lootTables =
                FindAssets<LootTableDefinition>();
            List<RaidSpawnCatalogDefinition> spawnCatalogs =
                FindAssets<RaidSpawnCatalogDefinition>();
            var report = new LootSpawnContentValidationReport(
                itemDatabase,
                lootTables,
                spawnCatalogs);

            bool databaseIsValid = ValidateItemDatabase(itemDatabase, report);
            var validLootTables = new HashSet<LootTableDefinition>();
            if (databaseIsValid)
            {
                ValidateLootTables(itemDatabase, lootTables, validLootTables, report);
            }

            ValidateSpawnCatalogs(
                itemDatabase,
                databaseIsValid,
                validLootTables,
                spawnCatalogs,
                report);
            return report;
        }

        public static bool TryPreviewLoot(
            LootTableDefinition lootTable,
            ItemDatabase itemDatabase,
            int mapSeed,
            string stableContainerId,
            out List<ItemDefinition> rolledItems,
            out string error)
        {
            rolledItems = new List<ItemDefinition>();
            if (lootTable == null)
            {
                error = "Select a LootTableDefinition to preview.";
                return false;
            }

            if (!lootTable.TryValidate(itemDatabase, out error))
            {
                return false;
            }

            if (!LootTableRoller.TryRollDefinitionIds(
                    lootTable,
                    mapSeed,
                    stableContainerId,
                    out List<int> itemIds,
                    out error))
            {
                return false;
            }

            for (int index = 0; index < itemIds.Count; index++)
            {
                int itemId = itemIds[index];
                if (!itemDatabase.TryGet(itemId, out ItemDefinition definition))
                {
                    rolledItems.Clear();
                    error = $"Rolled item ID {itemId} is missing from the ItemDatabase.";
                    return false;
                }

                rolledItems.Add(definition);
            }

            error = null;
            return true;
        }

        public static void LogValidationReport(
            LootSpawnContentValidationReport report)
        {
            if (report == null)
            {
                throw new ArgumentNullException(nameof(report));
            }

            for (int index = 0; index < report.Issues.Count; index++)
            {
                LootSpawnValidationIssue issue = report.Issues[index];
                if (issue.Severity == LootSpawnValidationSeverity.Error)
                {
                    Debug.LogError(issue.Message, issue.Context);
                }
                else
                {
                    Debug.LogWarning(issue.Message, issue.Context);
                }
            }

            if (report.IsValid)
            {
                Debug.Log(
                    $"Loot and spawn content validation complete: {report.GetSummary()}.");
            }
        }

        private static bool ValidateItemDatabase(
            ItemDatabase itemDatabase,
            LootSpawnContentValidationReport report)
        {
            if (itemDatabase == null)
            {
                report.AddError(
                    $"ItemDatabase is missing at " +
                    $"'{ItemContentAuthoringService.DefaultDatabasePath}'.");
                return false;
            }

            if (!itemDatabase.TryValidate(out string error))
            {
                report.AddError($"ItemDatabase is invalid: {error}", itemDatabase);
                return false;
            }

            return true;
        }

        private static void ValidateLootTables(
            ItemDatabase itemDatabase,
            IReadOnlyList<LootTableDefinition> lootTables,
            ISet<LootTableDefinition> validLootTables,
            LootSpawnContentValidationReport report)
        {
            for (int index = 0; index < lootTables.Count; index++)
            {
                LootTableDefinition lootTable = lootTables[index];
                if (!lootTable.TryValidate(itemDatabase, out string error))
                {
                    report.AddError(
                        $"Loot table '{lootTable.name}' is invalid: {error}",
                        lootTable);
                    continue;
                }

                validLootTables.Add(lootTable);
            }
        }

        private static void ValidateSpawnCatalogs(
            ItemDatabase itemDatabase,
            bool databaseIsValid,
            ISet<LootTableDefinition> validLootTables,
            IReadOnlyList<RaidSpawnCatalogDefinition> spawnCatalogs,
            LootSpawnContentValidationReport report)
        {
            for (int catalogIndex = 0;
                 catalogIndex < spawnCatalogs.Count;
                 catalogIndex++)
            {
                RaidSpawnCatalogDefinition catalog = spawnCatalogs[catalogIndex];
                report.SpawnEntryCount += catalog.Entries != null
                    ? catalog.Entries.Count
                    : 0;

                if (!catalog.TryValidate(out string catalogError))
                {
                    report.AddError(
                        $"Raid spawn catalog '{catalog.name}' is invalid: {catalogError}",
                        catalog);
                    continue;
                }

                if (!databaseIsValid)
                {
                    continue;
                }

                for (int entryIndex = 0;
                     entryIndex < catalog.Entries.Count;
                     entryIndex++)
                {
                    RaidSpawnCatalogEntry entry = catalog.Entries[entryIndex];
                    Chest[] chests = entry.Kind == RaidSpawnContentKind.Chest
                        ? new[] { entry.Prefab.GetComponent<Chest>() }
                        : entry.Prefab.GetComponentsInChildren<Chest>(true);
                    for (int chestIndex = 0; chestIndex < chests.Length; chestIndex++)
                    {
                        ValidateSpawnChestContent(
                            entry.StableId,
                            chests[chestIndex],
                            itemDatabase,
                            validLootTables,
                            catalog,
                            report);
                    }
                }
            }
        }

        private static void ValidateSpawnChestContent(
            string stableId,
            Chest chest,
            ItemDatabase itemDatabase,
            ISet<LootTableDefinition> validLootTables,
            RaidSpawnCatalogDefinition catalog,
            LootSpawnContentValidationReport report)
        {
            if (!chest.TryCreateAuthoredInventory(out _, out string authoredError))
            {
                report.AddError(
                    $"Raid spawn '{stableId}' has invalid authored Chest content: " +
                    authoredError,
                    catalog);
            }

            LootTableDefinition lootTable = chest.LootTable;
            if (lootTable == null)
            {
                // Null is intentional: the valid authored prefab inventory is preserved.
                return;
            }

            if (!validLootTables.Contains(lootTable))
            {
                if (!lootTable.TryValidate(itemDatabase, out string tableError))
                {
                    report.AddError(
                        $"Raid spawn '{stableId}' references invalid loot table " +
                        $"'{lootTable.name}': {tableError}",
                        catalog);
                    return;
                }

                validLootTables.Add(lootTable);
            }

            if (!TryValidateAllLootFitsChest(
                    lootTable,
                    itemDatabase,
                    chest,
                    out string fitError))
            {
                report.AddError(
                    $"Raid spawn '{stableId}' cannot materialize every candidate " +
                    $"from '{lootTable.name}': {fitError}",
                    catalog);
            }
        }

        private static bool TryValidateAllLootFitsChest(
            LootTableDefinition lootTable,
            ItemDatabase itemDatabase,
            Chest chest,
            out string error)
        {
            for (int index = 0; index < lootTable.Entries.Count; index++)
            {
                LootTableEntry entry = lootTable.Entries[index];
                if (!itemDatabase.TryGet(
                        entry.ItemDefinitionId,
                        out ItemDefinition definition))
                {
                    error = $"item ID {entry.ItemDefinitionId} is missing.";
                    return false;
                }

                if (!InventoryItemDataFactory.TryCreate(
                        definition,
                        out IVariableInventoryCellData item,
                        out string itemError))
                {
                    error =
                        $"item ID {entry.ItemDefinitionId} could not be created: " +
                        itemError;
                    return false;
                }

                var candidate = new StandardStashViewData(
                    chest.chestWidth,
                    chest.chestHeight);
                if (!candidate.GetInsertableId(item).HasValue)
                {
                    error =
                        $"item ID {entry.ItemDefinitionId} does not fit an empty " +
                        $"{chest.chestWidth}x{chest.chestHeight} grid.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static List<T> FindAssets<T>() where T : UnityEngine.Object
        {
            string[] guids = AssetDatabase.FindAssets($"t:{typeof(T).Name}");
            var assets = new List<T>(guids.Length);
            for (int index = 0; index < guids.Length; index++)
            {
                string path = AssetDatabase.GUIDToAssetPath(guids[index]);
                T asset = AssetDatabase.LoadAssetAtPath<T>(path);
                if (asset != null)
                {
                    assets.Add(asset);
                }
            }

            assets.Sort((left, right) => string.Compare(
                AssetDatabase.GetAssetPath(left),
                AssetDatabase.GetAssetPath(right),
                StringComparison.Ordinal));
            return assets;
        }
    }
}
