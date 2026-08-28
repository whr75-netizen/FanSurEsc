using System;
using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.Quests
{
    /// <summary>
    /// Owns the single prototype quest's mutable state. Save DTOs transport this state,
    /// while this journal remains the sole runtime writer.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class QuestJournal : MonoBehaviour
    {
        [SerializeField] private QuestDefinition prototypeQuest;
        [SerializeField] private RaidSession raidSession;
        [SerializeField] private RaidCheckpointController raidCheckpoint;

        private QuestProgressState progress;

        public event Action Changed;
        public event Action<string> QuestCompleted;

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
            if (raidSession != null)
            {
                raidSession.StateChanged += HandleRaidStateChanged;
            }
        }

        private void OnDisable()
        {
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

        internal void ApplyPreparedProgress(
            QuestProgressState restoredProgress,
            bool notify)
        {
            if (restoredProgress == null || restoredProgress.Definition != prototypeQuest)
            {
                throw new ArgumentException(
                    "Prepared quest progress does not belong to this journal.",
                    nameof(restoredProgress));
            }

            progress = restoredProgress;
            if (notify)
            {
                NotifyChangedSafely();
            }
        }

        internal void PublishCurrentState()
        {
            NotifyChangedSafely();
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

            NotifyQuestCompletedSafely(prototypeQuest.QuestId);
            NotifyChangedSafely();
            return true;
        }

        private bool CanChangeAtBase(QuestDefinition definition)
        {
            return isActiveAndEnabled && OwnsDefinition(definition) && raidSession != null &&
                   raidSession.CurrentSceneKind == GameplaySceneKind.Base &&
                   raidSession.State == RaidSessionState.Inactive;
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

        private void NotifyQuestCompletedSafely(string questId)
        {
            Action<string> handlers = QuestCompleted;
            if (handlers == null)
            {
                return;
            }

            foreach (Delegate handler in handlers.GetInvocationList())
            {
                try
                {
                    ((Action<string>)handler).Invoke(questId);
                }
                catch (Exception exception)
                {
                    // Completion is already authoritative. Record/UI observers cannot
                    // turn a successful report into a failed quest transaction.
                    Debug.LogException(exception, this);
                }
            }
        }
    }
}
