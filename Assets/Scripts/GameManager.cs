using UnityEngine;

public class GameManager : MonoBehaviour
{
    // 싱글톤 인스턴스
    public static GameManager Instance { get; private set; }

    // 추가 전역 데이터 (필요 시 확장)
    [SerializeField] private int playerLevel = 1;
    [SerializeField] private bool isSoundOn = true;

    void Awake()
    {
        // 싱글톤 설정
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject); // 씬 전환 시 유지
        }
        else if (Instance != this)
        {
            Destroy(gameObject); // 중복 방지
        }
    }

    // 전역 데이터 getter/setter (예시)
    public int PlayerLevel
    {
        get => playerLevel;
        set => playerLevel = value;
    }

    public bool IsSoundOn
    {
        get => isSoundOn;
        set => isSoundOn = value;
    }

    public void Initialize()
    {
        Debug.Log("GameManager 초기화 완료");
    }
}