using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Registers authored sprite surfaces with the existing building visibility owner.</summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(UrbanOcclusionFader))]
    public sealed class NativePixelBuilding : MonoBehaviour
    {
        public Bounds interior = new Bounds(new Vector3(0, 1.3f, 0), new Vector3(10, 3, 8));
        public Renderer[] frontWalls;
        public Collider[] frontColliders;
        public Renderer[] backWalls;
        public Collider[] backColliders;
        public Renderer[] roof;
        public Collider[] roofColliders;

        private void Start()
        {
            var fader = GetComponent<UrbanOcclusionFader>();
            fader.RegisterBuilding(transform, interior, null, null, frontWalls, frontColliders);
            // Rear walls remain visible inside, but still fade if their real collider hides the player outside.
            fader.RegisterBuilding(transform, interior, null, null, backWalls, backColliders, false);
            fader.RegisterStorey(transform, interior, 1, 2.45f, roof, roofColliders,
                System.Array.Empty<Renderer>(), System.Array.Empty<Collider>(),
                System.Array.Empty<Renderer>(), true);
        }
    }
}
