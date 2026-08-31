using System.Collections.Generic;
using FantasySurvival.Inventory;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    [CustomEditor(typeof(ItemDefinition))]
    public sealed class ItemDefinitionEditor : UnityEditor.Editor
    {
        private SerializedProperty id;
        private SerializedProperty displayName;
        private SerializedProperty description;
        private SerializedProperty width;
        private SerializedProperty height;
        private SerializedProperty icon;
        private SerializedProperty maxStackSize;
        private SerializedProperty equipmentSlot;
        private SerializedProperty backpackBonusRows;
        private SerializedProperty isTradable;
        private SerializedProperty tradeCurrency;
        private SerializedProperty tradePrice;
        private SerializedProperty weaponFireMode;
        private SerializedProperty roundsPerMinute;
        private SerializedProperty ammunitionDefinitionId;
        private SerializedProperty magazineCapacity;
        private SerializedProperty reloadDurationSeconds;
        private SerializedProperty weaponDamage;
        private SerializedProperty weaponRange;
        private SerializedProperty weaponNoiseRadius;
        private SerializedProperty medicineUseDurationSeconds;
        private SerializedProperty medicineHealthRestored;
        private SerializedProperty kind;
        private SerializedProperty containerWidth;
        private SerializedProperty containerHeight;

        private void OnEnable()
        {
            id = Find(ItemDefinitionSerializedFields.Id);
            displayName = Find(ItemDefinitionSerializedFields.DisplayName);
            description = Find(ItemDefinitionSerializedFields.Description);
            width = Find(ItemDefinitionSerializedFields.Width);
            height = Find(ItemDefinitionSerializedFields.Height);
            icon = Find(ItemDefinitionSerializedFields.Icon);
            maxStackSize = Find(ItemDefinitionSerializedFields.MaxStackSize);
            equipmentSlot = Find(ItemDefinitionSerializedFields.EquipmentSlot);
            backpackBonusRows = Find(ItemDefinitionSerializedFields.BackpackBonusRows);
            isTradable = Find(ItemDefinitionSerializedFields.IsTradable);
            tradeCurrency = Find(ItemDefinitionSerializedFields.TradeCurrency);
            tradePrice = Find(ItemDefinitionSerializedFields.TradePrice);
            weaponFireMode = Find(ItemDefinitionSerializedFields.WeaponFireMode);
            roundsPerMinute = Find(ItemDefinitionSerializedFields.RoundsPerMinute);
            ammunitionDefinitionId =
                Find(ItemDefinitionSerializedFields.AmmunitionDefinitionId);
            magazineCapacity = Find(ItemDefinitionSerializedFields.MagazineCapacity);
            reloadDurationSeconds =
                Find(ItemDefinitionSerializedFields.ReloadDurationSeconds);
            weaponDamage = Find(ItemDefinitionSerializedFields.WeaponDamage);
            weaponRange = Find(ItemDefinitionSerializedFields.WeaponRange);
            weaponNoiseRadius = Find(ItemDefinitionSerializedFields.WeaponNoiseRadius);
            medicineUseDurationSeconds =
                Find(ItemDefinitionSerializedFields.MedicineUseDurationSeconds);
            medicineHealthRestored =
                Find(ItemDefinitionSerializedFields.MedicineHealthRestored);
            kind = Find(ItemDefinitionSerializedFields.Kind);
            containerWidth = Find(ItemDefinitionSerializedFields.ContainerWidth);
            containerHeight = Find(ItemDefinitionSerializedFields.ContainerHeight);
        }

        public override void OnInspectorGUI()
        {
            serializedObject.UpdateIfRequiredOrScript();

            DrawHeading("Identity");
            using (new EditorGUI.DisabledScope(true))
            {
                EditorGUILayout.PropertyField(id, new GUIContent("Stable ID"));
            }
            EditorGUILayout.PropertyField(displayName, new GUIContent("Display Name"));
            EditorGUILayout.PropertyField(description, new GUIContent("Description"));

            DrawHeading("Classification");
            EditorGUILayout.PropertyField(kind, new GUIContent("Item Kind"));
            EquipmentSlotType previousSlot =
                (EquipmentSlotType)equipmentSlot.enumValueIndex;
            EditorGUI.BeginChangeCheck();
            EditorGUILayout.PropertyField(equipmentSlot, new GUIContent("Equipment Slot"));
            if (EditorGUI.EndChangeCheck() &&
                previousSlot == EquipmentSlotType.Backpack &&
                (EquipmentSlotType)equipmentSlot.enumValueIndex !=
                EquipmentSlotType.Backpack)
            {
                backpackBonusRows.intValue = 0;
            }

            ItemDefinitionKind currentKind =
                (ItemDefinitionKind)kind.enumValueIndex;
            EquipmentSlotType currentSlot =
                (EquipmentSlotType)equipmentSlot.enumValueIndex;
            bool isContainer = currentKind == ItemDefinitionKind.Container;
            bool isWeapon = currentSlot == EquipmentSlotType.Weapon;
            bool isBackpack = currentSlot == EquipmentSlotType.Backpack;
            bool forcesSingleStack = isContainer || currentSlot != EquipmentSlotType.None;

            if (isBackpack)
            {
                DrawHeading("Backpack Capacity");
                EditorGUILayout.PropertyField(
                    backpackBonusRows,
                    new GUIContent("Bonus Inventory Rows"));
                EditorGUILayout.HelpBox(
                    "Equipping this item appends the configured rows below the " +
                    "Player's base inventory. A container item cannot also grant rows.",
                    isContainer ? MessageType.Warning : MessageType.Info);
            }

            DrawHeading("Inventory Presentation");
            EditorGUILayout.PropertyField(width, new GUIContent("Grid Width"));
            EditorGUILayout.PropertyField(height, new GUIContent("Grid Height"));
            EditorGUILayout.PropertyField(icon, new GUIContent("Icon"));
            using (new EditorGUI.DisabledScope(forcesSingleStack))
            {
                EditorGUILayout.PropertyField(
                    maxStackSize,
                    new GUIContent("Maximum Stack Size"));
            }
            if (forcesSingleStack)
            {
                EditorGUILayout.HelpBox(
                    "Containers and equippable items always use a maximum stack size of 1.",
                    MessageType.Info);
            }

            DrawHeading("Trading");
            EditorGUILayout.PropertyField(isTradable, new GUIContent("Tradable"));
            if (isTradable.boolValue)
            {
                EditorGUILayout.PropertyField(
                    tradeCurrency,
                    new GUIContent("Trade Currency"));
                EditorGUILayout.PropertyField(tradePrice, new GUIContent("Trade Price"));
                if (isContainer)
                {
                    EditorGUILayout.HelpBox(
                        "Container items are excluded from trading by the current item contract.",
                        MessageType.Warning);
                }
            }

            if (isWeapon)
            {
                DrawHeading("Weapon");
                EditorGUILayout.PropertyField(
                    weaponFireMode,
                    new GUIContent("Fire Mode"));
                EditorGUILayout.PropertyField(
                    roundsPerMinute,
                    new GUIContent("Rounds Per Minute"));
                DrawAmmunitionPopup(ammunitionDefinitionId);
                EditorGUILayout.PropertyField(
                    magazineCapacity,
                    new GUIContent("Magazine Capacity"));
                EditorGUILayout.PropertyField(
                    reloadDurationSeconds,
                    new GUIContent("Reload Duration (Seconds)"));
                EditorGUILayout.PropertyField(
                    weaponDamage,
                    new GUIContent("Damage"));
                EditorGUILayout.PropertyField(
                    weaponRange,
                    new GUIContent("Range"));
                EditorGUILayout.PropertyField(
                    weaponNoiseRadius,
                    new GUIContent("Noise Radius"));
            }

            if (currentKind == ItemDefinitionKind.Medicine)
            {
                DrawHeading("Medicine");
                EditorGUILayout.PropertyField(
                    medicineUseDurationSeconds,
                    new GUIContent("Use Duration (Seconds)"));
                EditorGUILayout.PropertyField(
                    medicineHealthRestored,
                    new GUIContent("Health Restored"));
            }

            if (isContainer)
            {
                DrawHeading("Container");
                EditorGUILayout.PropertyField(
                    containerWidth,
                    new GUIContent("Internal Width"));
                EditorGUILayout.PropertyField(
                    containerHeight,
                    new GUIContent("Internal Height"));
            }

            bool changed = serializedObject.ApplyModifiedProperties();
            if (changed)
            {
                serializedObject.UpdateIfRequiredOrScript();
            }

            if (target is ItemDefinition definition &&
                !definition.TryValidateInventoryShape(out string error))
            {
                EditorGUILayout.Space(4f);
                EditorGUILayout.HelpBox(error, MessageType.Error);
            }
        }

        private void DrawAmmunitionPopup(SerializedProperty ammunitionId)
        {
            ItemDatabase database = ItemContentAuthoringService.LoadDefaultDatabase();
            if (database == null || database.Items == null)
            {
                EditorGUILayout.PropertyField(
                    ammunitionId,
                    new GUIContent("Ammunition ID"));
                EditorGUILayout.HelpBox(
                    "The default ItemDatabase is unavailable, so ammunition IDs cannot be resolved.",
                    MessageType.Warning);
                return;
            }

            var ids = new List<int>();
            var labels = new List<string>();
            int selectedIndex = -1;
            for (int index = 0; index < database.Items.Count; index++)
            {
                ItemDefinition definition = database.Items[index];
                if (definition == null || !definition.IsAmmunition)
                {
                    continue;
                }

                ids.Add(definition.Id);
                labels.Add($"[{definition.Id}] {GetDisplayName(definition)}");
                if (definition.Id == ammunitionId.intValue)
                {
                    selectedIndex = ids.Count - 1;
                }
            }

            if (selectedIndex < 0)
            {
                ids.Insert(0, ammunitionId.intValue);
                labels.Insert(0, $"[Missing ID {ammunitionId.intValue}]");
                selectedIndex = 0;
            }

            EditorGUI.BeginChangeCheck();
            int nextIndex = EditorGUILayout.Popup(
                new GUIContent("Ammunition"),
                selectedIndex,
                labels.ToArray());
            if (EditorGUI.EndChangeCheck() && nextIndex >= 0 && nextIndex < ids.Count)
            {
                ammunitionId.intValue = ids[nextIndex];
            }
        }

        private SerializedProperty Find(string propertyName)
        {
            SerializedProperty property = serializedObject.FindProperty(propertyName);
            if (property == null)
            {
                Debug.LogError(
                    $"ItemDefinition serialized field '{propertyName}' is missing.",
                    target);
            }

            return property;
        }

        private static void DrawHeading(string text)
        {
            EditorGUILayout.Space(6f);
            EditorGUILayout.LabelField(text, EditorStyles.boldLabel);
        }

        private static string GetDisplayName(ItemDefinition definition)
        {
            return string.IsNullOrWhiteSpace(definition.DisplayName)
                ? definition.name
                : definition.DisplayName;
        }
    }
}
