using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;

internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  const string root=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66";
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required");
  var specs=Json58.Parse(File.ReadAllText(Path.Combine(root,"GLOBAL_NAMES66.json"))).Select(o=>new GlobalJournal64.Spec{name=(string)o["name"],kind=(string)o["type"]=="Int"?GlobalJournal64.Kind.LegacyInt:(GlobalJournal64.Kind)Enum.Parse(typeof(GlobalJournal64.Kind),(string)o["type"])}).ToArray();
  GlobalJournal64 j=null;var report=new Obj58{["utc"]=DateTime.UtcNow.ToString("O"),["project"]=Application.dataPath,["sourceId"]="global-preflight66-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfffZ")};
  try
  {
   j=GlobalJournal64.Snapshot((string)report["sourceId"],Path.Combine(root,"GLOBALS_PREFLIGHT66.bin"),specs);
   report["externallyVerified"]=j.externalVerified;report["backupSHA256"]=j.backupSHA256;
   report["entries"]=new Arr58(j.entries.Select(e=>new Obj58{["name"]=e.spec.name,["kind"]=e.spec.kind.ToString(),["restorable"]=e.restorable,["reason"]=e.reason,["textureKind"]=e.textureKind,["textureGUID"]=e.assetGUID,["localId"]=e.localId}));
   j.RequireRecoverable(specs.Select(s=>s.name));report["readyBeforePlay"]=true;
  }
  catch(Exception e){report["readyBeforePlay"]=false;report["error"]=e.GetType().Name+": "+e.Message;}
  finally{if(j!=null)j.ReleaseHandleAfterVerified();}
  report["mutations"]=0;report["PlayEntries"]=0;
  File.WriteAllText(Path.Combine(root,"GLOBALS_PREFLIGHT66.json"),report.ToString());
  result.Log("66 global read-only preflight ready="+report["readyBeforePlay"]+" entries="+specs.Length+" no global setters/Play");
 }
}
