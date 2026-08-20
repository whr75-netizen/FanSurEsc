using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class GameLoadingManager : MonoBehaviour
{
    public LoadingTextAnimation textAnimation;
    [SerializeField] private Slider progressSlider;

    private void Start()
    {
        StartCoroutine(LoadGameMapAsync());
    }

    private System.Collections.IEnumerator LoadGameMapAsync()
    {
        AsyncOperation asyncLoad = SceneManager.LoadSceneAsync("GameMap1");
        if (asyncLoad == null)
        {
            Debug.LogError("Could not start loading GameMap1.", this);
            yield break;
        }

        asyncLoad.allowSceneActivation = true;

        while (!asyncLoad.isDone)
        {
            float progress = Mathf.Clamp01(asyncLoad.progress / 0.9f);
            if (textAnimation != null)
            {
                textAnimation.SetProgress(progress);
            }

            if (progressSlider != null)
            {
                progressSlider.value = progress;
            }
            yield return null;
        }

        if (progressSlider != null)
        {
            progressSlider.value = 1f;
        }
    }
}
