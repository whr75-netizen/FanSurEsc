using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public readonly struct UrbanMapGenerationParameters
    {
        public UrbanMapGenerationParameters(
            int minBlocksX,
            int maxBlocksX,
            int minBlocksZ,
            int maxBlocksZ,
            float minBlockSize,
            float maxBlockSize,
            float intersectionJitter,
            float cityRotationMin,
            float cityRotationMax,
            float secondaryRoadWidth,
            float primaryRoadWidth,
            float minorRoadRemovalChance,
            float outerMargin,
            float buildingSetback,
            float lotGap,
            float buildingDensity,
            float minBuildingHeight,
            float maxBuildingHeight,
            float anchorClearance,
            float protectedAnchorClearance)
        {
            MinBlocksX = minBlocksX;
            MaxBlocksX = maxBlocksX;
            MinBlocksZ = minBlocksZ;
            MaxBlocksZ = maxBlocksZ;
            MinBlockSize = minBlockSize;
            MaxBlockSize = maxBlockSize;
            IntersectionJitter = intersectionJitter;
            CityRotationMin = cityRotationMin;
            CityRotationMax = cityRotationMax;
            SecondaryRoadWidth = secondaryRoadWidth;
            PrimaryRoadWidth = primaryRoadWidth;
            MinorRoadRemovalChance = minorRoadRemovalChance;
            OuterMargin = outerMargin;
            BuildingSetback = buildingSetback;
            LotGap = lotGap;
            BuildingDensity = buildingDensity;
            MinBuildingHeight = minBuildingHeight;
            MaxBuildingHeight = maxBuildingHeight;
            AnchorClearance = anchorClearance;
            ProtectedAnchorClearance = protectedAnchorClearance;
        }

        public int MinBlocksX { get; }
        public int MaxBlocksX { get; }
        public int MinBlocksZ { get; }
        public int MaxBlocksZ { get; }
        public float MinBlockSize { get; }
        public float MaxBlockSize { get; }
        public float IntersectionJitter { get; }
        public float CityRotationMin { get; }
        public float CityRotationMax { get; }
        public float SecondaryRoadWidth { get; }
        public float PrimaryRoadWidth { get; }
        public float MinorRoadRemovalChance { get; }
        public float OuterMargin { get; }
        public float BuildingSetback { get; }
        public float LotGap { get; }
        public float BuildingDensity { get; }
        public float MinBuildingHeight { get; }
        public float MaxBuildingHeight { get; }
        public float AnchorClearance { get; }
        public float ProtectedAnchorClearance { get; }

        public static UrbanMapGenerationParameters CreateDefault()
        {
            return new UrbanMapGenerationParameters(
                minBlocksX: 4,
                maxBlocksX: 6,
                minBlocksZ: 4,
                maxBlocksZ: 6,
                minBlockSize: 14f,
                maxBlockSize: 20f,
                intersectionJitter: 1.35f,
                cityRotationMin: 35f,
                cityRotationMax: 55f,
                secondaryRoadWidth: 3.2f,
                primaryRoadWidth: 5.2f,
                minorRoadRemovalChance: 0.18f,
                outerMargin: 6f,
                buildingSetback: 1.2f,
                lotGap: 0.9f,
                buildingDensity: 0.78f,
                minBuildingHeight: 2.75f,
                maxBuildingHeight: 8.5f,
                anchorClearance: 4.5f,
                protectedAnchorClearance: 3.5f);
        }

        public bool TryValidate(out string error)
        {
            if (MinBlocksX < 2 || MinBlocksZ < 2 || MaxBlocksX < MinBlocksX || MaxBlocksZ < MinBlocksZ)
            {
                error = "Urban map block-count ranges are invalid.";
                return false;
            }

            if (MinBlockSize <= 0f || MaxBlockSize < MinBlockSize)
            {
                error = "Urban map block-size range is invalid.";
                return false;
            }

            if (SecondaryRoadWidth <= 0f || PrimaryRoadWidth < SecondaryRoadWidth)
            {
                error = "Urban map road widths are invalid.";
                return false;
            }

            if (MinorRoadRemovalChance < 0f || MinorRoadRemovalChance > 1f ||
                BuildingDensity < 0f || BuildingDensity > 1f)
            {
                error = "Urban map probability values must be between zero and one.";
                return false;
            }

            if (OuterMargin <= 0f || BuildingSetback < 0f || LotGap < 0f ||
                AnchorClearance < 0f || ProtectedAnchorClearance < 0f)
            {
                error = "Urban map clearance values are invalid.";
                return false;
            }

            if (MaxBuildingHeight < MinBuildingHeight || MinBuildingHeight <= 0f)
            {
                error = "Urban map building-height range is invalid.";
                return false;
            }

            error = null;
            return true;
        }
    }

    public readonly struct UrbanRoadSegment
    {
        public UrbanRoadSegment(int fromNodeIndex, int toNodeIndex, Vector2 start, Vector2 end, float width, bool isPrimary)
        {
            FromNodeIndex = fromNodeIndex;
            ToNodeIndex = toNodeIndex;
            Start = start;
            End = end;
            Width = width;
            IsPrimary = isPrimary;
        }

        public int FromNodeIndex { get; }
        public int ToNodeIndex { get; }
        public Vector2 Start { get; }
        public Vector2 End { get; }
        public float Width { get; }
        public bool IsPrimary { get; }
        public float Length => Vector2.Distance(Start, End);
    }

    public readonly struct UrbanBuildingPlacement
    {
        public UrbanBuildingPlacement(Vector2 center, Vector2 size, float height, int paletteIndex)
        {
            Center = center;
            Size = size;
            Height = height;
            PaletteIndex = paletteIndex;
        }

        public Vector2 Center { get; }
        public Vector2 Size { get; }
        public float Height { get; }
        public int PaletteIndex { get; }
        public Rect Footprint => new Rect(Center - Size * 0.5f, Size);
    }

    public enum UrbanRaidSpawnKind
    {
        Chest,
        Enemy
    }

    /// <summary>
    /// Pure input for deterministic raid placement. The values are technical prototype
    /// safety limits, not final encounter balance.
    /// </summary>
    public readonly struct UrbanRaidSpawnRequest
    {
        public UrbanRaidSpawnRequest(
            string stableId,
            UrbanRaidSpawnKind kind,
            float entryClearance,
            float portalClearance,
            float minimumSeparation,
            float approachDistance)
        {
            StableId = stableId;
            Kind = kind;
            EntryClearance = entryClearance;
            PortalClearance = portalClearance;
            MinimumSeparation = minimumSeparation;
            ApproachDistance = approachDistance;
        }

        public string StableId { get; }
        public UrbanRaidSpawnKind Kind { get; }
        public float EntryClearance { get; }
        public float PortalClearance { get; }
        public float MinimumSeparation { get; }
        public float ApproachDistance { get; }

        public bool TryValidate(out string error)
        {
            if (string.IsNullOrWhiteSpace(StableId))
            {
                error = "Raid spawn request has no stable ID.";
                return false;
            }

            if (Kind != UrbanRaidSpawnKind.Chest && Kind != UrbanRaidSpawnKind.Enemy)
            {
                error = $"Raid spawn request '{StableId}' has an invalid kind.";
                return false;
            }

            if (!IsFiniteNonNegative(EntryClearance) ||
                !IsFiniteNonNegative(PortalClearance) ||
                !IsFiniteNonNegative(MinimumSeparation) ||
                !IsFiniteNonNegative(ApproachDistance))
            {
                error = $"Raid spawn request '{StableId}' has an invalid safety distance.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool IsFiniteNonNegative(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value) && value >= 0f;
        }
    }

    public readonly struct UrbanRaidSpawnPlacement
    {
        public UrbanRaidSpawnPlacement(
            string stableId,
            UrbanRaidSpawnKind kind,
            Vector2 localPosition,
            float localYawDegrees,
            Vector2 approachLocalPosition)
        {
            StableId = stableId;
            Kind = kind;
            LocalPosition = localPosition;
            LocalYawDegrees = localYawDegrees;
            ApproachLocalPosition = approachLocalPosition;
        }

        public string StableId { get; }
        public UrbanRaidSpawnKind Kind { get; }
        public Vector2 LocalPosition { get; }
        public float LocalYawDegrees { get; }
        public Vector2 ApproachLocalPosition { get; }
    }

    /// <summary>
    /// Immutable, derived raid placement cache. It is rebuilt from the authoritative map
    /// seed and stable IDs and is never a parallel owner of Chest or Enemy runtime state.
    /// </summary>
    public sealed class UrbanRaidSpawnManifest
    {
        private readonly IReadOnlyList<UrbanRaidSpawnPlacement> placements;

        internal UrbanRaidSpawnManifest(
            int version,
            int seed,
            IReadOnlyList<UrbanRaidSpawnPlacement> sourcePlacements)
        {
            Version = version;
            Seed = seed;
            var placementCopy = sourcePlacements == null
                ? new List<UrbanRaidSpawnPlacement>()
                : new List<UrbanRaidSpawnPlacement>(sourcePlacements);
            placements = placementCopy.AsReadOnly();
        }

        public int Version { get; }
        public int Seed { get; }
        public int Count => placements.Count;
        public IReadOnlyList<UrbanRaidSpawnPlacement> Placements => placements;

        public bool TryGetPlacement(string stableId, out UrbanRaidSpawnPlacement placement)
        {
            for (int index = 0; index < placements.Count; index++)
            {
                if (string.Equals(placements[index].StableId, stableId, StringComparison.Ordinal))
                {
                    placement = placements[index];
                    return true;
                }
            }

            placement = default;
            return false;
        }
    }

    public static class UrbanRaidSpawnPrototypeRules
    {
        public const float ChestEntryClearance = 10f;
        public const float ChestPortalClearance = 8f;
        public const float EnemyPortalClearance = 10f;
        public const float ChestMinimumSeparation = 5f;
        public const float EnemyMinimumSeparation = 6f;
        public const float ChestApproachDistance = 1f;
        public const float EnemyEntrySafetyBuffer = 2f;

        public static UrbanRaidSpawnRequest CreateChestRequest(string stableId)
        {
            return new UrbanRaidSpawnRequest(
                stableId,
                UrbanRaidSpawnKind.Chest,
                ChestEntryClearance,
                ChestPortalClearance,
                ChestMinimumSeparation,
                ChestApproachDistance);
        }

        public static UrbanRaidSpawnRequest CreateEnemyRequest(
            string stableId,
            float visionRange,
            float patrolRadius)
        {
            float entryClearance = Mathf.Max(
                ChestEntryClearance,
                Mathf.Max(0f, visionRange) + Mathf.Max(0f, patrolRadius) + EnemyEntrySafetyBuffer);
            return new UrbanRaidSpawnRequest(
                stableId,
                UrbanRaidSpawnKind.Enemy,
                entryClearance,
                EnemyPortalClearance,
                EnemyMinimumSeparation,
                approachDistance: 0f);
        }
    }

    public sealed class UrbanMapLayout
    {
        public UrbanMapLayout(
            int generatorVersion,
            int seed,
            int blocksX,
            int blocksZ,
            float cityRotationDegrees,
            Rect localBounds,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            Vector2 portalApproachLocalPosition,
            List<Vector2> nodes,
            List<UrbanRoadSegment> roads,
            List<UrbanBuildingPlacement> buildings,
            List<Vector2> protectedLocalPoints)
        {
            GeneratorVersion = generatorVersion;
            Seed = seed;
            BlocksX = blocksX;
            BlocksZ = blocksZ;
            CityRotationDegrees = cityRotationDegrees;
            LocalBounds = localBounds;
            EntryLocalPosition = entryLocalPosition;
            PortalLocalPosition = portalLocalPosition;
            PortalApproachLocalPosition = portalApproachLocalPosition;
            Nodes = nodes;
            Roads = roads;
            Buildings = buildings;
            ProtectedLocalPoints = protectedLocalPoints;
        }

        public int GeneratorVersion { get; }
        public int Seed { get; }
        public int BlocksX { get; }
        public int BlocksZ { get; }
        public float CityRotationDegrees { get; }
        public Rect LocalBounds { get; }
        public Vector2 EntryLocalPosition { get; }
        public Vector2 PortalLocalPosition { get; }
        public Vector2 PortalApproachLocalPosition { get; }
        public IReadOnlyList<Vector2> Nodes { get; }
        public IReadOnlyList<UrbanRoadSegment> Roads { get; }
        public IReadOnlyList<UrbanBuildingPlacement> Buildings { get; }
        public IReadOnlyList<Vector2> ProtectedLocalPoints { get; }
    }

    public static class UrbanMapLayoutValidator
    {
        private const float GeometryTolerance = 0.01f;

        public static bool TryValidate(
            UrbanMapLayout layout,
            UrbanMapGenerationParameters parameters,
            out string error)
        {
            if (layout == null)
            {
                error = "Urban map layout is null.";
                return false;
            }

            if (layout.Nodes.Count == 0 || layout.Roads.Count == 0)
            {
                error = "Urban map layout has no connected road data.";
                return false;
            }

            if (!IsRoadGraphConnected(layout.Nodes.Count, layout.Roads))
            {
                error = "Urban map road graph is disconnected.";
                return false;
            }

            for (int buildingIndex = 0; buildingIndex < layout.Buildings.Count; buildingIndex++)
            {
                UrbanBuildingPlacement building = layout.Buildings[buildingIndex];
                Rect footprint = building.Footprint;

                if (!ContainsRect(layout.LocalBounds, footprint))
                {
                    error = $"Building {buildingIndex} exceeds the generated map bounds.";
                    return false;
                }

                for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
                {
                    if (RoadIntersectsRect(layout.Roads[roadIndex], footprint, parameters.BuildingSetback))
                    {
                        error = $"Building {buildingIndex} intersects road {roadIndex}.";
                        return false;
                    }
                }

                if (RectIntersectsCircle(footprint, layout.EntryLocalPosition, parameters.AnchorClearance) ||
                    RectIntersectsCircle(footprint, layout.PortalLocalPosition, parameters.AnchorClearance))
                {
                    error = $"Building {buildingIndex} blocks a critical map anchor.";
                    return false;
                }

                for (int pointIndex = 0; pointIndex < layout.ProtectedLocalPoints.Count; pointIndex++)
                {
                    if (RectIntersectsCircle(
                            footprint,
                            layout.ProtectedLocalPoints[pointIndex],
                            parameters.ProtectedAnchorClearance))
                    {
                        error = $"Building {buildingIndex} blocks protected point {pointIndex}.";
                        return false;
                    }
                }

                for (int otherIndex = buildingIndex + 1; otherIndex < layout.Buildings.Count; otherIndex++)
                {
                    if (footprint.Overlaps(layout.Buildings[otherIndex].Footprint))
                    {
                        error = $"Buildings {buildingIndex} and {otherIndex} overlap.";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        public static ulong ComputeStableHash(UrbanMapLayout layout)
        {
            if (layout == null)
            {
                throw new ArgumentNullException(nameof(layout));
            }

            const ulong offset = 1469598103934665603UL;
            const ulong prime = 1099511628211UL;
            ulong hash = offset;

            AddInt(layout.GeneratorVersion);
            AddInt(layout.BlocksX);
            AddInt(layout.BlocksZ);
            AddFloat(layout.CityRotationDegrees);
            AddFloat(layout.LocalBounds.width);
            AddFloat(layout.LocalBounds.height);

            for (int index = 0; index < layout.Roads.Count; index++)
            {
                UrbanRoadSegment road = layout.Roads[index];
                AddInt(road.FromNodeIndex);
                AddInt(road.ToNodeIndex);
                AddFloat(road.Start.x);
                AddFloat(road.Start.y);
                AddFloat(road.End.x);
                AddFloat(road.End.y);
                AddFloat(road.Width);
                AddInt(road.IsPrimary ? 1 : 0);
            }

            for (int index = 0; index < layout.Buildings.Count; index++)
            {
                UrbanBuildingPlacement building = layout.Buildings[index];
                AddFloat(building.Center.x);
                AddFloat(building.Center.y);
                AddFloat(building.Size.x);
                AddFloat(building.Size.y);
                AddFloat(building.Height);
                AddInt(building.PaletteIndex);
            }

            return hash;

            void AddInt(int value)
            {
                unchecked
                {
                    hash ^= (uint)value;
                    hash *= prime;
                }
            }

            void AddFloat(float value)
            {
                AddInt(Mathf.RoundToInt(value * 1000f));
            }
        }

        public static ulong ComputeStableHash(UrbanRaidSpawnManifest manifest)
        {
            if (manifest == null)
            {
                throw new ArgumentNullException(nameof(manifest));
            }

            const ulong offset = 1469598103934665603UL;
            const ulong prime = 1099511628211UL;
            ulong hash = offset;

            AddInt(manifest.Version);
            AddInt(manifest.Seed);
            AddInt(manifest.Count);
            for (int index = 0; index < manifest.Count; index++)
            {
                UrbanRaidSpawnPlacement placement = manifest.Placements[index];
                AddString(placement.StableId);
                AddInt((int)placement.Kind);
                AddFloat(placement.LocalPosition.x);
                AddFloat(placement.LocalPosition.y);
                AddFloat(placement.LocalYawDegrees);
                AddFloat(placement.ApproachLocalPosition.x);
                AddFloat(placement.ApproachLocalPosition.y);
            }

            return hash;

            void AddString(string value)
            {
                AddInt(value?.Length ?? 0);
                if (value == null)
                {
                    return;
                }

                for (int index = 0; index < value.Length; index++)
                {
                    AddInt(value[index]);
                }
            }

            void AddInt(int value)
            {
                unchecked
                {
                    hash ^= (uint)value;
                    hash *= prime;
                }
            }

            void AddFloat(float value)
            {
                AddInt(Mathf.RoundToInt(value * 1000f));
            }
        }

        public static ulong ComputeStableWorldHash(
            UrbanMapLayout layout,
            UrbanRaidSpawnManifest spawnManifest)
        {
            const ulong offset = 1469598103934665603UL;
            const ulong prime = 1099511628211UL;
            ulong hash = offset;

            AddUInt64(ComputeStableHash(layout));
            AddUInt64(ComputeStableHash(spawnManifest));
            return hash;

            void AddUInt64(ulong value)
            {
                unchecked
                {
                    hash ^= (uint)value;
                    hash *= prime;
                    hash ^= (uint)(value >> 32);
                    hash *= prime;
                }
            }
        }

        internal static bool RoadIntersectsRect(UrbanRoadSegment road, Rect rect, float extraClearance)
        {
            float expansion = road.Width * 0.5f + Mathf.Max(0f, extraClearance);
            Rect expanded = new Rect(
                rect.xMin - expansion,
                rect.yMin - expansion,
                rect.width + expansion * 2f,
                rect.height + expansion * 2f);

            return SegmentIntersectsRect(road.Start, road.End, expanded);
        }

        internal static bool RectIntersectsCircle(Rect rect, Vector2 center, float radius)
        {
            float closestX = Mathf.Clamp(center.x, rect.xMin, rect.xMax);
            float closestY = Mathf.Clamp(center.y, rect.yMin, rect.yMax);
            return (new Vector2(closestX, closestY) - center).sqrMagnitude <= radius * radius;
        }

        private static bool IsRoadGraphConnected(int nodeCount, IReadOnlyList<UrbanRoadSegment> roads)
        {
            var adjacency = new List<int>[nodeCount];
            for (int index = 0; index < nodeCount; index++)
            {
                adjacency[index] = new List<int>();
            }

            for (int index = 0; index < roads.Count; index++)
            {
                UrbanRoadSegment road = roads[index];
                adjacency[road.FromNodeIndex].Add(road.ToNodeIndex);
                adjacency[road.ToNodeIndex].Add(road.FromNodeIndex);
            }

            var visited = new bool[nodeCount];
            var queue = new Queue<int>();
            queue.Enqueue(0);
            visited[0] = true;
            int visitedCount = 0;

            while (queue.Count > 0)
            {
                int current = queue.Dequeue();
                visitedCount++;
                for (int index = 0; index < adjacency[current].Count; index++)
                {
                    int next = adjacency[current][index];
                    if (visited[next])
                    {
                        continue;
                    }

                    visited[next] = true;
                    queue.Enqueue(next);
                }
            }

            return visitedCount == nodeCount;
        }

        private static bool ContainsRect(Rect outer, Rect inner)
        {
            return inner.xMin >= outer.xMin - GeometryTolerance &&
                   inner.xMax <= outer.xMax + GeometryTolerance &&
                   inner.yMin >= outer.yMin - GeometryTolerance &&
                   inner.yMax <= outer.yMax + GeometryTolerance;
        }

        private static bool SegmentIntersectsRect(Vector2 start, Vector2 end, Rect rect)
        {
            if (rect.Contains(start) || rect.Contains(end))
            {
                return true;
            }

            Vector2 bottomLeft = new Vector2(rect.xMin, rect.yMin);
            Vector2 bottomRight = new Vector2(rect.xMax, rect.yMin);
            Vector2 topRight = new Vector2(rect.xMax, rect.yMax);
            Vector2 topLeft = new Vector2(rect.xMin, rect.yMax);

            return SegmentsIntersect(start, end, bottomLeft, bottomRight) ||
                   SegmentsIntersect(start, end, bottomRight, topRight) ||
                   SegmentsIntersect(start, end, topRight, topLeft) ||
                   SegmentsIntersect(start, end, topLeft, bottomLeft);
        }

        private static bool SegmentsIntersect(Vector2 a, Vector2 b, Vector2 c, Vector2 d)
        {
            if (Mathf.Max(a.x, b.x) + GeometryTolerance < Mathf.Min(c.x, d.x) ||
                Mathf.Max(c.x, d.x) + GeometryTolerance < Mathf.Min(a.x, b.x) ||
                Mathf.Max(a.y, b.y) + GeometryTolerance < Mathf.Min(c.y, d.y) ||
                Mathf.Max(c.y, d.y) + GeometryTolerance < Mathf.Min(a.y, b.y))
            {
                return false;
            }

            float abC = Cross(b - a, c - a);
            float abD = Cross(b - a, d - a);
            float cdA = Cross(d - c, a - c);
            float cdB = Cross(d - c, b - c);

            return abC * abD <= GeometryTolerance && cdA * cdB <= GeometryTolerance;
        }

        private static float Cross(Vector2 a, Vector2 b)
        {
            return a.x * b.y - a.y * b.x;
        }
    }
}
