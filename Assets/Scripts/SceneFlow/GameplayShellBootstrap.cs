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

            if (shellPrefab == null)
            {
                Debug.LogError("GameplayShellBootstrap has no shell prefab.", this);
                return;
            }

            Instantiate(shellPrefab);
        }
    }
}
