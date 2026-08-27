using FantasySurvival.SaveSystem;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace FantasySurvival.Controls
{
    [DisallowMultipleComponent]
    public sealed class KeyBindingSettingsPanel : MonoBehaviour
    {
        [SerializeField] private RectTransform rowsRoot;
        [SerializeField] private KeyBindingRowView rowTemplate;
        [SerializeField] private Text statusText;
        [SerializeField] private Button resetButton;

        private readonly System.Collections.Generic.List<KeyBindingRowView> rows =
            new System.Collections.Generic.List<KeyBindingRowView>();

        private InputActionRebindingExtensions.RebindingOperation rebindOperation;
        private InputAction rebindingAction;
        private InputBinding previousBinding;
        private int rebindingIndex = -1;
        private bool rebindingActionWasEnabled;
        private GameInputActionId rebindingActionId;
        private GameInputBindingSlot rebindingSlot;
        private int lastRebindCancellationFrame = -1;

        public bool IsConfigured =>
            rowsRoot != null && rowTemplate != null && rowTemplate.IsConfigured &&
            statusText != null && resetButton != null;
        public bool IsRebinding => rebindOperation != null;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError(
                    $"{nameof(KeyBindingSettingsPanel)} has missing required references.",
                    this);
                enabled = false;
                return;
            }

            rowTemplate.gameObject.SetActive(false);
            EnsureRows();
        }

        private void OnEnable()
        {
            if (!IsConfigured)
            {
                return;
            }

            GameUserSettings.InputBindingsChanged += HandleBindingsChanged;
            resetButton.onClick.AddListener(ResetToDefaults);
            SetStatus("변경할 키를 누른 뒤 새 키를 입력하세요. Esc는 변경 취소입니다.");
            Refresh();
        }

        private void OnDisable()
        {
            GameUserSettings.InputBindingsChanged -= HandleBindingsChanged;
            if (resetButton != null)
            {
                resetButton.onClick.RemoveListener(ResetToDefaults);
            }

            TryCancelPendingRebind();
        }

        public void Refresh()
        {
            if (!IsConfigured)
            {
                return;
            }

            EnsureRows();
            for (int index = 0; index < rows.Count; index++)
            {
                rows[index].Refresh();
                rows[index].SetButtonsInteractable(!IsRebinding);
            }

            resetButton.interactable = !IsRebinding;
        }

        public bool TryCancelPendingRebind()
        {
            if (rebindOperation == null)
            {
                return lastRebindCancellationFrame == Time.frameCount;
            }

            rebindOperation.Cancel();
            return true;
        }

        public void ResetToDefaults()
        {
            TryCancelPendingRebind();
            if (GameUserSettings.TryResetInputBindings(out string error))
            {
                SetStatus("키 설정을 기본값으로 복원했습니다.");
            }
            else
            {
                SetStatus(error);
            }

            Refresh();
        }

        private void EnsureRows()
        {
            if (rows.Count > 0)
            {
                return;
            }

            System.Collections.Generic.IReadOnlyList<GameInputBindingDefinition> definitions =
                GameInputBindings.Definitions;
            for (int index = 0; index < definitions.Count; index++)
            {
                KeyBindingRowView row = Instantiate(rowTemplate, rowsRoot);
                row.name = $"{definitions[index].ActionId}BindingRow";
                row.gameObject.SetActive(true);
                row.Configure(definitions[index], StartRebind);
                rows.Add(row);
            }
        }

        private void StartRebind(
            GameInputActionId actionId,
            GameInputBindingSlot slot)
        {
            if (IsRebinding)
            {
                return;
            }

            if (!GameInputBindings.TryResolveBinding(
                    actionId,
                    slot,
                    out InputAction action,
                    out int bindingIndex))
            {
                SetStatus("변경할 입력 binding을 찾을 수 없습니다.");
                return;
            }

            rebindingActionId = actionId;
            rebindingSlot = slot;
            rebindingAction = action;
            rebindingIndex = bindingIndex;
            previousBinding = action.bindings[bindingIndex];
            rebindingActionWasEnabled = action.enabled;
            if (rebindingActionWasEnabled)
            {
                action.Disable();
            }

            GameInputBindingDefinition definition =
                GameInputBindings.GetDefinition(actionId);
            SetStatus($"'{definition.DisplayName}'에 사용할 키를 누르세요. Esc: 취소");
            SetRowsListening(actionId, slot);

            try
            {
                rebindOperation = action
                    .PerformInteractiveRebinding(bindingIndex)
                    .WithCancelingThrough("<Keyboard>/escape")
                    .WithControlsExcluding("<Keyboard>/f5")
                    .WithControlsExcluding("<Gamepad>")
                    .WithControlsExcluding("<Joystick>")
                    .WithControlsExcluding("<Touchscreen>")
                    .WithControlsExcluding("<XRController>")
                    .WithControlsExcluding("<Pen>")
                    .OnComplete(HandleRebindCompleted)
                    .OnCancel(HandleRebindCancelled);
                rebindOperation.Start();
            }
            catch (System.Exception exception)
            {
                RestorePreviousBinding();
                DisposeRebindOperation();
                SetStatus($"키 변경을 시작하지 못했습니다: {exception.Message}");
                Refresh();
            }
        }

        private void HandleRebindCompleted(
            InputActionRebindingExtensions.RebindingOperation operation)
        {
            string candidatePath = rebindingAction != null && rebindingIndex >= 0
                ? rebindingAction.bindings[rebindingIndex].effectivePath
                : string.Empty;
            GameInputBindingDefinition definition =
                GameInputBindings.GetDefinition(rebindingActionId);

            // Interactive rebinding writes immediately. Restore the exact previous
            // override first, then let GameUserSettings perform the validated commit.
            RestorePreviousBinding();
            DisposeRebindOperation();

            if (GameUserSettings.TrySetInputBinding(
                    rebindingActionId,
                    rebindingSlot,
                    candidatePath,
                    out string error))
            {
                SetStatus(
                    $"'{definition.DisplayName}'을(를) " +
                    $"{GameInputBindings.FormatControlPath(candidatePath)}로 변경했습니다.");
            }
            else
            {
                SetStatus(error);
            }

            Refresh();
        }

        private void HandleRebindCancelled(
            InputActionRebindingExtensions.RebindingOperation operation)
        {
            lastRebindCancellationFrame = Time.frameCount;
            RestorePreviousBinding();
            DisposeRebindOperation();
            SetStatus("키 변경을 취소했습니다.");
            Refresh();
        }

        private void RestorePreviousBinding()
        {
            if (rebindingAction == null || rebindingIndex < 0)
            {
                return;
            }

            if (string.IsNullOrEmpty(previousBinding.overridePath) &&
                string.IsNullOrEmpty(previousBinding.overrideInteractions) &&
                string.IsNullOrEmpty(previousBinding.overrideProcessors))
            {
                rebindingAction.RemoveBindingOverride(rebindingIndex);
                return;
            }

            rebindingAction.ApplyBindingOverride(
                rebindingIndex,
                new InputBinding
                {
                    overridePath = previousBinding.overridePath,
                    overrideInteractions = previousBinding.overrideInteractions,
                    overrideProcessors = previousBinding.overrideProcessors
                });
        }

        private void DisposeRebindOperation()
        {
            InputAction action = rebindingAction;
            bool shouldEnable = rebindingActionWasEnabled;

            rebindOperation?.Dispose();
            rebindOperation = null;
            rebindingAction = null;
            rebindingIndex = -1;
            rebindingActionWasEnabled = false;
            previousBinding = default;

            if (shouldEnable && action != null)
            {
                action.Enable();
            }
        }

        private void SetRowsListening(
            GameInputActionId actionId,
            GameInputBindingSlot slot)
        {
            System.Collections.Generic.IReadOnlyList<GameInputBindingDefinition> definitions =
                GameInputBindings.Definitions;
            for (int index = 0; index < rows.Count; index++)
            {
                rows[index].Refresh();
                rows[index].SetButtonsInteractable(false);
                if (definitions[index].ActionId == actionId)
                {
                    rows[index].SetListening(slot);
                }
            }

            resetButton.interactable = false;
        }

        private void HandleBindingsChanged()
        {
            Refresh();
        }

        private void SetStatus(string message)
        {
            if (statusText != null)
            {
                statusText.text = message ?? string.Empty;
            }
        }
    }
}
