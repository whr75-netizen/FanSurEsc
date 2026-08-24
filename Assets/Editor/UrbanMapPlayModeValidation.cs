using System;
using System.IO;
using FantasySurvival.Interaction;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using Unity.AI.Navigation;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

namespace FantasySurvival.EditorTools
{
    [InitializeOnLoad]
    public static class UrbanMapPlayModeValidation
    {
        private const string GameMapTestPath = "Assets/Scenes/GameMapTest.unity";
        private const string GameMapTestName = "GameMapTest";
        private const string GameMap1Name = "GameMap1";
        private const string RaidEntrySpawnId = "RaidEntry";
        private const string BaseReturnSpawnId = "BaseReturn";
        private const int RequiredRoundTrips = 3;
        private const int ReadyObservationCount = 2;

        private const string KeyPrefix = "FantasySurvival.UrbanMapValidation.";
        private const string RunningKey = KeyPrefix + "Running";
        private const string ExitWhenDoneKey = KeyPrefix + "ExitWhenDone";
        private const string PhaseKey = KeyPrefix + "Phase";
        private const string ReadyFramesKey = KeyPrefix + "ReadyFrames";
        private const string RoundTripsKey = KeyPrefix + "RoundTrips";
        private const string RuntimeErrorsKey = KeyPrefix + "RuntimeErrors";
        private const string RuntimeErrorDetailsKey = KeyPrefix + "RuntimeErrorDetails";
        private const string FailureKey = KeyPrefix + "Failure";
        private const string SuccessKey = KeyPrefix + "Success";
        private const string OriginalSceneSetupKey = KeyPrefix + "OriginalSceneSetup";
        private const string DeadlineKey = KeyPrefix + "Deadline";
        private const string ShellIdKey = KeyPrefix + "ShellId";
        private const string PlayerIdKey = KeyPrefix + "PlayerId";
        private const string CameraIdKey = KeyPrefix + "CameraId";
        private const string InventoryIdKey = KeyPrefix + "InventoryId";
        private const string EventSystemIdKey = KeyPrefix + "EventSystemId";
        private const string FirstSeedKey = KeyPrefix + "FirstSeed";
        private const string FirstHashKey = KeyPrefix + "FirstHash";

        private const string PhaseEnteringPlay = "EnteringPlay";
        private const string PhaseDirectMapTest = "DirectMapTest";
        private const string PhaseInitialBase = "InitialBase";
        private const string PhaseRoundTripMapTest = "RoundTripMapTest";
        private const string PhaseRoundTripBase = "RoundTripBase";
        private const string PhaseExitingPlay = "ExitingPlay";

        [Serializable]
        private sealed class ValidationResult
        {
            public bool success;
            public string timestampUtc;
            public string summary;
            public string failure;
            public int runtimeErrorCount;
            public string runtimeErrorDetails;
            public int completedRoundTrips;
            public int firstSeed;
            public string firstLayoutHash;
        }

        [Serializable]
        private sealed class SceneSetupSnapshot
        {
            public SceneSetupRecord[] scenes;
        }

        [Serializable]
        private sealed class SceneSetupRecord
        {
            public string path;
            public bool isLoaded;
            public bool isActive;
        }

        static UrbanMapPlayModeValidation()
        {
            RegisterCallbacks();
        }

        [MenuItem("Tools/Fantasy Survival/Urban Map/Run Play Mode Validation")]
        public static void StartInteractive()
        {
            StartValidation(exitWhenDone: false);
        }

        public static void StartBatch()
        {
            try
            {
                StartValidation(exitWhenDone: true);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        private static void RegisterCallbacks()
        {
            EditorApplication.playModeStateChanged -= HandlePlayModeStateChanged;
            EditorApplication.playModeStateChanged += HandlePlayModeStateChanged;
            EditorApplication.update -= HandleEditorUpdate;
            EditorApplication.update += HandleEditorUpdate;
            Application.logMessageReceived -= HandleRuntimeLog;
            Application.logMessageReceived += HandleRuntimeLog;
        }

        private static void StartValidation(bool exitWhenDone)
        {
            if (SessionState.GetBool(RunningKey, false))
            {
                throw new InvalidOperationException("Urban map Play Mode validation is already running.");
            }

            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new InvalidOperationException("Unity must be idle in Edit Mode before urban map validation starts.");
            }

            EnsureOpenScenesAreClean(requireRestorableSetup: !exitWhenDone);
            SceneSetup[] originalSceneSetup = exitWhenDone
                ? Array.Empty<SceneSetup>()
                : EditorSceneManager.GetSceneManagerSetup();
            string serializedSceneSetup = exitWhenDone
                ? string.Empty
                : SerializeSceneSetup(originalSceneSetup);

            try
            {
                Scene testScene = EditorSceneManager.OpenScene(GameMapTestPath, OpenSceneMode.Single);
                ProceduralUrbanMapGenerator[] configuredGenerators = FindComponentsInScene<ProceduralUrbanMapGenerator>(testScene);
                if (configuredGenerators.Length != 1 || configuredGenerators[0].GetComponent<NavMeshSurface>() == null)
                {
                    throw new InvalidOperationException(
                        "GameMapTest must contain exactly one configured ProceduralUrbanMapGenerator and NavMeshSurface before Play Mode validation.");
                }
            }
            catch
            {
                if (!exitWhenDone)
                {
                    EditorSceneManager.RestoreSceneManagerSetup(originalSceneSetup);
                }

                throw;
            }

            ClearSessionState();
            SessionState.SetBool(RunningKey, true);
            SessionState.SetBool(ExitWhenDoneKey, exitWhenDone);
            SessionState.SetString(OriginalSceneSetupKey, serializedSceneSetup);
            SessionState.SetString(DeadlineKey, DateTime.UtcNow.AddMinutes(3).Ticks.ToString());
            SetPhase(PhaseEnteringPlay);
            RegisterCallbacks();
            EditorApplication.isPlaying = true;
        }

        private static void HandlePlayModeStateChanged(PlayModeStateChange state)
        {
            if (!SessionState.GetBool(RunningKey, false))
            {
                return;
            }

            if (state == PlayModeStateChange.EnteredPlayMode)
            {
                SetPhase(PhaseDirectMapTest);
                return;
            }

            if (state == PlayModeStateChange.EnteredEditMode &&
                SessionState.GetString(PhaseKey, string.Empty) == PhaseExitingPlay)
            {
                FinishInEditMode();
            }
        }

        private static void HandleEditorUpdate()
        {
            if (!SessionState.GetBool(RunningKey, false))
            {
                return;
            }

            try
            {
                if (HasTimedOut())
                {
                    Fail("Urban map Play Mode validation timed out.");
                    return;
                }

                string phase = SessionState.GetString(PhaseKey, string.Empty);
                if (EditorApplication.isPlaying && phase == PhaseEnteringPlay)
                {
                    SetPhase(PhaseDirectMapTest);
                    phase = PhaseDirectMapTest;
                }

                if (!EditorApplication.isPlaying)
                {
                    return;
                }

                switch (phase)
                {
                    case PhaseDirectMapTest:
                        UpdateDirectMapTestPhase();
                        break;
                    case PhaseInitialBase:
                        UpdateInitialBasePhase();
                        break;
                    case PhaseRoundTripMapTest:
                        UpdateRoundTripMapTestPhase();
                        break;
                    case PhaseRoundTripBase:
                        UpdateRoundTripBasePhase();
                        break;
                }
            }
            catch (Exception exception)
            {
                Fail(exception.ToString());
            }
        }

        private static void UpdateDirectMapTestPhase()
        {
            if (!WaitForSceneReady(GameMapTestName, RaidEntrySpawnId))
            {
                return;
            }

            ProceduralUrbanMapGenerator generator = ValidateUrbanScene("direct GameMapTest start");
            ValidateShellAndSpawn(RaidEntrySpawnId, captureIdentity: true);
            SessionState.SetInt(FirstSeedKey, generator.CurrentSeed);
            SessionState.SetString(
                FirstHashKey,
                UrbanMapLayoutValidator.ComputeStableHash(generator.CurrentLayout).ToString("X16"));

            SetPhase(PhaseInitialBase);
            StartTravel(GameMap1Name, BaseReturnSpawnId);
        }

        private static void UpdateInitialBasePhase()
        {
            if (!WaitForSceneReady(GameMap1Name, BaseReturnSpawnId))
            {
                return;
            }

            ValidateShellAndSpawn(BaseReturnSpawnId, captureIdentity: false);
            SetPhase(PhaseRoundTripMapTest);
            StartTravel(GameMapTestName, RaidEntrySpawnId);
        }

        private static void UpdateRoundTripMapTestPhase()
        {
            if (!WaitForSceneReady(GameMapTestName, RaidEntrySpawnId))
            {
                return;
            }

            int nextRoundTrip = SessionState.GetInt(RoundTripsKey, 0) + 1;
            ValidateUrbanScene($"round trip {nextRoundTrip} GameMapTest arrival");
            ValidateShellAndSpawn(RaidEntrySpawnId, captureIdentity: false);
            SetPhase(PhaseRoundTripBase);
            StartTravel(GameMap1Name, BaseReturnSpawnId);
        }

        private static void UpdateRoundTripBasePhase()
        {
            if (!WaitForSceneReady(GameMap1Name, BaseReturnSpawnId))
            {
                return;
            }

            ValidateShellAndSpawn(BaseReturnSpawnId, captureIdentity: false);
            int completedRoundTrips = SessionState.GetInt(RoundTripsKey, 0) + 1;
            SessionState.SetInt(RoundTripsKey, completedRoundTrips);

            if (completedRoundTrips < RequiredRoundTrips)
            {
                SetPhase(PhaseRoundTripMapTest);
                StartTravel(GameMapTestName, RaidEntrySpawnId);
                return;
            }

            int runtimeErrors = SessionState.GetInt(RuntimeErrorsKey, 0);
            if (runtimeErrors != 0)
            {
                Fail($"Play Mode produced {runtimeErrors} Error/Exception/Assert log entries.");
                return;
            }

            Succeed();
        }

        private static bool WaitForSceneReady(string expectedSceneName, string expectedSpawnId)
        {
            if (!string.Equals(SceneManager.GetActiveScene().name, expectedSceneName, StringComparison.Ordinal) ||
                DirectSceneTravel.IsLoading || DirectSceneTravel.HasPendingTravel)
            {
                SessionState.SetInt(ReadyFramesKey, 0);
                return false;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            SceneSpawnPoint spawn = FindSpawnPoint(SceneManager.GetActiveScene(), expectedSpawnId);
            if (shell == null || shell.PlayerTransform == null || spawn == null ||
                Vector3.Distance(shell.PlayerTransform.position, spawn.transform.position) > 0.15f)
            {
                SessionState.SetInt(ReadyFramesKey, 0);
                return false;
            }

            if (string.Equals(expectedSceneName, GameMapTestName, StringComparison.Ordinal))
            {
                EnemyAIController[] enemies = FindComponentsInScene<EnemyAIController>(
                    SceneManager.GetActiveScene());
                if (enemies.Length != 2)
                {
                    SessionState.SetInt(ReadyFramesKey, 0);
                    return false;
                }

                for (int index = 0; index < enemies.Length; index++)
                {
                    if (!enemies[index].IsNavigationReady)
                    {
                        SessionState.SetInt(ReadyFramesKey, 0);
                        return false;
                    }
                }
            }

            int readyFrames = SessionState.GetInt(ReadyFramesKey, 0) + 1;
            SessionState.SetInt(ReadyFramesKey, readyFrames);
            return readyFrames >= ReadyObservationCount;
        }

        private static ProceduralUrbanMapGenerator ValidateUrbanScene(string context)
        {
            Scene activeScene = SceneManager.GetActiveScene();
            ProceduralUrbanMapGenerator[] generators = FindComponentsInScene<ProceduralUrbanMapGenerator>(activeScene);
            Require(generators.Length == 1, $"{context}: expected one ProceduralUrbanMapGenerator, found {generators.Length}.");

            ProceduralUrbanMapGenerator generator = generators[0];
            UrbanMapLayout layout = generator.CurrentLayout;
            Require(generator.enabled, $"{context}: generator is disabled.");
            Require(layout != null, $"{context}: CurrentLayout is null.");
            Require(layout.Roads.Count > 0, $"{context}: no roads were generated.");
            Require(layout.Buildings.Count > 0, $"{context}: no graybox buildings were generated.");
            Require(generator.GeneratedContent != null && generator.GeneratedContent.gameObject.activeInHierarchy,
                $"{context}: generated content root is missing or inactive.");
            Require(generator.GeneratedContent.parent == generator.transform,
                $"{context}: generated content is not owned by the scene-local generator.");
            Require(!generator.NavigationBuildPending,
                $"{context}: runtime NavMesh build is still pending.");
            Require(generator.NavigationPathComplete,
                $"{context}: RaidEntry-to-ReturnPortal NavMesh path is not complete.");

            NavMeshSurface surface = generator.GetComponent<NavMeshSurface>();
            Require(surface != null && surface.navMeshData != null,
                $"{context}: runtime NavMeshData is missing.");

            UrbanMapGenerationParameters parameters = generator.GenerationParameters;
            Require(layout.CityRotationDegrees >= parameters.CityRotationMin - 0.01f &&
                    layout.CityRotationDegrees <= parameters.CityRotationMax + 0.01f,
                $"{context}: city rotation {layout.CityRotationDegrees:F2} is outside the configured range.");

            if (!UrbanMapLayoutValidator.TryValidate(layout, parameters, out string layoutError))
            {
                throw new InvalidOperationException($"{context}: runtime layout failed validation: {layoutError}");
            }

            ValidateGeneratedGeometry(generator, context);
            ValidateExistingSceneObjects(generator, context);
            return generator;
        }

        private static void ValidateGeneratedGeometry(ProceduralUrbanMapGenerator generator, string context)
        {
            Transform generated = generator.GeneratedContent;
            int groundCount = 0;
            int roadCount = 0;
            int buildingCount = 0;
            int boundaryCount = 0;

            for (int childIndex = 0; childIndex < generated.childCount; childIndex++)
            {
                GameObject child = generated.GetChild(childIndex).gameObject;
                if (child.name == "GeneratedGround")
                {
                    groundCount++;
                    Require(child.TryGetComponent(out Collider groundCollider) && groundCollider.enabled,
                        $"{context}: generated ground collider is missing or disabled.");
                    Require(!child.CompareTag("Obstacle"), $"{context}: generated ground must not block PlayerMovement.");
                    continue;
                }

                if (child.name.StartsWith("Road_", StringComparison.Ordinal) ||
                    child.name.StartsWith("PrimaryRoad_", StringComparison.Ordinal))
                {
                    roadCount++;
                    Collider roadCollider = child.GetComponent<Collider>();
                    Require(roadCollider == null || !roadCollider.enabled,
                        $"{context}: road '{child.name}' has an enabled collider.");
                    Require(!child.CompareTag("Obstacle"), $"{context}: road '{child.name}' is tagged as an obstacle.");
                    continue;
                }

                if (child.name.StartsWith("Building_", StringComparison.Ordinal))
                {
                    buildingCount++;
                    Require(child.TryGetComponent(out Collider buildingCollider) && buildingCollider.enabled,
                        $"{context}: building '{child.name}' has no enabled collider.");
                    Require(child.CompareTag("Obstacle"), $"{context}: building '{child.name}' is not tagged Obstacle.");
                    Require(child.GetComponent<NavMeshModifier>() != null,
                        $"{context}: building '{child.name}' has no NavMeshModifier.");
                    continue;
                }

                if (child.name.StartsWith("Boundary_", StringComparison.Ordinal))
                {
                    boundaryCount++;
                    Require(child.TryGetComponent(out Collider boundaryCollider) && boundaryCollider.enabled,
                        $"{context}: boundary '{child.name}' has no enabled collider.");
                    Require(child.CompareTag("Obstacle"), $"{context}: boundary '{child.name}' is not tagged Obstacle.");
                    continue;
                }

            }

            Require(groundCount == 1, $"{context}: expected one generated ground, found {groundCount}.");
            Require(roadCount == generator.CurrentLayout.Roads.Count,
                $"{context}: generated road object count {roadCount} does not match layout count {generator.CurrentLayout.Roads.Count}.");
            Require(buildingCount == generator.CurrentLayout.Buildings.Count,
                $"{context}: generated building object count {buildingCount} does not match layout count {generator.CurrentLayout.Buildings.Count}.");
            Require(boundaryCount == 4, $"{context}: expected four map boundaries, found {boundaryCount}.");
        }

        private static void ValidateExistingSceneObjects(ProceduralUrbanMapGenerator generator, string context)
        {
            Scene activeScene = SceneManager.GetActiveScene();
            GameObject legacyGround = FindRootByName(activeScene, "Plane");
            Require(legacyGround != null && !legacyGround.activeSelf,
                $"{context}: legacy Plane is missing or still active.");

            ReturnPortalInteractable[] portals = FindComponentsInScene<ReturnPortalInteractable>(activeScene);
            Require(portals.Length == 1, $"{context}: expected one existing ReturnPortal, found {portals.Length}.");
            Transform portal = portals[0].transform;
            Require(!portal.IsChildOf(generator.GeneratedContent),
                $"{context}: existing ReturnPortal was incorrectly reparented under generated content.");
            Require(portal.TryGetComponent(out Collider portalCollider) && portalCollider.enabled,
                $"{context}: ReturnPortal collider is missing or disabled.");
            Require(portal.CompareTag("Obstacle"), $"{context}: ReturnPortal lost its Obstacle tag.");

            Vector3 expectedPortalPosition = generator.GeneratedContent.TransformPoint(
                new Vector3(
                    generator.CurrentLayout.PortalLocalPosition.x,
                    0.5f,
                    generator.CurrentLayout.PortalLocalPosition.y));
            Require(Vector3.Distance(portal.position, expectedPortalPosition) <= 0.05f,
                $"{context}: ReturnPortal was not placed at the generated portal node.");

            EnemyAIController[] enemies = FindComponentsInScene<EnemyAIController>(activeScene);
            Require(enemies.Length == 2, $"{context}: expected two prototype enemies, found {enemies.Length}.");

            int meleeCount = 0;
            int rangedCount = 0;
            for (int index = 0; index < enemies.Length; index++)
            {
                EnemyStats stats = enemies[index].GetComponent<EnemyStats>();
                EnemyAISettings ai = stats != null && stats.Definition != null
                    ? stats.Definition.AI
                    : null;
                Require(ai != null, $"{context}: enemy '{enemies[index].name}' has no AI definition.");
                Require(enemies[index].IsNavigationReady,
                    $"{context}: enemy '{enemies[index].name}' is not ready on the runtime NavMesh.");

                if (ai.CombatArchetype == EnemyCombatArchetype.MeleeRush)
                {
                    meleeCount++;
                }
                else if (ai.CombatArchetype == EnemyCombatArchetype.RangedPursuit)
                {
                    rangedCount++;
                }
            }

            Require(meleeCount == 1 && rangedCount == 1,
                $"{context}: expected one melee and one ranged enemy, found melee={meleeCount}, ranged={rangedCount}.");
        }

        private static void ValidateShellAndSpawn(string expectedSpawnId, bool captureIdentity)
        {
            PersistentGameplayShell[] shells = UnityEngine.Object.FindObjectsByType<PersistentGameplayShell>(
                FindObjectsInactive.Include);
            Require(shells.Length == 1, $"Expected one PersistentGameplayShell, found {shells.Length}.");

            PersistentGameplayShell shell = shells[0];
            Require(PersistentGameplayShell.Instance == shell, "PersistentGameplayShell.Instance does not match the only shell.");
            Require(shell.PlayerTransform != null && shell.PlayerCamera != null &&
                    shell.PlayerEventSystem != null && shell.InventoryUI != null,
                "PersistentGameplayShell has a missing required public reference.");

            PlayerMovement[] players = UnityEngine.Object.FindObjectsByType<PlayerMovement>(
                FindObjectsInactive.Include);
            InventoryUIManager[] inventories = UnityEngine.Object.FindObjectsByType<InventoryUIManager>(
                FindObjectsInactive.Include);
            EventSystem[] eventSystems = UnityEngine.Object.FindObjectsByType<EventSystem>(
                FindObjectsInactive.Include);
            Require(players.Length == 1 && players[0].transform.IsChildOf(shell.transform),
                $"PlayerMovement count/ownership is invalid: {players.Length}.");
            Require(inventories.Length == 1 && inventories[0] == shell.InventoryUI,
                $"InventoryUIManager count/identity is invalid: {inventories.Length}.");
            Require(eventSystems.Length == 1 && eventSystems[0] == shell.PlayerEventSystem,
                $"EventSystem count/identity is invalid: {eventSystems.Length}.");
            Require(Camera.allCamerasCount == 1 && shell.PlayerCamera.isActiveAndEnabled,
                $"Active gameplay Camera count is {Camera.allCamerasCount}, expected one.");

            Camera[] activeSceneCameras = FindComponentsInScene<Camera>(SceneManager.GetActiveScene());
            for (int index = 0; index < activeSceneCameras.Length; index++)
            {
                Camera sceneCamera = activeSceneCameras[index];
                Transform root = sceneCamera.transform.root;
                Require(root.CompareTag("EditorOnly") && !sceneCamera.isActiveAndEnabled,
                    $"Scene-local Camera '{sceneCamera.name}' is not an inactive EditorOnly preview Camera.");
            }

            AudioListener[] listeners = UnityEngine.Object.FindObjectsByType<AudioListener>(
                FindObjectsInactive.Exclude);
            int enabledListenerCount = 0;
            for (int index = 0; index < listeners.Length; index++)
            {
                if (listeners[index].enabled && listeners[index].gameObject.activeInHierarchy)
                {
                    enabledListenerCount++;
                }
            }

            Require(enabledListenerCount == 1, $"Enabled AudioListener count is {enabledListenerCount}, expected one.");

            if (captureIdentity)
            {
                SessionState.SetString(ShellIdKey, GetIdentity(shell));
                SessionState.SetString(PlayerIdKey, GetIdentity(shell.PlayerTransform));
                SessionState.SetString(CameraIdKey, GetIdentity(shell.PlayerCamera));
                SessionState.SetString(InventoryIdKey, GetIdentity(shell.InventoryUI));
                SessionState.SetString(EventSystemIdKey, GetIdentity(shell.PlayerEventSystem));
            }
            else
            {
                RequireIdentity(ShellIdKey, shell, "PersistentGameplayShell");
                RequireIdentity(PlayerIdKey, shell.PlayerTransform, "Player");
                RequireIdentity(CameraIdKey, shell.PlayerCamera, "Camera");
                RequireIdentity(InventoryIdKey, shell.InventoryUI, "InventoryUIManager");
                RequireIdentity(EventSystemIdKey, shell.PlayerEventSystem, "EventSystem");
            }

            SceneSpawnPoint expectedSpawn = FindSpawnPoint(SceneManager.GetActiveScene(), expectedSpawnId);
            Require(expectedSpawn != null, $"Active scene has no spawn point '{expectedSpawnId}'.");
            Require(Vector3.Distance(shell.PlayerTransform.position, expectedSpawn.transform.position) <= 0.15f,
                $"Player is not at spawn '{expectedSpawnId}'.");

            Rigidbody playerBody = shell.PlayerTransform.GetComponent<Rigidbody>();
            if (playerBody != null)
            {
                Require(playerBody.linearVelocity.sqrMagnitude <= 0.0001f &&
                        playerBody.angularVelocity.sqrMagnitude <= 0.0001f,
                    $"Player Rigidbody velocity was not cleared at spawn '{expectedSpawnId}'.");
            }
        }

        private static void StartTravel(string destinationScene, string spawnId)
        {
            SessionState.SetInt(ReadyFramesKey, 0);
            if (!DirectSceneTravel.TryLoad(destinationScene, spawnId))
            {
                throw new InvalidOperationException(
                    $"DirectSceneTravel rejected validation travel to '{destinationScene}' spawn '{spawnId}'.");
            }
        }

        private static void Succeed()
        {
            SessionState.SetBool(SuccessKey, true);
            SessionState.SetString(FailureKey, string.Empty);
            SessionState.SetString(PhaseKey, PhaseExitingPlay);
            EditorApplication.isPlaying = false;
        }

        private static void Fail(string reason)
        {
            if (!SessionState.GetBool(RunningKey, false))
            {
                return;
            }

            SessionState.SetBool(SuccessKey, false);
            SessionState.SetString(FailureKey, reason ?? "Unknown validation failure.");
            SessionState.SetString(PhaseKey, PhaseExitingPlay);
            Debug.LogWarning($"[URBAN-MAP-VALIDATION] stopping after validation failure: {reason}");

            if (EditorApplication.isPlaying)
            {
                EditorApplication.isPlaying = false;
            }
            else
            {
                FinishInEditMode();
            }
        }

        private static void FinishInEditMode()
        {
            if (!SessionState.GetBool(RunningKey, false))
            {
                return;
            }

            bool success = SessionState.GetBool(SuccessKey, false);
            string failure = SessionState.GetString(FailureKey, string.Empty);
            Scene activeScene = SceneManager.GetActiveScene();
            if (!activeScene.IsValid() ||
                !string.Equals(activeScene.path, GameMapTestPath, StringComparison.Ordinal))
            {
                success = false;
                failure = AppendFailure(
                    failure,
                    $"Edit Mode did not restore '{GameMapTestPath}'. Active scene is '{activeScene.path}'.");
            }

            if (activeScene.IsValid() && activeScene.isDirty)
            {
                success = false;
                failure = AppendFailure(failure, "GameMapTest became dirty after Play Mode validation.");
            }

            int runtimeErrorCount = SessionState.GetInt(RuntimeErrorsKey, 0);
            if (runtimeErrorCount != 0)
            {
                success = false;
                failure = AppendFailure(
                    failure,
                    $"Play Mode, including teardown, produced {runtimeErrorCount} Error/Exception/Assert log entries.");
            }

            var result = new ValidationResult
            {
                success = success,
                timestampUtc = DateTime.UtcNow.ToString("O"),
                summary = success
                    ? $"Direct GameMapTest start and {RequiredRoundTrips} DirectSceneTravel round trips passed."
                    : "Urban map Play Mode validation failed.",
                failure = failure,
                runtimeErrorCount = runtimeErrorCount,
                runtimeErrorDetails = SessionState.GetString(RuntimeErrorDetailsKey, string.Empty),
                completedRoundTrips = SessionState.GetInt(RoundTripsKey, 0),
                firstSeed = SessionState.GetInt(FirstSeedKey, 0),
                firstLayoutHash = SessionState.GetString(FirstHashKey, string.Empty)
            };

            bool exitWhenDone = SessionState.GetBool(ExitWhenDoneKey, false);
            string originalSceneSetup = SessionState.GetString(OriginalSceneSetupKey, string.Empty);
            Exception finalizationException = null;

            try
            {
                if (!exitWhenDone)
                {
                    RestoreSceneSetup(originalSceneSetup);
                }

                WriteResult(result);
            }
            catch (Exception exception)
            {
                finalizationException = exception;
                success = false;
                result.success = false;
                result.failure = AppendFailure(result.failure, $"Validation finalization failed: {exception.Message}");
            }
            finally
            {
                ClearSessionState();

                if (finalizationException != null)
                {
                    Debug.LogException(finalizationException);
                }

                if (success)
                {
                    Debug.Log($"[URBAN-MAP-VALIDATION] PASS: {result.summary}");
                }
                else
                {
                    Debug.LogError($"[URBAN-MAP-VALIDATION] FAIL: {result.failure}");
                }

                if (exitWhenDone)
                {
                    EditorApplication.Exit(success ? 0 : 1);
                }
            }
        }

        private static void HandleRuntimeLog(string condition, string stackTrace, LogType type)
        {
            if (!SessionState.GetBool(RunningKey, false) ||
                (type != LogType.Error && type != LogType.Exception && type != LogType.Assert))
            {
                return;
            }

            int errorCount = SessionState.GetInt(RuntimeErrorsKey, 0) + 1;
            SessionState.SetInt(RuntimeErrorsKey, errorCount);
            if (errorCount <= 5)
            {
                string details = SessionState.GetString(RuntimeErrorDetailsKey, string.Empty);
                SessionState.SetString(
                    RuntimeErrorDetailsKey,
                    details + $"[{type}] {condition}\n{stackTrace}\n");
            }
        }

        private static void SetPhase(string phase)
        {
            SessionState.SetString(PhaseKey, phase);
            SessionState.SetInt(ReadyFramesKey, 0);
        }

        private static string AppendFailure(string existing, string addition)
        {
            return string.IsNullOrEmpty(existing) ? addition : existing + " " + addition;
        }

        private static bool HasTimedOut()
        {
            string deadlineText = SessionState.GetString(DeadlineKey, string.Empty);
            return !long.TryParse(deadlineText, out long deadlineTicks) || DateTime.UtcNow.Ticks > deadlineTicks;
        }

        private static void EnsureOpenScenesAreClean(bool requireRestorableSetup = true)
        {
            for (int sceneIndex = 0; sceneIndex < SceneManager.sceneCount; sceneIndex++)
            {
                Scene openScene = SceneManager.GetSceneAt(sceneIndex);
                if (openScene.isDirty)
                {
                    throw new InvalidOperationException(
                        $"Validation stopped because open scene '{openScene.name}' has unsaved changes.");
                }

                if (requireRestorableSetup && string.IsNullOrEmpty(openScene.path))
                {
                    throw new InvalidOperationException(
                        $"Validation stopped because open scene '{openScene.name}' has no saved asset path and cannot be restored safely.");
                }
            }
        }

        private static string SerializeSceneSetup(SceneSetup[] setup)
        {
            var snapshot = new SceneSetupSnapshot
            {
                scenes = new SceneSetupRecord[setup.Length]
            };

            for (int index = 0; index < setup.Length; index++)
            {
                snapshot.scenes[index] = new SceneSetupRecord
                {
                    path = setup[index].path,
                    isLoaded = setup[index].isLoaded,
                    isActive = setup[index].isActive
                };
            }

            return JsonUtility.ToJson(snapshot);
        }

        private static void RestoreSceneSetup(string serializedSetup)
        {
            SceneSetupSnapshot snapshot = JsonUtility.FromJson<SceneSetupSnapshot>(serializedSetup);
            if (snapshot?.scenes == null || snapshot.scenes.Length == 0)
            {
                throw new InvalidOperationException("Original Editor scene setup is missing or invalid.");
            }

            var setup = new SceneSetup[snapshot.scenes.Length];
            for (int index = 0; index < snapshot.scenes.Length; index++)
            {
                SceneSetupRecord record = snapshot.scenes[index];
                if (record == null || string.IsNullOrEmpty(record.path))
                {
                    throw new InvalidOperationException("Original Editor scene setup contains an invalid scene path.");
                }

                setup[index] = new SceneSetup
                {
                    path = record.path,
                    isLoaded = record.isLoaded,
                    isActive = record.isActive
                };
            }

            EditorSceneManager.RestoreSceneManagerSetup(setup);
        }

        private static void WriteResult(ValidationResult result)
        {
            string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            string logsDirectory = Path.Combine(projectRoot, "Logs");
            Directory.CreateDirectory(logsDirectory);
            string resultPath = Path.Combine(logsDirectory, "urban_map_playmode_validation.json");
            File.WriteAllText(resultPath, JsonUtility.ToJson(result, prettyPrint: true));
        }

        private static string GetIdentity(UnityEngine.Object target)
        {
            Require(target != null, "Cannot capture identity for a null Unity object.");
            return target.GetEntityId().ToString();
        }

        private static void RequireIdentity(string key, UnityEngine.Object target, string label)
        {
            string expected = SessionState.GetString(key, string.Empty);
            string actual = GetIdentity(target);
            Require(!string.IsNullOrEmpty(expected) && string.Equals(expected, actual, StringComparison.Ordinal),
                $"{label} identity changed. Expected={expected}, Actual={actual}.");
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new InvalidOperationException(message);
            }
        }

        private static SceneSpawnPoint FindSpawnPoint(Scene scene, string spawnId)
        {
            SceneSpawnPoint[] spawnPoints = FindComponentsInScene<SceneSpawnPoint>(scene);
            for (int index = 0; index < spawnPoints.Length; index++)
            {
                if (spawnPoints[index].SpawnId == spawnId)
                {
                    return spawnPoints[index];
                }
            }

            return null;
        }

        private static T[] FindComponentsInScene<T>(Scene scene) where T : Component
        {
            var components = new System.Collections.Generic.List<T>();
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                components.AddRange(roots[index].GetComponentsInChildren<T>(true));
            }

            return components.ToArray();
        }

        private static GameObject FindRootByName(Scene scene, string objectName)
        {
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                if (roots[index].name == objectName)
                {
                    return roots[index];
                }
            }

            return null;
        }

        private static void ClearSessionState()
        {
            SessionState.SetBool(RunningKey, false);
            SessionState.SetBool(ExitWhenDoneKey, false);
            SessionState.SetString(PhaseKey, string.Empty);
            SessionState.SetInt(ReadyFramesKey, 0);
            SessionState.SetInt(RoundTripsKey, 0);
            SessionState.SetInt(RuntimeErrorsKey, 0);
            SessionState.SetString(RuntimeErrorDetailsKey, string.Empty);
            SessionState.SetString(FailureKey, string.Empty);
            SessionState.SetBool(SuccessKey, false);
            SessionState.SetString(OriginalSceneSetupKey, string.Empty);
            SessionState.SetString(DeadlineKey, string.Empty);
            SessionState.SetString(ShellIdKey, string.Empty);
            SessionState.SetString(PlayerIdKey, string.Empty);
            SessionState.SetString(CameraIdKey, string.Empty);
            SessionState.SetString(InventoryIdKey, string.Empty);
            SessionState.SetString(EventSystemIdKey, string.Empty);
            SessionState.SetInt(FirstSeedKey, 0);
            SessionState.SetString(FirstHashKey, string.Empty);
        }
    }
}
