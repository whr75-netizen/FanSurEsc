using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenuManager : MonoBehaviour
{
    public void StartGame()
    {
        SceneManager.LoadScene("GameLoadingScene"); // 게임 로딩으로 이동
    }

    public void QuitGame()
    {
        Application.Quit();
    }
}