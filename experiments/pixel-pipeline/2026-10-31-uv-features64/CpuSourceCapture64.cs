// Prepared helper only. No entry point, Asset import, renderer call or global setter.
using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using Unity.Collections;

public static class CpuSourceCapture64
{
    public sealed class Frame
    {
        public string sourceId,viewId;
        public int frameIndex, renderSerial, phaseIndex;
        public float renderedSource, evaluatedFrame;
        public Matrix4x4 view, projection, effectiveProjection, gpuProjection, gpuEffectiveProjection;
        public Vector4 viewport, clipShift, nativeShift;
        public Vector2Int logicalSize, nativeSize;
        public string subsampleProducer, activeModeFlags;
    }

    static void Matrix(BinaryWriter w, Matrix4x4 m)
    { for(int c=0;c<4;c++) for(int r=0;r<4;r++) w.Write(m[r,c]); }
    static void V3(BinaryWriter w,Vector3 p) { w.Write(p.x);w.Write(p.y);w.Write(p.z); }
    static void V4(BinaryWriter w,Vector4 p) {w.Write(p.x);w.Write(p.y);w.Write(p.z);w.Write(p.w);}
    static void Identity(BinaryWriter w,Frame frame)
    {
        if(string.IsNullOrEmpty(frame.sourceId)||string.IsNullOrEmpty(frame.viewId)||frame.frameIndex!=Time.frameCount)
            throw new InvalidOperationException("unbound or advanced frame; no re-render");
        w.Write(frame.sourceId);w.Write(frame.viewId);w.Write(frame.frameIndex);w.Write(frame.renderSerial);
    }

    public static void WriteCpuGeometry(string path,Frame frame,MeshFilter[] evaluated,SkinnedMeshRenderer[] sources)
    {
        if(evaluated==null||sources==null||evaluated.Length!=sources.Length)
            throw new ArgumentException("actual evaluated/source renderer map required");
        // Lists are local and reused per mesh. No serialized whole-object JSON,
        // original mesh assignments, static geometry arrays or BakeMesh calls.
        var vertices=new List<Vector3>();var normals=new List<Vector3>();var uv=new List<Vector2>();
        using(var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read))
        using(var w=new BinaryWriter(stream))
        {
            w.Write(0x34364353);w.Write(1);Identity(w,frame);w.Write(evaluated.Length);
            for(int r=0;r<evaluated.Length;r++)
            {
                var filter=evaluated[r];var mesh=filter.sharedMesh;var src=sources[r];
                if(!mesh||!mesh.isReadable||!src)throw new InvalidOperationException("source geometry unavailable");
                string guid;long localId;AssetDatabase.TryGetGUIDAndLocalFileIdentifier(src.sharedMesh,out guid,out localId);
                w.Write(r);w.Write(guid??"");w.Write(localId);Matrix(w,filter.transform.localToWorldMatrix);
                mesh.GetVertices(vertices);mesh.GetNormals(normals);mesh.GetUVs(0,uv);
                if(normals.Count!=vertices.Count||uv.Count!=vertices.Count)throw new InvalidOperationException("missing normal/UV source");
                w.Write(vertices.Count);foreach(var p in vertices)V3(w,p);foreach(var p in normals)V3(w,p);foreach(var p in uv){w.Write(p.x);w.Write(p.y);}
                var materials=src.sharedMaterials;if(materials.Length!=mesh.subMeshCount)throw new InvalidOperationException("material/submesh mismatch");
                w.Write(mesh.subMeshCount);
                for(int sm=0;sm<mesh.subMeshCount;sm++)
                {
                    var ix=mesh.GetIndices(sm);w.Write(ix.Length);foreach(int index in ix)w.Write((uint)index);
                    AssetDatabase.TryGetGUIDAndLocalFileIdentifier(materials[sm],out guid,out localId);w.Write(guid??"");w.Write(localId);
                    var m=materials[sm];var st=m.HasProperty("_MainTex")?m.GetTextureScale("_MainTex"):Vector2.one;var offset=m.HasProperty("_MainTex")?m.GetTextureOffset("_MainTex"):Vector2.zero;
                    w.Write(st.x);w.Write(st.y);w.Write(offset.x);w.Write(offset.y);
                    if(!m.HasProperty("_MainTex")||!m.HasProperty("_Color"))throw new InvalidOperationException("explicit source colour contract missing");
                    var tex=m.GetTexture("_MainTex");AssetDatabase.TryGetGUIDAndLocalFileIdentifier(tex,out guid,out localId);w.Write(guid??"");w.Write(localId);var factor=m.GetColor("_Color");V4(w,factor);
                }
                var bones=src.bones;w.Write(bones.Length);foreach(var bone in bones){w.Write(bone?bone.name:"");Matrix(w,bone?bone.localToWorldMatrix:Matrix4x4.identity);}
                Matrix(w,src.transform.localToWorldMatrix);var original=src.sharedMesh;var bindposes=original.bindposes;w.Write(bindposes.Length);foreach(var pose in bindposes)Matrix(w,pose);w.Write(original.blendShapeCount);
                for(int i=0;i<original.blendShapeCount;i++){w.Write(original.GetBlendShapeName(i));w.Write(src.GetBlendShapeWeight(i));}
            }
            w.Flush();stream.Flush(true);
        }
        if(frame.frameIndex!=Time.frameCount)throw new InvalidOperationException("frame advanced; packet stays incomplete");
    }

    public static void WriteCamera(string path,Frame frame)
    {
        if(string.IsNullOrEmpty(frame.subsampleProducer)||string.IsNullOrEmpty(frame.activeModeFlags))
            throw new InvalidOperationException("actual sampler and mode flags required");
        using(var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read))
        using(var w=new BinaryWriter(stream))
        {
            w.Write(0x34365043);w.Write(1);Identity(w,frame);w.Write(frame.phaseIndex);w.Write(frame.renderedSource);w.Write(frame.evaluatedFrame);
            // Raw GPU and effective GPU are distinct. A consumer must not add
            // nativeShift/clipShift twice after using effectiveProjection.
            Matrix(w,frame.view);Matrix(w,frame.projection);Matrix(w,frame.effectiveProjection);Matrix(w,frame.gpuProjection);Matrix(w,frame.gpuEffectiveProjection);
            V4(w,frame.viewport);V4(w,frame.clipShift);V4(w,frame.nativeShift);w.Write(frame.logicalSize.x);w.Write(frame.logicalSize.y);w.Write(frame.nativeSize.x);w.Write(frame.nativeSize.y);
            w.Write("matrix:column-major; logical:y-down; each plane records its own y origin");w.Write(frame.subsampleProducer);w.Write(frame.activeModeFlags);w.Flush();stream.Flush(true);
        }
    }

    public static void WriteOwnedPlane(string path,Frame frame,RenderTexture texture,RectInt roi,string pass,string channel,string encoding,string yConvention)
    {
        if(!texture||roi.width<=0||roi.height<=0||roi.xMin<0||roi.yMin<0||roi.xMax>texture.width||roi.yMax>texture.height)
            throw new ArgumentException("invalid source ROI");
        if((long)roi.width*roi.height*16>1024*1024)throw new InvalidOperationException("plane exceeds one MiB");
        if(string.IsNullOrEmpty(pass)||string.IsNullOrEmpty(channel)||string.IsNullOrEmpty(encoding)||string.IsNullOrEmpty(yConvention))throw new ArgumentException("producer/channel/encoding/origin required");
        var data=new NativeArray<Color>(roi.width*roi.height,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);
        AsyncGPUReadbackRequest request=default;bool sent=false;
        try
        {
            request=AsyncGPUReadback.RequestIntoNativeArray(ref data,texture,0,roi.x,roi.width,roi.y,roi.height,0,1,TextureFormat.RGBAFloat);sent=true;request.WaitForCompletion();
            if(request.hasError)throw new InvalidOperationException("readback failed; do not retry without inspecting packet");
            using(var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read))
            using(var w=new BinaryWriter(stream))
            {
                w.Write(0x34365052);w.Write(1);Identity(w,frame);w.Write(pass);w.Write(channel);w.Write(encoding);w.Write(yConvention);w.Write(texture.width);w.Write(texture.height);w.Write(roi.x);w.Write(roi.y);w.Write(roi.width);w.Write(roi.height);
                // Stream owned native memory once. No GetData borrowed Dispose,
                // ToArray, Texture2D, PNG encoding or second full-plane copy.
                for(int i=0;i<data.Length;i++){var c=data[i];w.Write(c.r);w.Write(c.g);w.Write(c.b);w.Write(c.a);}w.Flush();stream.Flush(true);
            }
        }
        finally {if(sent&&!request.done)request.WaitForCompletion();data.Dispose();}
        if(frame.frameIndex!=Time.frameCount)throw new InvalidOperationException("frame advanced; packet stays incomplete");
    }
}
