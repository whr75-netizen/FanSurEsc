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

        private GameInputBindingDefinition definition;
        private Action<GameInputActionId, GameInputBindingSlot> bindingRequested;

        public bool IsConfigured =>
            actionLabel != null && primaryButton != null && primaryKeyText != null &&
            secondaryButton != null && secondaryKeyText != null;

        public void Configure(
            GameInputBindingDefinition bindingDefinition,
            Action<GameInputActionId, GameInputBindingSlot> onBindingRequested)
        {
            definition = bindingDefinition;
            bindingRequested = onBindingRequested;

            primaryButton.onClick.RemoveListener(RequestPrimaryBinding);
            secondaryButton.onClick.RemoveListener(RequestSecondaryBinding);
            primaryButton.onClick.AddListener(RequestPrimaryBinding);
            secondaryButton.onClick.AddListener(RequestSecondaryBinding);

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
            primaryButton.interactable = interactable;
            secondaryButton.interactable = interactable;
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
        }
    }
}
