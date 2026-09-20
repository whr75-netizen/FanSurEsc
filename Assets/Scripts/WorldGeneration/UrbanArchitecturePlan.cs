using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public enum UrbanArchitectureProgram { Supermarket, PoliceStation, Residence, Cafe, RetailShop }

    public readonly struct UrbanPlanRoom
    {
        public UrbanPlanRoom(int floor, string role, Rect bounds, bool hasDoor = false, Vector2 doorCenter = default)
        { Floor = floor; Role = role; Bounds = bounds; HasDoor = hasDoor; DoorCenter = doorCenter; }
        public int Floor { get; }
        public string Role { get; }
        public Rect Bounds { get; }
        public bool HasDoor { get; }
        public Vector2 DoorCenter { get; }
    }

    /// <summary>A shared wall centreline, with at most one opening. Geometry and collision use this same record.</summary>
    public readonly struct UrbanPlanPartition
    {
        public UrbanPlanPartition(int floor, Vector2 start, Vector2 end, Vector2 doorCenter = default, float doorWidth = 0f)
        { Floor = floor; Start = start; End = end; DoorCenter = doorCenter; DoorWidth = doorWidth; }
        public int Floor { get; }
        public Vector2 Start { get; }
        public Vector2 End { get; }
        public Vector2 DoorCenter { get; }
        public float DoorWidth { get; }
    }

    public sealed class UrbanPlanStair
    {
        public UrbanPlanStair(Rect bounds, float rise)
        {
            Bounds = bounds; Rise = rise;
            // The entrance lobby is +Z: the low end must be reached directly from that lobby.
            Start = new Vector2(bounds.center.x, bounds.yMax);
            End = new Vector2(bounds.center.x, bounds.yMin);
        }
        public Rect Bounds { get; }
        public Vector2 Start { get; }
        public Vector2 End { get; }
        public float Rise { get; }
        public float Run => Bounds.height;
    }

    /// <summary>Metres in the building's local XZ frame; +Z is the existing street-facing doorway.</summary>
    public sealed class UrbanFloorPlan
    {
        internal UrbanFloorPlan(int buildingIndex, UrbanArchitectureProgram program, Vector2 size,
            List<UrbanPlanRoom> rooms, List<UrbanPlanPartition> partitions, UrbanPlanStair stair, List<Rect> upperSlabs,
            Vector2? serviceDoorCenter = null)
        {
            BuildingIndex = buildingIndex; Program = program; Size = size;
            Rooms = rooms.AsReadOnly(); Partitions = partitions.AsReadOnly(); Stair = stair;
            UpperSlabs = upperSlabs.AsReadOnly();
            ServiceDoorCenter = serviceDoorCenter;
        }
        public int BuildingIndex { get; }
        public UrbanArchitectureProgram Program { get; }
        public Vector2 Size { get; }
        public float StoreyHeight => 3.4f;
        public int FloorCount => Stair != null ? 2 : 1;
        public Vector2 EntryPoint => new Vector2(0, Size.y * .5f - .5f);
        public int EntryRoomIndex
        {
            get
            {
                for (int i = 0; i < Rooms.Count; i++)
                    if (Rooms[i].Floor == 0 && Rooms[i].Bounds.Contains(EntryPoint)) return i;
                return -1;
            }
        }
        public Vector2? ServiceDoorCenter { get; }
        public float ServiceDoorWidth => 1.8f;
        public IReadOnlyList<UrbanPlanRoom> Rooms { get; }
        public IReadOnlyList<UrbanPlanPartition> Partitions { get; }
        public UrbanPlanStair Stair { get; }
        public IReadOnlyList<Rect> UpperSlabs { get; }

        public bool TryValidate(out string error)
        {
            const float tolerance = .001f;
            Rect footprint = new Rect(-Size * .5f, Size);
            for (int i = 0; i < Rooms.Count; i++)
            {
                UrbanPlanRoom room = Rooms[i];
                if (room.Floor < 0 || room.Floor >= FloorCount || room.Bounds.width < 1.4f ||
                    room.Bounds.height < 1.4f || !Contains(footprint, room.Bounds))
                { error = $"Architecture room {i} is outside its floor or below the circulation width."; return false; }
                if (ServiceDoorCenter.HasValue && room.Role != "Service corridor" &&
                    (room.Bounds.width < 2.4f - tolerance || room.Bounds.height < 2.4f - tolerance))
                { error = $"Commercial room {i} is below its 2.4m module dimension."; return false; }
                for (int j = 0; j < i; j++)
                    if (Rooms[j].Floor == room.Floor && PositiveOverlap(room.Bounds, Rooms[j].Bounds))
                    { error = $"Architecture rooms {i}/{j} overlap."; return false; }
                if (Stair != null && PositiveOverlap(room.Bounds, Stair.Bounds))
                { error = $"Architecture room {i} overlaps the stair opening."; return false; }
            }
            foreach (UrbanPlanPartition wall in Partitions)
            {
                Vector2 delta = wall.End - wall.Start;
                bool vertical = Mathf.Abs(delta.x) < tolerance;
                if (wall.Floor < 0 || wall.Floor >= FloorCount ||
                    (!vertical && Mathf.Abs(delta.y) >= tolerance) || delta.magnitude < .2f ||
                    !Contains(footprint, Rect.MinMaxRect(Mathf.Min(wall.Start.x, wall.End.x),
                        Mathf.Min(wall.Start.y, wall.End.y), Mathf.Max(wall.Start.x, wall.End.x), Mathf.Max(wall.Start.y, wall.End.y))))
                { error = "Architecture partition is not an in-bounds orthogonal segment."; return false; }
                if (wall.DoorWidth > 0)
                {
                    float along = Vector2.Dot(wall.DoorCenter - wall.Start, delta.normalized);
                    float perpendicular = Mathf.Abs(Vector2.Dot(wall.DoorCenter - wall.Start,
                        new Vector2(-delta.y, delta.x).normalized));
                    if (wall.DoorWidth < 1.4f || perpendicular > tolerance ||
                        along - wall.DoorWidth * .5f < .1f || along + wall.DoorWidth * .5f > delta.magnitude - .1f)
                    { error = "Architecture door does not retain its clear width and jambs."; return false; }
                }
            }
            if (Stair != null)
            {
                if (Stair.Bounds.width < 2.2f - tolerance || Stair.Run < 6f || Stair.Rise / Stair.Run > 1f ||
                    !Contains(footprint, Stair.Bounds))
                { error = "Architecture stair violates width, run, slope or footprint constraints."; return false; }
                float area = Stair.Bounds.width * Stair.Bounds.height;
                for (int i = 0; i < UpperSlabs.Count; i++)
                {
                    Rect slab = UpperSlabs[i];
                    if (!Contains(footprint, slab) || PositiveOverlap(slab, Stair.Bounds))
                    { error = "Upper slab blocks the stair opening or leaves the footprint."; return false; }
                    for (int j = 0; j < i; j++)
                        if (PositiveOverlap(slab, UpperSlabs[j]))
                        { error = "Upper slabs overlap."; return false; }
                    area += slab.width * slab.height;
                }
                if (Mathf.Abs(area - Size.x * Size.y) > .01f)
                { error = "Upper slabs and the stair opening do not partition the footprint."; return false; }
            }
            if (!AllRoomsReachable())
            { error = "Architecture contains a room disconnected from the entrance or stairs."; return false; }
            if (ServiceDoorCenter.HasValue)
            {
                Vector2 door = ServiceDoorCenter.Value;
                if (Mathf.Abs(door.y - footprint.yMin) > tolerance ||
                    door.x - ServiceDoorWidth * .5f < footprint.xMin + .1f ||
                    door.x + ServiceDoorWidth * .5f > footprint.xMax - .1f)
                { error = "Service door is not a rear exterior opening with clear jambs."; return false; }
                bool entersServiceRoom = false;
                foreach (UrbanPlanRoom room in Rooms)
                    if (room.Floor == 0 && (room.Role == "Stockroom" || room.Role == "Kitchen") &&
                        room.Bounds.Contains(door + Vector2.up * .5f) &&
                        door.x - ServiceDoorWidth * .5f >= room.Bounds.xMin + .1f &&
                        door.x + ServiceDoorWidth * .5f <= room.Bounds.xMax - .1f)
                        entersServiceRoom = true;
                if (!entersServiceRoom)
                { error = "Service door does not open directly into its stockroom or kitchen."; return false; }
                if (!PublicWcReachableWithoutKitchen())
                { error = "Commercial WC is missing or requires traversing a kitchen, stockroom or staff room."; return false; }
            }
            error = null; return true;
        }

        private bool AllRoomsReachable()
        {
            var visited = new bool[Rooms.Count];
            var queue = new Queue<int>();
            int entry = EntryRoomIndex;
            if (entry < 0) return false;
            visited[entry] = true; queue.Enqueue(entry);
            while (queue.Count > 0)
            {
                int current = queue.Dequeue();
                for (int i = 0; i < Rooms.Count; i++)
                {
                    if (visited[i]) continue;
                    bool connected = Rooms[current].Floor == Rooms[i].Floor
                        ? HaveOpenSharedBoundary(Rooms[current], Rooms[i])
                        : StairConnects(Rooms[current], Rooms[i]);
                    if (connected) { visited[i] = true; queue.Enqueue(i); }
                }
            }
            foreach (bool value in visited) if (!value) return false;
            return visited.Length > 0;
        }

        private bool PublicWcReachableWithoutKitchen()
        {
            int entry = EntryRoomIndex;
            if (entry < 0) return false;
            var visited = new bool[Rooms.Count];
            var queue = new Queue<int>();
            visited[entry] = true; queue.Enqueue(entry);
            while (queue.Count > 0)
            {
                int current = queue.Dequeue();
                for (int i = 0; i < Rooms.Count; i++)
                {
                    if (visited[i] || Rooms[i].Floor != 0 || Rooms[i].Role == "Kitchen" ||
                        Rooms[i].Role == "Stockroom" || Rooms[i].Role == "Staff room") continue;
                    if (HaveOpenSharedBoundary(Rooms[current], Rooms[i]))
                    { visited[i] = true; queue.Enqueue(i); }
                }
            }
            bool hasWc = false;
            for (int i = 0; i < Rooms.Count; i++)
                if (Rooms[i].Role == "WC") { hasWc = true; if (!visited[i]) return false; }
            return hasWc;
        }

        private bool StairConnects(UrbanPlanRoom a, UrbanPlanRoom b)
        {
            if (Stair == null) return false;
            if (a.Floor > b.Floor) { UrbanPlanRoom swap = a; a = b; b = swap; }
            return a.Floor == 0 && b.Floor == 1 &&
                a.Bounds.Contains(Stair.Start - (Stair.End-Stair.Start).normalized * .1f) &&
                b.Bounds.Contains(Stair.End + (Stair.End-Stair.Start).normalized * .1f);
        }

        private bool HaveOpenSharedBoundary(UrbanPlanRoom a, UrbanPlanRoom b)
        {
            const float tolerance = .001f;
            Rect x = a.Bounds, y = b.Bounds;
            bool vertical;
            float coordinate, low, high;
            if (Mathf.Abs(x.xMax - y.xMin) < tolerance || Mathf.Abs(y.xMax - x.xMin) < tolerance)
            {
                vertical = true; coordinate = Mathf.Abs(x.xMax - y.xMin) < tolerance ? x.xMax : y.xMax;
                low = Mathf.Max(x.yMin, y.yMin); high = Mathf.Min(x.yMax, y.yMax);
            }
            else if (Mathf.Abs(x.yMax - y.yMin) < tolerance || Mathf.Abs(y.yMax - x.yMin) < tolerance)
            {
                vertical = false; coordinate = Mathf.Abs(x.yMax - y.yMin) < tolerance ? x.yMax : y.yMax;
                low = Mathf.Max(x.xMin, y.xMin); high = Mathf.Min(x.xMax, y.xMax);
            }
            else return false;
            if (high - low < 1.4f) return false;
            var solid = new List<Vector2>();
            foreach (UrbanPlanPartition wall in Partitions)
            {
                if (wall.Floor != a.Floor || (Mathf.Abs(wall.End.x - wall.Start.x) < tolerance) != vertical ||
                    Mathf.Abs((vertical ? wall.Start.x : wall.Start.y) - coordinate) > tolerance) continue;
                float start = vertical ? wall.Start.y : wall.Start.x;
                float end = vertical ? wall.End.y : wall.End.x;
                if (start > end) { float swap = start; start = end; end = swap; }
                if (wall.DoorWidth <= 0) solid.Add(new Vector2(start, end));
                else
                {
                    float center = vertical ? wall.DoorCenter.y : wall.DoorCenter.x;
                    solid.Add(new Vector2(start, center - wall.DoorWidth * .5f));
                    solid.Add(new Vector2(center + wall.DoorWidth * .5f, end));
                }
            }
            solid.Sort((p, q) => p.x.CompareTo(q.x));
            float cursor = low;
            foreach (Vector2 interval in solid)
            {
                if (interval.y <= low || interval.x >= high) continue;
                if (Mathf.Min(interval.x, high) - cursor >= 1.4f - tolerance) return true;
                cursor = Mathf.Max(cursor, interval.y);
            }
            return high - cursor >= 1.4f - tolerance;
        }

        private static bool Contains(Rect outer, Rect inner) => inner.xMin >= outer.xMin - .001f &&
            inner.xMax <= outer.xMax + .001f && inner.yMin >= outer.yMin - .001f && inner.yMax <= outer.yMax + .001f;
        private static bool PositiveOverlap(Rect a, Rect b) => a.xMin < b.xMax - .001f && a.xMax > b.xMin + .001f &&
            a.yMin < b.yMax - .001f && a.yMax > b.yMin + .001f;
    }

    /// <summary>Room programs derived from existing city footprints without rescaling buildings or props.</summary>
    public sealed class UrbanArchitecturePlan
    {
        public static readonly UrbanArchitecturePlan Empty = new UrbanArchitecturePlan(new List<UrbanFloorPlan>(), -1);
        private UrbanArchitecturePlan(List<UrbanFloorPlan> buildings, int parkingParcelIndex)
        { Buildings = buildings.AsReadOnly(); ParkingParcelIndex = parkingParcelIndex; }
        public IReadOnlyList<UrbanFloorPlan> Buildings { get; }
        public int ParkingParcelIndex { get; }
        public UrbanFloorPlan FindForBuilding(int index)
        { foreach (UrbanFloorPlan plan in Buildings) if (plan.BuildingIndex == index) return plan; return null; }

        public static int SelectParkingParcel(IReadOnlyList<UrbanParcelPlacement> parcels, Vector2 entry)
        {
            int selected = -1; float distance = float.PositiveInfinity;
            for (int i = 0; i < parcels.Count; i++)
            {
                UrbanParcelPlacement parcel = parcels[i];
                if (parcel.Size.x < 14f || parcel.Size.y < 12f) continue;
                float candidate = (parcel.Center - entry).sqrMagnitude;
                if (candidate < distance) { selected = i; distance = candidate; }
            }
            if (selected < 0) throw new InvalidOperationException("No parcel can contain the parking prototype at its required physical size.");
            return selected;
        }

        /// <summary>Preserves the original three selections and medical binding, then programs other retail footprints.</summary>
        public static UrbanArchitecturePlan Create(List<UrbanBuildingPlacement> buildings, List<UrbanPoiPlacement> pois,
            Vector2 entry, int parkingParcelIndex)
        {
            var plans = new List<UrbanFloorPlan>();
            var selected = new HashSet<int>();
            Select(UrbanArchitectureProgram.Supermarket, UrbanPoiKind.Retail);
            Select(UrbanArchitectureProgram.PoliceStation, UrbanPoiKind.Office);
            Select(UrbanArchitectureProgram.Residence, UrbanPoiKind.Residential);
            Select(UrbanArchitectureProgram.Cafe, UrbanPoiKind.Retail, new Vector2(12f, 10f));
            Select(UrbanArchitectureProgram.RetailShop, UrbanPoiKind.Retail, new Vector2(12f, 12f));
            // Additional retail buildings reuse a program; geometry/identity choose it, not another random stream.
            for (int i = 0; i < buildings.Count; i++)
            {
                UrbanBuildingPlacement building = buildings[i];
                if (selected.Contains(i) || building.Kind != UrbanPoiKind.Retail || IsMedical(i)) continue;
                int shape = (Mathf.RoundToInt(building.Size.x * .5f) +
                    Mathf.RoundToInt(building.Size.y * .5f) + i) % 3;
                UrbanArchitectureProgram program = shape == 0 ? UrbanArchitectureProgram.Supermarket :
                    shape == 1 ? UrbanArchitectureProgram.Cafe : UrbanArchitectureProgram.RetailShop;
                Assign(i, program, UrbanPoiKind.Retail);
            }
            return new UrbanArchitecturePlan(plans, parkingParcelIndex);

            bool IsMedical(int index)
            {
                foreach (UrbanPoiPlacement poi in pois)
                    if (poi.BuildingIndex == index && poi.Kind == UrbanPoiKind.Medical) return true;
                return buildings[index].Kind == UrbanPoiKind.Medical;
            }

            void Select(UrbanArchitectureProgram program, UrbanPoiKind broadKind, Vector2? preferredSize = null)
            {
                int best = -1; float nearest = float.PositiveInfinity;
                bool bestPreferred = false;
                Vector2 minimum = preferredSize.HasValue ? new Vector2(12f, 10f) : new Vector2(14f, 12f);
                // Keep the review district compact; purpose is assigned before decoration/spawn consumption.
                for (int i = 0; i < buildings.Count; i++)
                {
                    UrbanBuildingPlacement building = buildings[i];
                    if (IsMedical(i) || selected.Contains(i) || building.Size.x < minimum.x || building.Size.y < minimum.y) continue;
                    bool preferred = preferredSize.HasValue && (building.Size - preferredSize.Value).sqrMagnitude < .001f;
                    float distance = (building.Center - entry).sqrMagnitude;
                    if (best < 0 || (preferred && !bestPreferred) || (preferred == bestPreferred && distance < nearest))
                    { best = i; nearest = distance; bestPreferred = preferred; }
                }
                if (best < 0) throw new InvalidOperationException($"No existing {minimum.x}m x {minimum.y}m or larger building can contain {program}; resizing is not permitted.");
                Assign(best, program, broadKind);
            }

            void Assign(int index, UrbanArchitectureProgram program, UrbanPoiKind broadKind)
            {
                selected.Add(index);
                buildings[index] = buildings[index].WithKind(broadKind);
                for (int i = 0; i < pois.Count; i++)
                {
                    UrbanPoiPlacement poi = pois[i];
                    if (poi.BuildingIndex != index) continue;
                    pois[i] = new UrbanPoiPlacement($"core:urban/{broadKind.ToString().ToLowerInvariant()}/parcel_{buildings[index].SourceParcelIndex}",
                        broadKind, index, poi.ContentLocalPosition, poi.ApproachLocalPosition, poi.LocalYawDegrees);
                }
                UrbanFloorPlan plan = BuildFloorPlan(index, program, buildings[index].Size);
                if (!plan.TryValidate(out string error)) throw new InvalidOperationException($"{program}: {error}");
                plans.Add(plan);
            }
        }

        public static UrbanFloorPlan BuildFloorPlan(int buildingIndex, UrbanArchitectureProgram program, Vector2 size)
        {
            if (program == UrbanArchitectureProgram.Supermarket || program == UrbanArchitectureProgram.Cafe ||
                program == UrbanArchitectureProgram.RetailShop)
                return UrbanCommercialFloorPlans.Build(buildingIndex, program, size);
            if (size.x < 14f || size.y < 12f || !float.IsFinite(size.x) || !float.IsFinite(size.y))
                throw new ArgumentException("Prototype floor plans require an unscaled footprint at least 14m x 12m.", nameof(size));
            var rooms = new List<UrbanPlanRoom>(); var walls = new List<UrbanPlanPartition>(); var slabs = new List<Rect>();
            float left = -size.x * .5f + .2f, right = size.x * .5f - .2f;
            float back = -size.y * .5f + .2f, front = size.y * .5f - .2f;
            float low = back + 1.6f, high = front - 2.4f, middle = (low + high) * .5f;
            float stairLeft = right - 2.2f;
            var stair = new UrbanPlanStair(Rect.MinMaxRect(stairLeft, low, right, high), 3.4f);
            for (int floor = 0; floor < 2; floor++)
            {
                rooms.Add(new UrbanPlanRoom(floor, "Entrance lobby", Rect.MinMaxRect(left, high, right, front)));
                rooms.Add(new UrbanPlanRoom(floor, "Central corridor", Rect.MinMaxRect(-1.2f, low, 1.2f, high)));
                rooms.Add(new UrbanPlanRoom(floor, "Rear landing", Rect.MinMaxRect(left, back, right, low)));
                string a = program == UrbanArchitectureProgram.PoliceStation ? (floor == 0 ? "Reception office" : "Detective office") : (floor == 0 ? "Living room" : "Bedroom");
                string b = program == UrbanArchitectureProgram.PoliceStation ? (floor == 0 ? "Interview room" : "Records room") : (floor == 0 ? "Kitchen" : "Study");
                string c = program == UrbanArchitectureProgram.PoliceStation ? (floor == 0 ? "Evidence room" : "Briefing room") : (floor == 0 ? "Utility room" : "Bathroom");
                AddRoom(floor, a, Rect.MinMaxRect(left, middle, -1.2f, high), new Vector2(-1.2f, (middle + high) * .5f));
                AddRoom(floor, b, Rect.MinMaxRect(left, low, -1.2f, middle), new Vector2(-1.2f, (low + middle) * .5f));
                AddRoom(floor, c, Rect.MinMaxRect(1.2f, low, stairLeft, high), new Vector2(1.2f, middle));
                walls.Add(new UrbanPlanPartition(floor, new Vector2(-1.2f, low), new Vector2(-1.2f, middle), new Vector2(-1.2f, (low + middle) * .5f), 1.6f));
                walls.Add(new UrbanPlanPartition(floor, new Vector2(-1.2f, middle), new Vector2(-1.2f, high), new Vector2(-1.2f, (middle + high) * .5f), 1.6f));
                walls.Add(new UrbanPlanPartition(floor, new Vector2(1.2f, low), new Vector2(1.2f, high), new Vector2(1.2f, middle), 1.6f));
                walls.Add(new UrbanPlanPartition(floor, new Vector2(left, middle), new Vector2(-1.2f, middle)));
                foreach (float z in new[] { low, high })
                {
                    walls.Add(new UrbanPlanPartition(floor, new Vector2(left, z), new Vector2(-1.2f, z)));
                    walls.Add(new UrbanPlanPartition(floor, new Vector2(1.2f, z), new Vector2(stairLeft, z)));
                }
                walls.Add(new UrbanPlanPartition(floor, new Vector2(stairLeft, low), new Vector2(stairLeft, high)));
            }
            Rect full = new Rect(-size * .5f, size), hole = stair.Bounds;
            slabs.Add(Rect.MinMaxRect(full.xMin, full.yMin, hole.xMin, full.yMax));
            slabs.Add(Rect.MinMaxRect(hole.xMax, full.yMin, full.xMax, full.yMax));
            slabs.Add(Rect.MinMaxRect(hole.xMin, full.yMin, hole.xMax, hole.yMin));
            slabs.Add(Rect.MinMaxRect(hole.xMin, hole.yMax, hole.xMax, full.yMax));
            return new UrbanFloorPlan(buildingIndex, program, size, rooms, walls, stair, slabs);

            void AddRoom(int floor, string role, Rect rect, Vector2 door) => rooms.Add(new UrbanPlanRoom(floor, role, rect, true, door));
        }

        public ulong StableHash
        {
            get
            {
                var h = new UrbanDecorationHash(); h.Add(ParkingParcelIndex); h.Add(Buildings.Count);
                foreach (UrbanFloorPlan plan in Buildings)
                {
                    h.Add(plan.BuildingIndex); h.Add((int)plan.Program); h.Add(plan.Size.x); h.Add(plan.Size.y);
                    h.Add(plan.StoreyHeight); h.Add(plan.FloorCount); h.Add(plan.Rooms.Count);
                    foreach (UrbanPlanRoom room in plan.Rooms)
                    { h.Add(room.Floor); h.Add(room.Role); AddRect(room.Bounds); h.Add(room.HasDoor ? 1 : 0); AddPoint(room.DoorCenter); }
                    h.Add(plan.Partitions.Count);
                    foreach (UrbanPlanPartition wall in plan.Partitions)
                    { h.Add(wall.Floor); AddPoint(wall.Start); AddPoint(wall.End); AddPoint(wall.DoorCenter); h.Add(wall.DoorWidth); }
                    h.Add(plan.Stair == null ? 0 : 1);
                    if (plan.Stair != null) { AddRect(plan.Stair.Bounds); h.Add(plan.Stair.Rise); }
                    h.Add(plan.ServiceDoorCenter.HasValue ? 1 : 0);
                    if (plan.ServiceDoorCenter.HasValue) { AddPoint(plan.ServiceDoorCenter.Value); h.Add(plan.ServiceDoorWidth); }
                    h.Add(plan.UpperSlabs.Count); foreach (Rect slab in plan.UpperSlabs) AddRect(slab);
                }
                return h.Value;
                void AddPoint(Vector2 p) { h.Add(p.x); h.Add(p.y); }
                void AddRect(Rect r) { h.Add(r.x); h.Add(r.y); h.Add(r.width); h.Add(r.height); }
            }
        }
    }
}
