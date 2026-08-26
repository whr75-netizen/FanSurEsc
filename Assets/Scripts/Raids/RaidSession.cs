using System;
using FantasySurvival.Combat;
using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.Raids
{
    public enum GameplaySceneKind
    {
        Unknown,
        Base,
        Raid
    }

    public enum RaidSessionState
    {
        Inactive,
        Entering,
        Active,
        Resolved,
        Returning
    }

    public enum RaidOutcome
    {
        None,
        Extracted,
        PlayerDied,
        Abandoned,
        RecoveryFailed
    }

    /// <summary>
    /// Owns one raid's in-memory lifecycle and outcome. It does not own Player,
    /// inventory contents, scene loading, or disk persistence.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class RaidSession : MonoBehaviour
    {
        [SerializeField] private PlayerStats playerStats;
        [SerializeField] private string defaultBaseScene = "GameMap1";
        [SerializeField] private string defaultBaseSpawnId = "BaseReturn";

        private GameplaySceneKind currentSceneKind = GameplaySceneKind.Unknown;
        private RaidSessionState state = RaidSessionState.Inactive;
        private RaidOutcome outcome = RaidOutcome.None;
        private string returnScene;
        private string returnSpawnId;
        private bool pendingBaseSettlement;
        private bool pendingFreshInvalidMapReturn;

        public event Action StateChanged;
        public event Action<RaidOutcome> Resolved;
        public event Action ReturnTravelFailed;

        public GameplaySceneKind CurrentSceneKind => currentSceneKind;
        public RaidSessionState State => state;
        public RaidOutcome Outcome => outcome;
        public bool IsRaidActive =>
            currentSceneKind == GameplaySceneKind.Raid && state == RaidSessionState.Active;
        public bool IsRaidResolved =>
            currentSceneKind == GameplaySceneKind.Raid &&
            (state == RaidSessionState.Resolved || state == RaidSessionState.Returning);
        public bool IsConfigured =>
            playerStats != null &&
            !string.IsNullOrWhiteSpace(defaultBaseScene) &&
            !string.IsNullOrWhiteSpace(defaultBaseSpawnId);

        private void Awake()
        {
            ResetReturnRoute();
            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(RaidSession)} has missing required configuration.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            if (playerStats != null)
            {
                playerStats.Died += HandlePlayerDied;
            }
        }

        private void OnDisable()
        {
            if (playerStats != null)
            {
                playerStats.Died -= HandlePlayerDied;
            }
        }

        public bool TryBeginRaid(string destinationScene, string destinationSpawnId)
        {
            if (!isActiveAndEnabled ||
                currentSceneKind != GameplaySceneKind.Base ||
                state != RaidSessionState.Inactive ||
                string.IsNullOrWhiteSpace(destinationScene) ||
                string.IsNullOrWhiteSpace(destinationSpawnId))
            {
                return false;
            }

            RaidCheckpointController checkpoint = GetCheckpointController();
            if (checkpoint == null || !checkpoint.IsConfigured)
            {
                Debug.LogError("Cannot begin a raid because its checkpoint controller is unavailable.", this);
                return false;
            }

            if (!checkpoint.TryPrepareNewRaid(
                    destinationScene,
                    destinationSpawnId,
                    out string checkpointError))
            {
                Debug.LogError(
                    $"Cannot begin a raid because its durable recovery baseline could not be created: {checkpointError}",
                    this);
                return false;
            }

            return BeginRaidTravel(destinationScene, destinationSpawnId);
        }

        internal bool TryBeginRecoveredTravel(
            string destinationScene,
            string destinationSpawnId)
        {
            if (!isActiveAndEnabled ||
                currentSceneKind != GameplaySceneKind.Base ||
                state != RaidSessionState.Inactive ||
                string.IsNullOrWhiteSpace(destinationScene) ||
                string.IsNullOrWhiteSpace(destinationSpawnId))
            {
                return false;
            }

            // The checkpoint controller has already staged and validated the existing
            // baseline/checkpoint pair. Do not create a new baseline on this path.
            return BeginRaidTravel(destinationScene, destinationSpawnId);
        }

        internal bool TryResolveRecoveryFailure(string reason)
        {
            if (!string.IsNullOrWhiteSpace(reason))
            {
                Debug.LogError($"Raid recovery failed: {reason}", this);
            }

            return Resolve(RaidOutcome.RecoveryFailed);
        }

        internal bool TryOverrideResolvedOutcomeWithRecoveryFailure(string reason)
        {
            if (currentSceneKind != GameplaySceneKind.Raid ||
                (state != RaidSessionState.Resolved && state != RaidSessionState.Returning) ||
                outcome == RaidOutcome.None)
            {
                return false;
            }

            if (!string.IsNullOrWhiteSpace(reason))
            {
                Debug.LogError($"Resolved raid was changed to recovery failure: {reason}", this);
            }

            state = RaidSessionState.Resolved;
            outcome = RaidOutcome.RecoveryFailed;
            playerStats?.SetDamageBlocked(true);
            NotifyStateChanged();
            Resolved?.Invoke(RaidOutcome.RecoveryFailed);
            return true;
        }

        internal bool TryAbortRecoveredEntryAsFailure()
        {
            if (currentSceneKind != GameplaySceneKind.Base || state != RaidSessionState.Entering)
            {
                return false;
            }

            state = RaidSessionState.Inactive;
            outcome = RaidOutcome.RecoveryFailed;
            pendingBaseSettlement = false;
            pendingFreshInvalidMapReturn = false;
            ResetReturnRoute();
            playerStats?.SetDamageBlocked(false);
            NotifyStateChanged();
            return true;
        }

        internal bool TryReturnFromInvalidRaidArrival(
            string activeSceneName,
            string reason,
            out string error)
        {
            if (currentSceneKind != GameplaySceneKind.Base ||
                state != RaidSessionState.Entering)
            {
                error = "Only a raid that is still entering can reject its destination map.";
                return false;
            }

            RaidCheckpointController checkpoint = GetCheckpointController();
            if (checkpoint == null || !checkpoint.IsConfigured)
            {
                error = "The raid checkpoint controller is unavailable.";
                return false;
            }

            if (!DirectSceneTravel.CanRedirectPendingArrival(
                    activeSceneName,
                    defaultBaseScene,
                    defaultBaseSpawnId,
                    out error))
            {
                return false;
            }

            if (!checkpoint.TryPrepareInvalidMapReturn(
                    reason,
                    out bool recoveryFailed,
                    out error))
            {
                return false;
            }

            pendingBaseSettlement = false;
            pendingFreshInvalidMapReturn = !recoveryFailed;
            ResetReturnRoute();
            currentSceneKind = GameplaySceneKind.Raid;
            state = RaidSessionState.Returning;
            if (recoveryFailed)
            {
                // A recovered exact seed must never be replaced with a different map.
                // Preserve the established fail-closed item policy and let the normal
                // base-arrival settlement apply it atomically.
                outcome = RaidOutcome.RecoveryFailed;
                playerStats?.SetDamageBlocked(true);
            }
            else
            {
                // A fresh technical generation failure is not a gameplay loss. Its
                // checkpoint controller has durably selected the exact pre-departure
                // state; ordinary mirroring and cleanup finish through the base gate.
                outcome = RaidOutcome.None;
            }

            NotifyStateChanged();

            if (!DirectSceneTravel.TryRedirectPendingArrival(
                    activeSceneName,
                    defaultBaseScene,
                    defaultBaseSpawnId,
                    HandleInvalidMapReturnTravelCompleted,
                    out error))
            {
                // TryRedirectPendingArrival deliberately preserves the replacement
                // pending token and black input lock when the Base load cannot even
                // start. Do not claim a visible Raid/Base state or clear rollback data.
                return false;
            }

            Debug.LogWarning(
                $"Raid scene '{activeSceneName}' was rejected before arrival completed: {reason} " +
                "The covered transition is returning to base.",
                this);
            return true;
        }

        private bool BeginRaidTravel(string destinationScene, string destinationSpawnId)
        {
            state = RaidSessionState.Entering;
            outcome = RaidOutcome.None;
            pendingBaseSettlement = false;
            pendingFreshInvalidMapReturn = false;
            ResetReturnRoute();
            NotifyStateChanged();

            return DirectSceneTravel.TryLoad(
                destinationScene,
                destinationSpawnId,
                HandleBeginTravelCompleted);
        }

        public bool TryResolveExtraction(string baseScene, string baseSpawnId)
        {
            if (!IsRaidActive ||
                string.IsNullOrWhiteSpace(baseScene) ||
                string.IsNullOrWhiteSpace(baseSpawnId))
            {
                return false;
            }

            returnScene = baseScene;
            returnSpawnId = baseSpawnId;
            return Resolve(RaidOutcome.Extracted);
        }

        public bool TryResolveAbandonment()
        {
            return Resolve(RaidOutcome.Abandoned);
        }

        public bool TryReturnToBase()
        {
            if (state != RaidSessionState.Resolved ||
                currentSceneKind != GameplaySceneKind.Raid ||
                string.IsNullOrWhiteSpace(returnScene) ||
                string.IsNullOrWhiteSpace(returnSpawnId))
            {
                return false;
            }

            state = RaidSessionState.Returning;
            NotifyStateChanged();

            return DirectSceneTravel.TryLoad(
                returnScene,
                returnSpawnId,
                HandleReturnTravelCompleted);
        }

        public bool TryEnterScene(GameplaySceneKind sceneKind, out string error)
        {
            if (sceneKind == GameplaySceneKind.Unknown)
            {
                error = "Gameplay scene kind is not configured.";
                return false;
            }

            if (state == RaidSessionState.Entering && sceneKind != GameplaySceneKind.Raid)
            {
                error = "A raid entry request reached a scene that is not configured as Raid.";
                return false;
            }

            if (state == RaidSessionState.Returning && sceneKind != GameplaySceneKind.Base)
            {
                error = "A raid return request reached a scene that is not configured as Base.";
                return false;
            }

            currentSceneKind = sceneKind;
            if (sceneKind == GameplaySceneKind.Raid)
            {
                if (state == RaidSessionState.Inactive || state == RaidSessionState.Entering)
                {
                    state = RaidSessionState.Active;
                    outcome = RaidOutcome.None;
                    ResetReturnRoute();
                }
            }
            else if (state != RaidSessionState.Inactive)
            {
                bool freshInvalidMapReturn = pendingFreshInvalidMapReturn;
                RaidOutcome completedOutcome = outcome;
                if ((completedOutcome == RaidOutcome.PlayerDied ||
                     completedOutcome == RaidOutcome.RecoveryFailed) &&
                    playerStats != null)
                {
                    // A dead persistent Player must be usable again after reaching the base.
                    playerStats.ResetHealth();
                }

                if (state == RaidSessionState.Active || state == RaidSessionState.Entering)
                {
                    Debug.LogWarning(
                        "Entered the base without a resolved raid outcome; the in-memory raid was cleared without changing inventory.",
                        this);
                }

                ResetRaidState(false);
                // A fresh invalid-map return has no gameplay outcome, but its exact
                // departure rollback still must pass the normal BasePersistenceReady
                // + arrival-complete transaction gate. The checkpoint owner suppresses
                // SettlementCommitted for that technical rollback after cleanup.
                pendingBaseSettlement = freshInvalidMapReturn || completedOutcome != RaidOutcome.None;
            }

            NotifyStateChanged();
            error = null;
            return true;
        }

        public void CompleteSceneArrival(GameplaySceneKind sceneKind)
        {
            if (sceneKind != currentSceneKind)
            {
                Debug.LogWarning(
                    $"Ignored arrival completion for {sceneKind} because the current context is {currentSceneKind}.",
                    this);
                return;
            }

            bool canReceiveDamage =
                (sceneKind == GameplaySceneKind.Base && state == RaidSessionState.Inactive) ||
                (sceneKind == GameplaySceneKind.Raid && state == RaidSessionState.Active);
            if (canReceiveDamage)
            {
                playerStats?.SetDamageBlocked(false);
            }

            if (sceneKind == GameplaySceneKind.Base &&
                state == RaidSessionState.Inactive &&
                pendingBaseSettlement)
            {
                pendingBaseSettlement = false;
                GetCheckpointController()?.ConfirmBaseSettlement();
            }
        }

        private bool Resolve(RaidOutcome resolvedOutcome)
        {
            if (!IsRaidActive || resolvedOutcome == RaidOutcome.None)
            {
                return false;
            }

            state = RaidSessionState.Resolved;
            outcome = resolvedOutcome;
            playerStats?.SetDamageBlocked(true);
            NotifyStateChanged();
            Resolved?.Invoke(resolvedOutcome);
            return true;
        }

        private void HandlePlayerDied(PlayerStats source, DamageContext context)
        {
            Resolve(RaidOutcome.PlayerDied);
        }

        private void HandleBeginTravelCompleted(bool succeeded)
        {
            if (!succeeded && state == RaidSessionState.Entering)
            {
                GetCheckpointController()?.NotifyRaidEntryTravelFailed();
                ResetRaidState();
            }
        }

        private void HandleReturnTravelCompleted(bool succeeded)
        {
            if (succeeded || state != RaidSessionState.Returning)
            {
                return;
            }

            state = RaidSessionState.Resolved;
            NotifyStateChanged();
            ReturnTravelFailed?.Invoke();
        }

        private void HandleInvalidMapReturnTravelCompleted(bool succeeded)
        {
            if (succeeded || state != RaidSessionState.Returning)
            {
                return;
            }

            // The redirect load started but Base arrival configuration later failed.
            // Match normal return failure semantics so the result UI can retry Base or
            // leave for Main Menu. Fresh technical rollback keeps Outcome=None.
            state = RaidSessionState.Resolved;
            NotifyStateChanged();
            ReturnTravelFailed?.Invoke();
        }

        private void ResetRaidState(bool notify = true)
        {
            state = RaidSessionState.Inactive;
            outcome = RaidOutcome.None;
            pendingFreshInvalidMapReturn = false;
            ResetReturnRoute();
            if (notify)
            {
                NotifyStateChanged();
            }
        }

        private void ResetReturnRoute()
        {
            returnScene = defaultBaseScene;
            returnSpawnId = defaultBaseSpawnId;
        }

        private void NotifyStateChanged()
        {
            StateChanged?.Invoke();
        }

        private static RaidCheckpointController GetCheckpointController()
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            return shell != null ? shell.RaidCheckpoint : null;
        }
    }
}
