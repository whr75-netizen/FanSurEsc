using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Serialization;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    [DisallowMultipleComponent]
    public sealed class EquipmentSlotCell : MonoBehaviour, IVariableInventoryCell,
        IPointerClickHandler, IPointerEnterHandler, IPointerExitHandler
    {
        [FormerlySerializedAs("slotType")]
        [SerializeField] private EquipmentSlotId slotId;
        [SerializeField] private Vector2 defaultCellSize = new Vector2(48f, 48f);
        [SerializeField] private Image background;
        [SerializeField] private RawImage icon;
        [SerializeField] private Image highlight;
        [SerializeField] private Text slotLabel;

        private Action<IVariableInventoryCell> onCellClick;
        private Action<IVariableInventoryCell> onCellOptionClick;
        private Action<IVariableInventoryCell> onCellEnter;
        private Action<IVariableInventoryCell> onCellExit;
        private bool selectable = true;

        public EquipmentSlotId SlotId => slotId;
        public RectTransform RectTransform => (RectTransform)transform;
        public IVariableInventoryCellData CellData { get; private set; }
        public Vector2 DefaultCellSize => defaultCellSize;
        public Vector2 MargineSpace => Vector2.zero;

        public void Configure(EquipmentSlotId id)
        {
            slotId = id;
            RefreshLabel();
        }

        public void SetCellCallback(
            Action<IVariableInventoryCell> cellClick,
            Action<IVariableInventoryCell> cellOptionClick,
            Action<IVariableInventoryCell> cellEnter,
            Action<IVariableInventoryCell> cellExit)
        {
            onCellClick = cellClick;
            onCellOptionClick = cellOptionClick;
            onCellEnter = cellEnter;
            onCellExit = cellExit;
        }

        public void Apply(IVariableInventoryCellData data)
        {
            CellData = data;
            if (icon != null)
            {
                var item = data as InventoryItemData;
                icon.texture = item != null ? item.Definition.Icon : null;
                icon.gameObject.SetActive(item != null && item.Definition.Icon != null);
            }

            RefreshLabel();
            SetHighlight(false, false);
        }

        public void SetSelectable(bool isSelectable)
        {
            selectable = isSelectable;
            if (background != null)
            {
                background.raycastTarget = isSelectable;
            }
        }

        public void SetHighlight(bool visible, bool valid)
        {
            if (highlight == null)
            {
                return;
            }

            highlight.color = valid
                ? new Color(0.2f, 0.8f, 0.35f, 0.55f)
                : new Color(0.9f, 0.25f, 0.2f, 0.55f);
            highlight.gameObject.SetActive(visible);
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            if (!selectable)
            {
                return;
            }

            if (eventData.button == PointerEventData.InputButton.Left)
            {
                onCellClick?.Invoke(this);
            }
            else
            {
                onCellOptionClick?.Invoke(this);
            }
        }

        public void OnPointerEnter(PointerEventData eventData)
        {
            if (selectable)
            {
                onCellEnter?.Invoke(this);
            }
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (selectable)
            {
                onCellExit?.Invoke(this);
            }
        }

        private void RefreshLabel()
        {
            if (slotLabel != null)
            {
                slotLabel.text = EquipmentSlotCatalog.GetShortLabel(slotId);
            }
        }

        private void OnValidate()
        {
            defaultCellSize.x = Mathf.Max(1f, defaultCellSize.x);
            defaultCellSize.y = Mathf.Max(1f, defaultCellSize.y);
            RefreshLabel();
        }
    }
}
