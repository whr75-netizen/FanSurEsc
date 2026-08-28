using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace FantasySurvival.Controls
{
    public enum GameInputActionId
    {
        MoveUp,
        MoveDown,
        MoveLeft,
        MoveRight,
        Run,
        Interact,
        Inventory,
        Information,
        Weapon1,
        Weapon2,
        Weapon3,
        Attack,
        RotateItem,
        CameraZoom,
        QuickTransferModifier,
        AlternateItemModifier,
        SingleItemModifier
    }

    public enum GameInputBindingSlot
    {
        Primary,
        Secondary
    }

    public readonly struct GameInputBindingDefinition
    {
        public GameInputBindingDefinition(
            GameInputActionId actionId,
            string category,
            string displayName)
        {
            ActionId = actionId;
            Category = category;
            DisplayName = displayName;
        }

        public GameInputActionId ActionId { get; }
        public string Category { get; }
        public string DisplayName { get; }
    }

    /// <summary>
    /// Resolves the project's immutable input catalog against the project-wide
    /// Input Actions asset. Runtime binding overrides live on that asset and are
    /// persisted only by GameUserSettings.
    /// </summary>
    public static class GameInputBindings
    {
        public const string GameplayMapName = "Gameplay";
        public const string PrimaryBindingName = "Primary";
        public const string SecondaryBindingName = "Secondary";

        private static readonly GameInputBindingDefinition[] BindingDefinitions =
        {
            new GameInputBindingDefinition(GameInputActionId.MoveUp, "이동", "위로 이동"),
            new GameInputBindingDefinition(GameInputActionId.MoveDown, "이동", "아래로 이동"),
            new GameInputBindingDefinition(GameInputActionId.MoveLeft, "이동", "왼쪽 이동"),
            new GameInputBindingDefinition(GameInputActionId.MoveRight, "이동", "오른쪽 이동"),
            new GameInputBindingDefinition(GameInputActionId.Run, "이동", "달리기"),
            new GameInputBindingDefinition(GameInputActionId.Interact, "게임플레이", "상호작용"),
            new GameInputBindingDefinition(GameInputActionId.Attack, "전투", "공격"),
            new GameInputBindingDefinition(GameInputActionId.Weapon1, "전투", "무기 1"),
            new GameInputBindingDefinition(GameInputActionId.Weapon2, "전투", "무기 2"),
            new GameInputBindingDefinition(GameInputActionId.Weapon3, "전투", "무기 3"),
            new GameInputBindingDefinition(GameInputActionId.Inventory, "화면", "인벤토리"),
            new GameInputBindingDefinition(GameInputActionId.Information, "화면", "정보창"),
            new GameInputBindingDefinition(
                GameInputActionId.RotateItem,
                "게임플레이",
                "재장전 / 든 아이템 회전"),
            new GameInputBindingDefinition(
                GameInputActionId.QuickTransferModifier,
                "인벤토리",
                "빠른 이동 + 클릭"),
            new GameInputBindingDefinition(
                GameInputActionId.AlternateItemModifier,
                "인벤토리",
                "절반 분할·빠른 장착 + 클릭"),
            new GameInputBindingDefinition(
                GameInputActionId.SingleItemModifier,
                "인벤토리",
                "한 개 집기·분배 + 클릭")
        };

        public static IReadOnlyList<GameInputBindingDefinition> Definitions =>
            BindingDefinitions;

        public static InputActionMap GameplayMap =>
            InputSystem.actions != null
                ? InputSystem.actions.FindActionMap(GameplayMapName, false)
                : null;

        public static Vector2 ReadMovement()
        {
            float horizontal =
                (IsPressed(GameInputActionId.MoveRight) ? 1f : 0f) -
                (IsPressed(GameInputActionId.MoveLeft) ? 1f : 0f);
            float vertical =
                (IsPressed(GameInputActionId.MoveUp) ? 1f : 0f) -
                (IsPressed(GameInputActionId.MoveDown) ? 1f : 0f);
            Vector2 movement = new Vector2(horizontal, vertical);
            return movement.sqrMagnitude > 1f ? movement.normalized : movement;
        }

        public static bool WasPressedThisFrame(GameInputActionId actionId)
        {
            InputAction action = GetAction(actionId);
            return action != null && action.enabled && action.WasPressedThisFrame();
        }

        public static bool IsPressed(GameInputActionId actionId)
        {
            InputAction action = GetAction(actionId);
            return action != null && action.enabled && action.IsPressed();
        }

        public static float ReadCameraZoomDelta()
        {
            InputAction action = GetAction(GameInputActionId.CameraZoom);
            return action != null && action.enabled
                ? action.ReadValue<Vector2>().y
                : 0f;
        }

        public static InputAction GetAction(GameInputActionId actionId)
        {
            InputActionMap map = GameplayMap;
            return map != null ? map.FindAction(actionId.ToString(), false) : null;
        }

        public static GameInputBindingDefinition GetDefinition(GameInputActionId actionId)
        {
            for (int index = 0; index < BindingDefinitions.Length; index++)
            {
                if (BindingDefinitions[index].ActionId == actionId)
                {
                    return BindingDefinitions[index];
                }
            }

            return new GameInputBindingDefinition(actionId, string.Empty, actionId.ToString());
        }

        public static bool TryResolveBinding(
            GameInputActionId actionId,
            GameInputBindingSlot slot,
            out InputAction action,
            out int bindingIndex)
        {
            action = GetAction(actionId);
            bindingIndex = -1;
            if (action == null)
            {
                return false;
            }

            string bindingName = slot == GameInputBindingSlot.Primary
                ? PrimaryBindingName
                : SecondaryBindingName;
            for (int index = 0; index < action.bindings.Count; index++)
            {
                if (string.Equals(
                        action.bindings[index].name,
                        bindingName,
                        StringComparison.OrdinalIgnoreCase))
                {
                    bindingIndex = index;
                    return true;
                }
            }

            return false;
        }

        public static string GetEffectivePath(
            GameInputActionId actionId,
            GameInputBindingSlot slot)
        {
            return TryResolveBinding(actionId, slot, out InputAction action, out int index)
                ? action.bindings[index].effectivePath
                : string.Empty;
        }

        public static bool HasBindingOverride(
            GameInputActionId actionId,
            GameInputBindingSlot slot)
        {
            return TryResolveBinding(actionId, slot, out InputAction action, out int index) &&
                   action.bindings[index].hasOverrides;
        }

        public static string GetBindingDisplayName(
            GameInputActionId actionId,
            GameInputBindingSlot slot)
        {
            return FormatControlPath(GetEffectivePath(actionId, slot));
        }

        public static string FormatControlPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
            {
                return "없음";
            }

            string normalized = path.Trim().ToLowerInvariant();
            switch (normalized)
            {
                case "<keyboard>/leftshift": return "왼쪽 Shift";
                case "<keyboard>/rightshift": return "오른쪽 Shift";
                case "<keyboard>/leftalt": return "왼쪽 Alt";
                case "<keyboard>/rightalt": return "오른쪽 Alt";
                case "<keyboard>/leftctrl": return "왼쪽 Ctrl";
                case "<keyboard>/rightctrl": return "오른쪽 Ctrl";
                case "<keyboard>/uparrow": return "위 방향키";
                case "<keyboard>/downarrow": return "아래 방향키";
                case "<keyboard>/leftarrow": return "왼쪽 방향키";
                case "<keyboard>/rightarrow": return "오른쪽 방향키";
                case "<keyboard>/space": return "Space";
                case "<keyboard>/enter": return "Enter";
                case "<keyboard>/tab": return "Tab";
                case "<keyboard>/backspace": return "Backspace";
                case "<mouse>/leftbutton": return "마우스 왼쪽";
                case "<mouse>/rightbutton": return "마우스 오른쪽";
                case "<mouse>/middlebutton": return "마우스 가운데";
            }

            try
            {
                string readable = InputControlPath.ToHumanReadableString(
                    path,
                    InputControlPath.HumanReadableStringOptions.OmitDevice);
                return string.IsNullOrWhiteSpace(readable) ? path : readable;
            }
            catch (Exception)
            {
                return path;
            }
        }

        public static bool IsSupportedRebindPath(string path)
        {
            return TryGetCanonicalRebindPath(path, out _);
        }

        public static bool TryGetCanonicalRebindPath(
            string path,
            out string canonicalPath)
        {
            canonicalPath = null;
            if (string.IsNullOrWhiteSpace(path))
            {
                return false;
            }

            try
            {
                InputControl control = InputSystem.FindControl(path);
                if (!(control is ButtonControl) || control.synthetic ||
                    !(control.device is Keyboard) && !(control.device is Mouse))
                {
                    return false;
                }

                if (control.device is Keyboard &&
                    (string.Equals(control.name, "escape", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(control.name, "f5", StringComparison.OrdinalIgnoreCase)))
                {
                    return false;
                }

                string deviceLayout = control.device is Keyboard ? "Keyboard" : "Mouse";
                canonicalPath = $"<{deviceLayout}>/{control.name}";
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        public static bool TryFindConflict(
            GameInputActionId actionId,
            GameInputBindingSlot slot,
            string candidatePath,
            out GameInputBindingDefinition conflict)
        {
            if (!TryGetCanonicalRebindPath(candidatePath, out string canonicalCandidate))
            {
                conflict = default;
                return false;
            }

            for (int definitionIndex = 0;
                 definitionIndex < BindingDefinitions.Length;
                 definitionIndex++)
            {
                GameInputBindingDefinition otherDefinition =
                    BindingDefinitions[definitionIndex];
                for (int slotIndex = 0; slotIndex < 2; slotIndex++)
                {
                    GameInputBindingSlot otherSlot =
                        (GameInputBindingSlot)slotIndex;
                    if (otherDefinition.ActionId == actionId && otherSlot == slot)
                    {
                        continue;
                    }

                    string otherPath = GetEffectivePath(otherDefinition.ActionId, otherSlot);
                    if (!TryGetCanonicalRebindPath(otherPath, out string canonicalOther) ||
                        !string.Equals(
                            canonicalCandidate,
                            canonicalOther,
                            StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    if (AreCompatibleDuplicates(actionId, otherDefinition.ActionId))
                    {
                        continue;
                    }

                    conflict = otherDefinition;
                    return true;
                }
            }

            conflict = default;
            return false;
        }

        public static bool TryValidateCurrentBindings(out string error)
        {
            if (GameplayMap == null)
            {
                error = $"'{GameplayMapName}' Input Action Map을 찾을 수 없습니다.";
                return false;
            }

            for (int definitionIndex = 0;
                 definitionIndex < BindingDefinitions.Length;
                 definitionIndex++)
            {
                GameInputBindingDefinition definition = BindingDefinitions[definitionIndex];
                if (!TryResolveBinding(
                        definition.ActionId,
                        GameInputBindingSlot.Primary,
                        out _,
                        out _))
                {
                    error = $"{definition.DisplayName}의 기본 키 binding이 없습니다.";
                    return false;
                }

                if (!TryResolveBinding(
                        definition.ActionId,
                        GameInputBindingSlot.Secondary,
                        out _,
                        out _))
                {
                    error = $"{definition.DisplayName}의 보조 키 binding이 없습니다.";
                    return false;
                }

                string primaryPath = GetEffectivePath(
                    definition.ActionId,
                    GameInputBindingSlot.Primary);
                if (!IsSupportedRebindPath(primaryPath))
                {
                    error = $"{definition.DisplayName}의 기본 키가 유효하지 않습니다.";
                    return false;
                }

                string secondaryPath = GetEffectivePath(
                    definition.ActionId,
                    GameInputBindingSlot.Secondary);
                if (!string.IsNullOrWhiteSpace(secondaryPath) &&
                    !IsSupportedRebindPath(secondaryPath))
                {
                    error = $"{definition.DisplayName}의 보조 키가 유효하지 않습니다.";
                    return false;
                }

                if (TryFindConflict(
                        definition.ActionId,
                        GameInputBindingSlot.Primary,
                        primaryPath,
                        out GameInputBindingDefinition primaryConflict))
                {
                    error = $"{definition.DisplayName}과 {primaryConflict.DisplayName}의 키가 중복됩니다.";
                    return false;
                }

                if (!string.IsNullOrWhiteSpace(secondaryPath) &&
                    TryFindConflict(
                        definition.ActionId,
                        GameInputBindingSlot.Secondary,
                        secondaryPath,
                        out GameInputBindingDefinition secondaryConflict))
                {
                    error = $"{definition.DisplayName}과 {secondaryConflict.DisplayName}의 키가 중복됩니다.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool AreCompatibleDuplicates(
            GameInputActionId first,
            GameInputActionId second)
        {
            return (first == GameInputActionId.Run &&
                    second == GameInputActionId.QuickTransferModifier) ||
                   (first == GameInputActionId.QuickTransferModifier &&
                    second == GameInputActionId.Run);
        }
    }
}
