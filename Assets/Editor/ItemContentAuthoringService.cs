using System;
using System.Collections.Generic;
using System.IO;
using FantasySurvival.Combat;
using FantasySurvival.Inventory;
using FantasySurvival.Trading;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    public enum ItemAuthoringIssueSeverity
    {
        Warning,
        Error
    }

    public sealed class ItemAuthoringIssue
    {
        public ItemAuthoringIssue(
            ItemAuthoringIssueSeverity severity,
            string message,
            UnityEngine.Object context = null)
        {
            Severity = severity;
            Message = message;
            Context = context;
        }

        public ItemAuthoringIssueSeverity Severity { get; }
        public string Message { get; }
        public UnityEngine.Object Context { get; }
    }

    public sealed class ItemAuthoringValidationReport
    {
        private readonly List<ItemAuthoringIssue> issues =
            new List<ItemAuthoringIssue>();

        public IReadOnlyList<ItemAuthoringIssue> Issues => issues;
        public int DefinitionCount { get; internal set; }
        public int RegisteredCount { get; internal set; }
        public int ErrorCount { get; private set; }
        public int WarningCount { get; private set; }
        public bool IsValid => ErrorCount == 0;

        internal void Add(
            ItemAuthoringIssueSeverity severity,
            string message,
            UnityEngine.Object context = null)
        {
            issues.Add(new ItemAuthoringIssue(severity, message, context));
            if (severity == ItemAuthoringIssueSeverity.Error)
            {
                ErrorCount++;
            }
            else
            {
                WarningCount++;
            }
        }

        public string GetSummary()
        {
            return
                $"Definitions {DefinitionCount}, registered {RegisteredCount}, " +
                $"errors {ErrorCount}, warnings {WarningCount}";
        }
    }

    public sealed class ItemContentCreateRequest
    {
        public string AssetName { get; set; }
        public string DisplayName { get; set; }
        public string Description { get; set; }
        public string DefinitionsFolder { get; set; } =
            ItemContentAuthoringService.DefaultDefinitionsFolder;
        public ItemDefinitionKind Kind { get; set; } = ItemDefinitionKind.Standard;
        public EquipmentSlotType EquipmentSlot { get; set; } = EquipmentSlotType.None;
        public int BackpackBonusRows { get; set; }
        public int DefensePercent { get; set; }
        public int Width { get; set; } = 1;
        public int Height { get; set; } = 1;
        public int MaxStackSize { get; set; } = 1;
        public int ContainerWidth { get; set; } = 1;
        public int ContainerHeight { get; set; } = 1;
        public bool IsTradable { get; set; }
        public TradeCurrency TradeCurrency { get; set; } = TradeCurrency.Silver;
        public int TradePrice { get; set; }
        public WeaponFireMode WeaponFireMode { get; set; } =
            WeaponFireMode.SemiAutomatic;
        public float RoundsPerMinute { get; set; } = 300f;
        public int AmmunitionDefinitionId { get; set; }
        public int MagazineCapacity { get; set; } = 3;
        public float ReloadDurationSeconds { get; set; } = 2.5f;
        public float WeaponDamage { get; set; } = 350f;
        public float WeaponRange { get; set; } = 30f;
        public float WeaponNoiseRadius { get; set; } = 18f;
        public float MedicineUseDurationSeconds { get; set; } = 2.5f;
        public float MedicineHealthRestored { get; set; } = 350f;
        public Texture2D Icon { get; set; }
    }

    internal static class ItemDefinitionSerializedFields
    {
        public const string Id = "id";
        public const string DisplayName = "displayName";
        public const string Description = "description";
        public const string Width = "width";
        public const string Height = "height";
        public const string Icon = "icon";
        public const string MaxStackSize = "maxStackSize";
        public const string EquipmentSlot = "equipmentSlot";
        public const string BackpackBonusRows = "backpackBonusRows";
        public const string DefensePercent = "defensePercent";
        public const string IsTradable = "isTradable";
        public const string TradeCurrency = "tradeCurrency";
        public const string TradePrice = "tradePrice";
        public const string WeaponFireMode = "weaponFireMode";
        public const string RoundsPerMinute = "roundsPerMinute";
        public const string AmmunitionDefinitionId = "ammunitionDefinitionId";
        public const string MagazineCapacity = "magazineCapacity";
        public const string ReloadDurationSeconds = "reloadDurationSeconds";
        public const string WeaponDamage = "weaponDamage";
        public const string WeaponRange = "weaponRange";
        public const string WeaponNoiseRadius = "weaponNoiseRadius";
        public const string MedicineUseDurationSeconds = "medicineUseDurationSeconds";
        public const string MedicineHealthRestored = "medicineHealthRestored";
        public const string Kind = "kind";
        public const string ContainerWidth = "containerWidth";
        public const string ContainerHeight = "containerHeight";
        public const string DatabaseItems = "items";
        public const string DatabaseNextDefinitionId = "nextDefinitionId";
    }

    /// <summary>
    /// Editor-only entry point shared by the authoring window and Unity RunCommand.
    /// ItemDefinition assets and ItemDatabase remain the only content authorities.
    /// </summary>
    public static class ItemContentAuthoringService
    {
        public const string DefaultDatabasePath =
            "Assets/GameData/Items/ItemDatabase.asset";
        public const string DefaultDefinitionsFolder =
            "Assets/GameData/Items/Definitions";

        public static ItemDatabase LoadDefaultDatabase()
        {
            return AssetDatabase.LoadAssetAtPath<ItemDatabase>(DefaultDatabasePath);
        }

        public static List<ItemDefinition> FindAllDefinitions()
        {
            string[] guids = AssetDatabase.FindAssets("t:ItemDefinition");
            var definitions = new List<ItemDefinition>(guids.Length);
            for (int index = 0; index < guids.Length; index++)
            {
                string path = AssetDatabase.GUIDToAssetPath(guids[index]);
                ItemDefinition definition =
                    AssetDatabase.LoadAssetAtPath<ItemDefinition>(path);
                if (definition != null)
                {
                    definitions.Add(definition);
                }
            }

            definitions.Sort(CompareDefinitions);
            return definitions;
        }

        public static int GetNextStableId()
        {
            return GetNextStableId(RequireDefaultDatabase());
        }

        private static int GetNextStableId(ItemDatabase database)
        {
            int maximumId = 0;
            List<ItemDefinition> definitions = FindAllDefinitions();
            for (int index = 0; index < definitions.Count; index++)
            {
                maximumId = Mathf.Max(maximumId, definitions[index].Id);
            }

            if (maximumId == int.MaxValue ||
                database.NextDefinitionId == int.MaxValue)
            {
                throw new InvalidOperationException(
                    "No item definition ID remains after Int32.MaxValue.");
            }

            return Mathf.Max(database.NextDefinitionId, maximumId + 1);
        }

        public static ItemAuthoringValidationReport ValidateProject()
        {
            return ValidateProject(LoadDefaultDatabase());
        }

        private static ItemAuthoringValidationReport ValidateProject(
            ItemDatabase database)
        {
            var report = new ItemAuthoringValidationReport();
            List<ItemDefinition> definitions = FindAllDefinitions();
            report.DefinitionCount = definitions.Count;

            if (database == null)
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Error,
                    "ItemDatabase is not assigned.");
                return report;
            }

            if (!database.TryValidate(out string databaseError))
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Error,
                    databaseError,
                    database);
            }

            var registeredDefinitions = new HashSet<ItemDefinition>();
            if (database.Items != null)
            {
                report.RegisteredCount = database.Items.Count;
                for (int index = 0; index < database.Items.Count; index++)
                {
                    ItemDefinition definition = database.Items[index];
                    if (definition != null)
                    {
                        registeredDefinitions.Add(definition);
                    }
                }
            }

            var definitionsById = new Dictionary<int, ItemDefinition>();
            int maximumProjectId = 0;
            for (int index = 0; index < definitions.Count; index++)
            {
                ItemDefinition definition = definitions[index];
                maximumProjectId = Mathf.Max(maximumProjectId, definition.Id);
                if (definitionsById.TryGetValue(
                        definition.Id,
                        out ItemDefinition duplicate))
                {
                    report.Add(
                        ItemAuthoringIssueSeverity.Error,
                        $"Project item ID {definition.Id} is shared by " +
                        $"'{duplicate.name}' and '{definition.name}'.",
                        definition);
                }
                else
                {
                    definitionsById.Add(definition.Id, definition);
                }

                if (!definition.TryValidateInventoryShape(out string definitionError))
                {
                    report.Add(
                        ItemAuthoringIssueSeverity.Error,
                        definitionError,
                        definition);
                }

                if (!registeredDefinitions.Contains(definition))
                {
                    report.Add(
                        ItemAuthoringIssueSeverity.Warning,
                        $"Item definition ID {definition.Id} '{definition.name}' is not " +
                        "registered in the selected ItemDatabase.",
                        definition);
                }

                AddPresentationWarnings(report, definition);
            }

            if (maximumProjectId < int.MaxValue &&
                database.NextDefinitionId <= maximumProjectId)
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Error,
                    $"ItemDatabase next ID {database.NextDefinitionId} does not " +
                    $"reserve project item IDs through {maximumProjectId}.",
                    database);
            }

            return report;
        }

        public static ItemDefinition CreateAndRegister(
            ItemContentCreateRequest request)
        {
            return CreateAndRegisterInternal(request, RequireDefaultDatabase());
        }

        /// <summary>
        /// Automation alias for the same immediately saved transaction used by the window.
        /// A Unity RunCommand caller should report the returned asset and modified database
        /// through its execution result. Creation is intentionally not a Ctrl+Z operation.
        /// </summary>
        public static ItemDefinition CreateAndRegisterForAutomation(
            ItemContentCreateRequest request)
        {
            return CreateAndRegister(request);
        }

        private static ItemDefinition CreateAndRegisterInternal(
            ItemContentCreateRequest request,
            ItemDatabase database)
        {
            ValidateCreateRequest(request, database);
            EnsureAssetFolder(request.DefinitionsFolder);

            int definitionId = GetNextStableId(database);
            string assetName = SanitizeAssetName(
                string.IsNullOrWhiteSpace(request.AssetName)
                    ? request.DisplayName
                    : request.AssetName);
            if (string.IsNullOrWhiteSpace(assetName))
            {
                assetName = $"Item_{definitionId}";
            }

            string folder = NormalizeAssetFolder(request.DefinitionsFolder);
            string assetPath = AssetDatabase.GenerateUniqueAssetPath(
                $"{folder}/{assetName}.asset");
            ItemDefinition definition = ScriptableObject.CreateInstance<ItemDefinition>();
            definition.name = Path.GetFileNameWithoutExtension(assetPath);

            var serialized = new SerializedObject(definition);
            SetInteger(serialized, ItemDefinitionSerializedFields.Id, definitionId);
            SetString(serialized, ItemDefinitionSerializedFields.DisplayName, request.DisplayName);
            SetString(serialized, ItemDefinitionSerializedFields.Description, request.Description);
            SetInteger(serialized, ItemDefinitionSerializedFields.Width, request.Width);
            SetInteger(serialized, ItemDefinitionSerializedFields.Height, request.Height);
            SetObject(serialized, ItemDefinitionSerializedFields.Icon, request.Icon);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.MaxStackSize,
                request.Kind == ItemDefinitionKind.Container ||
                request.EquipmentSlot != EquipmentSlotType.None
                    ? 1
                    : request.MaxStackSize);
            SetEnum(
                serialized,
                ItemDefinitionSerializedFields.EquipmentSlot,
                (int)request.EquipmentSlot);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.BackpackBonusRows,
                request.BackpackBonusRows);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.DefensePercent,
                request.EquipmentSlot == EquipmentSlotType.BodyArmor
                    ? request.DefensePercent
                    : 0);
            SetBoolean(
                serialized,
                ItemDefinitionSerializedFields.IsTradable,
                request.IsTradable);
            SetEnum(
                serialized,
                ItemDefinitionSerializedFields.TradeCurrency,
                (int)request.TradeCurrency);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.TradePrice,
                request.TradePrice);
            SetEnum(serialized, ItemDefinitionSerializedFields.Kind, (int)request.Kind);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.ContainerWidth,
                request.ContainerWidth);
            SetInteger(
                serialized,
                ItemDefinitionSerializedFields.ContainerHeight,
                request.ContainerHeight);
            if (request.EquipmentSlot == EquipmentSlotType.Weapon)
            {
                SetEnum(
                    serialized,
                    ItemDefinitionSerializedFields.WeaponFireMode,
                    (int)request.WeaponFireMode);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.RoundsPerMinute,
                    request.RoundsPerMinute);
                SetInteger(
                    serialized,
                    ItemDefinitionSerializedFields.AmmunitionDefinitionId,
                    request.AmmunitionDefinitionId);
                SetInteger(
                    serialized,
                    ItemDefinitionSerializedFields.MagazineCapacity,
                    request.MagazineCapacity);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.ReloadDurationSeconds,
                    request.ReloadDurationSeconds);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.WeaponDamage,
                    request.WeaponDamage);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.WeaponRange,
                    request.WeaponRange);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.WeaponNoiseRadius,
                    request.WeaponNoiseRadius);
            }
            if (request.Kind == ItemDefinitionKind.Medicine)
            {
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.MedicineUseDurationSeconds,
                    request.MedicineUseDurationSeconds);
                SetFloat(
                    serialized,
                    ItemDefinitionSerializedFields.MedicineHealthRestored,
                    request.MedicineHealthRestored);
            }
            serialized.ApplyModifiedPropertiesWithoutUndo();

            if (!definition.TryValidateInventoryShape(out string definitionError))
            {
                UnityEngine.Object.DestroyImmediate(definition);
                throw new InvalidOperationException(definitionError);
            }

            ReserveDefinitionId(database, definitionId);
            return CreatePreparedAndRegister(definition, assetPath, database);
        }

        public static ItemDefinition DuplicateAndRegister(
            ItemDefinition source,
            string assetName = null,
            string definitionsFolder = DefaultDefinitionsFolder)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }

            ItemDatabase database = RequireDefaultDatabase();
            ValidateEditorReady(database);
            EnsureAssetFolder(definitionsFolder);

            if (!database.TryValidate(out string databaseError))
            {
                throw new InvalidOperationException(databaseError);
            }

            ItemDefinition duplicate = ScriptableObject.CreateInstance<ItemDefinition>();
            EditorUtility.CopySerialized(source, duplicate);
            int definitionId = GetNextStableId(database);
            string requestedName = SanitizeAssetName(
                string.IsNullOrWhiteSpace(assetName)
                    ? source.name + "_Copy"
                    : assetName);
            if (string.IsNullOrWhiteSpace(requestedName))
            {
                requestedName = source.name + "_Copy";
            }
            string folder = NormalizeAssetFolder(definitionsFolder);
            string assetPath = AssetDatabase.GenerateUniqueAssetPath(
                $"{folder}/{requestedName}.asset");
            duplicate.name = Path.GetFileNameWithoutExtension(assetPath);

            var serialized = new SerializedObject(duplicate);
            SetInteger(serialized, ItemDefinitionSerializedFields.Id, definitionId);
            serialized.ApplyModifiedPropertiesWithoutUndo();

            if (!duplicate.TryValidateInventoryShape(out string definitionError))
            {
                UnityEngine.Object.DestroyImmediate(duplicate);
                throw new InvalidOperationException(definitionError);
            }

            ReserveDefinitionId(database, definitionId);
            return CreatePreparedAndRegister(duplicate, assetPath, database);
        }

        public static void RegisterExisting(
            ItemDefinition definition)
        {
            if (definition == null)
            {
                throw new ArgumentNullException(nameof(definition));
            }

            ItemDatabase database = RequireDefaultDatabase();
            ValidateEditorReady(database);
            if (!AssetDatabase.Contains(definition))
            {
                throw new InvalidOperationException(
                    "Only a saved ItemDefinition asset can be registered.");
            }

            if (!definition.TryValidateInventoryShape(out string definitionError))
            {
                throw new InvalidOperationException(definitionError);
            }

            EnsureProjectIdIsUnique(definition);

            if (!database.TryValidate(out string databaseError))
            {
                throw new InvalidOperationException(databaseError);
            }

            List<ItemDefinition> snapshot = SnapshotDatabase(database);
            for (int index = 0; index < snapshot.Count; index++)
            {
                ItemDefinition existing = snapshot[index];
                if (existing == definition)
                {
                    ReserveDefinitionId(database, definition.Id);
                    return;
                }

                if (existing != null && existing.Id == definition.Id)
                {
                    throw new InvalidOperationException(
                        $"ItemDatabase already uses item ID {definition.Id} at " +
                        $"'{existing.name}'.");
                }
            }

            ReserveDefinitionId(database, definition.Id);

            int undoGroup = BeginUndoGroup("Register Item Definition");
            try
            {
                Undo.RegisterCompleteObjectUndo(database, "Register Item Definition");
                AppendDatabaseEntry(database, definition);
                if (!database.TryValidate(out databaseError))
                {
                    throw new InvalidOperationException(databaseError);
                }

                EditorUtility.SetDirty(database);
                AssetDatabase.SaveAssetIfDirty(database);
                Undo.CollapseUndoOperations(undoGroup);
            }
            catch (Exception operationException)
            {
                var rollbackErrors = new List<Exception>();
                try
                {
                    Undo.RevertAllDownToGroup(undoGroup);
                }
                catch (Exception undoException)
                {
                    rollbackErrors.Add(undoException);
                }

                Exception restoreException = TryRestoreDatabaseState(
                    database,
                    snapshot);
                if (restoreException != null)
                {
                    rollbackErrors.Add(restoreException);
                }

                if (rollbackErrors.Count > 0)
                {
                    rollbackErrors.Insert(0, operationException);
                    throw new AggregateException(
                        "Item registration failed and its database rollback was incomplete.",
                        rollbackErrors);
                }

                throw;
            }
        }

        public static void LogValidationReport(ItemAuthoringValidationReport report)
        {
            if (report == null)
            {
                throw new ArgumentNullException(nameof(report));
            }

            for (int index = 0; index < report.Issues.Count; index++)
            {
                ItemAuthoringIssue issue = report.Issues[index];
                if (issue.Severity == ItemAuthoringIssueSeverity.Error)
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
                Debug.Log($"Item content validation complete: {report.GetSummary()}.");
            }
        }

        private static ItemDefinition CreatePreparedAndRegister(
            ItemDefinition definition,
            string assetPath,
            ItemDatabase database)
        {
            ValidateEditorReady(database);
            if (!database.TryValidate(out string databaseError))
            {
                UnityEngine.Object.DestroyImmediate(definition);
                throw new InvalidOperationException(databaseError);
            }

            List<ItemDefinition> snapshot = SnapshotDatabase(database);
            try
            {
                AssetDatabase.CreateAsset(definition, assetPath);
                AppendDatabaseEntry(database, definition);

                if (!database.TryValidate(out databaseError))
                {
                    throw new InvalidOperationException(databaseError);
                }

                EditorUtility.SetDirty(definition);
                EditorUtility.SetDirty(database);
                AssetDatabase.SaveAssetIfDirty(definition);
                AssetDatabase.SaveAssetIfDirty(database);
                return definition;
            }
            catch (Exception operationException)
            {
                var rollbackErrors = new List<Exception>();
                Exception restoreException = TryRestoreDatabaseState(
                    database,
                    snapshot);
                if (restoreException != null)
                {
                    rollbackErrors.Add(restoreException);
                }

                Exception deleteException = TryDeleteCreatedAsset(
                    definition,
                    assetPath);
                if (deleteException != null)
                {
                    rollbackErrors.Add(deleteException);
                }

                if (rollbackErrors.Count > 0)
                {
                    rollbackErrors.Insert(0, operationException);
                    throw new AggregateException(
                        "Item creation failed and its rollback was incomplete.",
                        rollbackErrors);
                }

                throw;
            }
        }

        private static void ValidateCreateRequest(
            ItemContentCreateRequest request,
            ItemDatabase database)
        {
            if (request == null)
            {
                throw new ArgumentNullException(nameof(request));
            }

            ValidateEditorReady(database);
            if (string.IsNullOrWhiteSpace(request.DisplayName))
            {
                throw new InvalidOperationException("Display name is required.");
            }

            if (!Enum.IsDefined(typeof(ItemDefinitionKind), request.Kind) ||
                !Enum.IsDefined(typeof(EquipmentSlotType), request.EquipmentSlot))
            {
                throw new InvalidOperationException("Item kind or equipment slot is invalid.");
            }

            if (request.Kind == ItemDefinitionKind.Container &&
                request.EquipmentSlot == EquipmentSlotType.Weapon)
            {
                throw new InvalidOperationException(
                    "An item cannot be both a container and a weapon.");
            }

            if (request.BackpackBonusRows < 0 ||
                request.BackpackBonusRows > InventoryGridConstraints.MaxDimension ||
                (request.BackpackBonusRows > 0 &&
                 request.EquipmentSlot != EquipmentSlotType.Backpack) ||
                (request.BackpackBonusRows > 0 &&
                 request.Kind == ItemDefinitionKind.Container))
            {
                throw new InvalidOperationException(
                    "Backpack bonus rows must be within the inventory dimension limit, " +
                    "and only a non-container Backpack item may grant them.");
            }

            if (request.DefensePercent < 0 ||
                request.DefensePercent > CombatValueRules.MaximumDefensePercent ||
                (request.DefensePercent > 0 &&
                 request.EquipmentSlot != EquipmentSlotType.BodyArmor))
            {
                throw new InvalidOperationException(
                    "Defense must be between 0 and 100 and belongs only to Body Armor.");
            }

            if (!InventoryGridConstraints.TryValidateDimensions(
                    request.Width,
                    request.Height,
                    out string inventoryError))
            {
                throw new InvalidOperationException(inventoryError);
            }

            if (request.MaxStackSize <= 0)
            {
                throw new InvalidOperationException("Maximum stack size must be positive.");
            }

            if (!PlayerWallet.IsValidCurrency(request.TradeCurrency) ||
                request.TradePrice < 0 ||
                (request.IsTradable && request.TradePrice == 0))
            {
                throw new InvalidOperationException(
                    "Trading data requires a valid currency, a non-negative price, " +
                    "and a positive price when enabled.");
            }

            if (request.Kind == ItemDefinitionKind.Container &&
                !InventoryGridConstraints.TryValidateDimensions(
                    request.ContainerWidth,
                    request.ContainerHeight,
                    out string containerError))
            {
                throw new InvalidOperationException(containerError);
            }

            if (!database.TryValidate(out string databaseError))
            {
                throw new InvalidOperationException(databaseError);
            }

            if (request.EquipmentSlot == EquipmentSlotType.Weapon &&
                (!database.TryGet(
                     request.AmmunitionDefinitionId,
                     out ItemDefinition ammunition) ||
                 !ammunition.IsAmmunition))
            {
                throw new InvalidOperationException(
                    $"Weapon creation requires a registered ammunition item, but ID " +
                    $"{request.AmmunitionDefinitionId} is not valid ammunition.");
            }

            if (request.EquipmentSlot == EquipmentSlotType.Weapon &&
                (!Enum.IsDefined(typeof(WeaponFireMode), request.WeaponFireMode) ||
                 !IsFinitePositive(request.RoundsPerMinute) ||
                 request.MagazineCapacity <= 0 ||
                 !IsFinitePositive(request.ReloadDurationSeconds) ||
                 !CombatValueRules.IsAttackPowerValid(request.WeaponDamage) ||
                 !IsFinitePositive(request.WeaponRange) ||
                 !IsFiniteNonNegative(request.WeaponNoiseRadius)))
            {
                throw new InvalidOperationException(
                    "Weapon cadence, magazine, reload, damage, range, or noise values are invalid.");
            }

            if (request.Kind == ItemDefinitionKind.Medicine &&
                (!IsFinitePositive(request.MedicineUseDurationSeconds) ||
                 !IsFinitePositive(request.MedicineHealthRestored)))
            {
                throw new InvalidOperationException(
                    "Medicine use duration and healing amount must be finite and positive.");
            }
        }

        private static bool IsFinitePositive(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value) && value > 0f;
        }

        private static bool IsFiniteNonNegative(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value) && value >= 0f;
        }

        private static ItemDatabase RequireDefaultDatabase()
        {
            ItemDatabase database = LoadDefaultDatabase();
            if (database == null || !AssetDatabase.Contains(database))
            {
                throw new InvalidOperationException(
                    $"The authoritative ItemDatabase is missing at " +
                    $"'{DefaultDatabasePath}'.");
            }

            return database;
        }

        private static void EnsureProjectIdIsUnique(ItemDefinition definition)
        {
            List<ItemDefinition> definitions = FindAllDefinitions();
            for (int index = 0; index < definitions.Count; index++)
            {
                ItemDefinition other = definitions[index];
                if (other != definition && other.Id == definition.Id)
                {
                    throw new InvalidOperationException(
                        $"Project item ID {definition.Id} is already used by " +
                        $"'{other.name}'.");
                }
            }
        }

        private static void ValidateEditorReady(ItemDatabase database)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                throw new InvalidOperationException(
                    "Item content assets can only be changed in Edit Mode.");
            }

            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new InvalidOperationException(
                    "Wait for Unity compilation and asset import to finish.");
            }

            if (database == null || !AssetDatabase.Contains(database))
            {
                throw new InvalidOperationException(
                    "A saved ItemDatabase asset must be assigned.");
            }
        }

        private static void AddPresentationWarnings(
            ItemAuthoringValidationReport report,
            ItemDefinition definition)
        {
            if (string.IsNullOrWhiteSpace(definition.DisplayName))
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Warning,
                    $"Item definition ID {definition.Id} has no display name.",
                    definition);
            }

            if (string.IsNullOrWhiteSpace(definition.Description))
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Warning,
                    $"Item definition ID {definition.Id} has no description.",
                    definition);
            }

            if (definition.Icon == null)
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Warning,
                    $"Item definition ID {definition.Id} has no icon.",
                    definition);
            }

            var serialized = new SerializedObject(definition);
            SerializedProperty authoredTradable =
                serialized.FindProperty(ItemDefinitionSerializedFields.IsTradable);
            SerializedProperty authoredPrice =
                serialized.FindProperty(ItemDefinitionSerializedFields.TradePrice);
            if (authoredTradable != null && authoredTradable.boolValue &&
                (definition.IsContainer || authoredPrice == null || authoredPrice.intValue <= 0))
            {
                report.Add(
                    ItemAuthoringIssueSeverity.Warning,
                    $"Item definition ID {definition.Id} has an inactive trading " +
                    "configuration (container or non-positive price).",
                    definition);
            }
        }

        private static int BeginUndoGroup(string name)
        {
            Undo.IncrementCurrentGroup();
            int group = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName(name);
            return group;
        }

        private static void ReserveDefinitionId(
            ItemDatabase database,
            int definitionId)
        {
            if (definitionId <= 0)
            {
                throw new InvalidOperationException(
                    "Item definition IDs must be positive before they can be reserved.");
            }

            var serialized = new SerializedObject(database);
            SerializedProperty nextId = serialized.FindProperty(
                ItemDefinitionSerializedFields.DatabaseNextDefinitionId);
            if (nextId == null)
            {
                throw new InvalidOperationException(
                    "ItemDatabase next definition ID field is missing.");
            }

            int reservedNextId = definitionId == int.MaxValue
                ? int.MaxValue
                : definitionId + 1;
            if (nextId.intValue >= reservedNextId)
            {
                return;
            }

            nextId.intValue = reservedNextId;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(database);
            AssetDatabase.SaveAssetIfDirty(database);
        }

        private static List<ItemDefinition> SnapshotDatabase(ItemDatabase database)
        {
            var snapshot = new List<ItemDefinition>();
            if (database.Items == null)
            {
                return snapshot;
            }

            for (int index = 0; index < database.Items.Count; index++)
            {
                snapshot.Add(database.Items[index]);
            }

            return snapshot;
        }

        private static void AppendDatabaseEntry(
            ItemDatabase database,
            ItemDefinition definition)
        {
            var serialized = new SerializedObject(database);
            SerializedProperty items =
                serialized.FindProperty(ItemDefinitionSerializedFields.DatabaseItems);
            if (items == null || !items.isArray)
            {
                throw new InvalidOperationException(
                    "ItemDatabase serialized item list is missing.");
            }

            int index = items.arraySize;
            items.arraySize++;
            items.GetArrayElementAtIndex(index).objectReferenceValue = definition;
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void RestoreDatabase(
            ItemDatabase database,
            IReadOnlyList<ItemDefinition> snapshot)
        {
            var serialized = new SerializedObject(database);
            SerializedProperty items =
                serialized.FindProperty(ItemDefinitionSerializedFields.DatabaseItems);
            if (items == null || !items.isArray)
            {
                return;
            }

            items.arraySize = snapshot.Count;
            for (int index = 0; index < snapshot.Count; index++)
            {
                items.GetArrayElementAtIndex(index).objectReferenceValue = snapshot[index];
            }

            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(database);
        }

        private static Exception TryRestoreDatabaseState(
            ItemDatabase database,
            IReadOnlyList<ItemDefinition> snapshot)
        {
            try
            {
                RestoreDatabase(database, snapshot);
                if (!database.TryValidate(out string validationError))
                {
                    throw new InvalidOperationException(validationError);
                }

                AssetDatabase.SaveAssetIfDirty(database);
                return null;
            }
            catch (Exception exception)
            {
                return exception;
            }
        }

        private static Exception TryDeleteCreatedAsset(
            ItemDefinition definition,
            string assetPath)
        {
            try
            {
                UnityEngine.Object savedAsset =
                    AssetDatabase.LoadMainAssetAtPath(assetPath);
                if (savedAsset != null)
                {
                    if (!AssetDatabase.DeleteAsset(assetPath))
                    {
                        throw new IOException(
                            $"Failed to delete rolled-back item asset '{assetPath}'.");
                    }
                }
                else if (definition != null && !AssetDatabase.Contains(definition))
                {
                    UnityEngine.Object.DestroyImmediate(definition);
                }

                return null;
            }
            catch (Exception exception)
            {
                return exception;
            }
        }

        private static void EnsureAssetFolder(string requestedFolder)
        {
            string folder = NormalizeAssetFolder(requestedFolder);
            if (AssetDatabase.IsValidFolder(folder))
            {
                return;
            }

            string[] segments = folder.Split('/');
            if (segments.Length == 0 || segments[0] != "Assets")
            {
                throw new InvalidOperationException(
                    "Item definition folder must be inside Assets.");
            }

            string parent = "Assets";
            for (int index = 1; index < segments.Length; index++)
            {
                string segment = segments[index];
                if (string.IsNullOrWhiteSpace(segment))
                {
                    throw new InvalidOperationException(
                        "Item definition folder contains an empty segment.");
                }

                string child = $"{parent}/{segment}";
                if (!AssetDatabase.IsValidFolder(child))
                {
                    AssetDatabase.CreateFolder(parent, segment);
                }

                parent = child;
            }
        }

        private static string NormalizeAssetFolder(string folder)
        {
            string normalized = string.IsNullOrWhiteSpace(folder)
                ? DefaultDefinitionsFolder
                : folder.Trim().Replace('\\', '/').TrimEnd('/');
            if (normalized != "Assets" && !normalized.StartsWith("Assets/", StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "Item definition folder must be inside Assets.");
            }

            return normalized;
        }

        private static string SanitizeAssetName(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return string.Empty;
            }

            char[] characters = value.Trim().ToCharArray();
            char[] invalid = Path.GetInvalidFileNameChars();
            for (int index = 0; index < characters.Length; index++)
            {
                char character = characters[index];
                if (character == '/' || character == '\\' ||
                    Array.IndexOf(invalid, character) >= 0)
                {
                    characters[index] = '_';
                }
            }

            return new string(characters).Trim().TrimEnd('.');
        }

        private static int CompareDefinitions(
            ItemDefinition left,
            ItemDefinition right)
        {
            int idComparison = left.Id.CompareTo(right.Id);
            if (idComparison != 0)
            {
                return idComparison;
            }

            return string.Compare(
                AssetDatabase.GetAssetPath(left),
                AssetDatabase.GetAssetPath(right),
                StringComparison.Ordinal);
        }

        private static void SetInteger(
            SerializedObject serialized,
            string propertyName,
            int value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"ItemDefinition field '{propertyName}' is missing.");
            }

            property.intValue = value;
        }

        private static void SetFloat(
            SerializedObject serialized,
            string propertyName,
            float value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"Serialized float field '{propertyName}' is missing.");
            }

            property.floatValue = value;
        }

        private static void SetBoolean(
            SerializedObject serialized,
            string propertyName,
            bool value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"Serialized boolean field '{propertyName}' is missing.");
            }

            property.boolValue = value;
        }

        private static void SetString(
            SerializedObject serialized,
            string propertyName,
            string value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"ItemDefinition field '{propertyName}' is missing.");
            }

            property.stringValue = value ?? string.Empty;
        }

        private static void SetObject(
            SerializedObject serialized,
            string propertyName,
            UnityEngine.Object value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"ItemDefinition field '{propertyName}' is missing.");
            }

            property.objectReferenceValue = value;
        }

        private static void SetEnum(
            SerializedObject serialized,
            string propertyName,
            int value)
        {
            SerializedProperty property = serialized.FindProperty(propertyName);
            if (property == null)
            {
                throw new InvalidOperationException(
                    $"ItemDefinition field '{propertyName}' is missing.");
            }

            // enumValueIndex is the declaration-order index, not the enum's
            // serialized integer value. TradeCurrency intentionally starts at 1,
            // so assigning its underlying value as an index logs an out-of-range
            // error even though the saved value is valid.
            property.intValue = value;
        }
    }
}
