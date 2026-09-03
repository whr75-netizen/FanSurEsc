using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public static class UrbanMapLayoutPlanner
    {
        public const int GeneratorVersion = 6;
        public const int SpawnManifestVersion = 3;

        private static readonly float[] SpawnCandidateFractions = { 0.2f, 0.35f, 0.5f, 0.65f, 0.8f };
        private const float PoiContentFacadeOffset = 0.75f;
        private const float PoiApproachOffset = 0.9f;
        private const string MedicalPoiStableId = "core:urban/medical_01";

        private struct EdgeDraft
        {
            public int From;
            public int To;
            public bool IsPrimary;
            public bool IsActive;
            public float Width;
        }

        private readonly struct ParcelDraft
        {
            public ParcelDraft(
                int sourceRoadIndex,
                float distanceAlongRoad,
                int side,
                Vector2 center,
                Vector2 size,
                Vector2 facadeDirection)
            {
                SourceRoadIndex = sourceRoadIndex;
                DistanceAlongRoad = distanceAlongRoad;
                Side = side;
                Center = center;
                Size = size;
                FacadeDirection = facadeDirection;
            }

            public int SourceRoadIndex { get; }
            public float DistanceAlongRoad { get; }
            public int Side { get; }
            public Vector2 Center { get; }
            public Vector2 Size { get; }
            public Vector2 FacadeDirection { get; }
            public Rect Footprint => new Rect(Center - Size * 0.5f, Size);
        }

        private sealed class DisjointSet
        {
            private readonly int[] parents;
            private readonly byte[] ranks;

            public DisjointSet(int count)
            {
                parents = new int[count];
                ranks = new byte[count];
                for (int index = 0; index < count; index++)
                {
                    parents[index] = index;
                }
            }

            public bool Union(int left, int right)
            {
                int leftRoot = Find(left);
                int rightRoot = Find(right);
                if (leftRoot == rightRoot)
                {
                    return false;
                }

                if (ranks[leftRoot] < ranks[rightRoot])
                {
                    parents[leftRoot] = rightRoot;
                }
                else if (ranks[leftRoot] > ranks[rightRoot])
                {
                    parents[rightRoot] = leftRoot;
                }
                else
                {
                    parents[rightRoot] = leftRoot;
                    ranks[leftRoot]++;
                }

                return true;
            }

            private int Find(int value)
            {
                int root = value;
                while (parents[root] != root)
                {
                    root = parents[root];
                }

                while (parents[value] != value)
                {
                    int parent = parents[value];
                    parents[value] = root;
                    value = parent;
                }

                return root;
            }
        }

        private struct StableRandom
        {
            private uint state;

            public StableRandom(uint seed)
            {
                state = seed == 0 ? 0x6D2B79F5u : seed;
            }

            public uint NextUInt()
            {
                uint value = state;
                value ^= value << 13;
                value ^= value >> 17;
                value ^= value << 5;
                state = value;
                return value;
            }

            public float NextFloat()
            {
                return (NextUInt() & 0x00FFFFFFu) / 16777216f;
            }

            public float Range(float minimum, float maximum)
            {
                return Mathf.Lerp(minimum, maximum, NextFloat());
            }

            public int Range(int minimumInclusive, int maximumExclusive)
            {
                if (maximumExclusive <= minimumInclusive)
                {
                    return minimumInclusive;
                }

                uint range = (uint)(maximumExclusive - minimumInclusive);
                return minimumInclusive + (int)(NextUInt() % range);
            }
        }

        private readonly struct SpawnCandidate
        {
            public SpawnCandidate(int candidateId, Vector2 localPosition, Vector2 roadDirection)
            {
                CandidateId = candidateId;
                LocalPosition = localPosition;
                RoadDirection = roadDirection;
            }

            public int CandidateId { get; }
            public Vector2 LocalPosition { get; }
            public Vector2 RoadDirection { get; }
        }

        private readonly struct SelectedSpawn
        {
            public SelectedSpawn(UrbanRaidSpawnRequest request, UrbanRaidSpawnPlacement placement)
            {
                Request = request;
                Placement = placement;
            }

            public UrbanRaidSpawnRequest Request { get; }
            public UrbanRaidSpawnPlacement Placement { get; }
        }

        public static UrbanMapLayout Generate(
            int seed,
            Vector2 entryWorldPosition,
            IReadOnlyList<Vector2> protectedWorldPositions,
            UrbanMapGenerationParameters parameters)
        {
            if (!parameters.TryValidate(out string settingsError))
            {
                throw new System.ArgumentException(settingsError, nameof(parameters));
            }

            var roadRandom = new StableRandom(DeriveSeed(seed, 0x63D83595u));
            var buildingRandom = new StableRandom(DeriveSeed(seed, 0xC2B2AE35u));

            int blocksX = parameters.BlocksPerAxis;
            int blocksZ = parameters.BlocksPerAxis;
            const float cityRotation = 0f;
            float halfMapSize = parameters.MapWorldSize * 0.5f;
            Rect localBounds = new Rect(
                -halfMapSize,
                -halfMapSize,
                parameters.MapWorldSize,
                parameters.MapWorldSize);

            float[] baseX = BuildAxisPositions(parameters, localBounds.xMin);
            float[] baseZ = BuildAxisPositions(parameters, localBounds.yMin);
            int nodeColumns = blocksX + 1;
            int nodeRows = blocksZ + 1;
            var nodes = BuildNodes(baseX, baseZ);

            int primaryRow = roadRandom.Range(1, Mathf.Max(2, nodeRows - 1));
            int primaryColumn = roadRandom.Range(1, Mathf.Max(2, nodeColumns - 1));
            List<EdgeDraft> edgeDrafts = BuildRoadNetwork(
                nodeColumns,
                nodeRows,
                primaryColumn,
                primaryRow,
                nodes.Count,
                parameters,
                ref roadRandom);
            List<UrbanRoadSegment> roads = CreateRoadSegments(edgeDrafts, nodes);

            Vector2 entryLocalPosition = nodes[0];
            // The current graybox slice keeps the one authored extraction portal on
            // the first road junction so combat, loot, and extraction can be tested
            // without crossing the whole unfinished city.
            int portalNodeIndex = 1;
            Vector2 portalLocalPosition = nodes[portalNodeIndex];
            Vector2 portalApproach = FindPortalApproach(edgeDrafts, nodes, portalNodeIndex, parameters.AnchorClearance * 0.65f);

            List<Vector2> protectedLocalPoints = ConvertProtectedPointsToLocal(
                protectedWorldPositions,
                entryWorldPosition,
                entryLocalPosition,
                cityRotation);

            UrbanSurfaceGrid surfaceGrid = BuildSurfaceGrid(localBounds, roads, parameters);

            List<UrbanParcelPlacement> parcels = BuildRoadFrontageParcels(
                localBounds,
                roads,
                surfaceGrid,
                parameters,
                ref buildingRandom);

            List<UrbanBuildingPlacement> buildings = BuildBuildings(
                parcels,
                roads,
                surfaceGrid,
                entryLocalPosition,
                portalLocalPosition,
                protectedLocalPoints,
                parameters,
                ref buildingRandom);

            List<UrbanSpatialCandidate> candidates = BuildSpatialCandidates(
                roads,
                parcels,
                buildings);
            List<UrbanPoiPlacement> pois = BuildPois(
                candidates,
                roads,
                buildings,
                localBounds,
                entryLocalPosition,
                portalLocalPosition);
            List<UrbanStreetFurniturePlacement> streetFurniture = BuildStreetFurniture(
                roads,
                surfaceGrid,
                buildings,
                candidates,
                entryLocalPosition,
                portalLocalPosition,
                protectedLocalPoints,
                parameters,
                seed);

            var layout = new UrbanMapLayout(
                GeneratorVersion,
                seed,
                blocksX,
                blocksZ,
                cityRotation,
                localBounds,
                entryLocalPosition,
                portalLocalPosition,
                portalApproach,
                nodes,
                roads,
                surfaceGrid,
                parcels,
                buildings,
                streetFurniture,
                protectedLocalPoints,
                candidates,
                pois);

            if (!UrbanMapLayoutValidator.TryValidate(layout, parameters, out string layoutError))
            {
                throw new System.InvalidOperationException($"Urban map generation failed for seed {seed}: {layoutError}");
            }

            return layout;
        }

        /// <summary>
        /// Builds a pure deterministic placement manifest from the map layout and stable IDs.
        /// NavMesh is intentionally not consulted here; runtime reachability is a separate
        /// fail-closed validation so Resume never changes entity count by silently rerolling.
        /// </summary>
        public static bool TryCreateRaidSpawnManifest(
            UrbanMapLayout layout,
            IReadOnlyList<UrbanRaidSpawnRequest> requests,
            out UrbanRaidSpawnManifest manifest,
            out string error)
        {
            manifest = null;
            if (layout == null || layout.Roads == null || layout.Roads.Count == 0)
            {
                error = "Cannot create a raid spawn manifest without a generated road layout.";
                return false;
            }

            if (requests == null || requests.Count == 0)
            {
                error = "Cannot create an empty raid spawn manifest.";
                return false;
            }

            var sortedRequests = new List<UrbanRaidSpawnRequest>(requests.Count);
            var stableIds = new HashSet<string>(System.StringComparer.Ordinal);
            for (int index = 0; index < requests.Count; index++)
            {
                UrbanRaidSpawnRequest request = requests[index];
                if (!request.TryValidate(out error) || !stableIds.Add(request.StableId))
                {
                    if (error == null)
                    {
                        error = $"Raid spawn requests contain duplicate stable ID '{request.StableId}'.";
                    }
                    return false;
                }

                sortedRequests.Add(request);
            }

            sortedRequests.Sort((left, right) =>
            {
                int poiComparison = (right.RequiredPoiKind != UrbanPoiKind.None)
                    .CompareTo(left.RequiredPoiKind != UrbanPoiKind.None);
                if (poiComparison != 0)
                {
                    return poiComparison;
                }

                float leftMaximum = left.MaximumEntryDistance > 0f
                    ? left.MaximumEntryDistance
                    : float.PositiveInfinity;
                float rightMaximum = right.MaximumEntryDistance > 0f
                    ? right.MaximumEntryDistance
                    : float.PositiveInfinity;
                int distanceComparison = leftMaximum.CompareTo(rightMaximum);
                return distanceComparison != 0
                    ? distanceComparison
                    : System.StringComparer.Ordinal.Compare(left.StableId, right.StableId);
            });

            List<SpawnCandidate> candidates = BuildSpawnCandidates(layout.Candidates);
            int roadRequestCount = 0;
            for (int index = 0; index < sortedRequests.Count; index++)
            {
                if (sortedRequests[index].RequiredPoiKind == UrbanPoiKind.None)
                {
                    roadRequestCount++;
                }
            }

            if (candidates.Count < roadRequestCount)
            {
                error =
                    $"Urban map seed {layout.Seed} has only {candidates.Count} road spawn candidates " +
                    $"for {roadRequestCount} road-bound entities.";
                return false;
            }

            var selected = new List<SelectedSpawn>(sortedRequests.Count);
            var placements = new List<UrbanRaidSpawnPlacement>(sortedRequests.Count);
            for (int requestIndex = 0; requestIndex < sortedRequests.Count; requestIndex++)
            {
                UrbanRaidSpawnRequest request = sortedRequests[requestIndex];
                if (request.RequiredPoiKind != UrbanPoiKind.None)
                {
                    if (!layout.TryGetPoi(request.RequiredPoiKind, out UrbanPoiPlacement poi))
                    {
                        error =
                            $"Urban map seed {layout.Seed} has no {request.RequiredPoiKind} POI " +
                            $"for raid entity '{request.StableId}'.";
                        return false;
                    }

                    if (!CanUseSpawnPosition(layout, request, poi.ContentLocalPosition, selected))
                    {
                        error =
                            $"Urban map seed {layout.Seed} cannot safely bind raid entity " +
                            $"'{request.StableId}' to POI '{poi.StableId}'.";
                        return false;
                    }

                    var poiPlacement = new UrbanRaidSpawnPlacement(
                        request.StableId,
                        request.Kind,
                        poi.ContentLocalPosition,
                        poi.LocalYawDegrees,
                        poi.ApproachLocalPosition);
                    selected.Add(new SelectedSpawn(request, poiPlacement));
                    placements.Add(poiPlacement);
                    continue;
                }

                uint requestHash = StableStringHash(request.StableId);
                uint selectionKey = DeriveSeed(
                    layout.Seed,
                    requestHash ^ ((uint)request.Kind + 1u) * 0x9E3779B9u);
                int startIndex = (int)(selectionKey % (uint)candidates.Count);
                int scanDirection = (selectionKey & 0x80000000u) == 0u ? 1 : -1;
                bool found = false;

                for (int scanOffset = 0; scanOffset < candidates.Count; scanOffset++)
                {
                    int candidateIndex = PositiveModulo(
                        startIndex + scanOffset * scanDirection,
                        candidates.Count);
                    SpawnCandidate candidate = candidates[candidateIndex];
                    bool reverseFacing = ((selectionKey ^ (uint)candidate.CandidateId * 0x85EBCA6Bu) & 1u) != 0u;
                    Vector2 facingDirection = reverseFacing
                        ? -candidate.RoadDirection
                        : candidate.RoadDirection;
                    Vector2 lateralDirection = new Vector2(-facingDirection.y, facingDirection.x);
                    if (((selectionKey >> 1) & 1u) != 0u)
                    {
                        lateralDirection = -lateralDirection;
                    }

                    Vector2 placementPosition =
                        candidate.LocalPosition + lateralDirection * request.ApproachDistance;
                    if (!CanUseSpawnPosition(layout, request, placementPosition, selected))
                    {
                        continue;
                    }

                    float yaw = Mathf.Atan2(facingDirection.x, facingDirection.y) * Mathf.Rad2Deg;
                    var placement = new UrbanRaidSpawnPlacement(
                        request.StableId,
                        request.Kind,
                        placementPosition,
                        yaw,
                        candidate.LocalPosition);
                    selected.Add(new SelectedSpawn(request, placement));
                    placements.Add(placement);
                    found = true;
                    break;
                }

                if (!found)
                {
                    error =
                        $"Urban map seed {layout.Seed} has no safe road position for raid entity " +
                        $"'{request.StableId}'. The seed is rejected instead of rerolled.";
                    return false;
                }
            }

            manifest = new UrbanRaidSpawnManifest(
                SpawnManifestVersion,
                layout.Seed,
                placements);
            error = null;
            return true;
        }

        private static List<SpawnCandidate> BuildSpawnCandidates(
            IReadOnlyList<UrbanSpatialCandidate> spatialCandidates)
        {
            var candidates = new List<SpawnCandidate>();
            for (int index = 0; index < spatialCandidates.Count; index++)
            {
                UrbanSpatialCandidate candidate = spatialCandidates[index];
                if (candidate.Kind != UrbanSpatialCandidateKind.Roadside)
                {
                    continue;
                }

                candidates.Add(new SpawnCandidate(
                    candidate.StableId,
                    candidate.LocalPosition,
                    candidate.LocalDirection));
            }

            return candidates;
        }

        private static List<UrbanSpatialCandidate> BuildSpatialCandidates(
            IReadOnlyList<UrbanRoadSegment> roads,
            IReadOnlyList<UrbanParcelPlacement> parcels,
            IReadOnlyList<UrbanBuildingPlacement> buildings)
        {
            var candidates = new List<UrbanSpatialCandidate>(
                roads.Count * SpawnCandidateFractions.Length + buildings.Count);
            int stableId = 0;

            // Preserve the original road-index/fraction-index order and numeric IDs.
            // Existing non-POI spawn manifests depend on this exact sequence.
            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                Vector2 delta = road.End - road.Start;
                if (delta.sqrMagnitude <= 0.0001f)
                {
                    continue;
                }

                Vector2 direction = delta.normalized;
                for (int fractionIndex = 0; fractionIndex < SpawnCandidateFractions.Length; fractionIndex++)
                {
                    float fraction = SpawnCandidateFractions[fractionIndex];
                    candidates.Add(new UrbanSpatialCandidate(
                        stableId++,
                        UrbanSpatialCandidateKind.Roadside,
                        Vector2.Lerp(road.Start, road.End, fraction),
                        direction,
                        sourceBuildingIndex: -1));
                }
            }

            for (int buildingIndex = 0; buildingIndex < buildings.Count; buildingIndex++)
            {
                UrbanBuildingPlacement building = buildings[buildingIndex];
                UrbanParcelPlacement parcel = parcels[building.SourceParcelIndex];
                Vector2 outward = parcel.FacadeDirection;
                float facadeExtent = Mathf.Abs(outward.x) * building.Size.x * 0.5f +
                                     Mathf.Abs(outward.y) * building.Size.y * 0.5f;
                Vector2 facadePoint = building.Center + outward * facadeExtent;
                Vector2 contentPosition = facadePoint + outward * PoiContentFacadeOffset;
                Vector2 approachPosition = contentPosition + outward * PoiApproachOffset;
                candidates.Add(new UrbanSpatialCandidate(
                    stableId++,
                    UrbanSpatialCandidateKind.BuildingApproach,
                    approachPosition,
                    outward,
                    buildingIndex));
            }

            return candidates;
        }

        private static List<UrbanPoiPlacement> BuildPois(
            IReadOnlyList<UrbanSpatialCandidate> candidates,
            IReadOnlyList<UrbanRoadSegment> roads,
            IReadOnlyList<UrbanBuildingPlacement> buildings,
            Rect localBounds,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition)
        {
            UrbanSpatialCandidate selected = default;
            Vector2 selectedContentPosition = default;
            float selectedDistanceSquared = float.PositiveInfinity;
            bool found = false;

            for (int index = 0; index < candidates.Count; index++)
            {
                UrbanSpatialCandidate candidate = candidates[index];
                if (candidate.Kind != UrbanSpatialCandidateKind.BuildingApproach ||
                    candidate.SourceBuildingIndex < 0 ||
                    candidate.SourceBuildingIndex >= buildings.Count)
                {
                    continue;
                }

                Vector2 contentPosition =
                    candidate.LocalPosition - candidate.LocalDirection * PoiApproachOffset;
                if (!ContainsPoint(localBounds, contentPosition) ||
                    !ContainsPoint(localBounds, candidate.LocalPosition) ||
                    ContainsPoint(buildings[candidate.SourceBuildingIndex].Footprint, contentPosition) ||
                    ContainsPoint(buildings[candidate.SourceBuildingIndex].Footprint, candidate.LocalPosition) ||
                    IsOnAnyRoad(contentPosition, roads) ||
                    IsInsideAnyOtherBuilding(
                        contentPosition,
                        candidate.LocalPosition,
                        candidate.SourceBuildingIndex,
                        buildings) ||
                    (contentPosition - entryLocalPosition).sqrMagnitude <
                    UrbanRaidSpawnPrototypeRules.ChestEntryClearance *
                    UrbanRaidSpawnPrototypeRules.ChestEntryClearance ||
                    (contentPosition - portalLocalPosition).sqrMagnitude <
                    UrbanRaidSpawnPrototypeRules.ChestPortalClearance *
                    UrbanRaidSpawnPrototypeRules.ChestPortalClearance)
                {
                    continue;
                }

                float distanceSquared = (candidate.LocalPosition - entryLocalPosition).sqrMagnitude;
                if (found && distanceSquared > selectedDistanceSquared + 0.0001f)
                {
                    continue;
                }

                if (found && Mathf.Abs(distanceSquared - selectedDistanceSquared) <= 0.0001f &&
                    candidate.StableId >= selected.StableId)
                {
                    continue;
                }

                selected = candidate;
                selectedContentPosition = contentPosition;
                selectedDistanceSquared = distanceSquared;
                found = true;
            }

            if (!found)
            {
                throw new System.InvalidOperationException(
                    "Urban map generation produced no safe building approach for the Medical POI.");
            }

            float yaw = Mathf.Atan2(
                selected.LocalDirection.x,
                selected.LocalDirection.y) * Mathf.Rad2Deg;
            return new List<UrbanPoiPlacement>
            {
                new UrbanPoiPlacement(
                    MedicalPoiStableId,
                    UrbanPoiKind.Medical,
                    selected.SourceBuildingIndex,
                    selectedContentPosition,
                    selected.LocalPosition,
                    yaw)
            };
        }

        private static List<UrbanStreetFurniturePlacement> BuildStreetFurniture(
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid surfaceGrid,
            IReadOnlyList<UrbanBuildingPlacement> buildings,
            IReadOnlyList<UrbanSpatialCandidate> spatialCandidates,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters,
            int seed)
        {
            var placements = new List<UrbanStreetFurniturePlacement>();
            int stableId = 0;

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                Vector2 segment = road.End - road.Start;
                if (segment.sqrMagnitude <= 0.0001f)
                {
                    continue;
                }

                float length = segment.magnitude;
                Vector2 direction = segment / length;
                Vector2 right = new Vector2(direction.y, -direction.x);
                float lateralOffset = road.Width * 0.5f + parameters.SidewalkWidth * 0.55f;
                float endpointClearance = parameters.JunctionFurnitureClearanceTiles *
                                          parameters.TileWorldSize;

                AddFurnitureSeries(
                    UrbanStreetFurnitureKind.StreetTree,
                    roadIndex,
                    road,
                    direction,
                    right,
                    length,
                    parameters.StreetTreeSpacingTiles * parameters.TileWorldSize,
                    endpointClearance,
                    lateralOffset,
                    chance: 1f,
                    seed,
                    0x2C1B3C6Du,
                    surfaceGrid,
                    buildings,
                    spatialCandidates,
                    entryLocalPosition,
                    portalLocalPosition,
                    protectedLocalPoints,
                    parameters,
                    placements,
                    ref stableId);

                AddFurnitureSeries(
                    UrbanStreetFurnitureKind.StreetLamp,
                    roadIndex,
                    road,
                    direction,
                    right,
                    length,
                    parameters.StreetLampSpacingTiles * parameters.TileWorldSize,
                    endpointClearance,
                    lateralOffset,
                    chance: 1f,
                    seed,
                    0x9E3779B9u,
                    surfaceGrid,
                    buildings,
                    spatialCandidates,
                    entryLocalPosition,
                    portalLocalPosition,
                    protectedLocalPoints,
                    parameters,
                    placements,
                    ref stableId);

                AddFurnitureSeries(
                    UrbanStreetFurnitureKind.Bicycle,
                    roadIndex,
                    road,
                    direction,
                    right,
                    length,
                    parameters.ClutterSpacingTiles * parameters.TileWorldSize,
                    endpointClearance,
                    lateralOffset,
                    parameters.ClutterChance,
                    seed,
                    0x85EBCA6Bu,
                    surfaceGrid,
                    buildings,
                    spatialCandidates,
                    entryLocalPosition,
                    portalLocalPosition,
                    protectedLocalPoints,
                    parameters,
                    placements,
                    ref stableId);
            }

            return placements;
        }

        private static void AddFurnitureSeries(
            UrbanStreetFurnitureKind requestedKind,
            int roadIndex,
            UrbanRoadSegment road,
            Vector2 roadDirection,
            Vector2 roadRight,
            float roadLength,
            float spacing,
            float endpointClearance,
            float requestedLateralOffset,
            float chance,
            int seed,
            uint stream,
            UrbanSurfaceGrid surfaceGrid,
            IReadOnlyList<UrbanBuildingPlacement> buildings,
            IReadOnlyList<UrbanSpatialCandidate> spatialCandidates,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters,
            List<UrbanStreetFurniturePlacement> placements,
            ref int stableId)
        {
            if (roadLength <= endpointClearance * 2f || spacing <= 0f)
            {
                return;
            }

            uint roadStream = unchecked(stream + (uint)roadIndex * 0x27D4EB2Du);
            var random = new StableRandom(DeriveSeed(seed, roadStream));
            float phase = requestedKind == UrbanStreetFurnitureKind.StreetTree
                ? spacing * 0.25f
                : requestedKind == UrbanStreetFurnitureKind.StreetLamp
                    ? spacing * 0.55f
                    : random.Range(0f, spacing);
            int slotIndex = 0;
            for (float distance = endpointClearance + phase;
                 distance < roadLength - endpointClearance;
                 distance += spacing, slotIndex++)
            {
                if (random.NextFloat() > chance)
                {
                    continue;
                }

                int side = ((roadIndex + slotIndex + (int)requestedKind) & 1) == 0 ? 1 : -1;
                Vector2 roadPoint = road.Start + roadDirection * distance;
                Vector2 desired = roadPoint + roadRight * (requestedLateralOffset * side);
                if (!TryFindSidewalkCell(
                        surfaceGrid,
                        desired,
                        roadPoint,
                        roadRight,
                        side,
                        parameters.SidewalkWidthTiles + 1,
                        out Vector2 localPosition) ||
                    !CanPlaceStreetFurniture(
                        localPosition,
                        surfaceGrid,
                        buildings,
                        spatialCandidates,
                        entryLocalPosition,
                        portalLocalPosition,
                        protectedLocalPoints,
                        parameters,
                        placements))
                {
                    continue;
                }

                UrbanStreetFurnitureKind kind = requestedKind;
                if (requestedKind == UrbanStreetFurnitureKind.Bicycle && random.NextFloat() >= 0.5f)
                {
                    kind = UrbanStreetFurnitureKind.TrashBin;
                }

                float yaw = Mathf.Atan2(roadDirection.x, roadDirection.y) * Mathf.Rad2Deg;
                float actualLateralOffset = Mathf.Abs(Vector2.Dot(localPosition - roadPoint, roadRight));
                placements.Add(new UrbanStreetFurniturePlacement(
                    stableId++,
                    kind,
                    roadIndex,
                    distance,
                    side,
                    actualLateralOffset,
                    localPosition,
                    yaw));
            }
        }

        private static bool TryFindSidewalkCell(
            UrbanSurfaceGrid surfaceGrid,
            Vector2 desired,
            Vector2 roadPoint,
            Vector2 roadRight,
            int side,
            int searchRadius,
            out Vector2 localPosition)
        {
            localPosition = default;
            if (!surfaceGrid.TryLocalToCell(desired, out int centerX, out int centerZ))
            {
                return false;
            }

            float bestDistanceSquared = float.PositiveInfinity;
            bool found = false;
            for (int offsetZ = -searchRadius; offsetZ <= searchRadius; offsetZ++)
            {
                for (int offsetX = -searchRadius; offsetX <= searchRadius; offsetX++)
                {
                    int x = centerX + offsetX;
                    int z = centerZ + offsetZ;
                    if (!surfaceGrid.ContainsCell(x, z) ||
                        surfaceGrid.GetKind(x, z) != UrbanSurfaceTileKind.Sidewalk)
                    {
                        continue;
                    }

                    Vector2 candidate = surfaceGrid.GetCellCenter(x, z);
                    if (Vector2.Dot(candidate - roadPoint, roadRight) * side <= 0f)
                    {
                        continue;
                    }

                    float distanceSquared = (candidate - desired).sqrMagnitude;
                    if (distanceSquared >= bestDistanceSquared)
                    {
                        continue;
                    }

                    bestDistanceSquared = distanceSquared;
                    localPosition = candidate;
                    found = true;
                }
            }

            return found;
        }

        private static bool CanPlaceStreetFurniture(
            Vector2 localPosition,
            UrbanSurfaceGrid surfaceGrid,
            IReadOnlyList<UrbanBuildingPlacement> buildings,
            IReadOnlyList<UrbanSpatialCandidate> spatialCandidates,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters,
            IReadOnlyList<UrbanStreetFurniturePlacement> existing)
        {
            if (!surfaceGrid.TryLocalToCell(localPosition, out int x, out int z) ||
                surfaceGrid.GetKind(x, z) != UrbanSurfaceTileKind.Sidewalk)
            {
                return false;
            }

            float anchorClearance = Mathf.Max(parameters.TileWorldSize * 2f, parameters.AnchorClearance * 0.65f);
            if ((localPosition - entryLocalPosition).sqrMagnitude < anchorClearance * anchorClearance ||
                (localPosition - portalLocalPosition).sqrMagnitude < anchorClearance * anchorClearance)
            {
                return false;
            }

            for (int index = 0; index < protectedLocalPoints.Count; index++)
            {
                float clearance = Mathf.Max(parameters.TileWorldSize, parameters.ProtectedAnchorClearance * 0.5f);
                if ((localPosition - protectedLocalPoints[index]).sqrMagnitude < clearance * clearance)
                {
                    return false;
                }
            }

            for (int index = 0; index < buildings.Count; index++)
            {
                if (ContainsPoint(buildings[index].Footprint, localPosition))
                {
                    return false;
                }
            }

            float approachClearanceSquared = parameters.TileWorldSize * parameters.TileWorldSize * 2.25f;
            for (int index = 0; index < spatialCandidates.Count; index++)
            {
                UrbanSpatialCandidate candidate = spatialCandidates[index];
                if (candidate.Kind == UrbanSpatialCandidateKind.BuildingApproach &&
                    (candidate.LocalPosition - localPosition).sqrMagnitude < approachClearanceSquared)
                {
                    return false;
                }
            }

            float minimumSeparationSquared = parameters.TileWorldSize * parameters.TileWorldSize * 1.25f;
            for (int index = 0; index < existing.Count; index++)
            {
                if ((existing[index].LocalPosition - localPosition).sqrMagnitude < minimumSeparationSquared)
                {
                    return false;
                }
            }

            return true;
        }

        private static bool IsInsideAnyOtherBuilding(
            Vector2 contentPosition,
            Vector2 approachPosition,
            int sourceBuildingIndex,
            IReadOnlyList<UrbanBuildingPlacement> buildings)
        {
            for (int index = 0; index < buildings.Count; index++)
            {
                if (index == sourceBuildingIndex)
                {
                    continue;
                }

                Rect footprint = buildings[index].Footprint;
                if (ContainsPoint(footprint, contentPosition) ||
                    ContainsPoint(footprint, approachPosition))
                {
                    return true;
                }
            }

            return false;
        }

        private static bool IsOnAnyRoad(
            Vector2 localPosition,
            IReadOnlyList<UrbanRoadSegment> roads)
        {
            for (int index = 0; index < roads.Count; index++)
            {
                if (UrbanMapLayoutValidator.RoadContainsPoint(roads[index], localPosition, 0.05f))
                {
                    return true;
                }
            }

            return false;
        }

        private static bool ContainsPoint(Rect rect, Vector2 point)
        {
            return point.x >= rect.xMin && point.x <= rect.xMax &&
                   point.y >= rect.yMin && point.y <= rect.yMax;
        }

        private static bool CanUseSpawnPosition(
            UrbanMapLayout layout,
            UrbanRaidSpawnRequest request,
            Vector2 localPosition,
            IReadOnlyList<SelectedSpawn> selected)
        {
            if ((localPosition - layout.EntryLocalPosition).sqrMagnitude <
                request.EntryClearance * request.EntryClearance)
            {
                return false;
            }

            if (request.MaximumEntryDistance > 0f &&
                (localPosition - layout.EntryLocalPosition).sqrMagnitude >
                request.MaximumEntryDistance * request.MaximumEntryDistance)
            {
                return false;
            }

            if ((localPosition - layout.PortalLocalPosition).sqrMagnitude <
                request.PortalClearance * request.PortalClearance)
            {
                return false;
            }

            for (int index = 0; index < selected.Count; index++)
            {
                SelectedSpawn existing = selected[index];
                float requiredSeparation = Mathf.Max(
                    request.MinimumSeparation,
                    existing.Request.MinimumSeparation);
                if ((localPosition - existing.Placement.LocalPosition).sqrMagnitude <
                    requiredSeparation * requiredSeparation)
                {
                    return false;
                }
            }

            return true;
        }

        private static int PositiveModulo(int value, int modulus)
        {
            int remainder = value % modulus;
            return remainder < 0 ? remainder + modulus : remainder;
        }

        private static uint StableStringHash(string value)
        {
            const uint offset = 2166136261u;
            const uint prime = 16777619u;
            uint hash = offset;
            unchecked
            {
                for (int index = 0; index < value.Length; index++)
                {
                    hash ^= value[index];
                    hash *= prime;
                }
            }

            return hash;
        }

        private static float[] BuildAxisPositions(
            UrbanMapGenerationParameters parameters,
            float boundsMinimum)
        {
            var positions = new float[parameters.BlocksPerAxis + 1];
            float firstNode = boundsMinimum +
                              (parameters.BorderTiles + 0.5f) * parameters.TileWorldSize;
            for (int index = 0; index < positions.Length; index++)
            {
                positions[index] = firstNode + index * parameters.BlockSpanWorld;
            }

            return positions;
        }

        private static List<Vector2> BuildNodes(
            float[] baseX,
            float[] baseZ)
        {
            int columns = baseX.Length;
            int rows = baseZ.Length;
            var nodes = new List<Vector2>(columns * rows);

            for (int row = 0; row < rows; row++)
            {
                for (int column = 0; column < columns; column++)
                {
                    nodes.Add(new Vector2(baseX[column], baseZ[row]));
                }
            }

            return nodes;
        }

        /// <summary>
        /// Builds an octilinear road graph in three explicit phases: mandatory major
        /// spines, a seed-weighted Kruskal backbone, then optional loops and at most
        /// one diagonal per coarse block. Connectivity is guaranteed by construction;
        /// the one-diagonal rule prevents hidden X intersections inside a tile block.
        /// </summary>
        private static List<EdgeDraft> BuildRoadNetwork(
            int columns,
            int rows,
            int primaryColumn,
            int primaryRow,
            int nodeCount,
            UrbanMapGenerationParameters parameters,
            ref StableRandom random)
        {
            var edges = new List<EdgeDraft>((columns - 1) * rows + (rows - 1) * columns);

            for (int row = 0; row < rows; row++)
            {
                for (int column = 0; column < columns; column++)
                {
                    int current = GetNodeIndex(column, row, columns);

                    if (column + 1 < columns)
                    {
                        bool primary = row == primaryRow;
                        edges.Add(new EdgeDraft
                        {
                            From = current,
                            To = GetNodeIndex(column + 1, row, columns),
                            IsPrimary = primary,
                            IsActive = primary,
                            Width = primary ? parameters.PrimaryRoadWidth : parameters.SecondaryRoadWidth
                        });
                    }

                    if (row + 1 < rows)
                    {
                        bool primary = column == primaryColumn;
                        edges.Add(new EdgeDraft
                        {
                            From = current,
                            To = GetNodeIndex(column, row + 1, columns),
                            IsPrimary = primary,
                            IsActive = primary,
                            Width = primary ? parameters.PrimaryRoadWidth : parameters.SecondaryRoadWidth
                        });
                    }
                }
            }

            var connectivity = new DisjointSet(nodeCount);
            var secondaryCandidates = new List<int>();
            for (int index = 0; index < edges.Count; index++)
            {
                EdgeDraft edge = edges[index];
                if (edge.IsPrimary)
                {
                    connectivity.Union(edge.From, edge.To);
                }
                else
                {
                    secondaryCandidates.Add(index);
                }
            }

            Shuffle(secondaryCandidates, ref random);
            for (int candidateIndex = 0; candidateIndex < secondaryCandidates.Count; candidateIndex++)
            {
                int edgeIndex = secondaryCandidates[candidateIndex];
                EdgeDraft edge = edges[edgeIndex];
                if (!connectivity.Union(edge.From, edge.To))
                {
                    continue;
                }

                edge.IsActive = true;
                edges[edgeIndex] = edge;
            }

            for (int candidateIndex = 0; candidateIndex < secondaryCandidates.Count; candidateIndex++)
            {
                int edgeIndex = secondaryCandidates[candidateIndex];
                EdgeDraft edge = edges[edgeIndex];
                if (edge.IsActive || random.NextFloat() > parameters.AdditionalRoadChance)
                {
                    continue;
                }

                edge.IsActive = true;
                edges[edgeIndex] = edge;
            }

            for (int row = 0; row + 1 < rows; row++)
            {
                for (int column = 0; column + 1 < columns; column++)
                {
                    if (random.NextFloat() > parameters.DiagonalRoadChance)
                    {
                        continue;
                    }

                    bool slopesUp = random.NextFloat() < 0.5f;
                    int from = slopesUp
                        ? GetNodeIndex(column, row, columns)
                        : GetNodeIndex(column + 1, row, columns);
                    int to = slopesUp
                        ? GetNodeIndex(column + 1, row + 1, columns)
                        : GetNodeIndex(column, row + 1, columns);
                    edges.Add(new EdgeDraft
                    {
                        From = from,
                        To = to,
                        IsPrimary = false,
                        IsActive = true,
                        Width = parameters.SecondaryRoadWidth
                    });
                }
            }

            return edges;
        }

        private static void Shuffle(List<int> values, ref StableRandom random)
        {
            for (int index = values.Count - 1; index > 0; index--)
            {
                int swapIndex = random.Range(0, index + 1);
                (values[index], values[swapIndex]) = (values[swapIndex], values[index]);
            }
        }

        private static List<UrbanRoadSegment> CreateRoadSegments(List<EdgeDraft> drafts, List<Vector2> nodes)
        {
            var roads = new List<UrbanRoadSegment>();
            for (int index = 0; index < drafts.Count; index++)
            {
                EdgeDraft draft = drafts[index];
                if (!draft.IsActive)
                {
                    continue;
                }

                roads.Add(new UrbanRoadSegment(
                    draft.From,
                    draft.To,
                    nodes[draft.From],
                    nodes[draft.To],
                    draft.Width,
                    draft.IsPrimary));
            }

            return roads;
        }

        private static Vector2 FindPortalApproach(
            List<EdgeDraft> drafts,
            List<Vector2> nodes,
            int portalNodeIndex,
            float distance)
        {
            for (int index = 0; index < drafts.Count; index++)
            {
                EdgeDraft draft = drafts[index];
                if (!draft.IsActive || (draft.From != portalNodeIndex && draft.To != portalNodeIndex))
                {
                    continue;
                }

                int neighbor = draft.From == portalNodeIndex ? draft.To : draft.From;
                Vector2 direction = (nodes[neighbor] - nodes[portalNodeIndex]).normalized;
                return nodes[portalNodeIndex] + direction * distance;
            }

            return nodes[portalNodeIndex];
        }

        private static List<Vector2> ConvertProtectedPointsToLocal(
            IReadOnlyList<Vector2> protectedWorldPositions,
            Vector2 entryWorldPosition,
            Vector2 entryLocalPosition,
            float cityRotationDegrees)
        {
            var result = new List<Vector2>();
            if (protectedWorldPositions == null)
            {
                return result;
            }

            float radians = -cityRotationDegrees * Mathf.Deg2Rad;
            float cosine = Mathf.Cos(radians);
            float sine = Mathf.Sin(radians);

            for (int index = 0; index < protectedWorldPositions.Count; index++)
            {
                Vector2 offset = protectedWorldPositions[index] - entryWorldPosition;
                result.Add(entryLocalPosition + new Vector2(
                    offset.x * cosine - offset.y * sine,
                    offset.x * sine + offset.y * cosine));
            }

            return result;
        }

        private static UrbanSurfaceGrid BuildSurfaceGrid(
            Rect localBounds,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanMapGenerationParameters parameters)
        {
            int size = parameters.MapTilesPerAxis;
            var kinds = new UrbanSurfaceTileKind[size * size];
            var roadPorts = new UrbanTileConnection[size * size];

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                int roadWidthTiles = road.IsPrimary
                    ? parameters.PrimaryRoadWidthTiles
                    : parameters.SecondaryRoadWidthTiles;
                int roadRadius = roadWidthTiles / 2;
                int sidewalkRadius = roadRadius + parameters.SidewalkWidthTiles;
                List<Vector2Int> centerline = RasterizeOctilinearRoad(
                    road,
                    localBounds.position,
                    parameters.TileWorldSize,
                    size);
                AddRoadPorts(roadPorts, size, centerline);

                for (int cellIndex = 0; cellIndex < centerline.Count; cellIndex++)
                {
                    StampSurfaceDisk(
                        kinds,
                        size,
                        centerline[cellIndex],
                        sidewalkRadius,
                        UrbanSurfaceTileKind.Sidewalk,
                        overwriteRoad: false);
                }

                UrbanSurfaceTileKind roadKind = road.IsPrimary
                    ? UrbanSurfaceTileKind.PrimaryRoad
                    : UrbanSurfaceTileKind.SecondaryRoad;
                for (int cellIndex = 0; cellIndex < centerline.Count; cellIndex++)
                {
                    StampSurfaceDisk(
                        kinds,
                        size,
                        centerline[cellIndex],
                        roadRadius,
                        roadKind,
                        overwriteRoad: road.IsPrimary);
                }
            }

            UrbanTileConnection[] masks = BuildAutotileConnectionMasks(kinds, size, size);
            return new UrbanSurfaceGrid(
                size,
                size,
                parameters.TileWorldSize,
                localBounds.position,
                kinds,
                masks,
                roadPorts);
        }

        private static void AddRoadPorts(
            UrbanTileConnection[] roadPorts,
            int gridSize,
            IReadOnlyList<Vector2Int> centerline)
        {
            for (int index = 1; index < centerline.Count; index++)
            {
                Vector2Int previous = centerline[index - 1];
                Vector2Int current = centerline[index];
                int deltaX = current.x - previous.x;
                int deltaZ = current.y - previous.y;
                UrbanTileConnection forward =
                    UrbanSurfaceGrid.ConnectionFromUnitStep(deltaX, deltaZ);
                UrbanTileConnection backward =
                    UrbanSurfaceGrid.ConnectionFromUnitStep(-deltaX, -deltaZ);
                roadPorts[previous.y * gridSize + previous.x] |= forward;
                roadPorts[current.y * gridSize + current.x] |= backward;
            }
        }

        private static List<Vector2Int> RasterizeOctilinearRoad(
            UrbanRoadSegment road,
            Vector2 localOrigin,
            float tileSize,
            int gridSize)
        {
            Vector2Int start = LocalToCellUnchecked(road.Start, localOrigin, tileSize);
            Vector2Int end = LocalToCellUnchecked(road.End, localOrigin, tileSize);
            int deltaX = end.x - start.x;
            int deltaZ = end.y - start.y;
            int absoluteX = Mathf.Abs(deltaX);
            int absoluteZ = Mathf.Abs(deltaZ);
            if (absoluteX != 0 && absoluteZ != 0 && absoluteX != absoluteZ)
            {
                throw new System.InvalidOperationException(
                    $"Road {road.FromNodeIndex}->{road.ToNodeIndex} is not aligned to one of the eight tile directions.");
            }

            int steps = Mathf.Max(absoluteX, absoluteZ);
            int stepX = System.Math.Sign(deltaX);
            int stepZ = System.Math.Sign(deltaZ);
            var cells = new List<Vector2Int>(steps + 1);
            for (int step = 0; step <= steps; step++)
            {
                var cell = new Vector2Int(start.x + stepX * step, start.y + stepZ * step);
                if (cell.x < 0 || cell.x >= gridSize || cell.y < 0 || cell.y >= gridSize)
                {
                    throw new System.InvalidOperationException(
                        $"Road {road.FromNodeIndex}->{road.ToNodeIndex} left the fixed surface grid.");
                }

                cells.Add(cell);
            }

            return cells;
        }

        private static Vector2Int LocalToCellUnchecked(
            Vector2 localPosition,
            Vector2 localOrigin,
            float tileSize)
        {
            Vector2 relative = localPosition - localOrigin;
            return new Vector2Int(
                Mathf.FloorToInt(relative.x / tileSize),
                Mathf.FloorToInt(relative.y / tileSize));
        }

        private static void StampSurfaceDisk(
            UrbanSurfaceTileKind[] kinds,
            int gridSize,
            Vector2Int center,
            int radius,
            UrbanSurfaceTileKind kind,
            bool overwriteRoad)
        {
            int radiusSquared = radius * radius;
            for (int offsetZ = -radius; offsetZ <= radius; offsetZ++)
            {
                for (int offsetX = -radius; offsetX <= radius; offsetX++)
                {
                    if (offsetX * offsetX + offsetZ * offsetZ > radiusSquared)
                    {
                        continue;
                    }

                    int x = center.x + offsetX;
                    int z = center.y + offsetZ;
                    if (x < 0 || x >= gridSize || z < 0 || z >= gridSize)
                    {
                        continue;
                    }

                    int index = z * gridSize + x;
                    UrbanSurfaceTileKind existing = kinds[index];
                    if (kind == UrbanSurfaceTileKind.Sidewalk)
                    {
                        if (existing == UrbanSurfaceTileKind.Ground)
                        {
                            kinds[index] = kind;
                        }
                        continue;
                    }

                    if (!UrbanSurfaceGrid.IsRoad(existing) || overwriteRoad)
                    {
                        kinds[index] = kind;
                    }
                }
            }
        }

        private static UrbanTileConnection[] BuildAutotileConnectionMasks(
            UrbanSurfaceTileKind[] kinds,
            int width,
            int height)
        {
            var masks = new UrbanTileConnection[kinds.Length];

            for (int z = 0; z < height; z++)
            {
                for (int x = 0; x < width; x++)
                {
                    int index = z * width + x;
                    UrbanSurfaceTileKind source = kinds[index];
                    masks[index] = UrbanSurfaceGrid.ComposeCanonicalSurfaceMask(
                        IsCompatibleSurface(kinds, width, height, x, z + 1, source),
                        IsCompatibleSurface(kinds, width, height, x + 1, z + 1, source),
                        IsCompatibleSurface(kinds, width, height, x + 1, z, source),
                        IsCompatibleSurface(kinds, width, height, x + 1, z - 1, source),
                        IsCompatibleSurface(kinds, width, height, x, z - 1, source),
                        IsCompatibleSurface(kinds, width, height, x - 1, z - 1, source),
                        IsCompatibleSurface(kinds, width, height, x - 1, z, source),
                        IsCompatibleSurface(kinds, width, height, x - 1, z + 1, source));
                }
            }

            return masks;
        }

        private static bool IsCompatibleSurface(
            UrbanSurfaceTileKind[] kinds,
            int width,
            int height,
            int x,
            int z,
            UrbanSurfaceTileKind source)
        {
            return x >= 0 && x < width && z >= 0 && z < height &&
                   UrbanSurfaceGrid.AreAutotileCompatible(source, kinds[z * width + x]);
        }

        private static List<UrbanParcelPlacement> BuildRoadFrontageParcels(
            Rect localBounds,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid surfaceGrid,
            UrbanMapGenerationParameters parameters,
            ref StableRandom random)
        {
            var drafts = new List<ParcelDraft>();
            float tileSize = parameters.TileWorldSize;
            float lotGap = Mathf.Ceil(parameters.LotGap / tileSize) * tileSize;
            float minimumFrontage = parameters.MinBuildingFrontageTiles * tileSize;
            float maximumFrontage = parameters.MaxBuildingFrontageTiles * tileSize;

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                Vector2 delta = road.End - road.Start;
                bool isCardinal = Mathf.Abs(delta.x) <= 0.01f || Mathf.Abs(delta.y) <= 0.01f;
                if (!isCardinal || delta.sqrMagnitude <= 0.0001f)
                {
                    // Diagonal frontage needs rotated footprint masks. Until that data exists,
                    // diagonals remain roads rather than silently accepting axis-aligned lots.
                    continue;
                }

                Vector2 roadDirection = delta.normalized;
                Vector2 roadNormal = new Vector2(-roadDirection.y, roadDirection.x);
                float startClearance = GetJunctionParcelClearance(
                    road.FromNodeIndex,
                    roads,
                    parameters);
                float endClearance = GetJunctionParcelClearance(
                    road.ToNodeIndex,
                    roads,
                    parameters);
                float frontageLength = road.Length - startClearance - endClearance;
                int parcelCount = Mathf.FloorToInt(
                    (frontageLength + lotGap) / (minimumFrontage + lotGap));

                while (parcelCount > 0)
                {
                    float availablePerParcel =
                        (frontageLength - lotGap * (parcelCount - 1)) / parcelCount;
                    if (availablePerParcel + 0.001f >= minimumFrontage)
                    {
                        break;
                    }

                    parcelCount--;
                }

                if (parcelCount <= 0)
                {
                    continue;
                }

                float frontage = Mathf.Clamp(
                    SnapDownToTile(
                        (frontageLength - lotGap * (parcelCount - 1)) / parcelCount,
                        tileSize),
                    minimumFrontage,
                    maximumFrontage);
                float usedLength = frontage * parcelCount + lotGap * (parcelCount - 1);
                float firstDistance = startClearance +
                                      Mathf.Max(0f, frontageLength - usedLength) * 0.5f +
                                      frontage * 0.5f;

                for (int parcelAlongRoad = 0; parcelAlongRoad < parcelCount; parcelAlongRoad++)
                {
                    float distanceAlongRoad = firstDistance +
                                              parcelAlongRoad * (frontage + lotGap);
                    Vector2 roadPoint = road.Start + roadDirection * distanceAlongRoad;

                    for (int side = -1; side <= 1; side += 2)
                    {
                        int depthTiles = random.Range(
                            parameters.MinBuildingDepthTiles,
                            parameters.MaxBuildingDepthTiles + 1);
                        float depth = depthTiles * tileSize;
                        Vector2 awayFromRoad = roadNormal * side;
                        float centerOffset = road.Width * 0.5f +
                                             parameters.SidewalkWidth +
                                             parameters.BuildingSetback +
                                             tileSize * 0.5f +
                                             depth * 0.5f;
                        Vector2 center = roadPoint + awayFromRoad * centerOffset;
                        Vector2 size = Mathf.Abs(roadDirection.x) > 0.5f
                            ? new Vector2(frontage, depth)
                            : new Vector2(depth, frontage);
                        var draft = new ParcelDraft(
                            roadIndex,
                            distanceAlongRoad,
                            side,
                            center,
                            size,
                            -awayFromRoad);

                        if (IsBuildableFootprint(
                                draft.Footprint,
                                localBounds,
                                roads,
                                surfaceGrid,
                                parameters))
                        {
                            drafts.Add(draft);
                        }
                    }
                }
            }

            var shuffledIndices = new List<int>(drafts.Count);
            for (int index = 0; index < drafts.Count; index++)
            {
                shuffledIndices.Add(index);
            }
            Shuffle(shuffledIndices, ref random);

            var selected = new List<ParcelDraft>();
            for (int shuffledIndex = 0; shuffledIndex < shuffledIndices.Count; shuffledIndex++)
            {
                ParcelDraft candidate = drafts[shuffledIndices[shuffledIndex]];
                bool overlaps = false;
                for (int selectedIndex = 0; selectedIndex < selected.Count; selectedIndex++)
                {
                    if (candidate.Footprint.Overlaps(selected[selectedIndex].Footprint))
                    {
                        overlaps = true;
                        break;
                    }
                }

                if (!overlaps)
                {
                    selected.Add(candidate);
                }
            }

            selected.Sort((left, right) =>
            {
                int roadComparison = left.SourceRoadIndex.CompareTo(right.SourceRoadIndex);
                if (roadComparison != 0)
                {
                    return roadComparison;
                }

                int distanceComparison = left.DistanceAlongRoad.CompareTo(right.DistanceAlongRoad);
                return distanceComparison != 0
                    ? distanceComparison
                    : left.Side.CompareTo(right.Side);
            });

            var parcels = new List<UrbanParcelPlacement>(selected.Count);
            for (int index = 0; index < selected.Count; index++)
            {
                ParcelDraft draft = selected[index];
                parcels.Add(new UrbanParcelPlacement(
                    index,
                    draft.SourceRoadIndex,
                    draft.DistanceAlongRoad,
                    draft.Side,
                    draft.Center,
                    draft.Size,
                    draft.FacadeDirection));
            }

            return parcels;
        }

        private static List<UrbanBuildingPlacement> BuildBuildings(
            IReadOnlyList<UrbanParcelPlacement> parcels,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid surfaceGrid,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters,
            ref StableRandom random)
        {
            var buildings = new List<UrbanBuildingPlacement>();
            for (int parcelIndex = 0; parcelIndex < parcels.Count; parcelIndex++)
            {
                if (random.NextFloat() > parameters.BuildingDensity)
                {
                    continue;
                }

                UrbanParcelPlacement parcel = parcels[parcelIndex];
                var placement = new UrbanBuildingPlacement(
                    parcelIndex,
                    parcel.Center,
                    parcel.Size,
                    random.Range(parameters.MinBuildingHeight, parameters.MaxBuildingHeight),
                    random.Range(0, 5));

                if (!CanPlaceBuilding(
                        placement,
                        roads,
                        surfaceGrid,
                        buildings,
                        entryLocalPosition,
                        portalLocalPosition,
                        protectedLocalPoints,
                        parameters))
                {
                    continue;
                }

                buildings.Add(placement);
            }

            return buildings;
        }

        private static bool CanPlaceBuilding(
            UrbanBuildingPlacement candidate,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid surfaceGrid,
            IReadOnlyList<UrbanBuildingPlacement> existingBuildings,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters)
        {
            Rect footprint = candidate.Footprint;

            if (!FootprintUsesOnlyGround(surfaceGrid, footprint))
            {
                return false;
            }

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                if (UrbanMapLayoutValidator.RoadIntersectsRect(
                        roads[roadIndex],
                        footprint,
                        parameters.SidewalkWidth + parameters.BuildingSetback))
                {
                    return false;
                }
            }

            if (UrbanMapLayoutValidator.RectIntersectsCircle(footprint, entryLocalPosition, parameters.AnchorClearance) ||
                UrbanMapLayoutValidator.RectIntersectsCircle(footprint, portalLocalPosition, parameters.AnchorClearance))
            {
                return false;
            }

            for (int index = 0; index < protectedLocalPoints.Count; index++)
            {
                if (UrbanMapLayoutValidator.RectIntersectsCircle(
                        footprint,
                        protectedLocalPoints[index],
                        parameters.ProtectedAnchorClearance))
                {
                    return false;
                }
            }

            for (int index = 0; index < existingBuildings.Count; index++)
            {
                if (footprint.Overlaps(existingBuildings[index].Footprint))
                {
                    return false;
                }
            }

            return true;
        }

        private static float GetJunctionParcelClearance(
            int nodeIndex,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanMapGenerationParameters parameters)
        {
            float widestConnectedHalfRoad = 0f;
            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                if (road.FromNodeIndex == nodeIndex || road.ToNodeIndex == nodeIndex)
                {
                    widestConnectedHalfRoad = Mathf.Max(widestConnectedHalfRoad, road.Width * 0.5f);
                }
            }

            return widestConnectedHalfRoad +
                   parameters.SidewalkWidth +
                   parameters.BuildingSetback +
                   parameters.TileWorldSize * 0.5f;
        }

        private static bool IsBuildableFootprint(
            Rect footprint,
            Rect localBounds,
            IReadOnlyList<UrbanRoadSegment> roads,
            UrbanSurfaceGrid surfaceGrid,
            UrbanMapGenerationParameters parameters)
        {
            if (!ContainsRect(localBounds, footprint) ||
                !FootprintUsesOnlyGround(surfaceGrid, footprint))
            {
                return false;
            }

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                if (UrbanMapLayoutValidator.RoadIntersectsRect(
                        roads[roadIndex],
                        footprint,
                        parameters.SidewalkWidth + parameters.BuildingSetback))
                {
                    return false;
                }
            }

            return true;
        }

        private static bool FootprintUsesOnlyGround(UrbanSurfaceGrid grid, Rect footprint)
        {
            const float tolerance = 0.01f;
            if (!grid.TryLocalToCell(new Vector2(footprint.xMin, footprint.yMin), out int minX, out int minZ) ||
                !grid.TryLocalToCell(
                    new Vector2(footprint.xMax - tolerance, footprint.yMax - tolerance),
                    out int maxX,
                    out int maxZ))
            {
                return false;
            }

            for (int z = minZ; z <= maxZ; z++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    Vector2 cellCenter = grid.GetCellCenter(x, z);
                    if (ContainsPoint(footprint, cellCenter) &&
                        grid.GetKind(x, z) != UrbanSurfaceTileKind.Ground)
                    {
                        return false;
                    }
                }
            }

            return true;
        }

        private static bool ContainsRect(Rect outer, Rect inner)
        {
            const float tolerance = 0.01f;
            return inner.xMin >= outer.xMin - tolerance &&
                   inner.xMax <= outer.xMax + tolerance &&
                   inner.yMin >= outer.yMin - tolerance &&
                   inner.yMax <= outer.yMax + tolerance;
        }

        private static float SnapDownToTile(float value, float tileSize)
        {
            return Mathf.Floor(value / tileSize) * tileSize;
        }

        private static int GetNodeIndex(int column, int row, int columns)
        {
            return row * columns + column;
        }

        private static uint DeriveSeed(int seed, uint stream)
        {
            unchecked
            {
                uint value = (uint)seed ^ stream;
                value ^= value >> 16;
                value *= 0x7FEB352Du;
                value ^= value >> 15;
                value *= 0x846CA68Bu;
                value ^= value >> 16;
                return value == 0 ? stream : value;
            }
        }
    }
}
