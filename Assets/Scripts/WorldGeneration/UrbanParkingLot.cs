using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Open parcel use: one row of stalls, a drive aisle and an independent pedestrian strip.</summary>
    public sealed class UrbanParkingLot : MonoBehaviour
    {
        private readonly List<Mesh> meshes=new List<Mesh>();
        private readonly List<Material> materials=new List<Material>();
        public int ParcelIndex { get; private set; }
        public int StallCount { get; private set; }
        public float AisleWidth => 6f;
        public Vector3 Entrance => transform.TransformPoint(new Vector3(0,.5f,size.y*.5f));
        private Vector2 size;

        public void Build(UrbanParcelPlacement parcel,int index,IsometricUrbanStyle style)
        {
            ParcelIndex=index;size=parcel.Size;
            float left=-size.x*.5f+.4f,right=size.x*.5f-.4f,back=-size.y*.5f+.4f;
            const float stallWidth=2.5f,stallDepth=5f,walkWidth=1.5f,y=.025f;
            if(size.y<12f||size.x<10f)throw new System.InvalidOperationException("Parking parcel cannot fit a 5m stall, 6m aisle and pedestrian strip.");
            var surface=new MetricAtlasMesh();
            surface.Face(new Vector3(left,y,back),Vector3.right,Vector3.forward,right-left,size.y-.8f,style.road,Vector2.one*2);
            Make("Parking asphalt",surface,style.road.texture,style);
            var walk=new MetricAtlasMesh();walk.Face(new Vector3(left,y+.004f,back),Vector3.right,Vector3.forward,walkWidth,size.y-.8f,style.sidewalk,Vector2.one*2);
            Make("Pedestrian strip",walk,style.sidewalk.texture,style);
            float start=left+walkWidth+.3f;
            StallCount=Mathf.FloorToInt((right-start)/stallWidth);
            var paint=new MetricAtlasMesh();
            for(int i=0;i<=StallCount;i++)
                paint.Face(new Vector3(start+i*stallWidth-.05f,y+.008f,back),Vector3.right,Vector3.forward,.1f,stallDepth,style.whiteLine,Vector2.one);
            paint.Face(new Vector3(start,y+.008f,back),Vector3.right,Vector3.forward,StallCount*stallWidth,.1f,style.whiteLine,Vector2.one);
            Make("Parking stall lines",paint,style.whiteLine.texture,style);
            var label=new GameObject("Parking label");label.transform.SetParent(transform,false);
            label.transform.localPosition=new Vector3(0,y+.01f,back+stallDepth+3);label.transform.localRotation=Quaternion.Euler(90,0,0);
            var text=label.AddComponent<TextMesh>();text.text="PARKING / "+StallCount+" SPACES";text.fontSize=40;text.characterSize=.20f;text.anchor=TextAnchor.MiddleCenter;text.color=Color.white;
        }
        private void Make(string name,MetricAtlasMesh data,Texture2D texture,IsometricUrbanStyle style)
        {
            Mesh mesh=data.Create(name);meshes.Add(mesh);
            Material material=style.CreateAtlasMaterial(texture,false,name,Color.white);materials.Add(material);
            var go=new GameObject(name);go.transform.SetParent(transform,false);go.AddComponent<MeshFilter>().sharedMesh=mesh;
            var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;
            // Existing continuous ground remains the collision/navigation authority.
        }
        private void OnDestroy()
        {
            foreach(var mesh in meshes)if(mesh!=null)Destroy(mesh);
            foreach(var material in materials)if(material!=null)Destroy(material);
        }
    }
}
