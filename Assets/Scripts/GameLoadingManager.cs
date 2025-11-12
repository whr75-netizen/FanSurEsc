using UnityEngine;
using UnityEngine.SceneManagement;

public class GameLoadingManager : MonoBehaviour
{
    public LoadingTextAnimation textAnimation;

    private void Start()
    {
        StartCoroutine(LoadGameMapAsync());
    }

    private System.Collections.IEnumerator LoadGameMapAsync()
    {
        AsyncOperation asyncLoad = SceneManager.LoadSceneAsync("GameMap1");
        asyncLoad.allowSceneActivation = true;

        while (!asyncLoad.isDone)
        {
            float progress = Mathf.Clamp01(asyncLoad.progress / 0.9f);
            textAnimation.SetProgress(progress);
            yield return null;
        }
    }
}