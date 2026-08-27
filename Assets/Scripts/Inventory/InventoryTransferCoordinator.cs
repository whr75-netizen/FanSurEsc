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
        private int committedTransferQuantity;
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
                SplitItem.Quantity != outstandingQuantity || outstandingQuantity <= 0 ||
                !splitOwner.GetId(SplitItem).HasValue)
            {
                error = "The split stack was not attached to a destination inventory.";
                return false;
            }

            state = TransactionState.Committed;
            error = null;
            return true;
        }

        public bool TryRecordPartialTransfer(
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
                error = "The partial transfer does not match the outstanding split quantity.";
                return false;
            }

            int expectedDetachedQuantity = remainingCarriedQuantity > 0
                ? remainingCarriedQuantity
                : outstandingQuantity;
            if (SplitItem.Quantity != expectedDetachedQuantity)
            {
                error = "The detached split quantity changed during the partial transfer.";
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
                error = "The source stack changed during the partial transfer.";
                return false;
            }

            IVariableInventoryViewData targetOwner = targetItem.InventoryOwner;
            if (targetOwner == null || !targetOwner.GetId(targetItem).HasValue)
            {
                error = "The partial transfer target is not attached to an inventory.";
                return false;
            }

            int transferredQuantityAfter = committedTransferQuantity + movedQuantity;
            if (transferredQuantityAfter > initialSplitQuantity)
            {
                error = "The transferred quantity exceeded the original split quantity.";
                return false;
            }

            expectedSourceQuantity = sourceQuantityAfterMerge;
            committedTransferQuantity = transferredQuantityAfter;
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
        private StorageQuickTransferTransaction pendingStorageRecovery;

        private struct TransferReceipt
        {
            public IVariableInventoryViewData Source;
            public IVariableInventoryViewData Destination;
            public IVariableInventoryCellData Item;
            public int SourceIndex;
            public int DestinationIndex;
        }

        private struct StorageQuickTransferResult
        {
            public int MovedQuantity;
            public int SourceRemainingQuantity;
        }

        private sealed class StorageStackFillStep
        {
            public InventoryItemData Target;
            public int QuantityBefore;
            public int QuantityAfter;
            public bool Applied;
        }

        /// <summary>
        /// Owns one synchronous Storage quick-transfer transaction. It never owns
        /// inventory data; it only records enough CAS state to finish or recover
        /// mutations made through the existing source/destination owner APIs.
        /// </summary>
        private sealed class StorageQuickTransferTransaction
        {
            private readonly IVariableInventoryViewData source;
            private readonly StandardStashViewData destination;
            private readonly InventoryItemData sourceItem;
            private readonly int sourceIndex;
            private readonly int originalQuantity;
            private readonly List<StorageStackFillStep> fillSteps;
            private readonly int plannedStackQuantity;

            private int? destinationIndex;
            private bool started;
            private bool committed;
            private bool sourceQuantityChanged;
            private bool rollbackComplete;

            private StorageQuickTransferTransaction(
                IVariableInventoryViewData source,
                StandardStashViewData destination,
                InventoryItemData sourceItem,
                int sourceIndex,
                List<StorageStackFillStep> fillSteps,
                int plannedStackQuantity)
            {
                this.source = source;
                this.destination = destination;
                this.sourceItem = sourceItem;
                this.sourceIndex = sourceIndex;
                this.fillSteps = fillSteps;
                this.plannedStackQuantity = plannedStackQuantity;
                originalQuantity = sourceItem.Quantity;
            }

            public static bool TryCreate(
                IVariableInventoryViewData source,
                StandardStashViewData destination,
                InventoryItemData sourceItem,
                out StorageQuickTransferTransaction transaction,
                out string error)
            {
                transaction = null;
                if (source == null || destination == null || sourceItem == null ||
                    ReferenceEquals(source, destination))
                {
                    error = "원본 또는 대상 인벤토리가 올바르지 않습니다.";
                    return false;
                }

                int? sourceIndex = source.GetId(sourceItem);
                if (!sourceIndex.HasValue ||
                    !ReferenceEquals(sourceItem.InventoryOwner, source))
                {
                    error = "원본 아이템의 슬롯 또는 소유권이 올바르지 않습니다.";
                    return false;
                }

                var fillSteps = new List<StorageStackFillStep>();
                int quantityToPlan = sourceItem.Quantity;
                if (sourceItem.MaxStackSize > 1)
                {
                    for (int i = 0; i < destination.CellData.Length && quantityToPlan > 0; i++)
                    {
                        if (!(destination.CellData[i] is InventoryItemData target) ||
                            ReferenceEquals(target, sourceItem) ||
                            !ReferenceEquals(target.InventoryOwner, destination) ||
                            !InventoryTransferCoordinator.IsSameStackKind(sourceItem, target) ||
                            target.Quantity >= target.MaxStackSize)
                        {
                            continue;
                        }

                        int moved = Mathf.Min(
                            quantityToPlan,
                            target.MaxStackSize - target.Quantity);
                        fillSteps.Add(new StorageStackFillStep
                        {
                            Target = target,
                            QuantityBefore = target.Quantity,
                            QuantityAfter = target.Quantity + moved
                        });
                        quantityToPlan -= moved;
                    }
                }

                transaction = new StorageQuickTransferTransaction(
                    source,
                    destination,
                    sourceItem,
                    sourceIndex.Value,
                    fillSteps,
                    sourceItem.Quantity - quantityToPlan);
                error = null;
                return true;
            }

            public bool TryExecute(
                out StorageQuickTransferResult result,
                out string error)
            {
                result = default;
                if (started)
                {
                    error = "The Storage quick-transfer transaction was already started.";
                    return false;
                }

                started = true;
                try
                {
                    source.InsertInventoryItem(sourceIndex, null);
                }
                catch (Exception exception)
                {
                    error = $"원본 아이템을 분리하지 못했습니다: {exception.Message}";
                    return false;
                }

                try
                {
                    destinationIndex = destination.GetInsertableId(sourceItem);
                }
                catch (Exception exception)
                {
                    error = $"대상 인벤토리의 빈 공간을 확인하지 못했습니다: {exception.Message}";
                    return false;
                }
                if (plannedStackQuantity <= 0 && !destinationIndex.HasValue)
                {
                    error = "대상 인벤토리에 합칠 stack이나 빈 공간이 없습니다.";
                    return false;
                }

                foreach (StorageStackFillStep step in fillSteps)
                {
                    if (!step.Target.TryChangeQuantity(
                            destination,
                            step.QuantityBefore,
                            step.QuantityAfter,
                            out error))
                    {
                        error = $"대상 stack 수량을 갱신하지 못했습니다: {error}";
                        return false;
                    }

                    step.Applied = true;
                }

                int remainder = originalQuantity - plannedStackQuantity;
                if (remainder > 0 && plannedStackQuantity > 0)
                {
                    if (!sourceItem.TryChangeQuantity(
                            null,
                            originalQuantity,
                            remainder,
                            out error))
                    {
                        error = $"이동 후 남은 stack 수량을 갱신하지 못했습니다: {error}";
                        return false;
                    }

                    sourceQuantityChanged = true;
                }

                if (remainder > 0)
                {
                    IVariableInventoryViewData remainderOwner = destinationIndex.HasValue
                        ? destination
                        : source;
                    int remainderIndex = destinationIndex ?? sourceIndex;
                    try
                    {
                        remainderOwner.InsertInventoryItem(remainderIndex, sourceItem);
                    }
                    catch (Exception exception)
                    {
                        error = $"남은 stack을 배치하지 못했습니다: {exception.Message}";
                        return false;
                    }
                }

                committed = true;
                result = new StorageQuickTransferResult
                {
                    MovedQuantity = destinationIndex.HasValue
                        ? originalQuantity
                        : plannedStackQuantity,
                    SourceRemainingQuantity = destinationIndex.HasValue ? 0 : remainder
                };
                error = null;
                return true;
            }

            public bool TryRollback(out string error)
            {
                error = null;
                if (rollbackComplete)
                {
                    return true;
                }

                if (committed)
                {
                    error = "A committed Storage quick-transfer cannot be rolled back.";
                    return false;
                }

                if (!TryDetachSourceItemFromUnexpectedOwner(out error))
                {
                    return false;
                }

                for (int i = fillSteps.Count - 1; i >= 0; i--)
                {
                    StorageStackFillStep step = fillSteps[i];
                    if (!step.Applied)
                    {
                        continue;
                    }

                    if (ReferenceEquals(step.Target.InventoryOwner, destination) &&
                        step.Target.Quantity == step.QuantityBefore)
                    {
                        step.Applied = false;
                        continue;
                    }

                    if (!step.Target.TryChangeQuantity(
                            destination,
                            step.QuantityAfter,
                            step.QuantityBefore,
                            out error))
                    {
                        return false;
                    }

                    step.Applied = false;
                }

                if (sourceItem.InventoryOwner == null &&
                    sourceItem.Quantity != originalQuantity)
                {
                    int expectedQuantity = originalQuantity - plannedStackQuantity;
                    if (!sourceQuantityChanged || sourceItem.Quantity != expectedQuantity ||
                        !sourceItem.TryChangeQuantity(
                            null,
                            expectedQuantity,
                            originalQuantity,
                            out error))
                    {
                        error = error ??
                                "The detached source stack no longer matches its rollback state.";
                        return false;
                    }

                    sourceQuantityChanged = false;
                }

                if (ReferenceEquals(sourceItem.InventoryOwner, source) &&
                    source.GetId(sourceItem) == sourceIndex &&
                    sourceItem.Quantity == originalQuantity)
                {
                    rollbackComplete = true;
                    error = null;
                    return true;
                }

                if (sourceItem.InventoryOwner != null ||
                    sourceItem.Quantity != originalQuantity)
                {
                    error = "The source stack is not detached in its original rollback state.";
                    return false;
                }

                try
                {
                    source.InsertInventoryItem(sourceIndex, sourceItem);
                }
                catch (Exception exception)
                {
                    error = $"원본 stack 복구에 실패했습니다: {exception.Message}";
                    return false;
                }

                rollbackComplete = true;
                error = null;
                return true;
            }

            private bool TryDetachSourceItemFromUnexpectedOwner(out string error)
            {
                IVariableInventoryViewData currentOwner = sourceItem.InventoryOwner;
                if (currentOwner == null)
                {
                    error = null;
                    return true;
                }

                if (ReferenceEquals(currentOwner, source) &&
                    source.GetId(sourceItem) == sourceIndex)
                {
                    if (sourceItem.Quantity == originalQuantity)
                    {
                        error = null;
                        return true;
                    }

                    int expectedRemainder = originalQuantity - plannedStackQuantity;
                    if (!sourceQuantityChanged ||
                        sourceItem.Quantity != expectedRemainder)
                    {
                        error = "The source stack changed while attached to its original slot.";
                        return false;
                    }

                    try
                    {
                        source.InsertInventoryItem(sourceIndex, null);
                    }
                    catch (Exception exception)
                    {
                        error = $"원본에서 남은 stack을 다시 분리하지 못했습니다: {exception.Message}";
                        return false;
                    }

                    error = null;
                    return true;
                }

                if (!ReferenceEquals(currentOwner, destination))
                {
                    error = "The source stack changed owner during Storage transfer recovery.";
                    return false;
                }

                int? currentIndex = destination.GetId(sourceItem);
                if (!currentIndex.HasValue)
                {
                    error = "The destination owner no longer contains the transferred stack.";
                    return false;
                }

                try
                {
                    destination.InsertInventoryItem(currentIndex.Value, null);
                }
                catch (Exception exception)
                {
                    error = $"대상에서 stack을 회수하지 못했습니다: {exception.Message}";
                    return false;
                }

                error = null;
                return true;
            }
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

        private sealed class SingleStackPlacementReceipt : IVariableInventorySinglePlacementReceipt
        {
            private readonly InventoryItemData placedItem;
            private readonly IVariableInventoryViewData destinationOwner;
            private readonly int destinationIndex;
            private readonly InventoryItemData carriedItem;
            private readonly bool restoreCarriedQuantity;
            private readonly int carriedQuantityBefore;
            private readonly int carriedQuantityAfter;
            private bool placedItemRemoved;
            private bool carriedQuantityRestored;
            private bool rolledBack;

            public SingleStackPlacementReceipt(
                InventoryItemData placedItem,
                IVariableInventoryViewData destinationOwner,
                int destinationIndex,
                InventoryItemData carriedItem,
                bool restoreCarriedQuantity,
                int carriedQuantityBefore,
                int carriedQuantityAfter)
            {
                this.placedItem = placedItem;
                this.destinationOwner = destinationOwner;
                this.destinationIndex = destinationIndex;
                this.carriedItem = carriedItem;
                this.restoreCarriedQuantity = restoreCarriedQuantity;
                this.carriedQuantityBefore = carriedQuantityBefore;
                this.carriedQuantityAfter = carriedQuantityAfter;
            }

            public IVariableInventoryCellData PlacedItem => placedItem;
            public int MovedQuantity => 1;
            public int RemainingQuantity => carriedQuantityAfter;

            public bool TryRollback(out string error)
            {
                if (rolledBack)
                {
                    error = null;
                    return true;
                }

                if (!placedItemRemoved)
                {
                    int? currentIndex = destinationOwner?.GetId(placedItem);
                    if (!currentIndex.HasValue || currentIndex.Value != destinationIndex ||
                        !ReferenceEquals(placedItem.InventoryOwner, destinationOwner))
                    {
                        error = "The separated item is no longer at its placement destination.";
                        return false;
                    }

                    try
                    {
                        destinationOwner.InsertInventoryItem(destinationIndex, null);
                        placedItemRemoved = true;
                    }
                    catch (Exception exception)
                    {
                        error = $"Could not remove the separated item: {exception.Message}";
                        return false;
                    }
                }

                if (restoreCarriedQuantity && !carriedQuantityRestored)
                {
                    if (carriedItem == null || carriedItem.InventoryOwner != null)
                    {
                        error = "The carried stack is no longer detached during placement rollback.";
                        return false;
                    }

                    if (carriedItem.Quantity == carriedQuantityBefore)
                    {
                        carriedQuantityRestored = true;
                    }
                    else if (!carriedItem.TryChangeQuantity(
                                 null,
                                 carriedQuantityAfter,
                                 carriedQuantityBefore,
                                 out error))
                    {
                        return false;
                    }
                    else
                    {
                        carriedQuantityRestored = true;
                    }
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

        public bool TrySetPlayerState(PlayerInventoryState state, out string error)
        {
            if (state == null)
            {
                error = "Player inventory state is missing.";
                return false;
            }

            if (!EnsurePendingStorageRecovery("Player 인벤토리 교체", out error))
            {
                return false;
            }

            playerState = state;
            error = null;
            return true;
        }

        public bool TrySetExternalSession(
            ExternalInventoryMode mode,
            StandardStashViewData inventory,
            out string error)
        {
            if (!EnsurePendingStorageRecovery("외부 인벤토리 연결", out error))
            {
                return false;
            }

            externalMode = mode;
            externalInventory = inventory;
            error = null;
            return true;
        }

        public bool TryClearExternalSession(out string error)
        {
            if (!EnsurePendingStorageRecovery("외부 인벤토리 닫기", out error))
            {
                return false;
            }

            externalMode = ExternalInventoryMode.None;
            externalInventory = null;
            error = null;
            return true;
        }

        public bool CanEquip(
            IVariableInventoryView sourceView,
            InventoryItemData item)
        {
            if (pendingStorageRecovery != null ||
                !TryResolveEquipSource(
                    sourceView,
                    item,
                    out IVariableInventoryViewData source,
                    out _) ||
                ReferenceEquals(source, playerState.Equipment))
            {
                return false;
            }

            EquipmentSlotId slot = EquipmentSlotCatalog.GetPrimarySlot(
                item.Definition.EquipmentSlot);
            return playerState.Equipment.GetItem(slot) == null;
        }

        public bool TryEquip(
            IVariableInventoryView sourceView,
            InventoryItemData item,
            out string error)
        {
            if (!EnsurePendingStorageRecovery("장착", out error))
            {
                return false;
            }

            if (!TryResolveEquipSource(sourceView, item, out IVariableInventoryViewData source, out error))
            {
                return false;
            }

            EquipmentSlotId slot = EquipmentSlotCatalog.GetPrimarySlot(
                item.Definition.EquipmentSlot);
            if (playerState.Equipment.GetItem(slot) != null)
            {
                error = $"{EquipmentSlotCatalog.GetDisplayName(slot)} 칸이 이미 사용 중입니다.";
                Report($"장착 실패: {error}", true);
                return false;
            }

            if (!TryTransferFirstFit(
                    source,
                    playerState.Equipment,
                    item,
                    out _,
                    out error))
            {
                Report($"장착 실패: {error}", true);
                return false;
            }

            Report($"장착 완료: {item.Definition.DisplayName}", false);
            refreshViews?.Invoke();
            error = null;
            return true;
        }

        public bool TryToggleEquipment(
            IVariableInventoryView sourceView,
            InventoryItemData item,
            out string error)
        {
            if (IsEquippedSource(sourceView, item))
            {
                return TryUnequipToPlayerInventory(sourceView, item, out error);
            }

            return TryEquip(sourceView, item, out error);
        }

        public bool TryBeginStackSplit(
            IVariableInventoryView sourceView,
            InventoryItemData sourceItem,
            int splitQuantity,
            out InventoryStackSplitTransaction transaction,
            out string error)
        {
            transaction = null;
            if (!EnsurePendingStorageRecovery("stack 나누기"))
            {
                error = "이전 Storage 자동이동 복구가 끝나지 않아 stack을 나눌 수 없습니다.";
                return false;
            }

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
            if (!EnsurePendingStorageRecovery("빠른 이동"))
            {
                return true;
            }

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
            if (!EnsurePendingStorageRecovery("아이템 이동"))
            {
                return VariableInventoryDropHandling.Reject;
            }

            return EvaluateDropHandling(sourceView, destinationView, item, true);
        }

        public VariableInventoryDropHandling GetDropPreviewHandling(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item)
        {
            if (pendingStorageRecovery != null &&
                !TryRecoverPendingStorageTransfer(out _))
            {
                return VariableInventoryDropHandling.Reject;
            }

            return EvaluateDropHandling(sourceView, destinationView, item, false);
        }

        public bool CanMergeStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item)
        {
            if (pendingStorageRecovery != null &&
                !TryRecoverPendingStorageTransfer(out _))
            {
                return false;
            }

            if (sourceView == null ||
                !(destinationView is IVariableInventoryBoundView destinationBound) ||
                !destinationBound.ContainsCell(destinationCell) ||
                !(item is InventoryItemData carriedItem) ||
                !(destinationCell?.CellData is InventoryItemData targetItem) ||
                ReferenceEquals(carriedItem, targetItem) || carriedItem.InventoryOwner != null ||
                !IsSameStackKind(carriedItem, targetItem) ||
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

        public bool TryPlaceSingleFromCarriedStack(
            IVariableInventoryView sourceView,
            IVariableInventoryPartialDropView destinationView,
            IVariableInventoryCell destinationCell,
            IVariableInventoryCellData item,
            out IVariableInventorySinglePlacementReceipt receipt,
            out string error)
        {
            receipt = null;
            error = null;
            if (!EnsurePendingStorageRecovery("stack 한 개 배치", out error))
            {
                return false;
            }

            if (externalMode == ExternalInventoryMode.Merchant)
            {
                error = "상인 거래 중에는 stack 단위 가격 정책이 확정되지 않아 한 개씩 배치할 수 없습니다.";
                return false;
            }

            if (sourceView == null || destinationView == null ||
                !destinationView.ContainsCell(destinationCell) ||
                destinationCell?.CellData != null ||
                !(item is InventoryItemData carriedItem) ||
                carriedItem.InventoryOwner != null ||
                carriedItem.MaxStackSize <= 1 || carriedItem.Quantity <= 0)
            {
                error = "Only a detached stack item can place one item into an empty grid cell.";
                return false;
            }

            if (EvaluateDropHandling(sourceView, destinationView, carriedItem, true) !=
                VariableInventoryDropHandling.Standard)
            {
                error = "This inventory boundary does not allow single-item placement.";
                return false;
            }

            int carriedBefore = carriedItem.Quantity;
            InventoryItemData placedItem = carriedItem;
            if (carriedBefore > 1)
            {
                if (!InventoryItemDataFactory.TryCreate(
                        carriedItem.Definition,
                        1,
                        out IVariableInventoryCellData created,
                        out error) ||
                    !(created is InventoryItemData createdItem))
                {
                    error = error ?? "Could not create the separated item.";
                    return false;
                }

                placedItem = createdItem;
            }

            placedItem.IsRotate = carriedItem.IsRotate;
            if (!destinationView.TryResolvePartialDrop(
                    destinationCell,
                    placedItem,
                    out IVariableInventoryViewData destinationOwner,
                    out int destinationIndex,
                    out error))
            {
                return false;
            }

            if (destinationOwner == null || destinationIndex < 0 ||
                !ReferenceEquals(destinationOwner, destinationView.ViewData) ||
                !destinationOwner.CheckInsert(destinationIndex, placedItem))
            {
                error = "The destination view returned an invalid single-item placement.";
                return false;
            }

            try
            {
                destinationOwner.InsertInventoryItem(destinationIndex, placedItem);
            }
            catch (Exception exception)
            {
                if (ReferenceEquals(placedItem.InventoryOwner, destinationOwner) &&
                    destinationOwner.GetId(placedItem) == destinationIndex)
                {
                    var insertionRecovery = new SingleStackPlacementReceipt(
                        placedItem,
                        destinationOwner,
                        destinationIndex,
                        carriedItem,
                        false,
                        carriedBefore,
                        carriedBefore);
                    if (!insertionRecovery.TryRollback(out string rollbackError))
                    {
                        receipt = insertionRecovery;
                        error = $"Could not attach the separated item: {exception.Message}. " +
                                $"Rollback also failed: {rollbackError}";
                        return false;
                    }
                }

                error = $"Could not attach the separated item: {exception.Message}";
                return false;
            }

            if (!ReferenceEquals(placedItem.InventoryOwner, destinationOwner) ||
                destinationOwner.GetId(placedItem) != destinationIndex)
            {
                var invalidPlacementRecovery = new SingleStackPlacementReceipt(
                    placedItem,
                    destinationOwner,
                    destinationIndex,
                    carriedItem,
                    false,
                    carriedItem.Quantity,
                    carriedItem.Quantity);
                if (!invalidPlacementRecovery.TryRollback(out string rollbackError))
                {
                    receipt = invalidPlacementRecovery;
                    error = $"The separated item attachment was inconsistent and rollback failed: {rollbackError}";
                    return false;
                }

                error = "The separated item attachment was inconsistent.";
                return false;
            }

            if (carriedBefore == 1)
            {
                receipt = new SingleStackPlacementReceipt(
                    placedItem,
                    destinationOwner,
                    destinationIndex,
                    carriedItem,
                    false,
                    carriedBefore,
                    0);
                error = null;
                return true;
            }

            if (!carriedItem.TryChangeQuantity(
                    null,
                    carriedBefore,
                    carriedBefore - 1,
                    out string quantityError))
            {
                var recovery = new SingleStackPlacementReceipt(
                    placedItem,
                    destinationOwner,
                    destinationIndex,
                    carriedItem,
                    false,
                    carriedBefore,
                    carriedBefore);
                if (!recovery.TryRollback(out string rollbackError))
                {
                    receipt = recovery;
                    error = $"{quantityError} Placement rollback also failed: {rollbackError}";
                    return false;
                }

                error = quantityError;
                return false;
            }

            receipt = new SingleStackPlacementReceipt(
                placedItem,
                destinationOwner,
                destinationIndex,
                carriedItem,
                true,
                carriedBefore,
                carriedBefore - 1);
            error = null;
            return true;
        }

        public bool CanPlaceSingleFromCarriedStack(
            IVariableInventoryView sourceView,
            IVariableInventoryView destinationView,
            IVariableInventoryCellData item)
        {
            return externalMode != ExternalInventoryMode.Merchant &&
                   sourceView != null && destinationView != null &&
                   item is InventoryItemData carriedItem &&
                   carriedItem.InventoryOwner == null &&
                   carriedItem.MaxStackSize > 1 && carriedItem.Quantity > 0 &&
                   EvaluateDropHandling(sourceView, destinationView, carriedItem, false) ==
                   VariableInventoryDropHandling.Standard;
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
            if (!EnsurePendingStorageRecovery("아이템 이동 확정"))
            {
                return;
            }

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
            if (item is InventoryItemData inventoryItem &&
                inventoryItem.MaxStackSize > 1 &&
                destination is StandardStashViewData stashDestination)
            {
                if (!StorageQuickTransferTransaction.TryCreate(
                        source,
                        stashDestination,
                        inventoryItem,
                        out StorageQuickTransferTransaction transaction,
                        out string createError))
                {
                    Report($"{actionName} 실패: {createError}", true);
                    return;
                }

                if (!transaction.TryExecute(
                        out StorageQuickTransferResult transferResult,
                        out string transferError))
                {
                    if (!transaction.TryRollback(out string rollbackError))
                    {
                        pendingStorageRecovery = transaction;
                        transferError =
                            $"{transferError} 자동 복구도 완료되지 않았습니다: {rollbackError}";
                    }

                    Report($"{actionName} 실패: {transferError}", true);
                    refreshViews?.Invoke();
                    return;
                }

                string resultMessage = transferResult.SourceRemainingQuantity > 0
                    ? $"{actionName} 완료: {transferResult.MovedQuantity}개 이동, " +
                      $"{transferResult.SourceRemainingQuantity}개 원본에 남음"
                    : $"{actionName} 완료: {transferResult.MovedQuantity}개 이동";
                Report(resultMessage, false);
                refreshViews?.Invoke();
                return;
            }

            if (!TryTransferFirstFit(source, destination, item, out _, out string error))
            {
                Report($"{actionName} 실패: {error}", true);
                return;
            }

            Report($"{actionName} 완료", false);
            refreshViews?.Invoke();
        }

        private bool TryRecoverPendingStorageTransfer(out string error)
        {
            if (pendingStorageRecovery == null)
            {
                error = null;
                return true;
            }

            if (!pendingStorageRecovery.TryRollback(out error))
            {
                return false;
            }

            pendingStorageRecovery = null;
            refreshViews?.Invoke();
            return true;
        }

        private bool TryResolveEquipSource(
            IVariableInventoryView sourceView,
            InventoryItemData item,
            out IVariableInventoryViewData source,
            out string error)
        {
            source = (sourceView as IVariableInventoryBoundView)?.ViewData;
            if (source == null || item == null || !item.Definition.IsEquippable)
            {
                error = "장착 가능한 아이템이 아닙니다.";
                return false;
            }

            if (ReferenceEquals(source, playerState.Equipment))
            {
                error = "이미 장착된 아이템입니다.";
                return false;
            }

            if (!ReferenceEquals(item.InventoryOwner, source) ||
                !source.GetId(item).HasValue)
            {
                error = "장착할 아이템의 원본 소유권을 확인할 수 없습니다.";
                return false;
            }

            bool playerOwned = IsPlayerOwned(source);
            bool storageOwned = externalMode == ExternalInventoryMode.Storage &&
                                externalInventory != null &&
                                IsNestedIn(externalInventory, source);
            if (!playerOwned && !storageOwned)
            {
                error = "현재 소유권에서는 이 아이템을 바로 장착할 수 없습니다.";
                return false;
            }

            error = null;
            return true;
        }

        private bool TryUnequipToPlayerInventory(
            IVariableInventoryView sourceView,
            InventoryItemData item,
            out string error)
        {
            if (!EnsurePendingStorageRecovery("장착 해제", out error))
            {
                return false;
            }

            if (!IsEquippedSource(sourceView, item))
            {
                error = "장착 해제할 아이템의 소유권을 확인할 수 없습니다.";
                return false;
            }

            IVariableInventoryViewData source =
                ((IVariableInventoryBoundView)sourceView).ViewData;
            if (!TryTransferFirstFit(
                    source,
                    playerState.Inventory,
                    item,
                    out _,
                    out error))
            {
                Report($"장착 해제 실패: {error}", true);
                return false;
            }

            Report($"장착 해제 완료: {item.Definition.DisplayName}", false);
            refreshViews?.Invoke();
            error = null;
            return true;
        }

        private bool IsEquippedSource(
            IVariableInventoryView sourceView,
            InventoryItemData item)
        {
            IVariableInventoryViewData source =
                (sourceView as IVariableInventoryBoundView)?.ViewData;
            return source != null && item != null &&
                   ReferenceEquals(source, playerState.Equipment) &&
                   ReferenceEquals(item.InventoryOwner, source) &&
                   source.GetId(item).HasValue;
        }

        private bool EnsurePendingStorageRecovery(string actionName)
        {
            return EnsurePendingStorageRecovery(actionName, out _);
        }

        private bool EnsurePendingStorageRecovery(string actionName, out string error)
        {
            if (TryRecoverPendingStorageTransfer(out error))
            {
                return true;
            }

            string message =
                $"{actionName} 차단: 이전 Storage 자동이동 복구가 끝나지 않았습니다. {error}";
            Debug.LogError(message);
            Report(message, true);
            refreshViews?.Invoke();
            error = message;
            return false;
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

        private static bool IsSameStackKind(
            InventoryItemData first,
            InventoryItemData second)
        {
            return first != null && second != null &&
                   first.MaxStackSize > 1 &&
                   first.Id == second.Id &&
                   first.MaxStackSize == second.MaxStackSize;
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
