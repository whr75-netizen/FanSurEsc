internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected){result.Log("WAIT_RUNTIME_READY; no capture armed");return;}EditorCapture511.Start();result.Log("511 Editor capture armed; inspect Walk511/status.json. Temporary state restores on completion/error.");}
}
