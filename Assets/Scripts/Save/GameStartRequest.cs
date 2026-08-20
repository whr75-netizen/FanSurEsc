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

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Clear();
        }

        public static void QueueNewGame()
        {
            pendingMode = GameStartMode.NewGame;
            pendingSave = null;
        }

        public static bool QueueLoad(GameSaveData saveData)
        {
            if (saveData == null)
            {
                return false;
            }

            pendingMode = GameStartMode.LoadGame;
            pendingSave = saveData;
            return true;
        }

        public static bool TryConsume(out GameStartMode mode, out GameSaveData saveData)
        {
            mode = pendingMode;
            saveData = pendingSave;

            bool hasRequest = mode != GameStartMode.None;
            Clear();
            return hasRequest;
        }

        private static void Clear()
        {
            pendingMode = GameStartMode.None;
            pendingSave = null;
        }
    }
}
