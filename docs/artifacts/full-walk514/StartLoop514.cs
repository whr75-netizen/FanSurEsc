internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected){result.Log("WAIT_RUNTIME_READY; no loop armed");return;}EditorLoop514.Start();result.Log("514 one full loop armed asynchronously; follow Loop514/progress.txt and status.json; no runtime changes beyond temporary test controls.");}
}
