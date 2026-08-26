using FantasySurvival.Interaction;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FantasySurvival.Quests
{
    [DisallowMultipleComponent]
    public sealed class QuestPanelController : MonoBehaviour
    {
        [SerializeField] private QuestJournal journal;
        [SerializeField] private InventoryUIManager inventoryUI;
        [SerializeField] private EventSystem eventSystem;
        [SerializeField] private GameObject dialogRoot;
        [SerializeField] private Text titleText;
        [SerializeField] private Text descriptionText;
        [SerializeField] private Text statusText;
        [SerializeField] private Button primaryButton;
        [SerializeField] private Text primaryButtonText;
        [SerializeField] private Button closeButton;
        [SerializeField] private GameObject trackerRoot;
        [SerializeField] private Text trackerText;

        private QuestGiverInteractable activeSource;
        private QuestDefinition activeDefinition;
        private bool inventoryInputWasBlocked;
        private bool ownsInventoryInputLock;

        public bool IsConfigured =>
            journal != null && journal.IsConfigured && inventoryUI != null && eventSystem != null &&
            dialogRoot != null && titleText != null && descriptionText != null &&
            statusText != null && primaryButton != null && primaryButtonText != null &&
            closeButton != null && trackerRoot != null && trackerText != null;
        public bool IsOpen => dialogRoot != null && dialogRoot.activeSelf;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(QuestPanelController)} has missing required references.", this);
                enabled = false;
                return;
            }

            primaryButton.onClick.AddListener(HandlePrimaryAction);
            closeButton.onClick.AddListener(HandleCloseRequested);
            dialogRoot.SetActive(false);
            RefreshView();
        }

        private void OnEnable()
        {
            if (journal != null)
            {
                journal.Changed += RefreshView;
            }
        }

        private void OnDisable()
        {
            if (journal != null)
            {
                journal.Changed -= RefreshView;
            }

            CloseInternal();
        }

        private void OnDestroy()
        {
            if (primaryButton != null)
            {
                primaryButton.onClick.RemoveListener(HandlePrimaryAction);
            }
            if (closeButton != null)
            {
                closeButton.onClick.RemoveListener(HandleCloseRequested);
            }
        }

        public bool TryToggle(QuestGiverInteractable source, QuestDefinition definition)
        {
            if (!isActiveAndEnabled || source == null || !journal.OwnsDefinition(definition))
            {
                return false;
            }

            if (IsOpenFor(source))
            {
                return TryClose(source);
            }

            if (IsOpen)
            {
                CloseInternal();
            }

            if (!inventoryUI.CloseAllInventories())
            {
                Debug.LogWarning(
                    "Quest panel could not open because the active inventory drag could not be restored.",
                    this);
                return false;
            }

            inventoryInputWasBlocked = inventoryUI.InputBlocked;
            inventoryUI.SetInputBlocked(true);
            ownsInventoryInputLock = true;
            activeSource = source;
            activeDefinition = definition;
            dialogRoot.SetActive(true);
            RefreshView();
            Select(primaryButton.interactable ? primaryButton : closeButton);
            return true;
        }

        public bool IsOpenFor(QuestGiverInteractable source)
        {
            return source != null && IsOpen && activeSource == source;
        }

        public bool TryClose(QuestGiverInteractable source = null)
        {
            if (source != null && activeSource != source)
            {
                return !IsOpen;
            }

            CloseInternal();
            return true;
        }

        private void HandlePrimaryAction()
        {
            if (activeDefinition == null)
            {
                return;
            }

            if (journal.Status == QuestProgressStatus.Available)
            {
                journal.TryAccept(activeDefinition);
            }
            else if (journal.Status == QuestProgressStatus.ReadyToTurnIn)
            {
                journal.TryTurnIn(activeDefinition);
            }
        }

        private void HandleCloseRequested()
        {
            TryClose();
        }

        private void CloseInternal()
        {
            if (dialogRoot != null)
            {
                dialogRoot.SetActive(false);
            }

            activeSource = null;
            activeDefinition = null;
            if (eventSystem != null)
            {
                eventSystem.SetSelectedGameObject(null);
            }

            if (ownsInventoryInputLock && inventoryUI != null)
            {
                inventoryUI.SetInputBlocked(inventoryInputWasBlocked);
            }

            ownsInventoryInputLock = false;
            inventoryInputWasBlocked = false;
        }

        private void RefreshView()
        {
            if (journal == null || journal.Definition == null)
            {
                if (trackerRoot != null)
                {
                    trackerRoot.SetActive(false);
                }
                return;
            }

            QuestDefinition definition = journal.Definition;
            QuestProgressStatus status = journal.Status;
            if (titleText != null)
            {
                titleText.text = definition.DisplayName;
            }
            if (descriptionText != null)
            {
                descriptionText.text = definition.Description;
            }

            string progress = $"적 처치 {journal.EnemyKills}/{journal.RequiredEnemyKills}";
            switch (status)
            {
                case QuestProgressStatus.Available:
                    SetDialogState($"목표: {progress} 후 생환", "수락", true);
                    break;
                case QuestProgressStatus.Active:
                    SetDialogState(
                        journal.EnemyKills >= journal.RequiredEnemyKills
                            ? "목표 달성: 살아서 기지로 귀환하십시오."
                            : $"진행 중: {progress}",
                        "진행 중",
                        false);
                    break;
                case QuestProgressStatus.ReadyToTurnIn:
                    SetDialogState("생환 확인 완료: 의뢰를 보고할 수 있습니다.", "완료 보고", true);
                    break;
                case QuestProgressStatus.Completed:
                    SetDialogState("의뢰 완료 (시험 보상 없음)", "완료됨", false);
                    break;
            }

            if (trackerRoot != null)
            {
                bool showTracker = status == QuestProgressStatus.Active ||
                                   status == QuestProgressStatus.ReadyToTurnIn;
                showTracker &= !journal.IsRaidTransitionOrSettlementPending;
                trackerRoot.SetActive(showTracker);
                if (showTracker && trackerText != null)
                {
                    trackerText.text = status == QuestProgressStatus.ReadyToTurnIn
                        ? $"{definition.DisplayName}\n기지 NPC에게 완료 보고"
                        : journal.EnemyKills >= journal.RequiredEnemyKills
                            ? $"{definition.DisplayName}\n목표 달성 - 살아서 귀환"
                            : $"{definition.DisplayName}\n{progress}";
                }
            }
        }

        private void SetDialogState(string status, string buttonLabel, bool buttonEnabled)
        {
            if (statusText != null)
            {
                statusText.text = status;
            }
            if (primaryButtonText != null)
            {
                primaryButtonText.text = buttonLabel;
            }
            if (primaryButton != null)
            {
                primaryButton.interactable = buttonEnabled;
            }
        }

        private void Select(Selectable selectable)
        {
            if (eventSystem == null || selectable == null || !selectable.gameObject.activeInHierarchy)
            {
                return;
            }

            eventSystem.SetSelectedGameObject(null);
            eventSystem.SetSelectedGameObject(selectable.gameObject);
        }
    }
}
