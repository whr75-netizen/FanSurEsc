using System;
using UnityEngine;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Marks one or more roof colliders as rain blockers. The colliders remain the
    /// geometry authority; the rain presentation only caches their top height.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class RainShelterOccluder : MonoBehaviour
    {
        [Tooltip("Non-trigger roof colliders. Empty uses colliders on this object and its children.")]
        [SerializeField] private Collider[] shelterColliders;

        internal static event Action<RainShelterOccluder> Registered;
        internal static event Action<RainShelterOccluder> Unregistered;
        internal static event Action<RainShelterOccluder> GeometryChanged;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticSignals()
        {
            Registered = null;
            Unregistered = null;
            GeometryChanged = null;
        }

        private void Awake()
        {
            CacheCollidersIfNeeded();
        }

        private void OnEnable()
        {
            CacheCollidersIfNeeded();
            Registered?.Invoke(this);
        }

        private void OnDisable()
        {
            Unregistered?.Invoke(this);
        }

        private void OnValidate()
        {
            if (Application.isPlaying)
            {
                GeometryChanged?.Invoke(this);
            }
        }

        public void NotifyGeometryChanged()
        {
            CacheCollidersIfNeeded();
            GeometryChanged?.Invoke(this);
        }

        internal void RasterizeTopHeights(
            float worldMinX,
            float worldMinZ,
            float cellSize,
            int resolution,
            float[] topHeights)
        {
            if (!isActiveAndEnabled)
            {
                return;
            }

            CacheCollidersIfNeeded();
            if (shelterColliders == null || topHeights == null)
            {
                return;
            }

            for (int colliderIndex = 0;
                 colliderIndex < shelterColliders.Length;
                 colliderIndex++)
            {
                Collider shelterCollider = shelterColliders[colliderIndex];
                if (shelterCollider == null ||
                    !shelterCollider.enabled ||
                    shelterCollider.isTrigger ||
                    !shelterCollider.gameObject.activeInHierarchy)
                {
                    continue;
                }

                Bounds bounds = shelterCollider.bounds;
                int minimumX = Mathf.Clamp(
                    Mathf.FloorToInt((bounds.min.x - worldMinX) / cellSize),
                    0,
                    resolution - 1);
                int maximumX = Mathf.Clamp(
                    Mathf.CeilToInt((bounds.max.x - worldMinX) / cellSize) - 1,
                    0,
                    resolution - 1);
                int minimumZ = Mathf.Clamp(
                    Mathf.FloorToInt((bounds.min.z - worldMinZ) / cellSize),
                    0,
                    resolution - 1);
                int maximumZ = Mathf.Clamp(
                    Mathf.CeilToInt((bounds.max.z - worldMinZ) / cellSize) - 1,
                    0,
                    resolution - 1);

                if (bounds.max.x < worldMinX ||
                    bounds.min.x > worldMinX + resolution * cellSize ||
                    bounds.max.z < worldMinZ ||
                    bounds.min.z > worldMinZ + resolution * cellSize)
                {
                    continue;
                }

                float rayStartY = bounds.max.y + 0.05f;
                float rayDistance = Mathf.Max(0.2f, bounds.size.y + 0.1f);
                for (int z = minimumZ; z <= maximumZ; z++)
                {
                    float worldZ = worldMinZ + (z + 0.5f) * cellSize;
                    for (int x = minimumX; x <= maximumX; x++)
                    {
                        float worldX = worldMinX + (x + 0.5f) * cellSize;
                        Ray ray = new Ray(
                            new Vector3(worldX, rayStartY, worldZ),
                            Vector3.down);
                        if (!shelterCollider.Raycast(ray, out RaycastHit hit, rayDistance))
                        {
                            continue;
                        }

                        int bufferIndex = z * resolution + x;
                        if (hit.point.y > topHeights[bufferIndex])
                        {
                            topHeights[bufferIndex] = hit.point.y;
                        }
                    }
                }
            }
        }

        internal bool TryRaycast(
            Ray ray,
            float maxDistance,
            out RaycastHit closestHit)
        {
            closestHit = default;
            if (!isActiveAndEnabled || maxDistance <= 0f)
            {
                return false;
            }

            CacheCollidersIfNeeded();
            if (shelterColliders == null)
            {
                return false;
            }

            bool foundHit = false;
            float closestDistance = maxDistance;
            for (int index = 0; index < shelterColliders.Length; index++)
            {
                Collider shelterCollider = shelterColliders[index];
                if (shelterCollider == null ||
                    !shelterCollider.enabled ||
                    shelterCollider.isTrigger ||
                    !shelterCollider.gameObject.activeInHierarchy ||
                    !shelterCollider.Raycast(ray, out RaycastHit hit, maxDistance) ||
                    hit.distance >= closestDistance)
                {
                    continue;
                }

                foundHit = true;
                closestDistance = hit.distance;
                closestHit = hit;
            }

            return foundHit;
        }

        private void CacheCollidersIfNeeded()
        {
            if (shelterColliders != null && shelterColliders.Length > 0)
            {
                return;
            }

            shelterColliders = GetComponentsInChildren<Collider>(true);
        }
    }
}
