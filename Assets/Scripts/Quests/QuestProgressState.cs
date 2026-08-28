using System;
using FantasySurvival.Raids;

namespace FantasySurvival.Quests
{
    public enum QuestProgressStatus
    {
        Available = 0,
        Active = 1,
        ReadyToTurnIn = 2,
        Completed = 3
    }

    /// <summary>
    /// Mutable state for one accepted quest. QuestJournal is its sole owner.
    /// This object has no Unity lifecycle or persistence responsibility.
    /// </summary>
    public sealed class QuestProgressState
    {
        private readonly QuestDefinition definition;
        private QuestProgressStatus status;
        private int enemyKills;

        public QuestProgressState(QuestDefinition definition)
        {
            this.definition = definition;
            status = QuestProgressStatus.Available;
        }

        public QuestDefinition Definition => definition;
        public QuestProgressStatus Status => status;
        public int EnemyKills => enemyKills;
        public int RequiredEnemyKills => definition != null ? definition.RequiredEnemyKills : 0;

        internal static bool TryCreateRestored(
            QuestDefinition definition,
            QuestProgressStatus restoredStatus,
            int restoredEnemyKills,
            out QuestProgressState restored,
            out string error)
        {
            restored = null;
            if (definition == null)
            {
                error = "Quest definition is unavailable.";
                return false;
            }

            if (!definition.TryValidate(out error))
            {
                error = $"Quest definition is invalid: {error}";
                return false;
            }

            if (!Enum.IsDefined(typeof(QuestProgressStatus), restoredStatus) ||
                restoredEnemyKills < 0 ||
                restoredEnemyKills > definition.RequiredEnemyKills)
            {
                error = "Saved quest status or enemy-kill progress is out of range.";
                return false;
            }

            bool validCombination = restoredStatus switch
            {
                QuestProgressStatus.Available => restoredEnemyKills == 0,
                QuestProgressStatus.Active =>
                    definition.RequiresSuccessfulExtraction ||
                    restoredEnemyKills < definition.RequiredEnemyKills,
                QuestProgressStatus.ReadyToTurnIn =>
                    restoredEnemyKills == definition.RequiredEnemyKills,
                QuestProgressStatus.Completed =>
                    restoredEnemyKills == definition.RequiredEnemyKills,
                _ => false
            };
            if (!validCombination)
            {
                error = "Saved quest status and enemy-kill progress are inconsistent.";
                return false;
            }

            restored = new QuestProgressState(definition)
            {
                status = restoredStatus,
                enemyKills = restoredEnemyKills
            };
            error = null;
            return true;
        }

        public bool TryAccept()
        {
            if (definition == null || status != QuestProgressStatus.Available)
            {
                return false;
            }

            status = QuestProgressStatus.Active;
            enemyKills = 0;
            return true;
        }

        public bool TryRecordEnemyKill()
        {
            if (definition == null || status != QuestProgressStatus.Active)
            {
                return false;
            }

            int previousKills = enemyKills;
            if (enemyKills < definition.RequiredEnemyKills)
            {
                enemyKills++;
            }

            if (!definition.RequiresSuccessfulExtraction &&
                enemyKills >= definition.RequiredEnemyKills)
            {
                status = QuestProgressStatus.ReadyToTurnIn;
            }

            return enemyKills != previousKills || status == QuestProgressStatus.ReadyToTurnIn;
        }

        public bool ApplyCommittedRaidOutcome(RaidOutcome outcome)
        {
            if (definition == null || status != QuestProgressStatus.Active ||
                outcome == RaidOutcome.None)
            {
                return false;
            }

            QuestProgressStatus previousStatus = status;
            int previousKills = enemyKills;
            if (outcome == RaidOutcome.Extracted &&
                enemyKills >= definition.RequiredEnemyKills)
            {
                status = QuestProgressStatus.ReadyToTurnIn;
            }
            else
            {
                // A failed raid, or an extraction before the objective was met, starts
                // the next attempt at zero without silently cancelling the quest.
                enemyKills = 0;
            }

            return previousStatus != status || previousKills != enemyKills;
        }

        public bool TryTurnIn()
        {
            if (status != QuestProgressStatus.ReadyToTurnIn)
            {
                return false;
            }

            status = QuestProgressStatus.Completed;
            return true;
        }
    }
}
