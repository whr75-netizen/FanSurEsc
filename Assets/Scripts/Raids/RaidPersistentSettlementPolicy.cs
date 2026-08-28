using FantasySurvival.Quests;
using FantasySurvival.SaveSystem;

namespace FantasySurvival.Raids
{
    /// <summary>
    /// Single pure composition point for every persistent effect of one committed
    /// raid outcome. The returned snapshot is safe to reuse through checkpoint,
    /// settlement journal, ordinary save, and final live-owner replacement.
    /// </summary>
    public static class RaidPersistentSettlementPolicy
    {
        public static bool TryCreateStateForOutcome(
            GameSaveData source,
            RaidOutcome outcome,
            QuestDefinition questDefinition,
            out GameSaveData settledState,
            out string error)
        {
            settledState = null;
            if (!RaidCheckpointValidator.IsTerminalOutcome(outcome))
            {
                error = $"Raid outcome {outcome} is not terminal.";
                return false;
            }

            if (!GameSaveManager.TryClonePreservingMigrationContext(
                    source,
                    out settledState,
                    out error))
            {
                error = $"Could not clone raid settlement state: {error}";
                return false;
            }

            if (!RaidItemSettlementPolicy.TryDiscardCarriedItems(
                    settledState,
                    outcome,
                    out error) ||
                !PlayerProgressSaveCodec.TryCreateForRaidOutcome(
                    settledState.playerProgress,
                    questDefinition,
                    outcome,
                    out PlayerProgressSaveData settledProgress,
                    out error))
            {
                settledState = null;
                return false;
            }

            settledState.playerProgress = settledProgress;
            error = null;
            return true;
        }
    }
}
