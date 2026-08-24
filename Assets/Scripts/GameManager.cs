using FantasySurvival.BaseBuilding;
using UnityEngine;

public class GameManager : MonoBehaviour
{
    // 싱글톤 인스턴스
    public static GameManager Instance { get; private set; }

    // 추가 전역 데이터 (필요 시 확장)
    [SerializeField] private int playerLevel = 1;
    [SerializeField] private bool isSoundOn = true;

    private BaseFurnitureStateStore baseFurnitureState;

    public BaseFurnitureStateStore BaseFurnitureState =>
        baseFurnitureState ??= new BaseFurnitureStateStore();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStaticState()
    {
        Instance = null;
    }

    void Awake()
    {
        // 싱글톤 설정
        if (Instance == null)
        {
            Instance = this;
            baseFurnitureState = new BaseFurnitureStateStore();
            DontDestroyOnLoad(gameObject); // 씬 전환 시 유지
        }
        else if (Instance != this)
        {
            Destroy(gameObject); // 중복 방지
        }
    }

    private void OnDestroy()
    {
        if (Instance == this)
        {
            Instance = null;
        }
    }

    public bool CanReplaceBaseFurnitureState(out string error)
    {
        if (BaseFurnitureState.HasActiveBindings)
        {
            error = "Base furniture state cannot be replaced while scene furniture is still bound.";
            return false;
        }

        error = null;
        return true;
    }

    public bool TryReplaceBaseFurnitureState(
        BaseFurnitureStateStore replacement,
        out string error)
    {
        if (replacement == null)
        {
            error = "Replacement base furniture state is missing.";
            return false;
        }

        if (!CanReplaceBaseFurnitureState(out error))
        {
            return false;
        }

        baseFurnitureState = replacement;
        error = null;
        return true;
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
