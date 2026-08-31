using System;
using System.Collections.Generic;
using FantasySurvival.Interaction;
using UnityEngine;
using UnityEngine.SceneManagement;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    /// <summary>
    /// Implemented by the Player's existing inventory authority. The pickup owns no
    /// input and only forwards the common Interact request through this boundary.
    /// </summary>
    public interface IWorldItemPickupReceiver
    {
        bool TryPickupWorldItem(WorldItemPickup pickup, out string error);
    }

    [DisallowMultipleComponent]
    [RequireComponent(typeof(SphereCollider))]
    public sealed class WorldItemPickup : Interactable
    {
        // Derived lookup only: each pickup's StandardStashViewData remains the sole
        // item-state owner, and the GameObject's Scene remains its lifetime owner.
        private static readonly HashSet<WorldItemPickup> ActivePickups =
            new HashSet<WorldItemPickup>();

        private StandardStashViewData inventory;
        private InventoryItemData item;
        private string stableId;
        private SphereCollider interactionCollider;
        private Renderer itemRenderer;
        private bool transferInProgress;

        public StandardStashViewData Inventory => inventory;
        public InventoryItemData Item => item;
        public string StableId => stableId;
        public bool IsEmpty => inventory == null || item == null ||
                               !ReferenceEquals(item.InventoryOwner, inventory) ||
                               !inventory.GetId(item).HasValue;

        public override string InteractionPrompt
        {
            get
            {
                if (item?.Definition == null)
                {
                    return "아이템 줍기";
                }

                string displayName = string.IsNullOrWhiteSpace(item.Definition.DisplayName)
                    ? item.Definition.name
                    : item.Definition.DisplayName;
                return item.Quantity > 1
                    ? $"{displayName} 줍기 ({item.Quantity}개)"
                    : $"{displayName} 줍기";
            }
        }

        private void Awake()
        {
            EnsurePresentation();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetRuntimeIndex()
        {
            ActivePickups.Clear();
        }

        private void OnEnable()
        {
            if (item == null || inventory == null)
            {
                return;
            }

            if (!TryRegisterActive(out string error))
            {
                Debug.LogError(error, this);
                enabled = false;
            }
        }

        private void OnDisable()
        {
            ActivePickups.Remove(this);
        }

        private void OnDestroy()
        {
            ActivePickups.Remove(this);
        }

        public bool TryInitialize(InventoryItemData detachedItem, out string error)
        {
            if (detachedItem == null || detachedItem.Definition == null)
            {
                error = "바닥에 놓을 runtime 아이템이 없습니다.";
                return false;
            }

            if (item != null || inventory != null)
            {
                error = "바닥 아이템 오브젝트가 이미 초기화되었습니다.";
                return false;
            }

            if (detachedItem.InventoryOwner != null)
            {
                error = "바닥에 놓을 아이템이 아직 다른 컨테이너에 속해 있습니다.";
                return false;
            }

            int footprintWidth = detachedItem.IsRotate
                ? detachedItem.Height
                : detachedItem.Width;
            int footprintHeight = detachedItem.IsRotate
                ? detachedItem.Width
                : detachedItem.Height;
            if (!InventoryGridConstraints.TryValidateDimensions(
                    footprintWidth,
                    footprintHeight,
                    out error))
            {
                return false;
            }

            EnsurePresentation();
            var candidate = new StandardStashViewData(
                footprintWidth,
                footprintHeight);
            int? slot = candidate.GetInsertableId(detachedItem);
            if (!slot.HasValue)
            {
                error = "바닥 아이템의 논리 소유 공간을 만들 수 없습니다.";
                return false;
            }

            try
            {
                candidate.InsertInventoryItem(slot.Value, detachedItem);
            }
            catch (System.Exception exception)
            {
                error = $"바닥 아이템 소유권을 연결하지 못했습니다: {exception.Message}";
                return false;
            }

            if (TryInitializeOwned(
                    Guid.NewGuid().ToString("D"),
                    candidate,
                    detachedItem,
                    out error))
            {
                return true;
            }

            // The detached runtime item must remain rollback-compatible if a future
            // initialization rule rejects the provisional world owner.
            if (ReferenceEquals(detachedItem.InventoryOwner, candidate) &&
                candidate.GetId(detachedItem).HasValue)
            {
                candidate.InsertInventoryItem(slot.Value, null);
            }
            return false;
        }

        internal bool TryInitializeRestored(
            string restoredStableId,
            StandardStashViewData restoredInventory,
            out string error)
        {
            if (!TryGetSingleOwnedItem(
                    restoredInventory,
                    out InventoryItemData restoredItem,
                    out error))
            {
                return false;
            }

            return TryInitializeOwned(
                restoredStableId,
                restoredInventory,
                restoredItem,
                out error);
        }

        internal bool TryActivate(out string error)
        {
            if (string.IsNullOrWhiteSpace(stableId) || IsEmpty)
            {
                error = "활성화할 바닥 아이템의 ID 또는 소유권이 없습니다.";
                return false;
            }

            if (!CanRegisterStableId(stableId, gameObject.scene, this, out error))
            {
                return false;
            }

            try
            {
                enabled = true;
                gameObject.SetActive(true);
            }
            catch (Exception exception)
            {
                error = $"바닥 아이템 표시를 활성화하지 못했습니다: {exception.Message}";
                return false;
            }

            if (!isActiveAndEnabled)
            {
                error = "바닥 아이템 오브젝트가 활성 상태가 되지 않았습니다.";
                return false;
            }

            // OnEnable performs the normal Play Mode registration. Explicitly close
            // the same contract here as well so editor validation and unusual Unity
            // activation ordering cannot leave an active pickup outside the index.
            if (!ActivePickups.Contains(this) && !TryRegisterActive(out error))
            {
                return false;
            }

            error = null;
            return true;
        }

        internal static bool TryGetActiveItems(
            Scene scene,
            List<WorldItemPickup> output,
            out string error)
        {
            error = null;
            if (output == null)
            {
                error = "바닥 아이템 조회 결과 목록이 없습니다.";
                return false;
            }

            output.Clear();
            if (!scene.IsValid() || !scene.isLoaded)
            {
                error = "바닥 아이템을 조회할 scene이 유효하지 않습니다.";
                return false;
            }

            RemoveDestroyedPickups();
            var stableIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (WorldItemPickup pickup in ActivePickups)
            {
                if (pickup == null || pickup.gameObject.scene != scene ||
                    !pickup.isActiveAndEnabled || !pickup.gameObject.activeInHierarchy ||
                    pickup.IsEmpty)
                {
                    continue;
                }

                if (!Guid.TryParse(pickup.stableId, out _) ||
                    !stableIds.Add(pickup.stableId) ||
                    !TryGetSingleOwnedItem(pickup.inventory, out InventoryItemData ownedItem, out error) ||
                    !ReferenceEquals(ownedItem, pickup.item))
                {
                    if (error == null)
                    {
                        error = "현재 scene의 바닥 아이템 ID 또는 단일 소유권이 올바르지 않습니다.";
                    }
                    output.Clear();
                    return false;
                }

                output.Add(pickup);
            }

            output.Sort((left, right) =>
                string.CompareOrdinal(left.stableId, right.stableId));
            error = null;
            return true;
        }

        internal static bool TryGetSingleOwnedItem(
            StandardStashViewData owner,
            out InventoryItemData ownedItem,
            out string error)
        {
            ownedItem = null;
            error = null;
            if (owner?.CellData == null ||
                !InventoryGridConstraints.TryValidateDimensions(
                    owner.CapacityWidth,
                    owner.CapacityHeight,
                    out error))
            {
                if (error == null)
                {
                    error = "바닥 아이템의 owner grid가 없습니다.";
                }
                return false;
            }

            foreach (IVariableInventoryCellData cell in owner.CellData)
            {
                if (cell == null)
                {
                    continue;
                }

                if (!(cell is InventoryItemData inventoryItem))
                {
                    error = "바닥 owner grid에 지원하지 않는 item 데이터가 있습니다.";
                    return false;
                }

                if (ownedItem != null && !ReferenceEquals(ownedItem, inventoryItem))
                {
                    error = "바닥 owner grid에는 root item이 정확히 하나만 있어야 합니다.";
                    return false;
                }

                ownedItem = inventoryItem;
            }

            if (ownedItem == null ||
                !ReferenceEquals(ownedItem.InventoryOwner, owner) ||
                owner.GetId(ownedItem) != 0)
            {
                error = "바닥 owner grid의 root item 소유권 또는 slot이 올바르지 않습니다.";
                return false;
            }

            int expectedWidth = ownedItem.IsRotate ? ownedItem.Height : ownedItem.Width;
            int expectedHeight = ownedItem.IsRotate ? ownedItem.Width : ownedItem.Height;
            if (owner.CapacityWidth != expectedWidth || owner.CapacityHeight != expectedHeight)
            {
                error = "바닥 owner grid가 item의 현재 회전 footprint와 정확히 일치하지 않습니다.";
                return false;
            }

            error = null;
            return true;
        }

        private bool TryInitializeOwned(
            string candidateStableId,
            StandardStashViewData candidateInventory,
            InventoryItemData candidateItem,
            out string error)
        {
            error = null;
            if (item != null || inventory != null || !string.IsNullOrEmpty(stableId))
            {
                error = "바닥 아이템 오브젝트가 이미 초기화되었습니다.";
                return false;
            }

            if (!Guid.TryParse(candidateStableId, out _) ||
                !TryGetSingleOwnedItem(candidateInventory, out InventoryItemData ownedItem, out error) ||
                !ReferenceEquals(ownedItem, candidateItem))
            {
                if (error == null)
                {
                    error = "바닥 아이템의 stable ID 또는 단일 소유권이 올바르지 않습니다.";
                }
                return false;
            }

            if (isActiveAndEnabled &&
                !CanRegisterStableId(candidateStableId, gameObject.scene, this, out error))
            {
                return false;
            }

            EnsurePresentation();
            stableId = candidateStableId;
            inventory = candidateInventory;
            item = candidateItem;
            gameObject.name = $"WorldItem_{candidateItem.Id}_{candidateItem.Definition.name}_{stableId}";
            ApplyTestColor(candidateItem.Id);

            if (isActiveAndEnabled && !TryRegisterActive(out error))
            {
                stableId = null;
                inventory = null;
                item = null;
                return false;
            }

            error = null;
            return true;
        }

        private bool TryRegisterActive(out string error)
        {
            if (!CanRegisterStableId(stableId, gameObject.scene, this, out error))
            {
                return false;
            }

            ActivePickups.Add(this);
            error = null;
            return true;
        }

        private static bool CanRegisterStableId(
            string candidateStableId,
            Scene scene,
            WorldItemPickup candidate,
            out string error)
        {
            if (!Guid.TryParse(candidateStableId, out _) ||
                !scene.IsValid() || !scene.isLoaded)
            {
                error = "바닥 아이템의 stable ID 또는 scene 소유권이 유효하지 않습니다.";
                return false;
            }

            RemoveDestroyedPickups();
            foreach (WorldItemPickup existing in ActivePickups)
            {
                if (existing != null && existing != candidate &&
                    existing.gameObject.scene == scene &&
                    string.Equals(existing.stableId, candidateStableId, StringComparison.Ordinal))
                {
                    error = $"scene에 바닥 아이템 stable ID '{candidateStableId}'가 중복되었습니다.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static void RemoveDestroyedPickups()
        {
            ActivePickups.RemoveWhere(pickup => pickup == null);
        }

        public override bool CanInteract(PlayerInteractor interactor)
        {
            return !transferInProgress && !IsEmpty && base.CanInteract(interactor);
        }

        public override void Interact(PlayerInteractor interactor)
        {
            if (!CanInteract(interactor) || interactor == null)
            {
                return;
            }

            IWorldItemPickupReceiver receiver =
                interactor.GetComponent<IWorldItemPickupReceiver>();
            if (receiver == null)
            {
                Debug.LogWarning(
                    "바닥 아이템을 받을 Player 인벤토리 경계가 없습니다.",
                    this);
                return;
            }

            transferInProgress = true;
            if (!receiver.TryPickupWorldItem(this, out string error))
            {
                transferInProgress = false;
                if (!string.IsNullOrEmpty(error))
                {
                    Debug.LogWarning($"아이템 습득 실패: {error}", this);
                }
                return;
            }

            if (IsEmpty)
            {
                DisableInteractionImmediately();
                Destroy(gameObject);
                return;
            }

            // A stack transfer may fill existing Player stacks while leaving a
            // smaller remainder in this same world owner.
            transferInProgress = false;
        }

        private void EnsurePresentation()
        {
            if (interactionCollider == null)
            {
                interactionCollider = GetComponent<SphereCollider>();
            }

            if (interactionCollider != null)
            {
                interactionCollider.isTrigger = true;
                interactionCollider.radius = 0.5f;
            }

            if (itemRenderer == null)
            {
                itemRenderer = GetComponent<Renderer>();
            }
        }

        private void ApplyTestColor(int definitionId)
        {
            if (itemRenderer == null)
            {
                return;
            }

            float hue = Mathf.Repeat(definitionId * 0.61803398875f, 1f);
            Color color = Color.HSVToRGB(hue, 0.55f, 0.9f);
            var properties = new MaterialPropertyBlock();
            itemRenderer.GetPropertyBlock(properties);
            properties.SetColor("_BaseColor", color);
            properties.SetColor("_Color", color);
            itemRenderer.SetPropertyBlock(properties);
        }

        private void DisableInteractionImmediately()
        {
            if (interactionCollider != null)
            {
                interactionCollider.enabled = false;
            }

            if (itemRenderer != null)
            {
                itemRenderer.enabled = false;
            }
        }
    }
}
