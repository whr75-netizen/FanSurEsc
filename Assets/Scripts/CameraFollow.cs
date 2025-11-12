using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    public Transform target; // 캐릭터 위치
    public Vector3 offset = new Vector3(0, 10, -5); // 카메라와 캐릭터 간 거리

    void LateUpdate()
    {
        if (target != null)
        {
            // 캐릭터 위치에 오프셋 더해서 카메라 위치 설정
            transform.position = target.position + offset;
        }
    }
}