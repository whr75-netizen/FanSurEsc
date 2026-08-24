using FantasySurvival.Raids;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.SceneFlow
{
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

            if (isPendingArrival)
            {
                DirectSceneTravel.CompleteArrival(activeSceneName);
                shell.FinishArrival(() =>
                    shell.RaidSession?.CompleteSceneArrival(gameplaySceneKind));
            }
            else
            {
                shell.RaidSession.CompleteSceneArrival(gameplaySceneKind);
            }

            playerPlaced = true;
            Debug.Log($"Player placed at spawn '{spawnId}' in scene '{activeSceneName}'.", this);
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
