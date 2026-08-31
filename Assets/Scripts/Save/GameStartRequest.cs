using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    public enum GameStartMode
    {
        None,
        NewGame,
        LoadGame,
        ResumeRaid,
        SettleRaidRecovery,
        SettleOrphanedRaid
    }

    public static class GameStartRequest
    {
        private sealed class PendingRequest
        {
            public GameStartMode Mode;
            public int SaveSlotIndex;
            public GameSaveData SaveData;
            public GameSaveData FallbackSaveData;
            public RaidRecoveryBaselineData RecoveryBaseline;
            public RaidCheckpointData RaidCheckpoint;
            public GameSaveData RecoverySettlementState;
            public RaidSettlementJournalKind RecoverySettlementKind;
            public RaidOutcome RecoveryOutcome;
        }

        private static PendingRequest pendingRequest;

        internal static bool HasPendingRequest =>
            pendingRequest != null && pendingRequest.Mode != GameStartMode.None;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Clear();
        }

        public static void QueueNewGame()
        {
            QueueNewGame(GameSaveManager.DefaultSlotIndex);
        }

        public static bool QueueNewGame(int saveSlotIndex)
        {
            if (!GameSaveManager.IsValidSlotIndex(saveSlotIndex))
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.NewGame,
                SaveSlotIndex = saveSlotIndex
            };
            return true;
        }

        public static bool QueueLoad(GameSaveData saveData)
        {
            return QueueLoad(saveData, null);
        }

        public static bool QueueLoad(GameSaveData saveData, GameSaveData fallbackSave)
        {
            return QueueLoad(
                GameSaveManager.DefaultSlotIndex,
                saveData,
                fallbackSave);
        }

        public static bool QueueLoad(int saveSlotIndex, GameSaveData saveData)
        {
            return QueueLoad(saveSlotIndex, saveData, null);
        }

        public static bool QueueLoad(
            int saveSlotIndex,
            GameSaveData saveData,
            GameSaveData fallbackSave)
        {
            if (!GameSaveManager.IsValidSlotIndex(saveSlotIndex) || saveData == null)
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.LoadGame,
                SaveSlotIndex = saveSlotIndex,
                SaveData = saveData,
                FallbackSaveData = object.ReferenceEquals(saveData, fallbackSave)
                    ? null
                    : fallbackSave
            };
            return true;
        }

        public static bool QueueResumeRaid(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint)
        {
            return QueueResumeRaid(
                GameSaveManager.DefaultSlotIndex,
                baseline,
                checkpoint);
        }

        public static bool QueueResumeRaid(
            int saveSlotIndex,
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint)
        {
            return QueueRaidRecovery(
                GameStartMode.ResumeRaid,
                saveSlotIndex,
                baseline,
                checkpoint,
                requireCheckpoint: true);
        }

        public static bool QueueRaidRecoverySettlement(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint)
        {
            return QueueRaidRecoverySettlement(
                GameSaveManager.DefaultSlotIndex,
                baseline,
                checkpoint);
        }

        public static bool QueueRaidRecoverySettlement(
            int saveSlotIndex,
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint)
        {
            RaidOutcome outcome = checkpoint != null &&
                                  checkpoint.phase == RaidCheckpointPhase.Resolved
                ? checkpoint.outcome
                : RaidOutcome.RecoveryFailed;
            return QueueRaidRecoverySettlement(
                saveSlotIndex,
                baseline,
                checkpoint,
                null,
                RaidSettlementJournalKind.None,
                outcome);
        }

        public static bool QueueRaidRecoverySettlement(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            GameSaveData settlementState,
            RaidSettlementJournalKind settlementKind,
            RaidOutcome outcome)
        {
            return QueueRaidRecoverySettlement(
                GameSaveManager.DefaultSlotIndex,
                baseline,
                checkpoint,
                settlementState,
                settlementKind,
                outcome);
        }

        public static bool QueueRaidRecoverySettlement(
            int saveSlotIndex,
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            GameSaveData settlementState,
            RaidSettlementJournalKind settlementKind,
            RaidOutcome outcome)
        {
            if (!GameSaveManager.IsValidSlotIndex(saveSlotIndex) ||
                !RaidCheckpointValidator.IsTerminalOutcome(outcome) ||
                (settlementState == null &&
                 settlementKind != RaidSettlementJournalKind.None) ||
                (settlementState != null &&
                 settlementKind != RaidSettlementJournalKind.OutcomeSettlement &&
                 settlementKind != RaidSettlementJournalKind.FreshDepartureRollback) ||
                (settlementKind == RaidSettlementJournalKind.FreshDepartureRollback &&
                 outcome != RaidOutcome.RecoveryFailed))
            {
                return false;
            }

            bool queued = QueueRaidRecovery(
                GameStartMode.SettleRaidRecovery,
                saveSlotIndex,
                baseline,
                checkpoint,
                requireCheckpoint: false);
            if (queued)
            {
                pendingRequest.RecoverySettlementState = settlementState;
                pendingRequest.RecoverySettlementKind = settlementKind;
                pendingRequest.RecoveryOutcome = outcome;
            }

            return queued;
        }

        public static bool QueueOrphanedRaidFailure(GameSaveData markedSave)
        {
            return QueueOrphanedRaidFailure(
                GameSaveManager.DefaultSlotIndex,
                markedSave);
        }

        public static bool QueueOrphanedRaidFailure(
            int saveSlotIndex,
            GameSaveData markedSave)
        {
            if (!GameSaveManager.IsValidSlotIndex(saveSlotIndex) ||
                markedSave == null || !markedSave.raidInProgress ||
                !System.Guid.TryParse(markedSave.activeRaidInstanceId, out _))
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.SettleOrphanedRaid,
                SaveSlotIndex = saveSlotIndex,
                SaveData = markedSave,
                RecoveryOutcome = RaidOutcome.RecoveryFailed
            };
            return true;
        }

        public static bool TryConsume(out GameStartMode mode, out GameSaveData saveData)
        {
            return TryConsume(out mode, out saveData, out _, out _);
        }

        public static bool TryConsume(
            out GameStartMode mode,
            out GameSaveData saveData,
            out GameSaveData fallbackSave)
        {
            return TryConsume(out mode, out saveData, out fallbackSave, out _);
        }

        public static bool TryConsume(
            out GameStartMode mode,
            out GameSaveData saveData,
            out GameSaveData fallbackSave,
            out int saveSlotIndex)
        {
            return TryConsume(
                out mode,
                out saveData,
                out fallbackSave,
                out _,
                out _,
                out _,
                out _,
                out _,
                out saveSlotIndex);
        }

        public static bool TryConsume(
            out GameStartMode mode,
            out GameSaveData saveData,
            out GameSaveData fallbackSave,
            out RaidRecoveryBaselineData recoveryBaseline,
            out RaidCheckpointData raidCheckpoint,
            out GameSaveData recoverySettlementState,
            out RaidSettlementJournalKind recoverySettlementKind,
            out RaidOutcome recoveryOutcome)
        {
            return TryConsume(
                out mode,
                out saveData,
                out fallbackSave,
                out recoveryBaseline,
                out raidCheckpoint,
                out recoverySettlementState,
                out recoverySettlementKind,
                out recoveryOutcome,
                out _);
        }

        public static bool TryConsume(
            out GameStartMode mode,
            out GameSaveData saveData,
            out GameSaveData fallbackSave,
            out RaidRecoveryBaselineData recoveryBaseline,
            out RaidCheckpointData raidCheckpoint,
            out GameSaveData recoverySettlementState,
            out RaidSettlementJournalKind recoverySettlementKind,
            out RaidOutcome recoveryOutcome,
            out int saveSlotIndex)
        {
            PendingRequest request = pendingRequest;
            mode = request?.Mode ?? GameStartMode.None;
            saveSlotIndex = request?.SaveSlotIndex ?? GameSaveManager.DefaultSlotIndex;
            saveData = request?.SaveData;
            fallbackSave = request?.FallbackSaveData;
            recoveryBaseline = request?.RecoveryBaseline;
            raidCheckpoint = request?.RaidCheckpoint;
            recoverySettlementState = request?.RecoverySettlementState;
            recoverySettlementKind = request?.RecoverySettlementKind ??
                                     RaidSettlementJournalKind.None;
            recoveryOutcome = request?.RecoveryOutcome ?? RaidOutcome.None;

            bool hasRequest = mode != GameStartMode.None;
            Clear();
            return hasRequest;
        }

        private static bool QueueRaidRecovery(
            GameStartMode mode,
            int saveSlotIndex,
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            bool requireCheckpoint)
        {
            if ((mode != GameStartMode.ResumeRaid &&
                 mode != GameStartMode.SettleRaidRecovery) ||
                !GameSaveManager.IsValidSlotIndex(saveSlotIndex) ||
                baseline == null ||
                (requireCheckpoint && checkpoint == null))
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = mode,
                SaveSlotIndex = saveSlotIndex,
                RecoveryBaseline = baseline,
                RaidCheckpoint = checkpoint
            };
            return true;
        }

        private static void Clear()
        {
            pendingRequest = null;
        }
    }
}
