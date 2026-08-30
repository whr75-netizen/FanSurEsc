using FantasySurvival.SaveSystem;
using UnityEngine;

namespace FantasySurvival.SceneFlow
{
    [DefaultExecutionOrder(-11000)]
    [DisallowMultipleComponent]
    public sealed class GameplayShellBootstrap : MonoBehaviour
    {
        [SerializeField] private PersistentGameplayShell shellPrefab;

        private void Awake()
        {
            if (PersistentGameplayShell.Instance != null)
            {
                return;
            }

#if UNITY_EDITOR
            // A gameplay scene opened directly in the Editor has no Main Menu
            // request. Keep that authoring session on disposable storage so an
            // interrupted real raid cannot block or be modified by quick tests.
            if (!GameStartRequest.HasPendingRequest &&
                !EditorDirectPlayStorageIsolation.TryActivate(out string storageError))
            {
                Debug.LogError(
                    $"Direct gameplay Play could not isolate save/recovery storage: {storageError}",
                    this);
                return;
            }
#endif

            if (shellPrefab == null)
            {
                Debug.LogError("GameplayShellBootstrap has no shell prefab.", this);
                return;
            }

            Instantiate(shellPrefab);
        }
    }
}
