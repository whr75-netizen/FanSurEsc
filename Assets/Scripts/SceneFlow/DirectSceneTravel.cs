using System;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.SceneFlow
{
    public static class DirectSceneTravel
    {
        private struct PendingTravel
        {
            public string DestinationScene;
            public string SpawnId;
        }

        private static PendingTravel pendingTravel;
        private static bool hasPendingTravel;
        private static bool isLoading;

        public static bool IsLoading => isLoading;
        public static bool HasPendingTravel => hasPendingTravel;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetState()
        {
            pendingTravel = default;
            hasPendingTravel = false;
            isLoading = false;
        }

        public static bool TryLoad(string destinationScene, string spawnId)
        {
            if (isLoading)
            {
                return false;
            }

            if (string.IsNullOrWhiteSpace(destinationScene))
            {
                Debug.LogError("Direct scene travel requires a destination scene.");
                return false;
            }

            if (string.IsNullOrWhiteSpace(spawnId))
            {
                Debug.LogError("Direct scene travel requires a destination spawn ID.");
                return false;
            }

            if (!Application.CanStreamedLevelBeLoaded(destinationScene))
            {
                Debug.LogError($"Scene '{destinationScene}' is not available in Build Settings.");
                return false;
            }

            pendingTravel = new PendingTravel
            {
                DestinationScene = destinationScene,
                SpawnId = spawnId
            };
            hasPendingTravel = true;
            isLoading = true;

            try
            {
                PersistentGameplayShell shell = PersistentGameplayShell.Instance;
                if (shell == null)
                {
                    Debug.LogError("Direct scene travel requires an active PersistentGameplayShell.");
                    ClearFailedRequest();
                    return false;
                }

                if (!shell.PrepareForTravel())
                {
                    ClearFailedRequest();
                    return false;
                }

                AsyncOperation operation = SceneManager.LoadSceneAsync(destinationScene, LoadSceneMode.Single);
                if (operation == null)
                {
                    ClearFailedRequest();
                    Debug.LogError($"Failed to start loading scene '{destinationScene}'.");
                    return false;
                }

                operation.completed += _ => isLoading = false;
                return true;
            }
            catch (Exception exception)
            {
                ClearFailedRequest();
                Debug.LogException(exception);
                return false;
            }
        }

        public static bool TryGetPendingSpawn(string activeSceneName, out string spawnId)
        {
            if (hasPendingTravel &&
                string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                spawnId = pendingTravel.SpawnId;
                return true;
            }

            spawnId = null;
            return false;
        }

        public static void CompleteArrival(string activeSceneName)
        {
            if (!hasPendingTravel ||
                !string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                return;
            }

            pendingTravel = default;
            hasPendingTravel = false;
        }

        public static void FailArrival(string activeSceneName, string reason)
        {
            if (!hasPendingTravel ||
                !string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                Debug.LogError(reason);
                return;
            }

            Debug.LogError(reason);
            ClearFailedRequest();
        }

        private static void ClearFailedRequest()
        {
            pendingTravel = default;
            hasPendingTravel = false;
            isLoading = false;
            PersistentGameplayShell.Instance?.CancelTravelPreparation();
        }
    }
}
