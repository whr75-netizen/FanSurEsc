using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand
{
    const string Output=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\renderer-family59";
    static UnityEngine.Object Ref(UnityEngine.Object target,string field){using(var s=new SerializedObject(target)){return s.FindProperty(field).objectReferenceValue;}}
    public void Execute(ExecutionResult result){
        var report=new Obj58{["memoryBefore"]=State58.Memory()};Obj58 before=null;
        try{
            before=State58.Read();State58.RequireEdit(before);report["before"]=before;
            var boot=Resources.FindObjectsOfTypeAll<MonoBehaviour>().Single(b=>b&&b.gameObject.scene.IsValid()&&b.GetType().Name=="GameplayShellBootstrap");var shell=Ref(boot,"shellPrefab")as Component;
            var native=shell.GetComponentsInChildren<MonoBehaviour>(true).Single(b=>b&&b.GetType().Name=="NativePlayer395");var surface=Ref(Ref(Ref(Ref(native,"host"),"main"),"motion"),"surface");SkinnedMeshRenderer[] sources;
            using(var s=new SerializedObject(surface)){var p=s.FindProperty("source");sources=Enumerable.Range(0,p.arraySize).Select(i=>p.GetArrayElementAtIndex(i).objectReferenceValue as SkinnedMeshRenderer).ToArray();}
            var registry=Obj58.Parse(File.ReadAllText(Path.Combine(Output,"SOURCE_REGISTRY59.json")));var specs=registry["bindings"].Select(b=>new RendererFamily59.Spec{
                rendererOrdinal=(int)b["rendererOrdinal"],subMesh=(int)b["subMesh"],bindingOrdinal=(int)b["bindingOrdinal"],triangleCount=(int)b["triangleCount"],materialId=(int)b["materialId"],sourceFamilyId=(string)b["sourceFamilyId"],meshUVSHA256=(string)b["meshUVSHA256"],indexSHA256=(string)b["indexSHA256"]}).ToArray();
            var binding=new RendererFamily59(sources,specs);var points=new Arr58();
            for(int draw=0;draw<specs.Length;draw++){
                var spec=specs[draw];var mesh=sources[spec.rendererOrdinal].sharedMesh;var uv=new System.Collections.Generic.List<Vector2>();mesh.GetUVs(0,uv);var indices=mesh.GetIndices(spec.subMesh);var source=binding.Draws[draw];
                for(int sample=0;sample<8;sample++){
                    int triangle=(int)Math.Floor((double)sample*(spec.triangleCount-1)/7);Vector2 a=uv[indices[triangle*3]],b=uv[indices[triangle*3+1]],c=uv[indices[triangle*3+2]];
                    var centre=new Vector2((float)(((double)a.x+b.x+c.x)/3),(float)(((double)a.y+b.y+c.y)/3));var effective=Vector2.Scale(centre,source.scale)+source.offset;
                    Color32 rgba;Vector2Int texel;string reason;bool known=binding.TryReadSourcePoint(draw,triangle,effective,out rgba,out texel,out reason);
                    points.Add(new Obj58{["draw"]=draw,["triangle"]=triangle,["sourceFamilyId"]=spec.sourceFamilyId,["uv"]=new Arr58(effective.x,effective.y),["known"]=known,["reason"]=reason,
                        ["rgba8"]=known?new Arr58((int)rgba.r,(int)rgba.g,(int)rgba.b,(int)rgba.a):null,["unityTexel"]=known?new Arr58(texel.x,texel.y):null});
                }
            }
            var descriptors=binding.PackDrawDescriptors();using(var w=new BinaryWriter(File.Create(Path.Combine(Output,"DRAW_DESCRIPTORS59.uint4"))))foreach(uint v in descriptors)w.Write(v);
            Color32 unused;Vector2Int t;string why;bool invalid=binding.TryReadSourcePoint(-1,0,Vector2.zero,out unused,out t,out why);
            report["points"]=points;report["draws"]=specs.Length;report["invalidDrawRejected"]=!invalid&&why=="unbound-draw";report["configuredAssetSourceOnly"]=true;report["liveVisibleCellsTested"]=false;report["rendered"]=false;
        }catch(Exception e){report["error"]=e.GetType().Name+": "+e.Message;}
        finally{var after=State58.Read();report["after"]=after;if(before!=null)report["stateChanges"]=new Arr58(State58.Changes(before,after));report["memoryAfter"]=State58.Memory();File.WriteAllText(Path.Combine(Output,"ACTUAL_SOURCE_POINTS59.json"),report.ToString());}
        result.Log("SOURCE59 draws="+report["draws"]+" error="+report["error"]+" stateChanges="+report["stateChanges"]);
    }
}
