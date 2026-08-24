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
        Abandoned
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

            state = RaidSessionState.Entering;
            outcome = RaidOutcome.None;
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
                RaidOutcome completedOutcome = outcome;
                if (completedOutcome == RaidOutcome.PlayerDied && playerStats != null)
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

        private void ResetRaidState(bool notify = true)
        {
            state = RaidSessionState.Inactive;
            outcome = RaidOutcome.None;
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
    }
}
