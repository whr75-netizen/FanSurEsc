using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    public enum GameStartMode
    {
        None,
        NewGame,
        LoadGame
    }

    public static class GameStartRequest
    {
        private static GameStartMode pendingMode;
        private static GameSaveData pendingSave;
        private static GameSaveData pendingFallbackSave;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Clear();
        }

        public static void QueueNewGame()
        {
            pendingMode = GameStartMode.NewGame;
            pendingSave = null;
            pendingFallbackSave = null;
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

            pendingMode = GameStartMode.LoadGame;
            pendingSave = saveData;
            pendingFallbackSave = object.ReferenceEquals(saveData, fallbackSave) ? null : fallbackSave;
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
            mode = pendingMode;
            saveData = pendingSave;
            fallbackSave = pendingFallbackSave;

            bool hasRequest = mode != GameStartMode.None;
            Clear();
            return hasRequest;
        }

        private static void Clear()
        {
            pendingMode = GameStartMode.None;
            pendingSave = null;
            pendingFallbackSave = null;
        }
    }
}
