using System;
using FantasySurvival.Quests;
using FantasySurvival.Raids;
using FantasySurvival.SaveSystem;
using UnityEngine;

namespace FantasySurvival.Information
{
    /// <summary>
    /// Owns aggregate Player records for the current persistent gameplay shell.
    /// Save DTOs transport exact snapshots; this component remains the sole runtime writer.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class PlayerSessionRecords : MonoBehaviour
    {
        [SerializeField] private QuestJournal questJournal;
        [SerializeField] private RaidCheckpointController raidCheckpoint;

        public event Action Changed;

        public int EnemyKills { get; private set; }
        public int SuccessfulExtractions { get; private set; }
        public int PlayerDeaths { get; private set; }
        public int Abandonments { get; private set; }
        public int RecoveryFailures { get; private set; }
        public int CompletedQuests { get; private set; }
        public int SettledRaids
        {
            get
            {
                long total = (long)SuccessfulExtractions + PlayerDeaths +
                             Abandonments + RecoveryFailures;
                return total >= int.MaxValue ? int.MaxValue : (int)total;
            }
        }
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
            if (questJournal != null)
            {
                questJournal.QuestCompleted += HandleQuestCompleted;
            }
        }

        private void OnDisable()
        {
            if (questJournal != null)
            {
                questJournal.QuestCompleted -= HandleQuestCompleted;
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

            if (EnemyKills < int.MaxValue)
            {
                EnemyKills++;
            }
            NotifyChangedSafely();
        }

        internal void ApplyPreparedRecords(
            PlayerProgressSaveData snapshot,
            bool notify)
        {
            if (snapshot == null)
            {
                throw new ArgumentNullException(nameof(snapshot));
            }

            EnemyKills = snapshot.enemyKills;
            SuccessfulExtractions = snapshot.successfulExtractions;
            PlayerDeaths = snapshot.playerDeaths;
            Abandonments = snapshot.abandonments;
            RecoveryFailures = snapshot.recoveryFailures;
            CompletedQuests = snapshot.completedQuests;
            if (notify)
            {
                NotifyChangedSafely();
            }
        }

        internal void PublishCurrentState()
        {
            NotifyChangedSafely();
        }

        private void HandleQuestCompleted(string questId)
        {
            if (!isActiveAndEnabled || questJournal == null ||
                questJournal.Definition == null ||
                !string.Equals(
                    questJournal.Definition.QuestId,
                    questId,
                    StringComparison.Ordinal) ||
                CompletedQuests == int.MaxValue)
            {
                return;
            }

            CompletedQuests++;
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
                    // Records are already updated. A derived presentation must not
                    // invalidate combat or a durably committed raid settlement.
                    Debug.LogException(exception, this);
                }
            }
        }
    }
}
