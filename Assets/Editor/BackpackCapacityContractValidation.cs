using System;
using System.Collections.Generic;
using FantasySurvival.Inventory;
using FantasySurvival.SaveSystem;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using VariableInventorySystem;

namespace FantasySurvival.EditorTools
{
    /// <summary>
    /// Art- and scene-independent checks for Backpack capacity, deterministic repack,
    /// exact rollback, previewed direct replacements, and save/restore dimensions.
    /// </summary>
    public static class BackpackCapacityContractValidation
    {
        private const string MenuPath =
            "Tools/Fantasy Survival/Inventory/Validate Backpack Capacity";
        private const int BaseWidth = 8;
        private const int BaseHeight = 9;

        [MenuItem(MenuPath)]
        public static void Run()
        {
            var definitions = new List<ItemDefinition>();
            ItemDatabase database = null;

            try
            {
                ItemDefinition smallBackpack = AddDefinition(
                    definitions, 900001, "Validation Small Backpack", 1, 1,
                    EquipmentSlotType.Backpack, 1);
                ItemDefinition mediumBackpack = AddDefinition(
                    definitions, 900002, "Validation Medium Backpack", 1, 1,
                    EquipmentSlotType.Backpack, 2);
                ItemDefinition largeBackpack = AddDefinition(
                    definitions, 900003, "Validation Large Backpack", 1, 1,
                    EquipmentSlotType.Backpack, 3);
                ItemDefinition wideSmallBackpack = AddDefinition(
                    definitions, 900004, "Validation Wide Small Backpack", 4, 4,
                    EquipmentSlotType.Backpack, 1);
                ItemDefinition fragmentedBackpack = AddDefinition(
                    definitions, 900007, "Validation Fragmented Backpack", 2, 2,
                    EquipmentSlotType.Backpack, 3);
                ItemDefinition marker = AddDefinition(
                    definitions, 900005, "Validation Marker", 1, 1,
                    EquipmentSlotType.None, 0);
                ItemDefinition rotatedMarker = AddDefinition(
                    definitions, 900006, "Validation Rotated Marker", 2, 1,
                    EquipmentSlotType.None, 0);
                database = CreateDatabase(definitions.ToArray());

                ValidateRemovalRepackReceiptAndSave(
                    largeBackpack, marker, rotatedMarker, database);
                ValidateBlockedRemovalIsAtomic(smallBackpack, marker, database);
                ValidateEquipmentPanelDefersBackpackPick(
                    smallBackpack,
                    marker);
                ValidateDeferredUnequipPreviewAndCommit(
                    largeBackpack,
                    marker,
                    rotatedMarker);
                ValidateDeferredUnequipFailureIsAtomic(
                    smallBackpack,
                    marker);
                ValidateStagedTakeNotificationBoundary(
                    smallBackpack,
                    marker);
                ValidateDetachedSmallerReplacementPreview(
                    smallBackpack,
                    largeBackpack,
                    marker);
                ValidateCoordinatorReplacementPreview(
                    smallBackpack,
                    mediumBackpack,
                    largeBackpack,
                    fragmentedBackpack,
                    marker,
                    database);
                ValidateCoordinatorUpgradeRollback(
                    wideSmallBackpack, mediumBackpack, marker);
                ValidateDiscardRestoresBaseHeight(smallBackpack, marker);
                ValidateInvalidDefinitionContract(definitions);

                Debug.Log(
                    "Backpack capacity validation passed: rows append below base 8x9; " +
                    "removal repacks when possible and remains unchanged when impossible; " +
                    "equipment-panel Backpack pick hides only its presentation until drop; " +
                    "deferred Backpack hover previews leave height, cells, rotation, ownership, " +
                    "equipment, and dirty state untouched; exact root placement changes only " +
                    "on commit and failed exact placement remains atomic; smaller replacement " +
                    "preview includes the old Backpack in the target capacity; staged external " +
                    "take publishes only after its destination is complete; " +
                    "drag rollback restores exact slots/rotation; larger, equal, and smaller " +
                    "direct replacements preserve the current layout when possible and apply " +
                    "a previewed repack only when required; the old backpack is included in " +
                    "the fit plan; failed replacement remains exact; discard and save/restore " +
                    "preserve dimensions.");
            }
            finally
            {
                DestroyTransient(database);
                for (int index = definitions.Count - 1; index >= 0; index--)
                {
                    DestroyTransient(definitions[index]);
                }
            }
        }

        [MenuItem(MenuPath, true)]
        private static bool CanRun()
        {
            return !EditorApplication.isPlayingOrWillChangePlaymode;
        }

        private static void ValidateRemovalRepackReceiptAndSave(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition,
            ItemDefinition rotatedMarkerDefinition,
            ItemDatabase database)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var backpack = new InventoryItemData(backpackDefinition);
            Require(
                state.TryPlaceEquipment(EquipmentSlotId.Backpack, backpack, out string error),
                error);
            Require(
                root.CapacityHeight == BaseHeight + backpackDefinition.BackpackBonusRows,
                "Equipping did not append the configured Backpack rows.");

            var marker = new InventoryItemData(markerDefinition);
            var rotatedMarker = new InventoryItemData(rotatedMarkerDefinition)
            {
                IsRotate = true
            };
            int markerOriginalIndex = BaseWidth * BaseHeight;
            int rotatedOriginalIndex = markerOriginalIndex + 2;
            root.InsertInventoryItem(markerOriginalIndex, marker);
            root.InsertInventoryItem(rotatedOriginalIndex, rotatedMarker);

            Require(
                state.TryTakeEquipment(
                    EquipmentSlotId.Backpack,
                    out IVariableInventoryCellData removed,
                    out PlayerInventoryState.EquipmentTakeReceipt receipt,
                    out error),
                error);
            Require(
                ReferenceEquals(removed, backpack),
                "Removal returned a different Backpack instance.");
            Require(root.CapacityHeight == BaseHeight, "Removal did not restore the base height.");
            Require(
                ReferenceEquals(marker.InventoryOwner, root) &&
                ReferenceEquals(rotatedMarker.InventoryOwner, root),
                "Repack changed root item ownership.");
            int markerRepackedIndex = RequireIndex(root, marker);
            int rotatedRepackedIndex = RequireIndex(root, rotatedMarker);
            Require(
                markerRepackedIndex < BaseWidth * BaseHeight &&
                rotatedRepackedIndex < BaseWidth * BaseHeight,
                "Repack left an item outside the base grid.");

            Require(state.TryRestoreTakenEquipment(receipt, out error), error);
            Require(
                root.CapacityHeight == BaseHeight + backpackDefinition.BackpackBonusRows &&
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), backpack),
                "Receipt restore did not restore Backpack capacity/equipment.");
            Require(
                RequireIndex(root, marker) == markerOriginalIndex &&
                RequireIndex(root, rotatedMarker) == rotatedOriginalIndex &&
                rotatedMarker.IsRotate,
                "Receipt restore did not restore exact slots and rotation.");

            Require(
                state.TryTakeEquipment(
                    EquipmentSlotId.Backpack,
                    out removed,
                    out _,
                    out error),
                error);
            Require(
                RequireIndex(root, marker) == markerRepackedIndex &&
                RequireIndex(root, rotatedMarker) == rotatedRepackedIndex,
                "Equivalent removal did not produce the same deterministic repack.");
            Require(
                InventorySaveCodec.TryCapture(
                    state, database, out PlayerItemStateSaveData save, out error),
                error);
            Require(
                save.inventoryWidth == BaseWidth && save.inventoryHeight == BaseHeight,
                "Repacked base inventory saved incorrect dimensions.");
            Require(
                InventorySaveCodec.TryRestore(
                    save, database, BaseWidth, BaseHeight,
                    out PlayerInventoryState restored, out error),
                error);
            InventoryItemData restoredMarker =
                RequireDefinition(restored.Inventory, markerDefinition.Id);
            InventoryItemData restoredRotated =
                RequireDefinition(restored.Inventory, rotatedMarkerDefinition.Id);
            Require(
                RequireIndex(restored.Inventory, restoredMarker) == markerRepackedIndex &&
                RequireIndex(restored.Inventory, restoredRotated) == rotatedRepackedIndex &&
                restoredRotated.IsRotate == rotatedMarker.IsRotate,
                "Save round-trip changed the repack placement/rotation.");
        }

        private static void ValidateBlockedRemovalIsAtomic(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition,
            ItemDatabase database)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var backpack = new InventoryItemData(backpackDefinition);
            Require(
                state.TryPlaceEquipment(EquipmentSlotId.Backpack, backpack, out string error),
                error);

            for (int index = 0; index <= BaseWidth * BaseHeight; index++)
            {
                root.InsertInventoryItem(index, new InventoryItemData(markerDefinition));
            }

            IVariableInventoryCellData[] before =
                (IVariableInventoryCellData[])root.CellData.Clone();
            Require(
                !state.TryTakeEquipment(
                    EquipmentSlotId.Backpack,
                    out IVariableInventoryCellData removed,
                    out PlayerInventoryState.EquipmentTakeReceipt receipt,
                    out error),
                "Backpack removal succeeded although 73 items cannot fit in 72 cells.");
            Require(removed == null && receipt == null, "Blocked removal leaked a detached Backpack.");
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), backpack) &&
                root.CapacityHeight == BaseHeight + 1,
                "Blocked removal changed Backpack equipment or capacity.");
            RequireGridReferences(root, before, "Blocked removal changed the root grid.");
            Require(
                InventorySaveCodec.TryCapture(state, database, out _, out error),
                $"The unchanged state could not be saved after blocked removal: {error}");

            int silverBefore = state.Wallet.Silver;
            var coordinator = new InventoryTransferCoordinator(state, null, null, null);
            Require(
                coordinator.TrySetExternalSession(
                    ExternalInventoryMode.Merchant,
                    new StandardStashViewData(1, 1),
                    out error),
                error);
            Require(
                coordinator.HandleQuickTransfer(
                    new BoundViewStub(state.Equipment),
                    backpack),
                "Equipped Backpack sale was not handled by the merchant path.");
            Require(
                state.Wallet.Silver == silverBefore &&
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), backpack) &&
                root.CapacityHeight == BaseHeight + 1,
                "Overflowing Backpack sale changed wallet, equipment, or capacity.");
            RequireGridReferences(
                root,
                before,
                "Overflowing Backpack sale changed inventory placement.");
        }

        private static void ValidateDeferredUnequipPreviewAndCommit(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition,
            ItemDefinition rotatedMarkerDefinition)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var backpack = new InventoryItemData(backpackDefinition);
            var displacedMarker = new InventoryItemData(markerDefinition);
            var rotatedMarker = new InventoryItemData(rotatedMarkerDefinition)
            {
                IsRotate = true
            };
            Require(
                state.TryPlaceEquipment(
                    EquipmentSlotId.Backpack,
                    backpack,
                    out string error),
                error);
            root.InsertInventoryItem(0, displacedMarker);
            root.InsertInventoryItem(BaseWidth * BaseHeight, rotatedMarker);

            root.IsDirty = false;
            state.Equipment.IsDirty = false;
            InventoryStateSnapshot beforePreview = CaptureState(
                state,
                backpack,
                displacedMarker,
                rotatedMarker);
            Require(
                state.CanUnequipToPlayerInventoryAt(
                    EquipmentSlotId.Backpack,
                    0,
                    false,
                    out error),
                error);
            RequireStateUnchanged(
                state,
                beforePreview,
                "Successful exact Backpack preview changed authoritative state.");

            Require(
                state.TryUnequipToPlayerInventoryAt(
                    EquipmentSlotId.Backpack,
                    0,
                    false,
                    out error),
                error);
            Require(
                state.Equipment.GetItem(EquipmentSlotId.Backpack) == null &&
                root.CapacityHeight == BaseHeight,
                "Deferred Backpack commit did not clear equipment and restore base height.");
            Require(
                ReferenceEquals(backpack.InventoryOwner, root) &&
                RequireIndex(root, backpack) == 0 &&
                !backpack.IsRotate,
                "Deferred Backpack commit did not place the same instance at the exact target.");
            Require(
                ReferenceEquals(displacedMarker.InventoryOwner, root) &&
                ReferenceEquals(rotatedMarker.InventoryOwner, root) &&
                RequireIndex(root, displacedMarker) < BaseWidth * BaseHeight &&
                RequireIndex(root, rotatedMarker) < BaseWidth * BaseHeight,
                "Deferred Backpack commit did not preserve and repack existing root items.");
        }

        private static void ValidateEquipmentPanelDefersBackpackPick(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            var backpack = new InventoryItemData(backpackDefinition);
            var marker = new InventoryItemData(markerDefinition);
            GameObject panelObject = null;
            try
            {
                Require(
                    state.TryPlaceEquipment(
                        EquipmentSlotId.Backpack,
                        backpack,
                        out string error),
                    error);
                state.Inventory.InsertInventoryItem(BaseWidth * BaseHeight, marker);

                panelObject = new GameObject(
                    "Transient Deferred Backpack Panel Validation",
                    typeof(RectTransform),
                    typeof(EquipmentPanelView));
                EquipmentPanelView panel = panelObject.GetComponent<EquipmentPanelView>();
                var cells = new EquipmentSlotCell[EquipmentSlotCatalog.Count];
                for (int index = 0; index < cells.Length; index++)
                {
                    var cellObject = new GameObject(
                        $"Transient {EquipmentSlotCatalog.GetSlotAtIndex(index)} Cell",
                        typeof(RectTransform),
                        typeof(EquipmentSlotCell));
                    cellObject.transform.SetParent(panelObject.transform, false);
                    cells[index] = cellObject.GetComponent<EquipmentSlotCell>();
                    cells[index].Configure(EquipmentSlotCatalog.GetSlotAtIndex(index));
                }

                var serialized = new SerializedObject(panel);
                SerializedProperty slotCells = serialized.FindProperty("slotCells");
                slotCells.arraySize = cells.Length;
                for (int index = 0; index < cells.Length; index++)
                {
                    slotCells.GetArrayElementAtIndex(index).objectReferenceValue = cells[index];
                }

                serialized.ApplyModifiedPropertiesWithoutUndo();
                panel.BindPlayerState(state);
                state.Inventory.IsDirty = false;
                state.Equipment.IsDirty = false;
                InventoryStateSnapshot beforePick = CaptureState(state, backpack, marker);
                EquipmentSlotCell backpackCell =
                    cells[EquipmentSlotCatalog.GetIndex(EquipmentSlotId.Backpack)];

                Require(panel.OnPick(backpackCell), "Equipment panel rejected Backpack drag start.");
                Require(
                    panel.IsDeferredDropActive(backpack) && backpackCell.CellData == null,
                    "Equipment panel did not keep a deferred Backpack carry after drag start.");
                RequireStateUnchanged(
                    state,
                    beforePick,
                    "Backpack drag start changed equipment, capacity, placement, or ownership.");

                panel.OnDroped(false);
                Require(
                    ReferenceEquals(backpackCell.CellData, backpack) &&
                    !panel.IsDeferredDropActive(backpack),
                    "Cancelled deferred Backpack drag did not restore its slot presentation.");
                RequireStateUnchanged(
                    state,
                    beforePick,
                    "Cancelled deferred Backpack drag changed authoritative state.");
            }
            finally
            {
                DestroyTransient(panelObject);
            }
        }

        private static void ValidateDeferredUnequipFailureIsAtomic(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var backpack = new InventoryItemData(backpackDefinition);
            Require(
                state.TryPlaceEquipment(
                    EquipmentSlotId.Backpack,
                    backpack,
                    out string error),
                error);

            var markers = new List<InventoryItemData>();
            for (int index = 0; index <= BaseWidth * BaseHeight; index++)
            {
                var marker = new InventoryItemData(markerDefinition);
                markers.Add(marker);
                root.InsertInventoryItem(index, marker);
            }

            root.IsDirty = false;
            state.Equipment.IsDirty = false;
            var trackedItems = new List<IVariableInventoryCellData>(markers.Count + 1)
            {
                backpack
            };
            trackedItems.AddRange(markers);
            InventoryStateSnapshot beforePreview = CaptureState(
                state,
                trackedItems.ToArray());
            Require(
                !state.CanUnequipToPlayerInventoryAt(
                    EquipmentSlotId.Backpack,
                    0,
                    false,
                    out error),
                "Exact Backpack preview succeeded although the target base grid cannot fit " +
                "the equipped Backpack and 73 existing items.");
            RequireStateUnchanged(
                state,
                beforePreview,
                "Failed exact Backpack preview changed authoritative state.");

            Require(
                !state.TryUnequipToPlayerInventoryAt(
                    EquipmentSlotId.Backpack,
                    0,
                    false,
                    out error),
                "Deferred Backpack commit succeeded after the same exact preview was rejected.");
            RequireStateUnchanged(
                state,
                beforePreview,
                "Failed deferred Backpack commit was not atomic.");
        }

        private static void ValidateDetachedSmallerReplacementPreview(
            ItemDefinition smallerBackpackDefinition,
            ItemDefinition equippedBackpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var equippedBackpack = new InventoryItemData(equippedBackpackDefinition);
            var detachedReplacement = new InventoryItemData(smallerBackpackDefinition);
            Require(
                state.TryPlaceEquipment(
                    EquipmentSlotId.Backpack,
                    equippedBackpack,
                    out string error),
                error);

            int smallerCapacity =
                BaseWidth * (BaseHeight + smallerBackpackDefinition.BackpackBonusRows);
            var markers = new List<InventoryItemData>(smallerCapacity);
            for (int index = 0; index < smallerCapacity; index++)
            {
                var marker = new InventoryItemData(markerDefinition);
                markers.Add(marker);
                root.InsertInventoryItem(index, marker);
            }

            root.IsDirty = false;
            state.Equipment.IsDirty = false;
            var trackedItems = new List<IVariableInventoryCellData>(markers.Count + 2)
            {
                equippedBackpack,
                detachedReplacement
            };
            trackedItems.AddRange(markers);
            InventoryStateSnapshot fullPreview = CaptureState(
                state,
                trackedItems.ToArray());
            Require(
                !state.CanUpgradeBackpackWithDetachedReplacement(
                    detachedReplacement,
                    out error),
                "Smaller Backpack preview ignored the old equipped Backpack's storage cell.");
            RequireStateUnchanged(
                state,
                fullPreview,
                "Rejected smaller Backpack preview changed authoritative state.");

            InventoryItemData removedMarker = markers[markers.Count - 1];
            int removedIndex = RequireIndex(root, removedMarker);
            root.InsertInventoryItem(removedIndex, null);
            Require(
                removedMarker.InventoryOwner == null,
                "Could not detach the marker used to expose one target-capacity cell.");
            root.IsDirty = false;
            state.Equipment.IsDirty = false;
            InventoryStateSnapshot oneCellFreePreview = CaptureState(
                state,
                equippedBackpack,
                detachedReplacement,
                removedMarker);
            Require(
                state.CanUpgradeBackpackWithDetachedReplacement(
                    detachedReplacement,
                    out error),
                error);
            RequireStateUnchanged(
                state,
                oneCellFreePreview,
                "Accepted smaller Backpack preview changed authoritative state.");
        }

        private static void ValidateStagedTakeNotificationBoundary(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            StandardStashViewData root = state.Inventory;
            var backpack = new InventoryItemData(backpackDefinition);
            var marker = new InventoryItemData(markerDefinition);
            Require(
                state.TryPlaceEquipment(
                    EquipmentSlotId.Backpack,
                    backpack,
                    out string error),
                error);
            int markerOriginalIndex = BaseWidth * BaseHeight;
            root.InsertInventoryItem(markerOriginalIndex, marker);

            int equipmentNotifications = 0;
            int capacityNotifications = 0;
            state.Equipment.Changed += () => equipmentNotifications++;
            state.CapacityChanged += () => capacityNotifications++;
            IVariableInventoryCellData[] beforeCells =
                (IVariableInventoryCellData[])root.CellData.Clone();
            bool markerOriginalRotation = marker.IsRotate;

            Require(
                state.TryStageTakeEquipment(
                    EquipmentSlotId.Backpack,
                    out IVariableInventoryCellData stagedItem,
                    out PlayerInventoryState.EquipmentTakeReceipt stagedReceipt,
                    out error),
                error);
            Require(
                ReferenceEquals(stagedItem, backpack) &&
                equipmentNotifications == 0 && capacityNotifications == 0,
                "Staged Backpack take notified observers before a destination was complete.");
            Require(state.TryRestoreTakenEquipment(stagedReceipt, out error), error);
            Require(
                equipmentNotifications == 0 && capacityNotifications == 0 &&
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), backpack) &&
                root.CapacityHeight == BaseHeight + backpackDefinition.BackpackBonusRows &&
                marker.IsRotate == markerOriginalRotation,
                "Unpublished staged-take rollback emitted notifications or lost state.");
            RequireGridReferences(
                root,
                beforeCells,
                "Unpublished staged-take rollback did not restore the exact layout.");

            Require(
                state.TryStageTakeEquipment(
                    EquipmentSlotId.Backpack,
                    out stagedItem,
                    out stagedReceipt,
                    out error),
                error);
            Require(
                state.TryPrepareStagedEquipmentTakePublication(
                    stagedReceipt,
                    out error),
                error);
            var external = new StandardStashViewData(2, 2);
            Require(external.CheckInsert(0, stagedItem), "External fixture rejected staged bag.");
            external.InsertInventoryItem(0, stagedItem);
            Require(
                equipmentNotifications == 0 && capacityNotifications == 0,
                "Destination insertion published the staged equipment change too early.");
            Require(
                state.TryPublishStagedEquipmentTake(stagedReceipt, out error),
                error);
            Require(
                equipmentNotifications == 1 && capacityNotifications == 1 &&
                ReferenceEquals(backpack.InventoryOwner, external) &&
                state.Equipment.GetItem(EquipmentSlotId.Backpack) == null &&
                root.CapacityHeight == BaseHeight,
                "Completed staged transfer did not publish one consistent equipment/capacity change.");
        }

        private static void ValidateCoordinatorReplacementPreview(
            ItemDefinition smallBackpackDefinition,
            ItemDefinition mediumBackpackDefinition,
            ItemDefinition largeBackpackDefinition,
            ItemDefinition fragmentedBackpackDefinition,
            ItemDefinition markerDefinition,
            ItemDatabase database)
        {
            PlayerInventoryState state = CreateState();
            var smallBackpack = new InventoryItemData(smallBackpackDefinition);
            var largeBackpack = new InventoryItemData(largeBackpackDefinition);
            var stableMarker = new InventoryItemData(markerDefinition);
            Require(
                state.TryPlaceEquipment(EquipmentSlotId.Backpack, smallBackpack, out string error),
                error);
            state.Inventory.InsertInventoryItem(0, largeBackpack);
            state.Inventory.InsertInventoryItem(8, stableMarker);
            int stableMarkerIndex = RequireIndex(state.Inventory, stableMarker);

            var sourceView = new BoundViewStub(state.Inventory);
            var coordinator = new InventoryTransferCoordinator(state, null, null, null);
            Require(
                coordinator.CanEquip(sourceView, largeBackpack),
                "Larger Backpack was not offered as an upgrade.");
            Require(coordinator.TryEquip(sourceView, largeBackpack, out error), error);
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), largeBackpack) &&
                state.Inventory.CapacityHeight == BaseHeight + 3 &&
                ReferenceEquals(smallBackpack.InventoryOwner, state.Inventory) &&
                state.Inventory.GetId(smallBackpack).HasValue &&
                RequireIndex(state.Inventory, stableMarker) == stableMarkerIndex,
                "Larger replacement did not equip the new bag and store the old bag.");

            var mediumBackpack = new InventoryItemData(mediumBackpackDefinition);
            int mediumIndex = state.Inventory.GetInsertableId(mediumBackpack) ?? -1;
            Require(mediumIndex >= 0, "Could not prepare the smaller Backpack fixture.");
            state.Inventory.InsertInventoryItem(mediumIndex, mediumBackpack);
            int storedSmallBackpackIndex = RequireIndex(state.Inventory, smallBackpack);
            Require(
                coordinator.CanEquip(sourceView, mediumBackpack),
                "A smaller Backpack with sufficient previewed space was not offered.");
            Require(
                coordinator.TryEquip(sourceView, mediumBackpack, out error),
                error);
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), mediumBackpack) &&
                state.Inventory.CapacityHeight == BaseHeight + 2 &&
                ReferenceEquals(largeBackpack.InventoryOwner, state.Inventory) &&
                state.Inventory.GetId(largeBackpack).HasValue &&
                RequireIndex(state.Inventory, smallBackpack) == storedSmallBackpackIndex &&
                RequireIndex(state.Inventory, stableMarker) == stableMarkerIndex,
                "Smaller replacement did not preserve the already-fitting layout.");

            var equalBackpack = new InventoryItemData(mediumBackpackDefinition);
            int equalIndex = state.Inventory.GetInsertableId(equalBackpack) ?? -1;
            Require(equalIndex >= 0, "Could not prepare the equal-capacity Backpack fixture.");
            state.Inventory.InsertInventoryItem(equalIndex, equalBackpack);
            Require(
                coordinator.CanEquip(sourceView, equalBackpack) &&
                coordinator.TryEquip(sourceView, equalBackpack, out error),
                error ?? "Equal-capacity Backpack replacement was not allowed.");
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), equalBackpack) &&
                state.Inventory.CapacityHeight == BaseHeight + 2 &&
                ReferenceEquals(mediumBackpack.InventoryOwner, state.Inventory),
                "Equal-capacity replacement lost a Backpack or changed capacity.");

            Require(
                InventorySaveCodec.TryCapture(
                    state, database, out PlayerItemStateSaveData save, out error),
                error);
            Require(
                save.inventoryHeight == BaseHeight + 2,
                "Expanded Backpack saved incorrect dimensions.");
            Require(
                InventorySaveCodec.TryRestore(
                    save, database, BaseWidth, BaseHeight,
                    out PlayerInventoryState restored, out error),
                error);
            Require(
                restored.Inventory.CapacityHeight == BaseHeight + 2 &&
                restored.Equipment.GetItem(EquipmentSlotId.Backpack) is InventoryItemData restoredBag &&
                restoredBag.Definition.Id == mediumBackpackDefinition.Id,
                "Expanded Backpack save round-trip lost capacity or equipment.");

            ValidateFragmentedReplacementPreview(
                smallBackpackDefinition,
                fragmentedBackpackDefinition,
                markerDefinition);
        }

        private static void ValidateFragmentedReplacementPreview(
            ItemDefinition smallBackpackDefinition,
            ItemDefinition fragmentedBackpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            var equippedBackpack = new InventoryItemData(fragmentedBackpackDefinition);
            var replacement = new InventoryItemData(smallBackpackDefinition);
            Require(
                state.TryPlaceEquipment(
                    EquipmentSlotId.Backpack,
                    equippedBackpack,
                    out string error),
                error);
            state.Inventory.InsertInventoryItem(0, replacement);

            InventoryItemData trackedMarker = null;
            int targetHeight = BaseHeight + smallBackpackDefinition.BackpackBonusRows;
            for (int y = 0; y < targetHeight; y++)
            {
                for (int x = 0; x < BaseWidth; x++)
                {
                    int index = x + y * BaseWidth;
                    if (((x + y) & 1) != 0 || index == 0)
                    {
                        continue;
                    }

                    var marker = new InventoryItemData(markerDefinition);
                    state.Inventory.InsertInventoryItem(index, marker);
                    if (index == 4)
                    {
                        trackedMarker = marker;
                    }
                }
            }

            Require(trackedMarker != null, "Fragmented replacement fixture has no marker.");
            int trackedBefore = RequireIndex(state.Inventory, trackedMarker);
            var coordinator = new InventoryTransferCoordinator(state, null, null, null);
            var sourceView = new BoundViewStub(state.Inventory);
            Require(
                coordinator.TryEquip(sourceView, replacement, out error),
                error);
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), replacement) &&
                state.Inventory.CapacityHeight == targetHeight &&
                ReferenceEquals(equippedBackpack.InventoryOwner, state.Inventory) &&
                state.Inventory.GetId(equippedBackpack).HasValue,
                "Previewed repack did not store the old Backpack in the smaller grid.");
            Require(
                RequireIndex(state.Inventory, trackedMarker) != trackedBefore,
                "The fragmented fixture unexpectedly succeeded without applying its previewed repack.");
        }

        private static void ValidateCoordinatorUpgradeRollback(
            ItemDefinition wideSmallBackpackDefinition,
            ItemDefinition mediumBackpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            var wideBackpack = new InventoryItemData(wideSmallBackpackDefinition);
            Require(
                state.TryPlaceEquipment(EquipmentSlotId.Backpack, wideBackpack, out string error),
                error);

            var replacement = new InventoryItemData(mediumBackpackDefinition);
            state.Inventory.InsertInventoryItem(0, replacement);
            for (int index = 1; index < state.Inventory.CellData.Length; index++)
            {
                state.Inventory.InsertInventoryItem(index, new InventoryItemData(markerDefinition));
            }

            IVariableInventoryCellData[] before =
                (IVariableInventoryCellData[])state.Inventory.CellData.Clone();
            var coordinator = new InventoryTransferCoordinator(state, null, null, null);
            var sourceView = new BoundViewStub(state.Inventory);
            Require(
                !coordinator.TryEquip(sourceView, replacement, out error),
                "Upgrade succeeded although the old 4x4 Backpack could not be stored.");
            Require(
                ReferenceEquals(state.Equipment.GetItem(EquipmentSlotId.Backpack), wideBackpack) &&
                state.Inventory.CapacityHeight == BaseHeight + 1 &&
                ReferenceEquals(replacement.InventoryOwner, state.Inventory),
                "Failed upgrade did not restore equipment/capacity/ownership.");
            RequireGridReferences(
                state.Inventory, before,
                "Failed upgrade did not restore the exact source layout.");
        }

        private static void ValidateDiscardRestoresBaseHeight(
            ItemDefinition backpackDefinition,
            ItemDefinition markerDefinition)
        {
            PlayerInventoryState state = CreateState();
            var backpack = new InventoryItemData(backpackDefinition);
            var marker = new InventoryItemData(markerDefinition);
            Require(
                state.TryPlaceEquipment(EquipmentSlotId.Backpack, backpack, out string error),
                error);
            state.Inventory.InsertInventoryItem(BaseWidth * BaseHeight, marker);
            Require(state.TryDiscardAllCarriedItems(out error), error);
            Require(
                state.Inventory.CapacityHeight == BaseHeight &&
                state.Equipment.GetItem(EquipmentSlotId.Backpack) == null &&
                backpack.InventoryOwner == null &&
                marker.InventoryOwner == null,
                "Discard did not clear equipment/items and restore base capacity.");
            for (int index = 0; index < state.Inventory.CellData.Length; index++)
            {
                Require(state.Inventory.CellData[index] == null, "Discard left a root item behind.");
            }
        }

        private static void ValidateInvalidDefinitionContract(
            ICollection<ItemDefinition> definitions)
        {
            ItemDefinition invalid = AddDefinition(
                definitions, 900007, "Invalid Capacity Item", 1, 1,
                EquipmentSlotType.BodyArmor, 1);
            Require(
                !invalid.TryValidateInventoryShape(out _),
                "A non-Backpack item was allowed to grant inventory rows.");
        }

        private static PlayerInventoryState CreateState()
        {
            return new PlayerInventoryState(
                new StandardStashViewData(BaseWidth, BaseHeight),
                new EquipmentLoadoutData(),
                new FantasySurvival.Trading.PlayerWallet(),
                BaseWidth,
                BaseHeight);
        }

        private static ItemDefinition AddDefinition(
            ICollection<ItemDefinition> definitions,
            int id,
            string displayName,
            int width,
            int height,
            EquipmentSlotType equipmentSlot,
            int backpackBonusRows)
        {
            ItemDefinition definition = ScriptableObject.CreateInstance<ItemDefinition>();
            definition.name = displayName;
            var serialized = new SerializedObject(definition);
            serialized.FindProperty("id").intValue = id;
            serialized.FindProperty("displayName").stringValue = displayName;
            serialized.FindProperty("width").intValue = width;
            serialized.FindProperty("height").intValue = height;
            serialized.FindProperty("maxStackSize").intValue = 1;
            serialized.FindProperty("equipmentSlot").enumValueIndex = (int)equipmentSlot;
            serialized.FindProperty("backpackBonusRows").intValue = backpackBonusRows;
            bool isPrototypeBackpack = equipmentSlot == EquipmentSlotType.Backpack;
            serialized.FindProperty("isTradable").boolValue = isPrototypeBackpack;
            serialized.FindProperty("tradeCurrency").intValue =
                (int)FantasySurvival.Trading.TradeCurrency.Silver;
            serialized.FindProperty("tradePrice").intValue = isPrototypeBackpack ? 1 : 0;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            definitions.Add(definition);
            return definition;
        }

        private static ItemDatabase CreateDatabase(params ItemDefinition[] definitions)
        {
            ItemDatabase database = ScriptableObject.CreateInstance<ItemDatabase>();
            database.name = "Transient Backpack Validation Database";
            var serialized = new SerializedObject(database);
            SerializedProperty items = serialized.FindProperty("items");
            items.arraySize = definitions.Length;
            for (int index = 0; index < definitions.Length; index++)
            {
                items.GetArrayElementAtIndex(index).objectReferenceValue = definitions[index];
            }

            serialized.FindProperty("nextDefinitionId").intValue = 900008;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            Require(database.TryValidate(out string error), error);
            return database;
        }

        private static int RequireIndex(
            IVariableInventoryViewData inventory,
            IVariableInventoryCellData item)
        {
            int? index = inventory.GetId(item);
            Require(index.HasValue, "Expected item is missing from its inventory.");
            return index.Value;
        }

        private static InventoryItemData RequireDefinition(
            StandardStashViewData inventory,
            int definitionId)
        {
            for (int index = 0; index < inventory.CellData.Length; index++)
            {
                if (inventory.CellData[index] is InventoryItemData item &&
                    item.Definition.Id == definitionId)
                {
                    return item;
                }
            }

            throw new InvalidOperationException(
                $"Definition {definitionId} is missing from restored inventory.");
        }

        private static void RequireGridReferences(
            StandardStashViewData inventory,
            IReadOnlyList<IVariableInventoryCellData> expected,
            string message)
        {
            Require(inventory.CellData.Length == expected.Count, message);
            for (int index = 0; index < expected.Count; index++)
            {
                Require(ReferenceEquals(inventory.CellData[index], expected[index]), message);
                if (inventory.CellData[index] is IVariableInventoryOwnedCellData owned)
                {
                    Require(ReferenceEquals(owned.InventoryOwner, inventory), message);
                }
            }
        }

        private static InventoryStateSnapshot CaptureState(
            PlayerInventoryState state,
            params IVariableInventoryCellData[] additionalItems)
        {
            var uniqueItems = new List<IVariableInventoryCellData>();
            for (int index = 0; index < state.Inventory.CellData.Length; index++)
            {
                AddUniqueReference(uniqueItems, state.Inventory.CellData[index]);
            }

            var equipment = new IVariableInventoryCellData[EquipmentSlotCatalog.Count];
            for (int index = 0; index < EquipmentSlotCatalog.Count; index++)
            {
                equipment[index] = state.Equipment.GetItem(
                    EquipmentSlotCatalog.GetSlotAtIndex(index));
                AddUniqueReference(uniqueItems, equipment[index]);
            }

            if (additionalItems != null)
            {
                foreach (IVariableInventoryCellData item in additionalItems)
                {
                    AddUniqueReference(uniqueItems, item);
                }
            }

            var itemStates = new ItemStateSnapshot[uniqueItems.Count];
            for (int index = 0; index < uniqueItems.Count; index++)
            {
                IVariableInventoryCellData item = uniqueItems[index];
                itemStates[index] = new ItemStateSnapshot(
                    item,
                    item.IsRotate,
                    item is IVariableInventoryOwnedCellData owned
                        ? owned.InventoryOwner
                        : null);
            }

            return new InventoryStateSnapshot(
                state.Inventory.CapacityHeight,
                state.Inventory.LayoutVersion,
                (IVariableInventoryCellData[])state.Inventory.CellData.Clone(),
                equipment,
                itemStates,
                state.Inventory.IsDirty,
                state.Equipment.IsDirty);
        }

        private static void RequireStateUnchanged(
            PlayerInventoryState state,
            InventoryStateSnapshot expected,
            string message)
        {
            Require(state.Inventory.CapacityHeight == expected.Height, message);
            Require(state.Inventory.LayoutVersion == expected.LayoutVersion, message);
            Require(state.Inventory.IsDirty == expected.InventoryIsDirty, message);
            Require(state.Equipment.IsDirty == expected.EquipmentIsDirty, message);
            RequireGridReferences(state.Inventory, expected.Cells, message);

            for (int index = 0; index < expected.Equipment.Length; index++)
            {
                Require(
                    ReferenceEquals(
                        state.Equipment.GetItem(EquipmentSlotCatalog.GetSlotAtIndex(index)),
                        expected.Equipment[index]),
                    message);
            }

            foreach (ItemStateSnapshot itemState in expected.Items)
            {
                Require(itemState.Item.IsRotate == itemState.Rotation, message);
                IVariableInventoryViewData owner =
                    itemState.Item is IVariableInventoryOwnedCellData owned
                        ? owned.InventoryOwner
                        : null;
                Require(ReferenceEquals(owner, itemState.Owner), message);
            }
        }

        private static void AddUniqueReference(
            ICollection<IVariableInventoryCellData> items,
            IVariableInventoryCellData candidate)
        {
            if (candidate == null)
            {
                return;
            }

            foreach (IVariableInventoryCellData item in items)
            {
                if (ReferenceEquals(item, candidate))
                {
                    return;
                }
            }

            items.Add(candidate);
        }

        private static void DestroyTransient(UnityEngine.Object transient)
        {
            if (transient != null)
            {
                UnityEngine.Object.DestroyImmediate(transient);
            }
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new InvalidOperationException(message);
            }
        }

        private sealed class BoundViewStub : IVariableInventoryBoundView
        {
            public BoundViewStub(IVariableInventoryViewData viewData)
            {
                ViewData = viewData;
            }

            public IVariableInventoryViewData ViewData { get; }
            public bool ContainsCell(IVariableInventoryCell cell) => false;
            public void SetDropPreviewHandling(VariableInventoryDropHandling? handling) { }
            public void SetCellCallback(
                Action<IVariableInventoryCell> onCellClick,
                Action<IVariableInventoryCell> onCellOptionClick,
                Action<IVariableInventoryCell> onCellEnter,
                Action<IVariableInventoryCell> onCellExit) { }
            public void Apply(IVariableInventoryViewData data) { }
            public void ReApply() { }
            public void OnPrePick(IVariableInventoryCell stareCell) { }
            public bool OnPick(IVariableInventoryCell stareCell) => false;
            public void OnDrag(
                IVariableInventoryCell stareCell,
                IVariableInventoryCell effectCell,
                PointerEventData cursorPosition) { }
            public bool OnDrop(
                IVariableInventoryCell stareCell,
                IVariableInventoryCell effectCell) => false;
            public void OnDroped(bool isDroped) { }
            public void OnCellEnter(
                IVariableInventoryCell stareCell,
                IVariableInventoryCell effectCell) { }
            public void OnCellExit(IVariableInventoryCell stareCell) { }
            public void OnSwitchRotate(
                IVariableInventoryCell stareCell,
                IVariableInventoryCell effectCell) { }
        }

        private sealed class InventoryStateSnapshot
        {
            public InventoryStateSnapshot(
                int height,
                long layoutVersion,
                IVariableInventoryCellData[] cells,
                IVariableInventoryCellData[] equipment,
                ItemStateSnapshot[] items,
                bool inventoryIsDirty,
                bool equipmentIsDirty)
            {
                Height = height;
                LayoutVersion = layoutVersion;
                Cells = cells;
                Equipment = equipment;
                Items = items;
                InventoryIsDirty = inventoryIsDirty;
                EquipmentIsDirty = equipmentIsDirty;
            }

            public int Height { get; }
            public long LayoutVersion { get; }
            public IVariableInventoryCellData[] Cells { get; }
            public IVariableInventoryCellData[] Equipment { get; }
            public ItemStateSnapshot[] Items { get; }
            public bool InventoryIsDirty { get; }
            public bool EquipmentIsDirty { get; }
        }

        private sealed class ItemStateSnapshot
        {
            public ItemStateSnapshot(
                IVariableInventoryCellData item,
                bool rotation,
                IVariableInventoryViewData owner)
            {
                Item = item;
                Rotation = rotation;
                Owner = owner;
            }

            public IVariableInventoryCellData Item { get; }
            public bool Rotation { get; }
            public IVariableInventoryViewData Owner { get; }
        }
    }
}
