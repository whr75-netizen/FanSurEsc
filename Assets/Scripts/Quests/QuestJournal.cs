using System;
using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.Quests
{
    /// <summary>
    /// Owns the single prototype quest's mutable state for this gameplay session.
    /// It observes committed raid settlement, but does not own raid state or disk saves.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class QuestJournal : MonoBehaviour
    {
        [SerializeField] private QuestDefinition prototypeQuest;
        [SerializeField] private RaidSession raidSession;
        [SerializeField] private RaidCheckpointController raidCheckpoint;

        private QuestProgressState progress;

        public event Action Changed;

        public QuestDefinition Definition => prototypeQuest;
        public QuestProgressStatus Status => progress?.Status ?? QuestProgressStatus.Available;
        public int EnemyKills => progress?.EnemyKills ?? 0;
        public int RequiredEnemyKills => prototypeQuest != null
            ? prototypeQuest.RequiredEnemyKills
            : 0;
        public bool IsRaidTransitionOrSettlementPending =>
            raidSession != null && raidCheckpoint != null &&
            raidCheckpoint.HasTrackedRaid && !raidSession.IsRaidActive;
        public bool IsConfigured =>
            prototypeQuest != null &&
            raidSession != null && raidSession.IsConfigured &&
            raidCheckpoint != null && raidCheckpoint.IsConfigured;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError(
                    $"{nameof(QuestJournal)} has invalid configuration: missing reference.",
                    this);
                enabled = false;
                return;
            }

            if (!prototypeQuest.TryValidate(out string error))
            {
                Debug.LogError(
                    $"{nameof(QuestJournal)} has invalid configuration: {error}",
                    this);
                enabled = false;
                return;
            }

            progress = new QuestProgressState(prototypeQuest);
        }

        private void OnEnable()
        {
            if (raidCheckpoint != null)
            {
                raidCheckpoint.SettlementCommitted += HandleSettlementCommitted;
            }
            if (raidSession != null)
            {
                raidSession.StateChanged += HandleRaidStateChanged;
            }
        }

        private void OnDisable()
        {
            if (raidCheckpoint != null)
            {
                raidCheckpoint.SettlementCommitted -= HandleSettlementCommitted;
            }
            if (raidSession != null)
            {
                raidSession.StateChanged -= HandleRaidStateChanged;
            }
        }

        public bool OwnsDefinition(QuestDefinition definition)
        {
            return definition != null && definition == prototypeQuest;
        }

        public bool TryAccept(QuestDefinition definition)
        {
            if (!CanChangeAtBase(definition) || progress == null || !progress.TryAccept())
            {
                return false;
            }

            NotifyChangedSafely();
            return true;
        }

        public bool TryRecordPlayerEnemyKill()
        {
            if (progress == null || raidSession == null || raidCheckpoint == null ||
                !raidSession.IsRaidActive || !raidCheckpoint.HasTrackedRaid ||
                !progress.TryRecordEnemyKill())
            {
                return false;
            }

            NotifyChangedSafely();
            return true;
        }

        public bool TryTurnIn(QuestDefinition definition)
        {
            if (!CanChangeAtBase(definition) || progress == null || !progress.TryTurnIn())
            {
                return false;
            }

            NotifyChangedSafely();
            return true;
        }

        private bool CanChangeAtBase(QuestDefinition definition)
        {
            return isActiveAndEnabled && OwnsDefinition(definition) && raidSession != null &&
                   raidSession.CurrentSceneKind == GameplaySceneKind.Base &&
                   raidSession.State == RaidSessionState.Inactive;
        }

        private void HandleSettlementCommitted(RaidOutcome outcome)
        {
            if (progress == null)
            {
                return;
            }

            progress.ApplyCommittedRaidOutcome(outcome);
            // Even when the quest values stay Active + 0, the checkpoint owner has
            // just cleared its tracked raid. Refresh the derived tracker so it does
            // not remain hidden after a failed or objective-missing settlement.
            NotifyChangedSafely();
        }

        private void HandleRaidStateChanged()
        {
            // The journal remains the quest-state authority. This notification only
            // refreshes derived UI while a raid transition/result is awaiting its
            // durable settlement; it does not advance or reset quest progress.
            NotifyChangedSafely();
        }

        private void NotifyChangedSafely()
        {
            Action handlers = Changed;
            if (handlers == null)
            {
                return;
            }

            foreach (Delegate handler in handlers.GetInvocationList())
            {
                try
                {
                    ((Action)handler).Invoke();
                }
                catch (Exception exception)
                {
                    // Quest progress is already authoritative at this point. A UI or
                    // other observer must not abort raid travel, death handling, or a
                    // committed settlement after the state change has succeeded.
                    Debug.LogException(exception, this);
                }
            }
        }
    }
}
