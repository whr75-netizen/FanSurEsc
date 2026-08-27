using System;
using System.IO;
using System.Text;
using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    [Serializable]
    internal sealed class UserSettingsData
    {
        public const string CurrentGameId = "fantasy-survival-escape-settings";
        public const int CurrentFormatVersion = 1;
        public const int CurrentInputBindingFormatVersion = 1;
        public const int MaximumInputBindingJsonLength = 65536;

        public string gameId;
        public int formatVersion;
        public bool soundEnabled;
        public bool hasInputBindingOverrides;
        public int inputBindingFormatVersion;
        public string inputBindingOverrides;

        public static UserSettingsData CreateDefault()
        {
            return new UserSettingsData
            {
                gameId = CurrentGameId,
                formatVersion = CurrentFormatVersion,
                soundEnabled = true,
                hasInputBindingOverrides = false,
                inputBindingFormatVersion = CurrentInputBindingFormatVersion,
                inputBindingOverrides = string.Empty
            };
        }

        public UserSettingsData Clone()
        {
            return new UserSettingsData
            {
                gameId = gameId,
                formatVersion = formatVersion,
                soundEnabled = soundEnabled,
                hasInputBindingOverrides = hasInputBindingOverrides,
                inputBindingFormatVersion = inputBindingFormatVersion,
                inputBindingOverrides = inputBindingOverrides
            };
        }
    }

    [Serializable]
    internal sealed class UserSettingsFileHeader
    {
        public string gameId;
        public int formatVersion;
    }

    internal static class UserSettingsFileStore
    {
        private const int MaximumFileBytes = 256 * 1024;

        public static bool TryRead(
            string path,
            out UserSettingsData settings,
            out string error)
        {
            settings = null;
            if (!File.Exists(path))
            {
                error = "File does not exist.";
                return false;
            }

            try
            {
                var fileInfo = new FileInfo(path);
                if (fileInfo.Length <= 0 || fileInfo.Length > MaximumFileBytes)
                {
                    error = $"Settings file size {fileInfo.Length} bytes is invalid.";
                    return false;
                }

                string json = File.ReadAllText(path, new UTF8Encoding(false, true));
                UserSettingsFileHeader header =
                    JsonUtility.FromJson<UserSettingsFileHeader>(json);
                if (header == null || header.gameId != UserSettingsData.CurrentGameId)
                {
                    error = "Settings file belongs to a different game or is missing its game ID.";
                    return false;
                }

                if (header.formatVersion != UserSettingsData.CurrentFormatVersion)
                {
                    error = $"Unsupported settings version {header.formatVersion}.";
                    return false;
                }

                settings = UserSettingsData.CreateDefault();
                JsonUtility.FromJsonOverwrite(json, settings);
                if (!TryValidate(settings, out error))
                {
                    settings = null;
                    return false;
                }

                return true;
            }
            catch (Exception exception)
            {
                settings = null;
                error = $"Could not read user settings: {exception.Message}";
                return false;
            }
        }

        public static bool TryWrite(
            string finalPath,
            UserSettingsData settings,
            out string error)
        {
            if (!TryValidate(settings, out error))
            {
                return false;
            }

            string json;
            try
            {
                json = JsonUtility.ToJson(settings, true);
            }
            catch (Exception exception)
            {
                error = $"Could not serialize user settings: {exception.Message}";
                return false;
            }

            int byteCount = Encoding.UTF8.GetByteCount(json);
            if (byteCount <= 0 || byteCount > MaximumFileBytes)
            {
                error = $"Settings data size {byteCount} bytes is invalid.";
                return false;
            }

            string directory = Path.GetDirectoryName(finalPath);
            if (string.IsNullOrWhiteSpace(directory))
            {
                error = "User-settings directory is invalid.";
                return false;
            }

            string temporaryPath = finalPath + ".tmp";
            string backupPath = finalPath + ".bak";
            try
            {
                Directory.CreateDirectory(directory);

                bool rotatePrimaryToBackup = false;
                if (File.Exists(finalPath))
                {
                    if (TryRead(finalPath, out _, out _))
                    {
                        rotatePrimaryToBackup = true;
                    }
                    else if (!TryQuarantine(finalPath, out _, out string quarantineError))
                    {
                        error =
                            $"Invalid existing settings could not be preserved: {quarantineError}";
                        return false;
                    }
                }

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
                        rotatePrimaryToBackup ? backupPath : null,
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
                error = $"Could not write user settings: {exception.Message}";
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
                    // The next settings write replaces a stale temp file.
                }
            }
        }

        public static bool TryQuarantine(
            string path,
            out string preservedPath,
            out string error)
        {
            preservedPath = null;
            if (!File.Exists(path))
            {
                error = null;
                return true;
            }

            try
            {
                string directory = Path.GetDirectoryName(path);
                string fileName = Path.GetFileName(path);
                string suffix = DateTime.UtcNow.ToString("yyyyMMddTHHmmssfff") +
                                "-" + Guid.NewGuid().ToString("N");
                preservedPath = Path.Combine(
                    directory ?? string.Empty,
                    $"{fileName}.corrupt-{suffix}");
                File.Move(path, preservedPath);
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                preservedPath = null;
                error = $"Could not preserve invalid settings file: {exception.Message}";
                return false;
            }
        }

        private static bool TryValidate(UserSettingsData settings, out string error)
        {
            if (settings == null)
            {
                error = "User settings are empty.";
                return false;
            }

            if (settings.gameId != UserSettingsData.CurrentGameId)
            {
                error = "User settings have an invalid game ID.";
                return false;
            }

            if (settings.formatVersion != UserSettingsData.CurrentFormatVersion)
            {
                error = $"Unsupported settings version {settings.formatVersion}.";
                return false;
            }

            // The outer file remains valid even when the nested Input System payload is
            // obsolete, missing, or malformed. GameUserSettings rejects it at apply time while
            // preserving the on-disk value for diagnosis or an explicit user reset.
            error = null;
            return true;
        }
    }
}
