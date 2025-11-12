// 파일 이름: InventoryUIManager.cs
// 플레이어 게임 오브젝트에 추가하세요.

using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using VariableInventorySystem;
using VariableInventorySystem.Sample;

public class InventoryUIManager : MonoBehaviour
{
    #region 필드 정의
    [Header("Core Component")] [SerializeField] private StandardCore standardCore;
    [Header("Player Inventory UI")] [SerializeField] private GameObject playerInventoryPanel;
    [SerializeField] private StandardStashView playerStashView;
    private StandardStashViewData playerInventoryData;
    [Header("External Inventory UI")] [SerializeField] private GameObject externalInventoryPanel;
    [SerializeField] private StandardStashView externalStashView;
    private StandardStashViewData currentExternalData;
    private Chest currentOpenedChest;
    [Header("Settings")] [SerializeField] private float interactionRange = 3f;
    [SerializeField] private int playerInventoryWidth = 8;
    [SerializeField] private int playerInventoryHeight = 9;
    private List<Chest> nearbyChests = new List<Chest>();
    private Chest closestChest = null;
    private bool isPlayerViewRegistered = false;
    private bool isExternalViewRegistered = false;
    // private bool isPlayerInventoryInitialized = false; // Apply 항상 호출 방식으로 변경 시 불필요

    #endregion

    #region 초기화
    void Awake()
    {
        if (standardCore == null) { Debug.LogError("StandardCore missing!"); enabled = false; return; }
        standardCore.Initialize();
        playerInventoryData = new StandardStashViewData(playerInventoryWidth, playerInventoryHeight);
        InitializeStartingItems();
        if (playerInventoryPanel == null || playerStashView == null || externalInventoryPanel == null || externalStashView == null) { Debug.LogError("UI references missing!"); enabled = false; return; }
        playerInventoryPanel.SetActive(false);
        externalInventoryPanel.SetActive(false);
    }
    void InitializeStartingItems() { /* 이전 답변과 동일 */ if (playerInventoryData == null) return; Debug.Log("[InitializeStartingItems] Adding items..."); try { var c = new CaseCellData(0); int? s = playerInventoryData.GetInsertableId(c); if (s.HasValue) playerInventoryData.InsertInventoryItem(s.Value, c); Debug.Log($" - Case Added: Slot {s}"); } catch { } for (int i = 0; i < 5; ++i) { try { var it = new ItemCellData(i); int? s = playerInventoryData.GetInsertableId(it); if (s.HasValue) { playerInventoryData.InsertInventoryItem(s.Value, it); Debug.Log($" - Item Seed {i} Added: Slot {s}"); } else break; } catch { } } Debug.Log($"[InitializeStartingItems] Finished. Items: {playerInventoryData.CellData?.Count(slot => slot != null) ?? 0}"); }
    #endregion

    #region 업데이트 및 상호작용 감지
    void Update() { UpdateClosestChest(); HandleInput(); CheckInteractionDistance(); }
    void OnTriggerEnter(Collider other) { /* 이전 답변과 동일 - Layer 체크 */ if (other.gameObject.layer == LayerMask.NameToLayer("Chest")) { Chest c = other.GetComponent<Chest>(); if (c != null && !nearbyChests.Contains(c)) nearbyChests.Add(c); } }
    void OnTriggerExit(Collider other)
    {
        if (other.gameObject.layer == LayerMask.NameToLayer("Chest"))
        { // Layer 체크
            Chest c = other.GetComponent<Chest>();
            if (c != null && nearbyChests.Contains(c))
            {
                nearbyChests.Remove(c);
                // ★★★ 열려있던 상자 범위 벗어나면 모두 닫기 ★★★
                if (c == currentOpenedChest)
                {
                    Debug.Log($"상자({c.name}) 범위 벗어남. 모든 인벤토리 닫기 시도.");
                    CloseAllInventories(); // HideExternalInventoryUI() 대신 호출
                }
                if (c == closestChest) closestChest = null;
            }
        }
    }
    void UpdateClosestChest() { /* 이전 답변과 동일 */ closestChest = null; float minDistance = float.MaxValue; nearbyChests.RemoveAll(item => item == null); foreach (var chest in nearbyChests) { float distance = Vector3.Distance(transform.position, chest.transform.position); if (distance < minDistance) { minDistance = distance; closestChest = chest; } } }
    void CheckInteractionDistance()
    {
        if (externalInventoryPanel != null && externalInventoryPanel.activeSelf && currentOpenedChest != null)
        {
            // 드래그 체크는 Hide/Close 함수 내부에서 하므로 여기선 제거
            if (currentOpenedChest == null) { CloseAllInventories(); return; } // 열린 상자 없으면 모두 닫기

            if (Vector3.Distance(transform.position, currentOpenedChest.transform.position) > interactionRange)
            {
                Debug.Log($"상자({currentOpenedChest.name}) 거리 멀어짐. 모든 인벤토리 닫기 시도.");
                CloseAllInventories(); // HideExternalInventoryUI() 대신 호출
            }
        }
    }
    #endregion

    #region 키 입력 처리
    void HandleInput()
    {
        // 드래그 체크는 각 닫기 함수에서 하므로 여기서는 제거
        if (Input.GetKeyDown(KeyCode.I))
        {
            if (externalInventoryPanel != null && externalInventoryPanel.activeSelf) CloseAllInventories(); // 외부 열려있으면 모두 닫기
            else TogglePlayerInventoryUI(); // 아니면 플레이어 토글
        }
        if (Input.GetKeyDown(KeyCode.E))
        {
            TryInteractWithChest();
        }
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            CloseAllInventories();
        }
    }

    void TryInteractWithChest()
    {
        if (closestChest != null && Vector3.Distance(transform.position, closestChest.transform.position) <= interactionRange)
        {
            if (externalInventoryPanel.activeSelf && currentOpenedChest == closestChest)
            {
                CloseAllInventories(); // 열린 상자면 모두 닫기 (내부에서 드래그 체크)
            }
            else
            {
                OpenPlayerAndExternalInventory(closestChest); // 열기 함수 호출
            }
        }
    }
    #endregion

    #region UI 관리 메소드 (드래그 취소 로직 포함)

    // 플레이어 인벤토리 토글
    void TogglePlayerInventoryUI() { if (playerInventoryPanel.activeSelf) HidePlayerInventoryUI(); else OpenPlayerInventoryUI(); }

    // 플레이어 인벤토리 열기 (Apply 항상 호출 - 상태 복원력)
    void OpenPlayerInventoryUI() { if (playerInventoryPanel == null || standardCore == null ) return; if (playerInventoryPanel.activeSelf) return; playerInventoryPanel.SetActive(true); if (!isPlayerViewRegistered) { standardCore.AddInventoryView(playerStashView); isPlayerViewRegistered = true; } playerStashView.Apply(playerInventoryData); Debug.Log("Player Inventory Opened"); }

    // 플레이어 인벤토리 숨기기 (드래그 중 취소 처리)
    private void HidePlayerInventoryUI()
    {
        // ★★★ 드래그 중이면 취소하고 함수 종료 ★★★
        if (standardCore != null && standardCore.IsDragging())
        {
            Debug.Log("[HidePlayerInventoryUI] 드래그 중. 취소 처리.");
            //standardCore.CancelDrag();
            return; // UI는 닫지 않음
        }
        // 드래그 중 아닐 때만 실행
        if (playerInventoryPanel == null || standardCore == null ) return; if (!playerInventoryPanel.activeSelf) return;
        if (isPlayerViewRegistered) { standardCore.RemoveInventoryView(playerStashView); isPlayerViewRegistered = false; }
        playerInventoryPanel.SetActive(false); Debug.Log("Player Inventory Hidden");
    }

    // 플레이어와 외부 인벤토리 함께 열기
    private void OpenPlayerAndExternalInventory(Chest chestToOpen) { OpenPlayerInventoryUI(); OpenExternalInventoryUI(chestToOpen); }

    // 외부 인벤토리 열기 (Apply는 필요시)
    void OpenExternalInventoryUI(Chest chest) { if (externalInventoryPanel == null || /*...*/ chest == null || chest.chestInventoryData == null) return; bool needsApply = !externalInventoryPanel.activeSelf || currentOpenedChest != chest; currentOpenedChest = chest; currentExternalData = chest.chestInventoryData; externalInventoryPanel.SetActive(true); if (!isExternalViewRegistered) { standardCore.AddInventoryView(externalStashView); isExternalViewRegistered = true; } if (needsApply) { externalStashView.Apply(currentExternalData); Debug.Log($"External Applied for {chest.name}"); } else { Debug.Log($"External Shown for {chest.name}"); } }

    // 외부 인벤토리 숨기기 (드래그 중 취소 처리)
    private void HideExternalInventoryUI()
    {
        // ★★★ 드래그 중이면 취소하고 함수 종료 ★★★
        if (standardCore != null && standardCore.IsDragging())
        {
            Debug.Log("[HideExternalInventoryUI] 드래그 중. 취소 처리.");
            standardCore.CancelDrag();
            return; // UI는 닫지 않음
        }
        // 드래그 중 아닐 때만 실행
        if (externalInventoryPanel == null || standardCore == null ) return; if (!externalInventoryPanel.activeSelf) return;
        if (isExternalViewRegistered) { standardCore.RemoveInventoryView(externalStashView); isExternalViewRegistered = false; }
        externalInventoryPanel.SetActive(false); currentOpenedChest = null; currentExternalData = null; Debug.Log("External Inventory Hidden");
    }

    // 모든 인벤토리 닫기 (Hide 함수 호출)
    public void CloseAllInventories()
    {
        HideExternalInventoryUI(); // 내부에서 드래그 체크 및 취소 처리
        HidePlayerInventoryUI();   // 내부에서 드래그 체크 및 취소 처리
    }

    // 컴포넌트 파괴 시 정리
    void OnDestroy() { /* 이전 코드와 동일 */ if (standardCore != null) { if (playerStashView != null) standardCore.RemoveInventoryView(playerStashView); if (externalStashView != null) standardCore.RemoveInventoryView(externalStashView); } }

    #endregion
}

// Chest.cs 스크립트는 이전과 동일하게 프로젝트에 존재해야 합니다.