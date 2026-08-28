using System;
using UnityEngine;
using UnityEngine.UI;

namespace FantasySurvival.Controls
{
    [DisallowMultipleComponent]
    public sealed class KeyBindingRowView : MonoBehaviour
    {
        [SerializeField] private Text actionLabel;
        [SerializeField] private Button primaryButton;
        [SerializeField] private Text primaryKeyText;
        [SerializeField] private Button secondaryButton;
        [SerializeField] private Text secondaryKeyText;
        [Tooltip("Optional per-row button that clears only the secondary binding.")]
        [SerializeField] private Button clearSecondaryButton;
        [Tooltip("Optional per-row button that resets both bindings on this row.")]
        [SerializeField] private Button resetRowButton;

        private GameInputBindingDefinition definition;
        private Action<GameInputActionId, GameInputBindingSlot> bindingRequested;
        private Action<GameInputActionId> secondaryClearRequested;
        private Action<GameInputActionId> rowResetRequested;
        private bool buttonsInteractable = true;

        public bool IsConfigured =>
            actionLabel != null && primaryButton != null && primaryKeyText != null &&
            secondaryButton != null && secondaryKeyText != null;

        public void Configure(
            GameInputBindingDefinition bindingDefinition,
            Action<GameInputActionId, GameInputBindingSlot> onBindingRequested,
            Action<GameInputActionId> onSecondaryClearRequested = null,
            Action<GameInputActionId> onRowResetRequested = null)
        {
            definition = bindingDefinition;
            bindingRequested = onBindingRequested;
            secondaryClearRequested = onSecondaryClearRequested;
            rowResetRequested = onRowResetRequested;

            primaryButton.onClick.RemoveListener(RequestPrimaryBinding);
            secondaryButton.onClick.RemoveListener(RequestSecondaryBinding);
            primaryButton.onClick.AddListener(RequestPrimaryBinding);
            secondaryButton.onClick.AddListener(RequestSecondaryBinding);
            if (clearSecondaryButton != null)
            {
                clearSecondaryButton.onClick.RemoveListener(ClearSecondaryBinding);
                clearSecondaryButton.onClick.AddListener(ClearSecondaryBinding);
            }

            if (resetRowButton != null)
            {
                resetRowButton.onClick.RemoveListener(ResetRowToDefaults);
                resetRowButton.onClick.AddListener(ResetRowToDefaults);
            }

            actionLabel.text = string.IsNullOrWhiteSpace(definition.Category)
                ? definition.DisplayName
                : $"[{definition.Category}] {definition.DisplayName}";
            Refresh();
        }

        public void Refresh()
        {
            primaryKeyText.text = GameInputBindings.GetBindingDisplayName(
                definition.ActionId,
                GameInputBindingSlot.Primary);
            secondaryKeyText.text = GameInputBindings.GetBindingDisplayName(
                definition.ActionId,
                GameInputBindingSlot.Secondary);
            RefreshUtilityButtons();
        }

        public void SetListening(GameInputBindingSlot slot)
        {
            Refresh();
            if (slot == GameInputBindingSlot.Primary)
            {
                primaryKeyText.text = "입력 대기...";
            }
            else
            {
                secondaryKeyText.text = "입력 대기...";
            }
        }

        public void SetButtonsInteractable(bool interactable)
        {
            buttonsInteractable = interactable;
            primaryButton.interactable = interactable;
            secondaryButton.interactable = interactable;
            RefreshUtilityButtons();
        }

        public void ClearSecondaryBinding()
        {
            secondaryClearRequested?.Invoke(definition.ActionId);
        }

        public void ResetRowToDefaults()
        {
            rowResetRequested?.Invoke(definition.ActionId);
        }

        private void RequestPrimaryBinding()
        {
            bindingRequested?.Invoke(
                definition.ActionId,
                GameInputBindingSlot.Primary);
        }

        private void RequestSecondaryBinding()
        {
            bindingRequested?.Invoke(
                definition.ActionId,
                GameInputBindingSlot.Secondary);
        }

        private void RefreshUtilityButtons()
        {
            if (clearSecondaryButton != null)
            {
                clearSecondaryButton.interactable =
                    buttonsInteractable &&
                    !string.IsNullOrWhiteSpace(GameInputBindings.GetEffectivePath(
                        definition.ActionId,
                        GameInputBindingSlot.Secondary));
            }

            if (resetRowButton != null)
            {
                resetRowButton.interactable =
                    buttonsInteractable &&
                    (GameInputBindings.HasBindingOverride(
                         definition.ActionId,
                         GameInputBindingSlot.Primary) ||
                     GameInputBindings.HasBindingOverride(
                         definition.ActionId,
                         GameInputBindingSlot.Secondary));
            }
        }

        private void OnDestroy()
        {
            if (primaryButton != null)
            {
                primaryButton.onClick.RemoveListener(RequestPrimaryBinding);
            }

            if (secondaryButton != null)
            {
                secondaryButton.onClick.RemoveListener(RequestSecondaryBinding);
            }

            if (clearSecondaryButton != null)
            {
                clearSecondaryButton.onClick.RemoveListener(ClearSecondaryBinding);
            }

            if (resetRowButton != null)
            {
                resetRowButton.onClick.RemoveListener(ResetRowToDefaults);
            }
        }
    }
}
