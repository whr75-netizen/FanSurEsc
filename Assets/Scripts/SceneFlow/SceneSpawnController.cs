using FantasySurvival.Raids;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.SceneFlow
{
    [DefaultExecutionOrder(-9000)]
    [DisallowMultipleComponent]
    public sealed class SceneSpawnController : MonoBehaviour
    {
        [SerializeField] private SceneSpawnPoint[] spawnPoints;
        [SerializeField] private string defaultSpawnId;
        [SerializeField] private GameplaySceneKind gameplaySceneKind;

        private bool playerPlaced;

        private void OnEnable()
        {
            SceneManager.sceneLoaded += HandleSceneLoaded;
        }

        private void OnDisable()
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
        }

        private void Start()
        {
            if (!playerPlaced)
            {
                TryPlacePlayer(SceneManager.GetActiveScene().name, true);
            }
        }

        private void HandleSceneLoaded(Scene scene, LoadSceneMode loadMode)
        {
            if (scene == gameObject.scene)
            {
                TryPlacePlayer(scene.name, false);
            }
        }

        private void TryPlacePlayer(string activeSceneName, bool allowDefaultSpawn)
        {
            bool isPendingArrival = DirectSceneTravel.TryGetPendingSpawn(activeSceneName, out string spawnId);
            if (!isPendingArrival)
            {
                if (!allowDefaultSpawn || string.IsNullOrWhiteSpace(defaultSpawnId))
                {
                    return;
                }

                spawnId = defaultSpawnId;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            Transform player = shell != null
                ? shell.PlayerTransform
                : null;

            if (player == null)
            {
                DirectSceneTravel.FailArrival(
                    activeSceneName,
                    $"Scene '{activeSceneName}' cannot place the player because the persistent gameplay shell is missing.");
                return;
            }

            if (gameplaySceneKind == GameplaySceneKind.Raid)
            {
                // CALL-ORDER INVARIANT: sceneLoaded is an early probe only; this
                // controller's ordered Start pass is the Raid arrival commit gate.
                // Until readiness is Ready, do not move Player, enter Raid, capture a
                // checkpoint, complete travel, reveal, or restore gameplay input.
                if (!allowDefaultSpawn)
                {
                    return;
                }

                RaidCheckpointController checkpoint = shell.RaidCheckpoint;
                string readinessError = null;
                RaidSceneArrivalReadiness readiness = checkpoint != null
                    ? checkpoint.GetRaidSceneArrivalReadiness(activeSceneName, out readinessError)
                    : RaidSceneArrivalReadiness.Invalid;
                if (checkpoint == null)
                {
                    readinessError = "The persistent raid checkpoint controller is missing.";
                }

                if (readiness == RaidSceneArrivalReadiness.Pending)
                {
                    // sceneLoaded never reaches this branch. After the generator's
                    // earlier ordered Start, Pending means the synchronous navigation
                    // contract did not finish; treat it as an unsafe arrival instead of
                    // letting the next-frame verifier reveal a half-prepared Raid.
                    readiness = RaidSceneArrivalReadiness.Invalid;
                    readinessError =
                        "Raid scene navigation remained pending after the ordered generator Start.";
                }

                if (readiness == RaidSceneArrivalReadiness.Invalid)
                {
                    string failureReason = string.IsNullOrWhiteSpace(readinessError)
                        ? $"Scene '{activeSceneName}' is not ready for raid arrival."
                        : readinessError;
                    string returnError = null;

                    if (isPendingArrival &&
                        shell.RaidSession != null &&
                        shell.RaidSession.TryReturnFromInvalidRaidArrival(
                            activeSceneName,
                            failureReason,
                            out returnError))
                    {
                        playerPlaced = true;
                        return;
                    }

                    if (!isPendingArrival)
                    {
                        if (!shell.PrepareForTravel())
                        {
                            Debug.LogError(
                                "The invalid direct raid-scene start also failed to acquire its gameplay input lock.",
                                this);
                        }

                        Debug.LogError(
                            $"Direct raid-scene authoring start was blocked because the map is invalid: {failureReason}",
                            this);
                        playerPlaced = true;
                        return;
                    }

                    DirectSceneTravel.HoldPendingArrival(
                        activeSceneName,
                        $"Raid map arrival failed and could not return safely to base: " +
                        $"{returnError ?? failureReason}");
                    playerPlaced = true;
                    return;
                }
            }

            SceneSpawnPoint destination = FindSpawnPoint(spawnId);
            if (destination == null)
            {
                DirectSceneTravel.FailArrival(
                    activeSceneName,
                    $"Scene '{activeSceneName}' has no spawn point with ID '{spawnId}'.");
                return;
            }

            player.SetPositionAndRotation(destination.transform.position, destination.transform.rotation);

            Rigidbody playerRigidbody = player.GetComponent<Rigidbody>();
            if (playerRigidbody != null)
            {
                playerRigidbody.linearVelocity = Vector3.zero;
                playerRigidbody.angularVelocity = Vector3.zero;
            }

            Physics.SyncTransforms();

            if (shell.RaidSession == null)
            {
                DirectSceneTravel.FailArrival(
                    activeSceneName,
                    $"Scene '{activeSceneName}' cannot register its gameplay context because RaidSession is missing.");
                return;
            }

            if (!shell.RaidSession.TryEnterScene(gameplaySceneKind, out string contextError))
            {
                DirectSceneTravel.FailArrival(
                    activeSceneName,
                    $"Scene '{activeSceneName}' could not register its gameplay context: {contextError}");
                return;
            }

            bool checkpointArrivalFailed = false;
            string checkpointArrivalError = null;
            if (gameplaySceneKind == GameplaySceneKind.Raid)
            {
                RaidCheckpointController checkpoint = shell.RaidCheckpoint;
                bool checkpointCompleted = checkpoint != null &&
                    checkpoint.TryCompleteRaidSceneArrival(
                        activeSceneName,
                        out checkpointArrivalError);
                if (!checkpointCompleted)
                {
                    if (checkpoint == null)
                    {
                        checkpointArrivalError = "The persistent raid checkpoint controller is missing.";
                    }
                    else if (string.IsNullOrWhiteSpace(checkpointArrivalError))
                    {
                        checkpointArrivalError = "The raid checkpoint could not complete scene arrival.";
                    }

                    checkpointArrivalFailed = true;
                }
            }

            if (checkpointArrivalFailed)
            {
                // Persist the fail-closed decision as soon as checkpoint restore/capture
                // is known to be unusable. The black-screen reveal may finish later, but
                // a process interruption during that fade must not expose the old Active
                // checkpoint as resumable on the next launch.
                string durableFailureError = null;
                if (shell.RaidCheckpoint == null ||
                    !shell.RaidCheckpoint.TryMakeRecoveryFailureDurable(
                        checkpointArrivalError,
                        out durableFailureError))
                {
                    Debug.LogError(
                        $"Raid checkpoint failure could not be made durable before reveal: " +
                        $"{durableFailureError ?? "checkpoint controller is unavailable."}",
                        this);
                }
            }

            if (isPendingArrival)
            {
                DirectSceneTravel.CompleteArrival(activeSceneName);
                shell.FinishArrival(() =>
                {
                    if (checkpointArrivalFailed)
                    {
                        ResolveCheckpointArrivalFailure(shell, checkpointArrivalError);
                    }

                    shell.RaidSession?.CompleteSceneArrival(gameplaySceneKind);
                });
            }
            else
            {
                if (checkpointArrivalFailed)
                {
                    ResolveCheckpointArrivalFailure(shell, checkpointArrivalError);
                }

                shell.RaidSession.CompleteSceneArrival(gameplaySceneKind);
            }

            playerPlaced = true;
            Debug.Log($"Player placed at spawn '{spawnId}' in scene '{activeSceneName}'.", this);
        }

        private void ResolveCheckpointArrivalFailure(
            PersistentGameplayShell shell,
            string checkpointError)
        {
            RaidCheckpointController checkpoint = shell.RaidCheckpoint;
            bool failureResolved = checkpoint != null &&
                checkpoint.TryResolveRecoveryFailure(checkpointError);
            if (!failureResolved &&
                shell.RaidSession.Outcome != RaidOutcome.RecoveryFailed)
            {
                failureResolved = shell.RaidSession.TryResolveRecoveryFailure(checkpointError);
            }

            if (!failureResolved &&
                shell.RaidSession.Outcome != RaidOutcome.RecoveryFailed)
            {
                Debug.LogError(
                    $"Raid checkpoint arrival failed and could not enter the fail-closed result state: {checkpointError}",
                    this);
            }
        }

        private SceneSpawnPoint FindSpawnPoint(string spawnId)
        {
            if (spawnPoints == null)
            {
                return null;
            }

            for (int i = 0; i < spawnPoints.Length; i++)
            {
                var spawnPoint = spawnPoints[i];
                if (spawnPoint != null && spawnPoint.SpawnId == spawnId)
                {
                    return spawnPoint;
                }
            }

            return null;
        }
    }
}
