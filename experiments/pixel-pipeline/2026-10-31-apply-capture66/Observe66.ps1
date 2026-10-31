$ErrorActionPreference='Stop'
$taskRoot='C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66'
$targetProcessId=28304
$output=Join-Path $taskRoot 'HOST_OBSERVE66.json'
if(Test-Path -LiteralPath $output){throw 'Observation already exists; do not overwrite evidence.'}
$samples=@()
for($sampleIndex=0;$sampleIndex -lt 3;$sampleIndex++){
 $now=[DateTime]::UtcNow.ToString('O')
 $p=Get-CimInstance Win32_Process -Filter "ProcessId=$targetProcessId"
 if(-not $p){$samples+=@{utc=$now;alive=$false};break}
 $samples+=@{utc=$now;alive=$true;processId=$p.ProcessId;kernel100ns=[UInt64]$p.KernelModeTime;user100ns=[UInt64]$p.UserModeTime;readOps=[UInt64]$p.ReadOperationCount;writeOps=[UInt64]$p.WriteOperationCount;readBytes=[UInt64]$p.ReadTransferCount;writeBytes=[UInt64]$p.WriteTransferCount;otherOps=[UInt64]$p.OtherOperationCount;otherBytes=[UInt64]$p.OtherTransferCount;threads=$p.ThreadCount;handles=$p.HandleCount;workingSetBytes=[UInt64]$p.WorkingSetSize;privateCommitBytes=[UInt64]$p.PrivatePageCount}
 if($sampleIndex -lt 2){Start-Sleep -Seconds 8}
}
$threads=@();$chains=@();$chainError=$null
$p=Get-Process -Id $targetProcessId -ErrorAction SilentlyContinue
if($p){
 foreach($t in $p.Threads){
  try{$row=@{id=$t.Id;startUTC=$t.StartTime.ToUniversalTime().ToString('O');cpuSeconds=$t.TotalProcessorTime.TotalSeconds;state=$t.ThreadState.ToString()};if($t.ThreadState -eq [System.Diagnostics.ThreadState]::Wait){$row.waitReason=$t.WaitReason.ToString()};$threads+=$row}
  catch{$threads+=@{id=$t.Id;readError=$_.Exception.Message}}
 }
 try{
  Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class ReadOnlyWct66 {
 [DllImport("advapi32.dll", SetLastError=true)]static extern IntPtr OpenThreadWaitChainSession(uint flags,IntPtr callback);
 [DllImport("advapi32.dll", SetLastError=true)]static extern bool GetThreadWaitChain(IntPtr session,UIntPtr context,uint flags,uint tid,ref uint count,IntPtr nodes,[MarshalAs(UnmanagedType.Bool)]out bool cycle);
 [DllImport("advapi32.dll")]static extern void CloseThreadWaitChainSession(IntPtr session);
 public static Dictionary<string,object> Query(uint tid){
  var result=new Dictionary<string,object>();result["queriedThread"]=tid;
  IntPtr session=OpenThreadWaitChainSession(0,IntPtr.Zero);
  if(session==IntPtr.Zero){result["openError"]=Marshal.GetLastWin32Error();return result;}
  // Native wct.h layout: 8-byte header, 272-byte aligned lock/thread union.
  const int stride=280;IntPtr nodes=Marshal.AllocHGlobal(stride*16);
  try{
   uint count=16;bool cycle;
   bool ok=GetThreadWaitChain(session,UIntPtr.Zero,0,tid,ref count,nodes,out cycle);
   result["success"]=ok;result["error"]=ok?0:Marshal.GetLastWin32Error();result["cycleReported"]=cycle;result["nodeCount"]=count;
   var list=new List<Dictionary<string,object>>();
   if(ok)for(int i=0;i<Math.Min(count,16);i++){
    IntPtr item=IntPtr.Add(nodes,i*stride);int kind=Marshal.ReadInt32(item,0);int status=Marshal.ReadInt32(item,4);
    var row=new Dictionary<string,object>();row["objectType"]=kind;row["objectStatus"]=status;
    if(kind==8){row["processId"]=Marshal.ReadInt32(item,8);row["threadId"]=Marshal.ReadInt32(item,12);row["waitTime"]=Marshal.ReadInt32(item,16);row["contextSwitches"]=Marshal.ReadInt32(item,20);}
    list.Add(row);
   }
   result["nodes"]=list;
  }finally{Marshal.FreeHGlobal(nodes);CloseThreadWaitChainSession(session);}
  return result;
 }
}
'@
  $earliest=@($threads | Where-Object {$_.ContainsKey('startUTC')} | Sort-Object startUTC,id | Select-Object -First 2)
  $hottest=@($threads | Where-Object {$_.ContainsKey('cpuSeconds')} | Sort-Object cpuSeconds -Descending | Select-Object -First 4)
  $selected=@(($earliest+$hottest) | Sort-Object id -Unique)
  foreach($t in $selected){$chains+=[ReadOnlyWct66]::Query([uint32]$t.id)}
 }catch{$chainError=$_.Exception.Message}
}
$result=@{utc=[DateTime]::UtcNow.ToString('O');processId=$targetProcessId;samples=$samples;threads=$threads;waitChains=$chains;waitChainError=$chainError;queryFlags=0;limits='No UI/Responding polling, debugger, dump, process memory read, thread suspension, privilege changes, COM callbacks or Unity queue commands. WCT success/no-cycle does not rule out unsupported locks or busy loops.'}
$result|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $output -Encoding utf8
$result|Select-Object utc,processId,@{n='sampleCount';e={$_.samples.Count}},@{n='threadCount';e={$_.threads.Count}},@{n='waitChainCount';e={$_.waitChains.Count}},waitChainError|ConvertTo-Json -Compress
