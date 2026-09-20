using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public sealed partial class EnterableSpriteBuilding
    {
        public int SanitaryFixtureCount { get; private set; }
        private readonly List<Rect> commercialOccupied = new List<Rect>();
        private Material fixtureBodyMaterial, fixtureDetailMaterial;

        private static bool IsCommercialPlan(UrbanFloorPlan plan) =>
            plan.Program == UrbanArchitectureProgram.Supermarket ||
            plan.Program == UrbanArchitectureProgram.Cafe || plan.Program == UrbanArchitectureProgram.RetailShop;

        // Role -> fixed metric module -> free boundary slot. No prop is scaled to force a fit.
        private void PopulateCommercialRoom(UrbanPlanRoom room, float y, IsometricUrbanStyle style,
            UrbanBuildingPrefab catalog, List<Renderer> contents)
        {
            switch (room.Role)
            {
                case "WC":
                    RequiredFixture("Toilet", new Vector3(.60f, .85f, .85f));
                    RequiredFixture("Wash basin", new Vector3(.60f, .90f, .55f));
                    break;
                case "Kitchen":
                    RequiredFixture("Preparation sink", new Vector3(1.20f, .90f, .65f));
                    RequiredFixture("Preparation counter", new Vector3(1.20f, .90f, .65f));
                    break;
                case "Stockroom":
                    PlaceCatalogAtWall("storage_shelf");
                    break;
                case "Staff room":
                    PlaceCatalogAtWall("office_desk");
                    break;
                case "Service counter":
                    RequiredFixture("Order counter", new Vector3(1.80f, 1f, .70f));
                    break;
                case "Dining area":
                    PlaceDiningSets();
                    break;
                case "Sales floor":
                    PlaceShelves();
                    RequiredFixture("Checkout counter", new Vector3(1.80f, 1f, .70f));
                    break;
            }

            void RequiredFixture(string id, Vector3 size)
            {
                if (!TryWallSlot(room, size, out Vector2 position, out float yaw))
                { PropClearanceErrors.Add(room.Role + ": no clear slot for " + id); return; }
                CreateCommercialFixture(id, position, yaw, size, y, style, contents);
                if (id == "Toilet" || id == "Wash basin") SanitaryFixtureCount++;
            }

            void PlaceCatalogAtWall(string id)
            {
                var source = catalog == null ? null : Array.Find(catalog.propPrefabs, p => p != null && p.catalogId == id);
                if (source == null) { PropClearanceErrors.Add(room.Role + ": missing catalog " + id); return; }
                if (!TryWallSlot(room, source.PlacementSize, out Vector2 position, out float yaw))
                { PropClearanceErrors.Add(room.Role + ": no clear slot for " + id); return; }
                AddCatalog(source, position, yaw);
            }

            void AddCatalog(UrbanBuildingProp source, Vector2 position, float yaw)
            {
                var prop = Instantiate(source, transform, false);
                prop.name = room.Role + "/" + source.catalogId;
                prop.transform.localPosition = new Vector3(position.x, y, position.y);
                prop.transform.localRotation = Quaternion.Euler(0, yaw, 0);
                var box = prop.GetComponent<BoxCollider>();
                box.center = Vector3.up * source.PlacementSize.y * .5f;
                box.size = source.PlacementSize;
                MarkNotWalkable(prop.gameObject);
                PlannedPropColliders.Add(box);
                contents.AddRange(prop.GetComponentsInChildren<Renderer>());
            }

            void PlaceShelves()
            {
                var source = catalog == null ? null : Array.Find(catalog.propPrefabs, p => p != null && p.catalogId == "retail_shelf");
                if (source == null) { PropClearanceErrors.Add("Missing retail shelf catalog module"); return; }
                Rect r = room.Bounds;
                Vector3 size = source.PlacementSize;
                // Modules occupy two side bands; the doorway-centred aisle remains at least 2.4m wide.
                int rows = Mathf.Max(1, Mathf.FloorToInt((r.height - 2.6f) / 2.2f));
                for (int row = 0; row < rows; row++)
                foreach (int side in new[] { -1, 1 })
                {
                    float x = side < 0 ? r.xMin + .65f + size.x * .5f : r.xMax - .65f - size.x * .5f;
                    var p = new Vector2(x, r.yMin + 1.1f + row * 2.2f);
                    if (Mathf.Abs(x) - size.x * .5f < 1.2f || !Reserve(room, p, size, 0)) continue;
                    AddCatalog(source, p, 0);
                }
            }

            void PlaceDiningSets()
            {
                Rect r = room.Bounds;
                var size = new Vector3(1.1f, .85f, 2.1f);
                int count = 0;
                foreach (float x in new[] { r.xMin + .35f + size.x * .5f, r.xMax - .35f - size.x * .5f })
                {
                    var p = new Vector2(x, r.yMin + .35f + size.z * .5f);
                    if (Mathf.Abs(x) - size.x * .5f < 1.2f || !Reserve(room, p, size, 0)) continue;
                    CreateCommercialFixture("Table and two chairs", p, 0, size, y, style, contents); count++;
                }
                if (count == 0) PropClearanceErrors.Add("Dining area has no clear seating module");
            }
        }

        private bool TryWallSlot(UrbanPlanRoom room, Vector3 size, out Vector2 position, out float yaw)
        {
            Rect r = room.Bounds;
            // Farthest wall first: sanitary fixtures face the entrance; all candidates derive from room bounds.
            Vector2 door = room.HasDoor ? room.DoorCenter : new Vector2(0, r.yMax);
            var sides = new[] { 0, 1, 2, 3 }; // back, right, front, left
            Vector2[] mid = { new Vector2(r.center.x,r.yMin),new Vector2(r.xMax,r.center.y),
                new Vector2(r.center.x,r.yMax),new Vector2(r.xMin,r.center.y) };
            Array.Sort(sides, (a,b) => (mid[b]-door).sqrMagnitude.CompareTo((mid[a]-door).sqrMagnitude));
            foreach (int side in sides)
            {
                yaw = -90f * side;
                bool alongX = side % 2 == 0;
                Vector2 half = alongX ? new Vector2(size.x,size.z)*.5f : new Vector2(size.z,size.x)*.5f;
                foreach (int end in new[] { -1, 1 })
                {
                    float x = alongX ? (end < 0 ? r.xMin+.22f+half.x : r.xMax-.22f-half.x) :
                        side == 1 ? r.xMax-.22f-half.x : r.xMin+.22f+half.x;
                    float z = alongX ? (side == 0 ? r.yMin+.22f+half.y : r.yMax-.22f-half.y) :
                        end < 0 ? r.yMin+.22f+half.y : r.yMax-.22f-half.y;
                    position = new Vector2(x,z);
                    if (Reserve(room, position, size, yaw)) return true;
                }
            }
            position = default; yaw = 0; return false;
        }

        private bool Reserve(UrbanPlanRoom room, Vector2 position, Vector3 size, float yaw)
        {
            bool turned = Mathf.Abs(Mathf.Sin(yaw*Mathf.Deg2Rad)) > .5f;
            Vector2 extent = turned ? new Vector2(size.z,size.x) : new Vector2(size.x,size.z);
            Rect footprint = new Rect(position-extent*.5f, extent);
            Rect safeRoom = Rect.MinMaxRect(room.Bounds.xMin+.10f,room.Bounds.yMin+.10f,
                room.Bounds.xMax-.10f,room.Bounds.yMax-.10f);
            if (!safeRoom.Contains(footprint.min) || !safeRoom.Contains(footprint.max)) return false;
            Rect clearance = UrbanBuildingDecorationPlanner.Expand(footprint, .75f);
            // Open/public zones also border doors: use the wall data, not only this room's label/HasDoor.
            foreach (UrbanPlanPartition wall in FloorPlan.Partitions)
            {
                if (wall.Floor != room.Floor || wall.DoorWidth <= 0) continue;
                bool horizontal = Mathf.Abs(wall.End.x-wall.Start.x) > .01f;
                Vector2 openingArea = horizontal ? new Vector2(wall.DoorWidth,2.8f) : new Vector2(2.8f,wall.DoorWidth);
                if (footprint.Overlaps(new Rect(wall.DoorCenter-openingArea*.5f,openingArea))) return false;
            }
            if (room.HasDoor)
            {
                Vector2 inside = room.DoorCenter + (room.Bounds.center-room.DoorCenter).normalized*.9f;
                if (clearance.Contains(room.DoorCenter) || clearance.Contains(inside)) return false;
            }
            else if (clearance.Contains(room.Bounds.center)) return false;
            if (clearance.Contains(FloorPlan.EntryPoint)) return false;
            if (FloorPlan.ServiceDoorCenter.HasValue)
            {
                Vector2 delivery = FloorPlan.ServiceDoorCenter.Value;
                var access = new Rect(delivery.x-FloorPlan.ServiceDoorWidth*.5f,delivery.y,
                    FloorPlan.ServiceDoorWidth,1.9f);
                if (footprint.Overlaps(access)) return false;
            }
            Rect separation = UrbanBuildingDecorationPlanner.Expand(footprint,.12f);
            foreach (Rect occupied in commercialOccupied) if (separation.Overlaps(occupied)) return false;
            commercialOccupied.Add(footprint);
            return true;
        }

        // Basic fixtures are explicitly geometry prototypes. They do not replace the authored pixel asset catalog.
        private void CreateCommercialFixture(string id, Vector2 p, float yaw, Vector3 size, float y,
            IsometricUrbanStyle style, List<Renderer> contents)
        {
            if (fixtureBodyMaterial == null)
            {
                fixtureBodyMaterial = Own(style.CreateAtlasMaterial(style.concrete.texture,false,"Commercial fixture body",Color.white));
                fixtureDetailMaterial = Own(style.CreateAtlasMaterial(style.concrete.texture,false,"Commercial fixture detail",new Color(.34f,.29f,.24f)));
            }
            var body = new MetricAtlasMesh(); var detail = new MetricAtlasMesh();
            if (id == "Toilet")
            {
                Box(body,0,.20f,.05f,.30f,.40f,.40f);
                Box(body,0,.57f,-.30f,.55f,.56f,.22f);
                Box(body,-.24f,.47f,.08f,.10f,.12f,.60f); Box(body,.24f,.47f,.08f,.10f,.12f,.60f);
                Box(body,0,.47f,-.17f,.40f,.12f,.10f); Box(body,0,.47f,.33f,.40f,.12f,.10f);
                Box(detail,0,.405f,.08f,.38f,.025f,.38f);
            }
            else if (id == "Wash basin" || id == "Preparation sink")
            {
                float w=size.x,d=size.z;
                Box(body,0,.38f,0,w-.12f,.76f,d-.10f);
                Box(body,0,.84f,-d*.5f+.055f,w,.12f,.11f); Box(body,0,.84f,d*.5f-.055f,w,.12f,.11f);
                Box(body,-w*.5f+.055f,.84f,0,.11f,.12f,d-.22f); Box(body,w*.5f-.055f,.84f,0,.11f,.12f,d-.22f);
                Box(detail,0,.77f,0,w-.22f,.02f,d-.22f);
            }
            else if (id == "Table and two chairs")
            {
                Box(detail,0,.73f,0,.9f,.08f,.8f);
                foreach(float x in new[]{-.34f,.34f}) foreach(float z in new[]{-.29f,.29f})
                    Box(body,x,.345f,z,.09f,.69f,.09f);
                foreach(float sign in new[]{-1f,1f})
                {
                    Box(detail,0,.44f,sign*.79f,.48f,.08f,.48f);
                    Box(detail,0,.66f,sign*1f,.48f,.38f,.08f);
                    foreach(float x in new[]{-.17f,.17f}) foreach(float z in new[]{-.17f,.17f})
                        Box(body,x,.20f,sign*.79f+z,.065f,.40f,.065f);
                }
            }
            else
            {
                Box(body,0,(size.y-.08f)*.5f,0,size.x-.08f,size.y-.08f,size.z-.08f);
                Box(detail,0,size.y-.04f,0,size.x,.08f,size.z);
            }
            var go=CreateMeshObject(id+" [prototype]",body,fixtureBodyMaterial);
            go.transform.localPosition=new Vector3(p.x,y,p.y);go.transform.localRotation=Quaternion.Euler(0,yaw,0);
            var detailGo=CreateMeshObject(id+" detail",detail,fixtureDetailMaterial);
            detailGo.transform.SetParent(go.transform,false);
            var collider=go.AddComponent<BoxCollider>();collider.center=Vector3.up*size.y*.5f;collider.size=size;
            MarkNotWalkable(go);PlannedPropColliders.Add(collider);
            contents.Add(go.GetComponent<Renderer>());contents.Add(detailGo.GetComponent<Renderer>());
            void Box(MetricAtlasMesh data,float x,float height,float z,float w,float h,float d) =>
                data.Box(new Vector3(x,height,z),new Vector3(w,h,d),style.concrete,Vector2.one);
        }
    }
}
