// Source binding only. No camera, renderer mutation, RGB fallback or role constants.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Collections.Generic;
using UnityEngine;

public sealed class RendererFamily59
{
    public sealed class Spec {public int rendererOrdinal,subMesh,bindingOrdinal,triangleCount,materialId;public string sourceFamilyId,meshUVSHA256,indexSHA256;}
    public sealed class Draw {public Spec source;public Material material;public Texture2D texture;public Color factor;public Vector2 scale,offset;}
    readonly Draw[] draws;
    public Draw[] Draws {get{return draws;}}
    static string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
    public RendererFamily59(SkinnedMeshRenderer[] sources,Spec[] specs){
        var uvHashes=new Dictionary<UnityEngine.Mesh,string>();draws=new Draw[specs.Length];
        foreach(var s in specs){
            var renderer=sources[s.rendererOrdinal];var mesh=renderer.sharedMesh;if(!mesh||!mesh.isReadable)throw new InvalidOperationException("Source mesh unavailable");
            if(!uvHashes.ContainsKey(mesh)){var uv=new List<Vector2>();mesh.GetUVs(0,uv);using(var memory=new MemoryStream()){using(var w=new BinaryWriter(memory,System.Text.Encoding.UTF8,true))foreach(var v in uv){w.Write(v.x);w.Write(v.y);}uvHashes[mesh]=Hash(memory.ToArray());}}
            var indices=mesh.GetIndices(s.subMesh);string indexHash;using(var memory=new MemoryStream()){using(var w=new BinaryWriter(memory,System.Text.Encoding.UTF8,true))foreach(int v in indices)w.Write((uint)v);indexHash=Hash(memory.ToArray());}
            if(uvHashes[mesh]!=s.meshUVSHA256||indexHash!=s.indexSHA256||indices.Length/3!=s.triangleCount)throw new InvalidOperationException("Source geometry identity changed");
            var material=renderer.sharedMaterials[s.subMesh];var texture=material.mainTexture as Texture2D;
            if(!material.HasProperty("_Color")||!material.HasProperty("_MainTex"))throw new NotSupportedException("Source base-colour/UV shader contract unavailable");
            draws[s.bindingOrdinal]=new Draw {source=s,material=material,texture=texture,factor=material.GetColor("_Color"),
                scale=material.GetTextureScale("_MainTex"),offset=material.GetTextureOffset("_MainTex")};
        }
    }
    static double Wrap(double v,TextureWrapMode mode){if(mode==TextureWrapMode.Repeat)return v-Math.Floor(v);if(mode==TextureWrapMode.Clamp)return Math.Max(0,Math.Min(1,v));if(mode==TextureWrapMode.Mirror){v-=2*Math.Floor(v/2);return v<=1?v:2-v;}throw new NotSupportedException("Texture wrap mode");}
    // UV must already be the effective shader UV (ST/animation applied by producer).
    public bool TryReadSourcePoint(int draw,int localPrimitive,Vector2 uv,out Color32 rgba,out Vector2Int texel,out string reason){
        rgba=new Color32();texel=new Vector2Int();reason=null;
        if(draw<0||draw>=draws.Length||draws[draw]==null){reason="unbound-draw";return false;}var d=draws[draw];
        if(localPrimitive<0||localPrimitive>=d.source.triangleCount){reason="primitive-out-of-range";return false;}
        if(float.IsNaN(uv.x)||float.IsInfinity(uv.x)||float.IsNaN(uv.y)||float.IsInfinity(uv.y)){reason="nonfinite-uv";return false;}
        if(!d.texture||!d.texture.isReadable){reason="source-texture-unreadable";return false;}
        try{int x=Math.Min(d.texture.width-1,(int)Math.Floor(Wrap(uv.x,d.texture.wrapModeU)*d.texture.width)),y=Math.Min(d.texture.height-1,(int)Math.Floor(Wrap(uv.y,d.texture.wrapModeV)*d.texture.height));texel=new Vector2Int(x,y);rgba=d.texture.GetPixel(x,y);return true;}
        catch(Exception e){reason=e.GetType().Name;return false;}
    }
    // Actual flattened draw order. Material/primitive IDs are provenance, not palette constants.
    public uint[] PackDrawDescriptors(){var words=new uint[draws.Length*4];for(int i=0;i<draws.Length;i++){var d=draws[i];words[i*4]=(uint)i+1;words[i*4+1]=(uint)d.source.rendererOrdinal;words[i*4+2]=(uint)d.source.subMesh;words[i*4+3]=(uint)d.source.triangleCount;}return words;}
}
