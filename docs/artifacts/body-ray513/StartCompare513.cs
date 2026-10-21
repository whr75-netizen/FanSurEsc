internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected){result.Log("WAIT_RUNTIME_READY; no comparison armed");return;}EditorCompare513.Start();result.Log("513 source-ray correction comparison armed after GPU foreground/default-OFF fixture; three actual adjacent Walk pairs only.");}
}
