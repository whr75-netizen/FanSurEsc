using UnityEngine;
using UnityEngine.SceneManagement;

public class InitialLoadingManager : MonoBehaviour
{
    public LoadingTextAnimation textAnimation; // Inspector에서 연결

    private void Start()
    {
        StartCoroutine(LoadMainMenuAsync());
    }

    private System.Collections.IEnumerator LoadMainMenuAsync()
    {
        AsyncOperation asyncLoad = SceneManager.LoadSceneAsync("MainMenuScene");
        asyncLoad.allowSceneActivation = true;

        while (!asyncLoad.isDone)
        {
            float progress = Mathf.Clamp01(asyncLoad.progress / 0.9f);
            textAnimation.SetProgress(progress); // 텍스트에 진행률 전달
            yield return null;
        }
    }
}