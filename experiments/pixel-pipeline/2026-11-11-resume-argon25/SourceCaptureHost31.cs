// REVIEW ONLY. No IRunCommand, EnterPlaymode, settings replacement, or automatic start.
using System;using UnityEditor;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public sealed class SourceCaptureHost31 {
 // Deliberate bounded strong roots: do not lose pending resources when an
 // external command returns. A retained owner blocks another arm on that view.
 static readonly PendingViews31<SourceCaptureHost31> pendingOwners=new PendingViews31<SourceCaptureHost31>();bool rootReleased;
 public static int PendingOwnerCount=>pendingOwners.Count; // Outer scope must be0 before starting another Play.
 readonly SourceOutline31 producer;readonly Action restoreBeforeExit,restoreAfterEdit;readonly ExitCoordinator31 exit=new ExitCoordinator31();bool armed,stopped;
 public SourceCaptureHost31(SourceOutline31 producer,Action restoreBeforeExit,Action restoreAfterEdit){this.producer=producer??throw new ArgumentNullException(nameof(producer));this.restoreBeforeExit=restoreBeforeExit??throw new ArgumentNullException(nameof(restoreBeforeExit));this.restoreAfterEdit=restoreAfterEdit??throw new ArgumentNullException(nameof(restoreAfterEdit));}
 public void Arm(){if(armed||stopped)throw new InvalidOperationException("31 host cannot rearm");if(!EditorApplication.isPlaying||!EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("31 requires existing stable Play; does not enter Play");if(!EditorSettings.enterPlayModeOptionsEnabled||(EditorSettings.enterPlayModeOptions&EnterPlayModeOptions.DisableDomainReload)==0)throw new InvalidOperationException("31 pending callback roots must survive normal Play exit; domain reload must already be disabled by the permitted outer scope");pendingOwners.Acquire(producer.ViewIdentity,this);armed=true;RenderPipelineManager.beginCameraRendering+=Enqueue;}
 void Enqueue(ScriptableRenderContext unused,Camera camera){if(stopped||producer.Failure!=null||camera!=producer.Camera)return;try{camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(producer);}catch(Exception e){producer.ReportFailure(e);}}
 void Stop(){stopped=true;RenderPipelineManager.beginCameraRendering-=Enqueue;producer.StopRecording();}
 public void BeginExit(){exit.Begin(Stop,restoreBeforeExit,()=>{if(EditorApplication.isPlaying||EditorApplication.isPlayingOrWillChangePlaymode)EditorApplication.ExitPlaymode();});}
 // Called by an explicit external observer. No background polling is installed.
 public void PumpExit(){exit.Pump(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&!EditorApplication.isCompiling&&!EditorApplication.isUpdating,()=>producer.CanRelease,()=>{if(!producer.TryReleaseOwned())throw new InvalidOperationException("31 owned resources retained; release failure");},restoreAfterEdit);if(exit.Finished&&armed&&!rootReleased){pendingOwners.Release(producer.ViewIdentity,this);rootReleased=true;}}
 public bool Ready=>producer.CanUsePixels;public Exception ProducerError=>producer.Failure;public bool ResourcesReleased=>exit.Released;public bool StateRestored=>exit.Restored;public bool ExitAttempted=>exit.ExitAttempted;public string[]Errors=>exit.Errors;
}
}
