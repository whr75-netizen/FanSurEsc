using System;
using FantasySurvival.BaseBuilding;
using FantasySurvival.SaveSystem;
using FantasySurvival.SceneFlow;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Raids
{
    /// <summary>
    /// Projects the authoritative live raid state into a recoverable checkpoint.
    /// This component owns checkpoint timing and recovery orchestration, but it does
    /// not become a second gameplay-state owner.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class RaidCheckpointController : MonoBehaviour
    {
        private enum RaidEntryOrigin
        {
            None,
            Fresh,
            Recovered
        }

        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private BaseFurnitureDatabase furnitureDatabase;
        [SerializeField] private string supportedRaidScene = "GameMapTest";
        [SerializeField] private string supportedSceneStateId = "core:gamemaptest:v1";
        [SerializeField, Min(0.25f)] private float checkpointIntervalSeconds = 1f;
        [SerializeField, Min(0f)] private float importantChangeDelaySeconds = 0.1f;
        [SerializeField, Min(0.25f)] private float minimumWriteGapSeconds = 1f;

        private RaidRecoveryBaselineData baseline;
        private RaidCheckpointData lastCheckpoint;
        private RaidCheckpointData pendingRestore;
        private GameSaveData pendingExactSettlementState;
        private RaidSettlementJournalKind pendingExactSettlementKind;
        private bool ordinarySettlementMirrored;
        private RaidCheckpointSceneBinding activeSceneBinding;
        private long nextSequence;
        private float nextCheckpointAt;
        private float lastSuccessfulWriteAt = float.NegativeInfinity;
        private bool raidTracked;
        private bool handlingWriteFailure;
        private bool basePersistenceReady;
        private bool baseArrivalComplete;
        private RaidEntryOrigin entryOrigin;
        private RaidOutcome trackedOutcome;
        private bool settlementInputLockHeld;
        private bool settlementMovementWasEnabled;
        private bool settlementInventoryInputWasBlocked;
        private bool settlementInteractionWasBlocked;
        private bool settlementDamageWasBlocked;

        public bool IsConfigured =>
            shell != null &&
            shell.PlayerTransform != null &&
            shell.PlayerStats != null &&
            shell.InventoryUI != null &&
            furnitureDatabase != null &&
             !string.IsNullOrWhiteSpace(supportedRaidScene) &&
             !string.IsNullOrWhiteSpace(supportedSceneStateId) &&
             checkpointIntervalSeconds >= 0.25f &&
             minimumWriteGapSeconds >= 0.25f;

        public bool HasTrackedRaid => raidTracked && baseline != null;
        public bool HasPendingRestore => pendingRestore != null;
        public bool IsSettlementInputLocked => settlementInputLockHeld;
        public bool HasPendingBaseSettlement =>
            HasTrackedRaid && basePersistenceReady && baseArrivalComplete;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(RaidCheckpointController)} has missing required configuration.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            if (shell?.PlayerStats != null)
            {
                shell.PlayerStats.HealthChanged += HandlePlayerHealthChanged;
            }

            if (shell?.RaidSession != null)
            {
                shell.RaidSession.Resolved += HandleRaidResolved;
            }
        }

        private void OnDisable()
        {
            if (shell?.PlayerStats != null)
            {
                shell.PlayerStats.HealthChanged -= HandlePlayerHealthChanged;
            }

            if (shell?.RaidSession != null)
            {
                shell.RaidSession.Resolved -= HandleRaidResolved;
            }
        }

        private void Update()
        {
            if (!ShouldCaptureActiveRaid() || Time.unscaledTime < nextCheckpointAt)
            {
                return;
            }

            if (!TryCaptureAndWrite(RaidCheckpointPhase.Active, RaidOutcome.None, out string error))
            {
                HandleCheckpointWriteFailure($"Periodic raid recovery checkpoint failed: {error}");
            }
        }

        private void OnApplicationPause(bool paused)
        {
            if (paused)
            {
                TryWriteBestEffortShutdownCheckpoint();
            }
        }

        private void OnApplicationQuit()
        {
            TryWriteBestEffortShutdownCheckpoint();
        }

        public bool TryPrepareNewRaid(
            string destinationScene,
            string destinationSpawnId,
            out string error)
        {
            if (!isActiveAndEnabled || !IsConfigured)
            {
                error = "Raid recovery controller is unavailable.";
                return false;
            }

            if (raidTracked || baseline != null)
            {
                error = "An unsettled raid recovery already exists.";
                return false;
            }

            GameSaveData ordinaryHeader = GetAuthoritativeOrdinarySave();
            if (ordinaryHeader != null && ordinaryHeader.raidInProgress)
            {
                error = "The ordinary save already declares an unresolved raid. " +
                        "Resolve it from the Main Menu before starting another raid.";
                return false;
            }

            if (RaidCheckpointStore.HasRecoveryArtifacts)
            {
                error = "Unreferenced or unsettled raid recovery files already exist.";
                return false;
            }

            if (!TryResolveSceneStateId(destinationScene, out string sceneStateId) ||
                string.IsNullOrWhiteSpace(destinationSpawnId))
            {
                error = $"Raid scene '{destinationScene}' is not configured for recovery.";
                return false;
            }

            if (!TryCapturePersistentState(out GameSaveData startingState, out error))
            {
                error = $"Could not capture the raid-start baseline: {error}";
                return false;
            }

            var candidate = new RaidRecoveryBaselineData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidRecoveryBaselineData.CurrentFormatVersion,
                raidInstanceId = Guid.NewGuid().ToString("D"),
                createdAtUtc = DateTime.UtcNow.ToString("O"),
                raidScene = destinationScene,
                raidSpawnId = destinationSpawnId,
                sceneStateId = sceneStateId,
                startingState = startingState
            };

            if (!TryValidateBaseline(candidate, out error))
            {
                error = $"Could not validate the raid-start state: {error}";
                return false;
            }

            if (!TryWriteRaidInProgressOrdinaryMarker(candidate, out error))
            {
                error = $"Could not mirror the active-raid marker into the ordinary save: {error}";
                return false;
            }

            // The ordinary marker is deliberately first. If baseline creation now
            // fails or the process stops in between, the next Main Menu sees
            // marker-without-cache and fails the attempted raid instead of guessing.
            if (!RaidCheckpointStore.TryCreateBaseline(candidate, out error))
            {
                error = $"Could not create a durable raid-start baseline: {error}";
                return false;
            }

            baseline = candidate;
            lastCheckpoint = null;
            pendingRestore = null;
            pendingExactSettlementState = null;
            pendingExactSettlementKind = RaidSettlementJournalKind.None;
            ordinarySettlementMirrored = false;
            nextSequence = 0;
            raidTracked = true;
            handlingWriteFailure = false;
            basePersistenceReady = false;
            baseArrivalComplete = false;
            entryOrigin = RaidEntryOrigin.Fresh;
            trackedOutcome = RaidOutcome.None;
            lastSuccessfulWriteAt = float.NegativeInfinity;
            nextCheckpointAt = Time.unscaledTime;
            error = null;
            return true;
        }

        private bool TryWriteRaidInProgressOrdinaryMarker(
            RaidRecoveryBaselineData candidateBaseline,
            out string error)
        {
            GameSaveData markedSave;
            try
            {
                markedSave = JsonUtility.FromJson<GameSaveData>(
                    JsonUtility.ToJson(candidateBaseline.startingState));
            }
            catch (Exception exception)
            {
                error = $"Could not clone the raid-start ordinary save: {exception.Message}";
                return false;
            }

            if (markedSave == null)
            {
                error = "Could not clone the raid-start ordinary save.";
                return false;
            }

            markedSave.savedAtUtc = DateTime.UtcNow.ToString("O");
            markedSave.raidInProgress = true;
            markedSave.activeRaidInstanceId = candidateBaseline.raidInstanceId;

            StandardStashViewData playerInventory = shell.InventoryUI.PlayerInventoryData;
            if (playerInventory == null)
            {
                error = "Player inventory dimensions are unavailable for active-raid marker validation.";
                return false;
            }

            return GameSaveManager.TryWriteSlotOneMirrored(
                markedSave,
                shell.InventoryUI.ItemDatabase,
                furnitureDatabase,
                playerInventory.CapacityWidth,
                playerInventory.CapacityHeight,
                out error);
        }

        public bool TryPreflightRecoveredRaid(
            RaidRecoveryBaselineData recoveredBaseline,
            RaidCheckpointData recoveredCheckpoint,
            out string error)
        {
            if (!isActiveAndEnabled || !IsConfigured || shell.RaidSession == null)
            {
                error = "Raid recovery controller is unavailable.";
                return false;
            }

            if (raidTracked || baseline != null || pendingRestore != null)
            {
                error = "A raid is already staged in the current gameplay session.";
                return false;
            }

            if (shell.RaidSession.CurrentSceneKind != GameplaySceneKind.Base ||
                shell.RaidSession.State != RaidSessionState.Inactive ||
                DirectSceneTravel.IsLoading ||
                shell.IsTravelPrepared)
            {
                error = "Raid recovery can begin only from an idle, fully arrived base scene.";
                return false;
            }

            // The ordinary slot is the authority for whether there is an active raid.
            // Do not inspect or trust a recovery payload until its marker still names it.
            if (!HasMatchingOrdinaryRaidMarker(recoveredBaseline?.raidInstanceId))
            {
                error = "The ordinary save no longer declares this active raid.";
                return false;
            }

            if (RaidCheckpointStore.HasSettlementJournalArtifacts)
            {
                error = "This raid already has a fail/settlement decision and cannot be resumed.";
                return false;
            }

            if (recoveredCheckpoint == null ||
                recoveredCheckpoint.phase != RaidCheckpointPhase.Active)
            {
                error = "Only an active raid checkpoint can be resumed.";
                return false;
            }

            if (!TryValidateCheckpoint(recoveredBaseline, recoveredCheckpoint, out error) ||
                !TryResolveSceneStateId(recoveredBaseline.raidScene, out string sceneStateId) ||
                !string.Equals(
                    sceneStateId,
                    recoveredBaseline.sceneStateId,
                    StringComparison.Ordinal))
            {
                error = $"Raid resume data is incompatible with the current project: {error}";
                return false;
            }

            if (!Mathf.Approximately(
                    recoveredCheckpoint.playerMaxHealth,
                    shell.PlayerStats.MaxHealth) ||
                recoveredCheckpoint.playerCurrentHealth <= 0f ||
                recoveredCheckpoint.playerCurrentHealth > shell.PlayerStats.MaxHealth)
            {
                error = "Recovered Player health is incompatible with the current Player definition.";
                return false;
            }

            if (!Application.CanStreamedLevelBeLoaded(recoveredBaseline.raidScene))
            {
                error = $"Raid scene '{recoveredBaseline.raidScene}' is not available in Build Settings.";
                return false;
            }

            if (!RaidCheckpointStore.TryReadBaseline(
                    out RaidRecoveryBaselineData storedBaseline,
                    out error) ||
                !TryValidateBaseline(storedBaseline, out error) ||
                !AreCanonicalJsonEquivalent(storedBaseline, recoveredBaseline))
            {
                error = $"Raid resume no longer matches its durable baseline: {error}";
                return false;
            }

            RaidCheckpointStore.ReadCheckpointCandidates(
                out RaidCheckpointData storedPrimary,
                out _,
                out RaidCheckpointData storedBackup,
                out _);
            bool matchesPrimary =
                TryValidateCheckpoint(storedBaseline, storedPrimary, out _) &&
                AreCanonicalJsonEquivalent(storedPrimary, recoveredCheckpoint);
            bool matchesBackup =
                TryValidateCheckpoint(storedBaseline, storedBackup, out _) &&
                AreCanonicalJsonEquivalent(storedBackup, recoveredCheckpoint);
            if (!matchesPrimary && !matchesBackup)
            {
                error = "The selected raid checkpoint changed or disappeared before resume began.";
                return false;
            }

            RaidCheckpointData newestStored = null;
            if (TryValidateCheckpoint(storedBaseline, storedPrimary, out _))
            {
                newestStored = storedPrimary;
            }
            if (TryValidateCheckpoint(storedBaseline, storedBackup, out _) &&
                (newestStored == null || storedBackup.sequence > newestStored.sequence))
            {
                newestStored = storedBackup;
            }
            if (newestStored == null ||
                newestStored.phase != RaidCheckpointPhase.Active ||
                newestStored.sequence != recoveredCheckpoint.sequence ||
                !AreCanonicalJsonEquivalent(newestStored, recoveredCheckpoint))
            {
                error = "A newer terminal or different checkpoint superseded the selected active recovery.";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryBeginRecoveredRaid(
            RaidRecoveryBaselineData recoveredBaseline,
            RaidCheckpointData recoveredCheckpoint,
            out string error)
        {
            if (!TryPreflightRecoveredRaid(recoveredBaseline, recoveredCheckpoint, out error))
            {
                return false;
            }

            baseline = recoveredBaseline;
            lastCheckpoint = recoveredCheckpoint;
            pendingRestore = recoveredCheckpoint;
            pendingExactSettlementState = null;
            pendingExactSettlementKind = RaidSettlementJournalKind.None;
            ordinarySettlementMirrored = false;
            nextSequence = recoveredCheckpoint.sequence;
            raidTracked = true;
            handlingWriteFailure = false;
            basePersistenceReady = false;
            baseArrivalComplete = false;
            entryOrigin = RaidEntryOrigin.Recovered;
            trackedOutcome = RaidOutcome.None;
            lastSuccessfulWriteAt = Time.unscaledTime;
            nextCheckpointAt = Time.unscaledTime + checkpointIntervalSeconds;

            if (shell.RaidSession.TryBeginRecoveredTravel(
                    recoveredBaseline.raidScene,
                    recoveredBaseline.raidSpawnId))
            {
                error = null;
                return true;
            }

            error = "The recovered raid was validated, but travel to its scene could not start. " +
                    "Its validated recovery files were preserved for a retry from the Main Menu.";
            return false;
        }

        public void NotifyRaidEntryTravelFailed()
        {
            if (!HasTrackedRaid)
            {
                return;
            }

            RaidEntryOrigin failedOrigin = entryOrigin;
            string raidInstanceId = baseline.raidInstanceId;

            if (failedOrigin == RaidEntryOrigin.Recovered)
            {
                // A scene/fade/spawn transport failure is not a checkpoint failure. Keep
                // the validated active recovery and keep this controller tracked so the
                // ordinary base-save path cannot commit the temporarily restored state.
                Debug.LogError(
                    $"Recovered raid '{raidInstanceId}' could not enter its scene; " +
                    "its recovery files were preserved for a Main Menu retry.",
                    this);
                return;
            }

            if (!TryCancelFreshRaidDeparture(out string error))
            {
                Debug.LogError(
                    $"A new raid failed before entry and its departure marker could not be safely cleared: {error}",
                    this);
            }
        }

        public bool TryRegisterScene(
            RaidCheckpointSceneBinding sceneBinding,
            out string error)
        {
            if (sceneBinding == null || !sceneBinding.IsConfigured)
            {
                error = "Raid checkpoint scene binding is missing or invalid.";
                return false;
            }

            if (activeSceneBinding != null && activeSceneBinding != sceneBinding)
            {
                error = "More than one raid checkpoint scene binding is active.";
                return false;
            }

            if (!TryResolveSceneStateId(sceneBinding.SceneName, out string expectedStateId) ||
                !string.Equals(
                    sceneBinding.SceneStateId,
                    expectedStateId,
                    StringComparison.Ordinal))
            {
                error = "Raid scene binding identity does not match the configured recovery scene.";
                return false;
            }

            activeSceneBinding = sceneBinding;
            error = null;
            return true;
        }

        public void UnregisterScene(RaidCheckpointSceneBinding sceneBinding)
        {
            if (activeSceneBinding == sceneBinding)
            {
                activeSceneBinding = null;
            }
        }

        public bool TryGetPendingMapSeed(
            string sceneName,
            string sceneStateId,
            out int mapSeed)
        {
            if (pendingRestore != null &&
                pendingRestore.phase == RaidCheckpointPhase.Active &&
                string.Equals(pendingRestore.raidScene, sceneName, StringComparison.Ordinal) &&
                string.Equals(pendingRestore.sceneStateId, sceneStateId, StringComparison.Ordinal))
            {
                mapSeed = pendingRestore.mapSeed;
                return true;
            }

            mapSeed = 0;
            return false;
        }

        public bool TryCompleteRaidSceneArrival(string activeSceneName, out string error)
        {
            if (!HasTrackedRaid)
            {
                // Direct GameMapTest authoring runs intentionally have no recovery lifetime.
                error = null;
                return true;
            }

            if (!string.Equals(activeSceneName, baseline.raidScene, StringComparison.Ordinal) ||
                activeSceneBinding == null ||
                !string.Equals(activeSceneBinding.SceneName, activeSceneName, StringComparison.Ordinal))
            {
                error = "The arriving raid scene has no matching recovery binding.";
                return false;
            }

            if (!string.IsNullOrEmpty(activeSceneBinding.SeedPreparationError))
            {
                error = activeSceneBinding.SeedPreparationError;
                return false;
            }

            if (pendingRestore != null)
            {
                if (!TryApplyPendingRestore(out error))
                {
                    return false;
                }
            }

            if (!TryCaptureAndWrite(RaidCheckpointPhase.Active, RaidOutcome.None, out error))
            {
                error = $"Could not create the first live raid checkpoint: {error}";
                return false;
            }

            return true;
        }

        public bool TryResolveRecoveryFailure(string reason)
        {
            if (!HasTrackedRaid || handlingWriteFailure)
            {
                return false;
            }

            HandleCheckpointWriteFailure(
                string.IsNullOrWhiteSpace(reason)
                    ? "Raid recovery became unavailable."
                    : reason);
            return shell.RaidSession != null &&
                   shell.RaidSession.Outcome == RaidOutcome.RecoveryFailed;
        }

        public bool TryMakeRecoveryFailureDurable(string reason, out string error)
        {
            if (!HasTrackedRaid || handlingWriteFailure)
            {
                error = "No tracked raid is available for a durable recovery-failure decision.";
                return false;
            }

            handlingWriteFailure = true;
            trackedOutcome = RaidOutcome.RecoveryFailed;
            bool durable = TryPersistRecoveryFailureDecision(reason, out error);
            pendingRestore = null;
            entryOrigin = RaidEntryOrigin.None;
            basePersistenceReady = false;
            baseArrivalComplete = false;
            handlingWriteFailure = false;
            return durable;
        }

        public void ConfirmBaseSettlement()
        {
            if (!HasTrackedRaid)
            {
                return;
            }

            baseArrivalComplete = true;
            TryFinalizeTrackedRaidAtBase();
        }

        public void NotifyBasePersistenceReady()
        {
            if (!HasTrackedRaid)
            {
                return;
            }

            basePersistenceReady = true;
            TryFinalizeTrackedRaidAtBase();
        }

        private void TryFinalizeTrackedRaidAtBase()
        {
            if (!HasTrackedRaid || !basePersistenceReady || !baseArrivalComplete)
            {
                return;
            }

            if (!TryCommitTrackedRaidAtBase(out string commitError))
            {
                Debug.LogError(
                    $"Raid '{baseline.raidInstanceId}' reached the base, but its ordinary save commit failed. " +
                    $"Recovery files were preserved: {commitError}",
                    this);
                return;
            }
        }

        public bool TryPreflightMenuRecoverySettlement(
            RaidRecoveryBaselineData requestedBaseline,
            RaidCheckpointData requestedCheckpoint,
            RaidOutcome settlementOutcome,
            GameSaveData exactSettlementState,
            RaidSettlementJournalKind exactSettlementKind,
            out string error)
        {
            string raidInstanceId = requestedBaseline?.raidInstanceId;
            if (string.IsNullOrWhiteSpace(raidInstanceId) ||
                !RaidCheckpointValidator.IsTerminalOutcome(settlementOutcome) ||
                (exactSettlementState == null &&
                 exactSettlementKind != RaidSettlementJournalKind.None) ||
                (exactSettlementState != null &&
                 exactSettlementKind != RaidSettlementJournalKind.OutcomeSettlement &&
                 exactSettlementKind != RaidSettlementJournalKind.FreshDepartureRollback) ||
                (exactSettlementKind == RaidSettlementJournalKind.FreshDepartureRollback &&
                 settlementOutcome != RaidOutcome.RecoveryFailed))
            {
                error = "Recovery settlement is missing its identity, terminal outcome, or exact transaction kind.";
                return false;
            }

            if (!isActiveAndEnabled || !IsConfigured || shell.RaidSession == null ||
                raidTracked || baseline != null || pendingRestore != null)
            {
                error = "Raid recovery settlement controller is unavailable or already busy.";
                return false;
            }

            if (shell.RaidSession.CurrentSceneKind != GameplaySceneKind.Base ||
                shell.RaidSession.State != RaidSessionState.Inactive ||
                DirectSceneTravel.IsLoading ||
                shell.IsTravelPrepared)
            {
                error = "Raid recovery settlement can begin only from an idle, fully arrived base scene.";
                return false;
            }

            // A matching ordinary marker is the normal authority. A journal is the
            // only marker-free exception because it represents an already-started,
            // idempotent settlement; it must never authorize Resume.
            GameSaveData ordinarySave = GetAuthoritativeOrdinarySave();
            bool ordinaryDeclaresRaid = ordinarySave != null &&
                                        ordinarySave.raidInProgress &&
                                        string.Equals(
                                            ordinarySave.activeRaidInstanceId,
                                            raidInstanceId,
                                            StringComparison.Ordinal);
            if (!ordinaryDeclaresRaid && ordinarySave != null && ordinarySave.raidInProgress)
            {
                error = "The ordinary save declares a different active raid.";
                return false;
            }

            if (!RaidCheckpointStore.TryReadBaseline(
                    out RaidRecoveryBaselineData storedBaseline,
                    out error) ||
                !string.Equals(
                    storedBaseline.raidInstanceId,
                    raidInstanceId,
                    StringComparison.Ordinal) ||
                !AreCanonicalJsonEquivalent(storedBaseline, requestedBaseline))
            {
                error = $"Recovery settlement no longer matches its durable baseline: {error}";
                return false;
            }

            if (!TryValidateBaseline(storedBaseline, out error))
            {
                error = $"Recovery settlement baseline is no longer valid: {error}";
                return false;
            }

            string exactJournalError = null;
            if (exactSettlementState != null &&
                !TryValidateMatchingExactSettlementJournal(
                    storedBaseline,
                    settlementOutcome,
                    exactSettlementState,
                    exactSettlementKind,
                    out exactJournalError))
            {
                error = $"Exact settlement transaction no longer matches its durable journal: {exactJournalError}";
                return false;
            }

            if (!ordinaryDeclaresRaid &&
                (ordinarySave == null || exactSettlementState == null ||
                 !AreCanonicalJsonEquivalent(ordinarySave, exactSettlementState)))
            {
                error = "Marker-free recovery is not the exact in-flight settlement mirrored in the ordinary save.";
                return false;
            }

            if (exactSettlementState == null &&
                !TryValidateRequestedSettlementCheckpoint(
                    storedBaseline,
                    requestedCheckpoint,
                    settlementOutcome,
                    out error))
            {
                return false;
            }

            error = null;
            return true;
        }

        public bool TryCompleteMenuRecoverySettlementAtBase(
            RaidRecoveryBaselineData requestedBaseline,
            RaidCheckpointData requestedCheckpoint,
            RaidOutcome settlementOutcome,
            GameSaveData exactSettlementState,
            RaidSettlementJournalKind exactSettlementKind,
            out string error)
        {
            if (!TryPreflightMenuRecoverySettlement(
                    requestedBaseline,
                    requestedCheckpoint,
                    settlementOutcome,
                    exactSettlementState,
                    exactSettlementKind,
                    out error))
            {
                return false;
            }

            if (!RaidCheckpointValidator.IsTerminalOutcome(settlementOutcome) ||
                !RaidCheckpointStore.TryReadBaseline(
                    out RaidRecoveryBaselineData storedBaseline,
                    out error))
            {
                error = $"Recovery settlement has an invalid outcome or missing baseline: {error}";
                return false;
            }

            baseline = storedBaseline;
            raidTracked = true;
            basePersistenceReady = true;
            baseArrivalComplete = true;
            entryOrigin = RaidEntryOrigin.None;
            trackedOutcome = settlementOutcome;
            pendingExactSettlementState = exactSettlementState;
            pendingExactSettlementKind = exactSettlementState == null
                ? RaidSettlementJournalKind.None
                : exactSettlementKind;
            ordinarySettlementMirrored = false;

            if (!TryCommitTrackedRaidAtBase(out error))
            {
                return false;
            }

            error = null;
            return true;
        }

        public bool TryPreflightOrphanedRaidSettlement(
            string raidInstanceId,
            out GameSaveData cleanSettlementState,
            out string error)
        {
            cleanSettlementState = null;
            if (string.IsNullOrWhiteSpace(raidInstanceId) ||
                !isActiveAndEnabled || !IsConfigured || shell.RaidSession == null ||
                raidTracked || baseline != null || pendingRestore != null)
            {
                error = "Orphaned raid settlement controller is unavailable or already busy.";
                return false;
            }

            if (shell.RaidSession.CurrentSceneKind != GameplaySceneKind.Base ||
                shell.RaidSession.State != RaidSessionState.Inactive ||
                DirectSceneTravel.IsLoading ||
                shell.IsTravelPrepared)
            {
                error = "Orphaned raid settlement can begin only from an idle, fully arrived base scene.";
                return false;
            }

            // Ordinary save is inspected first. Only its current authoritative marker
            // may authorize marker-only failure; any Recovery artifact changes this into
            // the regular recovery-settlement path and must be decided at Main Menu.
            GameSaveData markedSave = GetAuthoritativeOrdinarySave();
            if (markedSave == null || !markedSave.raidInProgress ||
                !string.Equals(
                    markedSave.activeRaidInstanceId,
                    raidInstanceId,
                    StringComparison.Ordinal))
            {
                error = "The ordinary save no longer declares the requested orphaned raid.";
                return false;
            }

            if (RaidCheckpointStore.HasRecoveryArtifacts)
            {
                error = "Recovery artifacts now exist; marker-only settlement was refused.";
                return false;
            }

            try
            {
                cleanSettlementState = JsonUtility.FromJson<GameSaveData>(
                    JsonUtility.ToJson(markedSave));
            }
            catch (Exception exception)
            {
                error = $"Could not clone the marked ordinary save: {exception.Message}";
                return false;
            }

            if (cleanSettlementState == null)
            {
                error = "Could not clone the marked ordinary save.";
                return false;
            }

            cleanSettlementState.raidInProgress = false;
            cleanSettlementState.activeRaidInstanceId = null;
            if (!RaidItemSettlementPolicy.TryDiscardCarriedItems(
                    cleanSettlementState,
                    RaidOutcome.RecoveryFailed,
                    out error))
            {
                cleanSettlementState = null;
                error = $"Marked ordinary save could not apply raid-failure item loss: {error}";
                return false;
            }

            if (!RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                    cleanSettlementState,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out error))
            {
                cleanSettlementState = null;
                error = $"Marked ordinary save is not a valid orphan settlement state: {error}";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryCommitTrackedRaidAtBase(out string error)
        {
            if (!HasPendingBaseSettlement)
            {
                error = "No fully arrived raid settlement is ready to commit at the base.";
                return false;
            }

            if (!TryAcquireSettlementInputLock(out error))
            {
                error = "Could not lock gameplay state for the settlement transaction: " + error;
                return false;
            }

            RaidOutcome settlementOutcome = trackedOutcome;
            if (!RaidCheckpointValidator.IsTerminalOutcome(settlementOutcome) &&
                shell.RaidSession != null &&
                RaidCheckpointValidator.IsTerminalOutcome(shell.RaidSession.Outcome))
            {
                settlementOutcome = shell.RaidSession.Outcome;
            }

            if (!RaidCheckpointValidator.IsTerminalOutcome(settlementOutcome))
            {
                error = "Tracked raid settlement is missing a terminal outcome.";
                return false;
            }

            // Re-check the ordinary authority immediately before the transaction. A
            // normal tracked raid must still have its matching marker. The only
            // marker-free retry is an exact journal state already mirrored into the
            // ordinary save by this same settlement transaction.
            error = null;
            GameSaveData ordinarySave = GetAuthoritativeOrdinarySave();
            if (ordinarySettlementMirrored)
            {
                // The exact transaction already reached the ordinary save. Recovery
                // cleanup may have deleted its own baseline or journal before a later
                // file failed to delete, so this in-process retry must not demand those
                // consumed proofs again. The immutable exact state and its ordinary
                // mirror are the remaining authority for cleanup-only retry.
                if (pendingExactSettlementState == null ||
                    ordinarySave == null ||
                    ordinarySave.raidInProgress ||
                    !AreCanonicalJsonEquivalent(ordinarySave, pendingExactSettlementState))
                {
                    error = "The ordinary save changed after settlement was mirrored; recovery cleanup was refused.";
                    return false;
                }

                return TryFinishMirroredSettlementCleanup(out error);
            }

            bool ordinaryDeclaresRaid = ordinarySave != null &&
                                        ordinarySave.raidInProgress &&
                                        string.Equals(
                                            ordinarySave.activeRaidInstanceId,
                                            baseline.raidInstanceId,
                                            StringComparison.Ordinal);
            if (!ordinaryDeclaresRaid &&
                (pendingExactSettlementState == null ||
                 ordinarySave == null || ordinarySave.raidInProgress ||
                 !AreCanonicalJsonEquivalent(
                     ordinarySave,
                     pendingExactSettlementState) ||
                 !TryValidateMatchingExactSettlementJournal(
                     baseline,
                     settlementOutcome,
                     pendingExactSettlementState,
                     pendingExactSettlementKind,
                     out error)))
            {
                error = "Ordinary save no longer authorizes this tracked settlement: " +
                        (error ?? "no matching exact settlement transaction exists.");
                return false;
            }

            if (!RaidCheckpointStore.TryReadBaseline(
                    out RaidRecoveryBaselineData storedBaseline,
                    out error) ||
                !TryValidateBaseline(storedBaseline, out error) ||
                !AreCanonicalJsonEquivalent(storedBaseline, baseline))
            {
                error = "Tracked settlement no longer matches its durable baseline: " + error;
                return false;
            }

            GameSaveData saveData;
            if (pendingExactSettlementState != null)
            {
                // A durable exact journal already owns the final transaction payload.
                // Do not infer its Player result from the outcome enum again: a fresh
                // raid that failed before scene entry deliberately stores the unchanged
                // pre-departure state under RecoveryFailed, while an actual failed raid
                // stores an empty Player item payload under the same outcome.
                saveData = pendingExactSettlementState;
                if (!RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                        saveData,
                        shell.InventoryUI.ItemDatabase,
                        furnitureDatabase,
                        InventoryUIManager.DefaultInventoryWidth,
                        InventoryUIManager.DefaultInventoryHeight,
                        out error))
                {
                    error = $"The exact settlement state is invalid: {error}";
                    return false;
                }

                if (saveData.playerItems.itemRecordCount == 0 &&
                    !shell.InventoryUI.TryDiscardAllCarriedItems(out error))
                {
                    error = $"Could not synchronize the live Player with the exact empty settlement: {error}";
                    return false;
                }

                if (!InventorySaveCodec.TryCapture(
                        shell.InventoryUI.PlayerState,
                        shell.InventoryUI.ItemDatabase,
                        out PlayerItemStateSaveData livePlayerItems,
                        out error) ||
                    !AreCanonicalJsonEquivalent(livePlayerItems, saveData.playerItems))
                {
                    error = $"The live Player item state does not match the exact settlement payload: " +
                            (error ?? "captured Player items differ from the durable transaction.");
                    return false;
                }
            }
            else
            {
                if (RaidItemSettlementPolicy.DiscardsCarriedItems(settlementOutcome) &&
                    !shell.InventoryUI.TryDiscardAllCarriedItems(out error))
                {
                    error = $"Could not apply the live Player item-loss settlement: {error}";
                    return false;
                }

                if (!TryCapturePersistentState(out GameSaveData sourceState, out error))
                {
                    return false;
                }

                if (!RaidItemSettlementPolicy.TryCreatePersistentStateForOutcome(
                        sourceState,
                        settlementOutcome,
                        out saveData,
                        out error))
                {
                    error = $"Could not create the outcome-specific settlement state: {error}";
                    return false;
                }
            }

            var journal = new RaidSettlementJournalData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidSettlementJournalData.CurrentFormatVersion,
                raidInstanceId = baseline.raidInstanceId,
                writtenAtUtc = DateTime.UtcNow.ToString("O"),
                kind = pendingExactSettlementKind == RaidSettlementJournalKind.None
                    ? RaidSettlementJournalKind.OutcomeSettlement
                    : pendingExactSettlementKind,
                outcome = settlementOutcome,
                settlementState = saveData
            };

            if (!RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    baseline,
                    journal,
                    out error) ||
                !RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                    saveData,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out error) ||
                !RaidCheckpointStore.TryWriteSettlementJournal(journal, out error))
            {
                error = $"Could not make the base settlement journal durable: {error}";
                return false;
            }

            // Once the journal is durable it is the exact settlement transaction.
            // Keep reusing that snapshot if the ordinary mirrored save or cleanup
            // must be retried; recapturing live state would change an in-flight result.
            pendingExactSettlementState = saveData;
            pendingExactSettlementKind = journal.kind;

            StandardStashViewData playerInventory = shell.InventoryUI.PlayerInventoryData;
            if (playerInventory == null)
            {
                error = "Player inventory dimensions are unavailable for ordinary save validation.";
                return false;
            }

            if (!GameSaveManager.TryWriteSlotOneMirrored(
                    saveData,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    playerInventory.CapacityWidth,
                    playerInventory.CapacityHeight,
                    out error))
            {
                error = $"Ordinary save commit failed after the settlement journal was secured: {error}";
                return false;
            }

            ordinarySettlementMirrored = true;
            return TryFinishMirroredSettlementCleanup(out error);
        }

        private bool TryFinishMirroredSettlementCleanup(out string error)
        {
            if (!ordinarySettlementMirrored || pendingExactSettlementState == null)
            {
                error = "No mirrored settlement transaction is ready for cleanup.";
                return false;
            }

            if (!RaidCheckpointStore.TryDeleteAll(out error))
            {
                error = $"The raid was durably settled, but its recovery files could not be removed: {error}";
                return false;
            }

            ResetTrackedRaid();
            error = null;
            return true;
        }

        private bool TryAcquireSettlementInputLock(out string error)
        {
            if (settlementInputLockHeld)
            {
                error = null;
                return true;
            }

            if (shell == null || shell.IsTravelPrepared || shell.PlayerMovement == null ||
                shell.InventoryUI == null || shell.PlayerInteractor == null ||
                shell.PlayerStats == null)
            {
                error = "Persistent Player services are unavailable or still completing scene travel.";
                return false;
            }

            if (!shell.InventoryUI.CloseAllInventories())
            {
                error = "The active inventory drag could not be restored before settlement.";
                return false;
            }

            settlementMovementWasEnabled = shell.PlayerMovement.enabled;
            settlementInventoryInputWasBlocked = shell.InventoryUI.InputBlocked;
            settlementInteractionWasBlocked = shell.PlayerInteractor.InteractionBlocked;
            settlementDamageWasBlocked = shell.PlayerStats.DamageBlocked;
            settlementInputLockHeld = true;

            shell.PlayerEventSystem?.SetSelectedGameObject(null);
            shell.PlayerMovement.enabled = false;
            shell.InventoryUI.SetInputBlocked(true);
            shell.PlayerInteractor.SetInteractionBlocked(true);
            shell.PlayerStats.SetDamageBlocked(true);
            error = null;
            return true;
        }

        private void ReleaseSettlementInputLock()
        {
            if (!settlementInputLockHeld)
            {
                return;
            }

            if (shell != null)
            {
                if (shell.PlayerMovement != null)
                {
                    shell.PlayerMovement.enabled = settlementMovementWasEnabled;
                }
                if (shell.InventoryUI != null)
                {
                    shell.InventoryUI.SetInputBlocked(settlementInventoryInputWasBlocked);
                }
                if (shell.PlayerInteractor != null)
                {
                    shell.PlayerInteractor.SetInteractionBlocked(settlementInteractionWasBlocked);
                }
                if (shell.PlayerStats != null)
                {
                    shell.PlayerStats.SetDamageBlocked(settlementDamageWasBlocked);
                }
            }

            settlementInputLockHeld = false;
            settlementMovementWasEnabled = false;
            settlementInventoryInputWasBlocked = false;
            settlementInteractionWasBlocked = false;
            settlementDamageWasBlocked = false;
        }

        private bool TryApplyPendingRestore(out string error)
        {
            RaidCheckpointData checkpoint = pendingRestore;
            if (checkpoint == null)
            {
                error = "Pending raid checkpoint is missing.";
                return false;
            }

            if (activeSceneBinding == null)
            {
                error = "Active raid scene binding is missing.";
                return false;
            }

            if (!TryValidateCheckpoint(baseline, checkpoint, out error))
            {
                return false;
            }

            PlayerStats playerStats = shell.PlayerStats;
            if (!Mathf.Approximately(checkpoint.playerMaxHealth, playerStats.MaxHealth) ||
                checkpoint.playerCurrentHealth <= 0f ||
                checkpoint.playerCurrentHealth > playerStats.MaxHealth)
            {
                error = "Recovered Player health is incompatible with the current Player definition.";
                return false;
            }

            if (!activeSceneBinding.TryPrepareRestore(
                    checkpoint,
                    shell.InventoryUI.ItemDatabase,
                    out RaidCheckpointSceneBinding.RestorePlan restorePlan,
                    out error))
            {
                return false;
            }

            if (!activeSceneBinding.TryApplyRestore(restorePlan, out error))
            {
                return false;
            }

            Transform player = shell.PlayerTransform;
            player.SetPositionAndRotation(
                RaidCheckpointSceneBinding.RestorePosition(checkpoint.playerTransform),
                RaidCheckpointSceneBinding.RestoreRotation(checkpoint.playerTransform));
            Rigidbody body = player.GetComponent<Rigidbody>();
            if (body != null)
            {
                body.linearVelocity = Vector3.zero;
                body.angularVelocity = Vector3.zero;
            }
            Physics.SyncTransforms();

            if (!playerStats.TryRestoreCheckpointHealth(
                    checkpoint.playerCurrentHealth,
                    checkpoint.playerMaxHealth,
                    out error))
            {
                return false;
            }

            lastCheckpoint = checkpoint;
            pendingRestore = null;
            nextSequence = checkpoint.sequence;
            error = null;
            return true;
        }

        private bool ShouldCaptureActiveRaid()
        {
            return HasTrackedRaid &&
                   pendingRestore == null &&
                   activeSceneBinding != null &&
                   shell.RaidSession != null &&
                   shell.RaidSession.IsRaidActive &&
                   !DirectSceneTravel.IsLoading &&
                   !shell.InventoryUI.HasActiveDrag;
        }

        private bool TryCaptureAndWrite(
            RaidCheckpointPhase phase,
            RaidOutcome outcome,
            out string error)
        {
            if (!HasTrackedRaid || activeSceneBinding == null)
            {
                error = "No active raid scene is available for recovery capture.";
                return false;
            }

            // SceneSpawnController calls this while the destination is still covered and
            // DirectSceneTravel still owns its pending-arrival token. That black-screen
            // boundary is the safest time to create/apply the first checkpoint, so only an
            // incomplete inventory drag blocks this explicit capture. Periodic callers
            // separately gate themselves with ShouldCaptureActiveRaid().
            if (shell.InventoryUI.HasActiveDrag)
            {
                error = "Recovery capture is deferred during scene travel or an inventory drag.";
                return false;
            }

            if (nextSequence >= long.MaxValue - 1)
            {
                error = "Raid checkpoint sequence can no longer advance safely.";
                return false;
            }

            if (!TryCapturePersistentState(out GameSaveData persistentState, out error) ||
                !activeSceneBinding.TryCaptureWorld(
                    shell.InventoryUI.ItemDatabase,
                    out int generatorVersion,
                    out int mapSeed,
                    out string layoutHash,
                    out var chestRecords,
                    out var enemyRecords,
                    out error))
            {
                return false;
            }

            if (phase == RaidCheckpointPhase.Resolved)
            {
                if (!RaidItemSettlementPolicy.TryCreatePersistentStateForOutcome(
                        persistentState,
                        outcome,
                        out GameSaveData outcomePersistentState,
                        out error))
                {
                    error = $"Could not apply the raid item settlement to the terminal checkpoint: {error}";
                    return false;
                }

                persistentState = outcomePersistentState;
            }

            var candidate = new RaidCheckpointData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidCheckpointData.CurrentFormatVersion,
                worldStateVersion = RaidCheckpointData.CurrentWorldStateVersion,
                raidInstanceId = baseline.raidInstanceId,
                sequence = nextSequence + 1,
                savedAtUtc = DateTime.UtcNow.ToString("O"),
                phase = phase,
                outcome = outcome,
                raidScene = baseline.raidScene,
                raidSpawnId = baseline.raidSpawnId,
                sceneStateId = baseline.sceneStateId,
                generatorVersion = generatorVersion,
                mapSeed = mapSeed,
                layoutHash = layoutHash,
                playerTransform = RaidCheckpointSceneBinding.CaptureTransform(shell.PlayerTransform),
                playerCurrentHealth = shell.PlayerStats.CurrentHealth,
                playerMaxHealth = shell.PlayerStats.MaxHealth,
                persistentState = persistentState,
                chests = chestRecords,
                chestRecordCount = chestRecords.Count,
                enemies = enemyRecords,
                enemyRecordCount = enemyRecords.Count
            };

            if (!RaidCheckpointValidator.TryValidateCheckpointStructure(
                    baseline,
                    candidate,
                    out error) ||
                !RaidCheckpointStore.TryWriteCheckpoint(
                    candidate,
                    lastCheckpoint,
                    out error))
            {
                return false;
            }

            lastCheckpoint = candidate;
            nextSequence = candidate.sequence;
            lastSuccessfulWriteAt = Time.unscaledTime;
            nextCheckpointAt = lastSuccessfulWriteAt + checkpointIntervalSeconds;
            error = null;
            return true;
        }

        private bool TryCapturePersistentState(
            out GameSaveData persistentState,
            out string error)
        {
            persistentState = null;
            InventoryUIManager inventory = shell.InventoryUI;
            GameManager owner = GameManager.Instance;

            if (inventory == null || inventory.PlayerState == null || inventory.HasActiveDrag)
            {
                error = "Player inventory is unavailable or currently being dragged.";
                return false;
            }

            if (owner == null)
            {
                error = "Persistent base-state owner is unavailable.";
                return false;
            }

            if (!InventorySaveCodec.TryCapture(
                    inventory.PlayerState,
                    inventory.ItemDatabase,
                    out PlayerItemStateSaveData playerItems,
                    out error) ||
                !BaseFurnitureSaveCodec.TryCapture(
                    owner.BaseFurnitureState,
                    inventory.ItemDatabase,
                    furnitureDatabase,
                    out BaseSaveData baseState,
                    out error))
            {
                return false;
            }

            persistentState = GameSaveManager.CreateSave(playerItems, baseState);
            error = null;
            return true;
        }

        private bool TryValidateBaseline(
            RaidRecoveryBaselineData candidate,
            out string error)
        {
            return RaidCheckpointValidator.TryValidateBaseline(
                candidate,
                shell.InventoryUI.ItemDatabase,
                furnitureDatabase,
                InventoryUIManager.DefaultInventoryWidth,
                InventoryUIManager.DefaultInventoryHeight,
                out error);
        }

        private bool TryValidateCheckpoint(
            RaidRecoveryBaselineData candidateBaseline,
            RaidCheckpointData candidateCheckpoint,
            out string error)
        {
            return RaidCheckpointValidator.TryValidateCheckpointForLoad(
                candidateBaseline,
                candidateCheckpoint,
                shell.InventoryUI.ItemDatabase,
                furnitureDatabase,
                InventoryUIManager.DefaultInventoryWidth,
                InventoryUIManager.DefaultInventoryHeight,
                out error);
        }

        private static bool HasMatchingOrdinaryRaidMarker(string raidInstanceId)
        {
            GameSaveData authoritative = GetAuthoritativeOrdinarySave();
            return authoritative != null && authoritative.raidInProgress &&
                   string.Equals(
                       authoritative.activeRaidInstanceId,
                       raidInstanceId,
                       StringComparison.Ordinal);
        }

        private static GameSaveData GetAuthoritativeOrdinarySave()
        {
            GameSaveManager.ReadSlotOneCandidates(
                out GameSaveData primary,
                out _,
                out GameSaveData backup,
                out _);
            return primary ?? backup;
        }

        private bool TryValidateMatchingExactSettlementJournal(
            RaidRecoveryBaselineData storedBaseline,
            RaidOutcome settlementOutcome,
            GameSaveData exactSettlementState,
            RaidSettlementJournalKind exactSettlementKind,
            out string error)
        {
            string stateValidationError = null;
            if (storedBaseline == null || exactSettlementState == null ||
                !RaidCheckpointValidator.IsTerminalOutcome(settlementOutcome) ||
                !RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                    exactSettlementState,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out stateValidationError))
            {
                error = "Exact settlement state is missing or invalid: " +
                        (stateValidationError ?? "required identity or outcome is missing.");
                return false;
            }

            RaidCheckpointStore.ReadSettlementJournalCandidates(
                out RaidSettlementJournalData primary,
                out _,
                out RaidSettlementJournalData backup,
                out _);

            bool primaryStructureValid =
                RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    storedBaseline,
                    primary,
                    out _);
            if (primaryStructureValid)
            {
                if (IsMatchingExactSettlementJournal(
                        storedBaseline,
                        primary,
                        settlementOutcome,
                        exactSettlementState,
                        exactSettlementKind))
                {
                    error = null;
                    return true;
                }

                error = "The authoritative settlement journal primary does not match the requested exact state.";
                return false;
            }

            if (IsMatchingExactSettlementJournal(
                    storedBaseline,
                    backup,
                    settlementOutcome,
                    exactSettlementState,
                    exactSettlementKind))
            {
                error = null;
                return true;
            }

            error = "No valid settlement journal matches the ordinary save and requested exact state.";
            return false;
        }

        private bool TryValidateRequestedSettlementCheckpoint(
            RaidRecoveryBaselineData storedBaseline,
            RaidCheckpointData requestedCheckpoint,
            RaidOutcome settlementOutcome,
            out string error)
        {
            RaidCheckpointStore.ReadCheckpointCandidates(
                out RaidCheckpointData primary,
                out _,
                out RaidCheckpointData backup,
                out _);

            RaidCheckpointData newest = null;
            if (TryValidateCheckpoint(storedBaseline, primary, out _))
            {
                newest = primary;
            }
            if (TryValidateCheckpoint(storedBaseline, backup, out _) &&
                (newest == null || backup.sequence > newest.sequence))
            {
                newest = backup;
            }

            if (requestedCheckpoint == null)
            {
                if (newest != null || settlementOutcome != RaidOutcome.RecoveryFailed)
                {
                    error = "Baseline-only failure settlement was superseded by a durable checkpoint or non-failure outcome.";
                    return false;
                }

                error = null;
                return true;
            }

            if (!TryValidateCheckpoint(storedBaseline, requestedCheckpoint, out error) ||
                newest == null ||
                !AreCanonicalJsonEquivalent(newest, requestedCheckpoint))
            {
                error = $"Requested settlement checkpoint is no longer the newest durable candidate: {error}";
                return false;
            }

            bool resolvedOutcomeMismatch =
                requestedCheckpoint.phase == RaidCheckpointPhase.Resolved &&
                requestedCheckpoint.outcome != settlementOutcome;
            string markerError = null;
            if (resolvedOutcomeMismatch &&
                (settlementOutcome != RaidOutcome.RecoveryFailed ||
                 !TryValidateAuthoritativeMarkerOnlyRecoveryFailureJournal(
                     storedBaseline,
                     out markerError)))
            {
                error = "Requested settlement checkpoint and terminal outcome disagree. " +
                        (markerError ?? "No authoritative marker-only recovery failure overrides it.");
                return false;
            }

            if (requestedCheckpoint.phase == RaidCheckpointPhase.Active &&
                settlementOutcome != RaidOutcome.RecoveryFailed)
            {
                error = "An active checkpoint can only be closed as a recovery failure.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryValidateAuthoritativeMarkerOnlyRecoveryFailureJournal(
            RaidRecoveryBaselineData storedBaseline,
            out string error)
        {
            RaidCheckpointStore.ReadSettlementJournalCandidates(
                out RaidSettlementJournalData primary,
                out _,
                out RaidSettlementJournalData backup,
                out _);

            bool primaryStructureValid =
                RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    storedBaseline,
                    primary,
                    out _);
            if (primaryStructureValid)
            {
                if (primary.outcome == RaidOutcome.RecoveryFailed &&
                    primary.settlementState == null)
                {
                    error = null;
                    return true;
                }

                error = "The authoritative settlement journal primary is not a marker-only recovery failure.";
                return false;
            }

            if (RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    storedBaseline,
                    backup,
                    out _) &&
                backup.outcome == RaidOutcome.RecoveryFailed &&
                backup.settlementState == null)
            {
                error = null;
                return true;
            }

            error = "No valid marker-only recovery failure journal matches this raid.";
            return false;
        }

        private static bool IsMatchingExactSettlementJournal(
            RaidRecoveryBaselineData storedBaseline,
            RaidSettlementJournalData journal,
            RaidOutcome settlementOutcome,
            GameSaveData exactSettlementState,
            RaidSettlementJournalKind exactSettlementKind)
        {
            return RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                       storedBaseline,
                       journal,
                       out _) &&
                   journal.settlementState != null &&
                   journal.kind == exactSettlementKind &&
                   journal.outcome == settlementOutcome &&
                   AreCanonicalJsonEquivalent(
                       journal.settlementState,
                       exactSettlementState);
        }

        private bool TryResolveSceneStateId(string sceneName, out string sceneStateId)
        {
            if (string.Equals(sceneName, supportedRaidScene, StringComparison.Ordinal))
            {
                sceneStateId = supportedSceneStateId;
                return true;
            }

            sceneStateId = null;
            return false;
        }

        private void HandlePlayerHealthChanged(float currentHealth, float maxHealth)
        {
            if (!ShouldCaptureActiveRaid())
            {
                return;
            }

            float now = Time.unscaledTime;
            float earliestAllowedWrite = lastSuccessfulWriteAt + minimumWriteGapSeconds;
            float requestedWrite = Mathf.Max(
                earliestAllowedWrite,
                now + importantChangeDelaySeconds);
            nextCheckpointAt = Mathf.Min(nextCheckpointAt, requestedWrite);
        }

        private void HandleRaidResolved(RaidOutcome resolvedOutcome)
        {
            if (!HasTrackedRaid || handlingWriteFailure || resolvedOutcome == RaidOutcome.None)
            {
                return;
            }

            trackedOutcome = resolvedOutcome;

            if (TryCaptureAndWrite(
                    RaidCheckpointPhase.Resolved,
                    resolvedOutcome,
                    out string captureError))
            {
                if (TrySecureResolvedDecision(resolvedOutcome, out string decisionError))
                {
                    return;
                }

                HandleCheckpointWriteFailure(
                    $"Raid result checkpoint was written, but its terminal decision could not be secured: " +
                    decisionError);
                return;
            }

            if (TryWriteResolvedFallback(resolvedOutcome, out string fallbackError))
            {
                Debug.LogWarning(
                    $"Raid result used the last durable recovery state because the final live capture failed: {captureError}",
                    this);
                if (TrySecureResolvedDecision(resolvedOutcome, out string decisionError))
                {
                    return;
                }

                HandleCheckpointWriteFailure(
                    $"Raid fallback result was written, but its terminal decision could not be secured: " +
                    decisionError);
                return;
            }

            HandleCheckpointWriteFailure(
                $"Raid result could not be made durable. Live capture: {captureError} " +
                $"Fallback: {fallbackError}");
        }

        private bool TryWriteResolvedFallback(RaidOutcome outcome, out string error)
        {
            RaidCheckpointData source = lastCheckpoint;
            if (source == null ||
                !TryValidateCheckpoint(baseline, source, out _) ||
                source.phase != RaidCheckpointPhase.Active)
            {
                RaidCheckpointStore.ReadCheckpointCandidates(
                    out RaidCheckpointData primary,
                    out _,
                    out RaidCheckpointData backup,
                    out _);
                bool primaryValid = TryValidateCheckpoint(baseline, primary, out _) &&
                                    primary.phase == RaidCheckpointPhase.Active;
                bool backupValid = TryValidateCheckpoint(baseline, backup, out _) &&
                                   backup.phase == RaidCheckpointPhase.Active;
                source = primaryValid && (!backupValid || primary.sequence >= backup.sequence)
                    ? primary
                    : backupValid ? backup : null;
            }

            if (source == null)
            {
                error = "No durable active checkpoint is available for terminal fallback.";
                return false;
            }

            if (Math.Max(nextSequence, source.sequence) >= long.MaxValue - 1)
            {
                error = "Raid checkpoint sequence can no longer advance safely.";
                return false;
            }

            if (!RaidCheckpointValidator.TryValidateCheckpointStructure(
                    baseline,
                    source,
                    out error))
            {
                return false;
            }

            RaidCheckpointData candidate;
            try
            {
                candidate = JsonUtility.FromJson<RaidCheckpointData>(
                    JsonUtility.ToJson(source));
            }
            catch (Exception exception)
            {
                error = $"Could not clone the last checkpoint: {exception.Message}";
                return false;
            }

            candidate.sequence = Math.Max(nextSequence, source.sequence) + 1;
            candidate.savedAtUtc = DateTime.UtcNow.ToString("O");
            candidate.phase = RaidCheckpointPhase.Resolved;
            candidate.outcome = outcome;
            if (outcome == RaidOutcome.PlayerDied)
            {
                candidate.playerCurrentHealth = 0f;
            }

            if (!RaidItemSettlementPolicy.TryCreatePersistentStateForOutcome(
                    candidate.persistentState,
                    outcome,
                    out GameSaveData settledPersistentState,
                    out error))
            {
                return false;
            }
            candidate.persistentState = settledPersistentState;

            if (!RaidCheckpointValidator.TryValidateCheckpointStructure(
                    baseline,
                    candidate,
                    out error) ||
                !RaidCheckpointStore.TryWriteCheckpoint(
                    candidate,
                    AreCanonicalJsonEquivalent(source, lastCheckpoint) ? lastCheckpoint : null,
                    out error))
            {
                return false;
            }

            lastCheckpoint = candidate;
            nextSequence = candidate.sequence;
            error = null;
            return true;
        }

        private bool TrySecureResolvedDecision(RaidOutcome outcome, out string error)
        {
            error = null;
            RaidCheckpointData terminal = lastCheckpoint;
            if (!HasTrackedRaid ||
                !RaidCheckpointValidator.IsTerminalOutcome(outcome) ||
                terminal == null ||
                terminal.phase != RaidCheckpointPhase.Resolved ||
                terminal.outcome != outcome ||
                !TryValidateCheckpoint(baseline, terminal, out error))
            {
                error = $"The latest checkpoint is not the validated terminal result: {error}";
                return false;
            }

            GameSaveData exactPersistentState = terminal.persistentState;
            if (!RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                    exactPersistentState,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out error))
            {
                error = $"The terminal checkpoint has no valid persistent settlement state: {error}";
                return false;
            }

            // The terminal checkpoint already contains the exact outcome-specific
            // persistent state. Reuse it at the base instead of recapturing live state.
            pendingExactSettlementState = exactPersistentState;
            pendingExactSettlementKind = RaidSettlementJournalKind.OutcomeSettlement;

            var journal = new RaidSettlementJournalData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidSettlementJournalData.CurrentFormatVersion,
                raidInstanceId = baseline.raidInstanceId,
                writtenAtUtc = DateTime.UtcNow.ToString("O"),
                kind = RaidSettlementJournalKind.OutcomeSettlement,
                outcome = outcome,
                settlementState = exactPersistentState
            };

            if (!RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    baseline,
                    journal,
                    out error))
            {
                return false;
            }

            if (RaidCheckpointStore.TryWriteSettlementJournal(journal, out string journalError))
            {
                error = null;
                return true;
            }

            // TryWriteCheckpoint rotates the prior Active record into .bak. If the
            // terminal primary were later unreadable, keeping that backup without a
            // terminal journal would make Main Menu offer Resume for a finished raid.
            // Removing only that backup preserves the terminal primary and fails closed
            // to baseline settlement if the primary also becomes unusable.
            if (RaidCheckpointStore.TryDeleteCheckpointBackup(out string cleanupError))
            {
                Debug.LogWarning(
                    $"Terminal raid journal could not be written, so the resumable Active backup was removed: " +
                    journalError,
                    this);
                error = null;
                return true;
            }

            error = $"Journal: {journalError} Active-backup cleanup: {cleanupError}";
            return false;
        }

        private void HandleCheckpointWriteFailure(string reason)
        {
            if (handlingWriteFailure || !HasTrackedRaid)
            {
                return;
            }

            handlingWriteFailure = true;
            bool decisionAlreadyDurable =
                trackedOutcome == RaidOutcome.RecoveryFailed &&
                HasValidDurableRecoveryFailureDecision();
            trackedOutcome = RaidOutcome.RecoveryFailed;

            if (!decisionAlreadyDurable)
            {
                TryPersistRecoveryFailureDecision(reason, out _);
            }

            if (shell.RaidSession != null)
            {
                if (shell.RaidSession.IsRaidActive)
                {
                    shell.RaidSession.TryResolveRecoveryFailure(reason);
                }
                else if (shell.RaidSession.IsRaidResolved)
                {
                    shell.RaidSession.TryOverrideResolvedOutcomeWithRecoveryFailure(reason);
                }
                else if (shell.RaidSession.State == RaidSessionState.Entering)
                {
                    shell.RaidSession.TryAbortRecoveredEntryAsFailure();
                }
            }

            pendingRestore = null;
            pendingExactSettlementState = null;
            pendingExactSettlementKind = RaidSettlementJournalKind.None;
            ordinarySettlementMirrored = false;
            entryOrigin = RaidEntryOrigin.None;
            basePersistenceReady = false;
            baseArrivalComplete = false;
            handlingWriteFailure = false;
        }

        private bool TryPersistRecoveryFailureDecision(string reason, out string error)
        {
            bool terminalWritten = TryWriteResolvedFallback(
                RaidOutcome.RecoveryFailed,
                out string terminalError);
            bool markerWritten = TryWriteFailureJournal(out string markerError);
            bool cleanupSucceeded = false;
            string cleanupError = null;

            if (!markerWritten)
            {
                cleanupSucceeded = terminalWritten
                    ? RaidCheckpointStore.TryDeleteCheckpointBackup(out cleanupError)
                    : RaidCheckpointStore.TryDeleteActiveCheckpoints(out cleanupError);
            }

            bool failClosedIsDurable = terminalWritten || markerWritten || cleanupSucceeded;
            Debug.LogError(
                $"{reason} The active raid was failed closed. " +
                $"Terminal checkpoint: {(terminalWritten ? "written" : terminalError)}. " +
                $"Failure marker: {(markerWritten ? "written" : markerError)}. " +
                $"Fallback cleanup: {(markerWritten ? "not required" : cleanupError ?? "complete")}.",
                this);
            if (!failClosedIsDurable)
            {
                Debug.LogError(
                    "CRITICAL: The storage device accepted neither a raid failure marker nor safe checkpoint cleanup. " +
                    "The runtime raid is failed, but no process-restart guarantee is possible until storage becomes writable.",
                    this);
            }

            error = failClosedIsDurable
                ? null
                : $"Terminal: {terminalError} Marker: {markerError} Cleanup: {cleanupError}";
            return failClosedIsDurable;
        }

        private bool TryWriteFailureJournal(out string error)
        {
            var journal = new RaidSettlementJournalData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidSettlementJournalData.CurrentFormatVersion,
                raidInstanceId = baseline.raidInstanceId,
                writtenAtUtc = DateTime.UtcNow.ToString("O"),
                kind = RaidSettlementJournalKind.RecoveryFailureMarker,
                outcome = RaidOutcome.RecoveryFailed,
                settlementState = null
            };

            if (!RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    baseline,
                    journal,
                    out error))
            {
                return false;
            }

            return RaidCheckpointStore.TryWriteSettlementJournal(journal, out error);
        }

        private bool TryCancelFreshRaidDeparture(out string error)
        {
            if (!HasTrackedRaid || baseline.startingState == null)
            {
                error = "Fresh raid departure has no recoverable starting state.";
                return false;
            }

            trackedOutcome = RaidOutcome.RecoveryFailed;
            var journal = new RaidSettlementJournalData
            {
                gameId = GameSaveData.CurrentGameId,
                formatVersion = RaidSettlementJournalData.CurrentFormatVersion,
                raidInstanceId = baseline.raidInstanceId,
                writtenAtUtc = DateTime.UtcNow.ToString("O"),
                kind = RaidSettlementJournalKind.FreshDepartureRollback,
                outcome = RaidOutcome.RecoveryFailed,
                settlementState = baseline.startingState
            };

            if (!RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                    baseline,
                    journal,
                    out error) ||
                !RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                    baseline.startingState,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out error) ||
                !RaidCheckpointStore.TryWriteSettlementJournal(journal, out error))
            {
                return false;
            }

            StandardStashViewData playerInventory = shell.InventoryUI.PlayerInventoryData;
            if (playerInventory == null)
            {
                error = "Player inventory dimensions are unavailable while cancelling raid departure.";
                return false;
            }

            if (!GameSaveManager.TryWriteSlotOneMirrored(
                    baseline.startingState,
                    shell.InventoryUI.ItemDatabase,
                    furnitureDatabase,
                    playerInventory.CapacityWidth,
                    playerInventory.CapacityHeight,
                    out error) ||
                !RaidCheckpointStore.TryDeleteAll(out error))
            {
                return false;
            }

            ResetTrackedRaid();
            error = null;
            return true;
        }

        private void TryWriteBestEffortShutdownCheckpoint()
        {
            if (!ShouldCaptureActiveRaid())
            {
                return;
            }

            if (!TryCaptureAndWrite(RaidCheckpointPhase.Active, RaidOutcome.None, out string error))
            {
                if (HasAnyValidDurableActiveCheckpoint())
                {
                    Debug.LogWarning(
                        $"Best-effort shutdown checkpoint was skipped; the previous validated checkpoint remains recoverable: {error}",
                        this);
                }
                else
                {
                    HandleCheckpointWriteFailure(
                        $"Shutdown left no valid durable active checkpoint: {error}");
                }
            }
        }

        private bool HasAnyValidDurableActiveCheckpoint()
        {
            RaidCheckpointStore.ReadCheckpointCandidates(
                out RaidCheckpointData primary,
                out _,
                out RaidCheckpointData backup,
                out _);
            return (TryValidateCheckpoint(baseline, primary, out _) &&
                    primary.phase == RaidCheckpointPhase.Active) ||
                   (TryValidateCheckpoint(baseline, backup, out _) &&
                    backup.phase == RaidCheckpointPhase.Active);
        }

        private bool HasValidDurableRecoveryFailureDecision()
        {
            if (RaidCheckpointStore.HasSettlementJournalArtifacts)
            {
                return true;
            }

            RaidCheckpointStore.ReadCheckpointCandidates(
                out RaidCheckpointData primary,
                out _,
                out RaidCheckpointData backup,
                out _);
            RaidCheckpointData newest = null;
            if (TryValidateCheckpoint(baseline, primary, out _))
            {
                newest = primary;
            }
            if (TryValidateCheckpoint(baseline, backup, out _) &&
                (newest == null || backup.sequence > newest.sequence))
            {
                newest = backup;
            }

            return newest != null &&
                   newest.phase == RaidCheckpointPhase.Resolved &&
                   newest.outcome == RaidOutcome.RecoveryFailed;
        }

        private static bool AreCanonicalJsonEquivalent(object left, object right)
        {
            if (left == null || right == null || left.GetType() != right.GetType())
            {
                return false;
            }

            try
            {
                return string.Equals(
                    JsonUtility.ToJson(left, false),
                    JsonUtility.ToJson(right, false),
                    StringComparison.Ordinal);
            }
            catch (Exception)
            {
                return false;
            }
        }

        private void ResetTrackedRaid()
        {
            ReleaseSettlementInputLock();
            baseline = null;
            lastCheckpoint = null;
            pendingRestore = null;
            pendingExactSettlementState = null;
            pendingExactSettlementKind = RaidSettlementJournalKind.None;
            ordinarySettlementMirrored = false;
            nextSequence = 0;
            nextCheckpointAt = 0f;
            lastSuccessfulWriteAt = float.NegativeInfinity;
            raidTracked = false;
            handlingWriteFailure = false;
            basePersistenceReady = false;
            baseArrivalComplete = false;
            entryOrigin = RaidEntryOrigin.None;
            trackedOutcome = RaidOutcome.None;
        }
    }
}
