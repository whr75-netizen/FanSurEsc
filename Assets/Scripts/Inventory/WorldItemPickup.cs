using FantasySurvival.Interaction;
using UnityEngine;
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
        private StandardStashViewData inventory;
        private InventoryItemData item;
        private SphereCollider interactionCollider;
        private Renderer itemRenderer;
        private bool transferInProgress;

        public StandardStashViewData Inventory => inventory;
        public InventoryItemData Item => item;
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

            inventory = candidate;
            item = detachedItem;
            gameObject.name = $"WorldItem_{detachedItem.Id}_{detachedItem.Definition.name}";
            ApplyTestColor(detachedItem.Id);
            error = null;
            return true;
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
