using System;
using UnityEngine;
using UnityEngine.UI;

namespace FantasySurvival.Inventory
{
    [DisallowMultipleComponent]
    public sealed class InventoryStackSplitDialog : MonoBehaviour
    {
        [Header("Canvas")]
        [SerializeField] private Canvas rootCanvas;
        [Header("Context Menu")]
        [SerializeField] private RectTransform contextPanel;
        [SerializeField] private Text contextItemText;
        [SerializeField] private Button useActionButton;
        [SerializeField] private Button splitActionButton;
        [SerializeField] private Button contextCancelButton;
        [Header("Quantity Entry")]
        [SerializeField] private RectTransform quantityPanel;
        [SerializeField] private Text titleText;
        [SerializeField] private Text rangeText;
        [SerializeField] private Text errorText;
        [SerializeField] private InputField quantityInput;
        [SerializeField] private Button confirmButton;
        [SerializeField] private Button cancelButton;

        private Func<int, string> confirmSplit;
        private Action useAction;
        private int maximumSplitQuantity;

        public bool IsOpen => gameObject.activeSelf;
        public bool IsQuantityEntryOpen => IsOpen && quantityPanel != null &&
                                           quantityPanel.gameObject.activeSelf;

        private void Awake()
        {
            useActionButton.onClick.AddListener(UseSelectedItem);
            splitActionButton.onClick.AddListener(ShowQuantityEntry);
            contextCancelButton.onClick.AddListener(Close);
            confirmButton.onClick.AddListener(Confirm);
            cancelButton.onClick.AddListener(Close);
            quantityInput.contentType = InputField.ContentType.IntegerNumber;
            quantityInput.lineType = InputField.LineType.SingleLine;
        }

        private void OnDestroy()
        {
            if (useActionButton != null)
            {
                useActionButton.onClick.RemoveListener(UseSelectedItem);
            }

            if (splitActionButton != null)
            {
                splitActionButton.onClick.RemoveListener(ShowQuantityEntry);
            }

            if (contextCancelButton != null)
            {
                contextCancelButton.onClick.RemoveListener(Close);
            }

            if (confirmButton != null)
            {
                confirmButton.onClick.RemoveListener(Confirm);
            }

            if (cancelButton != null)
            {
                cancelButton.onClick.RemoveListener(Close);
            }
        }

        private void OnDisable()
        {
            useAction = null;
            confirmSplit = null;
            maximumSplitQuantity = 0;
        }

        public void OpenContext(
            string itemDisplayName,
            Action onUse,
            int maxSplitQuantity,
            Vector2 screenPosition,
            Func<int, string> onConfirm)
        {
            bool canUse = onUse != null;
            bool canSplit = maxSplitQuantity >= 1 && onConfirm != null;
            if (!canUse && !canSplit)
            {
                return;
            }

            useAction = canUse ? onUse : null;
            maximumSplitQuantity = canSplit ? maxSplitQuantity : 0;
            confirmSplit = canSplit ? onConfirm : null;
            gameObject.SetActive(true);

            contextItemText.text = string.IsNullOrWhiteSpace(itemDisplayName)
                ? "아이템"
                : itemDisplayName;
            contextPanel.gameObject.SetActive(true);
            quantityPanel.gameObject.SetActive(false);
            useActionButton.gameObject.SetActive(canUse);
            splitActionButton.gameObject.SetActive(canSplit);
            LayoutContextActions(canUse, canSplit);
            errorText.text = string.Empty;
            PositionContextPanel(screenPosition);
        }

        public void Close()
        {
            useAction = null;
            confirmSplit = null;
            maximumSplitQuantity = 0;
            if (contextPanel != null)
            {
                contextPanel.gameObject.SetActive(false);
            }

            if (quantityPanel != null)
            {
                quantityPanel.gameObject.SetActive(false);
            }

            if (gameObject.activeSelf)
            {
                gameObject.SetActive(false);
            }
        }

        public bool TryValidateReferences(out string error)
        {
            if (rootCanvas == null || contextPanel == null || contextItemText == null ||
                useActionButton == null || splitActionButton == null ||
                contextCancelButton == null ||
                quantityPanel == null || titleText == null || rangeText == null ||
                errorText == null || quantityInput == null || confirmButton == null ||
                cancelButton == null)
            {
                error = "Inventory stack split dialog references are incomplete.";
                return false;
            }

            error = null;
            return true;
        }

        private void UseSelectedItem()
        {
            Action selectedAction = useAction;
            Close();
            selectedAction?.Invoke();
        }

        private void LayoutContextActions(bool canUse, bool canSplit)
        {
            float y = -42f;
            if (canUse)
            {
                useActionButton.GetComponent<RectTransform>().anchoredPosition =
                    new Vector2(10f, y);
                y -= 40f;
            }

            if (canSplit)
            {
                splitActionButton.GetComponent<RectTransform>().anchoredPosition =
                    new Vector2(10f, y);
                y -= 40f;
            }

            contextCancelButton.GetComponent<RectTransform>().anchoredPosition =
                new Vector2(10f, y);
            contextPanel.sizeDelta = new Vector2(
                contextPanel.sizeDelta.x,
                canUse && canSplit ? 166f : 126f);
        }

        private void ShowQuantityEntry()
        {
            contextPanel.gameObject.SetActive(false);
            quantityPanel.gameObject.SetActive(true);
            titleText.text = "나눌 수량";
            rangeText.text = $"1 ~ {maximumSplitQuantity}";
            errorText.text = string.Empty;
            quantityInput.text = "1";
            quantityInput.Select();
            quantityInput.ActivateInputField();
        }

        private void Confirm()
        {
            if (!int.TryParse(quantityInput.text, out int quantity) ||
                quantity < 1 || quantity > maximumSplitQuantity)
            {
                errorText.text = $"1부터 {maximumSplitQuantity}까지 입력하세요.";
                quantityInput.Select();
                quantityInput.ActivateInputField();
                return;
            }

            string error = confirmSplit?.Invoke(quantity);
            if (!string.IsNullOrEmpty(error))
            {
                errorText.text = error;
                quantityInput.Select();
                quantityInput.ActivateInputField();
                return;
            }

            Close();
        }

        private void PositionContextPanel(Vector2 screenPosition)
        {
            if (!(rootCanvas.transform is RectTransform canvasRect))
            {
                return;
            }

            Camera eventCamera = rootCanvas.renderMode == RenderMode.ScreenSpaceOverlay
                ? null
                : rootCanvas.worldCamera;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(
                    canvasRect,
                    screenPosition,
                    eventCamera,
                    out Vector2 localPoint))
            {
                localPoint = Vector2.zero;
            }

            Rect canvasBounds = canvasRect.rect;
            Vector2 panelSize = contextPanel.rect.size;
            Vector2 pivot = contextPanel.pivot;
            localPoint.x = Mathf.Clamp(
                localPoint.x,
                canvasBounds.xMin + panelSize.x * pivot.x,
                canvasBounds.xMax - panelSize.x * (1f - pivot.x));
            localPoint.y = Mathf.Clamp(
                localPoint.y,
                canvasBounds.yMin + panelSize.y * pivot.y,
                canvasBounds.yMax - panelSize.y * (1f - pivot.y));
            contextPanel.anchoredPosition = localPoint;
        }
    }
}
