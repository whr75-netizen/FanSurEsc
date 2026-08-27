using System;
using FantasySurvival.Actions;
using FantasySurvival.Inventory;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(PlayerActionController))]
public sealed class PlayerWeaponController : MonoBehaviour
{
    public const string UpperBodyLayerName = "Weapon Upper Body";

    [SerializeField] private InventoryUIManager inventoryManager;
    [SerializeField] private Animator characterAnimator;
    [SerializeField] private string upperBodyLayerName = UpperBodyLayerName;
    [SerializeField, Range(1, EquipmentSlotCatalog.WeaponSlotCount)]
    private int activeWeaponNumber = 1;
    [SerializeField] private KeyCode weapon1Key = KeyCode.Alpha1;
    [SerializeField] private KeyCode weapon2Key = KeyCode.Alpha2;
    [SerializeField] private KeyCode weapon3Key = KeyCode.Alpha3;

    private EquipmentLoadoutData observedLoadout;
    private int upperBodyLayerIndex = -1;
    private PlayerActionController actionController;

    public event Action WeaponStateChanged;

    public int ActiveWeaponNumber => activeWeaponNumber;
    public InventoryItemData ActiveWeapon => GetWeapon(activeWeaponNumber);
    public bool IsArmed => ActiveWeapon != null;

    private void Awake()
    {
        actionController = GetComponent<PlayerActionController>();
        activeWeaponNumber = Mathf.Clamp(
            activeWeaponNumber,
            1,
            EquipmentSlotCatalog.WeaponSlotCount);
        CacheAnimationLayer();
    }

    private void OnEnable()
    {
        if (inventoryManager == null)
        {
            Debug.LogError("PlayerWeaponController is missing InventoryUIManager.", this);
            return;
        }

        inventoryManager.PlayerStateChanged += HandlePlayerStateChanged;
        Bind(inventoryManager.PlayerState);
    }

    private void OnDisable()
    {
        if (inventoryManager != null)
        {
            inventoryManager.PlayerStateChanged -= HandlePlayerStateChanged;
        }

        Bind(null, false);
        SetWeaponPose(false);
    }

    private void Update()
    {
        if (inventoryManager != null && inventoryManager.InputBlocked)
        {
            return;
        }

        if (Input.GetKeyDown(weapon1Key))
        {
            ProcessWeaponSelectionInput(1);
        }
        else if (Input.GetKeyDown(weapon2Key))
        {
            ProcessWeaponSelectionInput(2);
        }
        else if (Input.GetKeyDown(weapon3Key))
        {
            ProcessWeaponSelectionInput(3);
        }
    }

    public bool ProcessWeaponSelectionInput(int oneBasedNumber)
    {
        if (EquipmentSlotCatalog.GetWeaponSlot(oneBasedNumber) == EquipmentSlotId.None)
        {
            return false;
        }

        actionController.CancelActive(PlayerActionCancelReason.EquipmentSwitchInput);
        return SelectWeapon(oneBasedNumber);
    }

    public bool SelectWeapon(int oneBasedNumber)
    {
        if (EquipmentSlotCatalog.GetWeaponSlot(oneBasedNumber) == EquipmentSlotId.None)
        {
            return false;
        }

        if (activeWeaponNumber == oneBasedNumber)
        {
            RefreshDerivedState();
            return true;
        }

        activeWeaponNumber = oneBasedNumber;
        RefreshDerivedState();
        return true;
    }

    public InventoryItemData GetWeapon(int oneBasedNumber)
    {
        EquipmentSlotId slot = EquipmentSlotCatalog.GetWeaponSlot(oneBasedNumber);
        return slot == EquipmentSlotId.None
            ? null
            : observedLoadout?.GetItem(slot) as InventoryItemData;
    }

    private void HandlePlayerStateChanged(PlayerInventoryState state)
    {
        Bind(state);
    }

    private void Bind(PlayerInventoryState state, bool notify = true)
    {
        if (observedLoadout != null)
        {
            observedLoadout.Changed -= HandleLoadoutChanged;
        }

        observedLoadout = state?.Equipment;
        if (observedLoadout != null)
        {
            observedLoadout.Changed += HandleLoadoutChanged;
        }

        if (notify)
        {
            RefreshDerivedState();
        }
    }

    private void HandleLoadoutChanged()
    {
        RefreshDerivedState();
    }

    private void RefreshDerivedState()
    {
        SetWeaponPose(IsArmed);
        WeaponStateChanged?.Invoke();
    }

    private void CacheAnimationLayer()
    {
        upperBodyLayerIndex = characterAnimator != null
            ? characterAnimator.GetLayerIndex(upperBodyLayerName)
            : -1;
    }

    private void SetWeaponPose(bool armed)
    {
        if (characterAnimator == null || !characterAnimator.isActiveAndEnabled)
        {
            return;
        }

        if (upperBodyLayerIndex < 0)
        {
            CacheAnimationLayer();
        }

        if (upperBodyLayerIndex >= 0)
        {
            characterAnimator.SetLayerWeight(upperBodyLayerIndex, armed ? 1f : 0f);
        }
    }

    private void OnValidate()
    {
        activeWeaponNumber = Mathf.Clamp(
            activeWeaponNumber,
            1,
            EquipmentSlotCatalog.WeaponSlotCount);
    }
}
