using System;
using System.Collections.Generic;
using FantasySurvival.SaveSystem;
using UnityEngine;

namespace FantasySurvival.Raids
{
    /// <summary>
    /// Stateless rule for the items carried by the Player when a raid ends.
    /// Base furniture is deliberately outside this policy and always remains safe.
    /// </summary>
    public static class RaidItemSettlementPolicy
    {
        public static bool DiscardsCarriedItems(RaidOutcome outcome)
        {
            return outcome == RaidOutcome.PlayerDied ||
                   outcome == RaidOutcome.Abandoned ||
                   outcome == RaidOutcome.RecoveryFailed;
        }

        public static bool TryDiscardCarriedItems(
            GameSaveData state,
            RaidOutcome outcome,
            out string error)
        {
            if (!DiscardsCarriedItems(outcome))
            {
                error = null;
                return true;
            }

            PlayerItemStateSaveData playerItems = state?.playerItems;
            if (playerItems == null ||
                !string.Equals(
                    playerItems.layoutId,
                    PlayerItemStateSaveData.FlatLayoutId,
                    StringComparison.Ordinal) ||
                playerItems.inventoryWidth <= 0 ||
                playerItems.inventoryHeight <= 0 ||
                playerItems.items == null ||
                playerItems.itemRecordCount < 0 ||
                playerItems.itemRecordCount != playerItems.items.Count)
            {
                error = "Raid settlement cannot discard a malformed Player item payload.";
                return false;
            }

            state.playerItems = new PlayerItemStateSaveData
            {
                layoutId = PlayerItemStateSaveData.FlatLayoutId,
                inventoryWidth = playerItems.inventoryWidth,
                inventoryHeight = playerItems.inventoryHeight,
                itemRecordCount = 0,
                items = new List<InventoryItemSaveData>()
            };
            state.playerInventory = null;
            error = null;
            return true;
        }
    }
}
