using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    public static class GameUserSettings
    {
        private const string SoundEnabledKey = "settings.soundEnabled";

        public static bool SoundEnabled => PlayerPrefs.GetInt(SoundEnabledKey, 1) != 0;

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
        }
    }
}
