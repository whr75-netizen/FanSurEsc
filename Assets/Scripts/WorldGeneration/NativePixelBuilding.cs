using System.Collections;
using FantasySurvival.SceneFlow;
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
        [Tooltip("Opt in only for a scene containing native sprites at this common density.")]
        public bool useNativePixelGrid;
        public float nativePixelsPerUnit = 22.627417f;
        [Tooltip("Zero preserves the existing camera size. A positive value selects native screen pixels per texel on entry.")]
        [Min(0)] public int initialNativeIntegerScale;
        private CameraZoomController nativeZoom;
        private Coroutine gridBinding;

        private void OnEnable()
        {
            if (useNativePixelGrid) gridBinding = StartCoroutine(BindNativeGrid());
        }

        private IEnumerator BindNativeGrid()
        {
            // Direct scene bootstrap may create the persistent shell after this building.
            while (PersistentGameplayShell.Instance == null ||
                   PersistentGameplayShell.Instance.PlayerCamera == null)
                yield return null;
            nativeZoom = PersistentGameplayShell.Instance.PlayerCamera.GetComponent<CameraZoomController>();
            if (nativeZoom != null) nativeZoom.SetNativePixelGrid(nativePixelsPerUnit, initialNativeIntegerScale);
            gridBinding = null;
        }

        private void OnDisable()
        {
            if (gridBinding != null) StopCoroutine(gridBinding);
            gridBinding = null;
            if (nativeZoom != null) nativeZoom.ClearNativePixelGrid();
            nativeZoom = null;
        }

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
