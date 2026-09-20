using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Authoring only. The planner owns all probability and placement decisions.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(EnterableSpriteBuilding))]
    public sealed class UrbanBuildingPrefab : MonoBehaviour
    {
        [Serializable]
        public sealed class Choice
        {
            public int propIndex;
            [Min(0.001f)] public float weight = 1f;
        }

        [Serializable]
        public sealed class Rule
        {
            public string stableId;
            public UrbanPoiKind requiredPoiKind;
            public UrbanDecorationZone zone;
            [Range(0, 1)] public float chance = .65f;
            [Min(0)] public int maxCount = 2;
            public Choice[] choices = Array.Empty<Choice>();
        }

        [Min(0)] public float reservedMargin = 1.25f;
        [HideInInspector] public int catalogRevision;
        [Min(1.4f)] public float aisleWidth = 1.4f;
        public UrbanBuildingProp[] propPrefabs = Array.Empty<UrbanBuildingProp>();
        public Rule[] rules = Array.Empty<Rule>();

        public UrbanBuildingLayoutProfile Snapshot(IsometricUrbanStyle style)
        {
            if (style == null) throw new ArgumentNullException(nameof(style));
            if (rules == null || propPrefabs == null)
                throw new InvalidOperationException("Building prefab rules and prop catalog must be assigned.");
            var copied = new List<UrbanBuildingDecorationRule>();
            foreach (Rule rule in rules)
            {
                if (rule == null || rule.choices == null)
                    throw new InvalidOperationException("Building prefab contains an empty rule.");
                var choices = new List<UrbanBuildingPropChoice>();
                foreach (Choice choice in rule.choices)
                {
                    if (choice == null || choice.propIndex < 0 || choice.propIndex >= propPrefabs.Length ||
                        propPrefabs[choice.propIndex] == null)
                        throw new InvalidOperationException("Building rule has a missing prop prefab.");
                    UrbanBuildingProp prefab = propPrefabs[choice.propIndex];
                    if (!prefab.TryValidate(out string error)) throw new InvalidOperationException(error);
                    choices.Add(new UrbanBuildingPropChoice(choice.propIndex, prefab.catalogId, prefab.allowedZones,
                        choice.weight, prefab.PlacementSize, prefab.maxPerBuilding));
                }
                copied.Add(new UrbanBuildingDecorationRule(rule.stableId, rule.requiredPoiKind, rule.zone,
                    rule.chance, rule.maxCount, choices));
            }
            var profile = new UrbanBuildingLayoutProfile(reservedMargin, style.wallThickness,
                style.doorWidth, aisleWidth, copied);
            if (!profile.TryValidate(out string profileError)) throw new InvalidOperationException(profileError);
            return profile;
        }

        public void Populate(UrbanMapLayout layout, int buildingIndex)
        {
            UrbanBuildingPlacement building = layout.Buildings[buildingIndex];
            foreach (UrbanBuildingDecorationPlacement placement in layout.BuildingDecorations)
            {
                if (placement.SourceBuildingIndex != buildingIndex) continue;
                UrbanBuildingProp prop = Instantiate(propPrefabs[placement.PropIndex], transform, false);
                prop.name = placement.StableId;
                Vector2 local = building.ToLocal(placement.LocalPosition);
                prop.transform.localPosition = new Vector3(local.x,
                    placement.Interior ? EnterableSpriteBuilding.FloorLift : 0f,
                    local.y);
                prop.transform.localRotation = Quaternion.Euler(0, placement.LocalYawDegrees - building.LocalYawDegrees, 0);
                prop.ApplyPlacement(placement);
            }
        }
    }
}
