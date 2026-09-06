using System;
using System.IO;
using FantasySurvival.Controls;
using UnityEngine;
using UnityEngine.InputSystem;

namespace FantasySurvival.SaveSystem
{
    public static class GameUserSettings
    {
        private const string SettingsFolderName = "Settings";
        private const string SettingsFileName = "user_settings.json";

        // Read only when no settings file exists. These keys are removed only after
        // the separate settings file has been durably written.
        private const string LegacySoundEnabledKey = "settings.soundEnabled";
        private const string LegacyInputBindingOverridesKey = "settings.inputBindingOverrides";
        private const string LegacyInputBindingFormatVersionKey =
            "settings.inputBindingFormatVersion";

        private static UserSettingsData currentSettings;
        private static bool settingsLoaded;
        private static bool invalidInputSettingsWarningReported;
        private static bool settingsStorageWarningReported;

#if UNITY_EDITOR
        private static string editorStorageRootOverride;
        private static bool editorLegacyMigrationEnabled = true;
#endif

        public static event Action InputBindingsChanged;

        public static string SettingsFilePath => Path.Combine(
            StorageRoot,
            SettingsFolderName,
            SettingsFileName);

        public static bool SoundEnabled
        {
            get
            {
                EnsureSettingsLoaded();
                return currentSettings.soundEnabled;
            }
        }

        private static string SettingsBackupPath => SettingsFilePath + ".bak";

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

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetRuntimeState()
        {
            ResetLoadedSettingsState();
            InputBindingsChanged = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void ApplyBeforeFirstScene()
        {
            Apply();
        }

        public static void SetSoundEnabled(bool enabled)
        {
            if (!TrySetSoundEnabled(enabled, out string error))
            {
                Debug.LogError(error);
            }
        }

        public static bool TrySetSoundEnabled(bool enabled, out string error)
        {
            EnsureSettingsLoaded();
            UserSettingsData previousSettings = currentSettings.Clone();
            currentSettings.soundEnabled = enabled;
            if (!TryPersistCurrentSettings(out string persistenceError))
            {
                currentSettings = previousSettings;
                AudioListener.pause = !currentSettings.soundEnabled;
                error =
                    $"소리 설정을 저장하지 못해 이전 값으로 복원했습니다: {persistenceError}";
                return false;
            }

            AudioListener.pause = !currentSettings.soundEnabled;
            error = null;
            return true;
        }

        public static void Apply()
        {
            EnsureSettingsLoaded();
            AudioListener.pause = !currentSettings.soundEnabled;
            ApplyInputBindings();
        }

        public static bool ApplyInputBindings()
        {
            EnsureSettingsLoaded();
            InputActionMap map = GameInputBindings.GameplayMap;
            if (map == null)
            {
                Debug.LogError(
                    $"Project-wide Input Actions에 '{GameInputBindings.GameplayMapName}' 맵이 없습니다.");
                return false;
            }

            bool wasEnabled = map.enabled;
            if (wasEnabled)
            {
                map.Disable();
            }

            bool applied = true;
            try
            {
                map.RemoveAllBindingOverrides();
                string json = currentSettings.inputBindingOverrides;
                if (!currentSettings.hasInputBindingOverrides)
                {
                    return true;
                }

                if (currentSettings.inputBindingFormatVersion !=
                        UserSettingsData.CurrentInputBindingFormatVersion ||
                    string.IsNullOrWhiteSpace(json) ||
                    json.Length > UserSettingsData.MaximumInputBindingJsonLength)
                {
                    applied = false;
                    ReportInvalidInputSettingsOnce(
                        "저장된 키 설정의 버전 또는 크기가 유효하지 않아 기본값을 사용합니다.");
                    return false;
                }

                map.LoadBindingOverridesFromJson(json, false);
                if (!GameInputBindings.TryValidateCurrentBindings(out string validationError))
                {
                    map.RemoveAllBindingOverrides();
                    applied = false;
                    ReportInvalidInputSettingsOnce(
                        $"저장된 키 설정이 현재 입력 목록과 맞지 않아 기본값을 사용합니다: {validationError}");
                }
            }
            catch (Exception exception)
            {
                map.RemoveAllBindingOverrides();
                applied = false;
                ReportInvalidInputSettingsOnce(
                    $"저장된 키 설정을 읽지 못해 기본값을 사용합니다: {exception.Message}");
            }
            finally
            {
                if (wasEnabled)
                {
                    map.Enable();
                }
            }

            if (applied)
            {
                invalidInputSettingsWarningReported = false;
            }

            return applied;
        }

        public static bool TrySetInputBinding(
            GameInputActionId actionId,
            GameInputBindingSlot slot,
            string controlPath,
            out string error)
        {
            EnsureSettingsLoaded();
            if (!GameInputBindings.TryGetCanonicalRebindPath(
                    controlPath,
                    out string canonicalPath))
            {
                error = "키보드 또는 마우스 버튼만 지정할 수 있으며 Esc, 카메라 회전용 우클릭과 개발용 F5는 고정키입니다.";
                return false;
            }

            if (!GameInputBindings.TryResolveBinding(
                    actionId,
                    slot,
                    out InputAction action,
                    out int bindingIndex))
            {
                error = "변경할 입력 binding을 찾을 수 없습니다.";
                return false;
            }

            if (GameInputBindings.TryFindConflict(
                    actionId,
                    slot,
                    canonicalPath,
                    out GameInputBindingDefinition conflict))
            {
                error = $"이미 '{conflict.DisplayName}'에서 사용하는 키입니다.";
                return false;
            }

            InputBinding previousBinding = action.bindings[bindingIndex];
            return TryCommitInputBindingChange(
                action,
                () => action.ApplyBindingOverride(bindingIndex, canonicalPath),
                () => RestoreBindingOverride(action, bindingIndex, previousBinding),
                "키 설정을 적용하지 못했습니다",
                out error);
        }

        public static bool TryClearSecondaryInputBinding(
            GameInputActionId actionId,
            out string error)
        {
            EnsureSettingsLoaded();
            if (!GameInputBindings.TryResolveBinding(
                    actionId,
                    GameInputBindingSlot.Secondary,
                    out InputAction action,
                    out int bindingIndex))
            {
                error = "해제할 보조 키 binding을 찾을 수 없습니다.";
                return false;
            }

            InputBinding previousBinding = action.bindings[bindingIndex];
            return TryCommitInputBindingChange(
                action,
                () => action.ApplyBindingOverride(
                    bindingIndex,
                    new InputBinding { overridePath = string.Empty }),
                () => RestoreBindingOverride(action, bindingIndex, previousBinding),
                "보조 키를 해제하지 못했습니다",
                out error);
        }

        public static bool TryResetInputBindings(
            GameInputActionId actionId,
            out string error)
        {
            EnsureSettingsLoaded();
            if (!GameInputBindings.TryResolveBinding(
                    actionId,
                    GameInputBindingSlot.Primary,
                    out InputAction action,
                    out int primaryBindingIndex) ||
                !GameInputBindings.TryResolveBinding(
                    actionId,
                    GameInputBindingSlot.Secondary,
                    out InputAction secondaryAction,
                    out int secondaryBindingIndex) ||
                action != secondaryAction)
            {
                error = "기본값으로 복원할 입력 binding을 찾을 수 없습니다.";
                return false;
            }

            InputBinding previousPrimaryBinding = action.bindings[primaryBindingIndex];
            InputBinding previousSecondaryBinding = action.bindings[secondaryBindingIndex];
            return TryCommitInputBindingChange(
                action,
                () =>
                {
                    action.RemoveBindingOverride(primaryBindingIndex);
                    action.RemoveBindingOverride(secondaryBindingIndex);
                },
                () =>
                {
                    RestoreBindingOverride(
                        action,
                        primaryBindingIndex,
                        previousPrimaryBinding);
                    RestoreBindingOverride(
                        action,
                        secondaryBindingIndex,
                        previousSecondaryBinding);
                },
                "해당 키 설정을 기본값으로 복원하지 못했습니다",
                out error);
        }

        public static bool TryResetInputBindings(out string error)
        {
            EnsureSettingsLoaded();
            InputActionMap map = GameInputBindings.GameplayMap;
            if (map == null)
            {
                error = "기본값으로 복원할 Gameplay Input Action Map이 없습니다.";
                return false;
            }

            string previousOverrides = map.SaveBindingOverridesAsJson();
            UserSettingsData previousSettings = currentSettings.Clone();

            bool wasEnabled = map.enabled;
            if (wasEnabled)
            {
                map.Disable();
            }

            try
            {
                map.RemoveAllBindingOverrides();
                currentSettings.hasInputBindingOverrides = false;
                currentSettings.inputBindingFormatVersion =
                    UserSettingsData.CurrentInputBindingFormatVersion;
                currentSettings.inputBindingOverrides = string.Empty;
                if (!TryPersistCurrentSettings(out error))
                {
                    currentSettings = previousSettings;
                    RestoreMapOverrides(map, previousOverrides);
                    return false;
                }
            }
            catch (Exception exception)
            {
                currentSettings = previousSettings;
                RestoreMapOverrides(map, previousOverrides);
                error = $"기본 키 설정을 저장하지 못했습니다: {exception.Message}";
                return false;
            }
            finally
            {
                if (wasEnabled)
                {
                    map.Enable();
                }
            }

            invalidInputSettingsWarningReported = false;
            InputBindingsChanged?.Invoke();
            error = null;
            return true;
        }

        private static bool TrySaveInputBindingOverrides(out string error)
        {
            InputActionMap map = GameInputBindings.GameplayMap;
            if (map == null)
            {
                error = "Gameplay Input Action Map이 없습니다.";
                return false;
            }

            string json = map.SaveBindingOverridesAsJson();
            if (json.Length > UserSettingsData.MaximumInputBindingJsonLength)
            {
                error = "키 설정 데이터가 허용 크기를 초과했습니다.";
                return false;
            }

            UserSettingsData previousSettings = currentSettings.Clone();
            currentSettings.hasInputBindingOverrides = !string.IsNullOrWhiteSpace(json);
            currentSettings.inputBindingFormatVersion =
                UserSettingsData.CurrentInputBindingFormatVersion;
            currentSettings.inputBindingOverrides =
                currentSettings.hasInputBindingOverrides ? json : string.Empty;
            if (TryPersistCurrentSettings(out error))
            {
                return true;
            }

            currentSettings = previousSettings;
            error = $"키 설정을 저장하지 못했습니다: {error}";
            return false;
        }

        private static bool TryCommitInputBindingChange(
            InputAction action,
            Action applyChange,
            Action rollBackChange,
            string exceptionPrefix,
            out string error)
        {
            bool wasEnabled = action.enabled;
            if (wasEnabled)
            {
                action.Disable();
            }

            try
            {
                applyChange();
                if (!GameInputBindings.TryValidateCurrentBindings(out error))
                {
                    rollBackChange();
                    return false;
                }

                if (!TrySaveInputBindingOverrides(out error))
                {
                    rollBackChange();
                    return false;
                }
            }
            catch (Exception exception)
            {
                rollBackChange();
                error = $"{exceptionPrefix}: {exception.Message}";
                return false;
            }
            finally
            {
                if (wasEnabled)
                {
                    action.Enable();
                }
            }

            invalidInputSettingsWarningReported = false;
            InputBindingsChanged?.Invoke();
            error = null;
            return true;
        }

        private static void EnsureSettingsLoaded()
        {
            if (settingsLoaded)
            {
                return;
            }

            try
            {
                currentSettings = LoadSettings() ?? UserSettingsData.CreateDefault();
            }
            catch (Exception exception)
            {
                currentSettings = UserSettingsData.CreateDefault();
                Debug.LogError(
                    $"사용자 설정 초기화 중 예상하지 못한 오류가 발생해 런타임 기본값을 사용합니다. " +
                    $"설정 파일은 자동으로 덮어쓰지 않습니다: {exception.Message}");
            }

            settingsLoaded = true;
        }

        private static UserSettingsData LoadSettings()
        {
            string primaryPath = SettingsFilePath;
            string backupPath = SettingsBackupPath;
            bool primaryExists = File.Exists(primaryPath);
            bool backupExists = File.Exists(backupPath);

            if (UserSettingsFileStore.TryRead(
                    primaryPath,
                    out UserSettingsData primary,
                    out string primaryError))
            {
                return primary;
            }

            if (UserSettingsFileStore.TryRead(
                    backupPath,
                    out UserSettingsData backup,
                    out string backupError))
            {
                string preservationMessage = string.Empty;
                bool primaryReadyForRestore = true;
                if (primaryExists)
                {
                    if (UserSettingsFileStore.TryQuarantine(
                            primaryPath,
                            out string preservedPath,
                            out string quarantineError))
                    {
                        preservationMessage = $" 손상 원본 보존: {preservedPath}.";
                    }
                    else
                    {
                        primaryReadyForRestore = false;
                        preservationMessage = $" 손상 원본 보존 실패: {quarantineError}.";
                    }
                }

                string restoreMessage = string.Empty;
                if (primaryReadyForRestore &&
                    !UserSettingsFileStore.TryWrite(primaryPath, backup, out string restoreError))
                {
                    restoreMessage = $" 기본 파일 복구 실패: {restoreError}.";
                }

                ReportSettingsStorageWarningOnce(
                    $"사용자 설정 기본 파일을 읽지 못해 유효한 백업을 사용합니다. " +
                    $"기본 파일 오류: {primaryError}.{preservationMessage}{restoreMessage}");
                return backup;
            }

            UserSettingsData settings = CaptureLegacySettings(out bool hasLegacySettings);
            string primaryPreservation = PreserveInvalidCandidate(
                primaryExists,
                primaryPath,
                primaryError);
            string backupPreservation = PreserveInvalidCandidate(
                backupExists,
                backupPath,
                backupError);

            if (UserSettingsFileStore.TryWrite(primaryPath, settings, out string writeError))
            {
                if (hasLegacySettings)
                {
                    TryClearLegacyPreferences();
                }
            }
            else
            {
                Debug.LogError(
                    $"사용자 설정 파일을 만들지 못했습니다. 런타임에서는 복원된 값 또는 기본값을 " +
                    $"사용하며 기존 PlayerPrefs는 보존합니다: {writeError}");
            }

            if (primaryExists || backupExists)
            {
                ReportSettingsStorageWarningOnce(
                    $"유효한 사용자 설정 파일이 없어 복원된 값 또는 기본값을 사용합니다. " +
                    $"기본 파일 오류: {primaryError}. 백업 오류: {backupError}." +
                    $"{primaryPreservation}{backupPreservation}");
            }

            return settings;
        }

        private static UserSettingsData CaptureLegacySettings(out bool hasLegacySettings)
        {
#if UNITY_EDITOR
            if (!string.IsNullOrWhiteSpace(editorStorageRootOverride) &&
                !editorLegacyMigrationEnabled)
            {
                hasLegacySettings = false;
                return UserSettingsData.CreateDefault();
            }
#endif
            bool hasSound = PlayerPrefs.HasKey(LegacySoundEnabledKey);
            bool hasOverrides = PlayerPrefs.HasKey(LegacyInputBindingOverridesKey);
            bool hasBindingVersion = PlayerPrefs.HasKey(LegacyInputBindingFormatVersionKey);
            hasLegacySettings = hasSound || hasOverrides || hasBindingVersion;

            UserSettingsData settings = UserSettingsData.CreateDefault();
            if (hasSound)
            {
                settings.soundEnabled = PlayerPrefs.GetInt(LegacySoundEnabledKey, 1) != 0;
            }

            if (hasOverrides)
            {
                settings.hasInputBindingOverrides = true;
                settings.inputBindingOverrides = PlayerPrefs.GetString(
                    LegacyInputBindingOverridesKey,
                    string.Empty);
                settings.inputBindingFormatVersion = PlayerPrefs.GetInt(
                    LegacyInputBindingFormatVersionKey,
                    0);
            }
            else if (hasBindingVersion)
            {
                settings.inputBindingFormatVersion = PlayerPrefs.GetInt(
                    LegacyInputBindingFormatVersionKey,
                    0);
            }

            return settings;
        }

        private static bool TryPersistCurrentSettings(out string error)
        {
            if (!UserSettingsFileStore.TryWrite(SettingsFilePath, currentSettings, out error))
            {
                return false;
            }

            TryClearLegacyPreferences();
            return true;
        }

        private static void TryClearLegacyPreferences()
        {
#if UNITY_EDITOR
            if (!string.IsNullOrWhiteSpace(editorStorageRootOverride) &&
                !editorLegacyMigrationEnabled)
            {
                return;
            }
#endif
            if (!PlayerPrefs.HasKey(LegacySoundEnabledKey) &&
                !PlayerPrefs.HasKey(LegacyInputBindingOverridesKey) &&
                !PlayerPrefs.HasKey(LegacyInputBindingFormatVersionKey))
            {
                return;
            }

            try
            {
                PlayerPrefs.DeleteKey(LegacySoundEnabledKey);
                PlayerPrefs.DeleteKey(LegacyInputBindingOverridesKey);
                PlayerPrefs.DeleteKey(LegacyInputBindingFormatVersionKey);
                PlayerPrefs.Save();
            }
            catch (Exception exception)
            {
                Debug.LogWarning(
                    $"사용자 설정 파일 저장은 완료됐지만 이전 PlayerPrefs 설정 정리는 실패했습니다. " +
                    $"새 설정 파일이 계속 우선됩니다: {exception.Message}");
            }
        }

        private static string PreserveInvalidCandidate(
            bool exists,
            string path,
            string readError)
        {
            if (!exists)
            {
                return string.Empty;
            }

            if (UserSettingsFileStore.TryQuarantine(
                    path,
                    out string preservedPath,
                    out string quarantineError))
            {
                return $" 손상 파일 보존: {preservedPath} ({readError}).";
            }

            return $" 손상 파일 보존 실패: {quarantineError} ({readError}).";
        }

        private static void RestoreMapOverrides(InputActionMap map, string json)
        {
            map.RemoveAllBindingOverrides();
            if (!string.IsNullOrWhiteSpace(json))
            {
                map.LoadBindingOverridesFromJson(json, false);
            }
        }

        private static void RestoreBindingOverride(
            InputAction action,
            int bindingIndex,
            InputBinding previousBinding)
        {
            if (previousBinding.overridePath == null &&
                previousBinding.overrideInteractions == null &&
                previousBinding.overrideProcessors == null)
            {
                action.RemoveBindingOverride(bindingIndex);
                return;
            }

            action.ApplyBindingOverride(
                bindingIndex,
                new InputBinding
                {
                    overridePath = previousBinding.overridePath,
                    overrideInteractions = previousBinding.overrideInteractions,
                    overrideProcessors = previousBinding.overrideProcessors
                });
        }

        private static void ResetLoadedSettingsState()
        {
            currentSettings = null;
            settingsLoaded = false;
            invalidInputSettingsWarningReported = false;
            settingsStorageWarningReported = false;
        }

        private static void ReportInvalidInputSettingsOnce(string message)
        {
            if (invalidInputSettingsWarningReported)
            {
                return;
            }

            invalidInputSettingsWarningReported = true;
            Debug.LogWarning(message);
        }

        private static void ReportSettingsStorageWarningOnce(string message)
        {
            if (settingsStorageWarningReported)
            {
                return;
            }

            settingsStorageWarningReported = true;
            Debug.LogWarning(message);
        }

#if UNITY_EDITOR
        public static bool SetEditorStorageRootForTests(string root, out string error)
        {
            return SetEditorStorageRootForTests(root, true, out error);
        }

        public static bool SetEditorStorageRootForTests(
            string root,
            bool allowLegacyMigration,
            out string error)
        {
            if (string.IsNullOrWhiteSpace(root))
            {
                error = "Editor settings-test storage root is empty.";
                return false;
            }

            try
            {
                editorStorageRootOverride = Path.GetFullPath(root);
                editorLegacyMigrationEnabled = allowLegacyMigration;
                ResetLoadedSettingsState();
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = $"Editor settings-test storage root is invalid: {exception.Message}";
                return false;
            }
        }

        public static void ReloadFromDiskForTests()
        {
            ResetLoadedSettingsState();
        }

        public static void ClearEditorStorageRootForTests()
        {
            editorStorageRootOverride = null;
            editorLegacyMigrationEnabled = true;
            ResetLoadedSettingsState();
        }
#endif
    }
}
