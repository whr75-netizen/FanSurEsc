using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public static class UrbanMapLayoutPlanner
    {
        public const int GeneratorVersion = 1;
        public const int SpawnManifestVersion = 1;

        private static readonly float[] SpawnCandidateFractions = { 0.2f, 0.35f, 0.5f, 0.65f, 0.8f };

        private struct EdgeDraft
        {
            public int From;
            public int To;
            public bool IsPrimary;
            public bool IsActive;
            public float Width;
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

            var dimensionsRandom = new StableRandom(DeriveSeed(seed, 0xA511E9B3u));
            var roadRandom = new StableRandom(DeriveSeed(seed, 0x63D83595u));
            var buildingRandom = new StableRandom(DeriveSeed(seed, 0xC2B2AE35u));

            int blocksX = dimensionsRandom.Range(parameters.MinBlocksX, parameters.MaxBlocksX + 1);
            int blocksZ = dimensionsRandom.Range(parameters.MinBlocksZ, parameters.MaxBlocksZ + 1);
            float cityRotation = dimensionsRandom.Range(parameters.CityRotationMin, parameters.CityRotationMax);

            float[] baseX = BuildAxisPositions(blocksX, parameters, ref dimensionsRandom);
            float[] baseZ = BuildAxisPositions(blocksZ, parameters, ref dimensionsRandom);
            int nodeColumns = blocksX + 1;
            int nodeRows = blocksZ + 1;
            var nodes = BuildNodes(baseX, baseZ, parameters.IntersectionJitter, ref roadRandom);

            int primaryRow = roadRandom.Range(1, Mathf.Max(2, nodeRows - 1));
            int primaryColumn = roadRandom.Range(1, Mathf.Max(2, nodeColumns - 1));
            List<EdgeDraft> edgeDrafts = BuildRoadDrafts(
                nodeColumns,
                nodeRows,
                primaryColumn,
                primaryRow,
                parameters);

            RemoveMinorRoadsWhileConnected(edgeDrafts, nodes.Count, parameters.MinorRoadRemovalChance, ref roadRandom);
            List<UrbanRoadSegment> roads = CreateRoadSegments(edgeDrafts, nodes);

            Vector2 entryLocalPosition = nodes[0];
            int portalNodeIndex = nodes.Count - 1;
            Vector2 portalLocalPosition = nodes[portalNodeIndex];
            Vector2 portalApproach = FindPortalApproach(edgeDrafts, nodes, portalNodeIndex, parameters.AnchorClearance * 0.65f);

            float outerMargin = parameters.OuterMargin;
            Rect localBounds = new Rect(
                -outerMargin,
                -outerMargin,
                baseX[baseX.Length - 1] + outerMargin * 2f,
                baseZ[baseZ.Length - 1] + outerMargin * 2f);

            List<Vector2> protectedLocalPoints = ConvertProtectedPointsToLocal(
                protectedWorldPositions,
                entryWorldPosition,
                cityRotation);

            List<UrbanBuildingPlacement> buildings = BuildBuildings(
                baseX,
                baseZ,
                roads,
                entryLocalPosition,
                portalLocalPosition,
                protectedLocalPoints,
                parameters,
                ref buildingRandom);

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
                buildings,
                protectedLocalPoints);

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
                System.StringComparer.Ordinal.Compare(left.StableId, right.StableId));

            List<SpawnCandidate> candidates = BuildSpawnCandidates(layout.Roads);
            if (candidates.Count < sortedRequests.Count)
            {
                error =
                    $"Urban map seed {layout.Seed} has only {candidates.Count} road spawn candidates " +
                    $"for {sortedRequests.Count} bound entities.";
                return false;
            }

            var selected = new List<SelectedSpawn>(sortedRequests.Count);
            var placements = new List<UrbanRaidSpawnPlacement>(sortedRequests.Count);
            for (int requestIndex = 0; requestIndex < sortedRequests.Count; requestIndex++)
            {
                UrbanRaidSpawnRequest request = sortedRequests[requestIndex];
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

        private static List<SpawnCandidate> BuildSpawnCandidates(IReadOnlyList<UrbanRoadSegment> roads)
        {
            var candidates = new List<SpawnCandidate>(roads.Count * SpawnCandidateFractions.Length);
            int candidateId = 0;
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
                    candidates.Add(new SpawnCandidate(
                        candidateId++,
                        Vector2.Lerp(road.Start, road.End, fraction),
                        direction));
                }
            }

            return candidates;
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
            int blockCount,
            UrbanMapGenerationParameters parameters,
            ref StableRandom random)
        {
            var positions = new float[blockCount + 1];
            for (int index = 1; index < positions.Length; index++)
            {
                positions[index] = positions[index - 1] + random.Range(parameters.MinBlockSize, parameters.MaxBlockSize);
            }

            return positions;
        }

        private static List<Vector2> BuildNodes(
            float[] baseX,
            float[] baseZ,
            float jitter,
            ref StableRandom random)
        {
            int columns = baseX.Length;
            int rows = baseZ.Length;
            var nodes = new List<Vector2>(columns * rows);

            for (int row = 0; row < rows; row++)
            {
                for (int column = 0; column < columns; column++)
                {
                    bool isEntry = row == 0 && column == 0;
                    bool isPortal = row == rows - 1 && column == columns - 1;
                    float edgeMultiplier = row == 0 || row == rows - 1 || column == 0 || column == columns - 1
                        ? 0.45f
                        : 1f;
                    float offsetX = isEntry || isPortal ? 0f : random.Range(-jitter, jitter) * edgeMultiplier;
                    float offsetZ = isEntry || isPortal ? 0f : random.Range(-jitter, jitter) * edgeMultiplier;
                    nodes.Add(new Vector2(baseX[column] + offsetX, baseZ[row] + offsetZ));
                }
            }

            return nodes;
        }

        private static List<EdgeDraft> BuildRoadDrafts(
            int columns,
            int rows,
            int primaryColumn,
            int primaryRow,
            UrbanMapGenerationParameters parameters)
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
                            IsActive = true,
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
                            IsActive = true,
                            Width = primary ? parameters.PrimaryRoadWidth : parameters.SecondaryRoadWidth
                        });
                    }
                }
            }

            return edges;
        }

        private static void RemoveMinorRoadsWhileConnected(
            List<EdgeDraft> edges,
            int nodeCount,
            float removalChance,
            ref StableRandom random)
        {
            var candidates = new List<int>();
            for (int index = 0; index < edges.Count; index++)
            {
                if (!edges[index].IsPrimary)
                {
                    candidates.Add(index);
                }
            }

            for (int index = candidates.Count - 1; index > 0; index--)
            {
                int swapIndex = random.Range(0, index + 1);
                (candidates[index], candidates[swapIndex]) = (candidates[swapIndex], candidates[index]);
            }

            for (int candidateIndex = 0; candidateIndex < candidates.Count; candidateIndex++)
            {
                if (random.NextFloat() > removalChance)
                {
                    continue;
                }

                int edgeIndex = candidates[candidateIndex];
                EdgeDraft draft = edges[edgeIndex];
                draft.IsActive = false;
                edges[edgeIndex] = draft;

                if (!IsGraphConnected(nodeCount, edges))
                {
                    draft.IsActive = true;
                    edges[edgeIndex] = draft;
                }
            }
        }

        private static bool IsGraphConnected(int nodeCount, List<EdgeDraft> edges)
        {
            var adjacency = new List<int>[nodeCount];
            for (int index = 0; index < nodeCount; index++)
            {
                adjacency[index] = new List<int>();
            }

            for (int index = 0; index < edges.Count; index++)
            {
                EdgeDraft edge = edges[index];
                if (!edge.IsActive)
                {
                    continue;
                }

                adjacency[edge.From].Add(edge.To);
                adjacency[edge.To].Add(edge.From);
            }

            var queue = new Queue<int>();
            var visited = new bool[nodeCount];
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
                result.Add(new Vector2(
                    offset.x * cosine - offset.y * sine,
                    offset.x * sine + offset.y * cosine));
            }

            return result;
        }

        private static List<UrbanBuildingPlacement> BuildBuildings(
            float[] baseX,
            float[] baseZ,
            IReadOnlyList<UrbanRoadSegment> roads,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters,
            ref StableRandom random)
        {
            var buildings = new List<UrbanBuildingPlacement>();
            const float geometrySafetyMargin = 0.15f;
            float roadInset = parameters.PrimaryRoadWidth * 0.5f +
                              parameters.BuildingSetback +
                              parameters.IntersectionJitter +
                              geometrySafetyMargin;

            for (int blockZ = 0; blockZ < baseZ.Length - 1; blockZ++)
            {
                for (int blockX = 0; blockX < baseX.Length - 1; blockX++)
                {
                    Rect usable = Rect.MinMaxRect(
                        baseX[blockX] + roadInset,
                        baseZ[blockZ] + roadInset,
                        baseX[blockX + 1] - roadInset,
                        baseZ[blockZ + 1] - roadInset);

                    if (usable.width < 3.5f || usable.height < 3.5f)
                    {
                        continue;
                    }

                    float targetLotWidth = random.Range(5.25f, 8.25f);
                    float targetLotDepth = random.Range(5.25f, 8.25f);
                    int columns = Mathf.Max(1, Mathf.FloorToInt(usable.width / targetLotWidth));
                    int rows = Mathf.Max(1, Mathf.FloorToInt(usable.height / targetLotDepth));
                    float cellWidth = usable.width / columns;
                    float cellDepth = usable.height / rows;

                    for (int row = 0; row < rows; row++)
                    {
                        for (int column = 0; column < columns; column++)
                        {
                            if (random.NextFloat() > parameters.BuildingDensity)
                            {
                                continue;
                            }

                            float maximumJitterX = Mathf.Max(0f, (cellWidth - parameters.LotGap - 3f) * 0.12f);
                            float maximumJitterZ = Mathf.Max(0f, (cellDepth - parameters.LotGap - 3f) * 0.12f);
                            Vector2 center = new Vector2(
                                usable.xMin + (column + 0.5f) * cellWidth + random.Range(-maximumJitterX, maximumJitterX),
                                usable.yMin + (row + 0.5f) * cellDepth + random.Range(-maximumJitterZ, maximumJitterZ));
                            Vector2 size = new Vector2(
                                Mathf.Max(3f, cellWidth - parameters.LotGap - random.Range(0f, 0.75f)),
                                Mathf.Max(3f, cellDepth - parameters.LotGap - random.Range(0f, 0.75f)));
                            var placement = new UrbanBuildingPlacement(
                                center,
                                size,
                                random.Range(parameters.MinBuildingHeight, parameters.MaxBuildingHeight),
                                random.Range(0, 5));

                            if (!CanPlaceBuilding(
                                    placement,
                                    roads,
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
                    }
                }
            }

            return buildings;
        }

        private static bool CanPlaceBuilding(
            UrbanBuildingPlacement candidate,
            IReadOnlyList<UrbanRoadSegment> roads,
            IReadOnlyList<UrbanBuildingPlacement> existingBuildings,
            Vector2 entryLocalPosition,
            Vector2 portalLocalPosition,
            IReadOnlyList<Vector2> protectedLocalPoints,
            UrbanMapGenerationParameters parameters)
        {
            Rect footprint = candidate.Footprint;

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                if (UrbanMapLayoutValidator.RoadIntersectsRect(roads[roadIndex], footprint, parameters.BuildingSetback))
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
