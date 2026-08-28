using UnityEngine;
using UnityEngine.UI;

namespace FantasySurvival.Actions
{
    /// <summary>
    /// Presents the Player's single timed action above its current world source.
    /// The action controller remains the sole owner of timing and completion.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class PlayerActionWorldCountdownView : MonoBehaviour
    {
        [SerializeField] private PlayerActionController actionController;
        [SerializeField] private Camera worldCamera;
        [SerializeField] private Canvas rootCanvas;
        [SerializeField] private RectTransform countdownRoot;
        [SerializeField] private Text countdownText;
        [SerializeField] private Vector3 worldOffset = new Vector3(0f, 2f, 0f);
        [SerializeField] private Vector2 screenOffset = new Vector2(0f, 10f);

        private bool isSubscribed;

        private void OnEnable()
        {
            if (!TryValidateConfiguration(out string error))
            {
                Debug.LogError(error, this);
                SetVisible(false);
                enabled = false;
                return;
            }

            actionController.ActionStarted += HandleActionStarted;
            actionController.ActionEnded += HandleActionEnded;
            Canvas.preWillRenderCanvases += RefreshPresentation;
            isSubscribed = true;
            SetVisible(actionController.IsBusy);
        }

        private void OnDisable()
        {
            if (isSubscribed)
            {
                actionController.ActionStarted -= HandleActionStarted;
                actionController.ActionEnded -= HandleActionEnded;
                Canvas.preWillRenderCanvases -= RefreshPresentation;
                isSubscribed = false;
            }

            SetVisible(false);
        }

        private void HandleActionStarted()
        {
            SetVisible(true);
            RefreshPresentation();
        }

        private void HandleActionEnded()
        {
            SetVisible(false);
        }

        private void RefreshPresentation()
        {
            Transform anchor = actionController.ActiveWorldAnchor;
            if (!actionController.IsBusy || anchor == null)
            {
                SetVisible(false);
                return;
            }

            Vector3 viewportPoint = worldCamera.WorldToViewportPoint(
                anchor.position + worldOffset);
            if (viewportPoint.z <= 0f || viewportPoint.x < 0f || viewportPoint.x > 1f ||
                viewportPoint.y < 0f || viewportPoint.y > 1f)
            {
                SetVisible(false);
                return;
            }

            Vector3 screenPoint = worldCamera.ViewportToScreenPoint(viewportPoint);
            Camera canvasCamera = rootCanvas.renderMode == RenderMode.ScreenSpaceOverlay
                ? null
                : rootCanvas.worldCamera;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(
                    rootCanvas.transform as RectTransform,
                    screenPoint,
                    canvasCamera,
                    out Vector2 localPoint))
            {
                SetVisible(false);
                return;
            }

            countdownRoot.anchoredPosition = localPoint + screenOffset;
            countdownText.text = $"{actionController.RemainingSeconds:0.0}초";
            SetVisible(true);
        }

        private void SetVisible(bool visible)
        {
            if (countdownRoot != null && countdownRoot.gameObject.activeSelf != visible)
            {
                countdownRoot.gameObject.SetActive(visible);
            }
        }

        public bool TryValidateConfiguration(out string error)
        {
            if (actionController == null || worldCamera == null || rootCanvas == null ||
                countdownRoot == null || countdownText == null)
            {
                error = $"{nameof(PlayerActionWorldCountdownView)} has missing required references.";
                return false;
            }

            if (!countdownRoot.IsChildOf(rootCanvas.transform))
            {
                error = "The action countdown root must belong to its configured HUD Canvas.";
                return false;
            }

            error = null;
            return true;
        }
    }
}
