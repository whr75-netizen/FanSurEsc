using UnityEngine;
using TMPro;

public class LoadingTextAnimation : MonoBehaviour
{
    public TextMeshProUGUI loadingText;
    private float timer = 0f;
    private int dotCount = 0;

    // 진행률을 외부에서 받을 변수
    public void SetProgress(float progress)
    {
        loadingText.text = "Loading" + new string('.', dotCount) + " " + Mathf.Round(progress * 100) + "%";
    }

    void Update()
    {
        timer += Time.deltaTime;
        if (timer >= 0.5f)
        {
            dotCount = (dotCount + 1) % 4;
            timer = 0f;
        }
    }
}