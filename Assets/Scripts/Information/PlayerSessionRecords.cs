using System;
using FantasySurvival.Quests;
using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.Information
{
    /// <summary>
    /// Owns lightweight aggregate records for the current persistent gameplay shell.
    /// These values intentionally live for one Play Session and are not save data.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class PlayerSessionRecords : MonoBehaviour
    {
        [SerializeField] private QuestJournal questJournal;
        [SerializeField] private RaidCheckpointController raidCheckpoint;

        private QuestProgressStatus previousQuestStatus;

        public event Action Changed;

        public int EnemyKills { get; private set; }
        public int SuccessfulExtractions { get; private set; }
        public int PlayerDeaths { get; private set; }
        public int Abandonments { get; private set; }
        public int RecoveryFailures { get; private set; }
        public int CompletedQuests { get; private set; }
        public int SettledRaids =>
            SuccessfulExtractions + PlayerDeaths + Abandonments + RecoveryFailures;
        public bool IsConfigured => questJournal != null && raidCheckpoint != null;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(PlayerSessionRecords)} has missing required references.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            previousQuestStatus = questJournal != null
                ? questJournal.Status
                : QuestProgressStatus.Available;

            if (questJournal != null)
            {
                questJournal.Changed += HandleQuestChanged;
            }
            if (raidCheckpoint != null)
            {
                raidCheckpoint.SettlementCommitted += HandleSettlementCommitted;
            }
        }

        private void OnDisable()
        {
            if (questJournal != null)
            {
                questJournal.Changed -= HandleQuestChanged;
            }
            if (raidCheckpoint != null)
            {
                raidCheckpoint.SettlementCommitted -= HandleSettlementCommitted;
            }
        }

        /// <summary>
        /// Called only after the existing Player damage-source attribution has confirmed a kill.
        /// </summary>
        public void RecordPlayerEnemyKill()
        {
            if (!isActiveAndEnabled)
            {
                return;
            }

            EnemyKills++;
            NotifyChangedSafely();
        }

        private void HandleSettlementCommitted(RaidOutcome outcome)
        {
            switch (outcome)
            {
                case RaidOutcome.Extracted:
                    SuccessfulExtractions++;
                    break;
                case RaidOutcome.PlayerDied:
                    PlayerDeaths++;
                    break;
                case RaidOutcome.Abandoned:
                    Abandonments++;
                    break;
                case RaidOutcome.RecoveryFailed:
                    RecoveryFailures++;
                    break;
                default:
                    return;
            }

            NotifyChangedSafely();
        }

        private void HandleQuestChanged()
        {
            QuestProgressStatus currentStatus = questJournal != null
                ? questJournal.Status
                : QuestProgressStatus.Available;
            if (previousQuestStatus != QuestProgressStatus.Completed &&
                currentStatus == QuestProgressStatus.Completed)
            {
                CompletedQuests++;
                NotifyChangedSafely();
            }

            previousQuestStatus = currentStatus;
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
                    // Records are already updated. A derived presentation must not
                    // invalidate combat or a durably committed raid settlement.
                    Debug.LogException(exception, this);
                }
            }
        }
    }
}
