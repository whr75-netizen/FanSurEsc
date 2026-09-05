using UnityEngine;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Authoring inputs for a baked batch of anchored foliage cards. The mesh is
    /// rebuilt explicitly in the Editor; runtime animation belongs to the shader.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public sealed class PixelFoliagePatch : MonoBehaviour
    {
        public enum PatchKind { Grass, Leaves }

        [SerializeField] private PatchKind kind;
        [SerializeField] private int seed = 1979;
        [SerializeField, Range(1, 4000)] private int count = 280;
        [Tooltip("Grass footprint in local X/Z metres.")]
        [SerializeField] private Vector2 area = new Vector2(6f, 4f);
        [Tooltip("Grass height or leaf-card size in world metres at unit scale.")]
        [SerializeField] private Vector2 sizeRange = new Vector2(0.35f, 0.65f);
        [Tooltip("Leaf anchors are baked onto these local ellipsoids.")]
        [SerializeField] private Vector3[] crownCenters = { new Vector3(0f, 3f, 0f) };
        [SerializeField] private Vector3[] crownRadii = { new Vector3(1.8f, 1.3f, 1.6f) };

        public PatchKind Kind => kind;
        public int Seed => seed;
        public int Count => count;
        public Vector2 Area => area;
        public Vector2 SizeRange => sizeRange;
        public Vector3[] CrownCenters => (Vector3[])crownCenters.Clone();
        public Vector3[] CrownRadii => (Vector3[])crownRadii.Clone();
    }
}
