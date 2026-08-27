using FantasySurvival.Actions;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Chest))]
    public sealed class ChestInteractable : Interactable
    {
        private const string OpenChestActionId = "core:action:open_chest";

        [SerializeField] private string interactionPrompt = "Open / Close Chest";
        [SerializeField, Min(0f)] private float openActionDurationSeconds = 1f;

        private Chest chest;
        private InventoryUIManager inventoryUI;
        private PlayerActionController actionController;

        public override string InteractionPrompt => string.IsNullOrWhiteSpace(interactionPrompt)
            ? "Open / Close Chest"
            : interactionPrompt;
        public float OpenActionDurationSeconds => Mathf.Max(0f, openActionDurationSeconds);

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

            if (resolvedInventoryUI.IsChestOpen(chest))
            {
                resolvedInventoryUI.TryToggleChestInventory(chest);
                return;
            }

            PlayerActionController resolvedActionController = ResolveActionController(interactor);
            if (resolvedActionController == null)
            {
                Debug.LogWarning("Chest interaction requires PlayerActionController on the player.", this);
                return;
            }

            if (resolvedActionController.IsActionOwnedBy(this))
            {
                return;
            }

            resolvedActionController.TryBegin(
                OpenChestActionId,
                this,
                OpenActionDurationSeconds,
                () => CanContinueOpening(interactor),
                () => CompleteOpen(interactor));
        }

        public override bool IsInteractionActive(PlayerInteractor interactor)
        {
            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            PlayerActionController resolvedActionController = ResolveActionController(interactor);
            return (resolvedActionController != null && resolvedActionController.IsActionOwnedBy(this)) ||
                   (resolvedInventoryUI != null && resolvedInventoryUI.IsChestOpen(chest));
        }

        public override bool TryCancelInteraction(PlayerInteractor interactor)
        {
            PlayerActionController resolvedActionController = ResolveActionController(interactor);
            if (resolvedActionController != null && resolvedActionController.IsActionOwnedBy(this))
            {
                resolvedActionController.TryCancel(this);
            }

            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            if (resolvedInventoryUI == null || !resolvedInventoryUI.IsChestOpen(chest))
            {
                return true;
            }

            return resolvedInventoryUI.CloseAllInventories();
        }

        private bool CanContinueOpening(PlayerInteractor interactor)
        {
            InventoryUIManager resolvedInventoryUI = ResolveInventoryUI(interactor);
            return CanInteract(interactor) &&
                   interactor.IsWithinInteractionRange(transform) &&
                   resolvedInventoryUI != null &&
                   !resolvedInventoryUI.IsChestOpen(chest);
        }

        private void CompleteOpen(PlayerInteractor interactor)
        {
            if (!CanContinueOpening(interactor))
            {
                return;
            }

            ResolveInventoryUI(interactor)?.TryToggleChestInventory(chest);
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

        private PlayerActionController ResolveActionController(PlayerInteractor interactor)
        {
            if (interactor == null)
            {
                return actionController;
            }

            if (actionController == null || actionController.gameObject != interactor.gameObject)
            {
                actionController = interactor.GetComponent<PlayerActionController>();
            }

            return actionController;
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
            if (actionController != null && actionController.IsActionOwnedBy(this))
            {
                actionController.TryCancel(this);
            }

            if (inventoryUI != null && inventoryUI.IsChestOpen(chest))
            {
                inventoryUI.CloseAllInventories();
            }
        }
    }
}
