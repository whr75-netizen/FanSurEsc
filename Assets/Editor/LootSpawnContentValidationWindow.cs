using System.Collections.Generic;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    public sealed class LootSpawnContentValidationWindow : EditorWindow
    {
        [SerializeField] private LootTableDefinition selectedLootTable;
        [SerializeField] private int previewSeed;
        [SerializeField] private string previewStableContainerId =
            "preview:loot_container";
        [SerializeField] private bool showIssues = true;
        [SerializeField] private bool showSpawnCatalogs = true;

        private LootSpawnContentValidationReport report;
        private Vector2 scrollPosition;
        private string previewMessage;
        private MessageType previewMessageType = MessageType.Info;

        [MenuItem("Tools/Fantasy Survival/Content/Loot and Spawns")]
        public static void ShowWindow()
        {
            LootSpawnContentValidationWindow window =
                GetWindow<LootSpawnContentValidationWindow>();
            window.titleContent = new GUIContent("Loot + Spawns");
            window.minSize = new Vector2(660f, 500f);
            window.Show();
        }

        [MenuItem("Tools/Fantasy Survival/Content/Validate Loot and Spawns")]
        public static void ValidateFromMenu()
        {
            LootSpawnContentValidationReport validationReport =
                LootSpawnContentValidationService.ValidateProject();
            LootSpawnContentValidationService.LogValidationReport(validationReport);
        }

        private void OnEnable()
        {
            Undo.undoRedoPerformed += HandleProjectChanged;
            EditorApplication.projectChanged += HandleProjectChanged;
            Refresh();
        }

        private void OnDisable()
        {
            Undo.undoRedoPerformed -= HandleProjectChanged;
            EditorApplication.projectChanged -= HandleProjectChanged;
        }

        private void OnGUI()
        {
            DrawToolbar();
            EditorGUILayout.HelpBox(
                "This is a read-only view over the existing ItemDatabase, " +
                "LootTableDefinition assets, and RaidSpawnCatalogDefinition assets. " +
                "It never rewrites content or changes runtime roll rules.",
                MessageType.Info);

            if (report == null)
            {
                Refresh();
            }

            DrawSummary();
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
            DrawIssues();
            DrawLootTableDetails();
            DrawSeedPreview();
            DrawSpawnCatalogs();
            EditorGUILayout.EndScrollView();
        }

        private void DrawToolbar()
        {
            using (new EditorGUILayout.HorizontalScope(EditorStyles.toolbar))
            {
                using (new EditorGUI.DisabledScope(true))
                {
                    EditorGUILayout.ObjectField(
                        report?.ItemDatabase,
                        typeof(ItemDatabase),
                        false,
                        GUILayout.MinWidth(240f));
                }

                GUILayout.FlexibleSpace();
                if (GUILayout.Button(
                        "Refresh",
                        EditorStyles.toolbarButton,
                        GUILayout.Width(64f)))
                {
                    Refresh();
                }

                if (GUILayout.Button(
                        "Validate + Log",
                        EditorStyles.toolbarButton,
                        GUILayout.Width(96f)))
                {
                    Refresh();
                    LootSpawnContentValidationService.LogValidationReport(report);
                }
            }
        }

        private void DrawSummary()
        {
            MessageType messageType = report.IsValid
                ? report.WarningCount > 0 ? MessageType.Warning : MessageType.Info
                : MessageType.Error;
            EditorGUILayout.HelpBox(report.GetSummary(), messageType);
        }

        private void DrawIssues()
        {
            showIssues = EditorGUILayout.BeginFoldoutHeaderGroup(
                showIssues,
                $"Validation Issues ({report.Issues.Count})");
            if (showIssues)
            {
                if (report.Issues.Count == 0)
                {
                    EditorGUILayout.HelpBox(
                        "No loot or spawn content errors were found.",
                        MessageType.Info);
                }

                for (int index = 0; index < report.Issues.Count; index++)
                {
                    LootSpawnValidationIssue issue = report.Issues[index];
                    using (new EditorGUILayout.HorizontalScope())
                    {
                        EditorGUILayout.HelpBox(
                            issue.Message,
                            issue.Severity == LootSpawnValidationSeverity.Error
                                ? MessageType.Error
                                : MessageType.Warning);
                        if (issue.Context != null &&
                            GUILayout.Button("Select", GUILayout.Width(58f)))
                        {
                            SelectAndPing(issue.Context);
                        }
                    }
                }
            }

            EditorGUILayout.EndFoldoutHeaderGroup();
        }

        private void DrawLootTableDetails()
        {
            EditorGUILayout.Space(4f);
            EditorGUILayout.LabelField("Loot Table", EditorStyles.boldLabel);

            LootTableDefinition nextSelection =
                (LootTableDefinition)EditorGUILayout.ObjectField(
                    "Selected Table",
                    selectedLootTable,
                    typeof(LootTableDefinition),
                    false);
            if (nextSelection != selectedLootTable)
            {
                selectedLootTable = nextSelection;
                previewMessage = null;
            }

            if (selectedLootTable == null)
            {
                EditorGUILayout.HelpBox(
                    "No LootTableDefinition is selected.",
                    MessageType.Info);
                return;
            }

            using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
            {
                EditorGUILayout.LabelField(
                    "Asset",
                    AssetDatabase.GetAssetPath(selectedLootTable));

                long totalBasisPoints = 0;
                IReadOnlyList<LootTableEntry> entries = selectedLootTable.Entries;
                if (entries == null)
                {
                    EditorGUILayout.HelpBox(
                        "The serialized loot entry list is missing.",
                        MessageType.Error);
                    return;
                }

                for (int index = 0; index < entries.Count; index++)
                {
                    LootTableEntry entry = entries[index];
                    if (entry == null)
                    {
                        EditorGUILayout.LabelField($"Entry {index}", "[Missing entry]");
                        continue;
                    }

                    int basisPoints = LootTableRoller.PercentToBasisPoints(
                        entry.DropChancePercent);
                    totalBasisPoints += basisPoints;
                    EditorGUILayout.LabelField(
                        $"Entry {index}",
                        $"{GetItemLabel(entry.ItemDefinitionId)}  |  " +
                        $"{basisPoints / 100f:0.##}%");
                }

                float totalPercent = totalBasisPoints / 100f;
                float noDropPercent = Mathf.Max(
                    0f,
                    (LootTableRoller.ChanceBasisPointCount - totalBasisPoints) / 100f);
                EditorGUILayout.LabelField("Total", $"{totalPercent:0.##}%");
                EditorGUILayout.LabelField("No drop", $"{noDropPercent:0.##}%");

                using (new EditorGUILayout.HorizontalScope())
                {
                    GUILayout.FlexibleSpace();
                    if (GUILayout.Button("Select Asset", GUILayout.Width(92f)))
                    {
                        SelectAndPing(selectedLootTable);
                    }
                }
            }
        }

        private void DrawSeedPreview()
        {
            EditorGUILayout.Space(4f);
            EditorGUILayout.LabelField("Single Seed Preview", EditorStyles.boldLabel);
            using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
            {
                previewSeed = EditorGUILayout.IntField("Map Seed", previewSeed);
                previewStableContainerId = EditorGUILayout.TextField(
                    "Stable Container ID",
                    previewStableContainerId);

                using (new EditorGUI.DisabledScope(
                           selectedLootTable == null ||
                           report.ItemDatabase == null ||
                           string.IsNullOrWhiteSpace(previewStableContainerId)))
                {
                    if (GUILayout.Button("Preview This Seed"))
                    {
                        PreviewSelectedLoot();
                    }
                }

                if (!string.IsNullOrEmpty(previewMessage))
                {
                    EditorGUILayout.HelpBox(previewMessage, previewMessageType);
                }
            }
        }

        private void DrawSpawnCatalogs()
        {
            EditorGUILayout.Space(4f);
            showSpawnCatalogs = EditorGUILayout.BeginFoldoutHeaderGroup(
                showSpawnCatalogs,
                $"Raid Spawn Catalogs ({report.SpawnCatalogs.Count})");
            if (showSpawnCatalogs)
            {
                for (int catalogIndex = 0;
                     catalogIndex < report.SpawnCatalogs.Count;
                     catalogIndex++)
                {
                    RaidSpawnCatalogDefinition catalog =
                        report.SpawnCatalogs[catalogIndex];
                    using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
                    {
                        using (new EditorGUILayout.HorizontalScope())
                        {
                            bool isValid = catalog.TryValidate(out string error);
                            EditorGUILayout.LabelField(
                                isValid ? "OK" : "ERROR",
                                GUILayout.Width(42f));
                            EditorGUILayout.LabelField(catalog.name, EditorStyles.boldLabel);
                            if (GUILayout.Button("Select", GUILayout.Width(58f)))
                            {
                                SelectAndPing(catalog);
                            }

                            if (!isValid)
                            {
                                EditorGUILayout.LabelField(error);
                            }
                        }

                        IReadOnlyList<RaidSpawnCatalogEntry> entries = catalog.Entries;
                        if (entries == null)
                        {
                            EditorGUILayout.HelpBox(
                                "The serialized spawn entry list is missing.",
                                MessageType.Error);
                            continue;
                        }

                        for (int entryIndex = 0;
                             entryIndex < entries.Count;
                             entryIndex++)
                        {
                            RaidSpawnCatalogEntry entry = entries[entryIndex];
                            if (entry == null)
                            {
                                EditorGUILayout.LabelField(
                                    $"Entry {entryIndex}",
                                    "[Missing entry]");
                                continue;
                            }

                            string detail =
                                $"{entry.Kind} | " +
                                $"{(entry.Prefab != null ? entry.Prefab.name : "[Missing prefab]")}";
                            if (entry.Kind == RaidSpawnContentKind.Chest &&
                                entry.Prefab != null)
                            {
                                Chest chest = entry.Prefab.GetComponent<Chest>();
                                if (chest != null)
                                {
                                    detail += chest.LootTable != null
                                        ? $" | Loot: {chest.LootTable.name}"
                                        : " | Loot: authored prefab inventory";
                                }
                            }

                            EditorGUILayout.LabelField(entry.StableId, detail);
                        }
                    }
                }
            }

            EditorGUILayout.EndFoldoutHeaderGroup();
        }

        private void PreviewSelectedLoot()
        {
            if (!LootSpawnContentValidationService.TryPreviewLoot(
                    selectedLootTable,
                    report.ItemDatabase,
                    previewSeed,
                    previewStableContainerId,
                    out List<ItemDefinition> rolledItems,
                    out string error))
            {
                previewMessage = error;
                previewMessageType = MessageType.Error;
                return;
            }

            if (rolledItems.Count == 0)
            {
                previewMessage = "Result: No drop";
            }
            else
            {
                var labels = new List<string>(rolledItems.Count);
                for (int index = 0; index < rolledItems.Count; index++)
                {
                    ItemDefinition definition = rolledItems[index];
                    labels.Add($"[{definition.Id}] {GetDisplayName(definition)}");
                }

                previewMessage = $"Result: {string.Join(", ", labels)}";
            }

            previewMessageType = MessageType.Info;
        }

        private string GetItemLabel(int itemDefinitionId)
        {
            if (report.ItemDatabase != null &&
                report.ItemDatabase.TryGet(
                    itemDefinitionId,
                    out ItemDefinition definition))
            {
                return $"[{itemDefinitionId}] {GetDisplayName(definition)}";
            }

            return $"[Missing ID {itemDefinitionId}]";
        }

        private static string GetDisplayName(ItemDefinition definition)
        {
            return string.IsNullOrWhiteSpace(definition.DisplayName)
                ? definition.name
                : definition.DisplayName;
        }

        private void Refresh()
        {
            report = LootSpawnContentValidationService.ValidateProject();
            if (selectedLootTable == null && report.LootTables.Count > 0)
            {
                selectedLootTable = report.LootTables[0];
            }

            Repaint();
        }

        private void HandleProjectChanged()
        {
            Refresh();
        }

        private static void SelectAndPing(UnityEngine.Object target)
        {
            Selection.activeObject = target;
            EditorGUIUtility.PingObject(target);
        }
    }
}
