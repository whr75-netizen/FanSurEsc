using Unity.AI.Navigation;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>A catalogued fixed prop. Canonical geometry and its footprint share metres and a floor pivot.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(BoxCollider), typeof(NavMeshModifier))]
    public sealed class UrbanBuildingProp : MonoBehaviour
    {
        public string catalogId;
        [TextArea] public string placementNotes;
        public UrbanDecorationZone allowedZones;
        [Min(1)] public int maxPerBuilding = 1;
        public Vector3 physicalSize = Vector3.one;
        public bool metricMesh;
        public string StableId { get; private set; }
        public int SourceBuildingIndex { get; private set; } = -1;
        public bool Interior { get; private set; }

        public Vector3 PlacementSize
        {
            get
            {
                if (metricMesh) return physicalSize;
                // mesh.bounds is deliberately enlarged for GPU billboard culling; use the real vertices.
                var filter = GetComponentInChildren<MeshFilter>();
                float width = 0;
                foreach (Vector3 vertex in filter.sharedMesh.vertices)
                    width = Mathf.Max(width, Mathf.Abs(vertex.x) * 2);
                return new Vector3(Mathf.Max(physicalSize.x, width), physicalSize.y,
                    Mathf.Max(physicalSize.z, width));
            }
        }

        public bool TryValidate(out string error)
        {
            if (string.IsNullOrWhiteSpace(catalogId) || allowedZones == 0 || maxPerBuilding < 1 ||
                !Positive(physicalSize.x) || !Positive(physicalSize.y) || !Positive(physicalSize.z) ||
                transform.localScale != Vector3.one || GetComponentInChildren<MeshRenderer>() == null ||
                !(metricMesh ? HasCanonicalVolume() : HasCanonicalCard()))
            {
                error = "Building prop needs identity, zones, positive metres, unit scale, and geometry inside its canonical footprint.";
                return false;
            }
            error = null;
            return true;
        }

        public void ApplyPlacement(UrbanBuildingDecorationPlacement placement)
        {
            StableId = placement.StableId;
            SourceBuildingIndex = placement.SourceBuildingIndex;
            Interior = placement.Interior;
            // The immutable snapshot is authoritative even if authoring data later changes.
            physicalSize = placement.PhysicalSize;
            var box = GetComponent<BoxCollider>();
            box.center = Vector3.up * physicalSize.y * .5f;
            box.size = physicalSize;
            box.isTrigger = false;
            var modifier = GetComponent<NavMeshModifier>();
            modifier.overrideArea = true;
            modifier.area = 1;
            gameObject.tag = "Obstacle";
        }

        private static bool Positive(float value) => !float.IsNaN(value) && !float.IsInfinity(value) && value > 0;

        private bool HasCanonicalVolume()
        {
            MeshFilter[] filters = GetComponentsInChildren<MeshFilter>(true);
            if (filters.Length == 0) return false;
            const float tolerance = .001f;
            bool hasVolume = false;
            foreach (MeshFilter filter in filters)
            {
                if (filter.sharedMesh == null) return false;
                Matrix4x4 toRoot = transform.worldToLocalMatrix * filter.transform.localToWorldMatrix;
                foreach (Vector3 vertex in filter.sharedMesh.vertices)
                {
                    Vector3 p = toRoot.MultiplyPoint3x4(vertex);
                    if (!float.IsFinite(p.x) || !float.IsFinite(p.y) || !float.IsFinite(p.z) ||
                        Mathf.Abs(p.x) > physicalSize.x*.5f+tolerance || p.y < -tolerance ||
                        p.y > physicalSize.y+tolerance || Mathf.Abs(p.z) > physicalSize.z*.5f+tolerance) return false;
                    hasVolume |= Mathf.Abs(p.z) > tolerance;
                }
            }
            return hasVolume;
        }

        private bool HasCanonicalCard()
        {
            var filter = GetComponentInChildren<MeshFilter>();
            if (filter == null || filter.sharedMesh == null || filter.transform.parent != transform ||
                filter.transform.localPosition != Vector3.zero || filter.transform.localScale != Vector3.one ||
                Quaternion.Angle(filter.transform.localRotation, Quaternion.identity) > .001f) return false;
            foreach (Vector3 vertex in filter.sharedMesh.vertices)
                if (!float.IsFinite(vertex.x) || !float.IsFinite(vertex.y) || !float.IsFinite(vertex.z) ||
                    Mathf.Abs(vertex.z) > .001f || vertex.y < 0 || vertex.y > physicalSize.y + .001f) return false;
            return true;
        }
    }
}
