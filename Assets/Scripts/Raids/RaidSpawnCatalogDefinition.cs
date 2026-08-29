using System;
using System.Collections.Generic;
using FantasySurvival.Interaction;
using FantasySurvival.Inventory;
using FantasySurvival.WorldGeneration;
using UnityEngine;

namespace FantasySurvival.Raids
{
    public enum RaidSpawnContentKind
    {
        Chest,
        Enemy
    }

    [Serializable]
    public sealed class RaidSpawnCatalogEntry
    {
        [Tooltip("Stable runtime instance ID used by the spawn manifest and Recovery records.")]
        [SerializeField] private string stableId;
        [Tooltip("Optional runtime hierarchy name. The prefab name is used when left empty.")]
        [SerializeField] private string runtimeName;
        [SerializeField] private RaidSpawnContentKind kind;
        [SerializeField] private GameObject prefab;
        [Tooltip("World-space Y used when the 2D spawn manifest is materialized.")]
        [SerializeField] private float groundYOffset;
        [Tooltip("Only Chest entries may request a semantic POI placement.")]
        [SerializeField] private UrbanPoiKind requiredPoiKind;

        public string StableId => stableId;
        public string RuntimeName => string.IsNullOrWhiteSpace(runtimeName)
            ? prefab != null ? prefab.name : string.Empty
            : runtimeName;
        public RaidSpawnContentKind Kind => kind;
        public GameObject Prefab => prefab;
        public float GroundYOffset => groundYOffset;
        public UrbanPoiKind RequiredPoiKind => requiredPoiKind;

        public bool TryValidate(out string error)
        {
            if (!IsValidStableId(stableId))
            {
                error =
                    $"Raid spawn stable ID '{stableId}' must use a lowercase namespace:path key.";
                return false;
            }

            if (prefab == null)
            {
                error = $"Raid spawn '{stableId}' has no prefab.";
                return false;
            }

            if (float.IsNaN(groundYOffset) || float.IsInfinity(groundYOffset))
            {
                error = $"Raid spawn '{stableId}' has an invalid ground Y offset.";
                return false;
            }

            if (kind == RaidSpawnContentKind.Chest)
            {
                Chest chest = prefab.GetComponent<Chest>();
                if (chest == null || prefab.GetComponent<EnemyStats>() != null ||
                    prefab.GetComponent<ChestInteractable>() == null)
                {
                    error =
                        $"Raid Chest spawn '{stableId}' requires root Chest and " +
                        "ChestInteractable components.";
                    return false;
                }

                if (!InventoryGridConstraints.TryValidateDimensions(
                        chest.chestWidth,
                        chest.chestHeight,
                        out string gridError))
                {
                    error =
                        $"Raid Chest spawn '{stableId}' has an invalid grid: {gridError}";
                    return false;
                }

                if (requiredPoiKind != UrbanPoiKind.None &&
                    requiredPoiKind != UrbanPoiKind.Medical)
                {
                    error = $"Raid Chest spawn '{stableId}' has an unsupported POI kind.";
                    return false;
                }
            }
            else if (kind == RaidSpawnContentKind.Enemy)
            {
                EnemyStats stats = prefab.GetComponent<EnemyStats>();
                EnemyAIController ai = prefab.GetComponent<EnemyAIController>();
                Chest[] corpseInventories = prefab.GetComponentsInChildren<Chest>(true);
                if (requiredPoiKind != UrbanPoiKind.None || stats == null || ai == null ||
                    stats.Definition == null || stats.Definition.AI == null ||
                    corpseInventories.Length != 1 ||
                    corpseInventories[0].GetComponentInParent<EnemyStats>(true) != stats)
                {
                    error =
                        $"Raid Enemy spawn '{stableId}' requires root EnemyStats/EnemyAIController, " +
                        "one owned corpse Chest, a valid EnemyDefinition, and no POI requirement.";
                    return false;
                }
            }
            else
            {
                error = $"Raid spawn '{stableId}' has an unsupported content kind.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool IsValidStableId(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                return false;
            }

            int separator = value.IndexOf(':');
            if (separator <= 0 || separator != value.LastIndexOf(':') ||
                separator >= value.Length - 1)
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
                bool isSeparator = character == '_' || character == '-' ||
                                   character == '.' ||
                                   (character == '/' && index > separator);
                if (!isLowerLetter && !isDigit && !isSeparator)
                {
                    return false;
                }
            }

            return true;
        }
    }

    [CreateAssetMenu(
        fileName = "RaidSpawnCatalog",
        menuName = "Fantasy Survival/Raids/Raid Spawn Catalog")]
    public sealed class RaidSpawnCatalogDefinition : ScriptableObject
    {
        [SerializeField] private List<RaidSpawnCatalogEntry> entries =
            new List<RaidSpawnCatalogEntry>();

        public IReadOnlyList<RaidSpawnCatalogEntry> Entries => entries;

        public bool TryValidate(out string error)
        {
            if (entries == null || entries.Count == 0)
            {
                error = $"Raid spawn catalog '{name}' has no entries.";
                return false;
            }

            var stableIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < entries.Count; index++)
            {
                RaidSpawnCatalogEntry entry = entries[index];
                if (entry == null)
                {
                    error =
                        $"Raid spawn catalog '{name}' entry {index} is missing.";
                    return false;
                }

                if (!entry.TryValidate(out string entryError))
                {
                    error =
                        $"Raid spawn catalog '{name}' entry {index} is invalid: {entryError}";
                    return false;
                }

                if (!stableIds.Add(entry.StableId))
                {
                    error =
                        $"Raid spawn catalog '{name}' duplicates stable ID '{entry.StableId}'.";
                    return false;
                }
            }

            error = null;
            return true;
        }
    }
}
