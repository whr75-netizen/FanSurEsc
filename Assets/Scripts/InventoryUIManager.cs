// 파일 이름: InventoryUIManager.cs
// 플레이어 게임 오브젝트에 추가하세요.

using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using FantasySurvival.Interaction;
using FantasySurvival.Inventory;
using FantasySurvival.Trading;
using VariableInventorySystem;

[RequireComponent(typeof(PlayerInteractor))]
public class InventoryUIManager : MonoBehaviour
{
    public const int DefaultInventoryWidth = 8;
    public const int DefaultInventoryHeight = 9;

    #region 필드 정의
    [Header("Core Component")] [SerializeField] private StandardCore standardCore;
    [Header("Item Database")] [SerializeField] private ItemDatabase itemDatabase;
    [SerializeField] private int[] startingItemIds = { 1, 2, 3, 4, 5 };
    [Header("Player Inventory UI")] [SerializeField] private GameObject playerInventoryPanel;
    [SerializeField] private StandardStashView playerStashView;
    [SerializeField] private Text goldAmountText;
    [SerializeField] private Text silverAmountText;
    [Header("Player Equipment UI")] [SerializeField] private GameObject equipmentPanel;
    [SerializeField] private EquipmentPanelView equipmentView;
    private PlayerInventoryState playerState;
    [Header("External Inventory UI")] [SerializeField] private GameObject externalInventoryPanel;
    [SerializeField] private StandardStashView externalStashView;
    private StandardStashViewData currentExternalData;
    private Chest currentOpenedChest;
    private Merchant currentOpenedMerchant;
    private Interactable currentExternalInteractable;
    private ExternalInventoryMode currentExternalMode;
    private PlayerInteractor playerInteractor;
    [Header("Merchant UI")]
    [SerializeField] private GameObject merchantControlsRoot;
    [SerializeField] private Button merchantAllTabButton;
    [SerializeField] private Button merchantEquipmentTabButton;
    [SerializeField] private Button merchantOtherTabButton;
    [SerializeField] private Text merchantCatalogText;
    [SerializeField] private Text merchantStatusText;
    [Header("Item Tooltip")]
    [SerializeField] private InventoryItemTooltipView itemTooltipView;
    [Header("Stack Split UI")]
    [SerializeField] private InventoryStackSplitDialog stackSplitDialog;
    [Header("Settings")]
    [SerializeField] private int playerInventoryWidth = DefaultInventoryWidth;
    [SerializeField] private int playerInventoryHeight = DefaultInventoryHeight;
    private bool isPlayerViewRegistered = false;
    private bool isEquipmentViewRegistered = false;
    private bool isExternalViewRegistered = false;
    private bool inputBlocked;
    private InventoryTransferCoordinator transferCoordinator;

    private enum MerchantCategory
    {
        All,
        Equipment,
        Other
    }

    private MerchantCategory merchantCategory = MerchantCategory.All;
    // private bool isPlayerInventoryInitialized = false; // Apply 항상 호출 방식으로 변경 시 불필요

    public bool InputBlocked => inputBlocked;
    public bool IsAnyInventoryOpen =>
        (playerInventoryPanel != null && playerInventoryPanel.activeSelf) ||
        (equipmentPanel != null && equipmentPanel.activeSelf) ||
        (externalInventoryPanel != null && externalInventoryPanel.activeSelf);
    public bool HasActiveDrag => standardCore != null && standardCore.IsDragging();
    public bool IsStackSplitQuantityEntryOpen =>
        stackSplitDialog != null && stackSplitDialog.IsQuantityEntryOpen;
    public bool BlocksGameplayInput => inputBlocked || IsAnyInventoryOpen;
    public bool IsExternalInventoryOpen =>
        externalInventoryPanel != null && externalInventoryPanel.activeSelf;
    public ItemDatabase ItemDatabase => itemDatabase;
    public PlayerInventoryState PlayerState => playerState;
    public StandardStashViewData PlayerInventoryData => playerState?.Inventory;
    public EquipmentLoadoutData PlayerEquipmentData => playerState?.Equipment;
    public PlayerWallet PlayerWallet => playerState?.Wallet;
    public event Action<PlayerInventoryState> PlayerStateChanged;

    #endregion

    #region 초기화
    void Awake()
    {
        playerInteractor = GetComponent<PlayerInteractor>();
        if (playerInteractor == null)
        {
            Debug.LogError("InventoryUIManager requires PlayerInteractor on the same GameObject.", this);
            enabled = false;
            return;
        }

        if (standardCore == null) { Debug.LogError("StandardCore missing!"); enabled = false; return; }
        if (itemDatabase == null) { Debug.LogError("ItemDatabase missing!"); enabled = false; return; }
        standardCore.Initialize();
        if (!TryCreateStartingInventory(out StandardStashViewData startingInventory, out string initializationError))
        {
            Debug.LogError($"[InitializeStartingItems] {initializationError}", this);
            enabled = false;
            return;
        }
        playerState = new PlayerInventoryState(startingInventory, new EquipmentLoadoutData());
        if (playerInventoryPanel == null || playerStashView == null ||
            equipmentPanel == null || equipmentView == null ||
            externalInventoryPanel == null || externalStashView == null ||
            goldAmountText == null || silverAmountText == null ||
            merchantControlsRoot == null || merchantAllTabButton == null ||
            merchantEquipmentTabButton == null || merchantOtherTabButton == null ||
            merchantCatalogText == null || merchantStatusText == null ||
            itemTooltipView == null || stackSplitDialog == null)
        {
            Debug.LogError("UI references missing!");
            enabled = false;
            return;
        }
        if (!itemTooltipView.TryValidateReferences(out string tooltipError))
        {
            Debug.LogError(tooltipError, itemTooltipView);
            enabled = false;
            return;
        }
        if (!stackSplitDialog.TryValidateReferences(out string splitDialogError))
        {
            Debug.LogError(splitDialogError, stackSplitDialog);
            enabled = false;
            return;
        }
        if (!equipmentView.TryValidateCells(out string equipmentError))
        {
            Debug.LogError(equipmentError, equipmentView);
            enabled = false;
            return;
        }
        // StandardCore also applies this shared presentation policy to nested
        // container popups created after initialization.
        standardCore.SetQuantityBadgeTextProvider(GetItemQuantityBadgeText);
        playerInventoryPanel.SetActive(false);
        equipmentPanel.SetActive(false);
        externalInventoryPanel.SetActive(false);
        merchantControlsRoot.SetActive(false);
        merchantAllTabButton.onClick.AddListener(() => SetMerchantCategory(MerchantCategory.All));
        merchantEquipmentTabButton.onClick.AddListener(() => SetMerchantCategory(MerchantCategory.Equipment));
        merchantOtherTabButton.onClick.AddListener(() => SetMerchantCategory(MerchantCategory.Other));
        transferCoordinator = new InventoryTransferCoordinator(
            playerState,
            RefreshOpenViews,
            SetExternalStatus);
        standardCore.SetTransferController(transferCoordinator);
        standardCore.HoveredCellChanged += HandleHoveredCellChanged;
        standardCore.ItemContextRequested += HandleItemContextRequested;
        standardCore.StackSplitRequested += HandleStackSplitRequested;
        itemTooltipView.Hide();
        stackSplitDialog.Close();
        BindWallet(playerState.Wallet);
        PlayerStateChanged?.Invoke(playerState);
    }

    bool TryCreateStartingInventory(out StandardStashViewData inventoryData, out string error)
    {
        if (!InventoryGridConstraints.TryValidateDimensions(
                playerInventoryWidth,
                playerInventoryHeight,
                out error))
        {
            inventoryData = null;
            return false;
        }

        inventoryData = new StandardStashViewData(playerInventoryWidth, playerInventoryHeight);
        if (inventoryData == null)
        {
            error = "Could not create the player inventory grid.";
            return false;
        }

        Debug.Log("[InitializeStartingItems] Adding items from ItemDatabase...");
        foreach (var itemId in startingItemIds)
        {
            if (!TryAddStartingItem(inventoryData, itemId, out error))
            {
                return false;
            }
        }

        int occupiedCellCount = 0;
        if (inventoryData.CellData != null)
        {
            foreach (IVariableInventoryCellData cell in inventoryData.CellData)
            {
                if (cell != null)
                {
                    occupiedCellCount++;
                }
            }
        }
        Debug.Log($"[InitializeStartingItems] Finished. Items: {occupiedCellCount}");
        error = null;
        return true;
    }

    bool TryAddStartingItem(StandardStashViewData target, int itemId, out string error)
    {
        if (!itemDatabase.TryGet(itemId, out var definition))
        {
            error = $"Unknown starting item ID: {itemId}.";
            return false;
        }

        if (!InventoryItemDataFactory.TryCreate(definition, out var item, out error))
        {
            error = $"Starting item ID {itemId} is invalid: {error}";
            return false;
        }

        var slot = target.GetInsertableId(item);
        if (!slot.HasValue)
        {
            error = $"No room for starting item {itemId} ({definition.DisplayName}).";
            return false;
        }

        target.InsertInventoryItem(slot.Value, item);
        Debug.Log($" - Added {definition.DisplayName} (ID {itemId}): Slot {slot.Value}");
        error = null;
        return true;
    }

    public bool TryResetToStartingInventory(out string error)
    {
        if (!TryCreateStartingPlayerState(out PlayerInventoryState startingState, out error))
        {
            return false;
        }

        return TryReplacePlayerState(startingState, out error);
    }

    public bool TryCreateStartingPlayerState(out PlayerInventoryState startingState, out string error)
    {
        startingState = null;
        if (!TryCreateStartingInventory(out StandardStashViewData startingInventory, out error))
        {
            return false;
        }

        startingState = new PlayerInventoryState(startingInventory, new EquipmentLoadoutData());
        error = null;
        return true;
    }

    public bool TryReplacePlayerInventory(StandardStashViewData replacement, out string error)
    {
        if (replacement == null)
        {
            error = "Replacement inventory is missing.";
            return false;
        }

        return TryReplacePlayerState(
            new PlayerInventoryState(
                replacement,
                playerState?.Equipment ?? new EquipmentLoadoutData(),
                playerState?.Wallet ?? new PlayerWallet()),
            out error);
    }

    public bool TryReplacePlayerState(PlayerInventoryState replacement, out string error)
    {
        if (replacement?.Inventory == null || replacement.Equipment == null)
        {
            error = "Replacement player inventory state is missing.";
            return false;
        }

        if (replacement.Inventory.CapacityWidth != playerInventoryWidth ||
            replacement.Inventory.CapacityHeight != playerInventoryHeight ||
            replacement.Inventory.CellData == null ||
            replacement.Inventory.CellData.Length != playerInventoryWidth * playerInventoryHeight)
        {
            error = $"Replacement inventory must be {playerInventoryWidth}x{playerInventoryHeight}.";
            return false;
        }

        if (!CloseAllInventories())
        {
            error = "Could not replace player state because the active drag could not be restored.";
            return false;
        }

        UnbindWallet(playerState?.Wallet);
        playerState = replacement;
        BindWallet(playerState.Wallet);
        transferCoordinator?.SetPlayerState(playerState);
        PlayerStateChanged?.Invoke(playerState);
        error = null;
        return true;
    }

    public bool TryDiscardAllCarriedItems(out string error)
    {
        if (playerState == null)
        {
            error = "Player inventory state is missing.";
            return false;
        }

        if (!CloseAllInventories())
        {
            error = "Could not discard carried items because the active drag could not be restored.";
            return false;
        }

        return playerState.TryDiscardAllCarriedItems(out error);
    }
    #endregion

    #region 업데이트 및 상호작용 감지
    void Update()
    {
        if (!inputBlocked)
        {
            HandleInput();
        }

        CheckInteractionDistance();
    }
    void CheckInteractionDistance()
    {
        if (!IsExternalInventoryOpen)
        {
            return;
        }

        // Unity의 파괴된 오브젝트는 null처럼 비교된다. 열린 외부 대상이
        // 사라졌다면 거리 계산보다 먼저 세 패널과 등록된 View를 정리한다.
        if (currentExternalInteractable == null)
        {
            CloseAllInventories();
            return;
        }

        if (!currentExternalInteractable.isActiveAndEnabled ||
            !currentExternalInteractable.gameObject.activeInHierarchy ||
            !playerInteractor.IsWithinInteractionRange(currentExternalInteractable.transform))
        {
            Debug.Log($"외부 인벤토리({currentExternalInteractable.name}) 상호작용 종료. 모든 인벤토리 닫기 시도.");
            CloseAllInventories();
        }
    }
    #endregion

    #region 키 입력 처리
    void HandleInput()
    {
        if (IsStackSplitQuantityEntryOpen)
        {
            return;
        }

        // 드래그 체크는 각 닫기 함수에서 하므로 여기서는 제거
        if (Input.GetKeyDown(KeyCode.I))
        {
            if (externalInventoryPanel != null && externalInventoryPanel.activeSelf) CloseAllInventories(); // 외부 열려있으면 모두 닫기
            else TogglePlayerInventoryUI(); // 아니면 플레이어 토글
        }
        if (standardCore != null && standardCore.IsDragging() && Input.GetKeyDown(KeyCode.R))
        {
            standardCore.SwitchRotate();
        }
    }

    public bool TryToggleChestInventory(Chest chest)
    {
        if (!isActiveAndEnabled || chest == null || chest.chestInventoryData == null)
        {
            return false;
        }

        if (playerInteractor == null || !playerInteractor.IsWithinInteractionRange(chest.transform))
        {
            return false;
        }

        if (externalInventoryPanel.activeSelf)
        {
            if (currentOpenedChest == chest)
            {
                return CloseAllInventories();
            }

            if (!CloseAllInventories())
            {
                return false;
            }
        }

        ChestInteractable interactable = chest.GetComponent<ChestInteractable>();
        if (interactable == null)
        {
            return false;
        }

        OpenPlayerAndExternalInventory(
            chest.chestInventoryData,
            interactable,
            ExternalInventoryMode.Storage,
            chest,
            null);

        return true;
    }

    public bool IsChestOpen(Chest chest)
    {
        return chest != null && IsExternalInventoryOpen &&
               currentExternalMode == ExternalInventoryMode.Storage &&
               currentOpenedChest == chest;
    }

    public bool TryToggleMerchantInventory(
        MerchantInteractable interactable,
        Merchant merchant,
        StandardStashViewData merchantInventory)
    {
        if (!isActiveAndEnabled || interactable == null || merchant == null ||
            merchantInventory == null ||
            playerInteractor == null ||
            !playerInteractor.IsWithinInteractionRange(interactable.transform))
        {
            return false;
        }

        if (IsExternalInventoryOpen)
        {
            if (currentExternalInteractable == interactable)
            {
                return CloseAllInventories();
            }

            if (!CloseAllInventories())
            {
                return false;
            }
        }

        OpenPlayerAndExternalInventory(
            merchantInventory,
            interactable,
            ExternalInventoryMode.Merchant,
            null,
            merchant);
        return true;
    }

    public bool IsMerchantOpen(MerchantInteractable merchant)
    {
        return merchant != null && IsExternalInventoryOpen &&
               currentExternalMode == ExternalInventoryMode.Merchant &&
               currentExternalInteractable == merchant;
    }

    public void SetInputBlocked(bool blocked)
    {
        inputBlocked = blocked;
    }
    #endregion

    #region UI 관리 메소드 (드래그 취소 로직 포함)

    // 플레이어 인벤토리 토글
    void TogglePlayerInventoryUI()
    {
        if (playerInventoryPanel.activeSelf)
        {
            CloseAllInventories();
        }
        else
        {
            OpenPlayerInventoryUI();
        }
    }

    // 플레이어 인벤토리 열기 (Apply 항상 호출 - 상태 복원력)
    void OpenPlayerInventoryUI()
    {
        if (playerInventoryPanel == null || equipmentPanel == null || standardCore == null || playerState == null)
        {
            return;
        }

        if (playerInventoryPanel.activeSelf)
        {
            return;
        }

        playerInventoryPanel.SetActive(true);
        equipmentPanel.SetActive(true);
        if (!isPlayerViewRegistered)
        {
            standardCore.AddInventoryView(playerStashView);
            isPlayerViewRegistered = true;
        }
        if (!isEquipmentViewRegistered)
        {
            standardCore.AddInventoryView(equipmentView);
            isEquipmentViewRegistered = true;
        }

        playerStashView.Apply(playerState.Inventory);
        equipmentView.Apply(playerState.Equipment);
        Debug.Log("Player Inventory And Equipment Opened");
    }

    // 플레이어 인벤토리 숨기기 (드래그 중 취소 처리)
    private void HidePlayerInventoryUI()
    {
        if (playerInventoryPanel == null || standardCore == null ) return; if (!playerInventoryPanel.activeSelf) return;
        if (isEquipmentViewRegistered) { standardCore.RemoveInventoryView(equipmentView); isEquipmentViewRegistered = false; }
        if (isPlayerViewRegistered) { standardCore.RemoveInventoryView(playerStashView); isPlayerViewRegistered = false; }
        if (equipmentPanel != null) equipmentPanel.SetActive(false);
        playerInventoryPanel.SetActive(false); Debug.Log("Player Inventory And Equipment Hidden");
    }

    // 플레이어와 외부 인벤토리 함께 열기
    private void OpenPlayerAndExternalInventory(
        StandardStashViewData data,
        Interactable interactable,
        ExternalInventoryMode mode,
        Chest chest,
        Merchant merchant)
    {
        OpenPlayerInventoryUI();
        OpenExternalInventoryUI(data, interactable, mode, chest, merchant);
    }

    // 외부 인벤토리 열기 (Apply는 필요시)
    void OpenExternalInventoryUI(
        StandardStashViewData data,
        Interactable interactable,
        ExternalInventoryMode mode,
        Chest chest,
        Merchant merchant)
    {
        if (externalInventoryPanel == null || data == null || interactable == null ||
            mode == ExternalInventoryMode.None)
        {
            return;
        }

        currentOpenedChest = chest;
        currentOpenedMerchant = merchant;
        currentExternalInteractable = interactable;
        currentExternalMode = mode;
        currentExternalData = data;
        externalInventoryPanel.SetActive(true);
        if (!isExternalViewRegistered)
        {
            standardCore.AddInventoryView(externalStashView);
            isExternalViewRegistered = true;
        }

        transferCoordinator.SetExternalSession(mode, data);
        if (mode == ExternalInventoryMode.Merchant)
        {
            merchantControlsRoot.SetActive(true);
            SetExternalStatus("Shift+클릭 또는 드래그로 구매·판매", false);
            merchantCategory = MerchantCategory.All;
            ConfigureMerchantItemPresentation(false);
        }
        else
        {
            merchantControlsRoot.SetActive(false);
            externalStashView.SetItemPresentation(null, null, false);
        }

        // External grids can have different dimensions (base Chest, corpse, Merchant).
        // Always bind the new authority once after its presentation context is set.
        externalStashView.Apply(currentExternalData);
        if (mode == ExternalInventoryMode.Merchant)
        {
            RefreshMerchantPresentationLabels();
        }
        Debug.Log($"External Applied for {interactable.name}");
    }

    // 외부 인벤토리 숨기기 (드래그 중 취소 처리)
    private void HideExternalInventoryUI()
    {
        if (externalInventoryPanel == null || standardCore == null ) return; if (!externalInventoryPanel.activeSelf) return;
        if (isExternalViewRegistered) { standardCore.RemoveInventoryView(externalStashView); isExternalViewRegistered = false; }
        itemTooltipView?.Hide();
        externalStashView.SetItemPresentation(null, null, false);
        merchantControlsRoot.SetActive(false);
        externalInventoryPanel.SetActive(false);
        currentOpenedChest = null;
        currentOpenedMerchant = null;
        currentExternalInteractable = null;
        currentExternalData = null;
        currentExternalMode = ExternalInventoryMode.None;
        transferCoordinator?.ClearExternalSession();
        Debug.Log("External Inventory Hidden");
    }

    // 모든 인벤토리 닫기 (Hide 함수 호출)
    public bool CloseAllInventories()
    {
        stackSplitDialog?.Close();
        if (standardCore != null && standardCore.IsDragging() && !standardCore.CancelDrag())
        {
            return false;
        }

        if (standardCore != null) standardCore.CloseAllCasePopups();
        itemTooltipView?.Hide();
        HideExternalInventoryUI();
        HidePlayerInventoryUI();
        return true;
    }

    void OnDisable()
    {
        itemTooltipView?.Hide();
        stackSplitDialog?.Close();
        CancelActiveDrag();
    }

    // 컴포넌트 파괴 시 정리
    void OnDestroy()
    {
        UnbindWallet(playerState?.Wallet);
        if (standardCore == null)
        {
            return;
        }

        standardCore.HoveredCellChanged -= HandleHoveredCellChanged;
        standardCore.ItemContextRequested -= HandleItemContextRequested;
        standardCore.StackSplitRequested -= HandleStackSplitRequested;
        standardCore.SetTransferController(null);
        stackSplitDialog?.Close();

        // A dragged item temporarily lives in the scene-local core, outside CellData.
        // Restore it before the scene unloads so the persistent inventory cannot lose it.
        CancelActiveDrag();

        if (playerStashView != null)
        {
            standardCore.RemoveInventoryView(playerStashView);
        }

        if (equipmentView != null)
        {
            standardCore.RemoveInventoryView(equipmentView);
        }

        if (externalStashView != null)
        {
            standardCore.RemoveInventoryView(externalStashView);
        }
    }

    private void BindWallet(PlayerWallet wallet)
    {
        if (wallet != null)
        {
            wallet.Changed += RefreshWalletUI;
        }
        RefreshWalletUI();
    }

    private void UnbindWallet(PlayerWallet wallet)
    {
        if (wallet != null)
        {
            wallet.Changed -= RefreshWalletUI;
        }
    }

    private void RefreshWalletUI()
    {
        if (goldAmountText != null)
        {
            goldAmountText.text = $"금  {(playerState?.Wallet.Gold ?? 0):N0}";
        }
        if (silverAmountText != null)
        {
            silverAmountText.text = $"은  {(playerState?.Wallet.Silver ?? 0):N0}";
        }
    }

    private void RefreshOpenViews()
    {
        itemTooltipView?.Hide();
        if (playerState != null && playerInventoryPanel != null && playerInventoryPanel.activeSelf)
        {
            playerStashView.Apply(playerState.Inventory);
            equipmentView.Apply(playerState.Equipment);
        }

        if (currentExternalData != null && IsExternalInventoryOpen)
        {
            externalStashView.Apply(currentExternalData);
            if (currentExternalMode == ExternalInventoryMode.Merchant)
            {
                RefreshMerchantPresentationLabels();
            }
        }
    }

    private void SetMerchantCategory(MerchantCategory category)
    {
        if (currentExternalMode != ExternalInventoryMode.Merchant || currentExternalData == null)
        {
            return;
        }

        if (standardCore.IsDragging() && !standardCore.CancelDrag())
        {
            SetExternalStatus("드래그 원본을 복구할 수 없어 탭을 바꾸지 못했습니다.", true);
            return;
        }

        itemTooltipView?.Hide();
        merchantCategory = category;
        ConfigureMerchantItemPresentation(true);
    }

    private void ConfigureMerchantItemPresentation(bool refreshCurrent)
    {
        externalStashView.SetItemPresentation(
            IsItemVisibleInMerchantCategory,
            GetMerchantPriceBadgeText,
            refreshCurrent);
        if (refreshCurrent)
        {
            RefreshMerchantPresentationLabels();
        }
    }

    private bool IsItemVisibleInMerchantCategory(IVariableInventoryCellData item)
    {
        if (!(item is InventoryItemData inventoryItem))
        {
            return merchantCategory == MerchantCategory.All;
        }

        switch (merchantCategory)
        {
            case MerchantCategory.Equipment: return inventoryItem.Definition.IsEquippable;
            case MerchantCategory.Other: return !inventoryItem.Definition.IsEquippable;
            default: return true;
        }
    }

    private static string GetMerchantPriceBadgeText(IVariableInventoryCellData item)
    {
        if (!(item is InventoryItemData inventoryItem) ||
            !inventoryItem.Definition.IsTradable)
        {
            return null;
        }

        return $"{InventoryTransferCoordinator.GetCurrencyName(inventoryItem.Definition.TradeCurrency)} " +
               inventoryItem.Definition.TradePrice.ToString("N0");
    }

    private static string GetItemQuantityBadgeText(IVariableInventoryCellData item)
    {
        if (!(item is InventoryItemData inventoryItem) || inventoryItem.MaxStackSize <= 1)
        {
            return null;
        }

        return $"{inventoryItem.Quantity}/{inventoryItem.MaxStackSize}";
    }

    private void RefreshMerchantPresentationLabels()
    {
        if (currentExternalMode != ExternalInventoryMode.Merchant)
        {
            return;
        }

        merchantAllTabButton.interactable = merchantCategory != MerchantCategory.All;
        merchantEquipmentTabButton.interactable = merchantCategory != MerchantCategory.Equipment;
        merchantOtherTabButton.interactable = merchantCategory != MerchantCategory.Other;
        RefreshMerchantCatalogText();
    }

    private void RefreshMerchantCatalogText()
    {
        if (merchantCatalogText == null || currentExternalData?.CellData == null)
        {
            return;
        }

        var seen = new HashSet<IVariableInventoryCellData>();
        int visibleItemCount = 0;
        foreach (IVariableInventoryCellData cell in currentExternalData.CellData)
        {
            if (!(cell is InventoryItemData item) || !seen.Add(item) ||
                !externalStashView.IsItemVisible(item) || !item.Definition.IsTradable)
            {
                continue;
            }

            visibleItemCount++;
        }

        merchantCatalogText.text = visibleItemCount > 0
            ? $"상품 {visibleItemCount}개"
            : "해당 분류의 상품이 없습니다.";
    }

    private void HandleItemContextRequested(
        IVariableInventoryView sourceView,
        IVariableInventoryCell sourceCell)
    {
        if (inputBlocked || standardCore == null || standardCore.IsDragging() ||
            sourceView == null || !(sourceCell?.CellData is InventoryItemData sourceItem))
        {
            return;
        }

        Action useAction = null;
        if (sourceItem is IStandardCaseCellData &&
            standardCore.CanOpenCase(sourceView, sourceCell))
        {
            useAction = () =>
            {
                if (!standardCore.TryOpenCase(sourceView, sourceCell))
                {
                    Debug.LogWarning("Container use failed because its source cell changed.", this);
                }
            };
        }

        bool canSplit = sourceItem.Quantity > 1 && sourceItem.MaxStackSize > 1 &&
                        currentExternalMode != ExternalInventoryMode.Merchant;
        if (!canSplit && useAction == null)
        {
            if (currentExternalMode == ExternalInventoryMode.Merchant &&
                sourceItem.Quantity > 1 && sourceItem.MaxStackSize > 1)
            {
                SetExternalStatus(
                    "Stack 단가 정책이 확정되기 전에는 상인 거래 중 분할할 수 없습니다.",
                    true);
            }

            return;
        }

        itemTooltipView?.Hide();
        stackSplitDialog.OpenContext(
            sourceItem.Definition.DisplayName,
            useAction,
            canSplit ? sourceItem.Quantity - 1 : 0,
            Input.mousePosition,
            canSplit
                ? quantity => TryBeginStackSplit(
                    sourceView,
                    sourceCell,
                    sourceItem,
                    quantity,
                    VariableInventoryCarryMode.Click)
                : null);
    }

    private void HandleStackSplitRequested(
        IVariableInventoryView sourceView,
        IVariableInventoryCell sourceCell,
        VariableInventoryCarryMode carryMode)
    {
        if (inputBlocked || standardCore == null || standardCore.IsDragging() ||
            sourceView == null || !(sourceCell?.CellData is InventoryItemData sourceItem) ||
            sourceItem.Quantity <= 1 || sourceItem.MaxStackSize <= 1)
        {
            return;
        }

        if (currentExternalMode == ExternalInventoryMode.Merchant)
        {
            SetExternalStatus(
                "Stack 단가 정책이 확정되기 전에는 상인 거래 중 분할할 수 없습니다.",
                true);
            return;
        }

        itemTooltipView?.Hide();
        int half = sourceItem.Quantity / 2;
        string error = TryBeginStackSplit(
            sourceView,
            sourceCell,
            sourceItem,
            half,
            carryMode);
        if (!string.IsNullOrEmpty(error))
        {
            Debug.LogWarning($"Stack split failed: {error}", this);
        }
    }

    private string TryBeginStackSplit(
        IVariableInventoryView sourceView,
        IVariableInventoryCell sourceCell,
        InventoryItemData sourceItem,
        int splitQuantity,
        VariableInventoryCarryMode carryMode)
    {
        if (transferCoordinator == null || standardCore == null)
        {
            return "인벤토리 분할 시스템이 준비되지 않았습니다.";
        }

        if (!transferCoordinator.TryBeginStackSplit(
                sourceView,
                sourceItem,
                splitQuantity,
                out InventoryStackSplitTransaction transaction,
                out string error))
        {
            return error;
        }

        bool Rollback()
        {
            bool restored = transaction.TryRollback(out string rollbackError);
            if (!restored)
            {
                Debug.LogError($"Stack split rollback failed: {rollbackError}", this);
                return false;
            }

            ReApplyViewIfAlive(sourceView);
            RefreshOpenViews();
            return true;
        }

        bool Commit()
        {
            if (!transaction.TryCommit(out string commitError))
            {
                Debug.LogError($"Stack split commit failed: {commitError}", this);
                return false;
            }

            return true;
        }

        bool RecordStackMerge(
            IVariableInventoryCellData target,
            int movedQuantity,
            int remainingQuantity)
        {
            string mergeError = null;
            if (!(target is InventoryItemData targetItem) ||
                !transaction.TryRecordStackMerge(
                    targetItem,
                    movedQuantity,
                    remainingQuantity,
                    out mergeError))
            {
                Debug.LogError(
                    $"Stack split merge record failed: {mergeError ?? "invalid target item"}",
                    this);
                return false;
            }

            return true;
        }

        if (!standardCore.TryBeginStackSplitCarry(
                sourceView,
                sourceCell,
                transaction.SplitItem,
                carryMode,
                Rollback,
                Commit,
                RecordStackMerge,
                out error))
        {
            if (!transaction.TryRollback(out string rollbackError))
            {
                error = $"{error} Rollback also failed: {rollbackError}";
            }

            ReApplyViewIfAlive(sourceView);
            RefreshOpenViews();
            return error;
        }

        ReApplyViewIfAlive(sourceView);
        RefreshOpenViews();
        return null;
    }

    private static void ReApplyViewIfAlive(IVariableInventoryView view)
    {
        if (view == null ||
            (view is UnityEngine.Object unityView && unityView == null))
        {
            return;
        }

        view.ReApply();
    }

    private void HandleHoveredCellChanged(
        IVariableInventoryView sourceView,
        IVariableInventoryCell cell)
    {
        if (itemTooltipView == null || standardCore == null || standardCore.IsDragging() ||
            !(cell?.CellData is InventoryItemData item))
        {
            itemTooltipView?.Hide();
            return;
        }

        if (sourceView is StandardStashView stashView &&
            !stashView.IsItemVisible(item))
        {
            itemTooltipView.Hide();
            return;
        }

        itemTooltipView.Show(item.Definition);
    }

    private void SetExternalStatus(string message, bool isError)
    {
        if (merchantStatusText == null || currentExternalMode != ExternalInventoryMode.Merchant)
        {
            return;
        }

        merchantStatusText.text = message ?? string.Empty;
        merchantStatusText.color = isError
            ? new Color(1f, 0.45f, 0.4f, 1f)
            : new Color(0.9f, 0.9f, 0.9f, 1f);
    }

    void CancelActiveDrag()
    {
        if (standardCore != null && standardCore.IsDragging())
        {
            standardCore.CancelDrag();
        }
    }

    #endregion
}

// Chest.cs 스크립트는 이전과 동일하게 프로젝트에 존재해야 합니다.
