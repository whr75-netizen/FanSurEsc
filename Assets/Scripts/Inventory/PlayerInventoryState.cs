using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using FantasySurvival.Trading;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public enum EquipmentSlotType
    {
        None = 0,
        Headgear = 1,
        BodyArmor = 2,
        FunctionalShoes = 3,
        Backpack = 4,
        Necklace = 5,
        Ring = 6,
        Pendant = 7,
        CosmeticHead = 8,
        CosmeticTop = 9,
        CosmeticBottom = 10,
        CosmeticShoes = 11,
        Weapon = 12
    }

    public enum EquipmentSlotId
    {
        None = 0,
        Headgear = 1,
        BodyArmor = 2,
        FunctionalShoes = 3,
        Backpack = 4,
        Necklace = 5,
        Ring = 6,
        Pendant = 7,
        CosmeticHead = 8,
        CosmeticTop = 9,
        CosmeticBottom = 10,
        CosmeticShoes = 11,
        Weapon1 = 12,
        Weapon2 = 13,
        Weapon3 = 14
    }

    public static class EquipmentSlotCatalog
    {
        public const int WeaponSlotCount = 3;

        private static readonly EquipmentSlotId[] orderedSlots =
        {
            EquipmentSlotId.Headgear,
            EquipmentSlotId.BodyArmor,
            EquipmentSlotId.FunctionalShoes,
            EquipmentSlotId.Backpack,
            EquipmentSlotId.Necklace,
            EquipmentSlotId.Ring,
            EquipmentSlotId.Pendant,
            EquipmentSlotId.CosmeticHead,
            EquipmentSlotId.CosmeticTop,
            EquipmentSlotId.CosmeticBottom,
            EquipmentSlotId.CosmeticShoes,
            EquipmentSlotId.Weapon1,
            EquipmentSlotId.Weapon2,
            EquipmentSlotId.Weapon3
        };

        public static IReadOnlyList<EquipmentSlotId> OrderedSlots => orderedSlots;
        public static int Count => orderedSlots.Length;

        public static bool IsValid(EquipmentSlotId slot)
        {
            return slot >= EquipmentSlotId.Headgear && slot <= EquipmentSlotId.Weapon3;
        }

        public static int GetIndex(EquipmentSlotId slot)
        {
            return IsValid(slot) ? (int)slot - 1 : -1;
        }

        public static EquipmentSlotId GetSlotAtIndex(int index)
        {
            return index >= 0 && index < orderedSlots.Length
                ? orderedSlots[index]
                : EquipmentSlotId.None;
        }

        public static EquipmentSlotType GetSlotType(EquipmentSlotId slot)
        {
            if (!IsValid(slot))
            {
                return EquipmentSlotType.None;
            }

            return slot >= EquipmentSlotId.Weapon1
                ? EquipmentSlotType.Weapon
                : (EquipmentSlotType)slot;
        }

        public static EquipmentSlotId GetPrimarySlot(EquipmentSlotType type)
        {
            if (type == EquipmentSlotType.None)
            {
                return EquipmentSlotId.None;
            }

            return type == EquipmentSlotType.Weapon
                ? EquipmentSlotId.Weapon1
                : (EquipmentSlotId)type;
        }

        public static EquipmentSlotId GetWeaponSlot(int oneBasedNumber)
        {
            switch (oneBasedNumber)
            {
                case 1: return EquipmentSlotId.Weapon1;
                case 2: return EquipmentSlotId.Weapon2;
                case 3: return EquipmentSlotId.Weapon3;
                default: return EquipmentSlotId.None;
            }
        }

        public static int GetWeaponNumber(EquipmentSlotId slot)
        {
            return slot >= EquipmentSlotId.Weapon1 && slot <= EquipmentSlotId.Weapon3
                ? (int)slot - (int)EquipmentSlotId.Weapon1 + 1
                : 0;
        }

        public static string GetDisplayName(EquipmentSlotId slot)
        {
            switch (slot)
            {
                case EquipmentSlotId.Headgear: return "모자";
                case EquipmentSlotId.BodyArmor: return "갑빠";
                case EquipmentSlotId.FunctionalShoes: return "신발";
                case EquipmentSlotId.Backpack: return "가방";
                case EquipmentSlotId.Necklace: return "목걸이";
                case EquipmentSlotId.Ring: return "반지";
                case EquipmentSlotId.Pendant: return "팬던트";
                case EquipmentSlotId.CosmeticHead: return "꾸밈 머리";
                case EquipmentSlotId.CosmeticTop: return "꾸밈 상의";
                case EquipmentSlotId.CosmeticBottom: return "꾸밈 하의";
                case EquipmentSlotId.CosmeticShoes: return "꾸밈 신발";
                case EquipmentSlotId.Weapon1: return "무기 1";
                case EquipmentSlotId.Weapon2: return "무기 2";
                case EquipmentSlotId.Weapon3: return "무기 3";
                default: return "장비 없음";
            }
        }

        public static string GetShortLabel(EquipmentSlotId slot)
        {
            switch (slot)
            {
                case EquipmentSlotId.Headgear: return "HAT";
                case EquipmentSlotId.BodyArmor: return "ARM";
                case EquipmentSlotId.FunctionalShoes: return "SHO";
                case EquipmentSlotId.Backpack: return "BAG";
                case EquipmentSlotId.Necklace: return "NEC";
                case EquipmentSlotId.Ring: return "RNG";
                case EquipmentSlotId.Pendant: return "PEN";
                case EquipmentSlotId.CosmeticHead: return "C-H";
                case EquipmentSlotId.CosmeticTop: return "C-T";
                case EquipmentSlotId.CosmeticBottom: return "C-B";
                case EquipmentSlotId.CosmeticShoes: return "C-S";
                case EquipmentSlotId.Weapon1: return "W1";
                case EquipmentSlotId.Weapon2: return "W2";
                case EquipmentSlotId.Weapon3: return "W3";
                default: return "---";
            }
        }
    }

    public sealed class EquipmentLoadoutData : IVariableInventoryViewData
    {
        private readonly IVariableInventoryCellData[] items =
            new IVariableInventoryCellData[EquipmentSlotCatalog.Count];

        public event Action Changed;

        public bool IsDirty { get; set; } = true;

        public IVariableInventoryCellData GetItem(EquipmentSlotId slot)
        {
            int index = EquipmentSlotCatalog.GetIndex(slot);
            return index >= 0 ? items[index] : null;
        }

        public int? GetId(IVariableInventoryCellData cellData)
        {
            if (cellData == null)
            {
                return null;
            }

            for (int i = 0; i < items.Length; i++)
            {
                if (ReferenceEquals(items[i], cellData))
                {
                    return i;
                }
            }

            return null;
        }

        public int? GetInsertableId(IVariableInventoryCellData cellData)
        {
            if (!(cellData is InventoryItemData item))
            {
                return null;
            }

            EquipmentSlotId slot = GetFirstAvailableSlot(item.Definition);
            int index = EquipmentSlotCatalog.GetIndex(slot);
            return index >= 0 && CheckInsert(index, cellData) ? index : (int?)null;
        }

        public EquipmentSlotId GetFirstAvailableSlot(ItemDefinition definition)
        {
            if (definition == null || !definition.IsEquippable)
            {
                return EquipmentSlotId.None;
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                int index = EquipmentSlotCatalog.GetIndex(slot);
                if (items[index] == null && definition.CanEquipIn(slot))
                {
                    return slot;
                }
            }

            return EquipmentSlotId.None;
        }

        public bool CheckInsert(int id, IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= items.Length || items[id] != null ||
                !(cellData is InventoryItemData item))
            {
                return false;
            }

            EquipmentSlotId slot = EquipmentSlotCatalog.GetSlotAtIndex(id);
            if (!item.Definition.CanEquipIn(slot))
            {
                return false;
            }

            return !(cellData is IVariableInventoryOwnedCellData owned) || owned.InventoryOwner == null;
        }

        public void InsertInventoryItem(int id, IVariableInventoryCellData cellData)
        {
            if (id < 0 || id >= items.Length)
            {
                throw new ArgumentOutOfRangeException(nameof(id));
            }

            var previous = items[id];
            if (ReferenceEquals(previous, cellData))
            {
                return;
            }

            if (cellData != null && !CheckInsert(id, cellData))
            {
                throw new InvalidOperationException("The item cannot be equipped in this slot.");
            }

            if (previous is IVariableInventoryOwnedCellData outgoing &&
                !outgoing.TryChangeInventoryOwner(this, null))
            {
                throw new InvalidOperationException("The equipped item ownership is inconsistent.");
            }

            if (cellData is IVariableInventoryOwnedCellData incoming &&
                !incoming.TryChangeInventoryOwner(null, this))
            {
                if (previous is IVariableInventoryOwnedCellData rollback)
                {
                    rollback.TryChangeInventoryOwner(null, this);
                }

                throw new InvalidOperationException("Could not attach the item to the equipment loadout.");
            }

            items[id] = cellData;
            IsDirty = true;
            Changed?.Invoke();
        }

        public bool TryTake(EquipmentSlotId slot, out IVariableInventoryCellData item)
        {
            item = null;
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (index < 0 || items[index] == null)
            {
                return false;
            }

            item = items[index];
            InsertInventoryItem(index, null);
            return true;
        }

        public bool TryPlace(EquipmentSlotId slot, IVariableInventoryCellData item)
        {
            int index = EquipmentSlotCatalog.GetIndex(slot);
            if (!CheckInsert(index, item))
            {
                return false;
            }

            InsertInventoryItem(index, item);
            return true;
        }

        internal void NotifyOwnedItemStateChanged(InventoryItemData item)
        {
            if (item == null || !ReferenceEquals(item.InventoryOwner, this) ||
                !GetId(item).HasValue)
            {
                return;
            }

            IsDirty = true;
            Changed?.Invoke();
        }

        internal bool TryClearAll(out string error)
        {
            var occupied = new List<KeyValuePair<int, InventoryItemData>>();
            var seen = new HashSet<InventoryItemData>(
                InventoryReferenceComparer<InventoryItemData>.Instance);
            for (int index = 0; index < items.Length; index++)
            {
                IVariableInventoryCellData item = items[index];
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Equipment slot {index} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is equipped in more than one slot.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, this))
                {
                    error = $"Equipment slot {index} has inconsistent item ownership.";
                    return false;
                }

                occupied.Add(new KeyValuePair<int, InventoryItemData>(index, inventoryItem));
            }

            if (occupied.Count == 0)
            {
                error = null;
                return true;
            }

            int detachedCount = 0;
            for (; detachedCount < occupied.Count; detachedCount++)
            {
                InventoryItemData item = occupied[detachedCount].Value;
                if (!item.TryChangeInventoryOwner(this, null))
                {
                    var rollbackFailures = new List<int>();
                    for (int rollback = detachedCount - 1; rollback >= 0; rollback--)
                    {
                        if (!occupied[rollback].Value.TryChangeInventoryOwner(null, this))
                        {
                            rollbackFailures.Add(occupied[rollback].Key);
                        }
                    }

                    error = $"Could not detach the item in equipment slot {occupied[detachedCount].Key}." +
                            (rollbackFailures.Count == 0
                                ? string.Empty
                                : $" Equipment ownership rollback also failed for slots {string.Join(", ", rollbackFailures)}.");
                    return false;
                }
            }

            foreach (KeyValuePair<int, InventoryItemData> placement in occupied)
            {
                items[placement.Key] = null;
            }

            IsDirty = true;
            Changed?.Invoke();
            error = null;
            return true;
        }
    }

    public sealed class PlayerInventoryState
    {
        private sealed class AmmunitionMutation
        {
            public StandardStashViewData Owner;
            public int SlotIndex;
            public InventoryItemData Item;
            public int OriginalQuantity;
            public int ConsumedQuantity;

            public int RemainingQuantity => OriginalQuantity - ConsumedQuantity;
        }

        private readonly HashSet<StandardStashViewData> ammunitionCountVisitedGrids =
            new HashSet<StandardStashViewData>(
                InventoryReferenceComparer<StandardStashViewData>.Instance);

        public StandardStashViewData Inventory { get; }
        public EquipmentLoadoutData Equipment { get; }
        public PlayerWallet Wallet { get; }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment)
            : this(inventory, equipment, new PlayerWallet())
        {
        }

        public PlayerInventoryState(
            StandardStashViewData inventory,
            EquipmentLoadoutData equipment,
            PlayerWallet wallet)
        {
            Inventory = inventory ?? throw new ArgumentNullException(nameof(inventory));
            Equipment = equipment ?? throw new ArgumentNullException(nameof(equipment));
            Wallet = wallet ?? throw new ArgumentNullException(nameof(wallet));
        }

        public bool TryGetOwnedStackItemPlacement(
            InventoryItemData item,
            out StandardStashViewData owner,
            out int slotIndex,
            out string error)
        {
            owner = null;
            slotIndex = -1;
            if (item?.Definition == null || item.Quantity <= 0)
            {
                error = "The requested stack item is invalid.";
                return false;
            }

            if (!(item.InventoryOwner is StandardStashViewData itemOwner) ||
                !OwnsInventory(itemOwner))
            {
                error = "The requested stack item is not owned by the Player inventory.";
                return false;
            }

            int? itemSlot = itemOwner.GetId(item);
            if (!itemSlot.HasValue)
            {
                error = "The stack item owner does not contain the requested item.";
                return false;
            }

            owner = itemOwner;
            slotIndex = itemSlot.Value;
            error = null;
            return true;
        }

        public bool OwnsInventory(IVariableInventoryViewData candidate)
        {
            if (candidate == null)
            {
                return false;
            }

            if (ReferenceEquals(candidate, Inventory) ||
                ReferenceEquals(candidate, Equipment))
            {
                return true;
            }

            return IsNestedInventory(Inventory, candidate) ||
                   IsNestedInventory(Equipment, candidate);
        }

        internal static bool IsNestedInventory(
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

            var visited = new HashSet<IVariableInventoryViewData>(
                InventoryReferenceComparer<IVariableInventoryViewData>.Instance);
            return ContainsNestedInventory(root, candidate, visited);
        }

        public bool TryConsumeOneOwnedStackItem(
            InventoryItemData item,
            StandardStashViewData expectedOwner,
            int expectedSlotIndex,
            int expectedQuantity,
            out string error)
        {
            if (expectedOwner == null || expectedQuantity <= 0)
            {
                error = "The expected stack item placement is invalid.";
                return false;
            }

            if (!TryGetOwnedStackItemPlacement(
                    item,
                    out StandardStashViewData actualOwner,
                    out int actualSlotIndex,
                    out error))
            {
                return false;
            }

            if (!ReferenceEquals(actualOwner, expectedOwner) ||
                actualSlotIndex != expectedSlotIndex ||
                item.Quantity != expectedQuantity)
            {
                error = "The stack item changed before it could be consumed.";
                return false;
            }

            if (expectedQuantity > 1)
            {
                return item.TryChangeQuantity(
                    expectedOwner,
                    expectedQuantity,
                    expectedQuantity - 1,
                    out error);
            }

            try
            {
                expectedOwner.InsertInventoryItem(expectedSlotIndex, null);
            }
            catch (Exception exception)
            {
                error = $"Could not remove the consumed stack item: {exception.Message}";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryGetReloadableRoundCount(
            InventoryItemData weapon,
            out int reloadableRoundCount,
            out string error)
        {
            reloadableRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int missingRounds = weapon.MagazineCapacity - weapon.LoadedAmmunition;
            if (missingRounds <= 0)
            {
                error = null;
                return true;
            }

            if (!TryBuildAmmunitionPlan(
                    weapon.Definition.AmmunitionDefinitionId,
                    missingRounds,
                    out List<AmmunitionMutation> plan,
                    out error))
            {
                return false;
            }

            foreach (AmmunitionMutation mutation in plan)
            {
                reloadableRoundCount += mutation.ConsumedQuantity;
            }

            error = null;
            return true;
        }

        public bool TryGetReserveAmmunitionCount(
            InventoryItemData weapon,
            out int reserveRoundCount,
            out string error)
        {
            reserveRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            ammunitionCountVisitedGrids.Clear();
            long total = 0;
            try
            {
                if (!TryCountAmmunitionFromGrid(
                        Inventory,
                        weapon.Definition.AmmunitionDefinitionId,
                        ammunitionCountVisitedGrids,
                        ref total,
                        out error))
                {
                    return false;
                }

                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (!(Equipment.GetItem(slot) is InventoryContainerItemData container))
                    {
                        continue;
                    }

                    if (!TryCountAmmunitionFromGrid(
                            container.CaseData,
                            weapon.Definition.AmmunitionDefinitionId,
                            ammunitionCountVisitedGrids,
                            ref total,
                            out error))
                    {
                        return false;
                    }
                }

                reserveRoundCount = total >= int.MaxValue ? int.MaxValue : (int)total;
                error = null;
                return true;
            }
            finally
            {
                ammunitionCountVisitedGrids.Clear();
            }
        }

        public bool TryConsumeLoadedRound(InventoryItemData weapon, out string error)
        {
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int loadedBefore = weapon.LoadedAmmunition;
            if (loadedBefore <= 0)
            {
                error = "The active weapon has no loaded ammunition.";
                return false;
            }

            if (!weapon.TryChangeLoadedAmmunition(
                    Equipment,
                    loadedBefore,
                    loadedBefore - 1,
                    out error))
            {
                return false;
            }

            Equipment.NotifyOwnedItemStateChanged(weapon);
            error = null;
            return true;
        }

        public bool TryReloadWeapon(
            InventoryItemData weapon,
            out int loadedRoundCount,
            out string error)
        {
            loadedRoundCount = 0;
            if (!TryValidateEquippedWeapon(weapon, out error))
            {
                return false;
            }

            int loadedBefore = weapon.LoadedAmmunition;
            int missingRounds = weapon.MagazineCapacity - loadedBefore;
            if (missingRounds <= 0)
            {
                error = "The active weapon magazine is already full.";
                return false;
            }

            if (!TryBuildAmmunitionPlan(
                    weapon.Definition.AmmunitionDefinitionId,
                    missingRounds,
                    out List<AmmunitionMutation> plan,
                    out error))
            {
                return false;
            }

            foreach (AmmunitionMutation mutation in plan)
            {
                loadedRoundCount += mutation.ConsumedQuantity;
            }

            if (loadedRoundCount <= 0)
            {
                error = "The Player inventory contains no compatible ammunition.";
                return false;
            }

            int appliedCount = 0;
            try
            {
                for (; appliedCount < plan.Count; appliedCount++)
                {
                    AmmunitionMutation mutation = plan[appliedCount];
                    if (mutation.RemainingQuantity > 0)
                    {
                        if (!mutation.Item.TryChangeQuantity(
                                mutation.Owner,
                                mutation.OriginalQuantity,
                                mutation.RemainingQuantity,
                                out string quantityError))
                        {
                            throw new InvalidOperationException(quantityError);
                        }
                    }
                    else
                    {
                        mutation.Owner.InsertInventoryItem(mutation.SlotIndex, null);
                    }
                }

                if (!weapon.TryChangeLoadedAmmunition(
                        Equipment,
                        loadedBefore,
                        loadedBefore + loadedRoundCount,
                        out string weaponError))
                {
                    throw new InvalidOperationException(weaponError);
                }
            }
            catch (Exception exception)
            {
                string rollbackError = RollBackAmmunitionPlan(plan, appliedCount);
                loadedRoundCount = 0;
                error = "Could not complete the ammunition reload transaction: " +
                        exception.Message + rollbackError;
                return false;
            }

            Equipment.NotifyOwnedItemStateChanged(weapon);
            error = null;
            return true;
        }

        /// <summary>
        /// Atomically removes every root item carried in the Player grid and equipment.
        /// Nested container contents leave with their root container. The Player state and
        /// both container instances stay alive so scene-persistent observers keep the same
        /// authoritative object graph.
        /// </summary>
        public bool TryDiscardAllCarriedItems(out string error)
        {
            if (Inventory.CellData == null)
            {
                error = "Player inventory cell data is missing.";
                return false;
            }

            var inventoryRoots = new List<KeyValuePair<int, InventoryItemData>>();
            var seen = new HashSet<InventoryItemData>(
                InventoryReferenceComparer<InventoryItemData>.Instance);
            for (int index = 0; index < Inventory.CellData.Length; index++)
            {
                IVariableInventoryCellData item = Inventory.CellData[index];
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Player inventory slot {index} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is referenced by multiple Player inventory slots.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, Inventory))
                {
                    error = $"Player inventory slot {index} has inconsistent item ownership.";
                    return false;
                }

                inventoryRoots.Add(
                    new KeyValuePair<int, InventoryItemData>(index, inventoryItem));
            }

            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                IVariableInventoryCellData item = Equipment.GetItem(slot);
                if (item == null)
                {
                    continue;
                }

                if (!(item is InventoryItemData inventoryItem))
                {
                    error = $"Equipment slot {slot} contains an unsupported runtime item type.";
                    return false;
                }

                if (!seen.Add(inventoryItem))
                {
                    error = "The same item is owned by both the Player grid and equipment.";
                    return false;
                }

                if (!ReferenceEquals(inventoryItem.InventoryOwner, Equipment))
                {
                    error = $"Equipment slot {slot} has inconsistent item ownership.";
                    return false;
                }
            }

            int removedInventoryRoots = 0;
            try
            {
                for (; removedInventoryRoots < inventoryRoots.Count; removedInventoryRoots++)
                {
                    Inventory.InsertInventoryItem(inventoryRoots[removedInventoryRoots].Key, null);
                }
            }
            catch (Exception exception)
            {
                string rollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not clear the Player inventory: " + exception.Message + rollbackError;
                return false;
            }

            if (!Equipment.TryClearAll(out string equipmentError))
            {
                string rollbackError = RestoreInventoryRoots(
                    inventoryRoots,
                    removedInventoryRoots);
                error = "Could not clear Player equipment: " + equipmentError + rollbackError;
                return false;
            }

            error = null;
            return true;
        }

        private string RestoreInventoryRoots(
            IReadOnlyList<KeyValuePair<int, InventoryItemData>> roots,
            int removedCount)
        {
            var failures = new List<string>();
            for (int index = 0; index < removedCount; index++)
            {
                KeyValuePair<int, InventoryItemData> placement = roots[index];
                try
                {
                    Inventory.InsertInventoryItem(placement.Key, placement.Value);
                }
                catch (Exception exception)
                {
                    failures.Add($"slot {placement.Key}: {exception.Message}");
                }
            }

            return failures.Count == 0
                ? string.Empty
                : $" Inventory rollback also failed ({string.Join("; ", failures)}).";
        }

        private static bool ContainsNestedInventory(
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
                    if (cell is IStandardCaseCellData container &&
                        container.CaseData != null &&
                        (ReferenceEquals(container.CaseData, target) ||
                         ContainsNestedInventory(container.CaseData, target, visited)))
                    {
                        return true;
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
                         ContainsNestedInventory(container.CaseData, target, visited)))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        private bool TryValidateEquippedWeapon(
            InventoryItemData weapon,
            out string error)
        {
            if (weapon?.Definition == null || !weapon.Definition.IsWeapon)
            {
                error = "The requested item is not a weapon.";
                return false;
            }

            if (!ReferenceEquals(weapon.InventoryOwner, Equipment))
            {
                error = "The requested weapon is not owned by the Player equipment loadout.";
                return false;
            }

            for (int weaponNumber = 1;
                 weaponNumber <= EquipmentSlotCatalog.WeaponSlotCount;
                 weaponNumber++)
            {
                if (ReferenceEquals(
                        Equipment.GetItem(EquipmentSlotCatalog.GetWeaponSlot(weaponNumber)),
                        weapon))
                {
                    error = null;
                    return true;
                }
            }

            error = "The requested weapon is not present in a Player weapon slot.";
            return false;
        }

        private bool TryBuildAmmunitionPlan(
            int ammunitionDefinitionId,
            int requestedQuantity,
            out List<AmmunitionMutation> plan,
            out string error)
        {
            plan = new List<AmmunitionMutation>();
            int remaining = requestedQuantity;
            var visitedGrids = new HashSet<StandardStashViewData>(
                InventoryReferenceComparer<StandardStashViewData>.Instance);
            if (!TryAppendAmmunitionFromGrid(
                    Inventory,
                    ammunitionDefinitionId,
                    plan,
                    visitedGrids,
                    ref remaining,
                    out error))
            {
                return false;
            }

            if (remaining > 0)
            {
                foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
                {
                    if (!(Equipment.GetItem(slot) is InventoryContainerItemData container))
                    {
                        continue;
                    }

                    if (!TryAppendAmmunitionFromGrid(
                            container.CaseData,
                            ammunitionDefinitionId,
                            plan,
                            visitedGrids,
                            ref remaining,
                            out error))
                    {
                        return false;
                    }

                    if (remaining <= 0)
                    {
                        break;
                    }
                }
            }

            error = null;
            return true;
        }

        private static bool TryCountAmmunitionFromGrid(
            StandardStashViewData grid,
            int ammunitionDefinitionId,
            HashSet<StandardStashViewData> visitedGrids,
            ref long total,
            out string error)
        {
            if (grid?.CellData == null || !visitedGrids.Add(grid))
            {
                error = grid == null || grid.CellData == null
                    ? "A Player-owned inventory grid is missing."
                    : "The Player inventory contains a shared or cyclic container grid.";
                return false;
            }

            for (int slotIndex = 0; slotIndex < grid.CellData.Length; slotIndex++)
            {
                if (!(grid.CellData[slotIndex] is InventoryItemData item))
                {
                    if (grid.CellData[slotIndex] != null)
                    {
                        error = $"Player inventory slot {slotIndex} contains an unsupported runtime item type.";
                        return false;
                    }

                    continue;
                }

                if (!ReferenceEquals(item.InventoryOwner, grid))
                {
                    error = $"Player inventory item ID {item.Id} has inconsistent ownership.";
                    return false;
                }

                if (item.Id == ammunitionDefinitionId && item.Definition.IsAmmunition)
                {
                    total = Math.Min(int.MaxValue, total + item.Quantity);
                }

                if (item is InventoryContainerItemData container &&
                    !TryCountAmmunitionFromGrid(
                        container.CaseData,
                        ammunitionDefinitionId,
                        visitedGrids,
                        ref total,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryAppendAmmunitionFromGrid(
            StandardStashViewData grid,
            int ammunitionDefinitionId,
            List<AmmunitionMutation> plan,
            HashSet<StandardStashViewData> visitedGrids,
            ref int remaining,
            out string error)
        {
            if (grid?.CellData == null || !visitedGrids.Add(grid))
            {
                error = grid == null || grid.CellData == null
                    ? "A Player-owned inventory grid is missing."
                    : "The Player inventory contains a shared or cyclic container grid.";
                return false;
            }

            for (int slotIndex = 0;
                 slotIndex < grid.CellData.Length && remaining > 0;
                 slotIndex++)
            {
                if (!(grid.CellData[slotIndex] is InventoryItemData item))
                {
                    if (grid.CellData[slotIndex] != null)
                    {
                        error = $"Player inventory slot {slotIndex} contains an unsupported runtime item type.";
                        return false;
                    }

                    continue;
                }

                if (!ReferenceEquals(item.InventoryOwner, grid))
                {
                    error = $"Player inventory item ID {item.Id} has inconsistent ownership.";
                    return false;
                }

                if (item.Id == ammunitionDefinitionId && item.Definition.IsAmmunition)
                {
                    int consumed = Math.Min(item.Quantity, remaining);
                    plan.Add(new AmmunitionMutation
                    {
                        Owner = grid,
                        SlotIndex = slotIndex,
                        Item = item,
                        OriginalQuantity = item.Quantity,
                        ConsumedQuantity = consumed
                    });
                    remaining -= consumed;
                }

                if (remaining > 0 && item is InventoryContainerItemData container &&
                    !TryAppendAmmunitionFromGrid(
                        container.CaseData,
                        ammunitionDefinitionId,
                        plan,
                        visitedGrids,
                        ref remaining,
                        out error))
                {
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static string RollBackAmmunitionPlan(
            IReadOnlyList<AmmunitionMutation> plan,
            int appliedCount)
        {
            var failures = new List<string>();
            int lastAppliedIndex = Math.Min(appliedCount, plan.Count) - 1;
            for (int index = lastAppliedIndex; index >= 0; index--)
            {
                AmmunitionMutation mutation = plan[index];
                try
                {
                    if (mutation.RemainingQuantity > 0)
                    {
                        if (!mutation.Item.TryChangeQuantity(
                                mutation.Owner,
                                mutation.RemainingQuantity,
                                mutation.OriginalQuantity,
                                out string quantityError))
                        {
                            failures.Add($"slot {mutation.SlotIndex}: {quantityError}");
                        }
                    }
                    else
                    {
                        mutation.Owner.InsertInventoryItem(
                            mutation.SlotIndex,
                            mutation.Item);
                    }
                }
                catch (Exception exception)
                {
                    failures.Add($"slot {mutation.SlotIndex}: {exception.Message}");
                }
            }

            return failures.Count == 0
                ? string.Empty
                : $" Ammunition rollback also failed ({string.Join("; ", failures)}).";
        }
    }

    internal sealed class InventoryReferenceComparer<T> : IEqualityComparer<T>
        where T : class
    {
        public static readonly InventoryReferenceComparer<T> Instance =
            new InventoryReferenceComparer<T>();

        public bool Equals(T x, T y) => ReferenceEquals(x, y);
        public int GetHashCode(T value) => RuntimeHelpers.GetHashCode(value);
    }
}
