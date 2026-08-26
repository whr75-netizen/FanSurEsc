using FantasySurvival.Trading;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Merchant))]
    public sealed class MerchantInteractable : Interactable
    {
        [SerializeField] private string interactionPrompt = "상인 거래 열기 / 닫기";

        private Merchant merchant;
        private InventoryUIManager inventoryUI;

        public override string InteractionPrompt => string.IsNullOrWhiteSpace(interactionPrompt)
            ? "상인 거래 열기 / 닫기"
            : interactionPrompt;

        private void Awake()
        {
            merchant = GetComponent<Merchant>();
        }

        public override bool CanInteract(PlayerInteractor interactor)
        {
            return base.CanInteract(interactor) && merchant != null && merchant.isActiveAndEnabled;
        }

        public override void Interact(PlayerInteractor interactor)
        {
            InventoryUIManager resolved = ResolveInventoryUI(interactor);
            if (resolved == null || merchant == null)
            {
                Debug.LogWarning("Merchant interaction requires the Player InventoryUIManager.", this);
                return;
            }

            if (!merchant.TryResolveInventory(out var inventory, out string error))
            {
                Debug.LogError($"Could not open merchant '{merchant.MerchantId}': {error}", this);
                return;
            }

            resolved.TryToggleMerchantInventory(this, merchant, inventory);
        }

        public override bool IsInteractionActive(PlayerInteractor interactor)
        {
            InventoryUIManager resolved = ResolveInventoryUI(interactor);
            return resolved != null && resolved.IsMerchantOpen(this);
        }

        public override bool TryCancelInteraction(PlayerInteractor interactor)
        {
            InventoryUIManager resolved = ResolveInventoryUI(interactor);
            if (resolved == null || !resolved.IsMerchantOpen(this))
            {
                return true;
            }

            return resolved.CloseAllInventories();
        }

        private InventoryUIManager ResolveInventoryUI(PlayerInteractor interactor)
        {
            if (inventoryUI == null && interactor != null)
            {
                inventoryUI = interactor.GetComponent<InventoryUIManager>();
            }

            return inventoryUI;
        }

        private void OnDisable()
        {
            if (inventoryUI != null && inventoryUI.IsMerchantOpen(this))
            {
                inventoryUI.CloseAllInventories();
            }
        }
    }
}
