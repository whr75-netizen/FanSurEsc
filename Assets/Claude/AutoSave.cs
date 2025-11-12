using UnityEngine;

/// <summary>
/// 자동 저장 시스템
/// - 일정 시간마다 자동 저장
/// - 체크포인트 트리거 저장
/// </summary>
public class AutoSave : MonoBehaviour
{
    [Header("자동 저장 설정")]
    public bool enableAutoSave = true;
    public float autoSaveInterval = 60f; // 60초마다
    public int autoSaveSlot = 0; // 자동 저장 전용 슬롯
    
    void Start()
    {
        if (enableAutoSave)
        {
            InvokeRepeating(nameof(AutoSaveGame), autoSaveInterval, autoSaveInterval);
        }
    }
    
    /// <summary>
    /// 자동 저장 실행
    /// </summary>
    void AutoSaveGame()
    {
        SaveManager.Save(autoSaveSlot);
        Debug.Log($"[AutoSave] 자동 저장 완료 (Slot {autoSaveSlot})");
    }
    
    /// <summary>
    /// 수동 저장 (특정 이벤트 시)
    /// </summary>
    public void SaveNow(int slot)
    {
        SaveManager.Save(slot);
    }
    
    void OnDestroy()
    {
        CancelInvoke();
    }
}
