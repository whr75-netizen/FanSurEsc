using UnityEngine;

namespace FantasySurvival.SceneFlow
{
    [DisallowMultipleComponent]
    public sealed class SceneSpawnPoint : MonoBehaviour
    {
        [SerializeField] private string spawnId = "Default";

        public string SpawnId => spawnId;

        private void OnDrawGizmos()
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireCube(transform.position, new Vector3(0.8f, 1f, 0.8f));
            Gizmos.DrawLine(transform.position, transform.position + transform.forward * 1.5f);
        }
    }
}
