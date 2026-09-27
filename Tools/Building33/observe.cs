// Run through Unity_RunCommand. The normal Editor assembly owns JsonUtility DTOs;
// Unity's runtime-generated command assembly cannot deserialize nested DTO arrays.
internal class CommandScript : IRunCommand
{
    public void Execute(ExecutionResult result)
    {
        PlannedPixelBuildingObservation.Execute("PHASE");
        result.Log("B33 observation executed; capture is scheduled for a later frame.");
    }
}
