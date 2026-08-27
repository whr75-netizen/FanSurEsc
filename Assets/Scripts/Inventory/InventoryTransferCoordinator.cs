using System;
using System.Collections.Generic;
using FantasySurvival.Trading;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public enum ExternalInventoryMode
    {
        None = 0,
        Storage = 1,
        Merchant = 2
    }

    public sealed class InventoryStackSplitTransaction
    {
        private enum TransactionState
        {
            Pending,
            Committed,
            RolledBack
        }

        private readonly InventoryItemData sourceItem;
        private readonly IVariableInventoryViewData sourceOwner;
        private readonly int initialSplitQuantity;
        private int expectedSourceQuantity;
        private int outstandingQuantity;
        private int committedMergeQuantity;
        private TransactionState state;

        internal InventoryStackSplitTransaction(
            InventoryItemData sourceItem,
            IVariableInventoryViewData sourceOwner,
            InventoryItemData splitItem,
            int originalQuantity,
            int remainingQuantity)
        {
            this.sourceItem = sourceItem;
            this.sourceOwner = sourceOwner;
            SplitItem = splitItem;
            initialSplitQuantity = originalQuantity - remainingQuantity;
            expectedSourceQuantity = remainingQuantity;
            outstandingQuantity = initialSplitQuantity;
        }

        public InventoryItemData SplitItem { get; }

        public bool TryCommit(out string error)
        {
            if (state == TransactionState.Committed)
            {
                error = null;
                return true;
            }

            if (state != TransactionState.Pending)
            {
                error = "The stack split was already rolled back.";
                return false;
            }

            if (sourceOwner == null ||
                !ReferenceEquals(sourceItem.InventoryOwner, sourceOwner) ||
                sourceItem.Quantity != expectedSourceQuantity ||
                !sourceOwner.GetId(sourceItem).HasValue)
            {
                error = "The source stack changed before the split could be committed.";
                return false;
            }

            IVariableInventoryViewData splitOwner = SplitItem?.InventoryOwner;
            if (SplitItem == null || splitOwner == null ||
                !splitOwner.GetId(SplitItem).HasValue)
            {
                error = "The split stack was not attached to a destination inventory.";
                return false;
            }

            state = TransactionState.Committed;
            error = null;
            return true;
        }

        public bool TryRecordStackMerge(
            InventoryItemData targetItem,
            int movedQuantity,
            int remainingCarriedQuantity,
            out string error)
        {
            if (state != TransactionState.Pending)
            {
                error = "The stack split is no longer pending.";
                return false;
            }

            if (targetItem == null || movedQuantity <= 0 || remainingCarriedQuantity < 0 ||
                movedQuantity + remainingCarriedQuantity != outstandingQuantity ||
                SplitItem == null || SplitItem.InventoryOwner != null)
            {
                error = "The stack merge does not match the outstanding split quantity.";
                return false;
            }

            int expectedDetachedQuantity = remainingCarriedQuantity > 0
                ? remainingCarriedQuantity
                : outstandingQuantity;
            if (SplitItem.Quantity != expectedDetachedQuantity)
            {
                error = "The detached split quantity changed during stack merge.";
                return false;
            }

            int sourceQuantityAfterMerge = expectedSourceQuantity +
                                           (ReferenceEquals(targetItem, sourceItem)
                                               ? movedQuantity
                                               : 0);
            if (sourceOwner == null ||
                !ReferenceEquals(sourceItem.InventoryOwner, sourceOwner) ||
                sourceItem.Quantity != sourceQuantityAfterMerge ||
                !sourceOwner.GetId(sourceItem).HasValue)
            {
                error = "The source stack changed during stack merge.";
                return false;
            }

            int mergedQuantityAfter = committedMergeQuantity + movedQuantity;
            if (mergedQuantityAfter > initialSplitQuantity)
            {
                error = "The merged quantity exceeded the original split quantity.";
                return false;
            }

            expectedSourceQuantity = sourceQuantityAfterMerge;
            committedMergeQuantity = mergedQuantityAfter;
            outstandingQuantity = remainingCarriedQuantity;

            if (outstandingQuantity == 0)
            {
                state = TransactionState.Committed;
            }

            error = null;
            return true;
        }

        public bool TryRollback(out string error)
        {
            if (state == TransactionState.RolledBack)
            {
                error = null;
                return true;
            }

            if (state != TransactionState.Pending)
            {
                error = "A committed stack split cannot be rolled back.";
                return false;
            }

            if (SplitItem == null || SplitItem.InventoryOwner != null ||
                SplitItem.Quantity != outstandingQuantity)
            {
                error = "The split stack is no longer detached from an inventory.";
                return false;
            }

            int restoredQuantity = expectedSourceQuantity + outstandingQuantity;
            if (!sourceItem.TryChangeQuantity(
                    sourceOwner,
                    expectedSourceQuantity,
                    restoredQuantity,
                    out error))
            {
                return false;
            }

            state = TransactionState.RolledBack;
            return true;
        }
    }

    /// <summary>
    /// Coordinates cross-container moves without becoming another inventory owner.
    /// Every mutation still goes through the authoritative source/destination data APIs.
    /// </summary>
    public sealed class InventoryTransferCoordinator : IVariableInventoryTransferController
    {
        private readonly Action refreshViews;
        private readonly Action<string, bool> reportStatus;

        private PlayerInventoryState playerState;
        private ExternalInventoryMode externalMode;
        private StandardStashViewData externalInventory;

        private struct TransferReceipt
        {
            public IVariableInventoryViewData Source;
            public IVariableInventoryViewData Destination;
            public IVariableInventoryCellData Item;
            public int SourceIndex;
            public int DestinationIndex;
        }

        private sealed class StackMergeReceipt : IVariableInventoryStackMergeReceipt
        {
            private readonly InventoryItemData targetItem;
            private readonly IVariableInventoryViewData targetOwner;
            private readonly InventoryItemData carriedItem;
            private readonly int targetQuantityBefore;
            private readonly int targetQuantityAfter;
            private readonly int carriedQuantityBefore;
            private readonly int carriedQuantityAfter;
            private readonly bool carriedQuantityChanged;
            private readonly bool requireCarriedOriginalState;
            private bool targetRolledBack;
            private bool carriedRolledBack;
            private bool rolledBack;

            public StackMergeReceipt(
                InventoryItemData targetItem,
                IVariableInventoryViewData targetOwner,
                InventoryItemData carriedItem,
                int targetQuantityBefore,
                int targetQuantityAfter,
                int carriedQuantityBefore,
                int carriedQuantityAfter,
                bool carriedQuantityChanged,
                bool targetAlreadyRolledBack = false,
                bool requireCarriedOriginalState = false)
            {
                this.targetItem = targetItem;
                this.targetOwner = targetOwner;
                this.carriedItem = carriedItem;
                this.targetQuantityBefore = targetQuantityBefore;
                this.targetQuantityAfter = targetQuantityAfter;
                this.carriedQuantityBefore = carriedQuantityBefore;
                this.carriedQuantityAfter = carriedQuantityAfter;
                this.carriedQuantityChanged = carriedQuantityChanged;
                this.requireCarriedOriginalState = requireCarriedOriginalState;
                targetRolledBack = targetAlreadyRolledBack;
            }

            public IVariableInventoryCellData TargetItem => targetItem;
            public int MovedQuantity => targetQuantityAfter - targetQuantityBefore;
            public int RemainingQuantity => carriedQuantityAfter;

            public bool TryRollback(out string error)
            {
                if (rolledBack)
                {
                    error = null;
                    return true;
                }

                if (!targetRolledBack)
                {
                    if (targetItem.Quantity == targetQuantityBefore &&
                        ReferenceEquals(targetItem.InventoryOwner, targetOwner))
                    {
                        targetRolledBack = true;
                    }
                    else if (!targetItem.TryChangeQuantity(
                                 targetOwner,
                                 targetQuantityAfter,
                                 targetQuantityBefore,
                                 out error))
                    {
                        return false;
                    }
                    else
                    {
                        targetRolledBack = true;
                    }
                }

                if (carriedQuantityChanged && !carriedRolledBack)
                {
                    if (carriedItem.Quantity == carriedQuantityBefore &&
                        carriedItem.InventoryOwner == null)
                    {
                        carriedRolledBack = true;
                    }
                    else if (!carriedItem.TryChangeQuantity(
                                 null,
                                 carriedQuantityAfter,
                                 carriedQuantityBefore,
                                 out error))
                    {
                        // Keep the target rollback applied. A later retry can finish
                        // restoring the carried quantity without re-mutating target.
                        return false;
                    }
                    else
                    {
                        carriedRolledBack = true;
                    }
                }

                if (requireCarriedOriginalState &&
                    (carriedItem.InventoryOwner != null ||
                     carriedItem.Quantity != carriedQuantityBefore))
                {
                    error = "The carried stack changed during merge failure recovery.";
                    return false;
                }

                rolledBack = true;
                error = null;
                return true;
            }
        }

        public InventoryTransferCoordinator(
            PlayerInventoryState playerState,
            Action refreshViews,
            Action<string, bool> reportStatus)
        {
            this.playerState = playerState ?? throw new ArgumentNullException(nameof(playerState));
            this.refreshViews = refreshViews;
            this.reportStatus = reportStatus;
        }

        public void SetPlayerState(PlayerInventoryState state)
        {
            playerState = state ?? throw new ArgumentNullException(nameof(state));
        }

        public void SetExternalSession(
            ExternalInventoryMode mode,
            StandardStashViewData inventory)
        {
            externalMode = mode;
            externalInventory = inventory;
        }

        public void ClearExternalSession()
        {
            externalMode = ExternalInventoryMode.None;
            externalInventory = null;
        }

        public bool TryBeginStackSplit(
            IVariableInventoryView sourceView,
            InventoryItemData sourceItem,
            int splitQuantity,
            out InventoryStackSplitTransaction transaction,
            out string error)
        {
            transaction = null;
            if (externalMode == ExternalInventoryMode.Merchant)
            {
                error = "상인 거래 중에는 stack 가격 정책이 확정되지 않아 분할할 수 없습니다.";
                return false;
            }

            if (!(sourceView is IVariableInventoryBoundView boundView) || sourceItem == null)
            {
                error = "분할할 아이템의 원본 인벤토리를 찾을 수 없습니다.";
                return false;
            }

            if (sourceView is StandardStashView stashView &&
                !stashView.IsItemVisible(sourceItem))
            {
                error = "현재 숨겨진 아이템은 분할할 수 없습니다.";
                return false;
            }

            IVariableInventoryViewData sourceOwner = boundView.ViewData;
            int originalQuantity = sourceItem.Quantity;
            if (sourceOwner == null ||
                !ReferenceEquals(sourceItem.InventoryOwner, sourceOwner) ||
                !sourceOwner.GetId(sourceItem).HasValue)
            {
                error = "아이템 소유권이 원본 인벤토리와 일치하지 않습니다.";
                return false;
            }

            if (sourceItem.MaxStackSize <= 1 || splitQuantity <= 0 ||
                splitQuantity >= originalQuantity)
            {
                error = $"나눌 수량은 1부터 {Mathf.Max(0, originalQuantity - 1)}까지여야 합니다.";
                return false;
            }

            if (!InventoryItemDataFactory.TryCreate(
                    sourceItem.Definition,
                    splitQuantity,
                    out IVariableInventoryCellData created,
                    out error) ||
                !(created is InventoryItemData splitItem))
            {
                error = error ?? "분할 아이템을 생성할 수 없습니다.";
                return false;
            }

            splitItem.IsRotate = sourceItem.IsRotate;
            int remainingQuantity = originalQuantity - splitQuantity;
            if (!sourceItem.TryChangeQuantity(
                    sourceOwner,
                    originalQuantity,
                    remainingQuantity,
                    out error))
            {
                return false;
            }

            transaction = new InventoryStackSplitTransaction(
                sourceItem,
                sourceOwner,
                splitItem,
                originalQuantity,
                remainingQuantity);
            error = null;
            return true;
        }

        public bool HandleQuickTransfer(
            IVariableInventoryView sourceView,
            IVariableInventoryCellData item)
        {
            if (externalMode == ExternalInventoryMode.None || externalInventory == null ||
                !(sourceView is IVariableInventoryBoundView boundView) || item == null)
            {
                return false;
            }

            if (sourceView is StandardStashView stashView && !stashView.IsItemVisible(item))
            {
                return true;
            }

            IVariableInventoryViewData source = boundView.ViewData;
            bool sourceIsPlayer = IsPlayerOwned(source);
            bool sourceIsExternal = IsNestedIn(externalInventory, source);

            if (externalMode == ExternalInventoryMode.Storage)
            {
                if (sourceIsPlayer)
                {
                    TryQuickMove(source, externalInventory, item, "보관");
                    return true;
                }

                if (sourceIsExternal)
                {
                    TryQuickMove(source, playerState.Inventory, item, "습득");
                    return true;
                }

                return false;
            }

            if (externalMode == ExternalInventoryMode.Merchant)
            {
                if (sourceIsExternal)
                {
                    TryQuickPurchase(source, item);
                    return true;
                }

                if (sourceIsPlayer)
                {
                    TryQuickSale(source, item);
                    return true;
                }
            }

            return false;
        }

        public VariableInventoryDropHandling GetDropHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item)
        {
            return EvaluateDropHandling(sourceView, destinationView, item, true);
        }

        public VariableInventoryDropHandling GetDropPreviewHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item)
        {
            return EvaluateDropHandling(sourceView, destinationView, item, false);
        }

        public bool CanMergeStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item)
        {
            if (sourceView == null ||
                !(destinationView is IVariableInventoryBoundView destinationBound) ||
                !destinationBound.ContainsCell(destinationCell) ||
                !(item is InventoryItemData carriedItem) ||
                !(destinationCell?.CellData is InventoryItemData targetItem) ||
                ReferenceEquals(carriedItem, targetItem) || carriedItem.InventoryOwner != null ||
                carriedItem.MaxStackSize <= 1 ||
                carriedItem.Id != targetItem.Id ||
                carriedItem.MaxStackSize != targetItem.MaxStackSize ||
                targetItem.Quantity >= targetItem.MaxStackSize)
            {
                return false;
            }

            IVariableInventoryViewData targetOwner = destinationBound.ViewData;
            if (targetOwner == null ||
                !ReferenceEquals(targetItem.InventoryOwner, targetOwner) ||
                !targetOwner.GetId(targetItem).HasValue)
            {
                return false;
            }

            if (externalMode != ExternalInventoryMode.Merchant)
            {
                return true;
            }

            if (externalInventory == null ||
                !(sourceView is IVariableInventoryBoundView sourceBound))
            {
                return false;
            }

            IVariableInventoryViewData sourceOwner = sourceBound.ViewData;
            bool samePlayerSide = IsPlayerOwned(sourceOwner) && IsPlayerOwned(targetOwner);
            bool sameMerchantSide = IsNestedIn(externalInventory, sourceOwner) &&
                                    IsNestedIn(externalInventory, targetOwner);
            return samePlayerSide || sameMerchantSide;
        }

        public bool TryMergeStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            out IVariableInventoryStackMergeReceipt receipt,
            out string error)
        {
            receipt = null;
            error = null;
            if (!CanMergeStack(sourceView, destinationView, destinationCell, item) ||
                !(destinationView is IVariableInventoryBoundView destinationBound) ||
                !(item is InventoryItemData carriedItem) ||
                !(destinationCell.CellData is InventoryItemData targetItem))
            {
                error = "The selected cells cannot merge these stacks.";
                return false;
            }

            IVariableInventoryViewData targetOwner = destinationBound.ViewData;
            int targetBefore = targetItem.Quantity;
            int carriedBefore = carriedItem.Quantity;
            int movedQuantity = Mathf.Min(
                carriedBefore,
                targetItem.MaxStackSize - targetBefore);
            int targetAfter = targetBefore + movedQuantity;
            int carriedAfter = carriedBefore - movedQuantity;

            if (movedQuantity <= 0 ||
                !targetItem.TryChangeQuantity(
                    targetOwner,
                    targetBefore,
                    targetAfter,
                    out error))
            {
                error = error ?? "There is no room in the destination stack.";
                return false;
            }

            bool carriedChanged = carriedAfter > 0;
            if (carriedChanged &&
                !carriedItem.TryChangeQuantity(
                    null,
                    carriedBefore,
                    carriedAfter,
                    out string carriedError))
            {
                bool carriedStillOriginal = carriedItem.InventoryOwner == null &&
                                            carriedItem.Quantity == carriedBefore;
                bool targetRollbackSucceeded = targetItem.TryChangeQuantity(
                    targetOwner,
                    targetAfter,
                    targetBefore,
                    out string rollbackError);
                if (!targetRollbackSucceeded &&
                    targetItem.Quantity == targetBefore &&
                    ReferenceEquals(targetItem.InventoryOwner, targetOwner))
                {
                    targetRollbackSucceeded = true;
                }

                if (targetRollbackSucceeded && carriedStillOriginal)
                {
                    error = carriedError;
                    return false;
                }

                receipt = new StackMergeReceipt(
                    targetItem,
                    targetOwner,
                    carriedItem,
                    targetBefore,
                    targetAfter,
                    carriedBefore,
                    carriedBefore,
                    false,
                    targetRollbackSucceeded,
                    true);
                error = targetRollbackSucceeded
                    ? $"{carriedError} The carried stack no longer matches its original state."
                    : $"{carriedError} Target rollback also failed: {rollbackError}";
                return false;
            }

            receipt = new StackMergeReceipt(
                targetItem,
                targetOwner,
                carriedItem,
                targetBefore,
                targetAfter,
                carriedBefore,
                carriedAfter,
                carriedChanged);
            error = null;
            return true;
        }

        private VariableInventoryDropHandling EvaluateDropHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item,
            bool reportFailure)
        {
            if (externalMode != ExternalInventoryMode.Merchant || externalInventory == null)
            {
                return VariableInventoryDropHandling.Standard;
            }

            if (!(sourceView is IVariableInventoryBoundView sourceBound) ||
                !(destinationView is IVariableInventoryBoundView destinationBound) ||
                !(item is InventoryItemData inventoryItem))
            {
                return VariableInventoryDropHandling.Reject;
            }

            IVariableInventoryViewData source = sourceBound.ViewData;
            IVariableInventoryViewData destination = destinationBound.ViewData;
            bool sourceIsPlayer = IsPlayerOwned(source);
            bool sourceIsMerchant = IsNestedIn(externalInventory, source);
            bool destinationIsPlayer = IsPlayerOwned(destination);
            bool destinationIsMerchant = IsNestedIn(externalInventory, destination);

            if (sourceIsMerchant && destinationIsMerchant)
            {
                return VariableInventoryDropHandling.Standard;
            }

            if (sourceIsPlayer && destinationIsPlayer)
            {
                return VariableInventoryDropHandling.Standard;
            }

            if (sourceIsPlayer && destinationIsMerchant)
            {
                if (!TryValidateTradeItem(inventoryItem, out string error) ||
                    !playerState.Wallet.CanCredit(
                        inventoryItem.Definition.TradeCurrency,
                        inventoryItem.Definition.TradePrice))
                {
                    if (reportFailure)
                    {
                        Report(error ?? "화폐 보유 한도를 초과하여 판매할 수 없습니다.", true);
                    }
                    return VariableInventoryDropHandling.Reject;
                }

                // A merchant sale is a deliberate sink. It does not consume a merchant
                // grid slot and the Player is paid only in OnDropCompleted.
                return VariableInventoryDropHandling.AcceptWithoutInsert;
            }

            if (sourceIsMerchant && destinationIsPlayer)
            {
                if (!TryValidateTradeItem(inventoryItem, out string error))
                {
                    if (reportFailure)
                    {
                        Report(error, true);
                    }
                    return VariableInventoryDropHandling.Reject;
                }

                if (!playerState.Wallet.CanSpend(
                        inventoryItem.Definition.TradeCurrency,
                        inventoryItem.Definition.TradePrice))
                {
                    if (reportFailure)
                    {
                        Report($"{GetCurrencyName(inventoryItem.Definition.TradeCurrency)}이 부족합니다.", true);
                    }
                    return VariableInventoryDropHandling.Reject;
                }

                return VariableInventoryDropHandling.Standard;
            }

            return VariableInventoryDropHandling.Reject;
        }

        public void OnDropCompleted(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item,
            VariableInventoryDropHandling handling)
        {
            if (externalMode != ExternalInventoryMode.Merchant || externalInventory == null ||
                !(sourceView is IVariableInventoryBoundView sourceBound) ||
                !(destinationView is IVariableInventoryBoundView destinationBound) ||
                !(item is InventoryItemData inventoryItem))
            {
                refreshViews?.Invoke();
                return;
            }

            bool sourceIsPlayer = IsPlayerOwned(sourceBound.ViewData);
            bool sourceIsMerchant = IsNestedIn(externalInventory, sourceBound.ViewData);
            bool destinationIsPlayer = IsPlayerOwned(destinationBound.ViewData);
            bool destinationIsMerchant = IsNestedIn(externalInventory, destinationBound.ViewData);
            TradeCurrency currency = inventoryItem.Definition.TradeCurrency;
            int price = inventoryItem.Definition.TradePrice;

            if (sourceIsMerchant && destinationIsPlayer)
            {
                if (!playerState.Wallet.TrySpend(currency, price))
                {
                    Debug.LogError(
                        "Merchant purchase completed without its prevalidated Player payment. " +
                        "The wallet has an unexpected competing writer.");
                }
                else
                {
                    Report($"구매 완료: {inventoryItem.Definition.DisplayName} (-{GetCurrencyName(currency)} {price:N0})", false);
                }
            }
            else if (sourceIsPlayer && destinationIsMerchant &&
                     handling == VariableInventoryDropHandling.AcceptWithoutInsert)
            {
                if (!playerState.Wallet.TryCredit(currency, price))
                {
                    Debug.LogError(
                        "Merchant sale completed without its prevalidated Player payment. " +
                        "The wallet has an unexpected competing writer.");
                }
                else
                {
                    Report($"판매 완료: {inventoryItem.Definition.DisplayName} (+{GetCurrencyName(currency)} {price:N0})", false);
                }
            }

            refreshViews?.Invoke();
        }

        private void TryQuickPurchase(
            IVariableInventoryViewData source,
            IVariableInventoryCellData item)
        {
            if (!(item is InventoryItemData inventoryItem))
            {
                Report("구매할 수 없는 아이템입니다.", true);
                return;
            }

            if (!TryValidateTradeItem(inventoryItem, out string error))
            {
                Report(error, true);
                return;
            }

            TradeCurrency currency = inventoryItem.Definition.TradeCurrency;
            int price = inventoryItem.Definition.TradePrice;
            if (!playerState.Wallet.CanSpend(currency, price))
            {
                Report($"{GetCurrencyName(currency)}이 부족합니다.", true);
                return;
            }

            if (!TryTransferFirstFit(
                    source,
                    playerState.Inventory,
                    item,
                    out TransferReceipt receipt,
                    out error))
            {
                Report($"구매 실패: {error}", true);
                return;
            }

            if (!playerState.Wallet.TrySpend(currency, price))
            {
                if (!TryRollbackTransfer(receipt, out string rollbackError))
                {
                    Debug.LogError($"Purchase payment and inventory rollback both failed: {rollbackError}");
                }
                Report("구매 결제를 확정하지 못해 아이템 이동을 취소했습니다.", true);
                refreshViews?.Invoke();
                return;
            }

            Report($"구매 완료: {inventoryItem.Definition.DisplayName} (-{GetCurrencyName(currency)} {price:N0})", false);
            refreshViews?.Invoke();
        }

        private void TryQuickSale(
            IVariableInventoryViewData source,
            IVariableInventoryCellData item)
        {
            if (!(item is InventoryItemData inventoryItem))
            {
                Report("판매할 수 없는 아이템입니다.", true);
                return;
            }

            if (!TryValidateTradeItem(inventoryItem, out string error))
            {
                Report(error, true);
                return;
            }

            TradeCurrency currency = inventoryItem.Definition.TradeCurrency;
            int price = inventoryItem.Definition.TradePrice;
            if (!playerState.Wallet.CanCredit(currency, price))
            {
                Report("화폐 보유 한도를 초과하여 판매할 수 없습니다.", true);
                return;
            }

            int? sourceIndex = source.GetId(item);
            if (!sourceIndex.HasValue)
            {
                Report("판매 원본 슬롯을 찾을 수 없습니다.", true);
                return;
            }

            try
            {
                source.InsertInventoryItem(sourceIndex.Value, null);
            }
            catch (Exception exception)
            {
                Report($"판매 아이템을 분리하지 못했습니다: {exception.Message}", true);
                return;
            }

            if (!playerState.Wallet.TryCredit(currency, price))
            {
                try
                {
                    source.InsertInventoryItem(sourceIndex.Value, item);
                }
                catch (Exception rollbackException)
                {
                    Debug.LogError($"Sale payment and source rollback both failed: {rollbackException.Message}");
                }
                Report("판매 대금을 확정하지 못해 판매를 취소했습니다.", true);
                refreshViews?.Invoke();
                return;
            }

            Report($"판매 완료: {inventoryItem.Definition.DisplayName} (+{GetCurrencyName(currency)} {price:N0})", false);
            refreshViews?.Invoke();
        }

        private void TryQuickMove(
            IVariableInventoryViewData source,
            IVariableInventoryViewData destination,
            IVariableInventoryCellData item,
            string actionName)
        {
            if (!TryTransferFirstFit(source, destination, item, out _, out string error))
            {
                Report($"{actionName} 실패: {error}", true);
                return;
            }

            Report($"{actionName} 완료", false);
            refreshViews?.Invoke();
        }

        private static bool TryTransferFirstFit(
            IVariableInventoryViewData source,
            IVariableInventoryViewData destination,
            IVariableInventoryCellData item,
            out TransferReceipt receipt,
            out string error)
        {
            receipt = default;
            if (source == null || destination == null || item == null || ReferenceEquals(source, destination))
            {
                error = "원본 또는 대상 인벤토리가 올바르지 않습니다.";
                return false;
            }

            int? sourceIndex = source.GetId(item);
            if (!sourceIndex.HasValue)
            {
                error = "원본 슬롯을 찾을 수 없습니다.";
                return false;
            }

            try
            {
                source.InsertInventoryItem(sourceIndex.Value, null);
            }
            catch (Exception exception)
            {
                error = $"원본 아이템을 분리하지 못했습니다: {exception.Message}";
                return false;
            }

            int? destinationIndex = destination.GetInsertableId(item);
            if (!destinationIndex.HasValue)
            {
                return TryRestoreSourceAfterFailedMove(
                    source,
                    sourceIndex.Value,
                    item,
                    "대상 인벤토리에 들어갈 빈 공간이 없습니다.",
                    out error);
            }

            try
            {
                destination.InsertInventoryItem(destinationIndex.Value, item);
            }
            catch (Exception exception)
            {
                return TryRestoreSourceAfterFailedMove(
                    source,
                    sourceIndex.Value,
                    item,
                    $"대상 인벤토리 삽입에 실패했습니다: {exception.Message}",
                    out error);
            }

            receipt = new TransferReceipt
            {
                Source = source,
                Destination = destination,
                Item = item,
                SourceIndex = sourceIndex.Value,
                DestinationIndex = destinationIndex.Value
            };
            error = null;
            return true;
        }

        private static bool TryRestoreSourceAfterFailedMove(
            IVariableInventoryViewData source,
            int sourceIndex,
            IVariableInventoryCellData item,
            string failure,
            out string error)
        {
            try
            {
                source.InsertInventoryItem(sourceIndex, item);
                error = failure;
            }
            catch (Exception rollbackException)
            {
                error = $"{failure} 원본 복구도 실패했습니다: {rollbackException.Message}";
                Debug.LogError(error);
            }

            return false;
        }

        private static bool TryRollbackTransfer(TransferReceipt receipt, out string error)
        {
            try
            {
                receipt.Destination.InsertInventoryItem(receipt.DestinationIndex, null);
                receipt.Source.InsertInventoryItem(receipt.SourceIndex, receipt.Item);
                error = null;
                return true;
            }
            catch (Exception exception)
            {
                error = exception.Message;
                return false;
            }
        }

        private bool IsPlayerOwned(IVariableInventoryViewData candidate)
        {
            return ReferenceEquals(candidate, playerState.Inventory) ||
                   ReferenceEquals(candidate, playerState.Equipment) ||
                   IsNestedIn(playerState.Inventory, candidate) ||
                   IsNestedIn(playerState.Equipment, candidate);
        }

        private static bool IsNestedIn(
            IVariableInventoryViewData root,
            IVariableInventoryViewData candidate)
        {
            if (root == null || candidate == null)
            {
                return false;
            }

            if (ReferenceEquals(root, candidate))
            {
                return true;
            }

            var visited = new HashSet<IVariableInventoryViewData>();
            return ContainsNestedGrid(root, candidate, visited);
        }

        private static bool ContainsNestedGrid(
            IVariableInventoryViewData current,
            IVariableInventoryViewData target,
            HashSet<IVariableInventoryViewData> visited)
        {
            if (current == null || !visited.Add(current))
            {
                return false;
            }

            if (current is StandardStashViewData stash && stash.CellData != null)
            {
                foreach (IVariableInventoryCellData cell in stash.CellData)
                {
                    if (cell is IStandardCaseCellData container && container.CaseData != null)
                    {
                        if (ReferenceEquals(container.CaseData, target) ||
                            ContainsNestedGrid(container.CaseData, target, visited))
                        {
                            return true;
                        }
                    }
                }
            }
            else if (current is EquipmentLoadoutData equipment)
            {
                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (equipment.GetItem(slot) is IStandardCaseCellData container &&
                        container.CaseData != null &&
                        (ReferenceEquals(container.CaseData, target) ||
                         ContainsNestedGrid(container.CaseData, target, visited)))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        private static bool TryValidateTradeItem(InventoryItemData item, out string error)
        {
            if (item?.Definition == null || !item.Definition.IsTradable)
            {
                error = item?.Definition != null && item.Definition.IsContainer
                    ? "상자류 아이템은 현재 거래에서 제외되어 있습니다."
                    : "현재 거래할 수 없는 아이템입니다.";
                return false;
            }

            error = null;
            return true;
        }

        private void Report(string message, bool isError)
        {
            reportStatus?.Invoke(message, isError);
        }

        public static string GetCurrencyName(TradeCurrency currency)
        {
            return currency == TradeCurrency.Gold ? "금" : "은";
        }
    }
}
