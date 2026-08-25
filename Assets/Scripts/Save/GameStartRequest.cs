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
            public GameSaveData SaveData;
            public GameSaveData FallbackSaveData;
            public RaidRecoveryBaselineData RecoveryBaseline;
            public RaidCheckpointData RaidCheckpoint;
            public GameSaveData RecoverySettlementState;
            public RaidSettlementJournalKind RecoverySettlementKind;
            public RaidOutcome RecoveryOutcome;
        }

        private static PendingRequest pendingRequest;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Clear();
        }

        public static void QueueNewGame()
        {
            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.NewGame
            };
        }

        public static bool QueueLoad(GameSaveData saveData)
        {
            return QueueLoad(saveData, null);
        }

        public static bool QueueLoad(GameSaveData saveData, GameSaveData fallbackSave)
        {
            if (saveData == null)
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.LoadGame,
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
            return QueueRaidRecovery(
                GameStartMode.ResumeRaid,
                baseline,
                checkpoint,
                requireCheckpoint: true);
        }

        public static bool QueueRaidRecoverySettlement(
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint)
        {
            RaidOutcome outcome = checkpoint != null &&
                                  checkpoint.phase == RaidCheckpointPhase.Resolved
                ? checkpoint.outcome
                : RaidOutcome.RecoveryFailed;
            return QueueRaidRecoverySettlement(
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
            if (!RaidCheckpointValidator.IsTerminalOutcome(outcome) ||
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
            if (markedSave == null || !markedSave.raidInProgress ||
                !System.Guid.TryParse(markedSave.activeRaidInstanceId, out _))
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = GameStartMode.SettleOrphanedRaid,
                SaveData = markedSave,
                RecoveryOutcome = RaidOutcome.RecoveryFailed
            };
            return true;
        }

        public static bool TryConsume(out GameStartMode mode, out GameSaveData saveData)
        {
            return TryConsume(out mode, out saveData, out _);
        }

        public static bool TryConsume(
            out GameStartMode mode,
            out GameSaveData saveData,
            out GameSaveData fallbackSave)
        {
            return TryConsume(
                out mode,
                out saveData,
                out fallbackSave,
                out _,
                out _,
                out _,
                out _,
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
            out RaidOutcome recoveryOutcome)
        {
            PendingRequest request = pendingRequest;
            mode = request?.Mode ?? GameStartMode.None;
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
            RaidRecoveryBaselineData baseline,
            RaidCheckpointData checkpoint,
            bool requireCheckpoint)
        {
            if ((mode != GameStartMode.ResumeRaid &&
                 mode != GameStartMode.SettleRaidRecovery) ||
                baseline == null ||
                (requireCheckpoint && checkpoint == null))
            {
                return false;
            }

            pendingRequest = new PendingRequest
            {
                Mode = mode,
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
