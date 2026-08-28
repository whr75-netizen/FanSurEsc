using System;
using System.Collections.Generic;
using FantasySurvival.Information;
using FantasySurvival.Quests;
using FantasySurvival.Raids;

namespace FantasySurvival.SaveSystem
{
    /// <summary>
    /// Transports QuestJournal and PlayerSessionRecords state without becoming a
    /// second runtime authority. Restore is prepare-then-replace; raid settlement is
    /// a pure projection that never mutates either the source DTO or live owners.
    /// </summary>
    public static class PlayerProgressSaveCodec
    {
        public sealed class RestorePlan
        {
            internal RestorePlan(
                QuestProgressState questProgress,
                PlayerProgressSaveData snapshot)
            {
                QuestProgress = questProgress;
                Snapshot = snapshot;
            }

            internal QuestProgressState QuestProgress { get; }
            internal PlayerProgressSaveData Snapshot { get; }
        }

        public static PlayerProgressSaveData CreateEmptySaveData(
            bool allowAuthoredQuestInitialization)
        {
            return new PlayerProgressSaveData
            {
                formatVersion = PlayerProgressSaveData.CurrentFormatVersion,
                questRecordCount = 0,
                quests = new List<QuestProgressSaveData>(),
                allowAuthoredQuestInitialization = allowAuthoredQuestInitialization,
                enemyKills = 0,
                successfulExtractions = 0,
                playerDeaths = 0,
                abandonments = 0,
                recoveryFailures = 0,
                completedQuests = 0
            };
        }

        public static bool TryCapture(
            QuestJournal journal,
            PlayerSessionRecords records,
            out PlayerProgressSaveData saveData,
            out string error)
        {
            saveData = null;
            if (journal == null || !journal.IsConfigured || journal.Definition == null ||
                records == null || !records.IsConfigured)
            {
                error = "Player quest or record authority is unavailable.";
                return false;
            }

            saveData = new PlayerProgressSaveData
            {
                formatVersion = PlayerProgressSaveData.CurrentFormatVersion,
                questRecordCount = 1,
                quests = new List<QuestProgressSaveData>
                {
                    new QuestProgressSaveData
                    {
                        questId = journal.Definition.QuestId,
                        status = journal.Status,
                        enemyKills = journal.EnemyKills
                    }
                },
                allowAuthoredQuestInitialization = false,
                enemyKills = records.EnemyKills,
                successfulExtractions = records.SuccessfulExtractions,
                playerDeaths = records.PlayerDeaths,
                abandonments = records.Abandonments,
                recoveryFailures = records.RecoveryFailures,
                completedQuests = records.CompletedQuests
            };

            if (!TryValidateStructure(saveData, out error) ||
                !QuestProgressState.TryCreateRestored(
                    journal.Definition,
                    journal.Status,
                    journal.EnemyKills,
                    out _,
                    out error))
            {
                saveData = null;
                return false;
            }

            error = null;
            return true;
        }

        public static bool TryValidateStructure(
            PlayerProgressSaveData saveData,
            out string error)
        {
            if (saveData == null ||
                saveData.formatVersion != PlayerProgressSaveData.CurrentFormatVersion ||
                saveData.quests == null ||
                saveData.questRecordCount < 0 ||
                saveData.questRecordCount != saveData.quests.Count ||
                saveData.questRecordCount > 1)
            {
                error = "Player progress payload has an unsupported header or quest roster.";
                return false;
            }

            if ((saveData.questRecordCount == 0) !=
                saveData.allowAuthoredQuestInitialization)
            {
                error = "Player progress quest roster and migration provenance disagree.";
                return false;
            }

            foreach (QuestProgressSaveData quest in saveData.quests)
            {
                if (quest == null || string.IsNullOrWhiteSpace(quest.questId) ||
                    !Enum.IsDefined(typeof(QuestProgressStatus), quest.status) ||
                    quest.enemyKills < 0 ||
                    (quest.status == QuestProgressStatus.Available && quest.enemyKills != 0) ||
                    ((quest.status == QuestProgressStatus.ReadyToTurnIn ||
                      quest.status == QuestProgressStatus.Completed) &&
                     quest.enemyKills <= 0))
                {
                    error = "Player progress payload contains an invalid quest record.";
                    return false;
                }
            }

            if (saveData.enemyKills < 0 ||
                saveData.successfulExtractions < 0 ||
                saveData.playerDeaths < 0 ||
                saveData.abandonments < 0 ||
                saveData.recoveryFailures < 0 ||
                saveData.completedQuests < 0)
            {
                error = "Player progress payload contains an invalid aggregate record.";
                return false;
            }

            error = null;
            return true;
        }

        public static bool HasProjectedRaidOutcome(
            PlayerProgressSaveData saveData,
            RaidOutcome outcome)
        {
            if (!TryValidateStructure(saveData, out _))
            {
                return false;
            }

            if (!saveData.allowAuthoredQuestInitialization)
            {
                return true;
            }

            return outcome switch
            {
                RaidOutcome.Extracted => saveData.successfulExtractions > 0,
                RaidOutcome.PlayerDied => saveData.playerDeaths > 0,
                RaidOutcome.Abandoned => saveData.abandonments > 0,
                RaidOutcome.RecoveryFailed => saveData.recoveryFailures > 0,
                _ => false
            };
        }

        public static bool TryPrepareRestore(
            PlayerProgressSaveData saveData,
            QuestJournal journal,
            PlayerSessionRecords records,
            out RestorePlan plan,
            out string error)
        {
            plan = null;
            if (!TryValidateStructure(saveData, out error))
            {
                return false;
            }

            if (journal == null || !journal.IsConfigured || journal.Definition == null ||
                records == null || !records.IsConfigured)
            {
                error = "Player quest or record authority is unavailable for restore.";
                return false;
            }

            QuestProgressStatus status = QuestProgressStatus.Available;
            int enemyKills = 0;
            if (saveData.questRecordCount == 1)
            {
                QuestProgressSaveData record = saveData.quests[0];
                if (!string.Equals(
                        record.questId,
                        journal.Definition.QuestId,
                        StringComparison.Ordinal))
                {
                    error = $"Saved quest '{record.questId}' does not match the current quest definition.";
                    return false;
                }

                status = record.status;
                enemyKills = record.enemyKills;
            }

            if (!QuestProgressState.TryCreateRestored(
                    journal.Definition,
                    status,
                    enemyKills,
                    out QuestProgressState questCandidate,
                    out error))
            {
                return false;
            }

            plan = new RestorePlan(questCandidate, Clone(saveData));
            error = null;
            return true;
        }

        public static void ApplyPreparedRestore(
            QuestJournal journal,
            PlayerSessionRecords records,
            RestorePlan plan)
        {
            if (journal == null || records == null || plan == null)
            {
                throw new ArgumentNullException(nameof(plan));
            }

            // Replace both authorities silently first. Presentation notifications run
            // only after PlayerSessionRecords has re-based itself to the restored quest.
            journal.ApplyPreparedProgress(plan.QuestProgress, false);
            records.ApplyPreparedRecords(plan.Snapshot, false);
            journal.PublishCurrentState();
            records.PublishCurrentState();
        }

        public static bool TryCreateForRaidOutcome(
            PlayerProgressSaveData source,
            QuestDefinition questDefinition,
            RaidOutcome outcome,
            out PlayerProgressSaveData projected,
            out string error)
        {
            projected = null;
            if (!IsTerminalOutcome(outcome))
            {
                error = $"Player progress cannot apply non-terminal raid outcome {outcome}.";
                return false;
            }

            if (!TryValidateStructure(source, out error))
            {
                error = $"Player progress cannot apply raid outcome {outcome}: {error}";
                return false;
            }

            projected = Clone(source);
            if (!TryProjectQuest(projected, questDefinition, outcome, out error) ||
                !TryIncrementOutcomeRecord(projected, outcome, out error) ||
                !TryValidateStructure(projected, out error))
            {
                projected = null;
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryProjectQuest(
            PlayerProgressSaveData projected,
            QuestDefinition definition,
            RaidOutcome outcome,
            out string error)
        {
            if (projected.questRecordCount == 0)
            {
                if (definition == null)
                {
                    // Legacy v6 progress had no quest state. A recovery failure can
                    // preserve that explicit migration default without inventing an ID.
                    if (outcome != RaidOutcome.Extracted)
                    {
                        error = null;
                        return true;
                    }

                    error = "An extracted raid cannot project an authored quest without its definition.";
                    return false;
                }

                projected.quests.Add(new QuestProgressSaveData
                {
                    questId = definition.QuestId,
                    status = QuestProgressStatus.Available,
                    enemyKills = 0
                });
                projected.questRecordCount = 1;
                projected.allowAuthoredQuestInitialization = false;
            }

            QuestProgressSaveData record = projected.quests[0];
            if (definition == null)
            {
                if (outcome == RaidOutcome.Extracted &&
                    record.status == QuestProgressStatus.Active)
                {
                    error = "An active quest requires its definition to project extraction.";
                    return false;
                }

                if (record.status == QuestProgressStatus.Active)
                {
                    record.enemyKills = 0;
                }

                error = null;
                return true;
            }

            if (!string.Equals(record.questId, definition.QuestId, StringComparison.Ordinal))
            {
                error = $"Saved quest '{record.questId}' does not match the current quest definition.";
                return false;
            }

            if (!QuestProgressState.TryCreateRestored(
                    definition,
                    record.status,
                    record.enemyKills,
                    out QuestProgressState quest,
                    out error))
            {
                error = $"Saved quest cannot apply the committed raid outcome: {error}";
                return false;
            }

            quest.ApplyCommittedRaidOutcome(outcome);
            record.status = quest.Status;
            record.enemyKills = quest.EnemyKills;
            projected.allowAuthoredQuestInitialization = false;
            error = null;
            return true;
        }

        private static bool IsTerminalOutcome(RaidOutcome outcome)
        {
            return outcome == RaidOutcome.Extracted ||
                   outcome == RaidOutcome.PlayerDied ||
                   outcome == RaidOutcome.Abandoned ||
                   outcome == RaidOutcome.RecoveryFailed;
        }

        private static bool TryIncrementOutcomeRecord(
            PlayerProgressSaveData projected,
            RaidOutcome outcome,
            out string error)
        {
            int current = outcome switch
            {
                RaidOutcome.Extracted => projected.successfulExtractions,
                RaidOutcome.PlayerDied => projected.playerDeaths,
                RaidOutcome.Abandoned => projected.abandonments,
                RaidOutcome.RecoveryFailed => projected.recoveryFailures,
                _ => -1
            };
            if (current < 0)
            {
                error = "Player raid-outcome record cannot advance safely.";
                return false;
            }

            switch (outcome)
            {
                case RaidOutcome.Extracted:
                    if (projected.successfulExtractions < int.MaxValue)
                    {
                        projected.successfulExtractions++;
                    }
                    break;
                case RaidOutcome.PlayerDied:
                    if (projected.playerDeaths < int.MaxValue)
                    {
                        projected.playerDeaths++;
                    }
                    break;
                case RaidOutcome.Abandoned:
                    if (projected.abandonments < int.MaxValue)
                    {
                        projected.abandonments++;
                    }
                    break;
                case RaidOutcome.RecoveryFailed:
                    if (projected.recoveryFailures < int.MaxValue)
                    {
                        projected.recoveryFailures++;
                    }
                    break;
                default:
                    error = "Unknown raid outcome record.";
                    return false;
            }

            error = null;
            return true;
        }

        private static PlayerProgressSaveData Clone(PlayerProgressSaveData source)
        {
            var clone = new PlayerProgressSaveData
            {
                formatVersion = source.formatVersion,
                questRecordCount = source.questRecordCount,
                quests = new List<QuestProgressSaveData>(source.questRecordCount),
                allowAuthoredQuestInitialization = source.allowAuthoredQuestInitialization,
                enemyKills = source.enemyKills,
                successfulExtractions = source.successfulExtractions,
                playerDeaths = source.playerDeaths,
                abandonments = source.abandonments,
                recoveryFailures = source.recoveryFailures,
                completedQuests = source.completedQuests
            };

            foreach (QuestProgressSaveData quest in source.quests)
            {
                clone.quests.Add(new QuestProgressSaveData
                {
                    questId = quest.questId,
                    status = quest.status,
                    enemyKills = quest.enemyKills
                });
            }

            return clone;
        }
    }
}
