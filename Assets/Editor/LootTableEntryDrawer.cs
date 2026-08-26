using System.Collections.Generic;
using FantasySurvival.Inventory;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    [CustomPropertyDrawer(typeof(LootTableEntry))]
    public sealed class LootTableEntryDrawer : PropertyDrawer
    {
        private const string ItemDatabasePath =
            "Assets/GameData/Items/ItemDatabase.asset";
        private const string ItemDefinitionIdPropertyName = "itemDefinitionId";
        private const string DropChancePercentPropertyName = "dropChancePercent";

        private static readonly GUIContent ChanceLabel = new GUIContent("확률 (%)");

        private static ItemDatabase itemDatabase;

        private readonly struct ItemOption
        {
            public ItemOption(int id, GUIContent label)
            {
                Id = id;
                Label = label;
            }

            public int Id { get; }
            public GUIContent Label { get; }
        }

        public override void OnGUI(
            Rect position,
            SerializedProperty property,
            GUIContent label)
        {
            EditorGUI.BeginProperty(position, label, property);

            SerializedProperty itemDefinitionId =
                property.FindPropertyRelative(ItemDefinitionIdPropertyName);
            SerializedProperty dropChancePercent =
                property.FindPropertyRelative(DropChancePercentPropertyName);
            if (itemDefinitionId == null || dropChancePercent == null)
            {
                EditorGUI.HelpBox(
                    position,
                    "LootTableEntry serialized fields are missing.",
                    MessageType.Error);
                EditorGUI.EndProperty();
                return;
            }

            float lineHeight = EditorGUIUtility.singleLineHeight;
            float spacing = EditorGUIUtility.standardVerticalSpacing;
            var itemLine = new Rect(position.x, position.y, position.width, lineHeight);
            var chanceLine = new Rect(
                position.x,
                position.y + lineHeight + spacing,
                position.width,
                lineHeight);

            Rect itemPopup = EditorGUI.PrefixLabel(itemLine, label);
            DrawItemPopup(itemPopup, itemDefinitionId);

            int previousIndent = EditorGUI.indentLevel;
            EditorGUI.indentLevel = previousIndent + 1;
            EditorGUI.PropertyField(chanceLine, dropChancePercent, ChanceLabel);
            EditorGUI.indentLevel = previousIndent;

            EditorGUI.EndProperty();
        }

        public override float GetPropertyHeight(
            SerializedProperty property,
            GUIContent label)
        {
            return EditorGUIUtility.singleLineHeight * 2f +
                   EditorGUIUtility.standardVerticalSpacing;
        }

        private static void DrawItemPopup(
            Rect position,
            SerializedProperty itemDefinitionId)
        {
            List<ItemOption> options = BuildItemOptions(
                itemDefinitionId.intValue,
                out int selectedIndex);
            var labels = new GUIContent[options.Count];
            for (int index = 0; index < options.Count; index++)
            {
                labels[index] = options[index].Label;
            }

            bool previousMixedValue = EditorGUI.showMixedValue;
            EditorGUI.showMixedValue = itemDefinitionId.hasMultipleDifferentValues;
            EditorGUI.BeginChangeCheck();
            int nextIndex = EditorGUI.Popup(position, selectedIndex, labels);
            if (EditorGUI.EndChangeCheck() && nextIndex >= 0 && nextIndex < options.Count)
            {
                itemDefinitionId.intValue = options[nextIndex].Id;
            }
            EditorGUI.showMixedValue = previousMixedValue;
        }

        private static List<ItemOption> BuildItemOptions(
            int currentId,
            out int selectedIndex)
        {
            ItemDatabase database = LoadItemDatabase();
            var definitions = new List<ItemDefinition>();
            var seenIds = new HashSet<int>();
            bool currentIdExists = false;

            if (database?.Items != null)
            {
                for (int index = 0; index < database.Items.Count; index++)
                {
                    ItemDefinition definition = database.Items[index];
                    if (definition == null || definition.Id <= 0 ||
                        !seenIds.Add(definition.Id))
                    {
                        continue;
                    }

                    definitions.Add(definition);
                    currentIdExists |= definition.Id == currentId;
                }
            }

            definitions.Sort((left, right) => left.Id.CompareTo(right.Id));

            var options = new List<ItemOption>(
                definitions.Count + (currentIdExists ? 0 : 1));
            if (!currentIdExists)
            {
                options.Add(new ItemOption(
                    currentId,
                    new GUIContent($"[Missing ID {currentId}]")));
            }

            selectedIndex = currentIdExists ? -1 : 0;
            for (int index = 0; index < definitions.Count; index++)
            {
                ItemDefinition definition = definitions[index];
                string displayName = string.IsNullOrWhiteSpace(definition.DisplayName)
                    ? definition.name
                    : definition.DisplayName;
                options.Add(new ItemOption(
                    definition.Id,
                    new GUIContent($"[{definition.Id}] {displayName}")));

                if (definition.Id == currentId)
                {
                    selectedIndex = options.Count - 1;
                }
            }

            if (selectedIndex < 0)
            {
                // This should be unreachable, but preserving the serialized value is safer
                // than silently replacing it if the database changes during an Inspector draw.
                options.Insert(0, new ItemOption(
                    currentId,
                    new GUIContent($"[Missing ID {currentId}]")));
                selectedIndex = 0;
            }

            return options;
        }

        private static ItemDatabase LoadItemDatabase()
        {
            if (itemDatabase == null ||
                AssetDatabase.GetAssetPath(itemDatabase) != ItemDatabasePath)
            {
                itemDatabase = AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
            }

            return itemDatabase;
        }
    }
}
