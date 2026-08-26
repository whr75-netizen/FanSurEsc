using UnityEngine;
using UnityEngine.UI;

namespace FantasySurvival.Inventory
{
    [DisallowMultipleComponent]
    public sealed class InventoryItemTooltipView : MonoBehaviour
    {
        [SerializeField] private Canvas rootCanvas;
        [SerializeField] private RectTransform panel;
        [SerializeField] private Text nameText;
        [SerializeField] private Text descriptionText;
        [SerializeField] private Text statsText;
        [SerializeField] private Vector2 pointerOffset = new Vector2(18f, -18f);

        private bool visible;

        public bool TryValidateReferences(out string error)
        {
            if (rootCanvas == null || panel == null || nameText == null ||
                descriptionText == null || statsText == null)
            {
                error = "Inventory item tooltip references are incomplete.";
                return false;
            }

            if (panel.parent == null || !(panel.parent is RectTransform))
            {
                error = "Inventory item tooltip must be parented under a Canvas RectTransform.";
                return false;
            }

            error = null;
            return true;
        }

        public void Show(ItemDefinition definition)
        {
            if (definition == null)
            {
                Hide();
                return;
            }

            if (!TryValidateReferences(out string error))
            {
                Hide();
                Debug.LogError(error, this);
                return;
            }

            InventoryItemTooltipContent content =
                InventoryItemTooltipFormatter.Create(definition);
            nameText.text = content.Name;
            descriptionText.text = content.Description;
            statsText.text = content.Stats;

            visible = true;
            panel.gameObject.SetActive(true);
            panel.SetAsLastSibling();
            PositionNearPointer();
        }

        public void Hide()
        {
            visible = false;
            if (panel != null && panel.gameObject.activeSelf)
            {
                panel.gameObject.SetActive(false);
            }
        }

        private void LateUpdate()
        {
            if (visible)
            {
                PositionNearPointer();
            }
        }

        private void OnDisable()
        {
            visible = false;
        }

        private void PositionNearPointer()
        {
            if (rootCanvas == null || panel == null ||
                !(panel.parent is RectTransform parentRect))
            {
                return;
            }

            Camera eventCamera = rootCanvas.renderMode == RenderMode.ScreenSpaceOverlay
                ? null
                : rootCanvas.worldCamera;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(
                    parentRect,
                    Input.mousePosition,
                    eventCamera,
                    out Vector2 localPointer))
            {
                return;
            }

            Vector2 desired = localPointer + pointerOffset;
            Vector2 panelSize = panel.rect.size;
            Rect parentBounds = parentRect.rect;

            float minX = parentBounds.xMin + panelSize.x * panel.pivot.x;
            float maxX = parentBounds.xMax - panelSize.x * (1f - panel.pivot.x);
            float minY = parentBounds.yMin + panelSize.y * panel.pivot.y;
            float maxY = parentBounds.yMax - panelSize.y * (1f - panel.pivot.y);

            desired.x = Mathf.Clamp(desired.x, minX, maxX);
            desired.y = Mathf.Clamp(desired.y, minY, maxY);
            panel.anchoredPosition = desired;
        }
    }
}
