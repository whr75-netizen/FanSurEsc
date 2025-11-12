using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 메인 메뉴 - 세이브 슬롯 관리
/// </summary>
public class MainMenu : MonoBehaviour
{
    [Header("세이브 슬롯 버튼들 (10개)")]
    public Button[] saveSlotButtons;
    
    [Header("슬롯 정보 텍스트")]
    public Text[] slotInfoTexts;
    
    void Start()
    {
        UpdateSaveSlots();
    }
    
    /// <summary>
    /// 세이브 슬롯 UI 갱신 (파일 존재 여부 표시)
    /// </summary>
    void UpdateSaveSlots()
    {
        SaveInfo[] saveInfos = SaveManager.GetAllSaveInfo();
        
        for (int i = 0; i < saveSlotButtons.Length; i++)
        {
            int slotIndex = i; // 클로저 문제 방지
            
            if (saveInfos[i].exists)
            {
                // 세이브 파일이 있으면 로드 가능
                saveSlotButtons[i].interactable = true;
                slotInfoTexts[i].text = $"Slot {i}\n{saveInfos[i].data.saveDate}";
                
                saveSlotButtons[i].onClick.RemoveAllListeners();
                saveSlotButtons[i].onClick.AddListener(() => LoadGame(slotIndex));
            }
            else
            {
                // 세이브 파일이 없으면 비활성화 또는 새 게임
                saveSlotButtons[i].interactable = false;
                slotInfoTexts[i].text = $"Slot {i}\n(비어있음)";
            }
        }
    }
    
    /// <summary>
    /// 세이브 데이터 로드 후 게임 씬으로 전환
    /// </summary>
    public void LoadGame(int slot)
    {
        SaveData data = SaveManager.Load(slot);
        
        if (data != null)
        {
            Debug.Log($"[MainMenu] 게임 로드: Slot {slot} - {data.currentScene}");
            GameLoader.LoadScene(data.currentScene, data);
        }
        else
        {
            Debug.LogError($"[MainMenu] 로드 실패: Slot {slot}");
        }
    }
    
    /// <summary>
    /// 새 게임 시작
    /// </summary>
    public void NewGame()
    {
        Debug.Log("[MainMenu] 새 게임 시작");
        GameLoader.LoadScene("GameStart", null);
    }
    
    /// <summary>
    /// 게임 종료
    /// </summary>
    public void QuitGame()
    {
        Debug.Log("[MainMenu] 게임 종료");
        Application.Quit();
    }
}
