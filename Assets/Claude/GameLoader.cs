using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// 씬 전환 시 데이터 안전 전달 및 플레이어 생성 담당
/// </summary>
public class GameLoader : MonoBehaviour
{
    [Header("플레이어 설정")]
    public GameObject playerPrefab;
    
    [Header("스폰 포인트 (선택)")]
    public Transform spawnPoint;
    
    // 씬 간 데이터 전달용 static 변수
    public static SaveData saveToLoad = null;
    
    void Start()
    {
        // 저장된 데이터가 있으면 로드, 없으면 새 게임
        if (saveToLoad != null)
        {
            LoadSavedPlayer();
        }
        else
        {
            CreateNewPlayer();
        }
    }
    
    /// <summary>
    /// 새 게임 시작 (플레이어 기본 생성)
    /// </summary>
    void CreateNewPlayer()
    {
        Vector3 spawnPos = spawnPoint != null ? spawnPoint.position : Vector3.zero;
        GameObject player = Instantiate(playerPrefab, spawnPos, Quaternion.identity);
        Debug.Log("[GameLoader] 새 플레이어 생성");
    }
    
    /// <summary>
    /// 저장된 데이터로 플레이어 복원
    /// </summary>
    void LoadSavedPlayer()
    {
        SaveData data = saveToLoad;
        
        Vector3 spawnPos = spawnPoint != null ? spawnPoint.position : Vector3.zero;
        GameObject player = Instantiate(playerPrefab, spawnPos, Quaternion.identity);
        
        // 플레이어 컴포넌트가 있다면 데이터 적용
        // Player playerScript = player.GetComponent<Player>();
        // if (playerScript != null)
        // {
        //     playerScript.LoadFromSaveData(data);
        // }
        
        Debug.Log($"[GameLoader] 세이브 데이터 로드 완료: {data.currentScene}");
        
        // 사용 완료 후 초기화
        saveToLoad = null;
    }
    
    /// <summary>
    /// 씬 로드 (세이브 데이터 포함)
    /// </summary>
    public static void LoadScene(string sceneName, SaveData data = null)
    {
        saveToLoad = data;
        SceneManager.LoadScene(sceneName);
    }
}
