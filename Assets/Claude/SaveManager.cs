using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// 게임 세이브/로드 시스템
/// - 폴더 자동 생성
/// - 슬롯별 저장 (최대 10개)
/// - 파일 존재 확인 기능
/// </summary>
public static class SaveManager
{
    static string saveFolder = Application.persistentDataPath + "/saves/";
    
    // ⚙️ 필수 전처리: 폴더 자동 생성
    static SaveManager()
    {
        if (!Directory.Exists(saveFolder))
        {
            Directory.CreateDirectory(saveFolder);
            Debug.Log($"[SaveManager] 세이브 폴더 생성: {saveFolder}");
        }
    }
    
    /// <summary>
    /// 게임 데이터 저장
    /// </summary>
    public static void Save(int slot)
    {
        SaveData data = new SaveData
        {
            saveSlot = slot,
            currentScene = SceneManager.GetActiveScene().name,
            saveDate = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
        };
        
        string json = JsonUtility.ToJson(data, true);
        string path = saveFolder + $"save_{slot}.json";
        
        try
        {
            File.WriteAllText(path, json);
            Debug.Log($"[SaveManager] 저장 완료: Slot {slot} - {path}");
        }
        catch (System.Exception e)
        {
            Debug.LogError($"[SaveManager] 저장 실패: {e.Message}");
        }
    }
    
    /// <summary>
    /// 게임 데이터 불러오기
    /// </summary>
    public static SaveData Load(int slot)
    {
        string path = saveFolder + $"save_{slot}.json";
        
        if (File.Exists(path))
        {
            try
            {
                string json = File.ReadAllText(path);
                SaveData data = JsonUtility.FromJson<SaveData>(json);
                Debug.Log($"[SaveManager] 불러오기 완료: Slot {slot}");
                return data;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SaveManager] 불러오기 실패: {e.Message}");
                return null;
            }
        }
        
        Debug.LogWarning($"[SaveManager] 세이브 파일 없음: {path}");
        return null;
    }
    
    /// <summary>
    /// 🛡️ 보완 권장: 세이브 파일 존재 여부 확인
    /// </summary>
    public static bool SaveExists(int slot)
    {
        string path = saveFolder + $"save_{slot}.json";
        return File.Exists(path);
    }
    
    /// <summary>
    /// 세이브 파일 삭제
    /// </summary>
    public static void Delete(int slot)
    {
        string path = saveFolder + $"save_{slot}.json";
        
        if (File.Exists(path))
        {
            try
            {
                File.Delete(path);
                Debug.Log($"[SaveManager] 세이브 삭제: Slot {slot}");
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[SaveManager] 삭제 실패: {e.Message}");
            }
        }
        else
        {
            Debug.LogWarning($"[SaveManager] 삭제할 파일 없음: Slot {slot}");
        }
    }
    
    /// <summary>
    /// 모든 세이브 슬롯 정보 조회
    /// </summary>
    public static SaveInfo[] GetAllSaveInfo()
    {
        SaveInfo[] saveInfos = new SaveInfo[10]; // 10개 슬롯
        
        for (int i = 0; i < 10; i++)
        {
            saveInfos[i] = new SaveInfo
            {
                slot = i,
                exists = SaveExists(i),
                data = SaveExists(i) ? Load(i) : null
            };
        }
        
        return saveInfos;
    }
}

/// <summary>
/// 세이브 데이터 구조
/// </summary>
[System.Serializable]
public class SaveData
{
    public int saveSlot;
    public string currentScene;
    public string saveDate;
    
    // 플레이어 데이터 (필요시 추가)
    // public int playerHealth;
    // public Vector3 playerPosition;
    // public List<ItemData> inventory;
}

/// <summary>
/// 세이브 슬롯 정보
/// </summary>
[System.Serializable]
public class SaveInfo
{
    public int slot;
    public bool exists;
    public SaveData data;
}
