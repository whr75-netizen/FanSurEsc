// Original GLB material/UV -> source family. No renderer-role/name/triangle-range map.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;

public static class OriginalMaterialUv58
{
    public static string FamilyKey(string model,int mesh,int primitive,int material) {return model+"/mesh"+mesh+"/primitive"+primitive+"/material"+material;}
    public static int ResolveFamily(SourcePalette58.Family[] families,string model,int mesh,int primitive,int material,double[] uv) {
        if(uv==null||uv.Length!=2||!uv.All(SourcePalette58.Finite))throw new ArgumentException("Finite source UV required");
        string key=FamilyKey(model,mesh,primitive,material);int result=Array.FindIndex(families,f=>f.id==key);
        if(result<0)throw new ArgumentException("Unbound original material/primitive");return result;
    }
    static string Hash(byte[] b) {using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
    static int Number(Json58 t,int d=0) {return t==null?d:(int)t;}
    static double[] Factor(Json58 t) {return t==null?new[]{1.0,1,1,1}:t.Values<double>().ToArray();}
    static int Width(Json58 accessor) {switch((string)accessor["type"]){case "VEC2":return 2;case "VEC3":return 3;case "SCALAR":return 1;default:throw new NotSupportedException("Accessor shape");}}
    static double[] ReadAccessor(Obj58 doc,byte[] glb,int bin,int accessorIndex,int element) {
        var a=doc["accessors"][accessorIndex];if(a["sparse"]!=null)throw new NotSupportedException("Sparse accessor not implemented");
        var view=doc["bufferViews"][Number(a["bufferView"])];if(Number(view["buffer"])!=0)throw new NotSupportedException("External buffer");
        int component=Number(a["componentType"]),width=Width(a),bytes=component==5121?1:component==5123?2:4;
        int offset=bin+Number(view["byteOffset"])+Number(a["byteOffset"])+element*Number(view["byteStride"],bytes*width);
        var result=new double[width];
        for(int i=0;i<width;i++) {
            int p=offset+i*bytes;
            if(component==5126)result[i]=BitConverter.ToSingle(glb,p);
            else if(component==5125)result[i]=BitConverter.ToUInt32(glb,p);
            else if(component==5123)result[i]=BitConverter.ToUInt16(glb,p);
            else if(component==5121)result[i]=glb[p];
            else throw new NotSupportedException("Accessor component");
        }
        return result;
    }
    static double Wrap(double x,int mode) {
        if(mode==33071)return Math.Max(0,Math.Min(1,x));
        if(mode==33648){double v=x-2*Math.Floor(x/2);return v<=1?v:2-v;}
        if(mode==10497)return x-Math.Floor(x);
        throw new NotSupportedException("Sampler wrap mode");
    }
    public static SourcePalette58.Family[] Read(string modelPath,string expectedModelSHA,Arr58 domains,int sampleCount,long maxDecodedImageBytes,out long peakOwnedTextureBytes,out string modelSHA) {
        byte[] glb=File.ReadAllBytes(modelPath);modelSHA=Hash(glb);peakOwnedTextureBytes=0;
        if(modelSHA!=expectedModelSHA)throw new InvalidOperationException("Original model hash changed before image decode");
        if(BitConverter.ToUInt32(glb,0)!=0x46546c67||BitConverter.ToUInt32(glb,4)!=2)throw new NotSupportedException("GLB2 required");
        int jsonLength=BitConverter.ToInt32(glb,12),binHeader=20+jsonLength,bin=binHeader+8;
        if(BitConverter.ToUInt32(glb,16)!=0x4e4f534a||BitConverter.ToUInt32(glb,binHeader+4)!=0x004e4942)throw new NotSupportedException("GLB JSON/BIN chunks required");
        var doc=Obj58.Parse(System.Text.Encoding.UTF8.GetString(glb,20,jsonLength));
        var families=new System.Collections.Generic.List<SourcePalette58.Family>();
        foreach(var domain in domains) {
            int meshIndex=(int)domain["meshIndex"],primitiveIndex=(int)domain["primitiveIndex"];
            var primitive=doc["meshes"][meshIndex]["primitives"][primitiveIndex];
            if(Number(primitive["mode"],4)!=4)throw new NotSupportedException("Triangle primitive required");
            int material=Number(primitive["material"],-1);if(material<0)throw new NotSupportedException("Explicit source material required");
            var pbr=doc["materials"][material]["pbrMetallicRoughness"];var baseTexture=pbr["baseColorTexture"];
            var transform=baseTexture["extensions"]?["KHR_texture_transform"];
            var offset=transform?["offset"]==null?new[]{0.0,0}:transform["offset"].Values<double>().ToArray();
            var scale=transform?["scale"]==null?new[]{1.0,1}:transform["scale"].Values<double>().ToArray();
            if(Number(transform?["texCoord"],Number(baseTexture["texCoord"]))!=0||offset.Length!=2||scale.Length!=2||offset.Any(v=>v!=0)||scale.Any(v=>v!=1)||
                (transform?["rotation"]!=null&&(double)transform["rotation"]!=0))throw new NotSupportedException("Nonidentity texture transform/TEXCOORD set not implemented");
            var textureInfo=doc["textures"][(int)baseTexture["index"]];int imageId=(int)textureInfo["source"];
            var image=doc["images"][imageId];if(image["bufferView"]==null)throw new NotSupportedException("Embedded source image required");
            var imageView=doc["bufferViews"][(int)image["bufferView"]];
            var png=new byte[(int)imageView["byteLength"]];Array.Copy(glb,bin+Number(imageView["byteOffset"]),png,0,png.Length);
            if(png.Length<24||png[0]!=137||png[1]!=80||png[2]!=78||png[3]!=71)throw new NotSupportedException("Native PNG required");
            long pngWidth=((long)png[16]<<24)|((long)png[17]<<16)|((long)png[18]<<8)|png[19];
            long pngHeight=((long)png[20]<<24)|((long)png[21]<<16)|((long)png[22]<<8)|png[23];
            if(pngWidth<=0||pngHeight<=0||pngWidth*pngHeight*4>maxDecodedImageBytes)throw new InvalidOperationException("Declared one-image decode budget exceeded");
            string imageSHA=Hash(png);var factor=Factor(pbr["baseColorFactor"]);
            Json58 sampler=textureInfo["sampler"]==null?null:doc["samplers"][(int)textureInfo["sampler"]];
            int wrapS=Number(sampler?["wrapS"],10497),wrapT=Number(sampler?["wrapT"],10497);
            int positions=(int)primitive["attributes"]["POSITION"],uvs=(int)primitive["attributes"]["TEXCOORD_0"];
            if(Number(doc["accessors"][positions]["componentType"])!=5126||Number(doc["accessors"][uvs]["componentType"])!=5126)throw new NotSupportedException("Float32 POSITION/UV required");
            int indices=Number(primitive["indices"],-1),indexCount=indices<0?(int)doc["accessors"][positions]["count"]:(int)doc["accessors"][indices]["count"],triangles=indexCount/3;
            if(indexCount%3!=0||sampleCount<2)throw new ArgumentException("Triangle/sample count");
            var samples=new System.Collections.Generic.List<SourcePalette58.Sample>();Texture2D texture=null;
            try {
                texture=new Texture2D(2,2,TextureFormat.RGBA32,false,true){hideFlags=HideFlags.HideAndDontSave};
                if(!ImageConversion.LoadImage(texture,png,false)||(texture.format!=TextureFormat.ARGB32&&texture.format!=TextureFormat.RGBA32&&texture.format!=TextureFormat.RGB24))throw new NotSupportedException("Uncompressed native image decode required: "+texture.format);
                peakOwnedTextureBytes=Math.Max(peakOwnedTextureBytes,(long)texture.width*texture.height*4);
                // Sparse CPU pixel reads let Unity handle ARGB32/RGBA32 channel layout.
                // No whole-image GetPixels copy and no borrowed array disposal.
                for(int sample=0;sample<sampleCount;sample++) {
                    int triangle=(int)Math.Floor((double)sample*(triangles-1)/(sampleCount-1));
                    var ids=Enumerable.Range(0,3).Select(c=>indices<0?triangle*3+c:(int)ReadAccessor(doc,glb,bin,indices,triangle*3+c)[0]).ToArray();
                    var p=ids.Select(i=>ReadAccessor(doc,glb,bin,positions,i)).ToArray();var uv=ids.Select(i=>ReadAccessor(doc,glb,bin,uvs,i)).ToArray();
                    var a=Enumerable.Range(0,3).Select(i=>p[1][i]-p[0][i]).ToArray();var b=Enumerable.Range(0,3).Select(i=>p[2][i]-p[0][i]).ToArray();
                    double x=a[1]*b[2]-a[2]*b[1],y=a[2]*b[0]-a[0]*b[2],z=a[0]*b[1]-a[1]*b[0],area=Math.Sqrt(x*x+y*y+z*z)/2;
                    if(area<=0)continue;
                    var centre=new[]{uv.Sum(v=>v[0])/3,uv.Sum(v=>v[1])/3};
                    int tx=Math.Min(texture.width-1,(int)Math.Floor(Wrap(centre[0],wrapS)*texture.width));
                    int ty=Math.Min(texture.height-1,(int)Math.Floor(Wrap(centre[1],wrapT)*texture.height));
                    Color32 colour=texture.GetPixel(tx,texture.height-1-ty);
                    if(colour.a==0)continue;
                    samples.Add(new SourcePalette58.Sample {id="mesh"+meshIndex+"/primitive"+primitiveIndex+"/triangle"+triangle,materialId=material,primitiveId=primitiveIndex,triangle=triangle,
                        uv=centre,texel=new[]{tx,ty},rgba8=new[]{(int)colour.r,(int)colour.g,(int)colour.b,(int)colour.a},weight=area,imageSHA256=imageSHA});
                }
            } finally {if(texture)UnityEngine.Object.DestroyImmediate(texture);}
            string key=FamilyKey(modelSHA,meshIndex,primitiveIndex,material);
            families.Add(new SourcePalette58.Family {id=key,domainId="mesh"+meshIndex+"/primitive"+primitiveIndex,
                source=new SourcePalette58.Source {modelSHA256=modelSHA,materialId=material,imageSHA256=imageSHA,factorLinear=factor},samples=samples.ToArray()});
        }
        return families.ToArray();
    }
}
