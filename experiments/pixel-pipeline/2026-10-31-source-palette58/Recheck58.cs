// Saved-data CPU check only: no render, texture, native buffer or scene access.
using System;
using System.IO;
using System.Linq;
using UnityEngine;
internal class CommandScript : IRunCommand
{
    const string Output=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\source-palette58";
    public void Execute(ExecutionResult result){
        var gpu=Obj58.Parse(File.ReadAllText(Path.Combine(Output,"GPU58.json")));var source=Obj58.Parse(File.ReadAllText(Path.Combine(Output,"SOURCE58.json")));
        byte[] bytes=File.ReadAllBytes(Path.Combine(Output,"CLASS58.float4"));int n=(int)gpu["sampleCount"],oldErrors=0,correctedErrors=0;var uploaded=new Color[n];
        for(int i=0;i<n;i++){
            var row=gpu["rows"][i];int family=(int)row["family"],count=source["records"][family]["palette"]["rgb8"].Count;
            uploaded[i]=new Color((float)(int)row[(bool)row["boundOpaque"]?"kPrime":"k"]/(count-1),(float)(double)source["cases"][i]["g"],.4f+i*.001f,.7f);
        }
        for(int i=0;i<n;i++){
            float depth=BitConverter.ToSingle(bytes,i*16+8);if(depth!=.4f+i*.001f)oldErrors++;
            for(int c=0;c<4;c++)if(BitConverter.ToSingle(bytes,i*16+c*4)!=uploaded[i][c])correctedErrors++;
        }
        var report=new Obj58{["samples"]=n,["originalExpressionDepthMismatches"]=oldErrors,["uploadedFloat32ComponentMismatches"]=correctedErrors,["passed"]=correctedErrors==0,["newGPUExecution"]=false,["sceneOrAssetAccess"]=false};
        File.WriteAllText(Path.Combine(Output,"CSHARP_RECHECK58.json"),report.ToString());result.Log("CPU58 saved-data recheck "+report.ToString());
    }
}
