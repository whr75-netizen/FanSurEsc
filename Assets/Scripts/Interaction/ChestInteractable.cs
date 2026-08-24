using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Chest))]
    public sealed class ChestInteractable : Interactable
    {
        [SerializeField] private string interactionPrompt = "Open / Close Chest";

        private Chest chest;
        private InventoryUIManager inventoryUI;

        public override string InteractionPrompt => string.IsNullOrWhiteSpace(interactionPrompt)
            ? "Open / Close Chest"
            : interactionPrompt;

        private void Awake()
        {
            ResolveChest();
        }

        private void OnEnable()
        {
            ResolveChest();
        }

        public override bool CanInteract(PlayerInteractor interactor)
        {
            return base.CanInteract(interactor) && chest != null &&
                   chest.isActiveAndEnabled && chest.chestInventoryData != null;
        }

        public override void Interact(PlayerInteractor interactor)
        {
            if (chest == null || interactor == null)
            {
                return;
            }

            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            if (resolvedInventoryUI == null)
            {
                Debug.LogWarning("Chest interaction requires InventoryUIManager on the player.", this);
                return;
            }

            resolvedInventoryUI.TryToggleChestInventory(chest);
        }

        public override bool IsInteractionActive(PlayerInteractor interactor)
        {
            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            return resolvedInventoryUI != null && resolvedInventoryUI.IsChestOpen(chest);
        }

        public override bool TryCancelInteraction(PlayerInteractor interactor)
        {
            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            if (resolvedInventoryUI == null || !resolvedInventoryUI.IsChestOpen(chest))
            {
                return true;
            }

            return resolvedInventoryUI.CloseAllInventories();
        }

        private InventoryUIManager ResolveInventoryUI(PlayerInteractor interactor)
        {
            if (inventoryUI != null)
            {
                return inventoryUI;
            }

            if (interactor != null)
            {
                inventoryUI = interactor.GetComponent<InventoryUIManager>();
            }

            return inventoryUI;
        }

        private void ResolveChest()
        {
            if (chest == null)
            {
                chest = GetComponent<Chest>();
            }
        }

        private void OnDisable()
        {
            if (inventoryUI != null && inventoryUI.IsChestOpen(chest))
            {
                inventoryUI.CloseAllInventories();
            }
        }
    }
}
