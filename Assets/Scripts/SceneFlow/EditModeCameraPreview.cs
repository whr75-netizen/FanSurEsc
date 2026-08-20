using UnityEngine;

namespace FantasySurvival.SceneFlow
{
    /// <summary>
    /// Keeps an authoring-only Camera visible in Edit Mode while ensuring it
    /// never participates in gameplay. The Camera lives on a child object so
    /// the active root can restore it after leaving Play Mode, even when Scene
    /// Reload is disabled.
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(-12000)]
    [DisallowMultipleComponent]
    public sealed class EditModeCameraPreview : MonoBehaviour
    {
        [SerializeField] private GameObject previewCameraObject;

        private void Awake()
        {
            RefreshState();
        }

        private void OnEnable()
        {
            RefreshState();
        }

        private void OnValidate()
        {
            RefreshState();
        }

        private void Update()
        {
            RefreshState();
        }

        private void RefreshState()
        {
            if (previewCameraObject == null)
            {
                return;
            }

            bool shouldBeActive = !Application.isPlaying;
            if (previewCameraObject.activeSelf != shouldBeActive)
            {
                previewCameraObject.SetActive(shouldBeActive);
            }
        }
    }
}
