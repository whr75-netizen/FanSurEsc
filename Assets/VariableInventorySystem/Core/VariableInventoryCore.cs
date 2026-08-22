// 파일 경로: Assets/VariableInventorySystem/Core/VariableInventoryCore.cs
// ★★★ 이 파일 전체를 아래 내용으로 교체하세요 ★★★

using System.Collections.Generic;
using System.Linq; // Linq.Any는 사용 안하지만 다른 곳에서 필요할 수 있음
using UnityEngine;
using UnityEngine.EventSystems;

namespace VariableInventorySystem
{
    public abstract class VariableInventoryCore : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        // --- 필드 ---
        protected List<IVariableInventoryView> InventoryViews { get; set; } = new List<IVariableInventoryView>();
        //    [SerializeField] protected virtual GameObject CellPrefab { get; set; }
        //      [SerializeField] protected virtual RectTransform EffectCellParent { get; set; }
        [field: SerializeField] protected virtual GameObject CellPrefab { get; set; }
        [field: SerializeField] protected virtual RectTransform EffectCellParent { get; set; }
        protected IVariableInventoryCell stareCell;
        protected IVariableInventoryCell effectCell;
        bool? originEffectCellRotate;
        Vector2 cursorPosition;
        private IVariableInventoryView originView = null; // ★ 드래그 시작 View 저장용

        // --- 추가/기존 메소드 ---
        public bool IsDragging() => effectCell?.CellData != null;
        public virtual void Initialize() { if (effectCell != null) return; if (CellPrefab == null || EffectCellParent == null) { Debug.LogError($"[{GetType().Name}] CellPrefab or EffectCellParent not set!", gameObject); return; } var e = Instantiate(CellPrefab, EffectCellParent); if (e == null) return; effectCell = e.GetComponent<IVariableInventoryCell>(); if (effectCell == null) { Destroy(e); return; } effectCell.RectTransform.gameObject.SetActive(false); effectCell.SetSelectable(false); }
        public virtual void AddInventoryView(IVariableInventoryView v) { if (v == null || InventoryViews.Contains(v)) return; InventoryViews.Add(v); v.SetCellCallback(OnCellClick, OnCellOptionClick, OnCellEnter, OnCellExit); }
        public virtual void RemoveInventoryView(IVariableInventoryView v) { if (v == null || !InventoryViews.Contains(v)) return; InventoryViews.Remove(v); }
        protected virtual void OnCellClick(IVariableInventoryCell cell) { }
        protected virtual void OnCellOptionClick(IVariableInventoryCell cell) { }
        protected virtual void OnCellEnter(IVariableInventoryCell cell) { stareCell = cell; foreach (var v in InventoryViews) v.OnCellEnter(stareCell, effectCell); }
        protected virtual void OnCellExit(IVariableInventoryCell cell) { if (stareCell == cell) stareCell = null; foreach (var v in InventoryViews) v.OnCellExit(cell); }

        // --- ★★★ OnBeginDrag (원본 기반 최소 수정) ★★★ ---
        public virtual void OnBeginDrag(PointerEventData eventData)
        {
            if (eventData.button != PointerEventData.InputButton.Left) return;
            if (IsDragging())
            {
                Debug.LogWarning("[Core.OnBeginDrag] A previous drag is still active. New source was not detached.");
                return;
            }

            // 1. 모든 View에 OnPrePick 호출 (원본과 동일)
            foreach (var inventoryView in InventoryViews)
            {
                inventoryView.OnPrePick(stareCell);
            }

            // 2. 현재 셀 데이터 저장 (원본과 동일)
            var stareData = stareCell?.CellData;
            if (stareData == null) { Debug.LogWarning("[Core.OnBeginDrag] No data in stareCell before pick."); return; }

            // 드래그 표시 셀을 먼저 준비한다. 원본 아이템을 소유자에서 분리한 뒤
            // 초기화가 실패하면 어느 컨테이너에도 속하지 않는 상태가 되기 때문이다.
            if (effectCell == null) Initialize();
            if (effectCell == null)
            {
                Debug.LogError("[Core.OnBeginDrag] effectCell is null. The source item was not detached.");
                return;
            }

            originView = null; // 초기화

            // 3. OnPick 성공 여부 확인 및 originView 저장 (Linq.Any 대신 foreach 사용)
            bool isHold = false;
            foreach (var inventoryView in InventoryViews)
            {
                if (inventoryView.OnPick(stareCell)) // OnPick 호출 (아이템 제거 및 상태 저장)
                {
                    isHold = true;
                    originView = inventoryView; // ★ OnPick 성공한 View를 originView에 저장
                    break; // 첫 성공 시 루프 중단 (Any와 동일 효과)
                }
            }

            // 4. 집기 실패 시 종료 (원본과 동일)
            if (!isHold)
            {
                Debug.LogWarning("[Core.OnBeginDrag] OnPick failed for all views.");
                originView = null; // 실패 시 확실히 초기화
                return;
            }

            // 5. effectCell 활성화 및 데이터 적용 (원본과 동일)
            effectCell.RectTransform.gameObject.SetActive(true);
            effectCell.Apply(stareData); // OnPick 전에 저장한 stareData 사용
            originEffectCellRotate = stareData.IsRotate; // 회전 상태 저장
        }

        // --- OnDrag (원본 유지) ---
        public virtual void OnDrag(PointerEventData eventData) { if (!IsDragging()) return; foreach (var v in InventoryViews) v.OnDrag(stareCell, effectCell, eventData); RectTransformUtility.ScreenPointToLocalPointInRectangle(EffectCellParent, eventData.position, eventData.enterEventCamera, out cursorPosition); var (w, h) = GetRotateSize(effectCell.CellData); effectCell.RectTransform.localPosition = cursorPosition + new Vector2(-(w - 1) * effectCell.DefaultCellSize.x * 0.5f, (h - 1) * effectCell.DefaultCellSize.y * 0.5f); }

        // --- OnEndDrag (originView 초기화 추가) ---
        public virtual void OnEndDrag(PointerEventData eventData)
        {
            if (!IsDragging()) return;
            bool isRelease = false; foreach (var view in InventoryViews) { if (view.OnDrop(stareCell, effectCell)) { isRelease = true; break; } }
            if (!isRelease) RestoreOriginalRotation();
            foreach (var inventoryView in InventoryViews) inventoryView?.OnDroped(isRelease); // ★ OnDroped에서 복구 처리됨
            if (!isRelease && IsDetachedOwnedItem())
            {
                Debug.LogError("[Core.OnEndDrag] Rollback failed. Drag state was kept instead of discarding the item reference.");
                return;
            }
            if (effectCell != null) { if (effectCell.RectTransform != null) effectCell.RectTransform.gameObject.SetActive(false); effectCell.Apply(null); }
            originEffectCellRotate = null;
            originView = null; // ★ 초기화
            stareCell = null; // 상태 초기화
            Debug.Log($"[Core.OnEndDrag] Drag ended. Drop Success: {isRelease}");
        }

        // --- SwitchRotate, GetRotateSize (원본 유지) ---
        public virtual void SwitchRotate() { if (!IsDragging()) return; if (!originEffectCellRotate.HasValue) originEffectCellRotate = effectCell.CellData.IsRotate; effectCell.CellData.IsRotate = !effectCell.CellData.IsRotate; effectCell.Apply(effectCell.CellData); var (w, h) = GetRotateSize(effectCell.CellData); effectCell.RectTransform.localPosition = cursorPosition + new Vector2(-(w - 1) * effectCell.DefaultCellSize.x * 0.5f, (h - 1) * effectCell.DefaultCellSize.y * 0.5f); foreach (var v in InventoryViews) v.OnSwitchRotate(stareCell, effectCell); }
        (int, int) GetRotateSize(IVariableInventoryCellData cell) { if (cell == null) return (1, 1); return (cell.IsRotate ? cell.Height : cell.Width, cell.IsRotate ? cell.Width : cell.Height); }

        // --- CancelDrag (OnDroped(false) 호출) ---
        public bool CancelDrag()
        {
            if (!IsDragging()) return true;
            Debug.Log("[VariableInventoryCore.CancelDrag] 드래그 취소 시도...");
            if (originView != null)
            {
                Debug.Log($"[VariableInventoryCore.CancelDrag] Origin View ({((Object)originView).GetEntityId()})의 OnDroped(false) 호출 시도.");
            }
            else { Debug.LogWarning("[VariableInventoryCore.CancelDrag] Origin view is unknown!"); }
            RestoreOriginalRotation();
            foreach (var inventoryView in InventoryViews) inventoryView?.OnDroped(false);
            if (IsDetachedOwnedItem())
            {
                Debug.LogError("[VariableInventoryCore.CancelDrag] Rollback failed. Drag state was kept instead of discarding the item reference.");
                return false;
            }
            // effectCell 정리 및 상태 초기화
            if (effectCell != null) { if (effectCell.RectTransform != null) effectCell.RectTransform.gameObject.SetActive(false); effectCell.Apply(null); }
            originEffectCellRotate = null; stareCell = null; originView = null;
            Debug.Log("[VariableInventoryCore.CancelDrag] 드래그 취소 완료.");
            return true;
        }

        private void RestoreOriginalRotation()
        {
            if (!originEffectCellRotate.HasValue || effectCell?.CellData == null)
            {
                return;
            }

            effectCell.CellData.IsRotate = originEffectCellRotate.Value;
            effectCell.Apply(effectCell.CellData);
        }

        private bool IsDetachedOwnedItem()
        {
            return effectCell?.CellData is IVariableInventoryOwnedCellData owned &&
                   owned.InventoryOwner == null;
        }
    }
}
