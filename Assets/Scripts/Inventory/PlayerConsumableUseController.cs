using System;
using FantasySurvival.Actions;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    /// <summary>
    /// Owns Player-side timed consumable use. Inventory quantity and health remain
    /// authoritative in PlayerInventoryState and PlayerStats respectively.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PlayerActionController))]
    [RequireComponent(typeof(PlayerStats))]
    public sealed class PlayerConsumableUseController : MonoBehaviour
    {
        private const string MedicineActionId = "item.medicine";

        private PlayerActionController actionController;
        private PlayerStats playerStats;
        private InventoryUIManager inventoryManager;

        private void Awake()
        {
            actionController = GetComponent<PlayerActionController>();
            playerStats = GetComponent<PlayerStats>();
            inventoryManager = GetComponent<InventoryUIManager>();
            if (actionController == null || playerStats == null || inventoryManager == null)
            {
                Debug.LogError(
                    $"{nameof(PlayerConsumableUseController)} on '{name}' has missing required references.",
                    this);
                enabled = false;
            }
        }

        private void OnDisable()
        {
            actionController?.TryCancel(
                this,
                PlayerActionCancelReason.ControllerDisabled);
        }

        public bool CanUseMedicine(InventoryItemData item)
        {
            return actionController != null &&
                   !actionController.IsActionOwnedBy(this) &&
                   TryCaptureMedicineUse(
                       item,
                       out _,
                       out _,
                       out _,
                       out _,
                       out _,
                       out _);
        }

        public bool TryBeginUseMedicine(
            InventoryItemData item,
            Action presentationRefresh,
            out string error)
        {
            if (actionController == null)
            {
                error = "The Player action controller is missing.";
                return false;
            }

            if (actionController.IsActionOwnedBy(this))
            {
                error = "A medicine use action is already in progress.";
                return false;
            }

            if (!TryCaptureMedicineUse(
                    item,
                    out PlayerInventoryState expectedPlayerState,
                    out StandardStashViewData expectedOwner,
                    out int expectedSlotIndex,
                    out int expectedQuantity,
                    out ItemDefinition definition,
                    out error))
            {
                return false;
            }

            if (actionController.IsBusy)
            {
                actionController.CancelActive(PlayerActionCancelReason.Requested);
            }

            float healingAmount = definition.MedicineHealthRestored;
            bool began = actionController.TryBegin(
                MedicineActionId,
                this,
                PlayerActionScope.Self,
                definition.MedicineUseDurationSeconds,
                () => CanContinueMedicineUse(
                    expectedPlayerState,
                    item,
                    expectedOwner,
                    expectedSlotIndex,
                    expectedQuantity),
                () => CompleteMedicineUse(
                    expectedPlayerState,
                    item,
                    expectedOwner,
                    expectedSlotIndex,
                    expectedQuantity,
                    healingAmount,
                    presentationRefresh));
            error = began ? null : "The medicine use action could not be started.";
            return began;
        }

        private bool TryCaptureMedicineUse(
            InventoryItemData item,
            out PlayerInventoryState playerState,
            out StandardStashViewData owner,
            out int slotIndex,
            out int quantity,
            out ItemDefinition definition,
            out string error)
        {
            playerState = inventoryManager != null ? inventoryManager.PlayerState : null;
            owner = null;
            slotIndex = -1;
            quantity = item?.Quantity ?? 0;
            definition = item?.Definition;
            if (!isActiveAndEnabled || actionController == null ||
                actionController.ActionsBlocked || playerStats == null ||
                inventoryManager == null || playerState == null || Time.timeScale <= 0f)
            {
                error = "The Player cannot use a consumable right now.";
                return false;
            }

            if (definition == null || !definition.IsMedicine || quantity <= 0 ||
                definition.MedicineUseDurationSeconds <= 0f ||
                definition.MedicineHealthRestored <= 0f)
            {
                error = "The requested item is not a valid medicine.";
                return false;
            }

            if (!playerStats.IsAlive ||
                playerStats.CurrentHealth >= playerStats.MaxHealth ||
                Mathf.Approximately(playerStats.CurrentHealth, playerStats.MaxHealth))
            {
                error = "The Player does not currently need healing.";
                return false;
            }

            return playerState.TryGetOwnedStackItemPlacement(
                item,
                out owner,
                out slotIndex,
                out error);
        }

        private bool CanContinueMedicineUse(
            PlayerInventoryState expectedPlayerState,
            InventoryItemData item,
            StandardStashViewData expectedOwner,
            int expectedSlotIndex,
            int expectedQuantity)
        {
            if (expectedPlayerState == null || item == null ||
                !ReferenceEquals(inventoryManager.PlayerState, expectedPlayerState) ||
                !playerStats.IsAlive ||
                playerStats.CurrentHealth >= playerStats.MaxHealth ||
                Mathf.Approximately(playerStats.CurrentHealth, playerStats.MaxHealth) ||
                !expectedPlayerState.TryGetOwnedStackItemPlacement(
                    item,
                    out StandardStashViewData actualOwner,
                    out int actualSlotIndex,
                    out _))
            {
                return false;
            }

            return ReferenceEquals(actualOwner, expectedOwner) &&
                   actualSlotIndex == expectedSlotIndex &&
                   item.Quantity == expectedQuantity &&
                   item.Definition != null && item.Definition.IsMedicine;
        }

        private void CompleteMedicineUse(
            PlayerInventoryState expectedPlayerState,
            InventoryItemData item,
            StandardStashViewData expectedOwner,
            int expectedSlotIndex,
            int expectedQuantity,
            float healingAmount,
            Action presentationRefresh)
        {
            if (!CanContinueMedicineUse(
                    expectedPlayerState,
                    item,
                    expectedOwner,
                    expectedSlotIndex,
                    expectedQuantity))
            {
                return;
            }

            if (!expectedPlayerState.TryConsumeOneOwnedStackItem(
                    item,
                    expectedOwner,
                    expectedSlotIndex,
                    expectedQuantity,
                    out string consumeError))
            {
                Debug.LogWarning($"Medicine consumption failed: {consumeError}", this);
                return;
            }

            playerStats.RestoreHealth(healingAmount);
            inventoryManager.RefreshPlayerItemPresentation(expectedPlayerState);
            try
            {
                presentationRefresh?.Invoke();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
            }
        }
    }
}
