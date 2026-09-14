using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Applies the map's initial view and restores the same camera when the map leaves.</summary>
    [DefaultExecutionOrder(100)]
    [DisallowMultipleComponent]
    public sealed class IsometricUrbanView : MonoBehaviour
    {
        public float cityYaw;

        private Camera boundCamera;
        private CameraFollow boundFollow;
        private Quaternion originalRotation;
        private Vector3 originalOffset;
        private bool originalOrthographic;
        private bool applied;

        private void LateUpdate()
        {
            if (applied)
                return;

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell == null || shell.PlayerCamera == null || shell.PlayerTransform == null)
                return;

            if (boundCamera != shell.PlayerCamera)
            {
                boundCamera = shell.PlayerCamera;
                boundFollow = boundCamera.GetComponent<CameraFollow>();
            }
            if (boundFollow == null)
                return;

            originalRotation = boundCamera.transform.rotation;
            originalOffset = boundFollow.offset;
            originalOrthographic = boundCamera.orthographic;
            boundCamera.orthographic = true;
            boundFollow.SetViewOrientation(Quaternion.Euler(30f, cityYaw + 45f, 0f));
            applied = true;
        }

        private void OnDisable()
        {
            if (applied && boundCamera != null && boundFollow != null &&
                boundFollow.gameObject == boundCamera.gameObject)
            {
                boundFollow.RestoreViewOrientation(originalRotation, originalOffset);
                boundCamera.orthographic = originalOrthographic;
            }
            applied = false;
            boundCamera = null;
            boundFollow = null;
        }
    }
}
