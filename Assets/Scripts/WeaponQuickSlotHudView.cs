using FantasySurvival.Inventory;
using UnityEngine;
using UnityEngine.UI;

[DisallowMultipleComponent]
public sealed class WeaponQuickSlotHudView : MonoBehaviour
{
    [SerializeField] private PlayerWeaponController weaponController;
    [SerializeField] private Image[] slotBackgrounds;
    [SerializeField] private RawImage[] weaponIcons;
    [SerializeField] private Text[] weaponNames;
    [SerializeField] private GameObject activeAmmoRoot;
    [SerializeField] private Text activeAmmoText;
    [SerializeField] private Color normalColor = new Color(0.08f, 0.1f, 0.13f, 0.9f);
    [SerializeField] private Color selectedColor = new Color(0.25f, 0.68f, 0.95f, 0.95f);

    private void OnEnable()
    {
        if (weaponController == null)
        {
            Debug.LogError("WeaponQuickSlotHudView is missing PlayerWeaponController.", this);
            return;
        }

        weaponController.WeaponStateChanged += Refresh;
        Refresh();
    }

    private void OnDisable()
    {
        if (weaponController != null)
        {
            weaponController.WeaponStateChanged -= Refresh;
        }
    }

    private void Refresh()
    {
        InventoryItemData activeWeapon = weaponController.ActiveWeapon;
        bool showActiveAmmunition = activeWeapon?.Definition != null &&
                                    activeWeapon.Definition.IsWeapon;
        if (activeAmmoRoot != null)
        {
            activeAmmoRoot.SetActive(showActiveAmmunition);
        }

        if (activeAmmoText != null)
        {
            int reserveAmmunition = 0;
            if (showActiveAmmunition)
            {
                weaponController.TryGetReserveAmmunitionCount(
                    activeWeapon,
                    out reserveAmmunition);
            }

            activeAmmoText.text = showActiveAmmunition
                ? $"탄창  {activeWeapon.LoadedAmmunition} / {activeWeapon.MagazineCapacity}   " +
                  $"예비  {reserveAmmunition}"
                : string.Empty;
        }

        for (int index = 0; index < EquipmentSlotCatalog.WeaponSlotCount; index++)
        {
            int weaponNumber = index + 1;
            InventoryItemData item = weaponController.GetWeapon(weaponNumber);

            if (slotBackgrounds != null && index < slotBackgrounds.Length &&
                slotBackgrounds[index] != null)
            {
                slotBackgrounds[index].color = weaponController.ActiveWeaponNumber == weaponNumber
                    ? selectedColor
                    : normalColor;
            }

            if (weaponIcons != null && index < weaponIcons.Length && weaponIcons[index] != null)
            {
                Texture icon = item?.Definition.Icon;
                weaponIcons[index].texture = icon;
                weaponIcons[index].gameObject.SetActive(icon != null);
            }

            if (weaponNames != null && index < weaponNames.Length && weaponNames[index] != null)
            {
                weaponNames[index].text = item != null
                    ? $"{item.Definition.DisplayName}  {item.LoadedAmmunition}/{item.MagazineCapacity}"
                    : "EMPTY";
            }
        }
    }
}
