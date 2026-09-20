using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public sealed partial class EnterableSpriteBuilding
    {
        public UrbanFloorPlan FloorPlan { get; private set; }
        public readonly List<string> PropClearanceErrors = new List<string>();
        public readonly List<Collider> PlannedPropColliders = new List<Collider>();

        private void BuildFloorPlan(IsometricUrbanStyle style, UrbanFloorPlan plan, UrbanPoiKind kind,
            UrbanOcclusionFader fader, UrbanBuildingPrefab catalog)
        {
            FloorPlan = plan;
            Storeys = plan.FloorCount;
            TotalHeight = Storeys * plan.StoreyHeight;
            float w = plan.Size.x, d = plan.Size.y, t = style.wallThickness;
            LocalInterior = new Bounds(new Vector3(0, TotalHeight * .5f, 0),
                new Vector3(w - t, TotalHeight, d - t));
            var wallMaterial = Own(style.CreateAtlasMaterial(style.wall.texture, false, "Planned wall", Color.white));
            var floorMaterial = Own(style.CreateAtlasMaterial(style.interior.texture, false, "Planned floor", Color.white));
            var allWalls = new List<Renderer>();
            var allColliders = new List<Collider>();
            var wallPatch = style.WallFor(kind);
            DoorOutside = transform.TransformPoint(new Vector3(0, .5f, d * .5f + 1.4f));
            DoorInside = transform.TransformPoint(new Vector3(0, .5f, d * .5f - 1.4f));
            SolidWallPoint = transform.TransformPoint(new Vector3(-w * .5f, .8f, 0));

            for (int level = 0; level < Storeys; level++)
            {
                float y = FloorLift + level * plan.StoreyHeight;
                var floors = new List<Renderer>(); var floorColliders = new List<Collider>();
                var walls = new List<Renderer>(); var colliders = new List<Collider>();
                var contents = new List<Renderer>();
                if (level == 0) Slab(new Rect(-w*.5f,-d*.5f,w,d));
                else foreach (Rect rect in plan.UpperSlabs) Slab(rect);

                bool serviceDoor = level == 0 && plan.ServiceDoorCenter.HasValue;
                Wall(new Vector2(-w*.5f,-d*.5f),new Vector2(w*.5f,-d*.5f),
                    serviceDoor ? plan.ServiceDoorWidth : 0, serviceDoor ? plan.ServiceDoorCenter.Value : default);
                Wall(new Vector2(-w*.5f,-d*.5f),new Vector2(-w*.5f,d*.5f),0,default);
                Wall(new Vector2(w*.5f,-d*.5f),new Vector2(w*.5f,d*.5f),0,default);
                Wall(new Vector2(-w*.5f,d*.5f),new Vector2(w*.5f,d*.5f),level==0?style.doorWidth:0,new Vector2(0,d*.5f));
                foreach (UrbanPlanPartition partition in plan.Partitions)
                    if (partition.Floor == level)
                        Wall(partition.Start,partition.End,partition.DoorWidth,partition.DoorCenter);
                foreach (UrbanPlanRoom room in plan.Rooms)
                {
                    if (room.Floor != level) continue;
                    contents.Add(MakePlanLabel(room.Role,new Vector3(room.Bounds.center.x,y+.025f,room.Bounds.center.y),.14f,true));
                    if (IsCommercialPlan(plan)) PopulateCommercialRoom(room, y, style, catalog, contents);
                    else PopulateRoom(room, y, catalog, contents);
                }
                if (level == 0 && plan.Stair != null) BuildStair(plan.Stair, floorMaterial, style, contents);
                if (level > 0 && plan.Stair != null)
                {
                    Rect hole=plan.Stair.Bounds;
                    // Solid guard on the open side of the stair well, leaving both landings open.
                    BoxWall(new Vector3(hole.xMin-.06f,y+.5f,hole.center.y),
                        new Vector3(.12f,1f,hole.height),"Stair guard");
                }
                allWalls.AddRange(walls); allColliders.AddRange(colliders);
                fader.RegisterStorey(transform,LocalInterior,level,plan.StoreyHeight,
                    floors.ToArray(),floorColliders.ToArray(),walls.ToArray(),colliders.ToArray(),contents.ToArray());

                void Slab(Rect r)
                {
                    var data=new MetricAtlasMesh();
                    data.Box(new Vector3(r.center.x,y-.10f,r.center.y),new Vector3(r.width,.20f,r.height),style.interior,Vector2.one*2);
                    var go=CreateMeshObject("Floor "+level,data,floorMaterial);
                    var box=go.AddComponent<BoxCollider>();box.center=new Vector3(r.center.x,y-.10f,r.center.y);box.size=new Vector3(r.width,.20f,r.height);
                    floors.Add(go.GetComponent<Renderer>());floorColliders.Add(box);
                }
                void Wall(Vector2 a,Vector2 b,float opening,Vector2 door)
                {
                    Vector2 axis=(b-a).normalized;float length=Vector2.Distance(a,b);
                    // Walls end at the underside of the next slab. Coplanar NotWalkable wall tops
                    // must not overwrite the upper floor's walkable doorway during voxelization.
                    float height=plan.StoreyHeight-.2f;
                    if(opening<=0){Segment(0,length,0,height);return;}
                    float offset=Vector2.Dot(door-a,axis),left=offset-opening*.5f,right=offset+opening*.5f;
                    Segment(0,left,0,height);Segment(right,length-right,0,height);
                    Segment(left,opening,DoorHeight,height-DoorHeight);
                    void Segment(float start,float len,float bottom,float height)
                    {
                        if(len<=.001f||height<=.001f)return;
                        Vector2 c=a+axis*(start+len*.5f);
                        Vector3 dimensions=Mathf.Abs(axis.x)>.5f?new Vector3(len,height,t):new Vector3(t,height,len);
                        BoxWall(new Vector3(c.x,y+bottom+height*.5f,c.y),dimensions,"Wall F"+level);
                    }
                }
                void BoxWall(Vector3 center,Vector3 dimensions,string name)
                {
                    var data=new MetricAtlasMesh();data.Box(center,dimensions,wallPatch,style.brickRepeatMetres);
                    var go=CreateMeshObject(name,data,wallMaterial);var box=go.AddComponent<BoxCollider>();box.center=center;box.size=dimensions;
                    go.tag="Obstacle";MarkNotWalkable(go);walls.Add(go.GetComponent<Renderer>());colliders.Add(box);
                }
            }
            var roofData=new MetricAtlasMesh();roofData.Box(new Vector3(0,FloorLift+TotalHeight-.10f,0),new Vector3(w,.2f,d),style.roof,Vector2.one*2);
            var roof=CreateMeshObject("Planned roof",roofData,Own(style.CreateAtlasMaterial(style.roof.texture,false,"Planned roof",Color.white)));
            var roofBox=roof.AddComponent<BoxCollider>();roofBox.center=new Vector3(0,FloorLift+TotalHeight-.1f,0);roofBox.size=new Vector3(w,.2f,d);
            MarkNotWalkable(roof);roof.AddComponent<FantasySurvival.WorldLighting.RainShelterOccluder>();
            RoofRenderer=roof.GetComponent<Renderer>();RoofCollider=roofBox;
            fader.RegisterStorey(transform,LocalInterior,Storeys,plan.StoreyHeight,new[]{RoofRenderer},new Collider[]{roofBox},
                Array.Empty<Renderer>(),Array.Empty<Collider>(),Array.Empty<Renderer>(),true);
            WallRenderers=allWalls.ToArray();WallColliders=allColliders.ToArray();
            MakePlanLabel(plan.Program+" / "+Storeys+"F",new Vector3(0,.08f,d*.5f+1.05f),.22f,true);
        }

        private void BuildStair(UrbanPlanStair stair,Material material,IsometricUrbanStyle style,List<Renderer> contents)
        {
            float run=Vector2.Distance(stair.Start,stair.End),width=stair.Bounds.width;
            float direction=Mathf.Sign(stair.End.y-stair.Start.y);
            int count=Mathf.CeilToInt(stair.Rise/.2f);float rise=stair.Rise/count,tread=run/count;
            var data=new MetricAtlasMesh();
            for(int i=0;i<count;i++)
                data.Box(new Vector3(stair.Start.x,FloorLift+rise*(i+.5f),stair.Start.y+direction*tread*(i+.5f)),
                    new Vector3(width,rise,tread),style.concrete,Vector2.one);
            var go=CreateMeshObject("Stair treads",data,material);contents.Add(go.GetComponent<Renderer>());
            // The collision surface is a continuous slope, sharing exactly the plan endpoints.
            float x0=stair.Bounds.xMin,x1=stair.Bounds.xMax,z0=stair.Start.y,z1=stair.End.y;
            var ramp=new Mesh {name="Planned stair ramp"};ownedMeshes.Add(ramp);
            ramp.vertices=new[]{new Vector3(x0,FloorLift,z0),new Vector3(x0,FloorLift+stair.Rise,z1),
                new Vector3(x1,FloorLift+stair.Rise,z1),new Vector3(x1,FloorLift,z0)};
            ramp.triangles=direction>0?new[]{0,1,2,0,2,3}:new[]{0,2,1,0,3,2};ramp.RecalculateNormals();ramp.RecalculateBounds();
            go.AddComponent<MeshCollider>().sharedMesh=ramp;
        }

        private void PopulateRoom(UrbanPlanRoom room,float y,UrbanBuildingPrefab catalog,List<Renderer> contents)
        {
            if(catalog==null)return;
            string role=room.Role.ToLowerInvariant();
            string id=role.Contains("bed")||role.Contains("cell")?"bed":
                role.Contains("stock")||role.Contains("records")||role.Contains("evidence")?"storage_shelf":
                role.Contains("living")||role.Contains("break")?"sofa":
                role.Contains("sales")?"retail_shelf":
                role.Contains("office")||role.Contains("interview")||role.Contains("study")||role.Contains("staff")||role.Contains("briefing")?"office_desk":null;
            if(id==null)return; // No suitable authored sanitary asset: keep its room, do not substitute another object.
            UrbanBuildingProp source=Array.Find(catalog.propPrefabs,p=>p!=null&&p.catalogId==id);
            if(source==null)return;
            Vector3 size=source.PlacementSize;
            Rect r=room.Bounds;
            if(role.Contains("sales"))
            {
                // Fixed shelf modules flank a clear 2.4m central aisle; never scale the source prop.
                for(int row=0;row<2;row++)for(int side=-1;side<=1;side+=2)
                    Place(new Vector2(side*(1.2f+size.x*.5f+.8f),r.yMin+2f+row*2.2f));
            }
            else Place(new Vector2(r.center.x,r.yMin+.35f+size.z*.5f));
            void Place(Vector2 p)
            {
                var footprint=new Rect(p.x-size.x*.5f,p.y-size.z*.5f,size.x,size.z);
                if(!r.Contains(footprint.min)||!r.Contains(footprint.max))return;
                if(room.HasDoor && UrbanBuildingDecorationPlanner.Expand(footprint,.7f).Contains(room.DoorCenter))return;
                var prop=Instantiate(source,transform,false);prop.name=room.Role+"/"+id;
                prop.transform.localPosition=new Vector3(p.x,y,p.y);prop.transform.localRotation=Quaternion.identity;
                var box=prop.GetComponent<BoxCollider>();box.center=Vector3.up*size.y*.5f;box.size=size;
                PlannedPropColliders.Add(box);contents.AddRange(prop.GetComponentsInChildren<Renderer>());
            }
        }

        private Renderer MakePlanLabel(string value,Vector3 local,float scale,bool horizontal)
        {
            var go=new GameObject(value);go.transform.SetParent(transform,false);go.transform.localPosition=local;
            if(horizontal)go.transform.localRotation=Quaternion.Euler(90,0,0);
            var label=go.AddComponent<TextMesh>();label.text=value;label.fontSize=40;label.characterSize=scale;
            label.anchor=TextAnchor.MiddleCenter;label.color=new Color(.10f,.10f,.10f,1);
            return go.GetComponent<Renderer>();
        }
    }
}
