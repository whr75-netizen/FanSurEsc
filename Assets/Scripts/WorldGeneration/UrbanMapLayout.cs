using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public readonly struct UrbanMapGenerationParameters
    {
        public UrbanMapGenerationParameters(
            int mapTilesPerAxis,
            int blocksPerAxis,
            int borderTiles,
            float tileWorldSize,
            int secondaryRoadWidthTiles,
            int primaryRoadWidthTiles,
            float additionalRoadChance,
            float diagonalRoadChance,
            int sidewalkWidthTiles,
            float buildingSetback,
            float lotGap,
            int minBuildingFrontageTiles,
            int maxBuildingFrontageTiles,
            int minBuildingDepthTiles,
            int maxBuildingDepthTiles,
            float buildingDensity,
            float minBuildingHeight,
            float maxBuildingHeight,
            float anchorClearance,
            float protectedAnchorClearance,
            int junctionFurnitureClearanceTiles,
            int streetTreeSpacingTiles,
            int streetLampSpacingTiles,
            int clutterSpacingTiles,
            float clutterChance)
        {
            MapTilesPerAxis = mapTilesPerAxis;
            BlocksPerAxis = blocksPerAxis;
            BorderTiles = borderTiles;
            TileWorldSize = tileWorldSize;
            SecondaryRoadWidthTiles = secondaryRoadWidthTiles;
            PrimaryRoadWidthTiles = primaryRoadWidthTiles;
            AdditionalRoadChance = additionalRoadChance;
            DiagonalRoadChance = diagonalRoadChance;
            SidewalkWidthTiles = sidewalkWidthTiles;
            BuildingSetback = buildingSetback;
            LotGap = lotGap;
            MinBuildingFrontageTiles = minBuildingFrontageTiles;
            MaxBuildingFrontageTiles = maxBuildingFrontageTiles;
            MinBuildingDepthTiles = minBuildingDepthTiles;
            MaxBuildingDepthTiles = maxBuildingDepthTiles;
            BuildingDensity = buildingDensity;
            MinBuildingHeight = minBuildingHeight;
            MaxBuildingHeight = maxBuildingHeight;
            AnchorClearance = anchorClearance;
            ProtectedAnchorClearance = protectedAnchorClearance;
            JunctionFurnitureClearanceTiles = junctionFurnitureClearanceTiles;
            StreetTreeSpacingTiles = streetTreeSpacingTiles;
            StreetLampSpacingTiles = streetLampSpacingTiles;
            ClutterSpacingTiles = clutterSpacingTiles;
            ClutterChance = clutterChance;
        }

        public int MapTilesPerAxis { get; }
        public int BlocksPerAxis { get; }
        public int BorderTiles { get; }
        public float TileWorldSize { get; }
        public int SecondaryRoadWidthTiles { get; }
        public int PrimaryRoadWidthTiles { get; }
        public float AdditionalRoadChance { get; }
        public float DiagonalRoadChance { get; }
        public int SidewalkWidthTiles { get; }
        public float BuildingSetback { get; }
        public float LotGap { get; }
        public int MinBuildingFrontageTiles { get; }
        public int MaxBuildingFrontageTiles { get; }
        public int MinBuildingDepthTiles { get; }
        public int MaxBuildingDepthTiles { get; }
        public float BuildingDensity { get; }
        public float MinBuildingHeight { get; }
        public float MaxBuildingHeight { get; }
        public float AnchorClearance { get; }
        public float ProtectedAnchorClearance { get; }
        public int JunctionFurnitureClearanceTiles { get; }
        public int StreetTreeSpacingTiles { get; }
        public int StreetLampSpacingTiles { get; }
        public int ClutterSpacingTiles { get; }
        public float ClutterChance { get; }

        public int BlockSpanTiles =>
            (MapTilesPerAxis - 1 - BorderTiles * 2) / BlocksPerAxis;
        public float MapWorldSize => MapTilesPerAxis * TileWorldSize;
        public float BlockSpanWorld => BlockSpanTiles * TileWorldSize;
        public float SecondaryRoadWidth => SecondaryRoadWidthTiles * TileWorldSize;
        public float PrimaryRoadWidth => PrimaryRoadWidthTiles * TileWorldSize;
        public float SidewalkWidth => SidewalkWidthTiles * TileWorldSize;

        public static UrbanMapGenerationParameters CreateDefault()
        {
            return new UrbanMapGenerationParameters(
                mapTilesPerAxis: 145,
                blocksPerAxis: 6,
                borderTiles: 12,
                tileWorldSize: 2f,
                secondaryRoadWidthTiles: 3,
                primaryRoadWidthTiles: 5,
                additionalRoadChance: 0.35f,
                diagonalRoadChance: 0.2f,
                sidewalkWidthTiles: 1,
                buildingSetback: 2f,
                lotGap: 2f,
                minBuildingFrontageTiles: 5,
                maxBuildingFrontageTiles: 6,
                minBuildingDepthTiles: 3,
                maxBuildingDepthTiles: 4,
                buildingDensity: 0.8f,
                minBuildingHeight: 10.5f,
                maxBuildingHeight: 18f,
                anchorClearance: 10f,
                protectedAnchorClearance: 8f,
                junctionFurnitureClearanceTiles: 3,
                streetTreeSpacingTiles: 7,
                streetLampSpacingTiles: 18,
                clutterSpacingTiles: 5,
                clutterChance: 0.22f);
        }

        public bool TryValidate(out string error)
        {
            if (MapTilesPerAxis < 17 || (MapTilesPerAxis & 1) == 0 ||
                BlocksPerAxis < 2 || BorderTiles < 1 ||
                MapTilesPerAxis - 1 - BorderTiles * 2 <= 0 ||
                (MapTilesPerAxis - 1 - BorderTiles * 2) % BlocksPerAxis != 0)
            {
                error =
                    "Urban map tile dimensions must form one odd, fixed square whose " +
                    "interior span divides evenly into the configured block count.";
                return false;
            }

            if (!IsFinite(TileWorldSize) || TileWorldSize <= 0f)
            {
                error = "Urban map tile world size must be positive.";
                return false;
            }

            if (SecondaryRoadWidthTiles <= 0 || PrimaryRoadWidthTiles < SecondaryRoadWidthTiles ||
                (SecondaryRoadWidthTiles & 1) == 0 || (PrimaryRoadWidthTiles & 1) == 0 ||
                SidewalkWidthTiles < 1 ||
                PrimaryRoadWidthTiles + SidewalkWidthTiles * 2 >= BlockSpanTiles)
            {
                error =
                    "Urban road widths must be odd tile counts, leave buildable space " +
                    "inside each block, and have at least one sidewalk tile per side.";
                return false;
            }

            if (!IsFinite(AdditionalRoadChance) || AdditionalRoadChance < 0f || AdditionalRoadChance > 1f ||
                !IsFinite(DiagonalRoadChance) || DiagonalRoadChance < 0f || DiagonalRoadChance > 1f ||
                !IsFinite(BuildingDensity) || BuildingDensity < 0f || BuildingDensity > 1f ||
                !IsFinite(ClutterChance) || ClutterChance < 0f || ClutterChance > 1f)
            {
                error = "Urban map probability values must be between zero and one.";
                return false;
            }

            if (!IsFinite(BuildingSetback) || BuildingSetback < 0f ||
                !IsFinite(LotGap) || LotGap < 0f ||
                !IsFinite(AnchorClearance) || AnchorClearance < 0f ||
                !IsFinite(ProtectedAnchorClearance) || ProtectedAnchorClearance < 0f)
            {
                error = "Urban map clearance values are invalid.";
                return false;
            }

            if (MinBuildingFrontageTiles < 3 ||
                MaxBuildingFrontageTiles < MinBuildingFrontageTiles ||
                MinBuildingDepthTiles < 3 ||
                MaxBuildingDepthTiles < MinBuildingDepthTiles ||
                MaxBuildingFrontageTiles >= BlockSpanTiles ||
                MaxBuildingDepthTiles >= BlockSpanTiles)
            {
                error = "Urban building parcel tile ranges are invalid for the configured block span.";
                return false;
            }

            if (!IsFinite(MinBuildingHeight) || !IsFinite(MaxBuildingHeight) ||
                MaxBuildingHeight < MinBuildingHeight || MinBuildingHeight <= 0f)
            {
                error = "Urban map building-height range is invalid.";
                return false;
            }

            if (JunctionFurnitureClearanceTiles < 1 || StreetTreeSpacingTiles < 2 ||
                StreetLampSpacingTiles < 2 || ClutterSpacingTiles < 2)
            {
                error = "Urban street-furniture tile spacing values are invalid.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
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
        public UrbanBuildingPlacement(
            int sourceParcelIndex,
            Vector2 center,
            Vector2 size,
            float height,
            int paletteIndex)
        {
            SourceParcelIndex = sourceParcelIndex;
            Center = center;
            Size = size;
            Height = height;
            PaletteIndex = paletteIndex;
        }

        public int SourceParcelIndex { get; }
        public Vector2 Center { get; }
        public Vector2 Size { get; }
        public float Height { get; }
        public int PaletteIndex { get; }
        public Rect Footprint => new Rect(Center - Size * 0.5f, Size);
    }

    /// <summary>
    /// One non-overlapping, road-fronting buildable lot. Roads own the frontage;
    /// buildings may occupy a parcel but never redefine it. This keeps future
    /// building catalogs and footprint variants separate from city subdivision.
    /// </summary>
    public readonly struct UrbanParcelPlacement
    {
        public UrbanParcelPlacement(
            int stableId,
            int sourceRoadIndex,
            float distanceAlongRoad,
            int side,
            Vector2 center,
            Vector2 size,
            Vector2 facadeDirection)
        {
            StableId = stableId;
            SourceRoadIndex = sourceRoadIndex;
            DistanceAlongRoad = distanceAlongRoad;
            Side = side;
            Center = center;
            Size = size;
            FacadeDirection = facadeDirection;
        }

        public int StableId { get; }
        public int SourceRoadIndex { get; }
        public float DistanceAlongRoad { get; }
        public int Side { get; }
        public Vector2 Center { get; }
        public Vector2 Size { get; }
        public Vector2 FacadeDirection { get; }
        public Rect Footprint => new Rect(Center - Size * 0.5f, Size);
    }

    public enum UrbanStreetFurnitureKind : byte
    {
        StreetTree = 0,
        StreetLamp = 1,
        Bicycle = 2,
        TrashBin = 3
    }

    /// <summary>
    /// Immutable placement measured from one road edge. Keeping the source edge,
    /// distance, side, and lateral offset makes presentation replaceable without
    /// losing the deterministic rule that produced the placement.
    /// </summary>
    public readonly struct UrbanStreetFurniturePlacement
    {
        public UrbanStreetFurniturePlacement(
            int stableId,
            UrbanStreetFurnitureKind kind,
            int sourceRoadIndex,
            float distanceAlongRoad,
            int side,
            float lateralOffset,
            Vector2 localPosition,
            float localYawDegrees)
        {
            StableId = stableId;
            Kind = kind;
            SourceRoadIndex = sourceRoadIndex;
            DistanceAlongRoad = distanceAlongRoad;
            Side = side;
            LateralOffset = lateralOffset;
            LocalPosition = localPosition;
            LocalYawDegrees = localYawDegrees;
        }

        public int StableId { get; }
        public UrbanStreetFurnitureKind Kind { get; }
        public int SourceRoadIndex { get; }
        public float DistanceAlongRoad { get; }
        public int Side { get; }
        public float LateralOffset { get; }
        public Vector2 LocalPosition { get; }
        public float LocalYawDegrees { get; }
    }

    public enum UrbanSpatialCandidateKind
    {
        Roadside,
        BuildingApproach
    }

    /// <summary>
    /// Immutable, seed-derived spatial query result shared by placement and AI systems.
    /// It is a cache of the authoritative layout, not a runtime state owner.
    /// </summary>
    public readonly struct UrbanSpatialCandidate
    {
        public UrbanSpatialCandidate(
            int stableId,
            UrbanSpatialCandidateKind kind,
            Vector2 localPosition,
            Vector2 localDirection,
            int sourceBuildingIndex)
        {
            StableId = stableId;
            Kind = kind;
            LocalPosition = localPosition;
            LocalDirection = localDirection;
            SourceBuildingIndex = sourceBuildingIndex;
        }

        public int StableId { get; }
        public UrbanSpatialCandidateKind Kind { get; }
        public Vector2 LocalPosition { get; }
        public Vector2 LocalDirection { get; }
        public int SourceBuildingIndex { get; }
    }

    public enum UrbanPoiKind
    {
        None,
        Medical
    }

    /// <summary>
    /// Authoritative semantic placement for a point of interest. Rendering color and
    /// bound runtime content are projections of this record.
    /// </summary>
    public readonly struct UrbanPoiPlacement
    {
        public UrbanPoiPlacement(
            string stableId,
            UrbanPoiKind kind,
            int buildingIndex,
            Vector2 contentLocalPosition,
            Vector2 approachLocalPosition,
            float localYawDegrees)
        {
            StableId = stableId;
            Kind = kind;
            BuildingIndex = buildingIndex;
            ContentLocalPosition = contentLocalPosition;
            ApproachLocalPosition = approachLocalPosition;
            LocalYawDegrees = localYawDegrees;
        }

        public string StableId { get; }
        public UrbanPoiKind Kind { get; }
        public int BuildingIndex { get; }
        public Vector2 ContentLocalPosition { get; }
        public Vector2 ApproachLocalPosition { get; }
        public float LocalYawDegrees { get; }
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
            float maximumEntryDistance,
            float portalClearance,
            float minimumSeparation,
            float approachDistance,
            UrbanPoiKind requiredPoiKind = UrbanPoiKind.None)
        {
            StableId = stableId;
            Kind = kind;
            EntryClearance = entryClearance;
            MaximumEntryDistance = maximumEntryDistance;
            PortalClearance = portalClearance;
            MinimumSeparation = minimumSeparation;
            ApproachDistance = approachDistance;
            RequiredPoiKind = requiredPoiKind;
        }

        public string StableId { get; }
        public UrbanRaidSpawnKind Kind { get; }
        public float EntryClearance { get; }
        public float MaximumEntryDistance { get; }
        public float PortalClearance { get; }
        public float MinimumSeparation { get; }
        public float ApproachDistance { get; }
        public UrbanPoiKind RequiredPoiKind { get; }

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

            if (RequiredPoiKind != UrbanPoiKind.None &&
                RequiredPoiKind != UrbanPoiKind.Medical)
            {
                error = $"Raid spawn request '{StableId}' has an invalid POI kind.";
                return false;
            }

            if (RequiredPoiKind != UrbanPoiKind.None && Kind != UrbanRaidSpawnKind.Chest)
            {
                error = $"Raid spawn request '{StableId}' assigns a POI to a non-Chest entity.";
                return false;
            }

            if (!IsFiniteNonNegative(EntryClearance) ||
                !IsFiniteNonNegative(MaximumEntryDistance) ||
                !IsFiniteNonNegative(PortalClearance) ||
                !IsFiniteNonNegative(MinimumSeparation) ||
                !IsFiniteNonNegative(ApproachDistance))
            {
                error = $"Raid spawn request '{StableId}' has an invalid safety distance.";
                return false;
            }

            if (MaximumEntryDistance > 0f &&
                MaximumEntryDistance < EntryClearance)
            {
                error =
                    $"Raid spawn request '{StableId}' has a maximum Entry distance " +
                    "smaller than its Entry clearance.";
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
        public const float ChestEntryClearance = 3.5f;
        public const float ChestMaximumEntryDistance = 8f;
        public const float ChestPortalClearance = 3f;
        public const float EnemyPortalClearance = 10f;
        public const float ChestMinimumSeparation = 3f;
        public const float EnemyMinimumSeparation = 6f;
        public const float ChestApproachDistance = 1f;
        public const float EnemyEntrySafetyBuffer = 2f;
        public const float NearMeleeEntryClearance = 7f;
        public const float NearMeleeMaximumEntryDistance = 16f;
        public const float NearMeleePortalClearance = 3f;
        public const float NearMeleeMinimumSeparation = 3f;

        public static UrbanRaidSpawnRequest CreateChestRequest(string stableId)
        {
            return new UrbanRaidSpawnRequest(
                stableId,
                UrbanRaidSpawnKind.Chest,
                ChestEntryClearance,
                ChestMaximumEntryDistance,
                ChestPortalClearance,
                ChestMinimumSeparation,
                ChestApproachDistance);
        }

        public static UrbanRaidSpawnRequest CreatePoiChestRequest(
            string stableId,
            UrbanPoiKind requiredPoiKind)
        {
            return new UrbanRaidSpawnRequest(
                stableId,
                UrbanRaidSpawnKind.Chest,
                ChestEntryClearance,
                maximumEntryDistance: 0f,
                ChestPortalClearance,
                ChestMinimumSeparation,
                approachDistance: 0f,
                requiredPoiKind);
        }

        public static UrbanRaidSpawnRequest CreateNearEntryMeleeRequest(string stableId)
        {
            return new UrbanRaidSpawnRequest(
                stableId,
                UrbanRaidSpawnKind.Enemy,
                NearMeleeEntryClearance,
                NearMeleeMaximumEntryDistance,
                NearMeleePortalClearance,
                NearMeleeMinimumSeparation,
                approachDistance: 0f);
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
                0f,
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
            UrbanSurfaceGrid surfaceGrid,
            List<UrbanParcelPlacement> parcels,
            List<UrbanBuildingPlacement> buildings,
            List<UrbanStreetFurniturePlacement> streetFurniture,
            List<Vector2> protectedLocalPoints,
            List<UrbanSpatialCandidate> candidates,
            List<UrbanPoiPlacement> pois)
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
            SurfaceGrid = surfaceGrid ?? throw new ArgumentNullException(nameof(surfaceGrid));
            Parcels = new List<UrbanParcelPlacement>(
                parcels ?? new List<UrbanParcelPlacement>()).AsReadOnly();
            Buildings = buildings;
            StreetFurniture = new List<UrbanStreetFurniturePlacement>(
                streetFurniture ?? new List<UrbanStreetFurniturePlacement>()).AsReadOnly();
            ProtectedLocalPoints = protectedLocalPoints;
            Candidates = new List<UrbanSpatialCandidate>(
                candidates ?? new List<UrbanSpatialCandidate>()).AsReadOnly();
            Pois = new List<UrbanPoiPlacement>(
                pois ?? new List<UrbanPoiPlacement>()).AsReadOnly();
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
        public UrbanSurfaceGrid SurfaceGrid { get; }
        public IReadOnlyList<UrbanParcelPlacement> Parcels { get; }
        public IReadOnlyList<UrbanBuildingPlacement> Buildings { get; }
        public IReadOnlyList<UrbanStreetFurniturePlacement> StreetFurniture { get; }
        public IReadOnlyList<Vector2> ProtectedLocalPoints { get; }
        public IReadOnlyList<UrbanSpatialCandidate> Candidates { get; }
        public IReadOnlyList<UrbanPoiPlacement> Pois { get; }

        public bool TryGetPoi(UrbanPoiKind kind, out UrbanPoiPlacement placement)
        {
            for (int index = 0; index < Pois.Count; index++)
            {
                if (Pois[index].Kind == kind)
                {
                    placement = Pois[index];
                    return true;
                }
            }

            placement = default;
            return false;
        }
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

            if (layout.BlocksX != parameters.BlocksPerAxis ||
                layout.BlocksZ != parameters.BlocksPerAxis ||
                !Mathf.Approximately(layout.CityRotationDegrees, 0f) ||
                !Mathf.Approximately(layout.LocalBounds.width, parameters.MapWorldSize) ||
                !Mathf.Approximately(layout.LocalBounds.height, parameters.MapWorldSize))
            {
                error = "Urban map no longer matches its fixed square, unrotated tile contract.";
                return false;
            }

            UrbanSurfaceGrid surfaceGrid = layout.SurfaceGrid;
            if (surfaceGrid == null ||
                surfaceGrid.Width != parameters.MapTilesPerAxis ||
                surfaceGrid.Height != parameters.MapTilesPerAxis ||
                !Mathf.Approximately(surfaceGrid.TileSize, parameters.TileWorldSize) ||
                Vector2.Distance(surfaceGrid.LocalOrigin, layout.LocalBounds.position) > GeometryTolerance)
            {
                error = "Urban map surface grid does not match its fixed map parameters.";
                return false;
            }

            for (int nodeIndex = 0; nodeIndex < layout.Nodes.Count; nodeIndex++)
            {
                if (!IsFinite(layout.Nodes[nodeIndex]))
                {
                    error = $"Road node {nodeIndex} is not finite.";
                    return false;
                }

                for (int otherNodeIndex = nodeIndex + 1;
                     otherNodeIndex < layout.Nodes.Count;
                     otherNodeIndex++)
                {
                    if ((layout.Nodes[nodeIndex] - layout.Nodes[otherNodeIndex]).sqrMagnitude <=
                        GeometryTolerance * GeometryTolerance)
                    {
                        error = $"Road nodes {nodeIndex} and {otherNodeIndex} occupy the same point.";
                        return false;
                    }
                }
            }

            for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = layout.Roads[roadIndex];
                Vector2 delta = road.End - road.Start;
                bool isOctilinear = Mathf.Abs(delta.x) <= GeometryTolerance ||
                                    Mathf.Abs(delta.y) <= GeometryTolerance ||
                                    Mathf.Abs(Mathf.Abs(delta.x) - Mathf.Abs(delta.y)) <= GeometryTolerance;
                if (road.FromNodeIndex < 0 || road.FromNodeIndex >= layout.Nodes.Count ||
                    road.ToNodeIndex < 0 || road.ToNodeIndex >= layout.Nodes.Count ||
                    road.FromNodeIndex == road.ToNodeIndex ||
                    (road.Start - layout.Nodes[road.FromNodeIndex]).sqrMagnitude >
                    GeometryTolerance * GeometryTolerance ||
                    (road.End - layout.Nodes[road.ToNodeIndex]).sqrMagnitude >
                    GeometryTolerance * GeometryTolerance ||
                    !IsFinite(road.Width) || road.Width <= 0f ||
                    !isOctilinear || delta.sqrMagnitude <= GeometryTolerance * GeometryTolerance)
                {
                    error = $"Road {roadIndex} has invalid node binding, width, or eight-direction geometry.";
                    return false;
                }
            }

            if (!IsRoadGraphConnected(layout.Nodes.Count, layout.Roads))
            {
                error = "Urban map road graph is disconnected.";
                return false;
            }

            if (!TryValidateRoadIntersections(layout, out error))
            {
                return false;
            }

            if (!TryBuildExpectedRoadPorts(
                    layout.Roads,
                    surfaceGrid,
                    out UrbanTileConnection[] expectedRoadPorts,
                    out error))
            {
                return false;
            }

            if (!TryValidateSurfaceGrid(surfaceGrid, expectedRoadPorts, out error))
            {
                return false;
            }

            var parcelIds = new HashSet<int>();
            for (int parcelIndex = 0; parcelIndex < layout.Parcels.Count; parcelIndex++)
            {
                UrbanParcelPlacement parcel = layout.Parcels[parcelIndex];
                Rect footprint = parcel.Footprint;
                if (parcel.StableId < 0 || !parcelIds.Add(parcel.StableId) ||
                    parcel.SourceRoadIndex < 0 || parcel.SourceRoadIndex >= layout.Roads.Count ||
                    (parcel.Side != -1 && parcel.Side != 1) ||
                    !IsFinite(parcel.DistanceAlongRoad) || parcel.DistanceAlongRoad < 0f ||
                    !IsFinite(parcel.Center) || !IsFinite(parcel.Size) ||
                    parcel.Size.x <= 0f || parcel.Size.y <= 0f ||
                    !IsFinite(parcel.FacadeDirection) ||
                    Mathf.Abs(parcel.FacadeDirection.sqrMagnitude - 1f) > GeometryTolerance)
                {
                    error = $"Urban parcel {parcelIndex} has invalid identity, source, or geometry.";
                    return false;
                }

                UrbanRoadSegment sourceRoad = layout.Roads[parcel.SourceRoadIndex];
                Vector2 sourceDelta = sourceRoad.End - sourceRoad.Start;
                bool sourceIsCardinal = Mathf.Abs(sourceDelta.x) <= GeometryTolerance ||
                                        Mathf.Abs(sourceDelta.y) <= GeometryTolerance;
                if (!sourceIsCardinal || parcel.DistanceAlongRoad > sourceRoad.Length + GeometryTolerance)
                {
                    error = $"Urban parcel {parcel.StableId} does not have a valid cardinal road frontage.";
                    return false;
                }

                Vector2 roadPoint = sourceRoad.Start +
                                    sourceDelta.normalized * parcel.DistanceAlongRoad;
                Vector2 roadDirection = sourceDelta.normalized;
                Vector2 roadNormal = new Vector2(-roadDirection.y, roadDirection.x);
                Vector2 expectedAwayFromRoad = roadNormal * parcel.Side;
                float parcelDepth = Mathf.Abs(roadDirection.x) > 0.5f
                    ? parcel.Size.y
                    : parcel.Size.x;
                float expectedCenterOffset = sourceRoad.Width * 0.5f +
                                             parameters.SidewalkWidth +
                                             parameters.BuildingSetback +
                                             parameters.TileWorldSize * 0.5f +
                                             parcelDepth * 0.5f;
                Vector2 expectedCenter = roadPoint + expectedAwayFromRoad * expectedCenterOffset;
                Vector2 expectedFacade = -expectedAwayFromRoad;
                if (Vector2.Distance(parcel.Center, expectedCenter) > GeometryTolerance ||
                    Vector2.Distance(parcel.FacadeDirection, expectedFacade) > GeometryTolerance)
                {
                    error = $"Urban parcel {parcel.StableId} does not match its road side, offset, or facade contract.";
                    return false;
                }

                if (!ContainsRect(layout.LocalBounds, footprint) ||
                    !FootprintUsesOnlyGround(surfaceGrid, footprint))
                {
                    error = $"Urban parcel {parcel.StableId} is outside buildable ground.";
                    return false;
                }

                for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
                {
                    if (RoadIntersectsRect(
                            layout.Roads[roadIndex],
                            footprint,
                            parameters.SidewalkWidth + parameters.BuildingSetback))
                    {
                        error = $"Urban parcel {parcel.StableId} intersects road {roadIndex}.";
                        return false;
                    }
                }

                for (int otherIndex = parcelIndex + 1; otherIndex < layout.Parcels.Count; otherIndex++)
                {
                    if (footprint.Overlaps(layout.Parcels[otherIndex].Footprint))
                    {
                        error = $"Urban parcels {parcel.StableId} and {layout.Parcels[otherIndex].StableId} overlap.";
                        return false;
                    }
                }
            }

            var occupiedParcels = new HashSet<int>();
            for (int buildingIndex = 0; buildingIndex < layout.Buildings.Count; buildingIndex++)
            {
                UrbanBuildingPlacement building = layout.Buildings[buildingIndex];
                Rect footprint = building.Footprint;

                if (building.SourceParcelIndex < 0 ||
                    building.SourceParcelIndex >= layout.Parcels.Count ||
                    !occupiedParcels.Add(building.SourceParcelIndex) ||
                    !IsFinite(building.Center) || !IsFinite(building.Size) ||
                    building.Size.x <= 0f || building.Size.y <= 0f ||
                    !IsFinite(building.Height) || building.Height <= 0f ||
                    !ContainsRect(layout.Parcels[building.SourceParcelIndex].Footprint, footprint))
                {
                    error = $"Building {buildingIndex} has invalid geometry or parcel ownership.";
                    return false;
                }

                if (!ContainsRect(layout.LocalBounds, footprint))
                {
                    error = $"Building {buildingIndex} exceeds the generated map bounds.";
                    return false;
                }

                for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
                {
                    if (RoadIntersectsRect(
                            layout.Roads[roadIndex],
                            footprint,
                            parameters.SidewalkWidth + parameters.BuildingSetback))
                    {
                        error = $"Building {buildingIndex} intersects road {roadIndex}.";
                        return false;
                    }
                }

                if (!FootprintUsesOnlyGround(surfaceGrid, footprint))
                {
                    error = $"Building {buildingIndex} overlaps a generated road or sidewalk tile.";
                    return false;
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

            var furnitureIds = new HashSet<int>();
            for (int furnitureIndex = 0; furnitureIndex < layout.StreetFurniture.Count; furnitureIndex++)
            {
                UrbanStreetFurniturePlacement furniture = layout.StreetFurniture[furnitureIndex];
                bool supportedKind = furniture.Kind == UrbanStreetFurnitureKind.StreetTree ||
                                     furniture.Kind == UrbanStreetFurnitureKind.StreetLamp ||
                                     furniture.Kind == UrbanStreetFurnitureKind.Bicycle ||
                                     furniture.Kind == UrbanStreetFurnitureKind.TrashBin;
                if (!supportedKind ||
                    furniture.StableId < 0 || !furnitureIds.Add(furniture.StableId) ||
                    furniture.SourceRoadIndex < 0 || furniture.SourceRoadIndex >= layout.Roads.Count ||
                    (furniture.Side != -1 && furniture.Side != 1) ||
                    !IsFinite(furniture.DistanceAlongRoad) || furniture.DistanceAlongRoad < 0f ||
                    !IsFinite(furniture.LateralOffset) || furniture.LateralOffset < 0f ||
                    !IsFinite(furniture.LocalPosition) ||
                    float.IsNaN(furniture.LocalYawDegrees) || float.IsInfinity(furniture.LocalYawDegrees) ||
                    !surfaceGrid.TryLocalToCell(furniture.LocalPosition, out int furnitureX, out int furnitureZ) ||
                    surfaceGrid.GetKind(furnitureX, furnitureZ) != UrbanSurfaceTileKind.Sidewalk)
                {
                    error = $"Street-furniture placement {furnitureIndex} is invalid or not on a sidewalk tile.";
                    return false;
                }

                UrbanRoadSegment sourceRoad = layout.Roads[furniture.SourceRoadIndex];
                if (furniture.DistanceAlongRoad > sourceRoad.Length + GeometryTolerance)
                {
                    error = $"Street-furniture placement {furniture.StableId} exceeds its source road.";
                    return false;
                }

                for (int buildingIndex = 0; buildingIndex < layout.Buildings.Count; buildingIndex++)
                {
                    if (ContainsPoint(layout.Buildings[buildingIndex].Footprint, furniture.LocalPosition))
                    {
                        error = $"Street-furniture placement {furniture.StableId} overlaps building {buildingIndex}.";
                        return false;
                    }
                }
            }

            var candidateIds = new HashSet<int>();
            for (int candidateIndex = 0; candidateIndex < layout.Candidates.Count; candidateIndex++)
            {
                UrbanSpatialCandidate candidate = layout.Candidates[candidateIndex];
                if (candidate.StableId < 0 || !candidateIds.Add(candidate.StableId) ||
                    !IsFinite(candidate.LocalPosition) ||
                    !IsFinite(candidate.LocalDirection) ||
                    candidate.LocalDirection.sqrMagnitude < 0.9f)
                {
                    error = $"Spatial candidate {candidateIndex} is invalid or has a duplicate ID.";
                    return false;
                }

                if (!ContainsPoint(layout.LocalBounds, candidate.LocalPosition))
                {
                    error = $"Spatial candidate {candidate.StableId} exceeds the generated map bounds.";
                    return false;
                }

                switch (candidate.Kind)
                {
                    case UrbanSpatialCandidateKind.Roadside:
                        if (candidate.SourceBuildingIndex != -1)
                        {
                            error = $"Roadside candidate {candidate.StableId} references a building.";
                            return false;
                        }
                        break;

                    case UrbanSpatialCandidateKind.BuildingApproach:
                        if (candidate.SourceBuildingIndex < 0 ||
                            candidate.SourceBuildingIndex >= layout.Buildings.Count)
                        {
                            error = $"Building approach candidate {candidate.StableId} has an invalid building index.";
                            return false;
                        }

                        if (ContainsPoint(
                                layout.Buildings[candidate.SourceBuildingIndex].Footprint,
                                candidate.LocalPosition))
                        {
                            error = $"Building approach candidate {candidate.StableId} is inside its building footprint.";
                            return false;
                        }
                        break;

                    default:
                        error = $"Spatial candidate {candidate.StableId} has an invalid kind.";
                        return false;
                }
            }

            var poiIds = new HashSet<string>(StringComparer.Ordinal);
            int medicalPoiCount = 0;
            for (int poiIndex = 0; poiIndex < layout.Pois.Count; poiIndex++)
            {
                UrbanPoiPlacement poi = layout.Pois[poiIndex];
                if (string.IsNullOrWhiteSpace(poi.StableId) || !poiIds.Add(poi.StableId) ||
                    poi.Kind == UrbanPoiKind.None ||
                    poi.BuildingIndex < 0 || poi.BuildingIndex >= layout.Buildings.Count ||
                    !IsFinite(poi.ContentLocalPosition) ||
                    !IsFinite(poi.ApproachLocalPosition) ||
                    float.IsNaN(poi.LocalYawDegrees) || float.IsInfinity(poi.LocalYawDegrees))
                {
                    error = $"POI {poiIndex} is invalid or has a duplicate stable ID.";
                    return false;
                }

                if (poi.Kind == UrbanPoiKind.Medical)
                {
                    medicalPoiCount++;
                }
                else
                {
                    error = $"POI '{poi.StableId}' has an unsupported kind.";
                    return false;
                }

                Rect footprint = layout.Buildings[poi.BuildingIndex].Footprint;
                if (!ContainsPoint(layout.LocalBounds, poi.ContentLocalPosition) ||
                    !ContainsPoint(layout.LocalBounds, poi.ApproachLocalPosition) ||
                    ContainsPoint(footprint, poi.ContentLocalPosition) ||
                    ContainsPoint(footprint, poi.ApproachLocalPosition) ||
                    (poi.ContentLocalPosition - layout.EntryLocalPosition).sqrMagnitude <
                    UrbanRaidSpawnPrototypeRules.ChestEntryClearance *
                    UrbanRaidSpawnPrototypeRules.ChestEntryClearance ||
                    (poi.ContentLocalPosition - layout.PortalLocalPosition).sqrMagnitude <
                    UrbanRaidSpawnPrototypeRules.ChestPortalClearance *
                    UrbanRaidSpawnPrototypeRules.ChestPortalClearance)
                {
                    error = $"POI '{poi.StableId}' is not safely outside its building footprint.";
                    return false;
                }

                for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
                {
                    if (RoadContainsPoint(layout.Roads[roadIndex], poi.ContentLocalPosition, 0.05f))
                    {
                        error = $"POI '{poi.StableId}' places its content on road {roadIndex}.";
                        return false;
                    }
                }

                bool hasMatchingApproach = false;
                for (int candidateIndex = 0; candidateIndex < layout.Candidates.Count; candidateIndex++)
                {
                    UrbanSpatialCandidate candidate = layout.Candidates[candidateIndex];
                    if (candidate.Kind == UrbanSpatialCandidateKind.BuildingApproach &&
                        candidate.SourceBuildingIndex == poi.BuildingIndex &&
                        (candidate.LocalPosition - poi.ApproachLocalPosition).sqrMagnitude <=
                        GeometryTolerance * GeometryTolerance)
                    {
                        hasMatchingApproach = true;
                        break;
                    }
                }

                if (!hasMatchingApproach)
                {
                    error = $"POI '{poi.StableId}' has no matching building approach candidate.";
                    return false;
                }
            }

            if (medicalPoiCount != 1)
            {
                error = $"Urban layout requires exactly one Medical POI, found {medicalPoiCount}.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryValidateSurfaceGrid(
            UrbanSurfaceGrid grid,
            UrbanTileConnection[] expectedRoadPorts,
            out string error)
        {
            int[] offsetsX = { 0, 1, 1, 1, 0, -1, -1, -1 };
            int[] offsetsZ = { 1, 1, 0, -1, -1, -1, 0, 1 };
            UrbanTileConnection[] flags =
            {
                UrbanTileConnection.N,
                UrbanTileConnection.NE,
                UrbanTileConnection.E,
                UrbanTileConnection.SE,
                UrbanTileConnection.S,
                UrbanTileConnection.SW,
                UrbanTileConnection.W,
                UrbanTileConnection.NW
            };
            UrbanTileConnection[] oppositeFlags =
            {
                UrbanTileConnection.S,
                UrbanTileConnection.SW,
                UrbanTileConnection.W,
                UrbanTileConnection.NW,
                UrbanTileConnection.N,
                UrbanTileConnection.NE,
                UrbanTileConnection.E,
                UrbanTileConnection.SE
            };

            for (int z = 0; z < grid.Height; z++)
            {
                for (int x = 0; x < grid.Width; x++)
                {
                    UrbanSurfaceTileKind source = grid.GetKind(x, z);
                    UrbanTileConnection expectedSurfaceMask =
                        UrbanSurfaceGrid.ComposeCanonicalSurfaceMask(
                            IsCompatibleSurface(grid, x, z + 1, source),
                            IsCompatibleSurface(grid, x + 1, z + 1, source),
                            IsCompatibleSurface(grid, x + 1, z, source),
                            IsCompatibleSurface(grid, x + 1, z - 1, source),
                            IsCompatibleSurface(grid, x, z - 1, source),
                            IsCompatibleSurface(grid, x - 1, z - 1, source),
                            IsCompatibleSurface(grid, x - 1, z, source),
                            IsCompatibleSurface(grid, x - 1, z + 1, source));
                    UrbanTileConnection roadPorts = grid.GetRoadPortMask(x, z);
                    int cellIndex = z * grid.Width + x;
                    if (roadPorts != expectedRoadPorts[cellIndex])
                    {
                        error = $"Surface cell ({x}, {z}) does not match the declared road graph ports.";
                        return false;
                    }

                    if (roadPorts != UrbanTileConnection.None && !UrbanSurfaceGrid.IsRoad(source))
                    {
                        error = $"Surface cell ({x}, {z}) has road ports but is not a road tile.";
                        return false;
                    }

                    for (int direction = 0; direction < offsetsX.Length; direction++)
                    {
                        int neighborX = x + offsetsX[direction];
                        int neighborZ = z + offsetsZ[direction];
                        bool containsNeighbor = grid.ContainsCell(neighborX, neighborZ);
                        if ((roadPorts & flags[direction]) == 0)
                        {
                            continue;
                        }

                        if (!containsNeighbor ||
                            !UrbanSurfaceGrid.IsRoad(grid.GetKind(neighborX, neighborZ)) ||
                            (grid.GetRoadPortMask(neighborX, neighborZ) & oppositeFlags[direction]) == 0)
                        {
                            error = $"Surface cell ({x}, {z}) has a non-reciprocal road port {flags[direction]}.";
                            return false;
                        }
                    }

                    if (grid.GetSurfaceConnectionMask(x, z) != expectedSurfaceMask)
                    {
                        error = $"Surface cell ({x}, {z}) has a stale autotile connection mask.";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        private static bool TryBuildExpectedRoadPorts(
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid grid,
            out UrbanTileConnection[] expectedRoadPorts,
            out string error)
        {
            expectedRoadPorts = new UrbanTileConnection[grid.CellCount];
            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                if (!grid.TryLocalToCell(road.Start, out int startX, out int startZ) ||
                    !grid.TryLocalToCell(road.End, out int endX, out int endZ))
                {
                    error = $"Road {roadIndex} leaves the surface grid.";
                    return false;
                }

                int deltaX = endX - startX;
                int deltaZ = endZ - startZ;
                int absoluteX = Mathf.Abs(deltaX);
                int absoluteZ = Mathf.Abs(deltaZ);
                if (absoluteX != 0 && absoluteZ != 0 && absoluteX != absoluteZ)
                {
                    error = $"Road {roadIndex} cannot be rasterized into eight-direction tile ports.";
                    return false;
                }

                int steps = Mathf.Max(absoluteX, absoluteZ);
                int stepX = Math.Sign(deltaX);
                int stepZ = Math.Sign(deltaZ);
                UrbanTileConnection forward =
                    UrbanSurfaceGrid.ConnectionFromUnitStep(stepX, stepZ);
                UrbanTileConnection backward =
                    UrbanSurfaceGrid.ConnectionFromUnitStep(-stepX, -stepZ);
                int previousX = startX;
                int previousZ = startZ;
                for (int step = 1; step <= steps; step++)
                {
                    int currentX = startX + stepX * step;
                    int currentZ = startZ + stepZ * step;
                    expectedRoadPorts[previousZ * grid.Width + previousX] |= forward;
                    expectedRoadPorts[currentZ * grid.Width + currentX] |= backward;
                    previousX = currentX;
                    previousZ = currentZ;
                }
            }

            error = null;
            return true;
        }

        private static bool TryValidateRoadIntersections(
            UrbanMapLayout layout,
            out string error)
        {
            for (int leftIndex = 0; leftIndex < layout.Roads.Count; leftIndex++)
            {
                UrbanRoadSegment left = layout.Roads[leftIndex];
                for (int rightIndex = leftIndex + 1;
                     rightIndex < layout.Roads.Count;
                     rightIndex++)
                {
                    UrbanRoadSegment right = layout.Roads[rightIndex];
                    if (!SegmentsIntersect(left.Start, left.End, right.Start, right.End))
                    {
                        continue;
                    }

                    int sharedNodeCount = 0;
                    if (left.FromNodeIndex == right.FromNodeIndex ||
                        left.FromNodeIndex == right.ToNodeIndex)
                    {
                        sharedNodeCount++;
                    }
                    if (left.ToNodeIndex == right.FromNodeIndex ||
                        left.ToNodeIndex == right.ToNodeIndex)
                    {
                        sharedNodeCount++;
                    }

                    if (sharedNodeCount != 1 ||
                        (AreCollinear(left.Start, left.End, right.Start) &&
                         AreCollinear(left.Start, left.End, right.End) &&
                         HasPositiveCollinearOverlap(left.Start, left.End, right.Start, right.End)))
                    {
                        error =
                            $"Roads {leftIndex} ({left.FromNodeIndex}->{left.ToNodeIndex}, " +
                            $"{left.Start}->{left.End}) and {rightIndex} " +
                            $"({right.FromNodeIndex}->{right.ToNodeIndex}, {right.Start}->{right.End}) " +
                            $"intersect anywhere other than one shared declared node " +
                            $"(shared nodes={sharedNodeCount}).";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        private static bool SegmentsIntersect(
            Vector2 leftStart,
            Vector2 leftEnd,
            Vector2 rightStart,
            Vector2 rightEnd)
        {
            float leftToRightStart = Cross(leftStart, leftEnd, rightStart);
            float leftToRightEnd = Cross(leftStart, leftEnd, rightEnd);
            float rightToLeftStart = Cross(rightStart, rightEnd, leftStart);
            float rightToLeftEnd = Cross(rightStart, rightEnd, leftEnd);

            if (((leftToRightStart > GeometryTolerance && leftToRightEnd < -GeometryTolerance) ||
                 (leftToRightStart < -GeometryTolerance && leftToRightEnd > GeometryTolerance)) &&
                ((rightToLeftStart > GeometryTolerance && rightToLeftEnd < -GeometryTolerance) ||
                 (rightToLeftStart < -GeometryTolerance && rightToLeftEnd > GeometryTolerance)))
            {
                return true;
            }

            return Mathf.Abs(leftToRightStart) <= GeometryTolerance &&
                   PointOnSegment(leftStart, leftEnd, rightStart) ||
                   Mathf.Abs(leftToRightEnd) <= GeometryTolerance &&
                   PointOnSegment(leftStart, leftEnd, rightEnd) ||
                   Mathf.Abs(rightToLeftStart) <= GeometryTolerance &&
                   PointOnSegment(rightStart, rightEnd, leftStart) ||
                   Mathf.Abs(rightToLeftEnd) <= GeometryTolerance &&
                   PointOnSegment(rightStart, rightEnd, leftEnd);
        }

        private static bool PointOnSegment(Vector2 start, Vector2 end, Vector2 point)
        {
            return point.x >= Mathf.Min(start.x, end.x) - GeometryTolerance &&
                   point.x <= Mathf.Max(start.x, end.x) + GeometryTolerance &&
                   point.y >= Mathf.Min(start.y, end.y) - GeometryTolerance &&
                   point.y <= Mathf.Max(start.y, end.y) + GeometryTolerance;
        }

        private static bool AreCollinear(Vector2 start, Vector2 end, Vector2 point)
        {
            return Mathf.Abs(Cross(start, end, point)) <= GeometryTolerance;
        }

        private static bool HasPositiveCollinearOverlap(
            Vector2 leftStart,
            Vector2 leftEnd,
            Vector2 rightStart,
            Vector2 rightEnd)
        {
            bool useX = Mathf.Abs(leftEnd.x - leftStart.x) >=
                        Mathf.Abs(leftEnd.y - leftStart.y);
            float leftMinimum = useX
                ? Mathf.Min(leftStart.x, leftEnd.x)
                : Mathf.Min(leftStart.y, leftEnd.y);
            float leftMaximum = useX
                ? Mathf.Max(leftStart.x, leftEnd.x)
                : Mathf.Max(leftStart.y, leftEnd.y);
            float rightMinimum = useX
                ? Mathf.Min(rightStart.x, rightEnd.x)
                : Mathf.Min(rightStart.y, rightEnd.y);
            float rightMaximum = useX
                ? Mathf.Max(rightStart.x, rightEnd.x)
                : Mathf.Max(rightStart.y, rightEnd.y);
            float overlap = Mathf.Min(leftMaximum, rightMaximum) -
                            Mathf.Max(leftMinimum, rightMinimum);
            return overlap > GeometryTolerance;
        }

        private static float Cross(Vector2 start, Vector2 end, Vector2 point)
        {
            Vector2 segment = end - start;
            Vector2 offset = point - start;
            return segment.x * offset.y - segment.y * offset.x;
        }

        private static bool IsCompatibleSurface(
            UrbanSurfaceGrid grid,
            int x,
            int z,
            UrbanSurfaceTileKind source)
        {
            return grid.ContainsCell(x, z) &&
                   UrbanSurfaceGrid.AreAutotileCompatible(source, grid.GetKind(x, z));
        }

        private static bool FootprintUsesOnlyGround(UrbanSurfaceGrid grid, Rect footprint)
        {
            if (!grid.TryLocalToCell(new Vector2(footprint.xMin, footprint.yMin), out int minX, out int minZ) ||
                !grid.TryLocalToCell(
                    new Vector2(
                        footprint.xMax - GeometryTolerance,
                        footprint.yMax - GeometryTolerance),
                    out int maxX,
                    out int maxZ))
            {
                return false;
            }

            for (int z = minZ; z <= maxZ; z++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    Vector2 center = grid.GetCellCenter(x, z);
                    if (ContainsPoint(footprint, center) &&
                        grid.GetKind(x, z) != UrbanSurfaceTileKind.Ground)
                    {
                        return false;
                    }
                }
            }

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

            AddInt(layout.SurfaceGrid.Width);
            AddInt(layout.SurfaceGrid.Height);
            AddFloat(layout.SurfaceGrid.TileSize);
            for (int z = 0; z < layout.SurfaceGrid.Height; z++)
            {
                for (int x = 0; x < layout.SurfaceGrid.Width; x++)
                {
                    AddInt((int)layout.SurfaceGrid.GetKind(x, z));
                    AddInt((int)layout.SurfaceGrid.GetSurfaceConnectionMask(x, z));
                    AddInt((int)layout.SurfaceGrid.GetRoadPortMask(x, z));
                }
            }

            AddInt(layout.Parcels.Count);
            for (int index = 0; index < layout.Parcels.Count; index++)
            {
                UrbanParcelPlacement parcel = layout.Parcels[index];
                AddInt(parcel.StableId);
                AddInt(parcel.SourceRoadIndex);
                AddFloat(parcel.DistanceAlongRoad);
                AddInt(parcel.Side);
                AddFloat(parcel.Center.x);
                AddFloat(parcel.Center.y);
                AddFloat(parcel.Size.x);
                AddFloat(parcel.Size.y);
                AddFloat(parcel.FacadeDirection.x);
                AddFloat(parcel.FacadeDirection.y);
            }

            AddInt(layout.Buildings.Count);
            for (int index = 0; index < layout.Buildings.Count; index++)
            {
                UrbanBuildingPlacement building = layout.Buildings[index];
                AddInt(building.SourceParcelIndex);
                AddFloat(building.Center.x);
                AddFloat(building.Center.y);
                AddFloat(building.Size.x);
                AddFloat(building.Size.y);
                AddFloat(building.Height);
                AddInt(building.PaletteIndex);
            }

            AddInt(layout.StreetFurniture.Count);
            for (int index = 0; index < layout.StreetFurniture.Count; index++)
            {
                UrbanStreetFurniturePlacement furniture = layout.StreetFurniture[index];
                AddInt(furniture.StableId);
                AddInt((int)furniture.Kind);
                AddInt(furniture.SourceRoadIndex);
                AddFloat(furniture.DistanceAlongRoad);
                AddInt(furniture.Side);
                AddFloat(furniture.LateralOffset);
                AddFloat(furniture.LocalPosition.x);
                AddFloat(furniture.LocalPosition.y);
                AddFloat(furniture.LocalYawDegrees);
            }

            AddInt(layout.Pois.Count);
            for (int index = 0; index < layout.Pois.Count; index++)
            {
                UrbanPoiPlacement poi = layout.Pois[index];
                AddString(poi.StableId);
                AddInt((int)poi.Kind);
                AddInt(poi.BuildingIndex);
                AddFloat(poi.ContentLocalPosition.x);
                AddFloat(poi.ContentLocalPosition.y);
                AddFloat(poi.ApproachLocalPosition.x);
                AddFloat(poi.ApproachLocalPosition.y);
                AddFloat(poi.LocalYawDegrees);
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

        internal static bool RoadContainsPoint(
            UrbanRoadSegment road,
            Vector2 point,
            float extraClearance)
        {
            Vector2 segment = road.End - road.Start;
            float denominator = segment.sqrMagnitude;
            float fraction = denominator <= 0.0001f
                ? 0f
                : Mathf.Clamp01(Vector2.Dot(point - road.Start, segment) / denominator);
            Vector2 closest = Vector2.Lerp(road.Start, road.End, fraction);
            float radius = road.Width * 0.5f + Mathf.Max(0f, extraClearance);
            return (point - closest).sqrMagnitude <= radius * radius;
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

        private static bool ContainsPoint(Rect rect, Vector2 point)
        {
            return point.x >= rect.xMin - GeometryTolerance &&
                   point.x <= rect.xMax + GeometryTolerance &&
                   point.y >= rect.yMin - GeometryTolerance &&
                   point.y <= rect.yMax + GeometryTolerance;
        }

        private static bool IsFinite(Vector2 value)
        {
            return !float.IsNaN(value.x) && !float.IsInfinity(value.x) &&
                   !float.IsNaN(value.y) && !float.IsInfinity(value.y);
        }

        private static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
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

    }
}
