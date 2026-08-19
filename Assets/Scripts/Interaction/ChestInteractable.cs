using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Chest))]
    public sealed class ChestInteractable : Interactable
    {
        private Chest chest;

        public override string InteractionPrompt => "Open / Close Chest";

        private void Awake()
        {
            chest = GetComponent<Chest>();
        }

        public override void Interact(PlayerInteractor interactor)
        {
            if (chest == null || interactor == null)
            {
                return;
            }

            var inventoryUI = interactor.GetComponent<InventoryUIManager>();
            if (inventoryUI == null)
            {
                Debug.LogWarning("Chest interaction requires InventoryUIManager on the player.", this);
                return;
            }

            inventoryUI.TryToggleChestInventory(chest);
        }
    }
}
