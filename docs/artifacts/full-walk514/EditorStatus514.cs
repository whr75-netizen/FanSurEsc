using UnityEngine;using UnityEditor;using UnityEngine.SceneManagement;
internal class CommandScript:IRunCommand{
 public void Execute(ExecutionResult result){var s=SceneManager.GetActiveScene();result.Log("514EDITOR project="+Application.dataPath+" play="+EditorApplication.isPlaying+" changing="+EditorApplication.isPlayingOrWillChangePlaymode+" paused="+EditorApplication.isPaused+" compiling="+EditorApplication.isCompiling+" updating="+EditorApplication.isUpdating+" scene="+s.path+" dirty="+s.isDirty);}
}
