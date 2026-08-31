using System;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace VariableInventorySystem
{
    public class StandardStashView : MonoBehaviour, IVariableInventoryPartialDropView,
        IVariableInventoryDeferredDropTarget
    {
        [SerializeField] GameObject cellPrefab;
        //[SerializeField] ScrollRect scrollRect;
        [SerializeField] GridLayoutGroup gridLayoutGroup;
        [SerializeField] Graphic condition;
        [SerializeField] RectTransform conditionTransform;
        [SerializeField] RectTransform background;
        [SerializeField] RectTransform sizeTarget;
        [SerializeField] Vector2 sizePadding;

        [SerializeField] float holdScrollPadding;
        [SerializeField] float holdScrollRate;

        [SerializeField] Color defaultColor;
        [SerializeField] Color positiveColor;
        [SerializeField] Color negativeColor;

        public StandardStashViewData StashData { get; private set; }
        public IVariableInventoryViewData ViewData => StashData;

        public int CellCount => StashData.CapacityWidth * StashData.CapacityHeight;

        protected IVariableInventoryCell[] itemViews;
        protected CellCorner cellCorner;

        int? originalId;
        IVariableInventoryCellData originalCellData;
        bool? originalCellRotate;
        Vector3 conditionOffset;
        bool conditionNeedsRefresh;

        Action<IVariableInventoryCell> onCellClick;
        Action<IVariableInventoryCell> onCellOptionClick;
        Action<IVariableInventoryCell> onCellEnter;
        Action<IVariableInventoryCell> onCellExit;
        Func<IVariableInventoryCellData, bool> itemVisibilityFilter;
        Func<IVariableInventoryCellData, string> itemBadgeTextProvider;
        Func<IVariableInventoryCellData, string> quantityBadgeTextProvider;
        VariableInventoryDropHandling? dropPreviewHandling;

        public void SetCellCallback(
            Action<IVariableInventoryCell> onCellClick,
            Action<IVariableInventoryCell> onCellOptionClick,
            Action<IVariableInventoryCell> onCellEnter,
            Action<IVariableInventoryCell> onCellExit)
        {
            this.onCellClick = onCellClick;
            this.onCellOptionClick = onCellOptionClick;
            this.onCellEnter = onCellEnter;
            this.onCellExit = onCellExit;
        }

        public virtual void Apply(IVariableInventoryViewData data)
        {
            StashData = ((StandardStashViewData)data);

            if (itemViews == null || itemViews.Length != CellCount)
            {
                DestroyItemViews();
                itemViews = new IVariableInventoryCell[CellCount];

                for (var i = 0; i < CellCount; i++)
                {
                    var itemView = Instantiate(cellPrefab, gridLayoutGroup.transform).GetComponent<StandardCell>();
                    itemViews[i] = itemView;

                    itemView.transform.SetAsFirstSibling();
                    itemView.SetCellCallback(
                        onCellClick,
                        onCellOptionClick,
                        onCellEnter,
                        onCellExit,
                        null,
                        null);
                    itemView.Apply(null);
                }

                background.SetAsFirstSibling();
            }

            // Different inventory shapes can have the same total cell count
            // (for example 6x12 and 8x9). Keep the layout bound to the current
            // authority even when the existing cell instances can be reused.
            gridLayoutGroup.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            gridLayoutGroup.constraintCount = StashData.CapacityWidth;
            gridLayoutGroup.cellSize = itemViews.First().DefaultCellSize;
            gridLayoutGroup.spacing = itemViews.First().MargineSpace;

            for (var i = 0; i < StashData.CellData.Length; i++)
            {
                itemViews[i].Apply(StashData.CellData[i]);
                if (itemViews[i] is StandardCell standardCell)
                {
                    standardCell.SetContentVisible(IsItemVisible(StashData.CellData[i]));
                    standardCell.SetBadgeText(GetItemBadgeText(StashData.CellData[i]));
                    standardCell.SetQuantityBadgeText(GetQuantityBadgeText(StashData.CellData[i]));
                }
            }

            RefreshLayoutGeometry();
        }

        private void RefreshLayoutGeometry()
        {
            if (gridLayoutGroup == null || StashData == null)
            {
                return;
            }

            if (sizeTarget != null)
            {
                float width = gridLayoutGroup.padding.horizontal +
                              StashData.CapacityWidth * gridLayoutGroup.cellSize.x +
                              Mathf.Max(0, StashData.CapacityWidth - 1) *
                              gridLayoutGroup.spacing.x;
                float height = gridLayoutGroup.padding.vertical +
                               StashData.CapacityHeight * gridLayoutGroup.cellSize.y +
                               Mathf.Max(0, StashData.CapacityHeight - 1) *
                               gridLayoutGroup.spacing.y;
                sizeTarget.SetSizeWithCurrentAnchors(
                    RectTransform.Axis.Horizontal,
                    width + sizePadding.x);
                sizeTarget.SetSizeWithCurrentAnchors(
                    RectTransform.Axis.Vertical,
                    height + sizePadding.y);
            }

            if (gridLayoutGroup.transform is RectTransform content)
            {
                LayoutRebuilder.ForceRebuildLayoutImmediate(content);
            }
        }

        public void SetItemVisibilityFilter(Func<IVariableInventoryCellData, bool> filter)
        {
            SetItemPresentation(filter, itemBadgeTextProvider);
        }

        public void SetItemBadgeTextProvider(
            Func<IVariableInventoryCellData, string> provider)
        {
            SetItemPresentation(itemVisibilityFilter, provider);
        }

        public void SetQuantityBadgeTextProvider(
            Func<IVariableInventoryCellData, string> provider,
            bool refreshCurrent = true)
        {
            quantityBadgeTextProvider = provider;
            if (refreshCurrent && StashData != null)
            {
                Apply(StashData);
            }
        }

        public void SetItemPresentation(
            Func<IVariableInventoryCellData, bool> visibilityFilter,
            Func<IVariableInventoryCellData, string> badgeTextProvider,
            bool refreshCurrent = true)
        {
            itemVisibilityFilter = visibilityFilter;
            itemBadgeTextProvider = badgeTextProvider;
            if (refreshCurrent && StashData != null)
            {
                Apply(StashData);
            }
        }

        public bool IsItemVisible(IVariableInventoryCellData item)
        {
            return item == null || itemVisibilityFilter == null || itemVisibilityFilter(item);
        }

        public string GetItemBadgeText(IVariableInventoryCellData item)
        {
            return item != null && itemBadgeTextProvider != null
                ? itemBadgeTextProvider(item)
                : null;
        }

        public string GetQuantityBadgeText(IVariableInventoryCellData item)
        {
            return item != null && quantityBadgeTextProvider != null
                ? quantityBadgeTextProvider(item)
                : null;
        }

        public void SetDropPreviewHandling(VariableInventoryDropHandling? handling)
        {
            dropPreviewHandling = handling;
            conditionNeedsRefresh = true;
        }

        public virtual void ReApply()
        {
            if (!StashData.IsDirty)
            {
                return;
            }

            Apply(StashData);
            StashData.IsDirty = false;
        }

        public virtual void OnPrePick(IVariableInventoryCell stareCell)
        {
            if (!OwnsCell(stareCell) || stareCell.CellData == null)
            {
                return;
            }

            UpdateConditionSize(stareCell, stareCell.CellData);
        }

        public virtual bool OnPick(IVariableInventoryCell stareCell)
        {
            if (!OwnsCell(stareCell) || stareCell.CellData == null)
            {
                return false;
            }

            if (!IsItemVisible(stareCell.CellData))
            {
                return false;
            }

            var id = StashData.GetId(stareCell.CellData);
            if (id.HasValue)
            {
                originalId = id;
                originalCellData = stareCell.CellData;
                originalCellRotate = originalCellData.IsRotate;

                itemViews[id.Value].Apply(null);
                StashData.InsertInventoryItem(id.Value, null);
                return true;
            }

            return false;
        }

        public virtual void OnDrag(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell, PointerEventData pointerEventData)
        {
            if (!OwnsCell(stareCell))
            {
                return;
            }

            // auto scroll
            /*
            var pointerViewportPosition = GetLocalPosition(scrollRect.viewport, pointerEventData.position, pointerEventData.enterEventCamera);

            if (pointerViewportPosition.y < scrollRect.viewport.rect.min.y + holdScrollPadding)
            {
                var scrollValue = scrollRect.verticalNormalizedPosition * scrollRect.viewport.rect.height;
                scrollValue -= holdScrollRate;
                scrollRect.verticalNormalizedPosition = Mathf.Clamp01(scrollValue / scrollRect.viewport.rect.height);
            }

            if (pointerViewportPosition.y > scrollRect.viewport.rect.max.y - holdScrollPadding)
            {
                var scrollValue = scrollRect.verticalNormalizedPosition * scrollRect.viewport.rect.height;
                scrollValue += holdScrollRate;
                scrollRect.verticalNormalizedPosition = Mathf.Clamp01(scrollValue / scrollRect.viewport.rect.height);
            }
            */
            // depends on anchor
            var pointerLocalPosition = GetLocalPosition(stareCell.RectTransform, pointerEventData.position, pointerEventData.enterEventCamera);
            var anchor = new Vector2(stareCell.DefaultCellSize.x * 0.5f, -stareCell.DefaultCellSize.y * 0.5f);
            var anchoredPosition = pointerLocalPosition + anchor;
            conditionOffset = new Vector3(
                Mathf.Floor(anchoredPosition.x / stareCell.DefaultCellSize.x) * stareCell.DefaultCellSize.x,
                Mathf.Ceil(anchoredPosition.y / stareCell.DefaultCellSize.y) * stareCell.DefaultCellSize.y);

            // cell corner
            var prevCorner = cellCorner;
            cellCorner = GetCorner((new Vector2(anchoredPosition.x % stareCell.DefaultCellSize.x, anchoredPosition.y % stareCell.DefaultCellSize.y) - anchor) * 0.5f);

            // shift the position only even number size
            var (width, height) = GetRotateSize(effectCell.CellData);
            var evenNumberOffset = GetEvenNumberOffset(width, height, stareCell.DefaultCellSize.x * 0.5f, stareCell.DefaultCellSize.y * 0.5f);
            conditionTransform.position = stareCell.RectTransform.position + ((conditionOffset + evenNumberOffset) * stareCell.RectTransform.lossyScale.x);

            // update condition
            if (prevCorner != cellCorner || conditionNeedsRefresh)
            {
                UpdateCondition(stareCell, effectCell);
                conditionNeedsRefresh = false;
            }
        }

        public virtual bool OnDrop(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (!OwnsCell(stareCell))
            {
                return false;
            }

            // check target;
            var index = GetIndex(stareCell, effectCell.CellData, cellCorner);
            if (!index.HasValue)
            {
                return false;
            }

            if (!StashData.CheckInsert(index.Value, effectCell.CellData))
            {
                // check free space in case
                if (stareCell.CellData != null && stareCell.CellData is VariableInventorySystem.IStandardCaseCellData caseData)
                {
                    var id = caseData.CaseData.GetInsertableId(effectCell.CellData);
                    if (id.HasValue)
                    {
                        caseData.CaseData.InsertInventoryItem(id.Value, effectCell.CellData);

                        originalId = null;
                        originalCellData = null;
                        originalCellRotate = null;
                        return true;
                    }
                }

                return false;
            }

            // place
            StashData.InsertInventoryItem(index.Value, effectCell.CellData);
            itemViews[index.Value].Apply(effectCell.CellData);

            originalId = null;
            originalCellData = null;
            originalCellRotate = null;
            return true;
        }

        public bool TryResolvePartialDrop(
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData detachedItem,
            out IVariableInventoryViewData destinationOwner,
            out int destinationIndex,
            out string error)
        {
            destinationOwner = null;
            destinationIndex = -1;
            error = null;
            if (!OwnsCell(destinationCell) || detachedItem == null ||
                destinationCell.CellData != null)
            {
                return false;
            }

            int? index = GetIndex(destinationCell, detachedItem, cellCorner);
            if (!index.HasValue ||
                OverlapsReservedPickFootprint(index.Value, detachedItem) ||
                !StashData.CheckInsert(index.Value, detachedItem))
            {
                return false;
            }

            destinationOwner = StashData;
            destinationIndex = index.Value;
            return true;
        }

        public bool TryResolveDeferredDropTarget(
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            IVariableInventoryViewData expectedSourceOwner,
            out IVariableInventoryViewData destinationOwner,
            out int destinationIndex,
            out string error)
        {
            destinationOwner = null;
            destinationIndex = -1;
            if (!OwnsCell(destinationCell) || item == null || expectedSourceOwner == null)
            {
                error = "The deferred drop target is not part of this inventory view.";
                return false;
            }

            int? index = GetIndex(destinationCell, item, cellCorner);
            if (index.HasValue &&
                StashData.CheckInsertFromOwner(
                    index.Value,
                    item,
                    expectedSourceOwner))
            {
                destinationOwner = StashData;
                destinationIndex = index.Value;
                error = null;
                return true;
            }

            if (destinationCell.CellData is IStandardCaseCellData caseData)
            {
                for (int candidate = 0;
                     candidate < caseData.CaseData.CellData.Length;
                     candidate++)
                {
                    if (!caseData.CaseData.CheckInsertFromOwner(
                            candidate,
                            item,
                            expectedSourceOwner))
                    {
                        continue;
                    }

                    destinationOwner = caseData.CaseData;
                    destinationIndex = candidate;
                    error = null;
                    return true;
                }
            }

            error = "The item does not fit at the selected inventory position.";
            return false;
        }

        public virtual void OnDroped(bool isDroped)
        {
            dropPreviewHandling = null;
            conditionTransform.gameObject.SetActive(false);
            condition.color = defaultColor;
            conditionNeedsRefresh = false;

            if (!isDroped && originalId.HasValue)
            {
                if (!StashData.CheckInsert(originalId.Value, originalCellData))
                {
                    Debug.LogError(
                        "The picked item's original footprint is no longer available. " +
                        "Rollback was stopped without replacing the occupying item.",
                        this);
                    return;
                }

                // revert
                itemViews[originalId.Value].Apply(originalCellData);
                StashData.InsertInventoryItem(originalId.Value, originalCellData);
            }

            originalId = null;
            originalCellData = null;
            originalCellRotate = null;
        }

        public virtual void OnCellEnter(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (!OwnsCell(stareCell) || !(stareCell is StandardCell standardCell))
            {
                return;
            }

            bool isDragging = effectCell?.CellData != null;
            conditionTransform.gameObject.SetActive(isDragging);
            if (isDragging)
            {
                // 각 인벤토리 View는 독립적인 condition을 가진다. 다른 View에서
                // 넘어온 아이템의 크기와 판정색을 이 View 기준으로 다시 계산한다.
                UpdateConditionSize(stareCell, effectCell.CellData);
                condition.color = defaultColor;
                conditionNeedsRefresh = true;
            }
            standardCell.SetHighLight(IsItemVisible(stareCell.CellData));
        }

        public virtual void OnCellExit(IVariableInventoryCell stareCell)
        {
            if (!OwnsCell(stareCell) || !(stareCell is StandardCell standardCell))
            {
                return;
            }

            conditionTransform.gameObject.SetActive(false);
            condition.color = defaultColor;
            conditionNeedsRefresh = false;

            cellCorner = CellCorner.None;

            standardCell.SetHighLight(false);
        }

        public virtual void OnSwitchRotate(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (!OwnsCell(stareCell))
            {
                return;
            }

            var (width, height) = GetRotateSize(effectCell.CellData);
            UpdateConditionSize(stareCell, effectCell.CellData);

            var evenNumberOffset = GetEvenNumberOffset(width, height, stareCell.DefaultCellSize.x * 0.5f, stareCell.DefaultCellSize.y * 0.5f);
            conditionTransform.position = stareCell.RectTransform.position + ((conditionOffset + evenNumberOffset) * stareCell.RectTransform.lossyScale.x);

            UpdateCondition(stareCell, effectCell);
            conditionNeedsRefresh = false;
        }

        private bool OwnsCell(IVariableInventoryCell cell)
        {
            return cell != null && itemViews != null && itemViews.Any(item => ReferenceEquals(item, cell));
        }

        public bool ContainsCell(IVariableInventoryCell cell)
        {
            return OwnsCell(cell);
        }

        private void DestroyItemViews()
        {
            if (itemViews == null)
            {
                return;
            }

            foreach (IVariableInventoryCell itemView in itemViews)
            {
                if (itemView?.RectTransform == null)
                {
                    continue;
                }

                GameObject cellObject = itemView.RectTransform.gameObject;
                cellObject.SetActive(false);
                Destroy(cellObject);
            }
        }

        protected virtual int? GetIndex(IVariableInventoryCell stareCell)
        {
            var index = (int?)null;
            for (var i = 0; i < itemViews.Length; i++)
            {
                if (itemViews[i] == stareCell)
                {
                    index = i;
                }
            }

            return index;
        }

        protected virtual int? GetIndex(IVariableInventoryCell stareCell, IVariableInventoryCellData effectCellData, CellCorner cellCorner)
        {
            var index = GetIndex(stareCell);

            // offset index
            var (width, height) = GetRotateSize(effectCellData);
            if (width % 2 == 0)
            {
                if ((cellCorner & CellCorner.Left) != CellCorner.None)
                {
                    index--;
                }
            }

            if (height % 2 == 0)
            {
                if ((cellCorner & CellCorner.Top) != CellCorner.None)
                {
                    index -= StashData.CapacityWidth;
                }
            }

            index -= (width - 1) / 2;
            index -= (height - 1) / 2 * StashData.CapacityWidth;
            return index;
        }

        private bool OverlapsReservedPickFootprint(
            int destinationId,
            IVariableInventoryCellData destinationItem)
        {
            if (!originalId.HasValue || originalCellData == null)
            {
                return false;
            }

            bool originalRotation = originalCellRotate ?? originalCellData.IsRotate;
            int originalWidth = originalRotation
                ? originalCellData.Height
                : originalCellData.Width;
            int originalHeight = originalRotation
                ? originalCellData.Width
                : originalCellData.Height;
            var (destinationWidth, destinationHeight) = GetRotateSize(destinationItem);
            int originalX = originalId.Value % StashData.CapacityWidth;
            int originalY = originalId.Value / StashData.CapacityWidth;
            int destinationX = destinationId % StashData.CapacityWidth;
            int destinationY = destinationId / StashData.CapacityWidth;

            bool separatedHorizontally = destinationX + destinationWidth <= originalX ||
                                         originalX + originalWidth <= destinationX;
            bool separatedVertically = destinationY + destinationHeight <= originalY ||
                                       originalY + originalHeight <= destinationY;
            return !separatedHorizontally && !separatedVertically;
        }

        protected virtual (int, int) GetRotateSize(IVariableInventoryCellData cell)
        {
            if (cell == null)
            {
                return (1, 1);
            }

            return (cell.IsRotate ? cell.Height : cell.Width, cell.IsRotate ? cell.Width : cell.Height);
        }

        protected virtual Vector2 GetLocalPosition(RectTransform parent, Vector2 position, Camera camera)
        {
            var localPosition = Vector2.zero;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(parent, position, camera, out localPosition);
            return localPosition;
        }

        protected virtual CellCorner GetCorner(Vector2 localPosition)
        {
            // depends on pivot
            var corner = CellCorner.None;
            if (localPosition.x < Mathf.Epsilon)
            {
                corner |= CellCorner.Left;
            }

            if (localPosition.x > Mathf.Epsilon)
            {
                corner |= CellCorner.Right;
            }

            if (localPosition.y > Mathf.Epsilon)
            {
                corner |= CellCorner.Top;
            }

            if (localPosition.y < Mathf.Epsilon)
            {
                corner |= CellCorner.Bottom;
            }

            return corner;
        }

        protected virtual Vector3 GetEvenNumberOffset(int width, int height, float widthOffset, float heightOffset)
        {
            var evenNumberOffset = Vector3.zero;

            if (width % 2 == 0)
            {
                if ((cellCorner & CellCorner.Left) != CellCorner.None)
                {
                    evenNumberOffset.x -= widthOffset;
                }

                if ((cellCorner & CellCorner.Right) != CellCorner.None)
                {
                    evenNumberOffset.x += widthOffset;
                }
            }

            if (height % 2 == 0)
            {
                if ((cellCorner & CellCorner.Top) != CellCorner.None)
                {
                    evenNumberOffset.y += heightOffset;
                }

                if ((cellCorner & CellCorner.Bottom) != CellCorner.None)
                {
                    evenNumberOffset.y -= heightOffset;
                }
            }

            return evenNumberOffset;
        }

        protected virtual void UpdateCondition(IVariableInventoryCell stareCell, IVariableInventoryCell effectCell)
        {
            if (dropPreviewHandling == VariableInventoryDropHandling.AcceptWithoutInsert)
            {
                condition.color = positiveColor;
                return;
            }

            if (dropPreviewHandling == VariableInventoryDropHandling.Reject)
            {
                condition.color = negativeColor;
                return;
            }

            var index = GetIndex(stareCell, effectCell.CellData, cellCorner);
            if ((index.HasValue && StashData.CheckInsert(index.Value, effectCell.CellData)))
            {
                condition.color = positiveColor;
            }
            else
            {
                // check free space in case
                if (stareCell.CellData != null &&
                    stareCell.CellData is VariableInventorySystem.IStandardCaseCellData caseData &&
                    caseData.CaseData.GetInsertableId(effectCell.CellData).HasValue)
                {
                    condition.color = positiveColor;
                }
                else
                {
                    condition.color = negativeColor;
                }
            }
        }

        private void UpdateConditionSize(IVariableInventoryCell targetCell, IVariableInventoryCellData item)
        {
            var (width, height) = GetRotateSize(item);
            conditionTransform.sizeDelta = new Vector2(
                targetCell.DefaultCellSize.x * width,
                targetCell.DefaultCellSize.y * height);
        }

        protected virtual void OnEnable()
        {
            // UI가 다시 나타날 때 condition(미리보기 테두리)이
            // 이전 상태로 남아있는 것을 방지하기 위해 강제로 숨김
            if (conditionTransform != null)
            {
                conditionTransform.gameObject.SetActive(false);
            }
            // 필요하다면 다른 관련 상태 변수 초기화 (예: cellCorner)
            cellCorner = CellCorner.None;
            conditionNeedsRefresh = false;
            // Debug.Log($"[StashView {GetInstanceID()}] OnEnable: Condition hidden."); // 필요시 디버그 로그
        }
    }
}
