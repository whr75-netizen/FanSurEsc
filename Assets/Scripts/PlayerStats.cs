using UnityEngine;
using UnityEngine.UI;

public class PlayerStats : MonoBehaviour
{
    public Slider healthBar; // Inspector에서 연결
    private float health = 100f;

    void Update()
    {
        // 테스트용: H 누르면 체력 감소
        if (Input.GetKeyDown(KeyCode.H))
        {
            health -= 10f;
            healthBar.value = health;
            Debug.Log("체력: " + health);
        }
    }
}