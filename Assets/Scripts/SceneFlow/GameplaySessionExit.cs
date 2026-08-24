using System;
using FantasySurvival.SaveSystem;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.SceneFlow
{
    /// <summary>
    /// Ends one gameplay Play Session and removes its persistent owners before the
    /// Main Menu receives input. This is intentionally separate from direct travel
    /// between gameplay scenes.
    /// </summary>
    public static class GameplaySessionExit
    {
        private const string MainMenuSceneName = "MainMenuScene";

        private static bool isExiting;
        private static Action failureCallback;

        public static bool IsExiting => isExiting;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetState()
        {
            isExiting = false;
            failureCallback = null;
        }

        public static bool TryExitToMainMenu(Action onFailure = null)
        {
            if (isExiting || DirectSceneTravel.IsLoading)
            {
                return false;
            }

            if (!Application.CanStreamedLevelBeLoaded(MainMenuSceneName))
            {
                Debug.LogError($"Scene '{MainMenuSceneName}' is not available in Build Settings.");
                InvokeFailure(onFailure);
                return false;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell == null || !shell.PrepareForTravel())
            {
                InvokeFailure(onFailure);
                return false;
            }

            isExiting = true;
            failureCallback = onFailure;
            if (!shell.BeginTravelTransition(BeginMainMenuLoad, HandleTransitionInterrupted))
            {
                isExiting = false;
                failureCallback = null;
                shell.CancelTravelPreparation(() => InvokeFailure(onFailure));
                return false;
            }

            return true;
        }

        private static void BeginMainMenuLoad()
        {
            try
            {
                AsyncOperation operation = SceneManager.LoadSceneAsync(
                    MainMenuSceneName,
                    LoadSceneMode.Single);
                if (operation == null)
                {
                    FailExit("Could not start loading MainMenuScene.");
                    return;
                }

                operation.completed += _ => CompleteExit();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                FailExit("Main Menu loading threw an exception.");
            }
        }

        private static void CompleteExit()
        {
            if (!isExiting)
            {
                return;
            }

            isExiting = false;
            failureCallback = null;
            Time.timeScale = 1f;

            GameManager.Instance?.EndGameplaySession();
            PersistentGameplayShell.Instance?.EndGameplaySession();
            GameUserSettings.Apply();
        }

        private static void HandleTransitionInterrupted()
        {
            if (isExiting)
            {
                FailExit("Gameplay session exit was interrupted before Main Menu loaded.");
            }
        }

        private static void FailExit(string reason)
        {
            if (!isExiting)
            {
                return;
            }

            Debug.LogError(reason);
            isExiting = false;
            Action callback = failureCallback;
            failureCallback = null;
            Time.timeScale = 1f;

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell != null)
            {
                shell.CancelTravelPreparation(callback);
            }
            else
            {
                callback?.Invoke();
            }
        }

        private static void InvokeFailure(Action callback)
        {
            if (callback == null)
            {
                return;
            }

            try
            {
                callback.Invoke();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
            }
        }
    }
}
