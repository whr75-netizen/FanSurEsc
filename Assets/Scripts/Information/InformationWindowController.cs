using System;
using System.Collections.Generic;
using System.Text;
using FantasySurvival.Inventory;
using FantasySurvival.Quests;
using FantasySurvival.Raids;
using FantasySurvival.SceneFlow;
using FantasySurvival.Trading;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.Information
{
    public enum InformationSection
    {
        Character,
        Records,
        Encyclopedia,
        Quests,
        Upgrades
    }

    /// <summary>
    /// Owns the U-key information overlay and presents read-only projections of
    /// existing runtime authorities. It owns no character, quest, item, or upgrade state.
    /// </summary>
    [DefaultExecutionOrder(-8000)]
    [DisallowMultipleComponent]
    public sealed class InformationWindowController : MonoBehaviour
    {
        [Header("Owners")]
        [SerializeField] private PersistentGameplayShell shell;
        [SerializeField] private PlayerWeaponController weaponController;
        [SerializeField] private EnemyDefinition[] enemyDefinitions = Array.Empty<EnemyDefinition>();

        [Header("Input")]
        [SerializeField] private KeyCode toggleKey = KeyCode.U;

        [Header("View")]
        [SerializeField] private GameObject informationCanvas;
        [SerializeField] private Text sectionTitleText;
        [SerializeField] private Text contentText;
        [SerializeField] private Button characterTabButton;
        [SerializeField] private Button recordsTabButton;
        [SerializeField] private Button encyclopediaTabButton;
        [SerializeField] private Button questsTabButton;
        [SerializeField] private Button upgradesTabButton;
        [SerializeField] private Button closeButton;

        private PlayerInventoryState observedPlayerState;
        private PlayerWallet observedWallet;
        private EquipmentLoadoutData observedEquipment;
        private InformationSection currentSection = InformationSection.Character;
        private bool isOpen;
        private bool ownsInputLock;
        private bool movementWasEnabled;
        private bool inventoryInputWasBlocked;
        private bool interactionWasBlocked;

        public bool IsConfigured =>
            shell != null && shell.InventoryUI != null && shell.PlayerMovement != null &&
            shell.PlayerInteractor != null && shell.PlayerStats != null &&
            shell.RaidSession != null && shell.RaidCheckpoint != null &&
            shell.QuestJournal != null && shell.PlayerSessionRecords != null &&
            weaponController != null && informationCanvas != null &&
            sectionTitleText != null && contentText != null &&
            characterTabButton != null && recordsTabButton != null &&
            encyclopediaTabButton != null && questsTabButton != null &&
            upgradesTabButton != null && closeButton != null;
        public bool IsOpen => isOpen;
        public InformationSection CurrentSection => currentSection;
        public KeyCode ToggleKey => toggleKey;

        private void Awake()
        {
            if (!IsConfigured)
            {
                Debug.LogError($"{nameof(InformationWindowController)} has missing required references.", this);
                if (informationCanvas != null)
                {
                    informationCanvas.SetActive(false);
                }
                enabled = false;
                return;
            }

            characterTabButton.onClick.AddListener(ShowCharacter);
            recordsTabButton.onClick.AddListener(ShowRecords);
            encyclopediaTabButton.onClick.AddListener(ShowEncyclopedia);
            questsTabButton.onClick.AddListener(ShowQuests);
            upgradesTabButton.onClick.AddListener(ShowUpgrades);
            closeButton.onClick.AddListener(HandleCloseRequested);
            informationCanvas.SetActive(false);
        }

        private void OnEnable()
        {
            if (!IsConfigured)
            {
                return;
            }

            shell.PlayerStats.HealthChanged += HandleHealthChanged;
            shell.RaidSession.StateChanged += RefreshIfOpen;
            shell.QuestJournal.Changed += RefreshIfOpen;
            shell.PlayerSessionRecords.Changed += RefreshIfOpen;
            shell.InventoryUI.PlayerStateChanged += HandlePlayerStateChanged;
            weaponController.WeaponStateChanged += RefreshIfOpen;
            BindPlayerState(shell.InventoryUI.PlayerState);
        }

        private void OnDisable()
        {
            CloseInternal();

            if (shell != null)
            {
                if (shell.PlayerStats != null)
                {
                    shell.PlayerStats.HealthChanged -= HandleHealthChanged;
                }
                if (shell.RaidSession != null)
                {
                    shell.RaidSession.StateChanged -= RefreshIfOpen;
                }
                if (shell.QuestJournal != null)
                {
                    shell.QuestJournal.Changed -= RefreshIfOpen;
                }
                if (shell.PlayerSessionRecords != null)
                {
                    shell.PlayerSessionRecords.Changed -= RefreshIfOpen;
                }
                if (shell.InventoryUI != null)
                {
                    shell.InventoryUI.PlayerStateChanged -= HandlePlayerStateChanged;
                }
            }
            if (weaponController != null)
            {
                weaponController.WeaponStateChanged -= RefreshIfOpen;
            }

            BindPlayerState(null);
        }

        private void OnDestroy()
        {
            if (characterTabButton != null)
            {
                characterTabButton.onClick.RemoveListener(ShowCharacter);
            }
            if (recordsTabButton != null)
            {
                recordsTabButton.onClick.RemoveListener(ShowRecords);
            }
            if (encyclopediaTabButton != null)
            {
                encyclopediaTabButton.onClick.RemoveListener(ShowEncyclopedia);
            }
            if (questsTabButton != null)
            {
                questsTabButton.onClick.RemoveListener(ShowQuests);
            }
            if (upgradesTabButton != null)
            {
                upgradesTabButton.onClick.RemoveListener(ShowUpgrades);
            }
            if (closeButton != null)
            {
                closeButton.onClick.RemoveListener(HandleCloseRequested);
            }
        }

        private void Update()
        {
            if (Input.GetKeyDown(toggleKey))
            {
                if (isOpen)
                {
                    TryClose();
                }
                else
                {
                    TryOpen();
                }
            }
        }

        public bool TryOpen()
        {
            if (isOpen)
            {
                return true;
            }

            if (!isActiveAndEnabled || !IsConfigured || !CanOpenInCurrentContext())
            {
                return false;
            }

            GameplayEscapeMenuController escapeMenu = shell.EscapeMenu;
            if (DirectSceneTravel.IsLoading || GameplaySessionExit.IsExiting ||
                shell.IsTravelPrepared || shell.RaidCheckpoint.IsSettlementInputLocked ||
                escapeMenu == null || escapeMenu.IsOpen || escapeMenu.IsMapSelectionVisible ||
                shell.PlayerInteractor.InteractionBlocked)
            {
                return false;
            }

            // Existing overlays must return their locks before this window snapshots
            // the exact state it will later restore.
            shell.QuestPanel?.TryClose();
            if (!shell.InventoryUI.CloseAllInventories())
            {
                Debug.LogWarning(
                    "Information window could not open because the active inventory drag could not be restored.",
                    this);
                return false;
            }

            if (shell.InventoryUI.InputBlocked || shell.PlayerInteractor.InteractionBlocked)
            {
                return false;
            }

            movementWasEnabled = shell.PlayerMovement.enabled;
            inventoryInputWasBlocked = shell.InventoryUI.InputBlocked;
            interactionWasBlocked = shell.PlayerInteractor.InteractionBlocked;
            ownsInputLock = true;

            shell.PlayerEventSystem?.SetSelectedGameObject(null);
            shell.PlayerMovement.enabled = false;
            shell.InventoryUI.SetInputBlocked(true);
            shell.PlayerInteractor.SetInteractionBlocked(true);

            isOpen = true;
            informationCanvas.SetActive(true);
            if (!RefreshViewSafely())
            {
                CloseInternal();
                return false;
            }
            Select(closeButton);
            return true;
        }

        public bool TryClose()
        {
            CloseInternal();
            return true;
        }

        public void ShowSection(InformationSection section)
        {
            currentSection = section;
            RefreshViewSafely();
        }

        private bool CanOpenInCurrentContext()
        {
            RaidSession raidSession = shell.RaidSession;
            return (raidSession.CurrentSceneKind == GameplaySceneKind.Base &&
                    raidSession.State == RaidSessionState.Inactive) ||
                   (raidSession.CurrentSceneKind == GameplaySceneKind.Raid &&
                    raidSession.State == RaidSessionState.Active);
        }

        private void CloseInternal()
        {
            if (informationCanvas != null)
            {
                informationCanvas.SetActive(false);
            }
            isOpen = false;

            if (!ownsInputLock)
            {
                return;
            }

            shell?.PlayerEventSystem?.SetSelectedGameObject(null);
            if (shell?.PlayerMovement != null)
            {
                shell.PlayerMovement.enabled = movementWasEnabled;
            }
            if (shell?.InventoryUI != null)
            {
                shell.InventoryUI.SetInputBlocked(inventoryInputWasBlocked);
            }
            if (shell?.PlayerInteractor != null)
            {
                shell.PlayerInteractor.SetInteractionBlocked(interactionWasBlocked);
            }

            ownsInputLock = false;
            movementWasEnabled = false;
            inventoryInputWasBlocked = false;
            interactionWasBlocked = false;
        }

        private void ShowCharacter()
        {
            ShowSection(InformationSection.Character);
        }

        private void ShowRecords()
        {
            ShowSection(InformationSection.Records);
        }

        private void ShowEncyclopedia()
        {
            ShowSection(InformationSection.Encyclopedia);
        }

        private void ShowQuests()
        {
            ShowSection(InformationSection.Quests);
        }

        private void ShowUpgrades()
        {
            ShowSection(InformationSection.Upgrades);
        }

        private void HandleCloseRequested()
        {
            TryClose();
        }

        private void HandleHealthChanged(float current, float maximum)
        {
            RefreshIfOpen();
        }

        private void HandlePlayerStateChanged(PlayerInventoryState state)
        {
            BindPlayerState(state);
            RefreshIfOpen();
        }

        private void BindPlayerState(PlayerInventoryState state)
        {
            if (ReferenceEquals(observedPlayerState, state))
            {
                return;
            }

            if (observedWallet != null)
            {
                observedWallet.Changed -= RefreshIfOpen;
            }
            if (observedEquipment != null)
            {
                observedEquipment.Changed -= RefreshIfOpen;
            }

            observedPlayerState = state;
            observedWallet = state?.Wallet;
            observedEquipment = state?.Equipment;

            if (observedWallet != null)
            {
                observedWallet.Changed += RefreshIfOpen;
            }
            if (observedEquipment != null)
            {
                observedEquipment.Changed += RefreshIfOpen;
            }
        }

        private void RefreshIfOpen()
        {
            if (isOpen)
            {
                RefreshViewSafely();
            }
        }

        private bool RefreshViewSafely()
        {
            try
            {
                RefreshView();
                return true;
            }
            catch (Exception exception)
            {
                // This component only projects authority-owned state. A presentation
                // failure must never break the health, inventory, quest, or raid mutation
                // that raised the notification.
                Debug.LogException(exception, this);
                return false;
            }
        }

        private void RefreshView()
        {
            if (!IsConfigured)
            {
                return;
            }

            characterTabButton.interactable = currentSection != InformationSection.Character;
            recordsTabButton.interactable = currentSection != InformationSection.Records;
            encyclopediaTabButton.interactable = currentSection != InformationSection.Encyclopedia;
            questsTabButton.interactable = currentSection != InformationSection.Quests;
            upgradesTabButton.interactable = currentSection != InformationSection.Upgrades;

            var builder = new StringBuilder(1024);
            switch (currentSection)
            {
                case InformationSection.Character:
                    sectionTitleText.text = "캐릭터";
                    BuildCharacterContent(builder);
                    break;
                case InformationSection.Records:
                    sectionTitleText.text = "기록";
                    BuildRecordsContent(builder);
                    break;
                case InformationSection.Encyclopedia:
                    sectionTitleText.text = "사전";
                    BuildEncyclopediaContent(builder);
                    break;
                case InformationSection.Quests:
                    sectionTitleText.text = "의뢰";
                    BuildQuestContent(builder);
                    break;
                case InformationSection.Upgrades:
                    sectionTitleText.text = "업그레이드";
                    BuildUpgradeContent(builder);
                    break;
            }

            contentText.text = builder.ToString();
        }

        private void BuildCharacterContent(StringBuilder builder)
        {
            PlayerStats stats = shell.PlayerStats;
            PlayerMovement movement = shell.PlayerMovement;
            RaidSession raid = shell.RaidSession;
            PlayerInventoryState state = shell.InventoryUI.PlayerState;
            PlayerWallet wallet = state?.Wallet;

            builder.AppendLine($"현재 위치: {GetSceneLabel(raid.CurrentSceneKind)}");
            builder.AppendLine($"원정 상태: {GetRaidStateLabel(raid.State)}");
            builder.AppendLine();
            builder.AppendLine($"체력: {stats.CurrentHealth:0.#} / {stats.MaxHealth:0.#}");
            builder.AppendLine($"걷기 속도: {movement.speed:0.##}");
            builder.AppendLine($"달리기 속도: {movement.RunSpeed:0.##}");
            builder.AppendLine();
            builder.AppendLine($"금: {(wallet?.Gold ?? 0):N0}");
            builder.AppendLine($"은: {(wallet?.Silver ?? 0):N0}");
            builder.AppendLine($"인벤토리 최상위 아이템: {CountInventoryItems(state?.Inventory)}개");
            builder.AppendLine($"장착 장비: {CountEquippedItems(state?.Equipment)}개");

            InventoryItemData activeWeapon = weaponController.ActiveWeapon;
            if (activeWeapon?.Definition != null)
            {
                ItemDefinition definition = activeWeapon.Definition;
                builder.AppendLine();
                builder.AppendLine($"활성 무기 {weaponController.ActiveWeaponNumber}: {definition.DisplayName}");
                builder.AppendLine(
                    $"시험 공격력 {definition.WeaponDamage:0.#} | 사거리 {definition.WeaponRange:0.#} | RPM {definition.RoundsPerMinute:0.#}");
            }
            else
            {
                builder.AppendLine();
                builder.AppendLine($"활성 무기 {weaponController.ActiveWeaponNumber}: 맨손");
            }
        }

        private void BuildRecordsContent(StringBuilder builder)
        {
            PlayerSessionRecords records = shell.PlayerSessionRecords;
            builder.AppendLine("이번 실행 기록 (세이브되지 않음)");
            builder.AppendLine();
            builder.AppendLine($"플레이어가 처치한 적: {records.EnemyKills}");
            builder.AppendLine($"정산이 완료된 원정: {records.SettledRaids}");
            builder.AppendLine($"  생환: {records.SuccessfulExtractions}");
            builder.AppendLine($"  사망: {records.PlayerDeaths}");
            builder.AppendLine($"  포기: {records.Abandonments}");
            builder.AppendLine($"  복구 실패: {records.RecoveryFailures}");
            builder.AppendLine($"완료 보고한 의뢰: {records.CompletedQuests}");
            builder.AppendLine();
            builder.AppendLine("영구 통계와 세이브 규칙은 아직 확정되지 않았습니다.");
        }

        private void BuildEncyclopediaContent(StringBuilder builder)
        {
            builder.AppendLine("발견/해금 규칙 미구현 - 현재 등록된 시험 정의 전체 표시");
            builder.AppendLine();
            builder.AppendLine("[아이템]");
            ItemDatabase database = shell.InventoryUI.ItemDatabase;
            if (database?.Items == null || database.Items.Count == 0)
            {
                builder.AppendLine("등록된 아이템 정의가 없습니다.");
            }
            else
            {
                foreach (ItemDefinition definition in database.Items)
                {
                    if (definition == null)
                    {
                        continue;
                    }

                    string category = definition.IsContainer
                        ? "컨테이너"
                        : definition.IsWeapon ? "무기" : definition.IsEquippable ? "장비" : "기타";
                    builder.AppendLine(
                        $"#{definition.Id} {definition.DisplayName} | {category} | {definition.Width}x{definition.Height}");
                    if (!string.IsNullOrWhiteSpace(definition.Description))
                    {
                        builder.AppendLine($"  {CompactLine(definition.Description, 64)}");
                    }
                }
            }

            builder.AppendLine();
            builder.AppendLine("[적 시험 정의]");
            bool foundEnemy = false;
            if (enemyDefinitions != null)
            {
                foreach (EnemyDefinition definition in enemyDefinitions)
                {
                    if (definition == null)
                    {
                        continue;
                    }

                    foundEnemy = true;
                    EnemyAISettings ai = definition.AI;
                    builder.AppendLine(ai != null
                        ? $"{definition.name} | 체력 {definition.MaxHealth:0.#} | {ai.CombatArchetype} | 전투속도 {ai.CombatSpeed:0.##}"
                        : $"{definition.name} | 체력 {definition.MaxHealth:0.#} | AI 설정 없음");
                }
            }
            if (!foundEnemy)
            {
                builder.AppendLine("등록된 적 시험 정의가 없습니다.");
            }
            builder.AppendLine("※ 적의 정식 ID·표시명·발견 상태는 아직 없습니다.");
        }

        private void BuildQuestContent(StringBuilder builder)
        {
            QuestJournal journal = shell.QuestJournal;
            QuestDefinition definition = journal.Definition;
            if (definition == null)
            {
                builder.AppendLine("등록된 의뢰가 없습니다.");
                return;
            }

            builder.AppendLine(definition.DisplayName);
            builder.AppendLine(CompactLine(definition.Description, 120));
            builder.AppendLine();
            builder.AppendLine($"상태: {GetQuestStatusLabel(journal.Status)}");
            builder.AppendLine($"적 처치: {journal.EnemyKills} / {journal.RequiredEnemyKills}");
            builder.AppendLine(
                $"생환 필요: {(definition.RequiresSuccessfulExtraction ? "예" : "아니요")}");
            builder.AppendLine("시험 보상: 없음");
            builder.AppendLine("저장 범위: 이번 실행만");
        }

        private static void BuildUpgradeContent(StringBuilder builder)
        {
            builder.AppendLine("현재 등록된 업그레이드가 없습니다.");
            builder.AppendLine();
            builder.AppendLine("기지/캐릭터 업그레이드의 정의, 비용, 효과와 저장 규칙은 미정입니다.");
            builder.AppendLine("규칙이 확정되면 이 탭은 해당 권위 데이터를 읽어 표시합니다.");
        }

        private static int CountInventoryItems(StandardStashViewData inventory)
        {
            if (inventory?.CellData == null)
            {
                return 0;
            }

            var uniqueItems = new HashSet<InventoryItemData>();
            foreach (object cell in inventory.CellData)
            {
                if (cell is InventoryItemData item)
                {
                    uniqueItems.Add(item);
                }
            }
            return uniqueItems.Count;
        }

        private static int CountEquippedItems(EquipmentLoadoutData equipment)
        {
            if (equipment == null)
            {
                return 0;
            }

            int count = 0;
            foreach (EquipmentSlotId slot in EquipmentSlotCatalog.OrderedSlots)
            {
                if (equipment.GetItem(slot) != null)
                {
                    count++;
                }
            }
            return count;
        }

        private static string GetSceneLabel(GameplaySceneKind kind)
        {
            switch (kind)
            {
                case GameplaySceneKind.Base: return "기지";
                case GameplaySceneKind.Raid: return "원정 지역";
                default: return "확인 중";
            }
        }

        private static string GetRaidStateLabel(RaidSessionState state)
        {
            switch (state)
            {
                case RaidSessionState.Inactive: return "대기";
                case RaidSessionState.Entering: return "출격 중";
                case RaidSessionState.Active: return "원정 중";
                case RaidSessionState.Resolved: return "결과 확정";
                case RaidSessionState.Returning: return "귀환 중";
                default: return state.ToString();
            }
        }

        private static string GetQuestStatusLabel(QuestProgressStatus status)
        {
            switch (status)
            {
                case QuestProgressStatus.Available: return "수락 가능";
                case QuestProgressStatus.Active: return "진행 중";
                case QuestProgressStatus.ReadyToTurnIn: return "완료 보고 가능";
                case QuestProgressStatus.Completed: return "완료";
                default: return status.ToString();
            }
        }

        private static string CompactLine(string value, int maximumLength)
        {
            string compact = (value ?? string.Empty)
                .Replace('\r', ' ')
                .Replace('\n', ' ')
                .Trim();
            return compact.Length <= maximumLength
                ? compact
                : compact.Substring(0, maximumLength - 1) + "…";
        }

        private void Select(Selectable selectable)
        {
            EventSystem eventSystem = shell.PlayerEventSystem;
            if (eventSystem == null || selectable == null ||
                !selectable.gameObject.activeInHierarchy)
            {
                return;
            }

            eventSystem.SetSelectedGameObject(null);
            eventSystem.SetSelectedGameObject(selectable.gameObject);
        }
    }
}
