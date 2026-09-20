using System.Collections.Generic;
using FantasySurvival.WorldLighting;
using Unity.AI.Navigation;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Real metric walls and exterior upper storeys; ground floor is enterable.</summary>
    public sealed partial class EnterableSpriteBuilding : MonoBehaviour
    {
        private readonly List<Mesh> ownedMeshes=new List<Mesh>();
        private readonly List<Material> ownedMaterials=new List<Material>();
        public Vector3 InteriorCenter=>transform.TransformPoint(new Vector3(0,.5f,0));
        public Vector3 DoorOutside{get;private set;}
        public Vector3 DoorInside{get;private set;}
        public Vector3 SolidWallPoint{get;private set;}
        public Bounds LocalInterior{get;private set;}
        public Renderer RoofRenderer{get;private set;}
        public Collider RoofCollider{get;private set;}
        public Renderer[] WallRenderers{get;private set;}
        public Collider[] WallColliders{get;private set;}
        public int Storeys{get;private set;}
        public float TotalHeight{get;private set;}
        public const float DoorHeight=2.65f;
        public const float FloorLift=.016f;
        public const float WindowFrameDepth=.13f;

        public void Build(IsometricUrbanStyle style,Vector2 size,Vector2 facade,
            float tileSize,Color tint,UrbanOcclusionFader fader,bool reserveFacadeCenter=false,float plannedHeight=0f,
            UrbanPoiKind kind=UrbanPoiKind.None, UrbanFloorPlan floorPlan=null, UrbanBuildingPrefab catalog=null)
        {
            if (floorPlan != null)
            {
                BuildFloorPlan(style, floorPlan, kind, fader, catalog);
                return;
            }
            float width=size.x,depth=size.y,storey=style.wallHeight,t=style.wallThickness;
            Storeys=Mathf.Max(1,Mathf.RoundToInt(plannedHeight/storey));
            TotalHeight=Storeys*storey;
            LocalInterior=new Bounds(new Vector3(0,storey*.5f,0),new Vector3(width-t*2,storey,depth-t*2));
            Material wallMaterial=Own(style.CreateAtlasMaterial(style.wall.texture,false,"Metric wall atlas",tint));
            Material floorMaterial=Own(style.CreateAtlasMaterial(style.interior.texture,false,"Metric interior atlas",Color.white));
            Material roofMaterial=Own(style.CreateAtlasMaterial(style.roof.texture,false,"Metric roof atlas",Color.white));
            IsometricUrbanStyle.AtlasPatch wallPatch=style.WallFor(kind);
            var floorMesh=new MetricAtlasMesh();
            floorMesh.Face(new Vector3(-width*.5f,FloorLift,-depth*.5f),Vector3.right,Vector3.forward,
                width,depth,style.interior,new Vector2(tileSize,tileSize));
            var floorObject=CreateMeshObject("Interior Floor",floorMesh,floorMaterial);
            floorObject.AddComponent<MeshCollider>().sharedMesh=floorObject.GetComponent<MeshFilter>().sharedMesh;
            var walls=new List<Renderer>();var colliders=new List<Collider>();
            UrbanBuildingDoorGeometry opening=UrbanBuildingDoorGeometry.Calculate(size,facade,t,style.doorWidth,reserveFacadeCenter);
            bool doorOnZ=opening.OnZ;
            float sign=doorOnZ?opening.Outward.y:opening.Outward.x;
            for(int side=0;side<4;side++)
            {
                bool onZ=side<2;
                float sideSign=side%2==0?-1:1;
                float length=onZ?width:depth,coordinate=sideSign*(onZ?depth:width)*.5f;
                bool doorway=onZ==doorOnZ&&sideSign==sign;
                if(doorway)
                {
                    float door=opening.Width;
                    float center=opening.CenterAlong;
                    float left=center-door*.5f,right=center+door*.5f;
                    AddWall(onZ,coordinate,-length*.5f,left+length*.5f,0,TotalHeight);
                    AddWall(onZ,coordinate,right,length*.5f-right,0,TotalHeight);
                    AddWall(onZ,coordinate,left,door,DoorHeight,TotalHeight-DoorHeight);
                    Vector3 outward=onZ?Vector3.forward*sign:Vector3.right*sign;
                    Vector3 o=onZ?new Vector3(center,0,coordinate):new Vector3(coordinate,0,center);
                    DoorOutside=transform.TransformPoint(o+outward*1.4f+Vector3.up*.5f);
                    DoorInside=transform.TransformPoint(o-outward*1.4f+Vector3.up*.5f);
                }
                else
                {
                    AddWall(onZ,coordinate,-length*.5f,length,0,TotalHeight);
                    SolidWallPoint=transform.TransformPoint(onZ?new Vector3(0,.8f,coordinate):new Vector3(coordinate,.8f,0));
                }
            }
            var roofMesh=new MetricAtlasMesh();
            roofMesh.Box(new Vector3(0,TotalHeight,0),new Vector3(width+t,t,depth+t),style.roof,Vector2.one*2);
            GameObject roof=CreateMeshObject("Roof",roofMesh,roofMaterial);
            RoofRenderer=roof.GetComponent<Renderer>();
            var roofBox=roof.AddComponent<BoxCollider>();roofBox.center=new Vector3(0,TotalHeight,0);
            roofBox.size=new Vector3(width+t,t,depth+t);roof.tag="Obstacle";MarkNotWalkable(roof);
            roof.AddComponent<RainShelterOccluder>();RoofCollider=roofBox;
            WallRenderers=walls.ToArray();WallColliders=colliders.ToArray();
            fader.RegisterBuilding(transform,LocalInterior,RoofRenderer,roofBox,WallRenderers,WallColliders);

            void AddWall(bool onZ,float coordinate,float start,float length,float bottom,float height)
            {
                if(length<=0||height<=0)return;
                var mesh=new MetricAtlasMesh();
                Vector3 At(float along,float y,float outward=0)=>onZ
                    ?new Vector3(along,y,coordinate+Mathf.Sign(coordinate)*outward)
                    :new Vector3(coordinate+Mathf.Sign(coordinate)*outward,y,along);
                Vector3 Size(float along,float y,float thick)=>onZ?new Vector3(along,y,thick):new Vector3(thick,y,along);
                Vector3 center=At(start+length*.5f,bottom+height*.5f),dimensions=Size(length,height,t);
                mesh.Box(center,dimensions,wallPatch,style.brickRepeatMetres);
                for(int level=0;level<=Storeys;level++)
                {
                    float y=level*storey;
                    if(y>=bottom&&y<=bottom+height)
                        mesh.Box(At(start+length*.5f,Mathf.Clamp(y,bottom+.08f,bottom+height-.08f)),
                            Size(length,.16f,t+.08f),style.concrete,Vector2.one);
                }
                mesh.Box(At(start+.09f,bottom+height*.5f),Size(.18f,height,t+.10f),style.concrete,Vector2.one);
                mesh.Box(At(start+length-.09f,bottom+height*.5f),Size(.18f,height,t+.10f),style.concrete,Vector2.one);
                int bays=Mathf.FloorToInt(length/2);
                for(int bay=0;bay<bays;bay++)
                for(int floor=0;floor<Storeys;floor++)
                {
                    bool shopFront=kind==UrbanPoiKind.Retail && floor==0 && onZ==doorOnZ && Mathf.Sign(coordinate)==sign;
                    float y=floor*storey+(shopFront?.55f:1),wh=shopFront?1.8f:1.25f,ww=shopFront?1.6f:1;
                    if(y<bottom+.2f||y+wh>bottom+height-.2f)continue;
                    float x=start+(bay+.5f)*length/bays;
                    mesh.Box(At(x,y+wh*.5f,t*.5f+.035f),Size(ww,wh,.045f),style.glass,new Vector2(ww,wh));
                    foreach(float edge in new[]{-1f,1f})
                    {
                        mesh.Box(At(x+edge*(ww*.5f+.055f),y+wh*.5f,t*.5f+WindowFrameDepth*.5f),Size(.11f,wh+.22f,WindowFrameDepth),style.concrete,Vector2.one);
                        mesh.Box(At(x,y+wh*.5f+edge*(wh*.5f+.055f),t*.5f+WindowFrameDepth*.5f),Size(ww,.11f,WindowFrameDepth),style.concrete,Vector2.one);
                    }
                }
                GameObject wall=CreateMeshObject("Metric Wall "+walls.Count,mesh,wallMaterial);
                var box=wall.AddComponent<BoxCollider>();
                Vector3 outward=onZ?Vector3.forward*Mathf.Sign(coordinate):Vector3.right*Mathf.Sign(coordinate);
                box.center=center+outward*WindowFrameDepth*.5f;
                box.size=dimensions+Size(0,0,WindowFrameDepth);
                wall.tag="Obstacle";MarkNotWalkable(wall);walls.Add(wall.GetComponent<Renderer>());colliders.Add(box);
            }
        }

        private static void MarkNotWalkable(GameObject target)
        {
            var modifier=target.AddComponent<NavMeshModifier>();modifier.overrideArea=true;modifier.area=1;
        }
        private GameObject CreateMeshObject(string name,MetricAtlasMesh data,Material material)
        {
            Mesh mesh=data.Create(name);ownedMeshes.Add(mesh);
            var go=new GameObject(name);go.transform.SetParent(transform,false);
            go.AddComponent<MeshFilter>().sharedMesh=mesh;
            var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;
            renderer.shadowCastingMode=ShadowCastingMode.Off;return go;
        }
        private Material Own(Material m){ownedMaterials.Add(m);return m;}
        private void OnDestroy()
        {
            foreach(Mesh mesh in ownedMeshes)if(mesh!=null)Destroy(mesh);
            foreach(Material m in ownedMaterials)if(m!=null)Destroy(m);
        }
    }
}
