using FantasySurvival.Raids;
using FantasySurvival.SaveSystem;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FantasySurvival.SceneFlow
{
    [DefaultExecutionOrder(-9000)]
    [DisallowMultipleComponent]
    public sealed class GameplayEscapeMenuController : MonoBehaviour
    {
        private enum MenuView
        {
            Closed,
            Main,
            Settings,
            Confirmation,
            Result
        }

        private enum ConfirmationAction
        {
            None,
            AbandonToBase,
            AbandonToMainMenu
        }

        [Header("Owners")]
        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private RaidSession raidSession;

        [Header("View roots")]
        [SerializeField] private GameObject pauseCanvas;
        [SerializeField] private GameObject mainPanel;
        [SerializeField] private GameObject settingsPanel;
        [SerializeField] private GameObject confirmationPanel;
        [SerializeField] private GameObject resultPanel;

        [Header("Main menu")]
        [SerializeField] private Text menuTitleText;
        [SerializeField] private Button baseResumeButton;
        [SerializeField] private Button raidResumeButton;
        [SerializeField] private Button abandonButton;
        [SerializeField] private Button settingsButton;
        [SerializeField] private Button mainMenuButton;

        [Header("Settings")]
        [SerializeField] private Toggle soundToggle;
        [SerializeField] private Button settingsBackButton;

        [Header("Confirmation")]
        [SerializeField] private Text confirmationText;
        [SerializeField] private Button confirmationAcceptButton;
        [SerializeField] private Button confirmationCancelButton;

        [Header("Raid result")]
        [SerializeField] private Text resultTitleText;
        [SerializeField] private Text resultDetailText;
        [SerializeField] private Button resultReturnToBaseButton;
        [SerializeField] private Button resultMainMenuButton;

        private MenuView currentView;
        private ConfirmationAction confirmationAction;
        private MapSelectionOverlay registeredMapSelection;

        private bool inputLockHeld;
        private bool movementWasEnabled;
        private bool inventoryInputWasBlocked;
        private bool interactionWasBlocked;
        private bool ownsWorldPause;
        private float previousTimeScale = 1f;

        public bool IsConfigured =>
            shell != null && raidSession != null &&
            pauseCanvas != null && mainPanel != null && settingsPanel != null &&
            confirmationPanel != null && resultPanel != null &&
            menuTitleText != null && baseResumeButton != null && raidResumeButton != null &&
            abandonButton != null && settingsButton != null && mainMenuButton != null &&
            soundToggle != null && settingsBackButton != null &&
            confirmationText != null && confirmationAcceptButton != null &&
            confirmationCancelButton != null && resultTitleText != null &&
            resultDetailText != null && resultReturnToBaseButton != null &&
            resultMainMenuButton != null;
        public bool IsOpen => currentView != MenuView.Closed;
        public bool IsWorldPaused => ownsWorldPause && Mathf.Approximately(Time.timeScale, 0f);
        public string CurrentViewName => currentView.ToString();

        private void Awake()
        {
            SetAllPanelsInactive();
            if (pauseCanvas != null)
            {
                pauseCanvas.SetActive(false);
            }

            currentView = MenuView.Closed;
            confirmationAction = ConfirmationAction.None;

            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(GameplayEscapeMenuController)} has missing required references.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            if (raidSession != null)
            {
                raidSession.Resolved += HandleRaidResolved;
                raidSession.ReturnTravelFailed += HandleReturnTravelFailed;
            }
        }

        private void OnDisable()
        {
            if (raidSession != null)
            {
                raidSession.Resolved -= HandleRaidResolved;
                raidSession.ReturnTravelFailed -= HandleReturnTravelFailed;
            }

            registeredMapSelection = null;
            HideAllAndReleaseInput();
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                HandleEscape();
            }
        }

        public bool TryRegisterMapSelectionOverlay(MapSelectionOverlay overlay)
        {
            if (overlay == null || IsOpen || GameplaySessionExit.IsExiting)
            {
                return false;
            }

            if (registeredMapSelection != null && registeredMapSelection != overlay)
            {
                return false;
            }

            registeredMapSelection = overlay;
            return true;
        }

        public void UnregisterMapSelectionOverlay(MapSelectionOverlay overlay)
        {
            if (registeredMapSelection == overlay)
            {
                registeredMapSelection = null;
            }
        }

        public void OpenMenuForCurrentContext()
        {
            OpenRootMenu();
        }

        public void CloseMenu()
        {
            if (currentView == MenuView.Result)
            {
                return;
            }

            HideAllAndReleaseInput();
        }

        public void OpenSettings()
        {
            if (currentView != MenuView.Main)
            {
                return;
            }

            currentView = MenuView.Settings;
            mainPanel.SetActive(false);
            settingsPanel.SetActive(true);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(false);
            soundToggle.SetIsOnWithoutNotify(GameUserSettings.SoundEnabled);
            Select(settingsBackButton);
        }

        public void BackToMainMenuPanel()
        {
            if (currentView == MenuView.Settings || currentView == MenuView.Confirmation)
            {
                ShowMainPanel();
            }
        }

        public void SetSoundEnabled(bool enabled)
        {
            GameUserSettings.SetSoundEnabled(enabled);
        }

        public void RequestAbandonToBase()
        {
            if (currentView != MenuView.Main || !raidSession.IsRaidActive)
            {
                return;
            }

            confirmationAction = ConfirmationAction.AbandonToBase;
            ShowConfirmation("원정을 포기하시겠습니까?\n확인하면 기지로 돌아갑니다.");
        }

        public void RequestMainMenu()
        {
            if (currentView != MenuView.Main)
            {
                return;
            }

            if (raidSession.IsRaidActive)
            {
                confirmationAction = ConfirmationAction.AbandonToMainMenu;
                ShowConfirmation("원정을 포기하시겠습니까?\n확인하면 주 메뉴로 이동합니다.");
                return;
            }

            if (raidSession.IsRaidResolved)
            {
                ShowResult(raidSession.Outcome);
                return;
            }

            BeginMainMenuExit();
        }

        public void ConfirmPendingAction()
        {
            if (currentView != MenuView.Confirmation ||
                confirmationAction == ConfirmationAction.None)
            {
                return;
            }

            ConfirmationAction action = confirmationAction;
            confirmationAction = ConfirmationAction.None;

            if (!raidSession.IsRaidActive || !raidSession.TryResolveAbandonment())
            {
                if (raidSession.IsRaidResolved)
                {
                    ShowResult(raidSession.Outcome);
                }
                else
                {
                    ShowMainPanel();
                }
                return;
            }

            if (action == ConfirmationAction.AbandonToBase)
            {
                BeginReturnToBase();
            }
            else
            {
                BeginMainMenuExit();
            }
        }

        public void CancelConfirmation()
        {
            if (currentView != MenuView.Confirmation)
            {
                return;
            }

            confirmationAction = ConfirmationAction.None;
            ShowMainPanel();
        }

        public void ReturnToBaseFromResult()
        {
            if (currentView == MenuView.Result && raidSession.IsRaidResolved)
            {
                BeginReturnToBase();
            }
        }

        public void GoToMainMenuFromResult()
        {
            if (currentView == MenuView.Result && raidSession.IsRaidResolved)
            {
                BeginMainMenuExit();
            }
        }

        private void HandleEscape()
        {
            if (GameplaySessionExit.IsExiting || DirectSceneTravel.IsLoading)
            {
                return;
            }

            if (currentView == MenuView.Result)
            {
                return;
            }

            if (currentView == MenuView.Confirmation)
            {
                CancelConfirmation();
                return;
            }

            if (currentView == MenuView.Settings)
            {
                ShowMainPanel();
                return;
            }

            if (currentView == MenuView.Main)
            {
                CloseMenu();
                return;
            }

            if (registeredMapSelection != null && registeredMapSelection.IsVisible)
            {
                registeredMapSelection.Cancel();
                return;
            }

            if (registeredMapSelection != null)
            {
                registeredMapSelection = null;
            }

            InventoryUIManager inventory = shell.InventoryUI;
            if (inventory != null && inventory.IsAnyInventoryOpen)
            {
                inventory.CloseAllInventories();
                return;
            }

            OpenRootMenu();
        }

        private void OpenRootMenu()
        {
            if (DirectSceneTravel.IsLoading || GameplaySessionExit.IsExiting)
            {
                return;
            }

            GameplaySceneKind sceneKind = raidSession.CurrentSceneKind;
            if (sceneKind == GameplaySceneKind.Raid && raidSession.IsRaidResolved)
            {
                ShowResult(raidSession.Outcome);
                return;
            }

            bool isBase = sceneKind == GameplaySceneKind.Base;
            bool isRaid = sceneKind == GameplaySceneKind.Raid && raidSession.IsRaidActive;
            if (!isBase && !isRaid)
            {
                return;
            }

            if (!TryAcquireInputLock(isBase, true))
            {
                return;
            }

            pauseCanvas.SetActive(true);
            ShowMainPanel();
        }

        private void ShowMainPanel()
        {
            if (!inputLockHeld)
            {
                return;
            }

            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Main;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(true);
            settingsPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(false);

            bool isBase = raidSession.CurrentSceneKind == GameplaySceneKind.Base;
            bool isRaid = raidSession.CurrentSceneKind == GameplaySceneKind.Raid &&
                          raidSession.IsRaidActive;
            menuTitleText.text = isBase ? "일시정지" : "원정 메뉴";
            baseResumeButton.gameObject.SetActive(isBase);
            raidResumeButton.gameObject.SetActive(isRaid);
            abandonButton.gameObject.SetActive(isRaid);
            settingsButton.gameObject.SetActive(isBase || isRaid);
            mainMenuButton.gameObject.SetActive(isBase || isRaid);
            Select(isBase ? baseResumeButton : raidResumeButton);
        }

        private void ShowConfirmation(string message)
        {
            currentView = MenuView.Confirmation;
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            confirmationPanel.SetActive(true);
            resultPanel.SetActive(false);
            confirmationText.text = message;
            Select(confirmationCancelButton);
        }

        private void ShowResult(RaidOutcome resolvedOutcome)
        {
            if (resolvedOutcome == RaidOutcome.None)
            {
                return;
            }

            if (!inputLockHeld && !TryAcquireInputLock(false, false))
            {
                return;
            }

            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Result;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(true);

            switch (resolvedOutcome)
            {
                case RaidOutcome.Extracted:
                    resultTitleText.text = "원정 성공";
                    resultDetailText.text = "귀환 지점에 도착했습니다.\n현재 시험 버전에서는 아이템 손실 규칙을 적용하지 않습니다.";
                    break;
                case RaidOutcome.PlayerDied:
                    resultTitleText.text = "원정 실패";
                    resultDetailText.text = "플레이어가 사망했습니다.\n현재 시험 버전에서는 아이템 손실 규칙을 적용하지 않습니다.";
                    break;
                default:
                    resultTitleText.text = "원정 포기";
                    resultDetailText.text = "원정은 포기 처리되었습니다.\n기지 이동을 다시 시도할 수 있습니다.";
                    break;
            }

            Select(resultReturnToBaseButton);
        }

        private void HandleRaidResolved(RaidOutcome resolvedOutcome)
        {
            if (resolvedOutcome != RaidOutcome.Abandoned)
            {
                ShowResult(resolvedOutcome);
            }
        }

        private void HandleReturnTravelFailed()
        {
            ShowResult(raidSession.Outcome);
        }

        private void BeginReturnToBase()
        {
            HideAllAndReleaseInput();
            if (!raidSession.TryReturnToBase())
            {
                ShowResult(raidSession.Outcome);
            }
        }

        private void BeginMainMenuExit()
        {
            HideAllAndReleaseInput();
            GameplaySessionExit.TryExitToMainMenu(HandleMainMenuExitFailed);
        }

        private void HandleMainMenuExitFailed()
        {
            if (raidSession.IsRaidResolved)
            {
                ShowResult(raidSession.Outcome);
            }
            else
            {
                OpenRootMenu();
            }
        }

        private bool TryAcquireInputLock(bool pauseWorld, bool requireSafeInventoryClose)
        {
            if (inputLockHeld)
            {
                return true;
            }

            InventoryUIManager inventory = shell.InventoryUI;
            bool inventoriesClosed = inventory != null && inventory.CloseAllInventories();
            if (!inventoriesClosed && requireSafeInventoryClose)
            {
                return false;
            }

            if (!inventoriesClosed)
            {
                Debug.LogError(
                    "A terminal raid result blocked Player input, but the active inventory drag could not be restored.",
                    this);
            }

            movementWasEnabled = shell.PlayerMovement != null && shell.PlayerMovement.enabled;
            inventoryInputWasBlocked = inventory != null && inventory.InputBlocked;
            interactionWasBlocked = shell.PlayerInteractor != null && shell.PlayerInteractor.InteractionBlocked;
            previousTimeScale = Time.timeScale;
            inputLockHeld = true;

            if (shell.PlayerMovement != null)
            {
                shell.PlayerMovement.enabled = false;
            }
            inventory?.SetInputBlocked(true);
            shell.PlayerInteractor?.SetInteractionBlocked(true);

            ownsWorldPause = pauseWorld;
            if (ownsWorldPause)
            {
                Time.timeScale = 0f;
            }

            return true;
        }

        private void HideAllAndReleaseInput()
        {
            currentView = MenuView.Closed;
            confirmationAction = ConfirmationAction.None;
            SetAllPanelsInactive();
            if (pauseCanvas != null)
            {
                pauseCanvas.SetActive(false);
            }

            EventSystem eventSystem = shell != null ? shell.PlayerEventSystem : null;
            if (eventSystem != null)
            {
                eventSystem.SetSelectedGameObject(null);
            }

            ReleaseInputLock();
        }

        private void ReleaseInputLock()
        {
            if (!inputLockHeld)
            {
                return;
            }

            if (ownsWorldPause)
            {
                Time.timeScale = previousTimeScale;
            }

            if (shell != null)
            {
                if (shell.PlayerMovement != null)
                {
                    shell.PlayerMovement.enabled = movementWasEnabled;
                }
                if (shell.InventoryUI != null)
                {
                    shell.InventoryUI.SetInputBlocked(inventoryInputWasBlocked);
                }
                if (shell.PlayerInteractor != null)
                {
                    shell.PlayerInteractor.SetInteractionBlocked(interactionWasBlocked);
                }
            }

            inputLockHeld = false;
            ownsWorldPause = false;
            movementWasEnabled = false;
            inventoryInputWasBlocked = false;
            interactionWasBlocked = false;
            previousTimeScale = 1f;
        }

        private void SetAllPanelsInactive()
        {
            if (mainPanel != null) mainPanel.SetActive(false);
            if (settingsPanel != null) settingsPanel.SetActive(false);
            if (confirmationPanel != null) confirmationPanel.SetActive(false);
            if (resultPanel != null) resultPanel.SetActive(false);
        }

        private void Select(Selectable selectable)
        {
            EventSystem eventSystem = shell != null ? shell.PlayerEventSystem : null;
            if (eventSystem == null)
            {
                return;
            }

            eventSystem.SetSelectedGameObject(null);
            if (selectable != null && selectable.gameObject.activeInHierarchy)
            {
                eventSystem.SetSelectedGameObject(selectable.gameObject);
            }
        }
    }
}
