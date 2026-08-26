using System;
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.SceneFlow
{
    /// <summary>
    /// Owns one covered gameplay-scene transition token.
    /// TryLoad -> shell cover/input lock -> scene load -> SceneSpawnController
    /// placement -> CompleteArrival -> shell reveal/input restore.
    /// </summary>
    public static class DirectSceneTravel
    {
        private struct PendingTravel
        {
            public string DestinationScene;
            public string SpawnId;
            public Action<bool> Completion;
        }

        private static PendingTravel pendingTravel;
        private static bool hasPendingTravel;
        private static bool isLoading;
        private static bool pendingArrivalHeld;

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
            pendingArrivalHeld = false;
        }

        public static bool TryLoad(string destinationScene, string spawnId)
        {
            return TryLoad(destinationScene, spawnId, null);
        }

        public static bool TryLoad(
            string destinationScene,
            string spawnId,
            Action<bool> completion)
        {
            if (IsLoading)
            {
                InvokeCompletion(completion, false);
                return false;
            }

            if (string.IsNullOrWhiteSpace(destinationScene))
            {
                Debug.LogError("Direct scene travel requires a destination scene.");
                InvokeCompletion(completion, false);
                return false;
            }

            if (string.IsNullOrWhiteSpace(spawnId))
            {
                Debug.LogError("Direct scene travel requires a destination spawn ID.");
                InvokeCompletion(completion, false);
                return false;
            }

            if (!Application.CanStreamedLevelBeLoaded(destinationScene))
            {
                Debug.LogError($"Scene '{destinationScene}' is not available in Build Settings.");
                InvokeCompletion(completion, false);
                return false;
            }

            pendingTravel = new PendingTravel
            {
                DestinationScene = destinationScene,
                SpawnId = spawnId,
                Completion = completion
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
                        () =>
                        {
                            StartSceneLoad(
                                destinationScene,
                                clearRequestOnFailure: true,
                                out _);
                        },
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

        private static bool StartSceneLoad(
            string destinationScene,
            bool clearRequestOnFailure,
            out string error)
        {
            try
            {
                AsyncOperation operation = SceneManager.LoadSceneAsync(
                    destinationScene,
                    LoadSceneMode.Single);
                if (operation == null)
                {
                    error = $"Failed to start loading scene '{destinationScene}'.";
                    Debug.LogError(error);
                    if (clearRequestOnFailure)
                    {
                        ClearFailedRequest();
                    }
                    else
                    {
                        // A rejected raid scene is already active. Keep the replacement
                        // pending token and the existing black cover/input lock so a
                        // synchronous redirect failure cannot reveal that invalid scene.
                        isLoading = false;
                        pendingArrivalHeld = true;
                    }

                    return false;
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

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                error = $"Loading scene '{destinationScene}' threw before an asynchronous load could start: " +
                        exception.Message;
                if (clearRequestOnFailure)
                {
                    ClearFailedRequest();
                }
                else
                {
                    isLoading = false;
                    pendingArrivalHeld = true;
                }

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

        internal static bool CanRedirectPendingArrival(
            string activeSceneName,
            string destinationScene,
            string spawnId,
            out string error)
        {
            if (!hasPendingTravel ||
                !string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                error = $"Scene '{activeSceneName}' is not the pending travel destination.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(destinationScene) ||
                string.IsNullOrWhiteSpace(spawnId))
            {
                error = "Arrival redirection requires a destination scene and spawn ID.";
                return false;
            }

            if (!Application.CanStreamedLevelBeLoaded(destinationScene))
            {
                error = $"Scene '{destinationScene}' is not available in Build Settings.";
                return false;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell == null || !shell.IsTravelPrepared)
            {
                error = "Arrival redirection requires the persistent shell to remain travel-prepared.";
                return false;
            }

            error = null;
            return true;
        }

        internal static bool TryRedirectPendingArrival(
            string activeSceneName,
            string destinationScene,
            string spawnId,
            Action<bool> completion,
            out string error)
        {
            if (!CanRedirectPendingArrival(
                    activeSceneName,
                    destinationScene,
                    spawnId,
                    out error))
            {
                return false;
            }

            // CALL-ORDER INVARIANT: the raid owner must first secure either the fresh
            // exact rollback or the recovered fail-closed decision. Then replace the
            // pending token without completing/cancelling the rejected destination,
            // releasing its input lock, or removing the existing black cover.
            pendingTravel = new PendingTravel
            {
                DestinationScene = destinationScene,
                SpawnId = spawnId,
                Completion = completion
            };
            isLoading = true;
            pendingArrivalHeld = false;
            return StartSceneLoad(
                destinationScene,
                clearRequestOnFailure: false,
                out error);
        }

        internal static void HoldPendingArrival(string activeSceneName, string reason)
        {
            if (!hasPendingTravel ||
                !string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                Debug.LogError(reason);
                return;
            }

            // The destination is known to be unsafe, while its rollback/redirect could
            // not be made restart-safe. Keep the covered pending token and every input
            // lock. A later process start can resolve the durable ordinary marker and
            // any Recovery artifacts without ever exposing this rejected scene.
            isLoading = false;
            pendingArrivalHeld = true;
            Debug.LogError(reason);
        }

        public static void CompleteArrival(string activeSceneName)
        {
            if (!hasPendingTravel ||
                !string.Equals(activeSceneName, pendingTravel.DestinationScene, StringComparison.Ordinal))
            {
                return;
            }

            Action<bool> completion = pendingTravel.Completion;
            pendingTravel = default;
            hasPendingTravel = false;
            pendingArrivalHeld = false;
            InvokeCompletion(completion, true);
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

            if (pendingArrivalHeld)
            {
                yield break;
            }

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
            Action<bool> completion = hasPendingTravel ? pendingTravel.Completion : null;
            pendingTravel = default;
            hasPendingTravel = false;
            isLoading = false;
            pendingArrivalHeld = false;
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell != null)
            {
                shell.CancelTravelPreparation(() => InvokeCompletion(completion, false));
            }
            else
            {
                InvokeCompletion(completion, false);
            }
        }

        private static void InvokeCompletion(Action<bool> completion, bool succeeded)
        {
            if (completion == null)
            {
                return;
            }

            try
            {
                completion.Invoke(succeeded);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
            }
        }
    }
}
