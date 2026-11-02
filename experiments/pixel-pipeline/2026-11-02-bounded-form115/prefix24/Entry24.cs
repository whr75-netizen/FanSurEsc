// One explicit official command only. Other stages use separate reviewed entries.
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
 public sealed class CommandScript : IRunCommand {
  public void Execute(ExecutionResult result) {
   global::Prefix24.Prefix24Host.Start(1,message=>result.Log(message));
  }
 }
}
