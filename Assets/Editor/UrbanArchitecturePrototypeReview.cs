using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using UnityEditor;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.SceneManagement;

/// <summary>Bounded observations through the existing Player movement and normal Play camera.</summary>
public static class UrbanArchitecturePrototypeReview
{
    const string Output = "LocalOnly/WorkLoop/urban-architecture27";
    const string CommercialOutput = "LocalOnly/WorkLoop/urban-commercial28";
    const float RootOffset = .5f, DeltaTime = .016f, Tolerance = .2f;
    static readonly string[] Programs = { "supermarket", "police", "residential", "parking" };
    static readonly string[] CommercialPrograms = { "supermarket", "cafe", "retailshop" };

    [Serializable] sealed class ProgramRecord
    {
        public string program;
        public int roomCount, functionalRoomCount, floors, roomsReached, sanitaryFixtureCount;
        public bool entranceReachable, serviceEntranceReachable;
        public List<string> layoutErrors = new List<string>();
        public List<string> propClearanceErrors = new List<string>();
        public List<string> movementErrors = new List<string>();
        public List<string> occlusionErrors = new List<string>();
        public string[] textureAssets;
    }
    [Serializable] sealed class StairRecord
    {
        public string program;
        public bool upReached, downReached, navMeshConnected;
        public Vector3 lowerFoot, upperFoot;
        public List<string> errors = new List<string>();
    }
    [Serializable] sealed class PreservationRecord
    {
        public bool samePlayer, sameCamera, cameraSettingsUnchanged, existingArtReused;
        public Vector3 cameraEulerBefore, cameraEulerAfter;
        public float orthographicSizeBefore, orthographicSizeAfter;
    }
    [Serializable] sealed class Observation
    {
        public int schemaVersion = 1, compileErrors;
        public string scene, method = "Play Mode calls: existing StepMove and CharacterController; no physical keyboard or art approval.";
        public ProgramRecord[] programs;
        public List<StairRecord> stairs = new List<StairRecord>();
        public PreservationRecord preservation = new PreservationRecord();
        public string[] previewFiles;
        public List<string> errors = new List<string>();
        public bool approvedPlansPreserved;
        public int commercialPlanCount;
        public string[] commercialSizes;
        public string approvedPlanComparison = "A27 saved police/residence canonical room, wall and stair geometry rebuilt at the saved size; seed-dependent parcel selection is not asserted unchanged.";
    }

    public static string ValidateAndSave(int compileErrors = 0) => ValidateAndSave(Programs, Output, false, compileErrors);

    public static string ValidateCommercialAndSave(int compileErrors = 0) =>
        ValidateAndSave(CommercialPrograms, CommercialOutput, true, compileErrors);

    static string ValidateAndSave(string[] programs, string output, bool commercial, int compileErrors)
    {
        var shell = RequirePlay();
        var player = shell.PlayerTransform;
        var camera = shell.PlayerCamera;
        Quaternion cameraRotation = camera.transform.rotation;
        float cameraSize = camera.orthographicSize;
        bool orthographic = camera.orthographic;
        var targetTexture = camera.targetTexture;
        float speed = shell.PlayerMovement.speed;
        var record = new Observation
        {
            scene = SceneManager.GetActiveScene().name,
            compileErrors = compileErrors,
            programs = programs.Select(p => new ProgramRecord { program = p }).ToArray(),
            // These are requested output paths, not an assertion that captures already exist.
            previewFiles = programs.Select(p => Path.GetFullPath(output + "/" + p + ".png")).ToArray()
        };
        record.preservation.cameraEulerBefore = camera.transform.eulerAngles;
        record.preservation.orthographicSizeBefore = cameraSize;
        try
        {
            shell.PlayerMovement.speed = 10f;
            Physics.SyncTransforms();
            if (commercial) ObserveCommercialCoverage(record);
            for (int index = 0; index < record.programs.Length; index++)
            {
                ProgramRecord program = record.programs[index];
                try
                {
                    if (program.program == "parking") ObserveParking(shell, program);
                    else ObserveBuilding(shell, program, record.stairs, commercial);
                }
                catch (Exception error) { program.layoutErrors.Add(error.GetType().Name + ": " + error.Message); }
            }
        }
        catch (Exception error) { record.errors.Add(error.GetType().Name + ": " + error.Message); }
        finally
        {
            if (shell != null && shell.PlayerMovement != null)
            {
                shell.PlayerMovement.StepMove(Vector2.zero, DeltaTime, false);
                shell.PlayerMovement.speed = speed;
            }
            var current = PersistentGameplayShell.Instance;
            record.preservation.samePlayer = current != null && current.PlayerTransform == player;
            record.preservation.sameCamera = current != null && current.PlayerCamera == camera;
            record.preservation.cameraSettingsUnchanged = camera != null &&
                Quaternion.Angle(cameraRotation, camera.transform.rotation) < .001f &&
                Mathf.Abs(cameraSize - camera.orthographicSize) < .0001f &&
                orthographic == camera.orthographic && targetTexture == camera.targetTexture;
            record.preservation.existingArtReused = record.programs.All(p => p.textureAssets != null && p.textureAssets.Length > 0);
            if (camera != null)
            {
                record.preservation.cameraEulerAfter = camera.transform.eulerAngles;
                record.preservation.orthographicSizeAfter = camera.orthographicSize;
            }
            Directory.CreateDirectory(output);
            File.WriteAllText(output + "/readback.json", JsonUtility.ToJson(record, true));
        }
        return Path.GetFullPath(output + "/readback.json");
    }

    static void ObserveBuilding(PersistentGameplayShell shell, ProgramRecord record, List<StairRecord> stairs, bool commercial = false)
    {
        var building = FindBuilding(record.program);
        var plan = building.FloorPlan;
        record.roomCount = plan.Rooms.Count;
        record.functionalRoomCount = plan.Rooms.Count(r => r.HasDoor ||
            (r.Role != "Entrance lobby" && r.Role != "Central corridor" && r.Role != "Rear landing" && !r.Role.Contains("corridor")));
        record.floors = plan.FloorCount;
        record.sanitaryFixtureCount = building.SanitaryFixtureCount;
        record.textureAssets = TextureAssets(building.transform);
        if (!plan.TryValidate(out string layoutError)) record.layoutErrors.Add(layoutError);
        record.propClearanceErrors.AddRange(building.PropClearanceErrors);
        foreach (Collider prop in building.PlannedPropColliders)
        foreach (Collider wall in building.WallColliders)
        {
            if (prop == null || wall == null || !prop.bounds.Intersects(wall.bounds)) continue;
            if (Physics.ComputePenetration(prop, prop.transform.position, prop.transform.rotation,
                    wall, wall.transform.position, wall.transform.rotation, out _, out float distance) && distance > .001f)
                record.propClearanceErrors.Add(prop.name + " overlaps " + wall.name + " by " + distance.ToString("F4") + "m");
        }
        for (int i = 0; i < building.PlannedPropColliders.Count; i++)
        for (int j = 0; j < i; j++)
        {
            Collider first = building.PlannedPropColliders[i], second = building.PlannedPropColliders[j];
            if (first == null || second == null || !first.bounds.Intersects(second.bounds)) continue;
            if (Physics.ComputePenetration(first, first.transform.position, first.transform.rotation,
                    second, second.transform.position, second.transform.rotation, out _, out float distance) && distance > .001f)
                record.propClearanceErrors.Add(first.name + " overlaps fixture " + second.name + " by " + distance.ToString("F4") + "m");
        }
        StairRecord stairRecord = null;
        if (plan.Stair != null)
        {
            stairRecord = new StairRecord { program = record.program };
            stairs.Add(stairRecord);
            Vector2 direction = (plan.Stair.End - plan.Stair.Start).normalized;
            stairRecord.lowerFoot = Foot(building, plan.Stair.Start - direction * .65f, 0);
            stairRecord.upperFoot = Foot(building, plan.Stair.End + direction * .65f, 1);
        }
        // DoorOutside already stores the player-root offset; never add it a second time.
        if (!shell.PlayerMovement.TryTeleport(building.DoorOutside, shell.PlayerTransform.rotation, out string teleportError))
        { record.movementErrors.Add(teleportError); return; }
        Settle(shell);
        CheckVisibility(-1);
        record.entranceReachable = Walk(shell, building.DoorInside - Vector3.up * RootOffset, "entrance", record.movementErrors, out _);
        if (!record.entranceReachable) return;
        CheckVisibility(0);
        if (stairRecord != null)
        {
            // Diagnose the reported vertical-access failure before spending movement calls on rooms.
            if (!Walk(shell, stairRecord.lowerFoot, "lower landing", stairRecord.errors, out _)) return;
            stairRecord.upReached = Walk(shell, stairRecord.upperFoot, "stairs up", stairRecord.errors, out bool upNav);
            stairRecord.navMeshConnected = upNav;
            if (!stairRecord.upReached) return;
            CheckVisibility(1);
            stairRecord.downReached = Walk(shell, stairRecord.lowerFoot, "stairs down", stairRecord.errors, out bool downNav);
            stairRecord.navMeshConnected &= downNav;
            if (!stairRecord.downReached) return;
        }
        if (!VisitRooms(0)) return;
        if (stairRecord != null && !VisitRooms(1)) return;
        if (commercial)
        {
            if (!plan.ServiceDoorCenter.HasValue) record.movementErrors.Add("Missing service entrance in commercial plan.");
            else
            {
                Vector2 door = plan.ServiceDoorCenter.Value;
                Vector2 outward = ExteriorNormal(plan.Size, door);
                bool insideReached = Walk(shell, Foot(building, door - outward * 1.1f, 0),
                    "service door inner approach", record.movementErrors, out _);
                record.serviceEntranceReachable = insideReached && Walk(shell, Foot(building, door + outward * 1.4f, 0),
                    "service door to exterior", record.movementErrors, out _);
                if (!record.serviceEntranceReachable) return;
            }
        }
        if (Walk(shell,building.DoorOutside-Vector3.up*RootOffset,"return through entrance",record.movementErrors,out _))
            CheckVisibility(-1);

        bool VisitRooms(int floor)
        {
            foreach (UrbanPlanRoom room in plan.Rooms)
            {
                if (room.Floor != floor) continue;
                Vector2 approach=room.HasDoor?room.DoorCenter+(room.Bounds.center-room.DoorCenter).normalized*.9f:
                    (floor == 0 && plan.Rooms[plan.EntryRoomIndex].Equals(room) ? plan.EntryPoint : room.Bounds.center);
                if (!Walk(shell, Foot(building, approach, floor),
                        "F" + floor + " " + room.Role, record.movementErrors, out _)) return false;
                record.roomsReached++;
            }
            return true;
        }
        void CheckVisibility(int floor)
        {
            var fader=UnityEngine.Object.FindFirstObjectByType<UrbanOcclusionFader>();
            if(fader==null){record.occlusionErrors.Add("Missing existing occlusion owner");return;}
            fader.EvaluateVisibility(shell.PlayerCamera,shell.PlayerTransform.position,.3f);
            foreach(var renderer in building.GetComponentsInChildren<Renderer>())
            {
                if(!renderer.name.StartsWith("Floor ",StringComparison.Ordinal))continue;
                int level=int.Parse(renderer.name.Substring(6));
                bool expected=floor<0||level<=floor;
                if(renderer.enabled!=expected)record.occlusionErrors.Add(renderer.name+" visible="+renderer.enabled+" expected="+expected);
            }
            if(building.RoofRenderer.enabled!=(floor<0))record.occlusionErrors.Add("Roof cutaway mismatch on floor "+floor);
            foreach(var collider in building.GetComponentsInChildren<Collider>())
                if(!collider.enabled)record.occlusionErrors.Add("Visibility disabled physical collider "+collider.name);
        }
    }

    static Vector2 ExteriorNormal(Vector2 size, Vector2 door)
    {
        Vector2 half = size * .5f;
        float xDistance = Mathf.Abs(Mathf.Abs(door.x) - half.x);
        float yDistance = Mathf.Abs(Mathf.Abs(door.y) - half.y);
        return xDistance < yDistance ? new Vector2(Mathf.Sign(door.x), 0) : new Vector2(0, Mathf.Sign(door.y));
    }

    static void ObserveCommercialCoverage(Observation record)
    {
        var generator = UnityEngine.Object.FindFirstObjectByType<ProceduralUrbanMapGenerator>();
        if (generator == null || generator.CurrentLayout == null)
            throw new InvalidOperationException("Active city layout is missing.");
        var plans = generator.CurrentLayout.Architecture.Buildings.Where(p =>
            p.Program == UrbanArchitectureProgram.Supermarket || p.Program == UrbanArchitectureProgram.Cafe ||
            p.Program == UrbanArchitectureProgram.RetailShop).ToArray();
        record.commercialPlanCount = plans.Length;
        record.commercialSizes = plans.Select(p => p.Size.x.ToString("G", System.Globalization.CultureInfo.InvariantCulture) + "x" +
            p.Size.y.ToString("G", System.Globalization.CultureInfo.InvariantCulture)).Distinct().OrderBy(s => s).ToArray();
        foreach (UrbanFloorPlan plan in plans)
            if (!plan.TryValidate(out string error)) record.errors.Add("Building " + plan.BuildingIndex + ": " + error);
        string previousPath = Output + "/floorplans.json";
        if (!File.Exists(previousPath)) { record.errors.Add("Missing approved A27 canonical plans."); return; }
        var previous = JsonUtility.FromJson<PlansExport>(File.ReadAllText(previousPath));
        if (previous == null || previous.plans == null) { record.errors.Add("Unreadable A27 canonical plans."); return; }
        bool preserved = true;
        foreach (string program in new[] { "police", "residential" })
        {
            var matches = previous.plans.Where(p => p.program == program).ToArray();
            if (matches.Length != 1) { record.errors.Add("Expected one approved " + program + " canonical plan."); preserved = false; continue; }
            PlanExport saved = matches[0];
            var rebuilt = UrbanArchitecturePlan.BuildFloorPlan(0, ProgramKind(program), saved.size);
            if (!SameGeometry(saved, rebuilt)) { record.errors.Add("Approved " + program + " canonical geometry changed."); preserved = false; }
        }
        record.approvedPlansPreserved = preserved;
    }

    static bool SameGeometry(PlanExport saved, UrbanFloorPlan current)
    {
        if (!Same(saved.size, current.Size) || saved.floors != current.FloorCount || saved.rooms.Count != current.Rooms.Count ||
            saved.walls.Count != current.Partitions.Count) return false;
        for (int i = 0; i < saved.rooms.Count; i++)
        {
            RoomExport a = saved.rooms[i]; UrbanPlanRoom b = current.Rooms[i];
            if (a.role != b.Role || a.floor != b.Floor || a.hasDoor != b.HasDoor || !Same(a.door, b.DoorCenter) || !Same(a.rect, b.Bounds)) return false;
        }
        for (int i = 0; i < saved.walls.Count; i++)
        {
            WallExport a = saved.walls[i]; UrbanPlanPartition b = current.Partitions[i];
            if (a.floor != b.Floor || !Same(a.start, b.Start) || !Same(a.end, b.End) || !Same(a.door, b.DoorCenter) ||
                Mathf.Abs(a.opening - b.DoorWidth) > .0001f) return false;
        }
        return current.Stair != null && Same(saved.stair, current.Stair.Bounds) &&
            Same(saved.stairStart, current.Stair.Start) && Same(saved.stairEnd, current.Stair.End);
    }

    static bool Same(Vector2 a, Vector2 b) => (a - b).sqrMagnitude <= .00000001f;
    static bool Same(Rect a, Rect b) => Same(a.position, b.position) && Same(a.size, b.size);

    [Serializable] sealed class PlanExport { public string program; public int buildingIndex; public Vector2 size; public Vector3 world; public int floors; public List<RoomExport> rooms=new List<RoomExport>(); public List<WallExport> walls=new List<WallExport>(); public Vector2 stairStart,stairEnd,entry,serviceDoor; public bool hasServiceDoor; public float serviceDoorWidth; public Rect stair; }
    [Serializable] sealed class RoomExport { public string role; public int floor; public Rect rect; public Vector2 door; public bool hasDoor; }
    [Serializable] sealed class WallExport { public int floor; public Vector2 start,end,door; public float opening; }
    [Serializable] sealed class PlansExport {public List<PlanExport> plans=new List<PlanExport>();}
    public static string ExportPlans() => ExportPlans(Programs.Take(3), Output);
    public static string ExportCommercialPlans() => ExportPlans(CommercialPrograms, CommercialOutput);

    static string ExportPlans(IEnumerable<string> programs, string output)
    {
        RequirePlay();var data=new PlansExport();
        foreach(string id in programs)
        {
            var building=FindBuilding(id);var plan=building.FloorPlan;
            var item=new PlanExport{program=id,buildingIndex=plan.BuildingIndex,size=plan.Size,world=building.transform.position,floors=plan.FloorCount,
                entry=plan.EntryPoint,hasServiceDoor=plan.ServiceDoorCenter.HasValue,
                serviceDoor=plan.ServiceDoorCenter.GetValueOrDefault(),serviceDoorWidth=plan.ServiceDoorWidth};
            foreach(var room in plan.Rooms)item.rooms.Add(new RoomExport{role=room.Role,floor=room.Floor,rect=room.Bounds,door=room.DoorCenter,hasDoor=room.HasDoor});
            foreach(var wall in plan.Partitions)item.walls.Add(new WallExport{floor=wall.Floor,start=wall.Start,end=wall.End,door=wall.DoorCenter,opening=wall.DoorWidth});
            if(plan.Stair!=null){item.stair=plan.Stair.Bounds;item.stairStart=plan.Stair.Start;item.stairEnd=plan.Stair.End;}
            data.plans.Add(item);
        }
        Directory.CreateDirectory(output);string path=output+"/floorplans.json";File.WriteAllText(path,JsonUtility.ToJson(data,true));return Path.GetFullPath(path);
    }

    static void ObserveParking(PersistentGameplayShell shell, ProgramRecord record)
    {
        var lot = UnityEngine.Object.FindFirstObjectByType<UrbanParkingLot>();
        if (lot == null) throw new InvalidOperationException("Parking prototype is missing.");
        record.textureAssets = TextureAssets(lot.transform);
        if (lot.StallCount < 1 || lot.AisleWidth < 6f) record.layoutErrors.Add("Parking stalls or six-metre aisle are missing.");
        if (!shell.PlayerMovement.TryTeleport(lot.Entrance, shell.PlayerTransform.rotation, out string error))
        { record.movementErrors.Add(error); return; }
        Settle(shell);
        var strip = lot.transform.Find("Pedestrian strip");
        if (strip == null) throw new InvalidOperationException("Pedestrian strip is missing.");
        Vector3 target = strip.GetComponent<Renderer>().bounds.center;
        record.entranceReachable = Walk(shell, target, "parking entrance to pedestrian strip", record.movementErrors, out _);
    }

    static Vector3 Foot(EnterableSpriteBuilding building, Vector2 position, int floor) =>
        building.transform.TransformPoint(new Vector3(position.x,
            EnterableSpriteBuilding.FloorLift + floor * building.FloorPlan.StoreyHeight, position.y));

    static void Settle(PersistentGameplayShell shell)
    {
        for (int i = 0; i < 12; i++) shell.PlayerMovement.StepMove(Vector2.zero, DeltaTime, false);
        Physics.SyncTransforms();
    }

    static bool Walk(PersistentGameplayShell shell, Vector3 targetFoot, string label, List<string> errors, out bool navConnected)
    {
        navConnected = false;
        Vector3 sourceFoot = shell.PlayerTransform.position - Vector3.up * RootOffset;
        if (!Sample(sourceFoot, out Vector3 from) || !Sample(targetFoot, out Vector3 to))
        { errors.Add(label + ": no same-floor NavMesh sample within 0.35m; from=" + sourceFoot + " to=" + targetFoot); return false; }
        var path = new NavMeshPath();
        if (!NavMesh.CalculatePath(from, to, NavMesh.AllAreas, path) || path.status != NavMeshPathStatus.PathComplete)
        { errors.Add(label + ": NavMesh path is " + path.status); return false; }
        navConnected = true;
        for (int corner = 1; corner < path.corners.Length; corner++)
        {
            Vector3 rootTarget = path.corners[corner] + Vector3.up * RootOffset;
            bool reached = false;
            for (int step = 0; step < 500; step++)
            {
                Vector3 delta = rootTarget - shell.PlayerTransform.position;
                Vector3 horizontal = Vector3.ProjectOnPlane(delta, Vector3.up);
                if (horizontal.magnitude <= Tolerance && Mathf.Abs(delta.y) <= Tolerance)
                { reached = true; break; }
                Vector3 right = Vector3.ProjectOnPlane(shell.PlayerCamera.transform.right, Vector3.up).normalized;
                Vector3 forward = Vector3.ProjectOnPlane(shell.PlayerCamera.transform.forward, Vector3.up);
                forward = (forward - right * Vector3.Dot(forward, right)).normalized;
                Vector3 direction = horizontal.magnitude > .03f ? horizontal.normalized : Vector3.zero;
                shell.PlayerMovement.StepMove(new Vector2(Vector3.Dot(direction, right), Vector3.Dot(direction, forward)), DeltaTime, false);
                Physics.SyncTransforms();
            }
            if (!reached)
            { errors.Add(label + ": StepMove timeout at corner " + corner + "; actual=" + shell.PlayerTransform.position + "; target=" + rootTarget); return false; }
        }
        Vector3 finalDelta = shell.PlayerTransform.position - (targetFoot + Vector3.up * RootOffset);
        if (Vector3.ProjectOnPlane(finalDelta, Vector3.up).magnitude > .35f || Mathf.Abs(finalDelta.y) > Tolerance)
        { errors.Add(label + ": final root differs from expected foot+0.5m: " + finalDelta); return false; }
        return true;
    }

    static bool Sample(Vector3 point, out Vector3 sampled)
    {
        bool found = NavMesh.SamplePosition(point, out NavMeshHit hit, .35f, NavMesh.AllAreas);
        sampled = hit.position;
        return found && Mathf.Abs(sampled.y - point.y) <= Tolerance;
    }

    static string[] TextureAssets(Transform root)
    {
        var result = new SortedSet<string>();
        foreach (Renderer renderer in root.GetComponentsInChildren<Renderer>(true))
        foreach (Material material in renderer.sharedMaterials)
        {
            if (material == null) continue;
            foreach (string property in material.GetTexturePropertyNames())
            {
                string path = AssetDatabase.GetAssetPath(material.GetTexture(property));
                if (!string.IsNullOrEmpty(path) && path.StartsWith("Assets/", StringComparison.Ordinal)) result.Add(path);
            }
        }
        return result.ToArray();
    }

    static EnterableSpriteBuilding FindBuilding(string program)
    {
        UrbanArchitectureProgram expected = ProgramKind(program);
        var generator = UnityEngine.Object.FindFirstObjectByType<ProceduralUrbanMapGenerator>();
        var representative = generator?.CurrentLayout?.Architecture?.Buildings.FirstOrDefault(p => p.Program == expected);
        if (representative == null) throw new InvalidOperationException("No planned representative for " + program);
        var found = UnityEngine.Object.FindObjectsByType<EnterableSpriteBuilding>(FindObjectsSortMode.None)
            .Where(b => b.FloorPlan != null && b.FloorPlan.Program == expected && b.FloorPlan.BuildingIndex == representative.BuildingIndex).ToArray();
        if (found.Length != 1) throw new InvalidOperationException("Expected one representative " + program + ", found " + found.Length);
        return found[0];
    }

    static UrbanArchitectureProgram ProgramKind(string program) => program == "supermarket" ? UrbanArchitectureProgram.Supermarket :
        program == "police" ? UrbanArchitectureProgram.PoliceStation :
        program == "residential" ? UrbanArchitectureProgram.Residence :
        program == "cafe" ? UrbanArchitectureProgram.Cafe :
        program == "retailshop" ? UrbanArchitectureProgram.RetailShop : throw new ArgumentException("Unknown program: " + program);

    static PersistentGameplayShell RequirePlay()
    {
        var shell = PersistentGameplayShell.Instance;
        if (!EditorApplication.isPlaying || SceneManager.GetActiveScene().name != "GameMapTest" ||
            shell == null || shell.PlayerTransform == null || shell.PlayerCamera == null || shell.PlayerMovement == null)
            throw new InvalidOperationException("Normal GameMapTest Play with the persistent Player is required.");
        return shell;
    }

    [MenuItem("Tools/Urban Architecture/Inspect Supermarket")] public static void InspectSupermarket() => Inspect("supermarket");
    [MenuItem("Tools/Urban Architecture/Inspect Police Ground")] public static void InspectPoliceGround() => Inspect("police");
    [MenuItem("Tools/Urban Architecture/Inspect Police Upper")] public static void InspectPoliceUpper() => Inspect("police", 1);
    [MenuItem("Tools/Urban Architecture/Inspect Residence")] public static void InspectResidence() => Inspect("residential");
    [MenuItem("Tools/Urban Architecture/Inspect Parking")] public static void InspectParking() => Inspect("parking");
    [MenuItem("Tools/Urban Architecture/Inspect Cafe")] public static void InspectCafe() => Inspect("cafe");
    [MenuItem("Tools/Urban Architecture/Inspect Retail Shop")] public static void InspectRetailShop() => Inspect("retailshop");

    public static void Inspect(string program, int floor = 0)
    {
        var shell = RequirePlay();
        Vector3 rootTarget;
        if (program == "parking")
        {
            var lot = UnityEngine.Object.FindFirstObjectByType<UrbanParkingLot>();
            if (lot == null) throw new InvalidOperationException("Parking missing.");
            rootTarget = lot.Entrance;
        }
        else
        {
            var building = FindBuilding(program);
            if (floor == 0)
                rootTarget = Foot(building, building.FloorPlan.EntryPoint, floor) + Vector3.up * RootOffset;
            else
            {
                var candidates = building.FloorPlan.Rooms.Where(r => r.Floor == floor && r.Role == "Entrance lobby").ToArray();
                if (candidates.Length != 1) throw new InvalidOperationException("Requested floor has no unique public room.");
                rootTarget = Foot(building, candidates[0].Bounds.center, floor) + Vector3.up * RootOffset;
            }
        }
        if (!shell.PlayerMovement.TryTeleport(rootTarget, shell.PlayerTransform.rotation, out string error))
            throw new InvalidOperationException(error);
        Settle(shell);
        // CameraFollow and the registered occlusion fader update normally on the next Play frame.
    }

    static string capturePath;
    static int captureFrame;
    static double captureStarted;
    static bool screenshotRequested, oldRunInBackground;

    public static string Capture(string program) => Capture(program, Programs, Output);

    public static string CaptureCommercial(string program)
    {
        if (!CommercialPrograms.Contains(program)) throw new ArgumentException("Unknown commercial program: " + program);
        return Capture(program, CommercialPrograms, CommercialOutput, true);
    }

    static string Capture(string program, string[] programs, string output, bool inspect = false)
    {
        var shell = RequirePlay();
        if (!programs.Contains(program)) throw new ArgumentException("Unknown program: " + program);
        if (capturePath != null) throw new InvalidOperationException("A capture is already pending.");
        string path = Path.GetFullPath(output + "/" + program + ".png");
        if (File.Exists(path)) throw new InvalidOperationException("Previous preview is preserved: " + path);
        if (shell.PlayerCamera.targetTexture != null) throw new InvalidOperationException("Expected the normal display camera.");
        if (inspect) Inspect(program);
        Directory.CreateDirectory(output);
        capturePath = path; captureFrame = Time.frameCount; captureStarted = EditorApplication.timeSinceStartup;
        screenshotRequested = false; oldRunInBackground = Application.runInBackground;
        Application.runInBackground = true;
        EditorApplication.update += CaptureUpdate;
        return path;
    }

    static void CaptureUpdate()
    {
        if (!EditorApplication.isPlaying || EditorApplication.timeSinceStartup - captureStarted > 10)
        { Debug.LogWarning("Urban architecture capture stopped before a confirmed PNG: " + capturePath); FinishCapture(); return; }
        if (!screenshotRequested && Time.frameCount >= captureFrame + 5)
        { ScreenCapture.CaptureScreenshot(capturePath, 1); screenshotRequested = true; }
        if (screenshotRequested && File.Exists(capturePath))
        { Debug.Log("Urban architecture normal Game View saved: " + capturePath); FinishCapture(); return; }
        EditorApplication.QueuePlayerLoopUpdate();
    }

    static void FinishCapture()
    {
        EditorApplication.update -= CaptureUpdate;
        Application.runInBackground = oldRunInBackground;
        capturePath = null;
    }
}
