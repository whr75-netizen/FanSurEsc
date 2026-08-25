using System;
using System.Collections.Generic;
using System.Globalization;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using FantasySurvival.SaveSystem;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class MainMenuManager : MonoBehaviour
{
    private enum RaidRecoveryDecision
    {
        None,
        ResumeOrFail,
        Settle,
        SettleOrphaned
    }

    [Header("Panels")]
    [SerializeField] private GameObject mainPanel;
    [SerializeField] private GameObject loadPanel;
    [SerializeField] private GameObject settingsPanel;
    [SerializeField] private GameObject exitPanel;

    [Header("Raid Recovery")]
    [SerializeField] private GameObject recoveryPanel;
    [SerializeField] private Text recoveryText;
    [SerializeField] private Button resumeRaidButton;
    [SerializeField] private Button failRaidButton;

    [Header("Load Slot")]
    [SerializeField] private ItemDatabase itemDatabase;
    [SerializeField] private BaseFurnitureDatabase furnitureDatabase;
    [SerializeField] private Text loadSlotText;
    [SerializeField] private Button loadSlotButton;

    [Header("Settings")]
    [SerializeField] private Toggle soundToggle;

    [Header("Status")]
    [SerializeField] private Text statusText;

    private GameSaveData cachedSave;
    private GameSaveData cachedFallbackSave;
    private RaidRecoveryBaselineData cachedRecoveryBaseline;
    private RaidCheckpointData cachedRecoveryCheckpoint;
    private GameSaveData cachedRecoverySettlementState;
    private RaidOutcome cachedRecoveryOutcome;
    private GameSaveData cachedOrphanedRaidSave;
    private RaidRecoveryDecision recoveryDecision;
    private bool recoveryDecisionRequired;
    private bool orphanedRaidSettlementBlocked;
    private bool recoverySettlementDurabilityBlocked;

    private void Awake()
    {
        GameUserSettings.Apply();
        InitializeRaidRecoveryView();
    }

#if UNITY_EDITOR
    public void ReinitializeRaidRecoveryForEditorTests()
    {
        InitializeRaidRecoveryView();
    }
#endif

    public void StartGame()
    {
        StartNewGame();
    }

    public void StartNewGame()
    {
        if (BlockNormalStartForRaidRecovery())
        {
            return;
        }

        GameStartRequest.QueueNewGame();
        SceneManager.LoadScene("GameLoadingScene");
    }

    public void OpenLoadPanel()
    {
        if (BlockNormalStartForRaidRecovery())
        {
            return;
        }

        bool canLoad = TrySelectLoadCandidate(out bool loadedBackup, out string status);

        if (canLoad)
        {
            loadSlotText.text = loadedBackup
                ? $"Slot 1  {GameSaveManager.GetDisplayTimestamp(cachedSave)}  (backup recovered)"
                : $"Slot 1  {GameSaveManager.GetDisplayTimestamp(cachedSave)}";
            SetStatus(status);
        }
        else
        {
            loadSlotText.text = "Slot 1  Empty or unavailable";
            SetStatus(status);
        }

        if (loadSlotButton != null)
        {
            loadSlotButton.interactable = canLoad;
        }

        ShowOnly(loadPanel);
    }

    public void LoadSelectedGame()
    {
        if (BlockNormalStartForRaidRecovery())
        {
            return;
        }

        if (cachedSave == null && !TrySelectLoadCandidate(out _, out string error))
        {
            SetStatus(error);
            return;
        }

        if (!GameStartRequest.QueueLoad(cachedSave, cachedFallbackSave))
        {
            SetStatus("Could not queue the selected save.");
            return;
        }

        SceneManager.LoadScene("GameLoadingScene");
    }

    public void ResumeInterruptedRaid()
    {
        if (!recoveryDecisionRequired ||
            recoveryDecision != RaidRecoveryDecision.ResumeOrFail ||
            cachedRecoveryBaseline == null ||
            cachedRecoveryCheckpoint == null ||
            cachedRecoveryCheckpoint.phase != RaidCheckpointPhase.Active)
        {
            SetRecoveryStatus("이어갈 수 있는 활성 원정 체크포인트가 없습니다.");
            return;
        }

        if (!TryValidateCheckpointForLoad(
                cachedRecoveryBaseline,
                cachedRecoveryCheckpoint,
                out string validationError))
        {
            SetRecoveryStatus($"원정 체크포인트가 더 이상 유효하지 않습니다: {validationError}");
            return;
        }

        if (!GameStartRequest.QueueResumeRaid(
                cachedRecoveryBaseline,
                cachedRecoveryCheckpoint))
        {
            SetRecoveryStatus("원정 이어하기 요청을 준비하지 못했습니다.");
            return;
        }

        DisableRecoveryActions();
        SceneManager.LoadScene("GameLoadingScene");
    }

    public void FailInterruptedRaid()
    {
        if (!recoveryDecisionRequired)
        {
            SetRecoveryStatus("실패 처리할 원정 복구 기준점이 없습니다.");
            return;
        }

        if (recoverySettlementDurabilityBlocked)
        {
            if (!TrySecureRecoveryFailureDecision(out string retryError))
            {
                SetRecoveryStatus(
                    "원정 실패 상태의 이중화가 아직 완료되지 않았습니다. 다시 시도해 주세요: " +
                    retryError);
                return;
            }

            recoverySettlementDurabilityBlocked = false;
        }

        if (recoveryDecision == RaidRecoveryDecision.SettleOrphaned)
        {
            if (!GameStartRequest.QueueOrphanedRaidFailure(cachedOrphanedRaidSave))
            {
                SetRecoveryStatus("캐시가 없는 원정 실패 정산 요청을 준비하지 못했습니다.");
                return;
            }

            DisableRecoveryActions();
            SceneManager.LoadScene("GameLoadingScene");
            return;
        }

        if (cachedRecoveryBaseline == null)
        {
            SetRecoveryStatus("실패 처리할 원정 복구 기준점이 없습니다.");
            return;
        }

        RaidCheckpointData settlementCheckpoint = cachedRecoveryCheckpoint;
        if (recoveryDecision == RaidRecoveryDecision.ResumeOrFail)
        {
            if (!TryCreateRecoveryFailedCheckpoint(
                    cachedRecoveryBaseline,
                    cachedRecoveryCheckpoint,
                    out settlementCheckpoint,
                    out string checkpointError))
            {
                SetRecoveryStatus($"원정 실패 상태를 기록하지 못했습니다: {checkpointError}");
                return;
            }

            if (!RaidCheckpointStore.TryWriteCheckpoint(settlementCheckpoint, out string writeError))
            {
                SetRecoveryStatus($"원정 실패 상태를 안전하게 저장하지 못했습니다: {writeError}");
                return;
            }

            // The primary terminal record is already durable. Disable Resume before any
            // secondary marker/backup maintenance so this in-memory menu can never queue
            // the older Active candidate after the decision has advanced.
            cachedRecoveryCheckpoint = settlementCheckpoint;
            cachedRecoveryOutcome = RaidOutcome.RecoveryFailed;
            recoveryDecision = RaidRecoveryDecision.Settle;
            ShowRecoveryDecision(
                "중단된 원정을 실패 처리했습니다. 기지 상태 정산을 계속해 주세요.",
                false,
                false);

            if (!TrySecureRecoveryFailureDecision(out string durabilityError))
            {
                recoverySettlementDurabilityBlocked = true;
                SetRecoveryStatus(
                    "원정 실패 상태의 이중화가 완료되지 않아 정산 이동을 보류했습니다. " +
                    $"같은 버튼으로 다시 시도해 주세요: {durabilityError}");
                return;
            }
        }

        if (recoveryDecision != RaidRecoveryDecision.Settle)
        {
            SetRecoveryStatus("원정 복구 결정 상태가 올바르지 않습니다.");
            return;
        }

        if (!GameStartRequest.QueueRaidRecoverySettlement(
                cachedRecoveryBaseline,
                settlementCheckpoint,
                cachedRecoverySettlementState,
                RaidCheckpointValidator.IsTerminalOutcome(cachedRecoveryOutcome)
                    ? cachedRecoveryOutcome
                    : settlementCheckpoint != null &&
                      settlementCheckpoint.phase == RaidCheckpointPhase.Resolved
                        ? settlementCheckpoint.outcome
                        : RaidOutcome.RecoveryFailed))
        {
            SetRecoveryStatus("원정 실패·결과 정산 요청을 준비하지 못했습니다.");
            return;
        }

        DisableRecoveryActions();
        SceneManager.LoadScene("GameLoadingScene");
    }

    private bool TrySelectLoadCandidate(out bool loadedBackup, out string status)
    {
        cachedSave = null;
        cachedFallbackSave = null;
        loadedBackup = false;

        GameSaveManager.ReadSlotOneCandidates(
            out GameSaveData primary,
            out string primaryReadError,
            out GameSaveData backup,
            out string backupReadError);

        bool primaryValid = TryValidateLoadCandidate(primary, out string primaryValidationError);
        bool backupValid = TryValidateLoadCandidate(backup, out string backupValidationError);

        if (primaryValid)
        {
            cachedSave = primary;
            cachedFallbackSave = backupValid ? backup : null;
            status = string.Empty;
            return true;
        }

        if (backupValid)
        {
            cachedSave = backup;
            loadedBackup = true;
            status = "Primary save was invalid; a validated backup will be loaded.";
            return true;
        }

        status = $"Primary: {CombineReadAndValidationError(primaryReadError, primaryValidationError)} " +
                 $"Backup: {CombineReadAndValidationError(backupReadError, backupValidationError)}";
        return false;
    }

    private bool TryValidateLoadCandidate(GameSaveData candidate, out string error)
    {
        return TryValidateLoadCandidate(candidate, false, out error);
    }

    private bool TryValidateLoadCandidate(
        GameSaveData candidate,
        bool allowActiveRaidMarker,
        out string error)
    {
        try
        {
            if (candidate == null)
            {
                error = "No readable save.";
                return false;
            }

            if (!allowActiveRaidMarker && candidate.raidInProgress)
            {
                error = "An active-raid ordinary save cannot be loaded outside raid failure settlement.";
                return false;
            }

            if (!InventorySaveCodec.TryRestore(
                    candidate.playerItems,
                    itemDatabase,
                    InventoryUIManager.DefaultInventoryWidth,
                    InventoryUIManager.DefaultInventoryHeight,
                    out _,
                    out error))
            {
                return false;
            }

            return BaseFurnitureSaveCodec.TryRestore(
                candidate.baseState,
                itemDatabase,
                furnitureDatabase,
                out _,
                out error);
        }
        catch (Exception exception)
        {
            // A malformed primary must never prevent validation of the backup candidate.
            error = $"Save validation failed unexpectedly: {exception.Message}";
            return false;
        }
    }

    private static string CombineReadAndValidationError(string readError, string validationError)
    {
        return string.IsNullOrWhiteSpace(readError) ? validationError : readError;
    }

    public void OpenSettingsPanel()
    {
        if (soundToggle != null)
        {
            soundToggle.SetIsOnWithoutNotify(GameUserSettings.SoundEnabled);
        }

        ShowOnly(settingsPanel);
        SetStatus(string.Empty);
    }

    public void SetSoundEnabled(bool enabled)
    {
        GameUserSettings.SetSoundEnabled(enabled);
        SetStatus(enabled ? "Sound enabled." : "Sound disabled.");
    }

    public void OpenExitPanel()
    {
        ShowOnly(exitPanel);
        SetStatus(string.Empty);
    }

    public void ShowMainPanel()
    {
        if (recoveryDecisionRequired)
        {
            ShowCurrentRecoveryDecision();
            SetStatus("먼저 중단된 원정의 이어하기 또는 실패·결과 정산을 선택해 주세요.");
            return;
        }

        ShowMainPanelCore();
    }

    private void ShowMainPanelCore()
    {
        cachedSave = null;
        cachedFallbackSave = null;
        ShowOnly(mainPanel);
        SetStatus(string.Empty);
    }

    public void QuitGame()
    {
#if UNITY_EDITOR
        Debug.Log("Quit requested. Application.Quit only closes a built player.", this);
#endif
        Application.Quit();
    }

    private void ShowOnly(GameObject panel)
    {
        if (mainPanel != null) mainPanel.SetActive(panel == mainPanel);
        if (loadPanel != null) loadPanel.SetActive(panel == loadPanel);
        if (settingsPanel != null) settingsPanel.SetActive(panel == settingsPanel);
        if (exitPanel != null) exitPanel.SetActive(panel == exitPanel);
        if (recoveryPanel != null) recoveryPanel.SetActive(panel == recoveryPanel);
    }

    private void SetStatus(string message)
    {
        if (statusText != null)
        {
            statusText.text = message ?? string.Empty;
        }
    }

    private void InitializeRaidRecoveryView()
    {
        ClearCachedRaidRecovery();
        GameSaveManager.ReadSlotOneCandidates(
            out GameSaveData ordinaryPrimary,
            out _,
            out GameSaveData ordinaryBackup,
            out _);
        GameSaveData ordinaryHeader = ordinaryPrimary ?? ordinaryBackup;
        bool ordinaryDeclaresActiveRaid = ordinaryHeader != null &&
                                          ordinaryHeader.raidInProgress;

        // The ordinary slot is the first decision source. Without its active marker,
        // Recovery can only finish an exact, already-started settlement transaction;
        // it can never restore an older baseline/checkpoint or authorize Resume.
        if (!ordinaryDeclaresActiveRaid)
        {
            InitializeMarkerlessRecoveryView(ordinaryHeader);
            return;
        }

        if (itemDatabase == null || furnitureDatabase == null)
        {
            ShowUnrecoverableMarkedSave(
                "원정 진행 또는 정산 표식이 있지만 검증용 데이터베이스가 연결되지 않았습니다. " +
                "자료를 변경하지 않고 새 게임과 일반 로드를 차단했습니다.");
            Debug.LogError(
                "MainMenuManager cannot reconcile the ordinary raid marker because its databases are missing.",
                this);
            return;
        }

        GameSaveData ordinarySave = null;
        if (!TrySelectMarkedOrdinarySaveCandidate(
                ordinaryHeader.activeRaidInstanceId,
                ordinaryPrimary,
                ordinaryBackup,
                out ordinarySave))
        {
            ShowUnrecoverableMarkedSave(
                "일반 세이브에는 원정 진행 표식이 있지만 Player/기지 상태를 안전하게 복원할 수 없습니다. " +
                "새 게임과 일반 로드를 차단했습니다.");
            return;
        }

        cachedOrphanedRaidSave = ordinarySave;
        if (!RaidCheckpointStore.HasRecoveryArtifacts)
        {
            ShowOrphanedRaidDecision(ordinarySave);
            return;
        }

        bool baselineRead = RaidCheckpointStore.TryReadBaseline(
            out RaidRecoveryBaselineData baseline,
            out string baselineReadError);
        string baselineValidationError = null;
        bool baselineValid = baselineRead &&
                             TryValidateBaseline(baseline, out baselineValidationError);
        if (!baselineValid)
        {
            HandleInvalidRecoveryBaseline(
                CombineReadAndValidationError(baselineReadError, baselineValidationError));
            return;
        }

        if (!string.Equals(
                baseline.raidInstanceId,
                ordinarySave.activeRaidInstanceId,
                StringComparison.Ordinal))
        {
            HandleInvalidRecoveryBaseline(
                "Recovery baseline raid ID does not match the ordinary save's active-raid marker.");
            return;
        }

        cachedRecoveryBaseline = baseline;
        RaidCheckpointStore.ReadCheckpointCandidates(
            out RaidCheckpointData primary,
            out string primaryReadError,
            out RaidCheckpointData backup,
            out string backupReadError);

        bool primaryValid = TryValidateCheckpointForLoad(
            baseline,
            primary,
            out string primaryValidationError);
        bool backupValid = TryValidateCheckpointForLoad(
            baseline,
            backup,
            out string backupValidationError);

        bool selectedBackup;
        cachedRecoveryCheckpoint = SelectNewestCheckpoint(
            primaryValid ? primary : null,
            backupValid ? backup : null,
            out selectedBackup);
        recoveryDecisionRequired = true;

        if (RaidCheckpointStore.HasSettlementJournalArtifacts)
        {
            bool journalSelected = TrySelectSettlementJournal(
                baseline,
                null,
                out RaidSettlementJournalData journal,
                out bool journalBackup,
                out bool exactStateInvalid,
                out string journalStatus);
            if (!journalSelected && exactStateInvalid)
            {
                ShowUnrecoverableMarkedSave(
                    "정산 저널의 정확한 상태가 손상되었고 유효한 exact 백업도 없어 " +
                    "더 오래된 체크포인트로 되돌릴 수 없습니다.");
                return;
            }
            cachedRecoveryOutcome = journalSelected
                ? journal.outcome
                : cachedRecoveryCheckpoint != null &&
                  cachedRecoveryCheckpoint.phase == RaidCheckpointPhase.Resolved &&
                  RaidCheckpointValidator.IsTerminalOutcome(cachedRecoveryCheckpoint.outcome)
                    ? cachedRecoveryCheckpoint.outcome
                    : RaidOutcome.RecoveryFailed;
            if (journalSelected && journal.settlementState != null)
            {
                if (TryValidateRecoveryPersistentState(
                        journal.settlementState,
                        out string stateError))
                {
                    cachedRecoverySettlementState = journal.settlementState;
                }
                else
                {
                    ShowUnrecoverableMarkedSave(
                        "정산 저널의 정확한 상태가 손상되어 더 오래된 체크포인트로 되돌릴 수 없습니다. " +
                        $"자료를 변경하지 않고 정산을 차단했습니다: {stateError}");
                    return;
                }
            }

            recoveryDecision = RaidRecoveryDecision.Settle;
            string journalBackupNotice = journalBackup
                ? "\n정상인 정산 저널 백업을 사용합니다."
                : string.Empty;
            ShowRecoveryDecision(
                $"이 원정은 이미 실패 또는 결과 정산 단계입니다. 이어하기는 허용되지 않습니다." +
                $"{journalBackupNotice}\n{journalStatus}",
                false,
                false);
            return;
        }

        if (cachedRecoveryCheckpoint == null)
        {
            recoveryDecision = RaidRecoveryDecision.Settle;
            ShowRecoveryDecision(
                "실시간 원정 체크포인트를 복구할 수 없습니다. " +
                "출발 전 기준점으로 원정을 실패 처리하고 기지 상태를 정산할 수 있습니다.",
                false,
                true);
            Debug.LogWarning(
                "Raid live checkpoints were unavailable while the recovery baseline remained valid. " +
                $"Primary: {CombineReadAndValidationError(primaryReadError, primaryValidationError)} " +
                $"Backup: {CombineReadAndValidationError(backupReadError, backupValidationError)}",
                this);
            return;
        }

        string displayTimestamp = RaidCheckpointStore.GetDisplayTimestamp(
            cachedRecoveryCheckpoint.savedAtUtc);
        string backupNotice = selectedBackup ? "\n정상인 백업 체크포인트를 사용합니다." : string.Empty;
        if (cachedRecoveryCheckpoint.phase == RaidCheckpointPhase.Active)
        {
            recoveryDecision = RaidRecoveryDecision.ResumeOrFail;
            ShowRecoveryDecision(
                $"비정상 종료된 원정이 있습니다.\n저장 시각: {displayTimestamp}" +
                $"{backupNotice}\n이어하거나 원정 실패로 처리할 수 있습니다.",
                true,
                true);
            return;
        }

        cachedRecoveryOutcome = cachedRecoveryCheckpoint.outcome;
        recoveryDecision = RaidRecoveryDecision.Settle;
        ShowRecoveryDecision(
            $"{GetResolvedRecoveryMessage(cachedRecoveryCheckpoint.outcome)}\n" +
            $"저장 시각: {displayTimestamp}{backupNotice}",
            false,
            false);
    }

    private void InitializeMarkerlessRecoveryView(GameSaveData ordinarySave)
    {
        if (!RaidCheckpointStore.HasRecoveryArtifacts)
        {
            ShowMainPanelCore();
            return;
        }

        if (!RaidCheckpointStore.HasSettlementJournalArtifacts)
        {
            QuarantineUnreferencedRecovery(
                "The ordinary save does not declare an active raid and no settlement journal exists.");
            return;
        }

        if (itemDatabase == null || furnitureDatabase == null)
        {
            ShowUnrecoverableMarkedSave(
                "일반 세이브의 원정 표식은 정리됐지만 남은 정산 자료를 검증할 데이터베이스가 없습니다. " +
                "자료를 변경하지 않고 시작을 차단했습니다.");
            return;
        }

        bool baselineRead = RaidCheckpointStore.TryReadBaseline(
            out RaidRecoveryBaselineData baseline,
            out string baselineReadError);
        string baselineValidationError = null;
        if (!baselineRead ||
            !TryValidateBaseline(baseline, out baselineValidationError))
        {
            QuarantineUnreferencedRecovery(
                "Marker-free settlement baseline is invalid: " +
                CombineReadAndValidationError(baselineReadError, baselineValidationError));
            return;
        }

        bool journalSelected = TrySelectSettlementJournal(
                baseline,
                ordinarySave,
                out RaidSettlementJournalData journal,
                out bool selectedBackup,
                out _,
                out string journalStatus);
        string settlementStateError = null;
        if (!journalSelected ||
            journal.settlementState == null ||
            !TryValidateRecoveryPersistentState(
                journal.settlementState,
                out settlementStateError) ||
            !AreCanonicalJsonEquivalent(ordinarySave, journal.settlementState))
        {
            QuarantineUnreferencedRecovery(
                "Marker-free Recovery did not contain a valid exact settlement transaction. " +
                $"Journal: {journalStatus} State: {settlementStateError}");
            return;
        }

        cachedRecoveryBaseline = baseline;
        cachedRecoveryCheckpoint = null;
        cachedRecoverySettlementState = journal.settlementState;
        cachedRecoveryOutcome = journal.outcome;
        recoveryDecisionRequired = true;
        recoveryDecision = RaidRecoveryDecision.Settle;
        string backupNotice = selectedBackup
            ? "\n정상인 정산 저널 백업을 사용합니다."
            : string.Empty;
        ShowRecoveryDecision(
            "일반 세이브 정산은 완료됐지만 미러 백업 또는 복구 캐시 정리가 중단되었습니다. " +
            $"동일한 정산 상태로 마무리합니다.{backupNotice}",
            false,
            false);
    }

    private void HandleInvalidRecoveryBaseline(string reason)
    {
        bool quarantined = RaidCheckpointStore.TryQuarantineAll(
            out string quarantineFolder,
            out string quarantineError);
        recoveryDecisionRequired = !quarantined && RaidCheckpointStore.HasRecoveryArtifacts;
        ShowMainPanelCore();

        if (quarantined)
        {
            Debug.LogWarning(
                $"Raid recovery baseline was invalid and its artifacts were quarantined to " +
                $"'{quarantineFolder}'. Reason: {reason}",
                this);

            ClearCachedRaidRecovery();
            if (TryInitializeOrphanedRaidMarkerView())
            {
                SetStatus(
                    "손상된 복구 캐시는 격리했습니다. 일반 세이브의 원정 진행 표식에 따라 " +
                    "이어하기 없이 원정 실패 정산만 허용합니다.");
                return;
            }

            ShowMainPanelCore();
            SetStatus(
                "원정 복구 기준점이 손상되어 복구 자료를 격리했습니다. " +
                "원정은 이어갈 수 없으며 일반 세이브는 변경하지 않았습니다.");
            return;
        }

        SetStatus(
            "원정 복구 기준점이 손상되었고 파일 격리에도 실패했습니다. " +
            "데이터 보호를 위해 새 게임과 일반 로드를 차단했습니다.");
        Debug.LogError(
            $"Raid recovery baseline was invalid and quarantine failed. " +
            $"Reason: {reason} Quarantine: {quarantineError}",
            this);
    }

    private bool BlockNormalStartForRaidRecovery()
    {
        if (!recoveryDecisionRequired)
        {
            return false;
        }

        ShowCurrentRecoveryDecision();
        SetStatus("중단된 원정의 복구 결정을 완료하기 전에는 새 게임이나 일반 로드를 시작할 수 없습니다.");
        return true;
    }

    private void ShowCurrentRecoveryDecision()
    {
        if (recoveryDecision == RaidRecoveryDecision.SettleOrphaned)
        {
            if (orphanedRaidSettlementBlocked)
            {
                ShowUnrecoverableMarkedSave(
                    "원정 진행 표식은 확인됐지만 실패 정산 상태가 유효하지 않아 작업을 계속할 수 없습니다.");
                return;
            }

            ShowRecoveryDecision(
                "일반 세이브에는 원정 진행 표식이 있지만 유효한 복구 캐시가 없습니다. " +
                "이어하기 없이 원정 실패로 정산해야 합니다.",
                false,
                true);
            return;
        }

        if (cachedRecoveryBaseline == null)
        {
            return;
        }

        if (recoveryDecision == RaidRecoveryDecision.Settle &&
            cachedRecoverySettlementState != null)
        {
            ShowRecoveryDecision(
                "이미 기록된 정확한 원정 정산 상태로 미러 저장과 복구 캐시 정리를 계속합니다.",
                false,
                false);
            return;
        }

        if (cachedRecoveryCheckpoint == null)
        {
            ShowRecoveryDecision(
                "실시간 원정 체크포인트를 복구할 수 없습니다. " +
                "출발 전 기준점으로 원정을 실패 처리하고 기지 상태를 정산할 수 있습니다.",
                false,
                true);
            return;
        }

        if (recoveryDecision == RaidRecoveryDecision.ResumeOrFail)
        {
            ShowRecoveryDecision(
                "비정상 종료된 원정이 있습니다. 이어하거나 원정 실패로 처리할 수 있습니다.",
                true,
                true);
            return;
        }

        ShowRecoveryDecision(
            GetResolvedRecoveryMessage(cachedRecoveryCheckpoint.outcome),
            false,
            false);
    }

    private bool ShowRecoveryDecision(
        string message,
        bool allowResume,
        bool actionStartsFailure)
    {
        if (!HasRecoveryViewReferences())
        {
            ShowMainPanelCore();
            SetStatus(
                "원정 복구 자료가 있지만 복구 확인 UI가 연결되지 않았습니다. " +
                "데이터 보호를 위해 새 게임과 일반 로드를 차단했습니다.");
            Debug.LogError("MainMenuManager raid recovery UI references are incomplete.", this);
            return false;
        }

        recoveryText.text = message ?? string.Empty;
        resumeRaidButton.gameObject.SetActive(allowResume);
        resumeRaidButton.interactable = allowResume;
        failRaidButton.gameObject.SetActive(true);
        failRaidButton.interactable = true;
        Text settlementLabel = failRaidButton.GetComponentInChildren<Text>(true);
        if (settlementLabel != null)
        {
            settlementLabel.text = actionStartsFailure ? "원정 실패 처리" : "정산 계속";
        }
        ShowOnly(recoveryPanel);
        SetStatus(string.Empty);
        return true;
    }

    private void SetRecoveryStatus(string message)
    {
        if (recoveryText != null && recoveryPanel != null && recoveryPanel.activeSelf)
        {
            recoveryText.text = message ?? string.Empty;
        }

        SetStatus(message);
    }

    private void DisableRecoveryActions()
    {
        if (resumeRaidButton != null)
        {
            resumeRaidButton.interactable = false;
        }

        if (failRaidButton != null)
        {
            failRaidButton.interactable = false;
        }
    }

    private bool TryValidateBaseline(RaidRecoveryBaselineData baseline, out string error)
    {
        try
        {
            return RaidCheckpointValidator.TryValidateBaseline(
                baseline,
                itemDatabase,
                furnitureDatabase,
                InventoryUIManager.DefaultInventoryWidth,
                InventoryUIManager.DefaultInventoryHeight,
                out error);
        }
        catch (Exception exception)
        {
            error = $"Baseline validation failed unexpectedly: {exception.Message}";
            return false;
        }
    }

    private bool TryValidateCheckpointForLoad(
        RaidRecoveryBaselineData baseline,
        RaidCheckpointData checkpoint,
        out string error)
    {
        try
        {
            return RaidCheckpointValidator.TryValidateCheckpointForLoad(
                baseline,
                checkpoint,
                itemDatabase,
                furnitureDatabase,
                InventoryUIManager.DefaultInventoryWidth,
                InventoryUIManager.DefaultInventoryHeight,
                out error);
        }
        catch (Exception exception)
        {
            error = $"Checkpoint validation failed unexpectedly: {exception.Message}";
            return false;
        }
    }

    private static RaidCheckpointData SelectNewestCheckpoint(
        RaidCheckpointData primary,
        RaidCheckpointData backup,
        out bool selectedBackup)
    {
        selectedBackup = false;
        if (primary == null)
        {
            selectedBackup = backup != null;
            return backup;
        }

        if (backup != null && backup.sequence > primary.sequence)
        {
            selectedBackup = true;
            return backup;
        }

        return primary;
    }

    private static bool TryCreateRecoveryFailedCheckpoint(
        RaidRecoveryBaselineData baseline,
        RaidCheckpointData source,
        out RaidCheckpointData terminal,
        out string error)
    {
        terminal = null;
        if (baseline == null || source == null || source.phase != RaidCheckpointPhase.Active)
        {
            error = "Active raid recovery data is missing.";
            return false;
        }

        if (source.sequence == long.MaxValue)
        {
            error = "Raid checkpoint sequence cannot advance.";
            return false;
        }

        terminal = new RaidCheckpointData
        {
            gameId = source.gameId,
            formatVersion = source.formatVersion,
            worldStateVersion = source.worldStateVersion,
            raidInstanceId = source.raidInstanceId,
            sequence = source.sequence + 1,
            savedAtUtc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
            phase = RaidCheckpointPhase.Resolved,
            outcome = RaidOutcome.RecoveryFailed,
            raidScene = source.raidScene,
            raidSpawnId = source.raidSpawnId,
            sceneStateId = source.sceneStateId,
            generatorVersion = source.generatorVersion,
            mapSeed = source.mapSeed,
            layoutHash = source.layoutHash,
            playerTransform = source.playerTransform,
            playerCurrentHealth = source.playerCurrentHealth,
            playerMaxHealth = source.playerMaxHealth,
            persistentState = source.persistentState,
            chestRecordCount = source.chestRecordCount,
            chests = source.chests == null
                ? null
                : new List<RaidChestSaveData>(source.chests),
            enemyRecordCount = source.enemyRecordCount,
            enemies = source.enemies == null
                ? null
                : new List<RaidEnemySaveData>(source.enemies)
        };

        if (!RaidCheckpointValidator.TryValidateCheckpointStructure(baseline, terminal, out error))
        {
            terminal = null;
            return false;
        }

        error = null;
        return true;
    }

    private static string GetResolvedRecoveryMessage(RaidOutcome outcome)
    {
        switch (outcome)
        {
            case RaidOutcome.Extracted:
                return "원정 성공 결과 정산이 중단되었습니다. 정산을 계속해 주세요.";
            case RaidOutcome.PlayerDied:
                return "플레이어 사망 결과 정산이 중단되었습니다. 정산을 계속해 주세요.";
            case RaidOutcome.Abandoned:
                return "원정 포기 결과 정산이 중단되었습니다. 정산을 계속해 주세요.";
            case RaidOutcome.RecoveryFailed:
                return "원정 복구 실패 정산이 중단되었습니다. 정산을 계속해 주세요.";
            default:
                return "원정 결과 정산이 중단되었습니다. 정산을 계속해 주세요.";
        }
    }

    private bool TryInitializeOrphanedRaidMarkerView()
    {
        GameSaveManager.ReadSlotOneCandidates(
            out GameSaveData primary,
            out _,
            out GameSaveData backup,
            out _);
        GameSaveData header = primary ?? backup;
        if (header == null || !header.raidInProgress)
        {
            return false;
        }

        if (!TrySelectMarkedOrdinarySaveCandidate(
                header.activeRaidInstanceId,
                primary,
                backup,
                out GameSaveData selected))
        {
            ShowUnrecoverableMarkedSave(
                "일반 세이브에는 원정 진행 표식이 있지만 실패 정산에 사용할 Player/기지 상태가 유효하지 않습니다.");
            return true;
        }

        ShowOrphanedRaidDecision(selected);
        return true;
    }

    private bool TrySelectMarkedOrdinarySaveCandidate(
        string raidInstanceId,
        GameSaveData primary,
        GameSaveData backup,
        out GameSaveData selected)
    {
        bool primaryValid = primary != null && primary.raidInProgress &&
                            string.Equals(
                                primary.activeRaidInstanceId,
                                raidInstanceId,
                                StringComparison.Ordinal) &&
                            TryValidateLoadCandidate(primary, true, out _);
        bool backupValid = backup != null && backup.raidInProgress &&
                           string.Equals(
                               backup.activeRaidInstanceId,
                               raidInstanceId,
                               StringComparison.Ordinal) &&
                           TryValidateLoadCandidate(backup, true, out _);
        selected = primaryValid ? primary : backupValid ? backup : null;
        return selected != null;
    }

    private void ShowUnrecoverableMarkedSave(string message)
    {
        cachedOrphanedRaidSave = null;
        orphanedRaidSettlementBlocked = true;
        cachedRecoveryOutcome = RaidOutcome.RecoveryFailed;
        recoveryDecisionRequired = true;
        recoveryDecision = RaidRecoveryDecision.SettleOrphaned;
        ShowRecoveryDecision(message, false, false);
        if (failRaidButton != null)
        {
            failRaidButton.interactable = false;
        }
        SetStatus("원정 실패 정산 데이터가 호환되지 않아 새 게임과 일반 로드를 차단했습니다.");
    }

    private void ShowOrphanedRaidDecision(GameSaveData selected)
    {
        cachedOrphanedRaidSave = selected;
        orphanedRaidSettlementBlocked = false;
        cachedRecoveryOutcome = RaidOutcome.RecoveryFailed;
        recoveryDecisionRequired = true;
        recoveryDecision = RaidRecoveryDecision.SettleOrphaned;
        ShowRecoveryDecision(
            "일반 세이브에는 원정 진행 표식이 있지만 유효한 복구 캐시가 없습니다. " +
            "상태를 임의로 살리지 않고 원정 실패로만 정산합니다.",
            false,
            true);
    }

    private void QuarantineUnreferencedRecovery(string reason)
    {
        bool quarantined = RaidCheckpointStore.TryQuarantineAll(
            out string quarantineFolder,
            out string quarantineError);
        recoveryDecisionRequired = !quarantined && RaidCheckpointStore.HasRecoveryArtifacts;
        ShowMainPanelCore();

        if (quarantined)
        {
            SetStatus(
                "일반 세이브에 활성 원정 표식이 없어 참조되지 않는 복구 캐시를 격리했습니다.");
            Debug.LogWarning(
                $"Unreferenced raid recovery was quarantined to '{quarantineFolder}'. Reason: {reason}",
                this);
            return;
        }

        SetStatus(
            "일반 세이브에 활성 원정 표식이 없지만 남은 복구 캐시를 격리하지 못했습니다. " +
            "저장 데이터 보호를 위해 시작을 차단했습니다.");
        Debug.LogError(
            $"Unreferenced raid recovery quarantine failed. Reason: {reason} Error: {quarantineError}",
            this);
    }

    private bool TrySelectSettlementJournal(
        RaidRecoveryBaselineData baseline,
        GameSaveData requiredOrdinaryExactState,
        out RaidSettlementJournalData selected,
        out bool selectedBackup,
        out bool exactStateInvalid,
        out string status)
    {
        RaidCheckpointStore.ReadSettlementJournalCandidates(
            out RaidSettlementJournalData primary,
            out string primaryReadError,
            out RaidSettlementJournalData backup,
            out string backupReadError);

        bool primaryStructureValid = RaidCheckpointValidator.TryValidateSettlementJournalStructure(
            baseline,
            primary,
            out string primaryValidationError);
        bool backupStructureValid = RaidCheckpointValidator.TryValidateSettlementJournalStructure(
            baseline,
            backup,
            out string backupValidationError);

        bool primaryClaimsExact = primary != null && primary.settlementState != null &&
                                  string.Equals(
                                      primary.raidInstanceId,
                                      baseline?.raidInstanceId,
                                      StringComparison.Ordinal);
        bool backupClaimsExact = backup != null && backup.settlementState != null &&
                                 string.Equals(
                                     backup.raidInstanceId,
                                     baseline?.raidInstanceId,
                                     StringComparison.Ordinal);
        string primaryStateError = primaryStructureValid
            ? null
            : "Journal structure is invalid.";
        string backupStateError = backupStructureValid
            ? null
            : "Journal structure is invalid.";
        bool primaryValid = primaryStructureValid &&
                            TryValidateSettlementJournalState(
                                primary,
                                requiredOrdinaryExactState,
                                out primaryStateError);
        bool backupValid = backupStructureValid &&
                           TryValidateSettlementJournalState(
                               backup,
                               requiredOrdinaryExactState,
                               out backupStateError);

        selected = null;
        selectedBackup = false;
        exactStateInvalid = false;
        if (primaryValid)
        {
            selected = primary;
        }
        else if (primaryClaimsExact)
        {
            // A readable primary claiming an exact transaction cannot fall back to a
            // marker or older checkpoint. In marker-free cleanup, a backup exact state
            // is safe only because it must also equal the authoritative ordinary save.
            // With an active marker, an invalid primary exact remains blocking.
            if (requiredOrdinaryExactState != null &&
                backupValid && backupClaimsExact)
            {
                selected = backup;
                selectedBackup = true;
            }
            else
            {
                exactStateInvalid = true;
            }
        }
        else if (backupValid)
        {
            selected = backup;
            selectedBackup = true;
        }

        if (selected == null && backupClaimsExact && !backupValid)
        {
            exactStateInvalid = true;
        }
        if (selected == null)
        {
            status = "정산 표식 파일을 읽을 수 없어도 안전상 이어하기는 금지합니다. " +
                     "유효한 최신 체크포인트 또는 출발 전 기준점으로 실패 정산합니다. " +
                     $"Primary: {CombineReadAndValidationError(primaryReadError, primaryValidationError)} " +
                     $"State: {primaryStateError} " +
                     $"Backup: {CombineReadAndValidationError(backupReadError, backupValidationError)} " +
                     $"State: {backupStateError}";
            return false;
        }

        status = selected.settlementState != null
            ? "중단 직전의 정확한 기지 정산 상태를 다시 적용합니다."
            : "원정 실패 표식이 기록되어 최신 유효 체크포인트 또는 출발 전 기준점으로 정산합니다.";
        return true;
    }

    private bool TryValidateSettlementJournalState(
        RaidSettlementJournalData journal,
        GameSaveData requiredOrdinaryExactState,
        out string error)
    {
        if (journal == null)
        {
            error = "Journal is missing.";
            return false;
        }

        if (journal.settlementState == null)
        {
            bool markerAllowed = requiredOrdinaryExactState == null;
            error = markerAllowed ? null : "Marker-only journal cannot finish a marker-free settlement.";
            return markerAllowed;
        }

        if (!TryValidateRecoveryPersistentState(journal.settlementState, out error))
        {
            return false;
        }

        if (requiredOrdinaryExactState != null &&
            !AreCanonicalJsonEquivalent(
                requiredOrdinaryExactState,
                journal.settlementState))
        {
            error = "Exact journal state does not match the authoritative ordinary save.";
            return false;
        }

        error = null;
        return true;
    }

    private bool TryValidateRecoveryPersistentState(GameSaveData saveData, out string error)
    {
        try
        {
            return RaidCheckpointValidator.TryValidatePersistentStateForLoad(
                saveData,
                itemDatabase,
                furnitureDatabase,
                InventoryUIManager.DefaultInventoryWidth,
                InventoryUIManager.DefaultInventoryHeight,
                out error);
        }
        catch (Exception exception)
        {
            error = $"Settlement-state validation failed unexpectedly: {exception.Message}";
            return false;
        }
    }

    private static bool TryWriteRecoveryFailureMarker(
        RaidRecoveryBaselineData baseline,
        out string error)
    {
        var journal = new RaidSettlementJournalData
        {
            gameId = GameSaveData.CurrentGameId,
            formatVersion = RaidSettlementJournalData.CurrentFormatVersion,
            raidInstanceId = baseline.raidInstanceId,
            writtenAtUtc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
            outcome = RaidOutcome.RecoveryFailed,
            settlementState = null
        };

        if (!RaidCheckpointValidator.TryValidateSettlementJournalStructure(
                baseline,
                journal,
                out error))
        {
            return false;
        }

        return RaidCheckpointStore.TryWriteSettlementJournal(journal, out error);
    }

    private bool TrySecureRecoveryFailureDecision(out string error)
    {
        if (cachedRecoveryBaseline == null)
        {
            error = "Recovery baseline is missing.";
            return false;
        }

        if (TryWriteRecoveryFailureMarker(
                cachedRecoveryBaseline,
                out string markerError))
        {
            error = null;
            return true;
        }

        if (RaidCheckpointStore.TryDeleteCheckpointBackup(out string backupError))
        {
            error = null;
            return true;
        }

        error = $"Marker: {markerError} Backup cleanup: {backupError}";
        return false;
    }

    private bool HasRecoveryViewReferences()
    {
        return recoveryPanel != null && recoveryText != null &&
               resumeRaidButton != null && failRaidButton != null;
    }

    private void ClearCachedRaidRecovery()
    {
        cachedRecoveryBaseline = null;
        cachedRecoveryCheckpoint = null;
        cachedRecoverySettlementState = null;
        cachedRecoveryOutcome = RaidOutcome.None;
        cachedOrphanedRaidSave = null;
        orphanedRaidSettlementBlocked = false;
        recoverySettlementDurabilityBlocked = false;
        recoveryDecision = RaidRecoveryDecision.None;
        recoveryDecisionRequired = false;
    }

    private static bool AreCanonicalJsonEquivalent(object left, object right)
    {
        if (left == null || right == null || left.GetType() != right.GetType())
        {
            return false;
        }

        try
        {
            return string.Equals(
                JsonUtility.ToJson(left, false),
                JsonUtility.ToJson(right, false),
                StringComparison.Ordinal);
        }
        catch (Exception)
        {
            return false;
        }
    }
}
