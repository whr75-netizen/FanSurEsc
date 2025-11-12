using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public float speed = 5f;
    public Vector3 checkSize = new Vector3(0.5f, 0.5f, 0.5f);

    void Update()
    {
        float moveX = Input.GetAxisRaw("Horizontal");
        float moveZ = Input.GetAxisRaw("Vertical");
        Vector3 movement = new Vector3(moveX, 0, moveZ).normalized * speed * Time.deltaTime;

        Vector3 nextPosition = transform.position;
        if (moveX != 0 && !IsColliding(new Vector3(movement.x, 0, 0)))
        {
            nextPosition.x += movement.x;
        }
        if (moveZ != 0 && !IsColliding(new Vector3(0, 0, movement.z)))
        {
            nextPosition.z += movement.z;
        }
        transform.position = nextPosition;
    }

    bool IsColliding(Vector3 movement)
    {
        Vector3 nextPosition = transform.position + movement;
        Collider[] obstacles = Physics.OverlapBox(nextPosition, checkSize, Quaternion.identity);
        foreach (Collider obstacle in obstacles)
        {
            if (obstacle.CompareTag("Obstacle"))
            {
                return true;
            }
        }
        return false;
    }
}