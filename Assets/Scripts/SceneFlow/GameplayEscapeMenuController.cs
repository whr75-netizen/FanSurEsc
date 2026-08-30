using FantasySurvival.Controls;
using FantasySurvival.Raids;
using FantasySurvival.SaveSystem;
using FantasySurvival.WorldLighting;
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
            EnvironmentTest,
            Confirmation,
            Result
        }

        private enum ConfirmationAction
        {
            None,
            AbandonToBase,
            AbandonToMainMenu,
            DismissBaseSaveFailure
        }

        [Header("Owners")]
        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private RaidSession raidSession;
        [SerializeField] private SkyLightingCycleController skyLighting;

        [Header("View roots")]
        [SerializeField] private GameObject pauseCanvas;
        [SerializeField] private Image backdropImage;
        [SerializeField] private GameObject mainPanel;
        [SerializeField] private GameObject settingsPanel;
        [SerializeField] private GameObject environmentTestPanel;
        [SerializeField] private GameObject confirmationPanel;
        [SerializeField] private GameObject resultPanel;

        [Header("Main menu")]
        [SerializeField] private Text menuTitleText;
        [SerializeField] private Button baseResumeButton;
        [SerializeField] private Button raidResumeButton;
        [SerializeField] private Button abandonButton;
        [SerializeField] private Button settingsButton;
        [SerializeField] private Button environmentTestButton;
        [SerializeField] private Button mainMenuButton;

        [Header("Settings")]
        [SerializeField] private Toggle soundToggle;
        [SerializeField] private KeyBindingSettingsPanel keyBindingPanel;
        [SerializeField] private Button settingsBackButton;

        [Header("Environment test")]
        [SerializeField] private Text environmentTestStatusText;
        [SerializeField] private Button dayTestButton;
        [SerializeField] private Button nightTestButton;
        [SerializeField] private Button clearWeatherTestButton;
        [SerializeField] private Button rainWeatherTestButton;
        [SerializeField] private Button environmentTestBackButton;

        [Header("Confirmation")]
        [SerializeField] private Text confirmationText;
        [SerializeField] private Button confirmationAcceptButton;
        [SerializeField] private Button confirmationCancelButton;

        [Header("Raid result")]
        [SerializeField] private Text resultTitleText;
        [SerializeField] private Text resultDetailText;
        [SerializeField] private Button resultReturnToBaseButton;
        [SerializeField] private Text resultPrimaryButtonText;
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
        private bool environmentTestAutomaticAdvanceAtOpen;
        private bool environmentTestClockOverrideActive;
        private Color defaultBackdropColor;
        private bool extractionSettlementFlow;
        private bool extractionSettlementCommitted;
        private bool extractionSettlementFailed;
        private RaidOutcome extractionSettlementOutcome;
        private BasePersistenceController activeBasePersistence;

        public bool IsConfigured =>
            shell != null && raidSession != null && skyLighting != null &&
            pauseCanvas != null && backdropImage != null &&
            mainPanel != null && settingsPanel != null &&
            environmentTestPanel != null && confirmationPanel != null && resultPanel != null &&
            menuTitleText != null && baseResumeButton != null && raidResumeButton != null &&
            abandonButton != null && settingsButton != null &&
            environmentTestButton != null && mainMenuButton != null &&
            soundToggle != null && keyBindingPanel != null && settingsBackButton != null &&
            environmentTestStatusText != null && dayTestButton != null &&
            nightTestButton != null && clearWeatherTestButton != null &&
            rainWeatherTestButton != null && environmentTestBackButton != null &&
            confirmationText != null && confirmationAcceptButton != null &&
            confirmationCancelButton != null && resultTitleText != null &&
            resultDetailText != null && resultReturnToBaseButton != null &&
            resultPrimaryButtonText != null &&
            resultMainMenuButton != null;
        public bool IsOpen => currentView != MenuView.Closed;
        public bool IsMapSelectionVisible =>
            registeredMapSelection != null && registeredMapSelection.IsVisible;
        public bool IsWorldPaused => ownsWorldPause && Mathf.Approximately(Time.timeScale, 0f);
        public bool IsEnvironmentTestOpen => currentView == MenuView.EnvironmentTest;
        public string CurrentViewName => currentView.ToString();
        public bool IsExtractionSettlementPending =>
            extractionSettlementFlow &&
            !extractionSettlementCommitted &&
            !extractionSettlementFailed;
        public bool IsExtractionSettlementConfirmationReady =>
            extractionSettlementFlow && extractionSettlementCommitted;
        public bool IsExtractionSettlementRetryVisible =>
            extractionSettlementFlow && extractionSettlementFailed;
        public bool HasRegisteredBasePersistence => activeBasePersistence != null;

        private void Awake()
        {
            if (backdropImage != null)
            {
                defaultBackdropColor = backdropImage.color;
            }

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

            if (shell?.RaidCheckpoint != null)
            {
                shell.RaidCheckpoint.SettlementCommitted += HandleSettlementCommitted;
                shell.RaidCheckpoint.SettlementFailed += HandleSettlementFailed;
            }
            if (shell?.SceneTransitionFader != null)
            {
                shell.SceneTransitionFader.Covered += HandleTravelCovered;
            }
        }

        private void OnDisable()
        {
            if (raidSession != null)
            {
                raidSession.Resolved -= HandleRaidResolved;
                raidSession.ReturnTravelFailed -= HandleReturnTravelFailed;
            }

            if (shell?.RaidCheckpoint != null)
            {
                shell.RaidCheckpoint.SettlementCommitted -= HandleSettlementCommitted;
                shell.RaidCheckpoint.SettlementFailed -= HandleSettlementFailed;
            }
            if (shell?.SceneTransitionFader != null)
            {
                shell.SceneTransitionFader.Covered -= HandleTravelCovered;
            }

            registeredMapSelection = null;
            extractionSettlementFlow = false;
            extractionSettlementCommitted = false;
            extractionSettlementFailed = false;
            extractionSettlementOutcome = RaidOutcome.None;
            HideAllAndReleaseInput();
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (shell?.RaidCheckpoint != null && shell.RaidCheckpoint.IsSettlementInputLocked)
                {
                    return;
                }

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
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(false);
            soundToggle.SetIsOnWithoutNotify(GameUserSettings.SoundEnabled);
            keyBindingPanel.Refresh();
            Select(settingsBackButton);
        }

        public void BackToMainMenuPanel()
        {
            if (currentView == MenuView.Settings ||
                currentView == MenuView.EnvironmentTest ||
                currentView == MenuView.Confirmation)
            {
                RestoreEnvironmentTestClock();
                ShowMainPanel();
            }
        }

        public void OpenEnvironmentTest()
        {
            if (currentView != MenuView.Main)
            {
                return;
            }

            currentView = MenuView.EnvironmentTest;
            environmentTestAutomaticAdvanceAtOpen =
                skyLighting != null && skyLighting.IsAdvancingAutomatically;
            environmentTestClockOverrideActive = false;
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(true);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(false);
            UpdateEnvironmentTestStatus();
            Select(dayTestButton);
        }

        public void SetEnvironmentTestDay()
        {
            if (currentView != MenuView.EnvironmentTest)
            {
                return;
            }

            BeginEnvironmentTestClockOverride();
            if (!skyLighting.SetPhase(SkyTimePhase.Day))
            {
                Debug.LogError("Failed to apply the Day environment test state.", this);
            }

            UpdateEnvironmentTestStatus();
        }

        public void SetEnvironmentTestNight()
        {
            if (currentView != MenuView.EnvironmentTest)
            {
                return;
            }

            BeginEnvironmentTestClockOverride();
            if (!skyLighting.SetPhase(SkyTimePhase.Night))
            {
                Debug.LogError("Failed to apply the Night environment test state.", this);
            }

            UpdateEnvironmentTestStatus();
        }

        public void SetEnvironmentTestClearWeather()
        {
            if (currentView != MenuView.EnvironmentTest)
            {
                return;
            }

            if (!skyLighting.SetWeather(SkyWeatherType.Clear, true))
            {
                Debug.LogError("Failed to apply the Clear weather test state.", this);
            }

            UpdateEnvironmentTestStatus();
        }

        public void SetEnvironmentTestRainWeather()
        {
            if (currentView != MenuView.EnvironmentTest)
            {
                return;
            }

            if (!skyLighting.SetWeather(SkyWeatherType.Rain, true))
            {
                Debug.LogError("Failed to apply the Rain weather test state.", this);
            }

            UpdateEnvironmentTestStatus();
        }

        public void SetSoundEnabled(bool enabled)
        {
            if (GameUserSettings.TrySetSoundEnabled(enabled, out string error))
            {
                return;
            }

            soundToggle.SetIsOnWithoutNotify(GameUserSettings.SoundEnabled);
            Debug.LogError(error, this);
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

            if (raidSession.CurrentSceneKind == GameplaySceneKind.Base &&
                !TrySaveBaseBeforeMainMenuExit())
            {
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

            if (action == ConfirmationAction.DismissBaseSaveFailure)
            {
                ShowMainPanel();
                return;
            }

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

        public bool RegisterBasePersistence(BasePersistenceController controller)
        {
            if (controller == null ||
                (activeBasePersistence != null && activeBasePersistence != controller))
            {
                return false;
            }

            activeBasePersistence = controller;
            return true;
        }

        public void UnregisterBasePersistence(BasePersistenceController controller)
        {
            if (activeBasePersistence == controller)
            {
                activeBasePersistence = null;
            }
        }

        public void ReturnToBaseFromResult()
        {
            if (currentView != MenuView.Result)
            {
                return;
            }

            if (extractionSettlementFlow)
            {
                if (extractionSettlementCommitted)
                {
                    extractionSettlementFlow = false;
                    extractionSettlementCommitted = false;
                    extractionSettlementFailed = false;
                    extractionSettlementOutcome = RaidOutcome.None;
                    HideAllAndReleaseInput();
                }
                else if (extractionSettlementFailed &&
                         shell?.RaidCheckpoint != null &&
                         shell.RaidCheckpoint.HasPendingBaseSettlement)
                {
                    RaidOutcome retryOutcome = extractionSettlementOutcome;
                    ShowExtractionSettlementProgress(retryOutcome);
                    if (!shell.RaidCheckpoint.TryCommitTrackedRaidAtBase(out string error))
                    {
                        Debug.LogError($"Raid settlement retry failed: {error}", this);
                        ShowExtractionSettlementFailure();
                    }
                }
                else if (raidSession.IsRaidResolved)
                {
                    ShowExtractionSettlementProgress(raidSession.Outcome);
                    raidSession.TryReturnToBase();
                }

                return;
            }

            if (raidSession.IsRaidResolved)
            {
                BeginReturnToBase();
            }
        }

        public void GoToMainMenuFromResult()
        {
            if (!extractionSettlementFlow &&
                currentView == MenuView.Result &&
                raidSession.IsRaidResolved)
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
                if (keyBindingPanel.TryCancelPendingRebind())
                {
                    return;
                }

                ShowMainPanel();
                return;
            }

            if (currentView == MenuView.EnvironmentTest)
            {
                BackToMainMenuPanel();
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

            if (shell.InformationWindow != null && shell.InformationWindow.IsOpen)
            {
                shell.InformationWindow.TryClose();
                return;
            }

            if (shell.QuestPanel != null && shell.QuestPanel.IsOpen)
            {
                shell.QuestPanel.TryClose();
                return;
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

            RestoreEnvironmentTestClock();
            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Main;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(true);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(false);
            SetExtractionBackdrop(false);

            bool isBase = raidSession.CurrentSceneKind == GameplaySceneKind.Base;
            bool isRaid = raidSession.CurrentSceneKind == GameplaySceneKind.Raid &&
                          raidSession.IsRaidActive;
            menuTitleText.text = isBase ? "일시정지" : "원정 메뉴";
            baseResumeButton.gameObject.SetActive(isBase);
            raidResumeButton.gameObject.SetActive(isRaid);
            abandonButton.gameObject.SetActive(isRaid);
            settingsButton.gameObject.SetActive(isBase || isRaid);
            environmentTestButton.gameObject.SetActive(isBase || isRaid);
            mainMenuButton.gameObject.SetActive(isBase || isRaid);
            Select(isBase ? baseResumeButton : raidResumeButton);
        }

        private void ShowConfirmation(string message)
        {
            currentView = MenuView.Confirmation;
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(true);
            resultPanel.SetActive(false);
            SetExtractionBackdrop(false);
            confirmationText.text = message;
            Select(confirmationCancelButton);
        }

        private void ShowResult(RaidOutcome resolvedOutcome)
        {
            if (resolvedOutcome == RaidOutcome.None &&
                (raidSession == null || !raidSession.IsRaidResolved))
            {
                return;
            }

            // Outcome.None is allowed only for a resolved technical return failure,
            // such as a fresh invalid-map rollback whose Base scene loaded but could
            // not complete arrival. The existing default result gives that safe state
            // explicit Retry Base and Main Menu exits without inventing a gameplay loss.

            if (!inputLockHeld && !TryAcquireInputLock(false, false))
            {
                return;
            }

            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Result;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(true);
            SetExtractionBackdrop(false);
            SetResultCopy(resolvedOutcome, false);
            resultReturnToBaseButton.gameObject.SetActive(true);
            resultPrimaryButtonText.text = "기지로 돌아가기";
            resultMainMenuButton.gameObject.SetActive(true);
            Select(resultReturnToBaseButton);
        }

        private void ShowExtractionSettlementProgress(RaidOutcome resolvedOutcome)
        {
            extractionSettlementFlow = true;
            extractionSettlementCommitted = false;
            extractionSettlementFailed = false;
            extractionSettlementOutcome = resolvedOutcome;
            if (!inputLockHeld && !TryAcquireInputLock(false, false))
            {
                return;
            }

            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Result;
            SetAllPanelsInactive();
            pauseCanvas.SetActive(false);
            SetExtractionBackdrop(false);
            resultReturnToBaseButton.gameObject.SetActive(false);
            resultMainMenuButton.gameObject.SetActive(false);

            if (shell?.SceneTransitionFader != null &&
                shell.SceneTransitionFader.IsCovered)
            {
                DisplayExtractionSettlementProgress();
            }
        }

        private void DisplayExtractionSettlementProgress()
        {
            if (!extractionSettlementFlow || extractionSettlementCommitted)
            {
                return;
            }

            pauseCanvas.SetActive(true);
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(true);
            SetExtractionBackdrop(true);
            resultTitleText.text = extractionSettlementOutcome == RaidOutcome.Extracted
                ? "생환 처리 중"
                : "원정 결과 처리 중";
            resultDetailText.text =
                "기지로 이동하고 원정 결과를 정산하고 있습니다.\n완료될 때까지 잠시 기다려 주십시오.";
            resultReturnToBaseButton.gameObject.SetActive(false);
            resultMainMenuButton.gameObject.SetActive(false);
            Select(null);
        }

        private void ShowExtractionSettlementComplete(RaidOutcome committedOutcome)
        {
            if (!inputLockHeld && !TryAcquireInputLock(false, false))
            {
                return;
            }

            extractionSettlementFlow = true;
            extractionSettlementCommitted = true;
            extractionSettlementFailed = false;
            extractionSettlementOutcome = committedOutcome;
            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Result;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(true);
            SetExtractionBackdrop(true);
            SetResultCopy(committedOutcome, true);
            resultReturnToBaseButton.gameObject.SetActive(true);
            resultPrimaryButtonText.text = "확인";
            resultMainMenuButton.gameObject.SetActive(false);
            Select(resultReturnToBaseButton);
        }

        private void ShowExtractionSettlementFailure()
        {
            if (!extractionSettlementFlow)
            {
                return;
            }

            extractionSettlementCommitted = false;
            extractionSettlementFailed = true;
            confirmationAction = ConfirmationAction.None;
            currentView = MenuView.Result;
            pauseCanvas.SetActive(true);
            mainPanel.SetActive(false);
            settingsPanel.SetActive(false);
            environmentTestPanel.SetActive(false);
            confirmationPanel.SetActive(false);
            resultPanel.SetActive(true);
            SetExtractionBackdrop(true);
            resultTitleText.text = "정산 실패";
            resultDetailText.text =
                "세이브와 원정 복구 정보 정리를 완료하지 못했습니다.\n정산을 다시 시도해 주십시오.";
            resultReturnToBaseButton.gameObject.SetActive(true);
            resultPrimaryButtonText.text = "정산 재시도";
            resultMainMenuButton.gameObject.SetActive(false);
            Select(resultReturnToBaseButton);
        }

        private void ShowExtractionReturnRetry(RaidOutcome resolvedOutcome)
        {
            ShowExtractionSettlementProgress(resolvedOutcome);
            DisplayExtractionSettlementProgress();
            resultTitleText.text = "기지 이동 실패";
            resultDetailText.text =
                "원정 결과 정산은 아직 완료되지 않았습니다.\n기지 이동을 다시 시도해 주십시오.";
            resultReturnToBaseButton.gameObject.SetActive(true);
            resultPrimaryButtonText.text = "기지 이동 재시도";
            resultMainMenuButton.gameObject.SetActive(false);
            Select(resultReturnToBaseButton);
        }

        private void SetResultCopy(RaidOutcome resolvedOutcome, bool settlementComplete)
        {
            switch (resolvedOutcome)
            {
                case RaidOutcome.Extracted:
                    resultTitleText.text = "원정 성공";
                    resultDetailText.text = settlementComplete
                        ? "정산이 완료되었습니다.\n플레이어가 소지한 아이템과 장비를 유지합니다."
                        : "귀환 지점에 도착했습니다.\n플레이어가 소지한 아이템과 장비를 유지합니다.";
                    break;
                case RaidOutcome.PlayerDied:
                    resultTitleText.text = "원정 실패";
                    resultDetailText.text = "플레이어가 사망했습니다.\n플레이어가 소지한 아이템과 장비를 모두 잃습니다.";
                    break;
                case RaidOutcome.Abandoned:
                    resultTitleText.text = "원정 포기";
                    resultDetailText.text = "원정은 포기 처리되었습니다.\n플레이어가 소지한 아이템과 장비를 모두 잃습니다.";
                    break;
                case RaidOutcome.RecoveryFailed:
                    resultTitleText.text = "원정 복구 실패";
                    resultDetailText.text = "저장된 원정 상태를 안전하게 복구하지 못했습니다.\n기지 보관물은 유지하고 플레이어 소지품과 장비를 잃습니다.";
                    break;
                default:
                    resultTitleText.text = "원정 종료";
                    resultDetailText.text = "원정 결과를 확인할 수 없습니다.";
                    break;
            }
        }

        private void HandleRaidResolved(RaidOutcome resolvedOutcome)
        {
            RaidOutcome authoritativeOutcome = raidSession != null
                ? raidSession.Outcome
                : resolvedOutcome;
            bool isAutomaticExtractionReturn =
                raidSession != null && raidSession.IsAutomaticExtractionReturn;
            if (isAutomaticExtractionReturn || extractionSettlementFlow)
            {
                ShowExtractionSettlementProgress(authoritativeOutcome);
            }
            else if (authoritativeOutcome != RaidOutcome.Abandoned)
            {
                ShowResult(authoritativeOutcome);
            }
        }

        private void HandleSettlementCommitted(RaidOutcome committedOutcome)
        {
            if (extractionSettlementFlow)
            {
                ShowExtractionSettlementComplete(committedOutcome);
            }
        }

        private void HandleSettlementFailed()
        {
            if (extractionSettlementFlow)
            {
                ShowExtractionSettlementFailure();
            }
        }

        private void HandleTravelCovered()
        {
            DisplayExtractionSettlementProgress();
        }

        private void HandleReturnTravelFailed()
        {
            if (extractionSettlementFlow)
            {
                ShowExtractionReturnRetry(raidSession.Outcome);
            }
            else
            {
                ShowResult(raidSession.Outcome);
            }
        }

        private void BeginReturnToBase()
        {
            HideAllAndReleaseInput();
            if (!raidSession.TryReturnToBase())
            {
                ShowResult(raidSession.Outcome);
            }
        }

        private bool TrySaveBaseBeforeMainMenuExit()
        {
            if (activeBasePersistence == null || !activeBasePersistence.isActiveAndEnabled)
            {
                ShowBaseSaveFailure(
                    "기지 저장 기능이 준비되지 않아 주 메뉴로 이동할 수 없습니다.");
                return false;
            }

            if (activeBasePersistence.SaveSlotOne())
            {
                return true;
            }

            ShowBaseSaveFailure(activeBasePersistence.CurrentStatusMessage);
            return false;
        }

        private void ShowBaseSaveFailure(string detail)
        {
            confirmationAction = ConfirmationAction.DismissBaseSaveFailure;
            string reason = string.IsNullOrWhiteSpace(detail)
                ? "기지 상태를 저장하지 못했습니다."
                : detail;
            ShowConfirmation(
                "저장에 실패하여 주 메뉴 이동을 취소했습니다.\n" + reason);
            Debug.LogError("Main Menu exit was blocked because the base save failed.", this);
        }

        private void BeginMainMenuExit()
        {
            if (extractionSettlementFlow)
            {
                return;
            }

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

            shell.InformationWindow?.TryClose();
            shell.QuestPanel?.TryClose();
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
            RestoreEnvironmentTestClock();
            currentView = MenuView.Closed;
            confirmationAction = ConfirmationAction.None;
            SetAllPanelsInactive();
            if (pauseCanvas != null)
            {
                pauseCanvas.SetActive(false);
            }
            SetExtractionBackdrop(false);

            EventSystem eventSystem = shell != null ? shell.PlayerEventSystem : null;
            if (eventSystem != null)
            {
                eventSystem.SetSelectedGameObject(null);
            }

            ReleaseInputLock();
        }

        private void BeginEnvironmentTestClockOverride()
        {
            if (skyLighting == null)
            {
                return;
            }

            environmentTestClockOverrideActive = true;
            skyLighting.SetAutomaticAdvance(false);
        }

        private void RestoreEnvironmentTestClock()
        {
            if (!environmentTestClockOverrideActive || skyLighting == null)
            {
                return;
            }

            skyLighting.SetAutomaticAdvance(
                environmentTestAutomaticAdvanceAtOpen);
            environmentTestClockOverrideActive = false;
        }

        private void SetExtractionBackdrop(bool opaque)
        {
            if (backdropImage == null)
            {
                return;
            }

            Color color = defaultBackdropColor;
            if (opaque)
            {
                color = Color.black;
            }

            backdropImage.color = color;
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
            if (environmentTestPanel != null) environmentTestPanel.SetActive(false);
            if (confirmationPanel != null) confirmationPanel.SetActive(false);
            if (resultPanel != null) resultPanel.SetActive(false);
        }

        private void UpdateEnvironmentTestStatus()
        {
            if (environmentTestStatusText == null || skyLighting == null)
            {
                return;
            }

            string timeLabel = skyLighting.CurrentPhase == SkyTimePhase.Night
                ? "밤"
                : "낮";
            string weatherLabel = skyLighting.CurrentWeatherType == SkyWeatherType.Rain
                ? "비"
                : "맑음";
            environmentTestStatusText.text =
                $"시간: {timeLabel} ({skyLighting.CurrentHour:0.0}시)\n" +
                $"날씨: {weatherLabel}";
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
