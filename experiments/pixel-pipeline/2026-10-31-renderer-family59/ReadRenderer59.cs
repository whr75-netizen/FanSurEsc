// Read-only live renderer/public serialized graph. No Initialize/Evaluate/Render.
using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

internal class CommandScript : IRunCommand
{
    const string Output=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-family59";
    static UnityEngine.Object Ref(UnityEngine.Object target,string field){if(!target)return null;using(var s=new SerializedObject(target)){var p=s.FindProperty(field);return p==null?null:p.objectReferenceValue;}}
    static bool Bool(UnityEngine.Object target,string field){if(!target)return false;using(var s=new SerializedObject(target)){var p=s.FindProperty(field);return p!=null&&p.boolValue;}}
    static string Text(UnityEngine.Object target,string field){if(!target)return null;using(var s=new SerializedObject(target)){var p=s.FindProperty(field);return p==null?null:p.stringValue;}}
    static UnityEngine.Object[] Refs(UnityEngine.Object target,string field){if(!target)return new UnityEngine.Object[0];using(var s=new SerializedObject(target)){var p=s.FindProperty(field);return p==null||!p.isArray?new UnityEngine.Object[0]:Enumerable.Range(0,p.arraySize).Select(i=>p.GetArrayElementAtIndex(i).objectReferenceValue).ToArray();}}
    static string PathOf(Transform t){if(!t)return null;return t.parent?PathOf(t.parent)+"/"+t.name:t.name;}
    static Obj58 Obj(UnityEngine.Object o){return o?new Obj58{["name"]=o.name,["type"]=o.GetType().FullName,["entityId"]=o.GetEntityId().ToString(),["assetPath"]=AssetDatabase.GetAssetPath(o),["guid"]=AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(o))}:null;}
    static Obj58 CameraInfo(Camera c){if(!c)return null;var r=Obj(c);r["path"]=PathOf(c.transform);r["enabled"]=c.enabled;r["active"]=c.gameObject.activeInHierarchy;r["orthographic"]=c.orthographic;r["ortho"]=c.orthographicSize;r["aspect"]=c.aspect;r["pixelWidth"]=c.pixelWidth;r["pixelHeight"]=c.pixelHeight;r["target"]=Obj(c.targetTexture);r["targetCreated"]=c.targetTexture&&c.targetTexture.IsCreated();return r;}
    static Obj58 MeshInfo(UnityEngine.Mesh m){if(!m)return null;var r=Obj(m);r["vertices"]=m.vertexCount;r["subMeshes"]=m.subMeshCount;r["readable"]=m.isReadable;r["indexCounts"]=new Arr58(Enumerable.Range(0,m.subMeshCount).Select(i=>(long)m.GetIndexCount(i)));return r;}
    static Obj58 MaterialInfo(Material m){if(!m)return null;var r=Obj(m);r["shader"]=Obj(m.shader);r["mainTexture"]=Obj(m.mainTexture);r["textures"]=new Arr58(m.GetTexturePropertyNames().Where(n=>m.GetTexture(n)).Select(n=>new Obj58{["property"]=n,["texture"]=Obj(m.GetTexture(n))}));if(m.HasProperty("_MainTex")){var scale=m.GetTextureScale("_MainTex");var offset=m.GetTextureOffset("_MainTex");r["mainTextureScale"]=new Arr58(scale.x,scale.y);r["mainTextureOffset"]=new Arr58(offset.x,offset.y);}if(m.HasProperty("_Color")){var c=m.GetColor("_Color");r["color"]=new Arr58(c.r,c.g,c.b,c.a);}var texture=m.mainTexture as Texture2D;if(texture){r["textureSize"]=new Arr58(texture.width,texture.height);r["textureReadable"]=texture.isReadable;r["textureFormat"]=texture.format.ToString();string path=AssetDatabase.GetAssetPath(texture);if(File.Exists(path)&&System.IO.Path.GetExtension(path).ToLowerInvariant()==".png")r["nativeImageFileSHA256"]=State58.Hash(File.ReadAllBytes(path));}return r;}
    public void Execute(ExecutionResult result){
        Directory.CreateDirectory(Output);var report=new Obj58{["memoryBefore"]=State58.Memory()};Obj58 before=null;
        try{
            before=State58.Read();State58.RequireEdit(before);report["before"]=before;
            var natives=Resources.FindObjectsOfTypeAll<MonoBehaviour>().Where(b=>b&&b.gameObject.scene.IsValid()&&b.gameObject.scene.isLoaded&&b.GetType().Name=="NativePlayer395").ToArray();
            report["liveNativeCount"]=natives.Length;var configured=new System.Collections.Generic.List<MonoBehaviour>();var bootRows=new Arr58();
            foreach(var bootstrap in Resources.FindObjectsOfTypeAll<MonoBehaviour>().Where(b=>b&&b.gameObject.scene.IsValid()&&b.gameObject.scene.isLoaded&&b.GetType().Name=="GameplayShellBootstrap")){
                var shell=Ref(bootstrap,"shellPrefab")as Component;bootRows.Add(new Obj58{["bootstrap"]=Obj(bootstrap),["shellPrefab"]=Obj(shell)});
                if(shell)configured.AddRange(shell.GetComponentsInChildren<MonoBehaviour>(true).Where(b=>b&&b.GetType().Name=="NativePlayer395"));
            }
            report["bootstraps"]=bootRows;report["assetReadOnlyNotInstantiated"]=true;report["configuredNativeCount"]=configured.Count;
            report["playStartScene"]=Obj(EditorSceneManager.playModeStartScene);report["enterPlayModeOptionsEnabled"]=EditorSettings.enterPlayModeOptionsEnabled;report["enterPlayModeOptions"]=EditorSettings.enterPlayModeOptions.ToString();
            natives=natives.Concat(configured).Distinct().ToArray();
            var records=new Arr58();
            foreach(var native in natives){
                var host=Ref(native,"host");var main=Ref(host,"main");var motion=Ref(main,"motion");var surface=Ref(motion,"surface");
                var row=Obj(native);row["path"]=PathOf(native.transform);row["enabled"]=native.enabled;row["active"]=native.gameObject.activeInHierarchy;row["ready"]=Bool(native,"ready");row["failure"]=Text(native,"failure");
                row["host"]=Obj(host);row["main"]=Obj(main);row["motion"]=Obj(motion);row["surface"]=Obj(surface);
                row["gameCamera"]=CameraInfo(Ref(native,"gameCamera")as Camera);row["localCamera"]=CameraInfo(Ref(native,"localCamera")as Camera);row["motionCamera"]=CameraInfo(Ref(motion,"camera")as Camera);
                var sources=new Arr58();int ordinal=0;
                foreach(var value in Refs(surface,"source")){
                    var skin=value as SkinnedMeshRenderer;if(!skin){sources.Add(null);ordinal++;continue;}
                    var s=Obj(skin);s["ordinal"]=ordinal++;s["path"]=PathOf(skin.transform);s["enabled"]=skin.enabled;s["active"]=skin.gameObject.activeInHierarchy;s["mesh"]=MeshInfo(skin.sharedMesh);
                    s["materials"]=new Arr58(skin.sharedMaterials.Select(MaterialInfo));
                    var mesh=skin.sharedMesh;
                    if(mesh&&mesh.isReadable){
                        var uv=new System.Collections.Generic.List<Vector2>();mesh.GetUVs(0,uv);string stem="source-"+ordinal;
                        string uvFile=stem+".uv.f32";using(var w=new BinaryWriter(File.Create(System.IO.Path.Combine(Output,uvFile))))foreach(var v in uv){w.Write(v.x);w.Write(v.y);}s["uvFile"]=uvFile;s["uvSHA256"]=State58.Hash(File.ReadAllBytes(System.IO.Path.Combine(Output,uvFile)));s["uvCount"]=uv.Count;
                        var indexFiles=new Arr58();
                        for(int sub=0;sub<mesh.subMeshCount;sub++){if(mesh.GetTopology(sub)!=MeshTopology.Triangles){indexFiles.Add(new Obj58{["subMesh"]=sub,["unsupportedTopology"]=mesh.GetTopology(sub).ToString()});continue;}var indices=mesh.GetIndices(sub);string name=stem+"-sub-"+sub+".indices.u32";using(var w=new BinaryWriter(File.Create(System.IO.Path.Combine(Output,name))))foreach(int valueIndex in indices)w.Write((uint)valueIndex);indexFiles.Add(new Obj58{["subMesh"]=sub,["file"]=name,["count"]=indices.Length,["sha256"]=State58.Hash(File.ReadAllBytes(System.IO.Path.Combine(Output,name)))});}
                        s["indexFiles"]=indexFiles;
                    }else s["sourceDataUnavailable"]=true;
                    sources.Add(s);
                }
                row["sourceRenderers"]=sources;
                row["outputs"]=new Arr58(Refs(surface,"outputs").Select(o=>{var f=o as MeshFilter;if(!f)return null;var d=Obj(f);d["path"]=PathOf(f.transform);d["mesh"]=MeshInfo(f.sharedMesh);var renderer=f.GetComponent<Renderer>();d["enabled"]=renderer&&renderer.enabled;d["materials"]=new Arr58(renderer?renderer.sharedMaterials.Select(MaterialInfo):Enumerable.Empty<Obj58>());return d;}));
                records.Add(row);
            }
            report["nativeRenderers"]=records;
            report["gameplay"]=new Arr58(Resources.FindObjectsOfTypeAll<MonoBehaviour>().Where(b=>b&&b.gameObject.scene.IsValid()&&b.GetType().Name=="Gameplay397").Select(b=>new Obj58{["object"]=Obj(b),["path"]=PathOf(b.transform),["enabled"]=b.enabled,["active"]=b.gameObject.activeInHierarchy,["activateGameplay"]=Bool(b,"activateGameplay"),["connected"]=Bool(b,"connected"),["player"]=Obj(Ref(b,"player")),["failure"]=Text(b,"failure")}));
            report["initializedOrRendered"]=false;
        }catch(Exception e){report["error"]=e.GetType().Name+": "+e.Message;}
        finally{var after=State58.Read();report["after"]=after;if(before!=null)report["stateChanges"]=new Arr58(State58.Changes(before,after));report["memoryAfter"]=State58.Memory();File.WriteAllText(System.IO.Path.Combine(Output,"CONFIGURED_RENDERER59.json"),report.ToString());}
        result.Log("RENDERER59 count="+report["nativeRenderers"]?.Count+" error="+report["error"]+" stateChanges="+report["stateChanges"]);
    }
}
