using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Metric planar tiles packed into one atlas mesh; partial tiles are cropped.</summary>
    public sealed class MetricAtlasMesh
    {
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<Vector3> uv = new List<Vector3>();
        private readonly List<int> triangles = new List<int>();
        private readonly Dictionary<IsometricUrbanStyle.AtlasPatch, Matrix4x4> transforms = new Dictionary<IsometricUrbanStyle.AtlasPatch, Matrix4x4>();

        public void Face(Vector3 origin, Vector3 right, Vector3 up, float width, float height,
            IsometricUrbanStyle.AtlasPatch patch, Vector2 repeat)
        {
            if (width <= 0f || height <= 0f) return;
            if (repeat.x <= 0f || repeat.y <= 0f) throw new System.ArgumentOutOfRangeException(nameof(repeat));
            if (!transforms.TryGetValue(patch, out Matrix4x4 h))
            {
                patch.GetHomography(out Vector4 a, out Vector4 b, out Vector4 c);
                h = Matrix4x4.zero; h.SetRow(0,a); h.SetRow(1,b); h.SetRow(2,c);
                transforms.Add(patch,h);
            }
            int nx = Mathf.CeilToInt(width/repeat.x), ny = Mathf.CeilToInt(height/repeat.y);
            for (int y=0;y<ny;y++)
            for (int x=0;x<nx;x++)
            {
                float x0=x*repeat.x, y0=y*repeat.y;
                float dx=Mathf.Min(repeat.x,width-x0), dy=Mathf.Min(repeat.y,height-y0);
                Vector3 o=origin+right*x0+up*y0;
                int start=vertices.Count;
                Add(o,0,0); Add(o+up*dy,0,dy/repeat.y);
                Add(o+up*dy+right*dx,dx/repeat.x,dy/repeat.y); Add(o+right*dx,dx/repeat.x,0);
                triangles.Add(start);triangles.Add(start+1);triangles.Add(start+2);
                triangles.Add(start);triangles.Add(start+2);triangles.Add(start+3);
            }
            void Add(Vector3 p,float u,float v)
            {
                vertices.Add(p);
                // Interpolate H*[u,v,1] homogeneously; the fragment divides once.
                uv.Add(h.MultiplyPoint3x4(new Vector3(u,v,1)));
            }
        }

        public void Box(Vector3 center,Vector3 size,IsometricUrbanStyle.AtlasPatch patch,Vector2 repeat)
        {
            Vector3 h=size*.5f;
            Face(center+new Vector3(-h.x,-h.y,-h.z),Vector3.right,Vector3.up,size.x,size.y,patch,repeat);
            Face(center+new Vector3(h.x,-h.y,h.z),Vector3.left,Vector3.up,size.x,size.y,patch,repeat);
            Face(center+new Vector3(-h.x,-h.y,h.z),Vector3.back,Vector3.up,size.z,size.y,patch,repeat);
            Face(center+new Vector3(h.x,-h.y,-h.z),Vector3.forward,Vector3.up,size.z,size.y,patch,repeat);
            Face(center+new Vector3(-h.x,h.y,-h.z),Vector3.right,Vector3.forward,size.x,size.z,patch,repeat);
            Face(center+new Vector3(-h.x,-h.y,h.z),Vector3.right,Vector3.back,size.x,size.z,patch,repeat);
        }

        public Mesh Create(string name)
        {
            var mesh=new Mesh{name=name,hideFlags=HideFlags.DontSave,indexFormat=IndexFormat.UInt32};
            mesh.SetVertices(vertices);mesh.SetUVs(0,uv);mesh.SetTriangles(triangles,0);
            mesh.RecalculateNormals();mesh.RecalculateBounds();return mesh;
        }
    }
}
