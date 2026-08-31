using System;
using System.Collections.Generic;
using FantasySurvival.Inventory;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    public sealed class ItemContentAuthoringWindow : EditorWindow
    {
        private static readonly string[] KindFilterLabels =
        {
            "All Kinds",
            "Standard",
            "Container",
            "Medicine",
            "Ammunition",
            "Food"
        };

        [SerializeField] private ItemDatabase database;
        [SerializeField] private ItemDefinition selectedDefinition;
        [SerializeField] private string definitionsFolder =
            ItemContentAuthoringService.DefaultDefinitionsFolder;
        [SerializeField] private string searchText = string.Empty;
        [SerializeField] private int kindFilter;
        [SerializeField] private bool showCreatePanel = true;
        [SerializeField] private bool showValidationIssues;

        private readonly List<ItemDefinition> definitions =
            new List<ItemDefinition>();
        private readonly Dictionary<ItemDefinition, IssueCounts> issueCounts =
            new Dictionary<ItemDefinition, IssueCounts>();

        private ItemAuthoringValidationReport validationReport;
        private UnityEditor.Editor selectedEditor;
        private Vector2 listScroll;
        private Vector2 inspectorScroll;
        private Vector2 validationScroll;

        [SerializeField] private string newAssetName = string.Empty;
        [SerializeField] private string newDisplayName = string.Empty;
        [SerializeField] private string newDescription = string.Empty;
        [SerializeField] private ItemDefinitionKind newKind = ItemDefinitionKind.Standard;
        [SerializeField] private EquipmentSlotType newEquipmentSlot = EquipmentSlotType.None;
        [SerializeField] private int newWidth = 1;
        [SerializeField] private int newHeight = 1;
        [SerializeField] private int newMaxStackSize = 1;
        [SerializeField] private int newContainerWidth = 1;
        [SerializeField] private int newContainerHeight = 1;
        [SerializeField] private int newAmmunitionDefinitionId;
        [SerializeField] private Texture2D newIcon;

        private struct IssueCounts
        {
            public int Errors;
            public int Warnings;
        }

        [MenuItem("Tools/Fantasy Survival/Content/Items")]
        public static void ShowWindow()
        {
            ItemContentAuthoringWindow window =
                GetWindow<ItemContentAuthoringWindow>();
            window.titleContent = new GUIContent("Item Content");
            window.minSize = new Vector2(820f, 520f);
            window.Show();
        }

        [MenuItem("Tools/Fantasy Survival/Content/Validate Items")]
        public static void ValidateItemsFromMenu()
        {
            ItemAuthoringValidationReport report =
                ItemContentAuthoringService.ValidateProject();
            ItemContentAuthoringService.LogValidationReport(report);
        }

        private void OnEnable()
        {
            database = ItemContentAuthoringService.LoadDefaultDatabase();

            Undo.undoRedoPerformed += HandleExternalChange;
            EditorApplication.projectChanged += HandleExternalChange;
            Selection.selectionChanged += HandleSelectionChanged;
            RefreshAll();
        }

        private void OnDisable()
        {
            Undo.undoRedoPerformed -= HandleExternalChange;
            EditorApplication.projectChanged -= HandleExternalChange;
            Selection.selectionChanged -= HandleSelectionChanged;
            DestroySelectedEditor();
        }

        private void OnGUI()
        {
            DrawToolbar();

            EditorGUILayout.HelpBox(
                "This window edits the existing ItemDefinition assets and ItemDatabase. " +
                "It does not create a second data store. AI automation can call " +
                "ItemContentAuthoringService directly through Unity RunCommand. New and " +
                "duplicated assets are saved immediately and are not Ctrl+Z operations.",
                MessageType.Info);

            DrawCreatePanel();
            DrawValidationSummary();

            EditorGUILayout.Space(4f);
            using (new EditorGUILayout.HorizontalScope())
            {
                DrawDefinitionBrowser();
                DrawSelectedDefinition();
            }
        }

        private void DrawToolbar()
        {
            using (new EditorGUILayout.HorizontalScope(EditorStyles.toolbar))
            {
                using (new EditorGUI.DisabledScope(true))
                {
                    EditorGUILayout.ObjectField(
                        database,
                        typeof(ItemDatabase),
                        false,
                        GUILayout.MinWidth(220f));
                }

                GUILayout.Space(6f);
                GUILayout.Label("Output", GUILayout.Width(42f));
                definitionsFolder = GUILayout.TextField(
                    definitionsFolder,
                    GUILayout.MinWidth(230f));
                if (GUILayout.Button("Choose", EditorStyles.toolbarButton, GUILayout.Width(58f)))
                {
                    ChooseDefinitionsFolder();
                }

                GUILayout.FlexibleSpace();
                if (GUILayout.Button("Refresh", EditorStyles.toolbarButton, GUILayout.Width(62f)))
                {
                    RefreshAll();
                }

                if (GUILayout.Button("Validate", EditorStyles.toolbarButton, GUILayout.Width(64f)))
                {
                    RefreshValidation(true);
                }
            }
        }

        private void DrawCreatePanel()
        {
            showCreatePanel = EditorGUILayout.BeginFoldoutHeaderGroup(
                showCreatePanel,
                "Create And Register Item");
            if (showCreatePanel)
            {
                using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
                {
                    int nextId = 0;
                    try
                    {
                        nextId = ItemContentAuthoringService.GetNextStableId();
                    }
                    catch (Exception exception)
                    {
                        EditorGUILayout.HelpBox(exception.Message, MessageType.Error);
                    }

                    using (new EditorGUI.DisabledScope(true))
                    {
                        EditorGUILayout.IntField("Next Stable ID", nextId);
                    }

                    newAssetName = EditorGUILayout.TextField("Asset Name", newAssetName);
                    newDisplayName = EditorGUILayout.TextField("Display Name", newDisplayName);
                    newDescription = EditorGUILayout.TextArea(
                        newDescription,
                        GUILayout.MinHeight(38f));
                    newKind = (ItemDefinitionKind)EditorGUILayout.EnumPopup(
                        "Item Kind",
                        newKind);
                    newEquipmentSlot = (EquipmentSlotType)EditorGUILayout.EnumPopup(
                        "Equipment Slot",
                        newEquipmentSlot);
                    newWidth = EditorGUILayout.IntField("Grid Width", newWidth);
                    newHeight = EditorGUILayout.IntField("Grid Height", newHeight);
                    newIcon = (Texture2D)EditorGUILayout.ObjectField(
                        "Icon",
                        newIcon,
                        typeof(Texture2D),
                        false);

                    if (newEquipmentSlot == EquipmentSlotType.Weapon)
                    {
                        DrawCreateAmmunitionPopup();
                    }

                    bool forcedSingleStack =
                        newKind == ItemDefinitionKind.Container ||
                        newEquipmentSlot != EquipmentSlotType.None;
                    using (new EditorGUI.DisabledScope(forcedSingleStack))
                    {
                        newMaxStackSize = EditorGUILayout.IntField(
                            "Maximum Stack Size",
                            forcedSingleStack ? 1 : newMaxStackSize);
                    }

                    if (newKind == ItemDefinitionKind.Container)
                    {
                        newContainerWidth = EditorGUILayout.IntField(
                            "Internal Width",
                            newContainerWidth);
                        newContainerHeight = EditorGUILayout.IntField(
                            "Internal Height",
                            newContainerHeight);
                    }

                    using (new EditorGUILayout.HorizontalScope())
                    {
                        GUILayout.FlexibleSpace();
                        using (new EditorGUI.DisabledScope(
                                   database == null ||
                                   string.IsNullOrWhiteSpace(newDisplayName) ||
                                   (newEquipmentSlot == EquipmentSlotType.Weapon &&
                                    newAmmunitionDefinitionId <= 0)))
                        {
                            if (GUILayout.Button("Create + Register", GUILayout.Width(138f)))
                            {
                                CreateItem();
                            }
                        }
                    }
                }
            }

            EditorGUILayout.EndFoldoutHeaderGroup();
        }

        private void DrawValidationSummary()
        {
            if (validationReport == null)
            {
                return;
            }

            MessageType messageType = validationReport.ErrorCount > 0
                ? MessageType.Error
                : validationReport.WarningCount > 0
                    ? MessageType.Warning
                    : MessageType.Info;
            EditorGUILayout.HelpBox(
                "Item content: " + validationReport.GetSummary(),
                messageType);

            if (validationReport.Issues.Count == 0)
            {
                return;
            }

            showValidationIssues = EditorGUILayout.Foldout(
                showValidationIssues,
                "Validation details",
                true);
            if (!showValidationIssues)
            {
                return;
            }

            validationScroll = EditorGUILayout.BeginScrollView(
                validationScroll,
                GUILayout.MaxHeight(130f));
            for (int index = 0; index < validationReport.Issues.Count; index++)
            {
                ItemAuthoringIssue issue = validationReport.Issues[index];
                using (new EditorGUILayout.HorizontalScope())
                {
                    GUILayout.Label(
                        issue.Severity == ItemAuthoringIssueSeverity.Error
                            ? "ERROR"
                            : "WARN",
                        EditorStyles.miniBoldLabel,
                        GUILayout.Width(42f));
                    if (GUILayout.Button(issue.Message, EditorStyles.miniButton))
                    {
                        if (issue.Context != null)
                        {
                            Selection.activeObject = issue.Context;
                            EditorGUIUtility.PingObject(issue.Context);
                        }
                    }
                }
            }
            EditorGUILayout.EndScrollView();
        }

        private void DrawDefinitionBrowser()
        {
            using (new EditorGUILayout.VerticalScope(GUILayout.Width(300f)))
            {
                EditorGUILayout.LabelField("Definitions", EditorStyles.boldLabel);
                searchText = EditorGUILayout.TextField(
                    searchText,
                    EditorStyles.toolbarSearchField);
                kindFilter = EditorGUILayout.Popup(
                    "Kind Filter",
                    Mathf.Clamp(kindFilter, 0, KindFilterLabels.Length - 1),
                    KindFilterLabels);

                listScroll = EditorGUILayout.BeginScrollView(
                    listScroll,
                    EditorStyles.helpBox,
                    GUILayout.ExpandHeight(true));
                int visibleCount = 0;
                for (int index = 0; index < definitions.Count; index++)
                {
                    ItemDefinition definition = definitions[index];
                    if (!MatchesFilters(definition))
                    {
                        continue;
                    }

                    visibleCount++;
                    IssueCounts counts = issueCounts.TryGetValue(
                        definition,
                        out IssueCounts found)
                        ? found
                        : default;
                    string status = counts.Errors > 0
                        ? $" E{counts.Errors}"
                        : counts.Warnings > 0
                            ? $" W{counts.Warnings}"
                            : string.Empty;
                    string registration = IsRegistered(definition) ? string.Empty : " [UNREG]";
                    string label =
                        $"[{definition.Id}] {GetDisplayName(definition)}{registration}{status}";
                    bool nextSelected = GUILayout.Toggle(
                        selectedDefinition == definition,
                        label,
                        EditorStyles.miniButton);
                    if (nextSelected && selectedDefinition != definition)
                    {
                        SelectDefinition(definition, true);
                    }
                }

                if (visibleCount == 0)
                {
                    EditorGUILayout.HelpBox(
                        "No item definitions match the current filter.",
                        MessageType.None);
                }
                EditorGUILayout.EndScrollView();
            }
        }

        private void DrawSelectedDefinition()
        {
            using (new EditorGUILayout.VerticalScope(GUILayout.ExpandWidth(true)))
            {
                if (selectedDefinition == null)
                {
                    EditorGUILayout.HelpBox(
                        "Select an item definition to edit its authoritative asset.",
                        MessageType.Info);
                    return;
                }

                using (new EditorGUILayout.HorizontalScope())
                {
                    EditorGUILayout.LabelField(
                        $"[{selectedDefinition.Id}] {GetDisplayName(selectedDefinition)}",
                        EditorStyles.boldLabel);
                    GUILayout.FlexibleSpace();
                    if (GUILayout.Button("Ping", GUILayout.Width(48f)))
                    {
                        Selection.activeObject = selectedDefinition;
                        EditorGUIUtility.PingObject(selectedDefinition);
                    }

                    using (new EditorGUI.DisabledScope(database == null))
                    {
                        if (GUILayout.Button("Duplicate as New", GUILayout.Width(120f)))
                        {
                            DuplicateSelected();
                        }

                        using (new EditorGUI.DisabledScope(IsRegistered(selectedDefinition)))
                        {
                            if (GUILayout.Button("Register", GUILayout.Width(68f)))
                            {
                                RegisterSelected();
                            }
                        }
                    }
                }

                EditorGUILayout.LabelField(
                    AssetDatabase.GetAssetPath(selectedDefinition),
                    EditorStyles.miniLabel);
                inspectorScroll = EditorGUILayout.BeginScrollView(
                    inspectorScroll,
                    EditorStyles.helpBox,
                    GUILayout.ExpandHeight(true));
                EnsureSelectedEditor();
                if (selectedEditor != null)
                {
                    EditorGUI.BeginChangeCheck();
                    selectedEditor.OnInspectorGUI();
                    if (EditorGUI.EndChangeCheck())
                    {
                        RefreshValidation(false);
                    }
                }
                EditorGUILayout.EndScrollView();
            }
        }

        private void CreateItem()
        {
            try
            {
                var request = new ItemContentCreateRequest
                {
                    AssetName = newAssetName,
                    DisplayName = newDisplayName,
                    Description = newDescription,
                    DefinitionsFolder = definitionsFolder,
                    Kind = newKind,
                    EquipmentSlot = newEquipmentSlot,
                    Width = Mathf.Max(1, newWidth),
                    Height = Mathf.Max(1, newHeight),
                    MaxStackSize = Mathf.Max(1, newMaxStackSize),
                    ContainerWidth = Mathf.Max(1, newContainerWidth),
                    ContainerHeight = Mathf.Max(1, newContainerHeight),
                    AmmunitionDefinitionId = newAmmunitionDefinitionId,
                    Icon = newIcon
                };
                ItemDefinition created =
                    ItemContentAuthoringService.CreateAndRegister(request);
                newAssetName = string.Empty;
                newDisplayName = string.Empty;
                newDescription = string.Empty;
                newIcon = null;
                RefreshAll();
                SelectDefinition(created, true);
                ShowNotification(new GUIContent($"Created and saved item ID {created.Id}."));
            }
            catch (Exception exception)
            {
                HandleOperationException("Item creation failed", exception);
            }
        }

        private void DuplicateSelected()
        {
            try
            {
                ItemDefinition duplicate =
                    ItemContentAuthoringService.DuplicateAndRegister(
                        selectedDefinition,
                        null,
                        definitionsFolder);
                RefreshAll();
                SelectDefinition(duplicate, true);
                ShowNotification(new GUIContent($"Created and saved item ID {duplicate.Id}."));
            }
            catch (Exception exception)
            {
                HandleOperationException("Item duplication failed", exception);
            }
        }

        private void RegisterSelected()
        {
            try
            {
                ItemContentAuthoringService.RegisterExisting(selectedDefinition);
                RefreshAll();
                ShowNotification(new GUIContent("Item registered."));
            }
            catch (Exception exception)
            {
                HandleOperationException("Item registration failed", exception);
            }
        }

        private void RefreshAll()
        {
            definitions.Clear();
            definitions.AddRange(ItemContentAuthoringService.FindAllDefinitions());
            if (selectedDefinition != null && !definitions.Contains(selectedDefinition))
            {
                selectedDefinition = null;
            }

            if (selectedDefinition == null && definitions.Count > 0)
            {
                selectedDefinition = definitions[0];
            }

            RefreshValidation(false);
            RebuildSelectedEditor();
            Repaint();
        }

        private void RefreshValidation(bool logResults)
        {
            validationReport =
                ItemContentAuthoringService.ValidateProject();
            issueCounts.Clear();
            for (int index = 0; index < validationReport.Issues.Count; index++)
            {
                ItemAuthoringIssue issue = validationReport.Issues[index];
                if (!(issue.Context is ItemDefinition definition))
                {
                    continue;
                }

                issueCounts.TryGetValue(definition, out IssueCounts counts);
                if (issue.Severity == ItemAuthoringIssueSeverity.Error)
                {
                    counts.Errors++;
                }
                else
                {
                    counts.Warnings++;
                }
                issueCounts[definition] = counts;
            }

            if (logResults)
            {
                ItemContentAuthoringService.LogValidationReport(validationReport);
            }
        }

        private void SelectDefinition(ItemDefinition definition, bool syncSelection)
        {
            selectedDefinition = definition;
            inspectorScroll = Vector2.zero;
            RebuildSelectedEditor();
            if (syncSelection && definition != null)
            {
                Selection.activeObject = definition;
            }

            Repaint();
        }

        private void EnsureSelectedEditor()
        {
            if (selectedDefinition == null)
            {
                DestroySelectedEditor();
                return;
            }

            if (selectedEditor == null || selectedEditor.target != selectedDefinition)
            {
                RebuildSelectedEditor();
            }
        }

        private void RebuildSelectedEditor()
        {
            DestroySelectedEditor();
            if (selectedDefinition != null)
            {
                selectedEditor = UnityEditor.Editor.CreateEditor(selectedDefinition);
            }
        }

        private void DestroySelectedEditor()
        {
            if (selectedEditor != null)
            {
                DestroyImmediate(selectedEditor);
                selectedEditor = null;
            }
        }

        private bool MatchesFilters(ItemDefinition definition)
        {
            if (definition == null)
            {
                return false;
            }

            if (kindFilter > 0 &&
                definition.Kind != (ItemDefinitionKind)(kindFilter - 1))
            {
                return false;
            }

            if (string.IsNullOrWhiteSpace(searchText))
            {
                return true;
            }

            string query = searchText.Trim();
            return definition.Id.ToString().IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0 ||
                   definition.name.IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0 ||
                   (!string.IsNullOrWhiteSpace(definition.DisplayName) &&
                    definition.DisplayName.IndexOf(
                        query,
                        StringComparison.OrdinalIgnoreCase) >= 0);
        }

        private bool IsRegistered(ItemDefinition definition)
        {
            if (database?.Items == null || definition == null)
            {
                return false;
            }

            for (int index = 0; index < database.Items.Count; index++)
            {
                if (database.Items[index] == definition)
                {
                    return true;
                }
            }

            return false;
        }

        private void ChooseDefinitionsFolder()
        {
            string selected = EditorUtility.OpenFolderPanel(
                "Choose Item Definition Folder",
                Application.dataPath,
                string.Empty);
            if (string.IsNullOrWhiteSpace(selected))
            {
                return;
            }

            string normalizedDataPath = Application.dataPath.Replace('\\', '/');
            string normalizedSelected = selected.Replace('\\', '/');
            if (!normalizedSelected.StartsWith(
                    normalizedDataPath,
                    StringComparison.OrdinalIgnoreCase))
            {
                ShowNotification(new GUIContent("Choose a folder inside Assets."));
                return;
            }

            definitionsFolder = "Assets" +
                normalizedSelected.Substring(normalizedDataPath.Length);
        }

        private void DrawCreateAmmunitionPopup()
        {
            var ids = new List<int>();
            var labels = new List<string>();
            if (database?.Items != null)
            {
                for (int index = 0; index < database.Items.Count; index++)
                {
                    ItemDefinition definition = database.Items[index];
                    if (definition == null || !definition.IsAmmunition)
                    {
                        continue;
                    }

                    ids.Add(definition.Id);
                    labels.Add($"[{definition.Id}] {GetDisplayName(definition)}");
                }
            }

            if (ids.Count == 0)
            {
                newAmmunitionDefinitionId = 0;
                EditorGUILayout.HelpBox(
                    "Create and register an ammunition item before creating a weapon.",
                    MessageType.Error);
                return;
            }

            int selectedIndex = ids.IndexOf(newAmmunitionDefinitionId);
            if (selectedIndex < 0)
            {
                selectedIndex = 0;
                newAmmunitionDefinitionId = ids[0];
            }

            int nextIndex = EditorGUILayout.Popup(
                "Ammunition",
                selectedIndex,
                labels.ToArray());
            newAmmunitionDefinitionId = ids[nextIndex];
        }

        private void HandleExternalChange()
        {
            RefreshAll();
        }

        private void HandleSelectionChanged()
        {
            if (Selection.activeObject is ItemDefinition definition &&
                definitions.Contains(definition) &&
                selectedDefinition != definition)
            {
                SelectDefinition(definition, false);
            }
        }

        private static string GetDisplayName(ItemDefinition definition)
        {
            return string.IsNullOrWhiteSpace(definition.DisplayName)
                ? definition.name
                : definition.DisplayName;
        }

        private static void HandleOperationException(
            string label,
            Exception exception)
        {
            Debug.LogError($"{label}: {exception.Message}");
            Debug.LogException(exception);
        }
    }
}
