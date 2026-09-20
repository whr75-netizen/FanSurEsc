using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    [Flags]
    public enum UrbanDecorationZone
    {
        None = 0,
        InteriorEntrance = 1,
        InteriorStorage = 2,
        InteriorWorkArea = 4,
        ExteriorService = 8,
        PublicSidewalk = 16
    }

    public readonly struct UrbanBuildingPropChoice
    {
        public UrbanBuildingPropChoice(int propIndex, string catalogId, UrbanDecorationZone allowedZones,
            float weight, Vector3 physicalSize, int maxPerBuilding = 1)
        {
            PropIndex = propIndex; CatalogId = catalogId; AllowedZones = allowedZones;
            Weight = weight; PhysicalSize = physicalSize; MaxPerBuilding = maxPerBuilding;
        }
        public int PropIndex { get; }
        public string CatalogId { get; }
        public UrbanDecorationZone AllowedZones { get; }
        public float Weight { get; }
        public Vector3 PhysicalSize { get; }
        public int MaxPerBuilding { get; }
    }

    public sealed class UrbanBuildingDecorationRule
    {
        public UrbanBuildingDecorationRule(string stableId, UrbanPoiKind requiredPoiKind, UrbanDecorationZone zone, float chance, int maxCount,
            IReadOnlyList<UrbanBuildingPropChoice> choices)
        {
            StableId = stableId; RequiredPoiKind = requiredPoiKind; Zone = zone; Chance = chance; MaxCount = maxCount;
            var copy = new List<UrbanBuildingPropChoice>();
            if (choices != null) for (int i = 0; i < choices.Count; i++) copy.Add(choices[i]);
            Choices = copy.AsReadOnly();
        }
        public string StableId { get; }
        public UrbanPoiKind RequiredPoiKind { get; }
        public UrbanDecorationZone Zone { get; }
        public bool Interior => UrbanBuildingDecorationPlanner.IsInterior(Zone);
        public float Chance { get; }
        public int MaxCount { get; }
        public IReadOnlyList<UrbanBuildingPropChoice> Choices { get; }
    }

    /// <summary>One immutable snapshot of a building prefab's spatial authoring rules.</summary>
    public sealed class UrbanBuildingLayoutProfile
    {
        public UrbanBuildingLayoutProfile(float reservedMargin, float wallThickness, float doorWidth,
            float aisleWidth, IReadOnlyList<UrbanBuildingDecorationRule> rules)
        {
            ReservedMargin = reservedMargin; WallThickness = wallThickness;
            DoorWidth = doorWidth; AisleWidth = aisleWidth;
            var copy = new List<UrbanBuildingDecorationRule>();
            if (rules != null) for (int i = 0; i < rules.Count; i++) copy.Add(rules[i]);
            Rules = copy.AsReadOnly();
        }
        public float ReservedMargin { get; }
        public float WallThickness { get; }
        public float ExteriorWallOffset => WallThickness*.5f + EnterableSpriteBuilding.WindowFrameDepth;
        public float DoorWidth { get; }
        public float AisleWidth { get; }
        public IReadOnlyList<UrbanBuildingDecorationRule> Rules { get; }

        public bool TryValidate(out string error)
        {
            if (!Finite(ReservedMargin) || ReservedMargin < 0 || !Finite(WallThickness) || WallThickness <= 0 ||
                !Finite(DoorWidth) || DoorWidth <= 0 || !Finite(AisleWidth) || AisleWidth < 1.4f)
            { error = "Building profile requires finite dimensions and an aisle at least 1.4 metres wide."; return false; }
            var ids = new HashSet<string>(StringComparer.Ordinal);
            var catalog = new Dictionary<string, UrbanBuildingPropChoice>(StringComparer.Ordinal);
            var indices = new Dictionary<int, string>();
            foreach (UrbanBuildingDecorationRule rule in Rules)
            {
                if (rule == null || string.IsNullOrWhiteSpace(rule.StableId) || !ids.Add(rule.StableId) ||
                    !Finite(rule.Chance) || rule.Chance < 0 || rule.Chance > 1 || rule.MaxCount < 0 || rule.Choices.Count == 0)
                { error = "Building decoration rules require unique IDs, valid probability/count, and prop choices."; return false; }
                if ((rule.RequiredPoiKind == UrbanPoiKind.None || !Enum.IsDefined(typeof(UrbanPoiKind), rule.RequiredPoiKind)) || !UrbanBuildingDecorationPlanner.IsSupportedZone(rule.Zone))
                {
                    error = $"Building rule '{rule.StableId}' requires an existing concrete POI and one supported building zone; None and PublicSidewalk are not building fallbacks.";
                    return false;
                }
                var ruleCatalogIds = new HashSet<string>(StringComparer.Ordinal);
                double total = 0;
                foreach (UrbanBuildingPropChoice choice in rule.Choices)
                {
                    Vector3 size = choice.PhysicalSize;
                    const UrbanDecorationZone allZones = UrbanDecorationZone.InteriorEntrance | UrbanDecorationZone.InteriorStorage |
                        UrbanDecorationZone.InteriorWorkArea | UrbanDecorationZone.ExteriorService | UrbanDecorationZone.PublicSidewalk;
                    if (choice.PropIndex < 0 || string.IsNullOrWhiteSpace(choice.CatalogId) || !ruleCatalogIds.Add(choice.CatalogId) ||
                        choice.AllowedZones == UrbanDecorationZone.None || (choice.AllowedZones & ~allZones) != 0 || choice.MaxPerBuilding < 0 ||
                        !Finite(choice.Weight) || choice.Weight < 0 ||
                        !Finite(size.x) || !Finite(size.y) || !Finite(size.z) || size.x <= 0 || size.y <= 0 || size.z <= 0)
                    { error = $"Building rule '{rule.StableId}' has an invalid prop choice."; return false; }
                    if (catalog.TryGetValue(choice.CatalogId, out UrbanBuildingPropChoice known) &&
                        (known.PropIndex != choice.PropIndex || known.AllowedZones != choice.AllowedZones ||
                         known.PhysicalSize != choice.PhysicalSize || known.MaxPerBuilding != choice.MaxPerBuilding) ||
                        indices.TryGetValue(choice.PropIndex, out string knownId) && !string.Equals(knownId, choice.CatalogId, StringComparison.Ordinal))
                    { error = $"Prop catalog identity '{choice.CatalogId}' has inconsistent metadata across rules."; return false; }
                    catalog[choice.CatalogId] = choice; indices[choice.PropIndex] = choice.CatalogId;
                    total += choice.Weight;
                }
                if (total <= 0 || double.IsInfinity(total))
                { error = $"Building rule '{rule.StableId}' has no positive finite choice weight."; return false; }
            }
            error = null; return true;
        }

        public ulong StableHash
        {
            get
            {
                var h = new UrbanDecorationHash();
                h.Add(ReservedMargin); h.Add(WallThickness); h.Add(ExteriorWallOffset); h.Add(DoorWidth); h.Add(AisleWidth); h.Add(Rules.Count);
                foreach (UrbanBuildingDecorationRule rule in Rules)
                {
                    h.Add(rule.StableId); h.Add((int)rule.RequiredPoiKind); h.Add((int)rule.Zone); h.Add(rule.Chance); h.Add(rule.MaxCount); h.Add(rule.Choices.Count);
                    foreach (UrbanBuildingPropChoice choice in rule.Choices)
                    {
                        h.Add(choice.PropIndex); h.Add(choice.CatalogId); h.Add((int)choice.AllowedZones); h.Add(choice.MaxPerBuilding);
                        h.Add(choice.Weight); h.Add(choice.PhysicalSize.x); h.Add(choice.PhysicalSize.y); h.Add(choice.PhysicalSize.z);
                    }
                }
                return h.Value;
            }
        }
        private static bool Finite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
    }

    public readonly struct UrbanBuildingDoorGeometry
    {
        private UrbanBuildingDoorGeometry(bool onZ, float coordinate, float centerAlong, float width, float sign)
        {
            OnZ = onZ; Coordinate = coordinate; CenterAlong = centerAlong; Width = width;
            LocalCenter = onZ ? new Vector2(centerAlong, coordinate) : new Vector2(coordinate, centerAlong);
            Outward = onZ ? Vector2.up * sign : Vector2.right * sign;
        }
        public bool OnZ { get; }
        public float Coordinate { get; }
        public float CenterAlong { get; }
        public float Width { get; }
        public Vector2 LocalCenter { get; }
        public Vector2 Outward { get; }
        public static UrbanBuildingDoorGeometry Calculate(Vector2 size, Vector2 facade, float wallThickness,
            float doorWidth, bool reserveFacadeCenter)
        {
            bool onZ = Mathf.Abs(facade.y) >= Mathf.Abs(facade.x);
            float sign = Mathf.Sign(onZ ? facade.y : facade.x);
            if (sign == 0) sign = 1;
            float length = onZ ? size.x : size.y;
            float width = Mathf.Min(doorWidth, length - wallThickness * 4);
            float center = reserveFacadeCenter ? Mathf.Min(length * .25f, (length - width) * .5f - wallThickness) : 0;
            return new UrbanBuildingDoorGeometry(onZ, sign * (onZ ? size.y : size.x) * .5f, center, width, sign);
        }
    }

    public readonly struct UrbanBuildingDecorationPlacement
    {
        public UrbanBuildingDecorationPlacement(int sourceBuildingIndex, string stableId, int propIndex, string catalogId,
            UrbanPoiKind requiredPoiKind, UrbanDecorationZone zone,
            Vector2 localPosition, float localYawDegrees, Vector3 physicalSize, string ruleId = null, int slotIndex = -1)
        {
            SourceBuildingIndex = sourceBuildingIndex; StableId = stableId; PropIndex = propIndex; CatalogId = catalogId;
            RequiredPoiKind = requiredPoiKind; Zone = zone;
            LocalPosition = localPosition; LocalYawDegrees = localYawDegrees; PhysicalSize = physicalSize;
            RuleId = ruleId; SlotIndex = slotIndex;
        }
        public int SourceBuildingIndex { get; }
        public string StableId { get; }
        public int PropIndex { get; }
        public string CatalogId { get; }
        public UrbanPoiKind RequiredPoiKind { get; }
        public UrbanDecorationZone Zone { get; }
        public bool Interior => UrbanBuildingDecorationPlanner.IsInterior(Zone);
        public Vector2 LocalPosition { get; }
        public float LocalYawDegrees { get; }
        public Vector3 PhysicalSize { get; }
        public string RuleId { get; }
        public int SlotIndex { get; }
        public UrbanOrientedRect Bounds
        {
            get
            {
                float angle = LocalYawDegrees * Mathf.Deg2Rad;
                return new UrbanOrientedRect(LocalPosition, new Vector2(PhysicalSize.x, PhysicalSize.z),
                    new Vector2(Mathf.Sin(angle), Mathf.Cos(angle)));
            }
        }
        public Rect Footprint => Bounds.Aabb;
    }

    /// <summary>POI/zone/catalog filtering precedes weighted selection; each building/rule has one probability gate.</summary>
    public static class UrbanBuildingDecorationPlanner
    {
        private const float Tolerance = .001f;

        private sealed class EligibleChoice
        {
            public UrbanBuildingPropChoice Choice;
            public List<UrbanBuildingDecorationPlacement> Slots;
        }

        public static bool IsInterior(UrbanDecorationZone zone) => zone == UrbanDecorationZone.InteriorEntrance ||
            zone == UrbanDecorationZone.InteriorStorage || zone == UrbanDecorationZone.InteriorWorkArea;

        public static bool IsSupportedZone(UrbanDecorationZone zone) => IsInterior(zone) || zone == UrbanDecorationZone.ExteriorService;

        public static List<UrbanBuildingDecorationPlacement> Generate(int seed, IReadOnlyList<UrbanParcelPlacement> parcels,
            IReadOnlyList<UrbanBuildingPlacement> buildings, IReadOnlyList<UrbanPoiPlacement> pois, UrbanBuildingLayoutProfile profile)
        {
            var result = new List<UrbanBuildingDecorationPlacement>();
            if (profile == null) return result;
            if (!profile.TryValidate(out string profileError)) throw new ArgumentException(profileError, nameof(profile));
            for (int buildingIndex = 0; buildingIndex < buildings.Count; buildingIndex++)
            {
                UrbanBuildingPlacement building = buildings[buildingIndex];
                UrbanParcelPlacement parcel = parcels[building.SourceParcelIndex];
                foreach (UrbanBuildingDecorationRule rule in profile.Rules)
                {
                    if (!MatchesPoi(buildingIndex, rule.RequiredPoiKind, pois)) continue;
                    // This draw occurs once, not once per alternative location.
                    var rng = new UrbanDecorationRandom(seed, parcel.StableId, rule.StableId, -1);
                    if (rng.Next() >= rule.Chance) continue;
                    for (int count = 0; count < rule.MaxCount; count++)
                    {
                        var eligible = new List<EligibleChoice>();
                        double total = 0;
                        foreach (UrbanBuildingPropChoice choice in rule.Choices)
                        {
                            if (choice.Weight <= 0 || (choice.AllowedZones & rule.Zone) == 0 ||
                                CountCatalog(result, buildingIndex, choice.CatalogId) >= choice.MaxPerBuilding) continue;
                            var slots = new List<UrbanBuildingDecorationPlacement>();
                            int wallCount = GetZoneWalls(rule.Zone, Vector2.up).Length;
                            for (int slot = 0; slot < wallCount * 3; slot++)
                            {
                                if (!TryCreateSlot(buildingIndex, building, parcel, rule, choice, profile, slot, out UrbanBuildingDecorationPlacement p) ||
                                    !IsAllowed(p, parcel, building, pois, profile)) continue;
                                bool overlaps = false;
                                foreach (UrbanBuildingDecorationPlacement previous in result)
                                    if (p.Bounds.Overlaps(previous.Bounds)) { overlaps = true; break; }
                                if (!overlaps) slots.Add(p);
                            }
                            if (slots.Count == 0) continue;
                            eligible.Add(new EligibleChoice { Choice = choice, Slots = slots });
                            total += choice.Weight;
                        }
                        if (eligible.Count == 0) break;
                        // Each object's weight counts once, independently of how many positions fit it.
                        double selection = rng.Next() * total;
                        EligibleChoice chosen = eligible[eligible.Count - 1];
                        foreach (EligibleChoice option in eligible)
                        { selection -= option.Choice.Weight; if (selection < 0) { chosen = option; break; } }
                        int slotIndex = Mathf.Min(chosen.Slots.Count - 1, Mathf.FloorToInt(rng.Next() * chosen.Slots.Count));
                        result.Add(chosen.Slots[slotIndex]);
                    }
                }
            }
            return result;
        }

        private static Vector2[] GetZoneWalls(UrbanDecorationZone zone, Vector2 front)
        {
            if (zone == UrbanDecorationZone.InteriorEntrance) return new[] { front };
            if (zone == UrbanDecorationZone.InteriorStorage || zone == UrbanDecorationZone.ExteriorService) return new[] { -front };
            if (zone == UrbanDecorationZone.InteriorWorkArea)
            {
                Vector2 right = new Vector2(front.y, -front.x);
                return new[] { -front, right, -right };
            }
            throw new InvalidOperationException($"Zone '{zone}' is not implemented by the building decoration planner.");
        }

        private static bool TryCreateSlot(int buildingIndex, UrbanBuildingPlacement building, UrbanParcelPlacement parcel,
            UrbanBuildingDecorationRule rule, UrbanBuildingPropChoice choice, UrbanBuildingLayoutProfile profile,
            int slot, out UrbanBuildingDecorationPlacement placement)
        {
            placement = default;
            Vector2[] walls = GetZoneWalls(rule.Zone, Vector2.up);
            if (slot < 0 || slot >= walls.Length * 3) return false;
            Vector2 outward = walls[slot / 3];
            Vector2 tangent = new Vector2(outward.y, -outward.x);
            float normalExtent = Mathf.Abs(outward.x) * building.Size.x * .5f + Mathf.Abs(outward.y) * building.Size.y * .5f;
            float alongExtent = Mathf.Abs(tangent.x) * building.Size.x * .5f + Mathf.Abs(tangent.y) * building.Size.y * .5f;
            float alongLimit = alongExtent - profile.WallThickness - choice.PhysicalSize.x * .5f;
            float normal = rule.Interior
                ? normalExtent - profile.WallThickness - choice.PhysicalSize.z * .5f
                : normalExtent + profile.ExteriorWallOffset + choice.PhysicalSize.z * .5f;
            if (alongLimit < 0 || normal <= 0 || choice.PhysicalSize.y >= building.Height) return false;
            int alongIndex = slot % 3;
            float along = alongIndex == 0 ? -alongLimit : alongIndex == 1 ? alongLimit : 0;
            Vector2 facing = rule.Interior ? -outward : outward;
            placement = new UrbanBuildingDecorationPlacement(buildingIndex,
                $"parcel:{parcel.StableId}/rule:{rule.StableId}/slot:{slot}", choice.PropIndex, choice.CatalogId,
                rule.RequiredPoiKind, rule.Zone, building.ToMap(outward * normal + tangent * along),
                building.LocalYawDegrees + Mathf.Atan2(facing.x, facing.y) * Mathf.Rad2Deg, choice.PhysicalSize, rule.StableId, slot);
            return true;
        }

        private static bool MatchesPoi(int buildingIndex, UrbanPoiKind requiredKind, IReadOnlyList<UrbanPoiPlacement> pois)
        {
            if (requiredKind == UrbanPoiKind.None) return false;
            foreach (UrbanPoiPlacement poi in pois)
                if (poi.BuildingIndex == buildingIndex && poi.Kind == requiredKind) return true;
            return false;
        }

        private static int CountCatalog(IReadOnlyList<UrbanBuildingDecorationPlacement> placements, int buildingIndex, string catalogId)
        {
            int count = 0;
            foreach (UrbanBuildingDecorationPlacement p in placements)
                if (p.SourceBuildingIndex == buildingIndex && string.Equals(p.CatalogId, catalogId, StringComparison.Ordinal)) count++;
            return count;
        }

        public static bool TryValidate(UrbanMapLayout layout, out string error)
        {
            UrbanBuildingLayoutProfile profile = layout.BuildingProfile;
            if (profile == null)
            { error = layout.BuildingDecorations.Count == 0 ? null : "Decorations have no authoritative building profile."; return error == null; }
            if (!profile.TryValidate(out error)) return false;
            var ids = new HashSet<string>(StringComparer.Ordinal);
            var ruleCounts = new Dictionary<string, int>(StringComparer.Ordinal);
            for (int i = 0; i < layout.BuildingDecorations.Count; i++)
            {
                UrbanBuildingDecorationPlacement p = layout.BuildingDecorations[i];
                if (p.SourceBuildingIndex < 0 || p.SourceBuildingIndex >= layout.Buildings.Count ||
                    string.IsNullOrEmpty(p.StableId) || !ids.Add(p.StableId) || string.IsNullOrWhiteSpace(p.CatalogId) ||
                    p.PropIndex < 0 || p.SlotIndex < 0 || p.SlotIndex >= 9 || !IsSupportedZone(p.Zone) ||
                    !Finite(p.LocalPosition.x) || !Finite(p.LocalPosition.y) || !Finite(p.LocalYawDegrees) ||
                    !Finite(p.PhysicalSize.x) || !Finite(p.PhysicalSize.y) || !Finite(p.PhysicalSize.z) ||
                    p.PhysicalSize.x <= 0 || p.PhysicalSize.y <= 0 || p.PhysicalSize.z <= 0)
                { error = $"Invalid building decoration identity or dimensions at index {i}."; return false; }
                UrbanBuildingPlacement building = layout.Buildings[p.SourceBuildingIndex];
                UrbanBuildingDecorationRule owner = null;
                foreach (UrbanBuildingDecorationRule rule in profile.Rules)
                    if (string.Equals(rule.StableId, p.RuleId, StringComparison.Ordinal)) { owner = rule; break; }
                bool matchesChoice = false;
                UrbanBuildingPropChoice selectedChoice = default;
                if (owner != null && owner.Zone == p.Zone && owner.RequiredPoiKind == p.RequiredPoiKind && owner.Chance > 0 &&
                    MatchesPoi(p.SourceBuildingIndex, owner.RequiredPoiKind, layout.Pois))
                    foreach (UrbanBuildingPropChoice choice in owner.Choices)
                        if (choice.PropIndex == p.PropIndex && string.Equals(choice.CatalogId, p.CatalogId, StringComparison.Ordinal) &&
                            (choice.AllowedZones & p.Zone) != 0 && choice.Weight > 0 &&
                            (choice.PhysicalSize - p.PhysicalSize).sqrMagnitude < Tolerance * Tolerance)
                        { matchesChoice = true; selectedChoice = choice; break; }
                int parcelId = layout.Parcels[building.SourceParcelIndex].StableId;
                string canonicalId = $"parcel:{parcelId}/rule:{p.RuleId}/slot:{p.SlotIndex}";
                if (!matchesChoice || !string.Equals(p.StableId, canonicalId, StringComparison.Ordinal) ||
                    Mathf.Abs((p.LocalYawDegrees - building.LocalYawDegrees) / 90f -
                        Mathf.Round((p.LocalYawDegrees - building.LocalYawDegrees) / 90f)) > Tolerance)
                { error = $"Building decoration '{p.StableId}' does not match its prefab rule and choice."; return false; }
                var gate = new UrbanDecorationRandom(layout.Seed, parcelId, owner.StableId, -1);
                if (gate.Next() >= owner.Chance || CountCatalog(layout.BuildingDecorations, p.SourceBuildingIndex, p.CatalogId) > selectedChoice.MaxPerBuilding)
                { error = $"Building decoration '{p.StableId}' violates the once-per-building rule gate or catalog cap."; return false; }
                if (!TryCreateSlot(p.SourceBuildingIndex, building, layout.Parcels[building.SourceParcelIndex], owner, selectedChoice,
                        profile, p.SlotIndex, out UrbanBuildingDecorationPlacement expected) ||
                    Vector2.Distance(p.LocalPosition, expected.LocalPosition) > Tolerance ||
                    Mathf.Abs(Mathf.DeltaAngle(p.LocalYawDegrees, expected.LocalYawDegrees)) > Tolerance)
                { error = $"Building decoration '{p.StableId}' does not occupy a declared '{p.Zone}' slot."; return false; }
                string countKey = $"{p.SourceBuildingIndex}:{p.RuleId}";
                ruleCounts.TryGetValue(countKey, out int count);
                if (count + 1 > owner.MaxCount)
                { error = $"Building decoration rule '{p.RuleId}' exceeds its per-building maximum."; return false; }
                ruleCounts[countKey] = count + 1;
                if (p.PhysicalSize.y >= building.Height || !IsAllowed(p, layout.Parcels[building.SourceParcelIndex], building, layout.Pois, profile))
                { error = $"Building decoration '{p.StableId}' violates its reservation or access corridor."; return false; }
                for (int j = i + 1; j < layout.BuildingDecorations.Count; j++)
                    if (p.Bounds.Overlaps(layout.BuildingDecorations[j].Bounds))
                    { error = $"Building decorations '{p.StableId}' and '{layout.BuildingDecorations[j].StableId}' overlap."; return false; }
            }
            error = null; return true;
        }

        private static bool IsAllowed(UrbanBuildingDecorationPlacement p, UrbanParcelPlacement parcel,
            UrbanBuildingPlacement building, IReadOnlyList<UrbanPoiPlacement> pois, UrbanBuildingLayoutProfile profile)
        {
            if (!parcel.Bounds.Contains(p.Bounds)) return false;
            float relativeYaw = (p.LocalYawDegrees - building.LocalYawDegrees) * Mathf.Deg2Rad;
            Rect rect = new UrbanOrientedRect(building.ToLocal(p.LocalPosition),
                new Vector2(p.PhysicalSize.x, p.PhysicalSize.z),
                new Vector2(Mathf.Sin(relativeYaw), Mathf.Cos(relativeYaw))).Aabb;
            Rect body = new Rect(-building.Size * .5f, building.Size);
            Rect interior = Expand(body, -profile.WallThickness);
            if (p.Interior ? !Contains(interior, rect) : Overlaps(Expand(body, profile.ExteriorWallOffset), rect)) return false;
            float halfAisle = profile.AisleWidth * .5f;
            Vector2 c = Vector2.zero;
            if (Overlaps(rect, new Rect(c.x - halfAisle, interior.yMin, profile.AisleWidth, interior.height)) ||
                Overlaps(rect, new Rect(interior.xMin, c.y - halfAisle, interior.width, profile.AisleWidth))) return false;
            foreach (UrbanPoiPlacement poi in pois)
            {
                if (poi.BuildingIndex != p.SourceBuildingIndex) continue;
                if (Overlaps(rect, SegmentBounds(building.ToLocal(poi.ContentLocalPosition), building.ToLocal(poi.ApproachLocalPosition), halfAisle))) return false;
            }
            return !p.Bounds.Overlaps(GetDoorAccessBounds(building, profile));
        }

        /// <summary>The actual shifted door's access corridor, in map-local XZ coordinates.</summary>
        public static UrbanOrientedRect GetDoorAccessBounds(UrbanBuildingPlacement building, UrbanBuildingLayoutProfile profile)
        {
            if (profile == null) throw new ArgumentNullException(nameof(profile));
            UrbanBuildingDoorGeometry door = UrbanBuildingDoorGeometry.Calculate(building.Size, Vector2.up,
                profile.WallThickness, profile.DoorWidth, building.Kind == UrbanPoiKind.Medical);
            Vector2 inside = door.OnZ ? new Vector2(door.LocalCenter.x, 0f) : new Vector2(0f, door.LocalCenter.y);
            Vector2 outside = door.LocalCenter + door.Outward * (profile.ReservedMargin + profile.WallThickness);
            return UrbanOrientedRect.FromSegment(building.ToMap(inside), building.ToMap(outside),
                Mathf.Max(profile.AisleWidth * .5f, door.Width * .5f));
        }

        public static Rect Expand(Rect rect, float amount) => new Rect(rect.xMin - amount, rect.yMin - amount, rect.width + amount * 2, rect.height + amount * 2);
        private static Rect SegmentBounds(Vector2 a, Vector2 b, float halfWidth) => new Rect(
            Mathf.Min(a.x, b.x) - halfWidth, Mathf.Min(a.y, b.y) - halfWidth,
            Mathf.Abs(a.x - b.x) + halfWidth * 2, Mathf.Abs(a.y - b.y) + halfWidth * 2);
        private static bool Contains(Rect outer, Rect inner) => inner.xMin >= outer.xMin - Tolerance && inner.xMax <= outer.xMax + Tolerance &&
            inner.yMin >= outer.yMin - Tolerance && inner.yMax <= outer.yMax + Tolerance;
        private static bool Overlaps(Rect a, Rect b) => a.xMin < b.xMax - Tolerance && a.xMax > b.xMin + Tolerance &&
            a.yMin < b.yMax - Tolerance && a.yMax > b.yMin + Tolerance;
        private static bool Finite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
    }

    internal sealed class UrbanDecorationHash
    {
        public ulong Value { get; private set; } = 1469598103934665603UL;
        public void Add(int value) { unchecked { Value = (Value ^ (uint)value) * 1099511628211UL; } }
        public void Add(float value) => Add(BitConverter.SingleToInt32Bits(value));
        public void Add(string value) { Add(value?.Length ?? 0); if (value != null) foreach (char c in value) Add(c); }
    }

    internal struct UrbanDecorationRandom
    {
        private uint state;
        public UrbanDecorationRandom(int seed, int parcel, string rule, int slot)
        {
            var h = new UrbanDecorationHash(); h.Add(seed); h.Add(parcel); h.Add(rule); h.Add(slot);
            state = (uint)(h.Value ^ (h.Value >> 32)); if (state == 0) state = 0x9e3779b9u;
        }
        public float Next() { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return (state >> 8) * (1f / 16777216f); }
    }
}
