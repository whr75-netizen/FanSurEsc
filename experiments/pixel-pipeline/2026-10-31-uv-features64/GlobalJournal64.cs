// Prepared only; not imported, compiled in Unity, or executed in task64.
// Public journal + externally hashed binary backup, never private-instance-only.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;

public sealed class GlobalJournal64
{
    public enum Kind { Float,LegacyInt,Integer,Vector,Matrix,Texture,FloatArray,VectorArray,MatrixArray,Buffer,ConstantBuffer }
    public sealed class Spec {public string name;public Kind kind;}
    public sealed class Entry
    {
        public Spec spec;public float scalar;public int integer;public Vector4 vector;public Matrix4x4 matrix;
        public float[] floats;public Vector4[] vectors;public Matrix4x4[] matrices;
        public Texture originalTexture;public string textureKind,assetGUID;public long localId;
        public bool restorable,mutated;public string reason;
    }
    public static GlobalJournal64 Active;
    public readonly List<Entry> entries=new List<Entry>();
    public string sourceId,externalPath,backupSHA256;
    public bool externalVerified;

    public static GlobalJournal64 Snapshot(string sourceId,string path,IEnumerable<Spec> specs)
    {
        if(Active!=null)throw new InvalidOperationException("existing journal requires inspection, not replacement");
        var j=new GlobalJournal64{sourceId=sourceId,externalPath=path};
        foreach(var s in specs)
        {
            if(j.entries.Any(e=>e.spec.name==s.name))throw new ArgumentException("duplicate global name");
            var e=new Entry{spec=s,restorable=true};
            switch(s.kind)
            {
                case Kind.Float:e.scalar=Shader.GetGlobalFloat(s.name);break;
                // Legacy SetGlobalInt uses float storage in Unity6000.5. Keep
                // the full original float, not only its integer truncation.
                case Kind.LegacyInt:e.scalar=Shader.GetGlobalFloat(s.name);e.integer=Shader.GetGlobalInt(s.name);break;
                case Kind.Integer:e.integer=Shader.GetGlobalInteger(s.name);break;
                case Kind.Vector:e.vector=Shader.GetGlobalVector(s.name);break;
                case Kind.Matrix:e.matrix=Shader.GetGlobalMatrix(s.name);break;
                case Kind.FloatArray:e.floats=Shader.GetGlobalFloatArray(s.name);e.restorable=e.floats!=null&&e.floats.Length>0;break;
                case Kind.VectorArray:e.vectors=Shader.GetGlobalVectorArray(s.name);e.restorable=e.vectors!=null&&e.vectors.Length>0;break;
                case Kind.MatrixArray:e.matrices=Shader.GetGlobalMatrixArray(s.name);e.restorable=e.matrices!=null&&e.matrices.Length>0;break;
                case Kind.Texture:
                    e.originalTexture=Shader.GetGlobalTexture(s.name);
                    if(!e.originalTexture)e.textureKind="null";
                    else if(e.originalTexture==Texture2D.blackTexture)e.textureKind="builtin-black";
                    else if(e.originalTexture==Texture2D.whiteTexture)e.textureKind="builtin-white";
                    else if(e.originalTexture==Texture2D.grayTexture)e.textureKind="builtin-gray";
                    else {e.restorable=EditorUtility.IsPersistent(e.originalTexture)&&AssetDatabase.TryGetGUIDAndLocalFileIdentifier(e.originalTexture,out e.assetGUID,out e.localId);e.textureKind=e.restorable?"persistent-asset":"runtime-unrecoverable";}
                    break;
                case Kind.Buffer:case Kind.ConstantBuffer:e.restorable=false;e.reason="No public Shader global binding getter; do not mutate";break;
            }
            if(!e.restorable&&string.IsNullOrEmpty(e.reason))e.reason="absent/zero array or runtime-only texture; do not mutate";
            j.entries.Add(e);
        }
        j.WriteExternal();Active=j;return j;
    }

    static void Matrix(BinaryWriter w,Matrix4x4 m){for(int c=0;c<4;c++)for(int r=0;r<4;r++)w.Write(m[r,c]);}
    static void Vector(BinaryWriter w,Vector4 v){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}
    void WriteExternal()
    {
        using(var stream=new FileStream(externalPath,FileMode.CreateNew,FileAccess.Write,FileShare.Read))
        using(var w=new BinaryWriter(stream))
        {
            w.Write(0x34364a47);w.Write(1);w.Write(sourceId);w.Write(entries.Count);
            foreach(var e in entries)
            {
                w.Write(e.spec.name);w.Write((int)e.spec.kind);w.Write(e.restorable);w.Write(e.reason??"");
                w.Write(e.scalar);w.Write(e.integer);Vector(w,e.vector);Matrix(w,e.matrix);
                w.Write(e.textureKind??"");w.Write(e.assetGUID??"");w.Write(e.localId);
                w.Write(e.floats?.Length??0);if(e.floats!=null)foreach(var v in e.floats)w.Write(v);
                w.Write(e.vectors?.Length??0);if(e.vectors!=null)foreach(var v in e.vectors)Vector(w,v);
                w.Write(e.matrices?.Length??0);if(e.matrices!=null)foreach(var v in e.matrices)Matrix(w,v);
            }
            w.Flush();stream.Flush(true);
        }
        using(var h=SHA256.Create())using(var f=File.OpenRead(externalPath))backupSHA256=BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();
        externalVerified=VerifyExternal();
        if(!externalVerified)throw new IOException("external backup verification failed");
    }

    static bool Bits(float a,float b){return BitConverter.SingleToInt32Bits(a)==BitConverter.SingleToInt32Bits(b);}
    static bool VectorBits(Vector4 a,Vector4 b){for(int i=0;i<4;i++)if(!Bits(a[i],b[i]))return false;return true;}
    static bool MatrixBits(Matrix4x4 a,Matrix4x4 b){for(int i=0;i<16;i++)if(!Bits(a[i],b[i]))return false;return true;}
    static bool ReadVector(BinaryReader r,Vector4 expected){for(int i=0;i<4;i++)if(!Bits(r.ReadSingle(),expected[i]))return false;return true;}
    static bool ReadMatrix(BinaryReader r,Matrix4x4 expected){for(int c=0;c<4;c++)for(int row=0;row<4;row++)if(!Bits(r.ReadSingle(),expected[row,c]))return false;return true;}
    bool VerifyExternal()
    {
        using(var r=new BinaryReader(File.OpenRead(externalPath)))
        {
            if(r.ReadInt32()!=0x34364a47||r.ReadInt32()!=1||r.ReadString()!=sourceId||r.ReadInt32()!=entries.Count)return false;
            foreach(var e in entries)
            {
                if(r.ReadString()!=e.spec.name||r.ReadInt32()!=(int)e.spec.kind||r.ReadBoolean()!=e.restorable||r.ReadString()!=(e.reason??""))return false;
                if(!Bits(r.ReadSingle(),e.scalar)||r.ReadInt32()!=e.integer||!ReadVector(r,e.vector)||!ReadMatrix(r,e.matrix))return false;
                if(r.ReadString()!=(e.textureKind??"")||r.ReadString()!=(e.assetGUID??"")||r.ReadInt64()!=e.localId)return false;
                if(r.ReadInt32()!=(e.floats?.Length??0))return false;if(e.floats!=null)foreach(float v in e.floats)if(!Bits(r.ReadSingle(),v))return false;
                if(r.ReadInt32()!=(e.vectors?.Length??0))return false;if(e.vectors!=null)foreach(var v in e.vectors)if(!ReadVector(r,v))return false;
                if(r.ReadInt32()!=(e.matrices?.Length??0))return false;if(e.matrices!=null)foreach(var v in e.matrices)if(!ReadMatrix(r,v))return false;
            }
            return r.BaseStream.Position==r.BaseStream.Length;
        }
    }

    // Call on the ENTIRE renderer mutation inventory before normal Play/render.
    // This does not intercept or excuse untracked setters inside product passes.
    public void RequireRecoverable(IEnumerable<string> mutationNames)
    {
        if(!externalVerified)throw new InvalidOperationException("external backup not verified");
        foreach(string name in mutationNames)
        {var e=entries.SingleOrDefault(x=>x.spec.name==name);if(e==null||!e.restorable)throw new InvalidOperationException("unbacked global mutation: "+name);}
    }
    public void BeforeMutation(string name,int newArrayLength=-1)
    {
        RequireRecoverable(new[]{name});var e=entries.Single(x=>x.spec.name==name);
        int old=e.floats?.Length??e.vectors?.Length??e.matrices?.Length??-1;
        if(newArrayLength>=0&&newArrayLength!=old)throw new InvalidOperationException("global array length change forbidden");
        e.mutated=true;
    }
    public void RestoreMarked()
    {
        // No buffer setters. Assets and built-ins are retained references, never
        // destroyed/recreated from a guessed EntityId or surrounding colours.
        foreach(var e in entries.Where(x=>x.mutated))
        {
            if(!e.restorable)throw new InvalidOperationException("unrestorable global: "+e.spec.name);
            string n=e.spec.name;
            switch(e.spec.kind)
            {
                case Kind.Float:Shader.SetGlobalFloat(n,e.scalar);break;
                case Kind.LegacyInt:Shader.SetGlobalFloat(n,e.scalar);break;
                case Kind.Integer:Shader.SetGlobalInteger(n,e.integer);break;
                case Kind.Vector:Shader.SetGlobalVector(n,e.vector);break;
                case Kind.Matrix:Shader.SetGlobalMatrix(n,e.matrix);break;
                case Kind.Texture:
                    if(e.textureKind!="null"&&!e.originalTexture)throw new InvalidOperationException("original texture lifetime lost");
                    Shader.SetGlobalTexture(n,e.originalTexture);break;
                case Kind.FloatArray:Shader.SetGlobalFloatArray(n,e.floats);break;
                case Kind.VectorArray:Shader.SetGlobalVectorArray(n,e.vectors);break;
                case Kind.MatrixArray:Shader.SetGlobalMatrixArray(n,e.matrices);break;
                default:throw new InvalidOperationException("unsupported restore type");
            }
        }
        // Getter-by-getter equality verification is a required caller step before
        // clearing Active; this helper does not clear the only recovery handle.
    }
    public string[] VerifyMarked()
    {
        var errors=new List<string>();
        foreach(var e in entries.Where(x=>x.mutated))
        {
            string n=e.spec.name;bool same=false;
            switch(e.spec.kind)
            {
                case Kind.Float:case Kind.LegacyInt:same=Bits(Shader.GetGlobalFloat(n),e.scalar);break;
                case Kind.Integer:same=Shader.GetGlobalInteger(n)==e.integer;break;
                case Kind.Vector:same=VectorBits(Shader.GetGlobalVector(n),e.vector);break;
                case Kind.Matrix:same=MatrixBits(Shader.GetGlobalMatrix(n),e.matrix);break;
                case Kind.Texture:same=Shader.GetGlobalTexture(n)==e.originalTexture;break;
                case Kind.FloatArray:var a=Shader.GetGlobalFloatArray(n);same=a!=null&&a.Length==e.floats.Length&&a.Zip(e.floats,Bits).All(v=>v);break;
                case Kind.VectorArray:var b=Shader.GetGlobalVectorArray(n);same=b!=null&&b.Length==e.vectors.Length&&b.Zip(e.vectors,VectorBits).All(v=>v);break;
                case Kind.MatrixArray:var c=Shader.GetGlobalMatrixArray(n);same=c!=null&&c.Length==e.matrices.Length&&c.Zip(e.matrices,MatrixBits).All(v=>v);break;
            }
            if(!same)errors.Add(n);
        }
        return errors.ToArray();
    }
    public void ReleaseHandleAfterVerified()
    {
        if(!externalVerified||VerifyMarked().Length!=0)throw new InvalidOperationException("restore not verified; preserve recovery handle");
        // Drop only journal references, never Dispose/Destroy original textures
        // or user buffers. No forced GC. External backup stays on disk.
        entries.Clear();if(Active==this)Active=null;
    }
}
