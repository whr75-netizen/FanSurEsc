using UnityEngine;

public class PauseMenu : MonoBehaviour
{
    public GameObject pauseCanvas; // Inspector에서 연결

    void Start()
    {
        pauseCanvas.SetActive(false); // 처음엔 안 보이게
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            pauseCanvas.SetActive(!pauseCanvas.activeSelf); // 토글
        }
    }

    public void QuitGame()
    {
        Application.Quit(); // 게임 종료
        Debug.Log("게임 종료 버튼 눌림"); // 에디터 테스트용
    }
}