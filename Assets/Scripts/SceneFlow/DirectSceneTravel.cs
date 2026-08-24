using System;
using System.Collections;
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

        public static bool IsLoading => isLoading || hasPendingTravel ||
                                        (PersistentGameplayShell.Instance != null &&
                                         PersistentGameplayShell.Instance.IsTravelPrepared);
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
            if (IsLoading)
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

                if (!shell.BeginTravelTransition(
                        () => StartSceneLoad(destinationScene),
                        ClearFailedRequest))
                {
                    ClearFailedRequest();
                    Debug.LogError("Failed to start the gameplay scene fade transition.");
                    return false;
                }
                return true;
            }
            catch (Exception exception)
            {
                ClearFailedRequest();
                Debug.LogException(exception);
                return false;
            }
        }

        private static void StartSceneLoad(string destinationScene)
        {
            try
            {
                AsyncOperation operation = SceneManager.LoadSceneAsync(
                    destinationScene,
                    LoadSceneMode.Single);
                if (operation == null)
                {
                    Debug.LogError($"Failed to start loading scene '{destinationScene}'.");
                    ClearFailedRequest();
                    return;
                }

                operation.completed += _ =>
                {
                    isLoading = false;

                    PersistentGameplayShell shell = PersistentGameplayShell.Instance;
                    if (shell != null)
                    {
                        shell.StartCoroutine(VerifyArrivalOnNextFrame(destinationScene));
                    }
                    else if (hasPendingTravel)
                    {
                        FailArrival(
                            destinationScene,
                            $"Scene '{destinationScene}' loaded, but the persistent gameplay shell was lost before arrival completed.");
                    }
                };
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                ClearFailedRequest();
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

        private static IEnumerator VerifyArrivalOnNextFrame(string destinationScene)
        {
            // SceneSpawnController normally completes arrival from sceneLoaded or Start.
            // Give both lifecycle paths one frame before treating a still-pending request
            // as a broken destination configuration.
            yield return null;

            if (!hasPendingTravel ||
                !string.Equals(
                    pendingTravel.DestinationScene,
                    destinationScene,
                    StringComparison.Ordinal))
            {
                yield break;
            }

            FailArrival(
                destinationScene,
                $"Scene '{destinationScene}' loaded without completing player placement. " +
                "Check its active SceneSpawnController and requested spawn ID.");
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
