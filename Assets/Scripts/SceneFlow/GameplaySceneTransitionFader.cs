using System;
using System.Collections;
using UnityEngine;

namespace FantasySurvival.SceneFlow
{
    [DisallowMultipleComponent]
    public sealed class GameplaySceneTransitionFader : MonoBehaviour
    {
        [SerializeField] private Canvas transitionCanvas;
        [SerializeField] private CanvasGroup canvasGroup;
        [SerializeField, Min(0f)] private float fadeOutSeconds = 0.2f;
        [SerializeField, Min(0f)] private float fadeInSeconds = 0.25f;

        private Coroutine activeFade;
        private bool isTransitionActive;
        private Action interruptionCallback;

        public bool IsConfigured => transitionCanvas != null && canvasGroup != null;
        public bool IsTransitionActive => isTransitionActive;
        public bool IsCovered => IsConfigured && transitionCanvas.enabled &&
                                 canvasGroup.alpha >= 0.999f;

        private void Awake()
        {
            SetIdleVisualState();
        }

        public bool TryCover(Action onCovered, Action onInterrupted)
        {
            if (!IsConfigured || !isActiveAndEnabled || isTransitionActive)
            {
                return false;
            }

            isTransitionActive = true;
            interruptionCallback = onInterrupted;
            transitionCanvas.enabled = true;
            canvasGroup.blocksRaycasts = true;
            canvasGroup.interactable = false;
            activeFade = StartCoroutine(FadeTo(
                1f,
                fadeOutSeconds,
                () =>
                {
                    activeFade = null;
                    onCovered?.Invoke();
                }));
            return true;
        }

        public void Reveal(Action onRevealed)
        {
            if (!IsConfigured || !isActiveAndEnabled)
            {
                isTransitionActive = false;
                interruptionCallback = null;
                onRevealed?.Invoke();
                return;
            }

            if (activeFade != null)
            {
                StopCoroutine(activeFade);
            }

            isTransitionActive = true;
            transitionCanvas.enabled = true;
            canvasGroup.blocksRaycasts = true;
            canvasGroup.interactable = false;
            activeFade = StartCoroutine(FadeTo(
                0f,
                fadeInSeconds,
                () =>
                {
                    activeFade = null;
                    interruptionCallback = null;
                    SetIdleVisualState();
                    onRevealed?.Invoke();
                }));
        }

        private IEnumerator FadeTo(float targetAlpha, float duration, Action onCompleted)
        {
            float startAlpha = canvasGroup.alpha;
            if (duration <= 0f || Mathf.Approximately(startAlpha, targetAlpha))
            {
                canvasGroup.alpha = targetAlpha;
                onCompleted?.Invoke();
                yield break;
            }

            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.unscaledDeltaTime;
                canvasGroup.alpha = Mathf.Lerp(
                    startAlpha,
                    targetAlpha,
                    Mathf.Clamp01(elapsed / duration));
                yield return null;
            }

            canvasGroup.alpha = targetAlpha;
            onCompleted?.Invoke();
        }

        private void SetIdleVisualState()
        {
            isTransitionActive = false;
            if (!IsConfigured)
            {
                return;
            }

            canvasGroup.alpha = 0f;
            canvasGroup.blocksRaycasts = false;
            canvasGroup.interactable = false;
            transitionCanvas.enabled = false;
        }

        private void OnDisable()
        {
            bool wasInterrupted = isTransitionActive && Application.isPlaying;
            Action interrupted = interruptionCallback;
            interruptionCallback = null;

            if (activeFade != null)
            {
                StopCoroutine(activeFade);
                activeFade = null;
            }

            SetIdleVisualState();
            if (wasInterrupted)
            {
                interrupted?.Invoke();
            }
        }

#if UNITY_EDITOR
        private void OnValidate()
        {
            fadeOutSeconds = Mathf.Max(0f, fadeOutSeconds);
            fadeInSeconds = Mathf.Max(0f, fadeInSeconds);
        }
#endif
    }
}
