using System;
using FantasySurvival.Controls;
using UnityEngine;
using UnityEngine.InputSystem;

namespace FantasySurvival.SaveSystem
{
    public static class GameUserSettings
    {
        private const string SoundEnabledKey = "settings.soundEnabled";
        private const string InputBindingOverridesKey = "settings.inputBindingOverrides";
        private const string InputBindingFormatVersionKey = "settings.inputBindingFormatVersion";
        private const int CurrentInputBindingFormatVersion = 1;
        private const int MaximumInputBindingJsonLength = 65536;

        private readonly struct StoredInputBindings
        {
            public StoredInputBindings(
                bool hasOverrides,
                string overrides,
                bool hasVersion,
                int version)
            {
                HasOverrides = hasOverrides;
                Overrides = overrides;
                HasVersion = hasVersion;
                Version = version;
            }

            public bool HasOverrides { get; }
            public string Overrides { get; }
            public bool HasVersion { get; }
            public int Version { get; }
        }

        private static bool invalidInputSettingsWarningReported;

        public static event Action InputBindingsChanged;

        public static bool SoundEnabled => PlayerPrefs.GetInt(SoundEnabledKey, 1) != 0;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetRuntimeState()
        {
            invalidInputSettingsWarningReported = false;
            InputBindingsChanged = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void ApplyBeforeFirstScene()
        {
            Apply();
        }

        public static void SetSoundEnabled(bool enabled)
        {
            PlayerPrefs.SetInt(SoundEnabledKey, enabled ? 1 : 0);
            PlayerPrefs.Save();
            Apply();
        }

        public static void Apply()
        {
            AudioListener.pause = !SoundEnabled;
            ApplyInputBindings();
        }

        public static bool ApplyInputBindings()
        {
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
                if (!PlayerPrefs.HasKey(InputBindingOverridesKey))
                {
                    return true;
                }

                int version = PlayerPrefs.GetInt(InputBindingFormatVersionKey, 0);
                string json = PlayerPrefs.GetString(InputBindingOverridesKey, string.Empty);
                if (version != CurrentInputBindingFormatVersion ||
                    string.IsNullOrWhiteSpace(json) ||
                    json.Length > MaximumInputBindingJsonLength)
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
            if (!GameInputBindings.TryGetCanonicalRebindPath(
                    controlPath,
                    out string canonicalPath))
            {
                error = "키보드 또는 마우스 버튼만 지정할 수 있으며 Esc와 개발용 F5는 고정키입니다.";
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
            bool wasEnabled = action.enabled;
            if (wasEnabled)
            {
                action.Disable();
            }

            try
            {
                action.ApplyBindingOverride(bindingIndex, canonicalPath);
                if (!GameInputBindings.TryValidateCurrentBindings(out error))
                {
                    RestoreBindingOverride(action, bindingIndex, previousBinding);
                    return false;
                }

                if (!TrySaveInputBindingOverrides(out error))
                {
                    RestoreBindingOverride(action, bindingIndex, previousBinding);
                    return false;
                }
            }
            catch (Exception exception)
            {
                RestoreBindingOverride(action, bindingIndex, previousBinding);
                error = $"키 설정을 적용하지 못했습니다: {exception.Message}";
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

        public static bool TryResetInputBindings(out string error)
        {
            InputActionMap map = GameInputBindings.GameplayMap;
            if (map == null)
            {
                error = "기본값으로 복원할 Gameplay Input Action Map이 없습니다.";
                return false;
            }

            string previousOverrides = map.SaveBindingOverridesAsJson();
            StoredInputBindings previousStoredBindings = CaptureStoredInputBindings();

            bool wasEnabled = map.enabled;
            if (wasEnabled)
            {
                map.Disable();
            }

            try
            {
                map.RemoveAllBindingOverrides();
                PlayerPrefs.DeleteKey(InputBindingOverridesKey);
                PlayerPrefs.DeleteKey(InputBindingFormatVersionKey);
                PlayerPrefs.Save();
            }
            catch (Exception exception)
            {
                RestoreMapOverrides(map, previousOverrides);
                RestoreStoredInputBindings(previousStoredBindings);
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
            StoredInputBindings previousStoredBindings = CaptureStoredInputBindings();
            try
            {
                InputActionMap map = GameInputBindings.GameplayMap;
                if (map == null)
                {
                    error = "Gameplay Input Action Map이 없습니다.";
                    return false;
                }

                string json = map.SaveBindingOverridesAsJson();
                if (json.Length > MaximumInputBindingJsonLength)
                {
                    error = "키 설정 데이터가 허용 크기를 초과했습니다.";
                    return false;
                }

                PlayerPrefs.SetInt(
                    InputBindingFormatVersionKey,
                    CurrentInputBindingFormatVersion);
                PlayerPrefs.SetString(InputBindingOverridesKey, json);
                PlayerPrefs.Save();
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                RestoreStoredInputBindings(previousStoredBindings);
                error = $"키 설정을 저장하지 못했습니다: {exception.Message}";
                return false;
            }
        }

        private static StoredInputBindings CaptureStoredInputBindings()
        {
            bool hasOverrides = PlayerPrefs.HasKey(InputBindingOverridesKey);
            bool hasVersion = PlayerPrefs.HasKey(InputBindingFormatVersionKey);
            return new StoredInputBindings(
                hasOverrides,
                hasOverrides
                    ? PlayerPrefs.GetString(InputBindingOverridesKey, string.Empty)
                    : string.Empty,
                hasVersion,
                hasVersion
                    ? PlayerPrefs.GetInt(InputBindingFormatVersionKey, 0)
                    : 0);
        }

        private static void RestoreStoredInputBindings(StoredInputBindings snapshot)
        {
            if (snapshot.HasOverrides)
            {
                PlayerPrefs.SetString(InputBindingOverridesKey, snapshot.Overrides);
            }
            else
            {
                PlayerPrefs.DeleteKey(InputBindingOverridesKey);
            }

            if (snapshot.HasVersion)
            {
                PlayerPrefs.SetInt(InputBindingFormatVersionKey, snapshot.Version);
            }
            else
            {
                PlayerPrefs.DeleteKey(InputBindingFormatVersionKey);
            }

            try
            {
                PlayerPrefs.Save();
            }
            catch (Exception)
            {
                // The caller already reports the original persistence failure.
            }
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
            if (string.IsNullOrEmpty(previousBinding.overridePath) &&
                string.IsNullOrEmpty(previousBinding.overrideInteractions) &&
                string.IsNullOrEmpty(previousBinding.overrideProcessors))
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

        private static void ReportInvalidInputSettingsOnce(string message)
        {
            if (invalidInputSettingsWarningReported)
            {
                return;
            }

            invalidInputSettingsWarningReported = true;
            Debug.LogWarning(message);
        }
    }
}
