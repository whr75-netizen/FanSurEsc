using FantasySurvival.Raids;

namespace FantasySurvival.Quests
{
    public enum QuestProgressStatus
    {
        Available,
        Active,
        ReadyToTurnIn,
        Completed
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
