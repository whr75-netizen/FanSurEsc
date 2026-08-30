#if UNITY_EDITOR
using System;
using System.IO;
using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    /// <summary>
    /// Redirects direct gameplay-scene Play sessions to disposable storage.
    /// Main Menu starts keep using the normal persistent-data path.
    /// </summary>
    internal static class EditorDirectPlayStorageIsolation
    {
        private const string StorageFolderName = "FantasySurvivalDirectPlay";

        private static string activeStorageRoot;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetForPlaySession()
        {
            activeStorageRoot = null;
            GameSaveManager.ClearEditorStorageRootForTests();
            RaidCheckpointStore.ClearEditorStorageRootForTests();
        }

        internal static bool TryActivate(out string error)
        {
            if (!string.IsNullOrWhiteSpace(activeStorageRoot))
            {
                error = null;
                return true;
            }

            try
            {
                string storageRoot = Path.GetFullPath(Path.Combine(
                    Application.temporaryCachePath,
                    StorageFolderName,
                    Guid.NewGuid().ToString("N")));
                Directory.CreateDirectory(storageRoot);

                if (!GameSaveManager.SetEditorStorageRootForTests(
                        storageRoot,
                        out string saveError))
                {
                    error = $"ordinary save isolation failed: {saveError}";
                    return false;
                }

                if (!RaidCheckpointStore.SetEditorStorageRootForTests(
                        storageRoot,
                        out string recoveryError))
                {
                    GameSaveManager.ClearEditorStorageRootForTests();
                    error = $"raid recovery isolation failed: {recoveryError}";
                    return false;
                }

                activeStorageRoot = storageRoot;
                Debug.Log(
                    $"[Editor Test] Direct gameplay Play uses isolated temporary " +
                    $"save/recovery storage: {activeStorageRoot}");
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                GameSaveManager.ClearEditorStorageRootForTests();
                RaidCheckpointStore.ClearEditorStorageRootForTests();
                activeStorageRoot = null;
                error = exception.Message;
                return false;
            }
        }
    }
}
#endif
