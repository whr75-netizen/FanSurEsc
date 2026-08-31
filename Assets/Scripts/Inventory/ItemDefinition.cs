using FantasySurvival.Combat;
using FantasySurvival.Trading;
using UnityEngine;

namespace FantasySurvival.Inventory
{
    public enum ItemDefinitionKind
    {
        Standard,
        Container,
        Medicine,
        Ammunition,
        Food
    }

    public sealed class ItemDefinition : ScriptableObject
    {
        [SerializeField, Min(1)] private int id = 1;
        [SerializeField] private string displayName;
        [SerializeField, TextArea] private string description;

        [Header("Inventory Presentation")]
        [SerializeField, Min(1)] private int width = 1;
        [SerializeField, Min(1)] private int height = 1;
        [SerializeField] private Texture2D icon;
        [SerializeField, Min(1)] private int maxStackSize = 1;

        [Header("Equipment")]
        [SerializeField] private EquipmentSlotType equipmentSlot;

        [Header("Trading Prototype")]
        [SerializeField] private bool isTradable;
        [SerializeField] private TradeCurrency tradeCurrency = TradeCurrency.Silver;
        [SerializeField, Min(0)] private int tradePrice;

        [Header("Weapon Prototype")]
        [SerializeField] private WeaponFireMode weaponFireMode;
        [SerializeField, Min(1f)] private float roundsPerMinute = 300f;
        [SerializeField, Min(1)] private int ammunitionDefinitionId = 8;
        [SerializeField, Min(1)] private int magazineCapacity = 3;
        [SerializeField, Min(0.01f)] private float reloadDurationSeconds = 2.5f;
        [SerializeField, Min(0f)] private float weaponDamage = 35f;
        [SerializeField, Min(0.1f)] private float weaponRange = 30f;
        [SerializeField, Min(0f)] private float weaponNoiseRadius = 18f;

        [Header("Medicine Prototype")]
        [SerializeField, Min(0.01f)] private float medicineUseDurationSeconds = 2.5f;
        [SerializeField, Min(0.01f)] private float medicineHealthRestored = 35f;

        [Header("Item Type")]
        [SerializeField] private ItemDefinitionKind kind;
        [Header("Container")]
        [SerializeField, Min(1)] private int containerWidth = 1;
        [SerializeField, Min(1)] private int containerHeight = 1;

        public int Id => id;
        public string DisplayName => displayName;
        public string Description => description;
        public int Width => width;
        public int Height => height;
        public Texture2D Icon => icon;
        public int MaxStackSize => maxStackSize;
        public EquipmentSlotType EquipmentSlot => equipmentSlot;
        public bool IsEquippable => equipmentSlot != EquipmentSlotType.None;
        public bool IsWeapon => equipmentSlot == EquipmentSlotType.Weapon;
        public bool IsTradable => isTradable && !IsContainer && tradePrice > 0 &&
                                  PlayerWallet.IsValidCurrency(tradeCurrency);
        public TradeCurrency TradeCurrency => tradeCurrency;
        public int TradePrice => tradePrice;
        public WeaponFireMode WeaponFireMode => weaponFireMode;
        public float RoundsPerMinute => roundsPerMinute;
        public int AmmunitionDefinitionId => ammunitionDefinitionId;
        public int MagazineCapacity => magazineCapacity;
        public float ReloadDurationSeconds => reloadDurationSeconds;
        public float WeaponDamage => weaponDamage;
        public float WeaponRange => weaponRange;
        public float WeaponNoiseRadius => weaponNoiseRadius;
        public float MedicineUseDurationSeconds => medicineUseDurationSeconds;
        public float MedicineHealthRestored => medicineHealthRestored;
        public ItemDefinitionKind Kind => kind;
        public bool IsContainer => kind == ItemDefinitionKind.Container;
        public bool IsMedicine => kind == ItemDefinitionKind.Medicine;
        public bool IsAmmunition => kind == ItemDefinitionKind.Ammunition;
        public bool IsFood => kind == ItemDefinitionKind.Food;
        public int ContainerWidth => containerWidth;
        public int ContainerHeight => containerHeight;

        public bool CanEquipIn(EquipmentSlotId slot)
        {
            return slot != EquipmentSlotId.None &&
                   equipmentSlot == EquipmentSlotCatalog.GetSlotType(slot);
        }

        public bool TryValidateInventoryShape(out string error)
        {
            if (id <= 0)
            {
                error = $"Item definition '{name}' has an invalid ID.";
                return false;
            }

            if (!InventoryGridConstraints.TryValidateDimensions(width, height, out error))
            {
                error = $"Item definition ID {id} has an invalid inventory footprint: {error}";
                return false;
            }

            if (maxStackSize <= 0)
            {
                error = $"Item definition ID {id} has an invalid maximum stack size.";
                return false;
            }

            if ((IsContainer || IsEquippable) && maxStackSize != 1)
            {
                error = $"Container or equipment definition ID {id} must have a maximum stack size of 1.";
                return false;
            }

            if (IsContainer && IsWeapon)
            {
                error = $"Item definition ID {id} cannot be both a weapon and a container.";
                return false;
            }

            if (IsWeapon &&
                (ammunitionDefinitionId <= 0 || magazineCapacity <= 0 ||
                 float.IsNaN(reloadDurationSeconds) ||
                 float.IsInfinity(reloadDurationSeconds) || reloadDurationSeconds <= 0f ||
                 float.IsNaN(roundsPerMinute) ||
                 float.IsInfinity(roundsPerMinute) || roundsPerMinute <= 0f))
            {
                error = $"Weapon definition ID {id} has invalid ammunition, magazine, reload, or fire-rate settings.";
                return false;
            }

            if (IsMedicine &&
                (float.IsNaN(medicineUseDurationSeconds) ||
                 float.IsInfinity(medicineUseDurationSeconds) ||
                 medicineUseDurationSeconds <= 0f ||
                 float.IsNaN(medicineHealthRestored) ||
                 float.IsInfinity(medicineHealthRestored) ||
                 medicineHealthRestored <= 0f))
            {
                error = $"Medicine definition ID {id} has an invalid use duration or healing amount.";
                return false;
            }

            if (IsContainer && !InventoryGridConstraints.TryValidateDimensions(
                    containerWidth,
                    containerHeight,
                    out error))
            {
                error = $"Item definition ID {id} has invalid container dimensions: {error}";
                return false;
            }

            error = null;
            return true;
        }

        private void OnValidate()
        {
            id = Mathf.Max(1, id);
            width = Mathf.Max(1, width);
            height = Mathf.Max(1, height);
            maxStackSize = IsContainer || IsEquippable ? 1 : Mathf.Max(1, maxStackSize);
            containerWidth = Mathf.Max(1, containerWidth);
            containerHeight = Mathf.Max(1, containerHeight);
            roundsPerMinute = Mathf.Max(1f, roundsPerMinute);
            ammunitionDefinitionId = Mathf.Max(1, ammunitionDefinitionId);
            magazineCapacity = Mathf.Max(1, magazineCapacity);
            reloadDurationSeconds = Mathf.Max(0.01f, reloadDurationSeconds);
            weaponDamage = Mathf.Max(0f, weaponDamage);
            weaponRange = Mathf.Max(0.1f, weaponRange);
            weaponNoiseRadius = Mathf.Max(0f, weaponNoiseRadius);
            medicineUseDurationSeconds = Mathf.Max(0.01f, medicineUseDurationSeconds);
            medicineHealthRestored = Mathf.Max(0.01f, medicineHealthRestored);
        }
    }
}
