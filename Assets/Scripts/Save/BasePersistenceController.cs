using System;
using FantasySurvival.BaseBuilding;
using FantasySurvival.Inventory;
using FantasySurvival.Raids;
using FantasySurvival.SceneFlow;
using FantasySurvival.Trading;
using UnityEngine;

namespace FantasySurvival.SaveSystem
{
    [DefaultExecutionOrder(1000)]
    [DisallowMultipleComponent]
    public sealed class BasePersistenceController : MonoBehaviour
    {
        private const float StatusDuration = 8f;

        private struct PendingStartAction
        {
            public GameStartMode Mode;
            public int SaveSlotIndex;
            public RaidRecoveryBaselineData RecoveryBaseline;
            public RaidCheckpointData RaidCheckpoint;
            public GameSaveData RecoverySettlementState;
            public RaidSettlementJournalKind RecoverySettlementKind;
            public RaidOutcome RecoveryOutcome;
            public GameSaveData PreparedRecoverySettlementState;
            public GameSaveData OrphanedRaidSave;
        }

        [Header("Scene-authored persistent furniture")]
        [SerializeField] private BaseFurnitureDatabase furnitureDatabase;
        [SerializeField] private BaseFurnitureInstance[] persistentFurniture =
            Array.Empty<BaseFurnitureInstance>();
        [Header("Scene-authored persistent merchants")]
        [SerializeField] private Merchant[] persistentMerchants = Array.Empty<Merchant>();

        private string statusMessage = "F5 or Save to save player and base state.";
        private float statusUntil;
        private bool baseFurnitureBound;
        private bool ordinaryMirrorRepairPending;

        public string CurrentStatusMessage => statusMessage;

        private void Start()
        {
            if (!TryGetInventory(out InventoryUIManager inventory, out string error))
            {
                SetStatus($"Base initialization failed: {error}", true);
                return;
            }

            if (!TryGetBaseOwner(out GameManager owner, out error))
            {
                SetStatus($"Base initialization failed: {error}", true);
                return;
            }

            if (!TryValidateFurnitureDefinitions(out error))
            {
                SetStatus($"Base initialization failed: {error}", true);
                return;
            }

            if (!TryValidateMerchantDefinitions(inventory, out error))
            {
                SetStatus($"Base initialization failed: {error}", true);
                return;
            }

            if (!TryApplyPendingStartRequest(
                    inventory,
                    owner,
                    out bool allowAuthoredFurnitureInitialization,
                    out PendingStartAction pendingStartAction))
            {
                // Do not bind an authored fallback or enable F5 after a requested load failed.
                // This prevents a content mismatch from silently replacing the selected slot.
                return;
            }

            if (!owner.BaseFurnitureState.TryBindAll(
                    persistentFurniture,
                    allowAuthoredFurnitureInitialization,
                    out string bindError))
            {
                SetStatus($"Base furniture binding failed: {bindError}", true);
                return;
            }

            baseFurnitureBound = true;
            PersistentGameplayShell.Instance?.RaidCheckpoint?.NotifyBasePersistenceReady();
            CompleteStartActionAfterBaseBinding(pendingStartAction);

            GameplayEscapeMenuController escapeMenu =
                PersistentGameplayShell.Instance?.EscapeMenu;
            if (escapeMenu != null && !escapeMenu.RegisterBasePersistence(this))
            {
                SetStatus(
                    "Base initialization failed: another base persistence controller is already registered.",
                    true);
            }
        }

        private void OnDisable()
        {
            PersistentGameplayShell.Instance?.EscapeMenu?.UnregisterBasePersistence(this);
        }

        private void Update()
        {
            if (!DirectSceneTravel.IsLoading && !IsInformationWindowOpen() &&
                Input.GetKeyDown(KeyCode.F5))
            {
                SaveActiveSlot();
            }
        }

        private void OnGUI()
        {
            if (DirectSceneTravel.IsLoading || IsInformationWindowOpen())
            {
                return;
            }

            const float width = 300f;
            const float height = 112f;
            Rect panel = new Rect(Screen.width - width - 16f, 16f, width, height);
            GUI.Box(panel, "Save Prototype");

            int activeSlotIndex = PersistentGameplayShell.Instance?.ActiveSaveSlotIndex ??
                                  GameSaveManager.DefaultSlotIndex;
            if (GUI.Button(
                    new Rect(panel.x + 12f, panel.y + 28f, width - 24f, 30f),
                    $"Save Slot {activeSlotIndex}  (F5)"))
            {
                SaveActiveSlot();
            }

            string visibleStatus = Time.unscaledTime <= statusUntil || statusUntil <= 0f
                ? statusMessage
                : $"F5 or Save Slot {activeSlotIndex} to save player and base state.";
            GUI.Label(new Rect(panel.x + 12f, panel.y + 64f, width - 24f, 42f), visibleStatus);
        }

        private static bool IsInformationWindowOpen()
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            return shell != null && shell.InformationWindow != null &&
                   shell.InformationWindow.IsOpen;
        }

        public bool SaveSlotOne()
        {
            return SaveActiveSlot();
        }

        public bool SaveActiveSlot()
        {
            return SaveActiveSlot(
                ordinaryMirrorRepairPending,
                allowReplaceUnresolvedSlot: false,
                setSuccessStatus: true);
        }

        private bool SaveActiveSlot(
            bool mirrorOrdinarySlot,
            bool allowReplaceUnresolvedSlot,
            bool setSuccessStatus)
        {
            if (DirectSceneTravel.IsLoading)
            {
                SetStatus("Save is unavailable during gameplay scene travel.", false);
                return false;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell == null ||
                !GameSaveManager.IsValidSlotIndex(shell.ActiveSaveSlotIndex))
            {
                SetStatus("Save failed: active save-slot ownership is unavailable.", true);
                return false;
            }

            int activeSlotIndex = shell.ActiveSaveSlotIndex;
            if (!TryGetInventory(out InventoryUIManager inventory, out string error) ||
                !TryGetBaseOwner(out GameManager owner, out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (!baseFurnitureBound)
            {
                SetStatus("Save failed: base furniture is not bound to its runtime state.", true);
                return false;
            }

            RaidCheckpointController checkpoint =
                PersistentGameplayShell.Instance?.RaidCheckpoint;
            bool settledTrackedRaidThisSave = false;
            if (checkpoint != null && checkpoint.HasTrackedRaid)
            {
                if (!checkpoint.HasPendingBaseSettlement)
                {
                    SetStatus(
                        "Save is blocked while an unresolved raid recovery is waiting for retry or settlement.",
                        true);
                    return false;
                }

                if (!checkpoint.TryCommitTrackedRaidAtBase(out string settlementError))
                {
                    SetStatus($"Raid settlement save failed: {settlementError}", true);
                    return false;
                }

                // The exact journal transaction is now complete. Continue this same F5
                // operation and capture the current live base state as a normal save as
                // well; the Player may have changed inventory after an earlier commit
                // failure, and reporting success while discarding that change is unsafe.
                settledTrackedRaidThisSave = true;
            }

            if (!allowReplaceUnresolvedSlot && !ordinaryMirrorRepairPending &&
                TryGetActiveOrdinaryRaidMarker(
                    activeSlotIndex,
                    out string activeRaidInstanceId))
            {
                SetStatus(
                    $"Save is blocked because ordinary slot {activeSlotIndex} still declares unresolved raid " +
                    $"'{activeRaidInstanceId}'. Resolve it from the Main Menu.",
                    true);
                return false;
            }

            if (!allowReplaceUnresolvedSlot &&
                RaidCheckpointStore.HasRecoveryArtifactsForSlot(activeSlotIndex))
            {
                SetStatus(
                    $"Save is blocked because unresolved raid recovery files are present " +
                    $"for slot {activeSlotIndex}. Resolve them from the Main Menu.",
                    true);
                return false;
            }

            if (!inventory.CloseAllInventories())
            {
                SetStatus("Save failed: the active inventory drag could not be restored.", true);
                return false;
            }

            if (!InventorySaveCodec.TryCapture(
                    inventory.PlayerState,
                    inventory.ItemDatabase,
                    out PlayerItemStateSaveData inventorySave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (!PlayerCurrencySaveCodec.TryCapture(
                    inventory.PlayerWallet,
                    out PlayerCurrencySaveData currencySave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (!BaseFurnitureSaveCodec.TryCapture(
                    owner.BaseFurnitureState,
                    inventory.ItemDatabase,
                    furnitureDatabase,
                    out BaseSaveData baseSave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (!BaseMerchantSaveCodec.TryCapture(
                    owner.BaseMerchantState,
                    inventory.ItemDatabase,
                    out BaseMerchantStateSaveData merchantSave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (!PlayerProgressSaveCodec.TryCapture(
                    shell?.QuestJournal,
                    shell?.PlayerSessionRecords,
                    out PlayerProgressSaveData progressSave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            GameSaveData saveData = GameSaveManager.CreateSave(
                inventorySave,
                currencySave,
                progressSave,
                baseSave,
                merchantSave);
            bool written = mirrorOrdinarySlot
                ? GameSaveManager.TryWriteSlotMirrored(
                    activeSlotIndex,
                    saveData,
                    inventory.ItemDatabase,
                    furnitureDatabase,
                    inventory.PlayerState.BaseInventoryWidth,
                    inventory.PlayerState.BaseInventoryHeight,
                    out error)
                : GameSaveManager.TryWriteSlot(
                    activeSlotIndex,
                    saveData,
                    inventory.ItemDatabase,
                    furnitureDatabase,
                    inventory.PlayerState.BaseInventoryWidth,
                    inventory.PlayerState.BaseInventoryHeight,
                    out error);
            if (!written)
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            if (mirrorOrdinarySlot)
            {
                ordinaryMirrorRepairPending = false;
            }
            if (setSuccessStatus)
            {
                SetStatus(
                    settledTrackedRaidThisSave
                        ? $"Raid settlement was committed and the current base state was saved " +
                          $"to slot {activeSlotIndex} at " +
                          GameSaveManager.GetDisplayTimestamp(saveData)
                        : $"Saved player and base to slot {activeSlotIndex} at " +
                          GameSaveManager.GetDisplayTimestamp(saveData),
                    false);
            }
            return true;
        }

        private static bool TryGetActiveOrdinaryRaidMarker(
            int slotIndex,
            out string raidInstanceId)
        {
            GameSaveManager.ReadSlotCandidates(
                slotIndex,
                out GameSaveData primary,
                out _,
                out GameSaveData backup,
                out _);
            GameSaveData authoritative = primary ?? backup;
            if (authoritative != null && authoritative.raidInProgress &&
                Guid.TryParse(authoritative.activeRaidInstanceId, out _))
            {
                raidInstanceId = authoritative.activeRaidInstanceId;
                return true;
            }

            raidInstanceId = null;
            return false;
        }

        private bool TryApplyPendingStartRequest(
            InventoryUIManager inventory,
            GameManager owner,
            out bool allowAuthoredFurnitureInitialization,
            out PendingStartAction pendingStartAction)
        {
            allowAuthoredFurnitureInitialization = false;
            pendingStartAction = default;
            if (!GameStartRequest.TryConsume(
                    out GameStartMode mode,
                    out GameSaveData saveData,
                    out GameSaveData fallbackSave,
                    out RaidRecoveryBaselineData recoveryBaseline,
                    out RaidCheckpointData raidCheckpoint,
                    out GameSaveData recoverySettlementState,
                    out RaidSettlementJournalKind recoverySettlementKind,
                    out RaidOutcome recoveryOutcome,
                    out int saveSlotIndex))
            {
                allowAuthoredFurnitureInitialization = owner.BaseFurnitureState.StateCount == 0;
                return true;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            string slotError = null;
            if (shell == null || !shell.TrySelectSaveSlot(saveSlotIndex, out slotError))
            {
                SetStatus(
                    $"Start request could not select save slot {saveSlotIndex}: " +
                    (slotError ?? "persistent gameplay shell is unavailable."),
                    true);
                return false;
            }

            pendingStartAction = new PendingStartAction
            {
                Mode = mode,
                SaveSlotIndex = saveSlotIndex,
                RecoveryBaseline = recoveryBaseline,
                RaidCheckpoint = raidCheckpoint,
                RecoverySettlementState = recoverySettlementState,
                RecoverySettlementKind = recoverySettlementKind,
                RecoveryOutcome = recoveryOutcome,
                OrphanedRaidSave = mode == GameStartMode.SettleOrphanedRaid ? saveData : null
            };

            if (mode == GameStartMode.NewGame)
            {
                bool applied = TryApplyNewGame(inventory, owner);
                allowAuthoredFurnitureInitialization = applied;
                return applied;
            }

            if (mode == GameStartMode.LoadGame && saveData != null)
            {
                return TryApplyLoadGame(
                    inventory,
                    owner,
                    saveData,
                    fallbackSave,
                    out allowAuthoredFurnitureInitialization);
            }

            if (mode == GameStartMode.ResumeRaid &&
                recoveryBaseline != null &&
                raidCheckpoint?.persistentState != null)
            {
                RaidCheckpointController checkpoint =
                    PersistentGameplayShell.Instance?.RaidCheckpoint;
                string preflightError = null;
                if (checkpoint == null ||
                    !checkpoint.TryPreflightRecoveredRaid(
                        recoveryBaseline,
                        raidCheckpoint,
                        out preflightError))
                {
                    SetStatus(
                        $"Raid resume preflight failed before changing player/base state: " +
                        $"{preflightError ?? "raid checkpoint controller is unavailable."}",
                        true);
                    return false;
                }

                if (TryApplyRecoveryPersistentState(
                    inventory,
                    owner,
                    raidCheckpoint.persistentState,
                    out allowAuthoredFurnitureInitialization,
                    out string error))
                {
                    return true;
                }

                SetStatus($"Raid resume failed; current player and base state were kept: {error}", true);
                return false;
            }

            if (mode == GameStartMode.SettleRaidRecovery && recoveryBaseline != null)
            {
                RaidCheckpointController checkpoint =
                    PersistentGameplayShell.Instance?.RaidCheckpoint;
                string preflightError = null;
                if (checkpoint == null ||
                    !checkpoint.TryPrepareMenuRecoverySettlementState(
                        recoveryBaseline,
                        raidCheckpoint,
                        recoveryOutcome,
                        recoverySettlementState,
                        recoverySettlementKind,
                        out GameSaveData preparedSettlementState,
                        out preflightError))
                {
                    SetStatus(
                        $"Raid recovery settlement preflight failed before changing player/base state: " +
                        $"{preflightError ?? "raid checkpoint controller is unavailable."}",
                        true);
                    return false;
                }

                pendingStartAction.PreparedRecoverySettlementState = preparedSettlementState;
                if (TryApplyRecoveryPersistentState(
                    inventory,
                    owner,
                    preparedSettlementState,
                    out allowAuthoredFurnitureInitialization,
                    out string error))
                {
                    return true;
                }

                SetStatus(
                    "Raid recovery settlement failed; current player and base state were kept. " +
                    error,
                    true);
                return false;
            }

            if (mode == GameStartMode.SettleOrphanedRaid &&
                saveData != null && saveData.raidInProgress)
            {
                RaidCheckpointController checkpoint =
                    PersistentGameplayShell.Instance?.RaidCheckpoint;
                string preflightError = null;
                if (checkpoint == null ||
                    !checkpoint.TryPreflightOrphanedRaidSettlement(
                        saveData.activeRaidInstanceId,
                        out GameSaveData authoritativeSettlementState,
                        out preflightError))
                {
                    SetStatus(
                        "Orphaned raid failure preflight failed before changing player/base state: " +
                        (preflightError ?? "raid checkpoint controller is unavailable."),
                        true);
                    return false;
                }

                pendingStartAction.OrphanedRaidSave = authoritativeSettlementState;
                if (TryApplyRecoveryPersistentState(
                    inventory,
                    owner,
                    authoritativeSettlementState,
                    out allowAuthoredFurnitureInitialization,
                    out string error))
                {
                    return true;
                }

                SetStatus(
                    $"Orphaned raid failure settlement could not restore its marked base state: {error}",
                    true);
                return false;
            }

            SetStatus("Start request was invalid.", true);
            return false;
        }

        private bool TryApplyRecoveryPersistentState(
            InventoryUIManager inventory,
            GameManager owner,
            GameSaveData persistentState,
            out bool allowAuthoredFurnitureInitialization,
            out string error)
        {
            allowAuthoredFurnitureInitialization = false;
            if (!TryPrepareLoadGame(
                    inventory,
                    owner,
                    persistentState,
                    out PlayerInventoryState playerCandidate,
                    out BaseFurnitureStateStore baseCandidate,
                    out BaseMerchantStateStore merchantCandidate,
                    out PlayerProgressSaveCodec.RestorePlan progressPlan,
                    out bool preparedAllowsAuthoredInitialization,
                    out error))
            {
                return false;
            }

            if (!TryApplyPreparedLoad(
                    inventory,
                    owner,
                    playerCandidate,
                    baseCandidate,
                    merchantCandidate,
                    progressPlan,
                    out error))
            {
                return false;
            }

            allowAuthoredFurnitureInitialization = preparedAllowsAuthoredInitialization;
            error = null;
            return true;
        }

        private void CompleteStartActionAfterBaseBinding(PendingStartAction pendingStartAction)
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (pendingStartAction.Mode == GameStartMode.NewGame)
            {
                if (!SaveActiveSlot(
                        mirrorOrdinarySlot: true,
                        allowReplaceUnresolvedSlot: true,
                        setSuccessStatus: false))
                {
                    SetStatus(
                        $"New game was initialized, but save slot " +
                        $"{pendingStartAction.SaveSlotIndex} could not be overwritten.",
                        true);
                    return;
                }

                // The clean ordinary state is durable before old interrupted-raid
                // projections are removed. Failure leaves visible recovery artifacts
                // for this slot only and never touches another profile.
                if (!RaidCheckpointStore.TryDeleteAll(
                        pendingStartAction.SaveSlotIndex,
                        out string deleteError))
                {
                    SetStatus(
                        $"New game was saved to slot {pendingStartAction.SaveSlotIndex}, " +
                        $"but that slot's old raid recovery could not be removed: {deleteError}",
                        true);
                    return;
                }

                ordinaryMirrorRepairPending = false;
                SetStatus(
                    $"New game started and was saved to slot " +
                    $"{pendingStartAction.SaveSlotIndex}.",
                    false);
                return;
            }

            if (pendingStartAction.Mode == GameStartMode.ResumeRaid)
            {
                string error = null;
                if (shell?.RaidCheckpoint == null ||
                    !shell.RaidCheckpoint.TryBeginRecoveredRaid(
                        pendingStartAction.RecoveryBaseline,
                        pendingStartAction.RaidCheckpoint,
                        out error))
                {
                    SetStatus(
                        $"Raid resume could not begin after base restoration: " +
                        $"{error ?? "raid checkpoint controller is unavailable."}",
                        true);
                    return;
                }

                SetStatus("Recovered persistent state; loading the interrupted raid.", false);
                return;
            }

            if (pendingStartAction.Mode == GameStartMode.SettleRaidRecovery)
            {
                if (shell?.PlayerStats == null || shell.RaidCheckpoint == null)
                {
                    SetStatus("Raid recovery settlement failed: persistent Player services are unavailable.", true);
                    return;
                }

                shell.PlayerStats.ResetHealth();
                if (!shell.RaidCheckpoint.TryCompleteMenuRecoverySettlementAtBase(
                        pendingStartAction.RecoveryBaseline,
                        pendingStartAction.RaidCheckpoint,
                        pendingStartAction.RecoveryOutcome,
                        pendingStartAction.RecoverySettlementState,
                        pendingStartAction.RecoverySettlementKind,
                        pendingStartAction.PreparedRecoverySettlementState,
                        out string error))
                {
                    SetStatus($"Raid recovery settlement failed: {error}", true);
                    return;
                }

                SetStatus("Interrupted raid recovery was settled at the base.", false);
                return;
            }

            if (pendingStartAction.Mode == GameStartMode.SettleOrphanedRaid)
            {
                if (shell?.PlayerStats == null)
                {
                    SetStatus("Orphaned raid failure settlement failed: Player services are unavailable.", true);
                    return;
                }

                shell.PlayerStats.ResetHealth();
                ordinaryMirrorRepairPending = true;
                if (!SaveActiveSlot(
                        mirrorOrdinarySlot: true,
                        allowReplaceUnresolvedSlot: false,
                        setSuccessStatus: false))
                {
                    SetStatus(
                        "Orphaned raid was failed, but its clean ordinary save mirror could not be completed. Retry F5.",
                        true);
                    return;
                }

                SetStatus(
                    "The ordinary save showed an active raid without recovery cache. The raid was failed and settled at the base.",
                    false);
                return;
            }

        }

        private bool TryApplyNewGame(InventoryUIManager inventory, GameManager owner)
        {
            if (!inventory.TryCreateStartingPlayerState(out PlayerInventoryState playerCandidate, out string error))
            {
                SetStatus($"New game failed: {error}", true);
                return false;
            }

            var baseCandidate = new BaseFurnitureStateStore();
            var merchantCandidate = new BaseMerchantStateStore();
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (!baseCandidate.TryValidateBindings(persistentFurniture, true, out error) ||
                !merchantCandidate.TryValidateBindings(persistentMerchants, true, out error) ||
                !TryMaterializeMerchantStates(merchantCandidate, out error) ||
                !PlayerProgressSaveCodec.TryPrepareRestore(
                    PlayerProgressSaveCodec.CreateEmptySaveData(true),
                    shell?.QuestJournal,
                    shell?.PlayerSessionRecords,
                    out PlayerProgressSaveCodec.RestorePlan progressPlan,
                    out error) ||
                !owner.CanReplaceBaseFurnitureState(out error))
            {
                SetStatus($"New game failed: {error}", true);
                return false;
            }

            if (!TryApplyPreparedLoad(
                    inventory,
                    owner,
                    playerCandidate,
                    baseCandidate,
                    merchantCandidate,
                    progressPlan,
                    out error))
            {
                SetStatus($"New game failed: {error}", true);
                return false;
            }

            SetStatus("New game state prepared at the base.", false);
            return true;
        }

        private bool TryApplyLoadGame(
            InventoryUIManager inventory,
            GameManager owner,
            GameSaveData saveData,
            GameSaveData fallbackSave,
            out bool allowAuthoredFurnitureInitialization)
        {
            allowAuthoredFurnitureInitialization = false;
            if (TryPrepareLoadGame(
                    inventory,
                    owner,
                    saveData,
                    out PlayerInventoryState playerCandidate,
                    out BaseFurnitureStateStore baseCandidate,
                    out BaseMerchantStateStore merchantCandidate,
                    out PlayerProgressSaveCodec.RestorePlan progressPlan,
                    out bool primaryAllowsAuthoredInitialization,
                    out string primaryError))
            {
                if (!TryApplyPreparedLoad(
                        inventory,
                        owner,
                        playerCandidate,
                        baseCandidate,
                        merchantCandidate,
                        progressPlan,
                        out string applyError))
                {
                    SetStatus($"Load failed; current player and base state were kept: {applyError}", true);
                    return false;
                }

                allowAuthoredFurnitureInitialization = primaryAllowsAuthoredInitialization;
                SetStatus(
                    $"Loaded player and base from slot " +
                    $"{PersistentGameplayShell.Instance?.ActiveSaveSlotIndex ?? GameSaveManager.DefaultSlotIndex} " +
                    $"at {GameSaveManager.GetDisplayTimestamp(saveData)}",
                    false);
                return true;
            }

            if (fallbackSave == null)
            {
                SetStatus(
                    $"Load failed; current player and base state were kept: {primaryError}",
                    true);
                return false;
            }

            if (!TryPrepareLoadGame(
                    inventory,
                    owner,
                    fallbackSave,
                    out playerCandidate,
                    out baseCandidate,
                    out merchantCandidate,
                    out progressPlan,
                    out bool fallbackAllowsAuthoredInitialization,
                    out string fallbackError))
            {
                SetStatus(
                    $"Load failed; current player and base state were kept. " +
                    $"Primary: {primaryError} Backup: {fallbackError}",
                    true);
                return false;
            }

            if (!TryApplyPreparedLoad(
                    inventory,
                    owner,
                    playerCandidate,
                    baseCandidate,
                    merchantCandidate,
                    progressPlan,
                    out string fallbackApplyError))
            {
                SetStatus(
                    $"Backup load failed; current player and base state were kept: {fallbackApplyError}",
                    true);
                return false;
            }

            allowAuthoredFurnitureInitialization = fallbackAllowsAuthoredInitialization;
            SetStatus(
                $"Primary save was incompatible with the current base layout; loaded validated backup at " +
                $"{GameSaveManager.GetDisplayTimestamp(fallbackSave)}",
                false);
            return true;
        }

        private bool TryPrepareLoadGame(
            InventoryUIManager inventory,
            GameManager owner,
            GameSaveData saveData,
            out PlayerInventoryState playerCandidate,
            out BaseFurnitureStateStore baseCandidate,
            out BaseMerchantStateStore merchantCandidate,
            out PlayerProgressSaveCodec.RestorePlan progressPlan,
            out bool allowAuthoredFurnitureInitialization,
            out string error)
        {
            playerCandidate = null;
            baseCandidate = null;
            merchantCandidate = null;
            progressPlan = null;
            allowAuthoredFurnitureInitialization =
                saveData?.baseState != null &&
                saveData.baseState.allowAuthoredFurnitureInitialization;

            try
            {
                PlayerInventoryState currentState = inventory.PlayerState;
                if (saveData == null || currentState?.Inventory == null)
                {
                    error = saveData == null
                        ? "save candidate is missing."
                        : "current inventory configuration is missing.";
                    return false;
                }

                if (!InventorySaveCodec.TryRestore(
                        saveData.playerItems,
                        inventory.ItemDatabase,
                        currentState.BaseInventoryWidth,
                        currentState.BaseInventoryHeight,
                        out playerCandidate,
                        out error))
                {
                    return false;
                }

                if (!PlayerCurrencySaveCodec.TryRestore(
                        saveData.playerCurrency,
                        out PlayerWallet walletCandidate,
                        out error))
                {
                    return false;
                }

                playerCandidate = new PlayerInventoryState(
                    playerCandidate.Inventory,
                    playerCandidate.Equipment,
                    walletCandidate,
                    playerCandidate.BaseInventoryWidth,
                    playerCandidate.BaseInventoryHeight);

                if (!BaseFurnitureSaveCodec.TryRestore(
                        saveData.baseState,
                        inventory.ItemDatabase,
                        furnitureDatabase,
                        out baseCandidate,
                        out error))
                {
                    return false;
                }

                if (!BaseMerchantSaveCodec.TryRestore(
                        saveData.baseMerchantState,
                        inventory.ItemDatabase,
                        out merchantCandidate,
                        out error))
                {
                    return false;
                }

                bool allowAuthoredMerchantInitialization =
                    saveData.baseMerchantState != null &&
                    saveData.baseMerchantState.allowAuthoredMerchantInitialization;
                if (!merchantCandidate.TryValidateBindings(
                        persistentMerchants,
                        allowAuthoredMerchantInitialization,
                        out error))
                {
                    return false;
                }

                if (!TryMaterializeMerchantStates(merchantCandidate, out error))
                {
                    return false;
                }

                if (!baseCandidate.TryValidateBindings(
                        persistentFurniture,
                        allowAuthoredFurnitureInitialization,
                        out error))
                {
                    return false;
                }

                PersistentGameplayShell shell = PersistentGameplayShell.Instance;
                if (!PlayerProgressSaveCodec.TryPrepareRestore(
                        saveData.playerProgress,
                        shell?.QuestJournal,
                        shell?.PlayerSessionRecords,
                        out progressPlan,
                        out error))
                {
                    return false;
                }

                return owner.CanReplaceBaseFurnitureState(out error);
            }
            catch (Exception exception)
            {
                playerCandidate = null;
                baseCandidate = null;
                merchantCandidate = null;
                progressPlan = null;
                error = $"save preparation failed unexpectedly: {exception.Message}";
                return false;
            }
        }

        private bool TryApplyPreparedLoad(
            InventoryUIManager inventory,
            GameManager owner,
            PlayerInventoryState playerCandidate,
            BaseFurnitureStateStore baseCandidate,
            BaseMerchantStateStore merchantCandidate,
            PlayerProgressSaveCodec.RestorePlan progressPlan,
            out string error)
        {
            BaseFurnitureStateStore previousBase = owner.BaseFurnitureState;
            BaseMerchantStateStore previousMerchants = owner.BaseMerchantState;
            if (!owner.TryReplaceBaseFurnitureState(baseCandidate, out error))
            {
                return false;
            }

            if (!owner.TryReplaceBaseMerchantState(merchantCandidate, out error))
            {
                if (!owner.TryReplaceBaseFurnitureState(previousBase, out string rollbackError))
                {
                    error += $" Base rollback also failed: {rollbackError}";
                }
                return false;
            }

            // Inventory observers are notified only once both authoritative states are current.
            if (!inventory.TryReplacePlayerState(playerCandidate, out error))
            {
                if (!owner.TryReplaceBaseMerchantState(previousMerchants, out string merchantRollbackError))
                {
                    error += $" Merchant rollback also failed: {merchantRollbackError}";
                }
                if (!owner.TryReplaceBaseFurnitureState(previousBase, out string rollbackError))
                {
                    error += $" Base rollback also failed: {rollbackError}";
                }

                return false;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            PlayerProgressSaveCodec.ApplyPreparedRestore(
                shell.QuestJournal,
                shell.PlayerSessionRecords,
                progressPlan);
            error = null;
            return true;
        }

        private bool TryValidateFurnitureDefinitions(out string error)
        {
            if (furnitureDatabase == null)
            {
                error = "base furniture database is missing.";
                return false;
            }

            if (!furnitureDatabase.TryValidate(out error))
            {
                return false;
            }

            if (persistentFurniture == null)
            {
                error = "persistent furniture list is missing.";
                return false;
            }

            foreach (BaseFurnitureInstance instance in persistentFurniture)
            {
                if (instance == null)
                {
                    error = "persistent furniture list contains a missing instance.";
                    return false;
                }

                if (!furnitureDatabase.TryGet(
                        instance.DefinitionKey,
                        out BaseFurnitureDefinition registered) ||
                    registered != instance.Definition)
                {
                    error = $"furniture '{instance.name}' does not reference its registered definition asset.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private bool TryValidateMerchantDefinitions(
            InventoryUIManager inventory,
            out string error)
        {
            if (inventory?.ItemDatabase == null || persistentMerchants == null)
            {
                error = "Player ItemDatabase or persistent merchant list is missing.";
                return false;
            }

            var seenIds = new System.Collections.Generic.HashSet<string>(StringComparer.Ordinal);
            foreach (Merchant merchant in persistentMerchants)
            {
                if (merchant == null)
                {
                    error = "persistent merchant list contains a missing instance.";
                    return false;
                }

                if (!merchant.TryValidateAuthoring(out error))
                {
                    error = $"[{merchant.name}] {error}";
                    return false;
                }

                if (merchant.ItemDatabase != inventory.ItemDatabase)
                {
                    error = $"merchant '{merchant.name}' must use the Player inventory's authoritative ItemDatabase asset.";
                    return false;
                }

                if (!seenIds.Add(merchant.MerchantId))
                {
                    error = $"persistent merchant ID '{merchant.MerchantId}' is duplicated.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private bool TryMaterializeMerchantStates(
            BaseMerchantStateStore store,
            out string error)
        {
            if (store == null || persistentMerchants == null)
            {
                error = "merchant state store or authored merchant list is missing.";
                return false;
            }

            foreach (Merchant merchant in persistentMerchants)
            {
                if (merchant == null)
                {
                    error = "authored merchant list contains a missing instance.";
                    return false;
                }

                if (!merchant.TryMaterializeIn(store, out _, out error))
                {
                    error = $"[{merchant.name}] {error}";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private static bool TryGetInventory(out InventoryUIManager inventory, out string error)
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            inventory = shell != null ? shell.InventoryUI : null;
            if (inventory == null || !inventory.isActiveAndEnabled)
            {
                error = "persistent player inventory is unavailable.";
                return false;
            }

            error = null;
            return true;
        }

        private static bool TryGetBaseOwner(out GameManager owner, out string error)
        {
            owner = GameManager.Instance;
            if (owner == null || !owner.isActiveAndEnabled)
            {
                error = "persistent GameManager base-state owner is unavailable.";
                return false;
            }

            error = null;
            return true;
        }

        private void SetStatus(string message, bool isError)
        {
            statusMessage = message;
            statusUntil = Time.unscaledTime + StatusDuration;

            if (isError)
            {
                Debug.LogError(message, this);
            }
            else
            {
                Debug.Log(message, this);
            }
        }
    }
}
