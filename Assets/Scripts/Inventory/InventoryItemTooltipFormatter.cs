using System.Text;
using FantasySurvival.Combat;

namespace FantasySurvival.Inventory
{
    public readonly struct InventoryItemTooltipContent
    {
        public string Name { get; }
        public string Description { get; }
        public string Stats { get; }

        public InventoryItemTooltipContent(string name, string description, string stats)
        {
            Name = name;
            Description = description;
            Stats = stats;
        }
    }

    /// <summary>
    /// Builds presentation text from the immutable ItemDefinition. It does not own,
    /// copy, or persist item state.
    /// </summary>
    public static class InventoryItemTooltipFormatter
    {
        public static InventoryItemTooltipContent Create(ItemDefinition definition)
        {
            if (definition == null)
            {
                return new InventoryItemTooltipContent(
                    "알 수 없는 아이템",
                    "설명 정보가 없습니다.",
                    string.Empty);
            }

            string itemName = string.IsNullOrWhiteSpace(definition.DisplayName)
                ? definition.name
                : definition.DisplayName;
            string description = string.IsNullOrWhiteSpace(definition.Description)
                ? "설명 정보가 없습니다."
                : definition.Description.Trim();

            var stats = new StringBuilder(160);
            AppendStat(stats, "분류", GetCategoryName(definition));
            AppendStat(stats, "인벤토리 크기", $"{definition.Width} × {definition.Height}");

            if (definition.IsEquippable)
            {
                AppendStat(stats, "장착 부위", GetEquipmentTypeName(definition.EquipmentSlot));
            }

            if (definition.IsWeapon)
            {
                AppendStat(
                    stats,
                    "발사 방식",
                    definition.WeaponFireMode == WeaponFireMode.Automatic ? "자동" : "단발");
                AppendStat(stats, "피해", FormatNumber(definition.WeaponDamage));
                AppendStat(stats, "연사력", $"{FormatNumber(definition.RoundsPerMinute)} RPM");
                AppendStat(stats, "사거리", FormatNumber(definition.WeaponRange));
                AppendStat(stats, "소음 반경", FormatNumber(definition.WeaponNoiseRadius));
            }

            if (definition.IsContainer)
            {
                int cellCount = definition.ContainerWidth * definition.ContainerHeight;
                AppendStat(
                    stats,
                    "내부 공간",
                    $"{definition.ContainerWidth} × {definition.ContainerHeight} ({cellCount}칸)");
            }

            return new InventoryItemTooltipContent(itemName, description, stats.ToString());
        }

        private static void AppendStat(StringBuilder builder, string label, string value)
        {
            if (builder.Length > 0)
            {
                builder.AppendLine();
            }

            builder.Append(label).Append(": ").Append(value);
        }

        private static string GetCategoryName(ItemDefinition definition)
        {
            if (definition.IsWeapon)
            {
                return "무기";
            }

            if (definition.IsContainer)
            {
                return "컨테이너";
            }

            return definition.IsEquippable ? "장비" : "일반";
        }

        private static string GetEquipmentTypeName(EquipmentSlotType type)
        {
            if (type == EquipmentSlotType.Weapon)
            {
                return "무기";
            }

            EquipmentSlotId primarySlot = EquipmentSlotCatalog.GetPrimarySlot(type);
            return primarySlot != EquipmentSlotId.None
                ? EquipmentSlotCatalog.GetDisplayName(primarySlot)
                : "장착 불가";
        }

        private static string FormatNumber(float value)
        {
            return value.ToString("0.##");
        }
    }
}
