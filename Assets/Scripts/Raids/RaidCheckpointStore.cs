using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

namespace FantasySurvival.Raids
{
    /// <summary>
    /// File transport for the active raid recovery projection. Runtime gameplay state
    /// remains authoritative in its normal owners.
    /// </summary>
    public static class RaidCheckpointStore
    {
        private const int MaxRecoveryBytes = 8 * 1024 * 1024;
        private const string RecoveryFolderName = "Recovery";
        private const string BaselineFileName = "active_raid_baseline.json";
        private const string CheckpointFileName = "active_raid_checkpoint.json";
        private const string SettlementJournalFileName = "active_raid_settlement.json";

#if UNITY_EDITOR
        private static string editorStorageRootOverride;
#endif

        public static string RecoveryFolder => Path.Combine(StorageRoot, RecoveryFolderName);
        public static string BaselinePath => Path.Combine(RecoveryFolder, BaselineFileName);
        public static string ActiveCheckpointPath => Path.Combine(RecoveryFolder, CheckpointFileName);
        public static string ActiveCheckpointBackupPath => ActiveCheckpointPath + ".bak";
        public static string SettlementJournalPath =>
            Path.Combine(RecoveryFolder, SettlementJournalFileName);
        public static string SettlementJournalBackupPath => SettlementJournalPath + ".bak";

        private static string StorageRoot
        {
            get
            {
#if UNITY_EDITOR
                if (!string.IsNullOrWhiteSpace(editorStorageRootOverride))
                {
                    return editorStorageRootOverride;
                }
#endif
                return Application.persistentDataPath;
            }
        }

        public static bool HasRecoveryArtifacts =>
            File.Exists(BaselinePath) ||
            File.Exists(ActiveCheckpointPath) ||
             File.Exists(ActiveCheckpointBackupPath) ||
             File.Exists(SettlementJournalPath) ||
             File.Exists(SettlementJournalBackupPath) ||
             File.Exists(BaselinePath + ".tmp") ||
             File.Exists(ActiveCheckpointPath + ".tmp") ||
             File.Exists(SettlementJournalPath + ".tmp");

        public static bool HasSettlementJournalArtifacts =>
            File.Exists(SettlementJournalPath) ||
            File.Exists(SettlementJournalBackupPath) ||
            File.Exists(SettlementJournalPath + ".tmp");

        public static bool TryCreateBaseline(RaidRecoveryBaselineData baseline, out string error)
        {
            if (baseline == null)
            {
                error = "Raid recovery baseline is missing.";
                return false;
            }

            if (HasRecoveryArtifacts)
            {
                error = "An unsettled raid recovery already exists.";
                return false;
            }

            return TryWriteJson(baseline, BaselinePath, null, false, out error);
        }

        public static bool TryWriteCheckpoint(RaidCheckpointData checkpoint, out string error)
        {
            return TryWriteCheckpoint(checkpoint, null, out error);
        }

        /// <summary>
        /// Writes a checkpoint atomically. The current primary is rotated into the
        /// backup only when it is byte-for-byte equivalent after canonical JSON
        /// serialization to a checkpoint the caller already validated. Passing null
        /// preserves the existing backup.
        /// </summary>
        public static bool TryWriteCheckpoint(
            RaidCheckpointData checkpoint,
            RaidCheckpointData validatedCurrentPrimary,
            out string error)
        {
            if (checkpoint == null || string.IsNullOrWhiteSpace(checkpoint.raidInstanceId))
            {
                error = "Raid checkpoint is missing its raid instance ID.";
                return false;
            }

            bool rotatePrimary = validatedCurrentPrimary != null &&
                TryReadCheckpointFile(
                     ActiveCheckpointPath,
                     out RaidCheckpointData current,
                     out _) &&
                AreCanonicalJsonEquivalent(current, validatedCurrentPrimary);

            return TryWriteJson(
                checkpoint,
                ActiveCheckpointPath,
                ActiveCheckpointBackupPath,
                rotatePrimary,
                out error);
        }

        public static bool TryWriteSettlementJournal(
            RaidSettlementJournalData journal,
            out string error)
        {
            if (journal == null || string.IsNullOrWhiteSpace(journal.raidInstanceId))
            {
                error = "Raid settlement journal is missing its raid instance ID.";
                return false;
            }

            // First install the new record while preserving any existing backup. Then
            // write the same record again so File.Replace mirrors it into .bak. A crash
            // after either atomic install still leaves at least one complete new record.
            if (!TryWriteJson(
                    journal,
                    SettlementJournalPath,
                    SettlementJournalBackupPath,
                    false,
                    out error))
            {
                return false;
            }

            if (!TryWriteJson(
                    journal,
                    SettlementJournalPath,
                    SettlementJournalBackupPath,
                    true,
                    out string mirrorError))
            {
                Debug.LogWarning(
                    $"Raid settlement journal primary is durable, but its mirror could not be refreshed: {mirrorError}");
            }

            error = null;
            return true;
        }

        public static bool TryReadBaseline(
            out RaidRecoveryBaselineData baseline,
            out string error)
        {
            return TryReadJsonFile(BaselinePath, out baseline, out error);
        }

        public static void ReadCheckpointCandidates(
            out RaidCheckpointData primary,
            out string primaryError,
            out RaidCheckpointData backup,
            out string backupError)
        {
            TryReadCheckpointFile(ActiveCheckpointPath, out primary, out primaryError);
            TryReadCheckpointFile(ActiveCheckpointBackupPath, out backup, out backupError);
        }

        public static void ReadSettlementJournalCandidates(
            out RaidSettlementJournalData primary,
            out string primaryError,
            out RaidSettlementJournalData backup,
            out string backupError)
        {
            TryReadJsonFile(SettlementJournalPath, out primary, out primaryError);
            TryReadJsonFile(SettlementJournalBackupPath, out backup, out backupError);
        }

        public static bool TryDeleteActiveCheckpoints(out string error)
        {
            return TryDeleteFiles(
                new[]
                {
                    ActiveCheckpointPath,
                    ActiveCheckpointBackupPath,
                    ActiveCheckpointPath + ".tmp"
                },
                out error);
        }

        public static bool TryDeleteCheckpointBackup(out string error)
        {
            return TryDeleteFiles(new[] { ActiveCheckpointBackupPath }, out error);
        }

        public static bool TryDeleteAll(out string error)
        {
            return TryDeleteFiles(
                new[]
                {
                    BaselinePath,
                    BaselinePath + ".tmp",
                    ActiveCheckpointPath,
                    ActiveCheckpointBackupPath,
                    ActiveCheckpointPath + ".tmp",
                    SettlementJournalPath,
                    SettlementJournalBackupPath,
                    SettlementJournalPath + ".tmp"
                },
                out error);
        }

        public static bool TryQuarantineAll(out string quarantineFolder, out string error)
        {
            quarantineFolder = null;
            var existing = new List<string>();
            string[] paths =
            {
                BaselinePath,
                BaselinePath + ".tmp",
                ActiveCheckpointPath,
                ActiveCheckpointBackupPath,
                ActiveCheckpointPath + ".tmp",
                SettlementJournalPath,
                SettlementJournalBackupPath,
                SettlementJournalPath + ".tmp"
            };

            foreach (string path in paths)
            {
                if (File.Exists(path))
                {
                    existing.Add(path);
                }
            }

            if (existing.Count == 0)
            {
                error = null;
                return true;
            }

            try
            {
                string timestamp = DateTime.UtcNow.ToString(
                    "yyyyMMdd_HHmmss_fff",
                    CultureInfo.InvariantCulture);
                string corruptRoot = Path.Combine(RecoveryFolder, "Corrupt");
                quarantineFolder = Path.Combine(corruptRoot, timestamp);
                int suffix = 1;
                while (Directory.Exists(quarantineFolder))
                {
                    quarantineFolder = Path.Combine(corruptRoot, $"{timestamp}_{suffix}");
                    suffix++;
                }

                Directory.CreateDirectory(quarantineFolder);
                foreach (string source in existing)
                {
                    string destination = Path.Combine(
                        quarantineFolder,
                        Path.GetFileName(source));
                    File.Move(source, destination);
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Could not quarantine invalid raid recovery files: {exception.Message}";
                return false;
            }
        }

        public static string GetDisplayTimestamp(string savedAtUtc)
        {
            if (DateTime.TryParse(
                    savedAtUtc,
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.RoundtripKind,
                    out DateTime utc))
            {
                return utc.ToLocalTime().ToString(
                    "yyyy-MM-dd HH:mm:ss",
                    CultureInfo.CurrentCulture);
            }

            return "Unknown time";
        }

#if UNITY_EDITOR
        public static bool SetEditorStorageRootForTests(string root, out string error)
        {
            if (string.IsNullOrWhiteSpace(root) || !Path.IsPathRooted(root))
            {
                error = "Editor recovery test root must be an absolute path.";
                return false;
            }

            try
            {
                editorStorageRootOverride = Path.GetFullPath(root);
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Editor recovery test root is invalid: {exception.Message}";
                return false;
            }
        }

        public static void ClearEditorStorageRootForTests()
        {
            editorStorageRootOverride = null;
        }
#endif

        private static bool TryReadCheckpointFile(
            string path,
            out RaidCheckpointData checkpoint,
            out string error)
        {
            return TryReadJsonFile(path, out checkpoint, out error);
        }

        private static bool AreCanonicalJsonEquivalent(object left, object right)
        {
            if (left == null || right == null || left.GetType() != right.GetType())
            {
                return false;
            }

            try
            {
                return string.Equals(
                    JsonUtility.ToJson(left, false),
                    JsonUtility.ToJson(right, false),
                    StringComparison.Ordinal);
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static bool TryReadJsonFile<T>(
            string path,
            out T data,
            out string error)
            where T : class
        {
            data = null;
            if (!File.Exists(path))
            {
                error = "File does not exist.";
                return false;
            }

            try
            {
                var info = new FileInfo(path);
                if (info.Length <= 0 || info.Length > MaxRecoveryBytes)
                {
                    error = $"Recovery file size {info.Length} bytes is invalid.";
                    return false;
                }

                string json = File.ReadAllText(path, Encoding.UTF8);
                data = JsonUtility.FromJson<T>(json);
                if (data == null)
                {
                    error = "Recovery file is empty or malformed.";
                    return false;
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                data = null;
                error = $"Could not read raid recovery file: {exception.Message}";
                return false;
            }
        }

        private static bool TryWriteJson(
            object payload,
            string finalPath,
            string backupPath,
            bool rotatePrimary,
            out string error)
        {
            string json;
            try
            {
                json = JsonUtility.ToJson(payload, true);
            }
            catch (Exception exception)
            {
                error = $"Could not serialize raid recovery: {exception.Message}";
                return false;
            }

            int byteCount = Encoding.UTF8.GetByteCount(json);
            if (byteCount <= 0 || byteCount > MaxRecoveryBytes)
            {
                error = $"Raid recovery size {byteCount} bytes is invalid.";
                return false;
            }

            string directory = Path.GetDirectoryName(finalPath);
            string temporaryPath = finalPath + ".tmp";
            try
            {
                Directory.CreateDirectory(directory);
                using (var stream = new FileStream(
                           temporaryPath,
                           FileMode.Create,
                           FileAccess.Write,
                           FileShare.None))
                using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                {
                    writer.Write(json);
                    writer.Flush();
                    stream.Flush(true);
                }

                if (File.Exists(finalPath))
                {
                    File.Replace(
                        temporaryPath,
                        finalPath,
                        rotatePrimary ? backupPath : null,
                        true);
                }
                else
                {
                    File.Move(temporaryPath, finalPath);
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Could not write raid recovery: {exception.Message}";
                return false;
            }
            finally
            {
                try
                {
                    if (File.Exists(temporaryPath))
                    {
                        File.Delete(temporaryPath);
                    }
                }
                catch
                {
                    // The next atomic write can replace a stale temp file.
                }
            }
        }

        private static bool TryDeleteFiles(IEnumerable<string> paths, out string error)
        {
            try
            {
                foreach (string path in paths)
                {
                    if (File.Exists(path))
                    {
                        File.Delete(path);
                    }
                }

                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Could not remove settled raid recovery files: {exception.Message}";
                return false;
            }
        }
    }
}
