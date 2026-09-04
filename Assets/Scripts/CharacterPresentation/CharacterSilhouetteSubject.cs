using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.CharacterPresentation
{
    /// <summary>
    /// Marks this hierarchy as a character-silhouette source without moving it to a
    /// gameplay physics layer. The renderer feature filters this dedicated rendering
    /// layer bit, so selection, collision, raycasts, and AI masks remain unchanged.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class CharacterSilhouetteSubject : MonoBehaviour
    {
        public const uint RenderingLayerMask = 1u << 31;
        public const uint ScreenPixelRenderingLayerMask = 1u << 30;
        public const uint ClassicOutlineRenderingLayerMask = 1u << 29;

        [SerializeField]
        [Tooltip("Quantize the already-lit visible character color in screen space. " +
            "The screen path supplies its own matching one-cell silhouette outline.")]
        private bool screenSpacePixelColor;

        private static readonly int PixelGridAnchorId =
            Shader.PropertyToID("_CharacterPixelGridAnchorWS");
        private static readonly int LightingPositionOffsetId =
            Shader.PropertyToID("_CharacterLightingPositionOffsetWS");

        private static int activeSubjectCount;
        private static int activeScreenPixelSubjectCount;

        private bool registered;
        private bool screenPixelRegistered;
        private bool renderSnapApplied;
        private Camera snappedCamera;
        private Vector3 unsnappedPosition;
        private readonly HashSet<Renderer> ownedRenderers = new HashSet<Renderer>();
        private MaterialPropertyBlock propertyBlock;

        public static bool HasActiveSubject => activeSubjectCount > 0;
        public static bool HasActiveScreenPixelSubject =>
            activeScreenPixelSubjectCount > 0;

        public bool ScreenSpacePixelColor => screenSpacePixelColor;

        private void OnEnable()
        {
            if (propertyBlock == null)
            {
                propertyBlock = new MaterialPropertyBlock();
            }

            if (!registered)
            {
                activeSubjectCount++;
                registered = true;
            }

            SynchronizeScreenPixelRegistration();
            ApplyToChildRenderers();
            RenderPipelineManager.beginCameraRendering += BeginCameraRendering;
            RenderPipelineManager.endCameraRendering += EndCameraRendering;
        }

        private void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= BeginCameraRendering;
            RenderPipelineManager.endCameraRendering -= EndCameraRendering;
            RestoreRenderPosition();
            ReleaseChildRenderers();

            if (screenPixelRegistered)
            {
                activeScreenPixelSubjectCount = Mathf.Max(
                    0,
                    activeScreenPixelSubjectCount - 1);
                screenPixelRegistered = false;
            }

            if (!registered)
            {
                return;
            }

            activeSubjectCount = Mathf.Max(0, activeSubjectCount - 1);
            registered = false;
        }

        private void OnTransformChildrenChanged()
        {
            ApplyToChildRenderers();
        }

        private void OnValidate()
        {
            if (!isActiveAndEnabled)
            {
                return;
            }

            SynchronizeScreenPixelRegistration();
            ApplyToChildRenderers();
        }

        public void SetScreenSpacePixelColor(bool enabled)
        {
            if (screenSpacePixelColor == enabled)
            {
                return;
            }

            screenSpacePixelColor = enabled;
            if (!isActiveAndEnabled)
            {
                return;
            }

            SynchronizeScreenPixelRegistration();
            ApplyToChildRenderers();
        }

        [ContextMenu("Refresh Silhouette Renderers")]
        public void ApplyToChildRenderers()
        {
            Renderer[] renderers = GetComponentsInChildren<Renderer>(true);
            HashSet<Renderer> currentRenderers = new HashSet<Renderer>(renderers);

            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer != null && !currentRenderers.Contains(ownedRenderer))
                {
                    ownedRenderer.renderingLayerMask &=
                        ~(RenderingLayerMask |
                            ScreenPixelRenderingLayerMask |
                            ClassicOutlineRenderingLayerMask);
                }
            }

            ownedRenderers.Clear();
            foreach (Renderer childRenderer in renderers)
            {
                // Bit 31 remains the shared character marker used by local
                // lighting. The two outline presentation paths are exclusive,
                // so a screen-pixel subject cannot receive both outlines.
                childRenderer.renderingLayerMask |= RenderingLayerMask;
                if (screenSpacePixelColor)
                {
                    childRenderer.renderingLayerMask |= ScreenPixelRenderingLayerMask;
                    childRenderer.renderingLayerMask &=
                        ~ClassicOutlineRenderingLayerMask;
                }
                else
                {
                    childRenderer.renderingLayerMask &= ~ScreenPixelRenderingLayerMask;
                    childRenderer.renderingLayerMask |=
                        ClassicOutlineRenderingLayerMask;
                }

                ownedRenderers.Add(childRenderer);
            }

            ApplyPixelGridAnchor(transform.position);
        }

        private void BeginCameraRendering(
            ScriptableRenderContext context,
            Camera camera)
        {
            if (!Application.isPlaying ||
                camera == null ||
                camera.cameraType != CameraType.Game ||
                !camera.orthographic)
            {
                return;
            }

            // The component belongs on the presentation root. Gameplay movement,
            // collision, AI, and persistence stay on an unsnapped parent/root.
            RestoreRenderPosition();

            Vector3 anchorPosition = transform.position;
            Vector3 viewportPosition = camera.WorldToViewportPoint(anchorPosition);
            if (viewportPosition.z <= 0f)
            {
                ApplyPixelGridAnchor(anchorPosition);
                return;
            }

            float renderScale = UniversalRenderPipeline.asset != null
                ? UniversalRenderPipeline.asset.renderScale
                : 1f;
            int renderWidth = Mathf.Max(
                1,
                Mathf.FloorToInt(camera.pixelWidth * renderScale));
            int renderHeight = Mathf.Max(
                1,
                Mathf.FloorToInt(camera.pixelHeight * renderScale));
            viewportPosition.x = SnapViewportCoordinate(
                viewportPosition.x,
                renderWidth);
            viewportPosition.y = SnapViewportCoordinate(
                viewportPosition.y,
                renderHeight);

            Vector3 snappedAnchorPosition = camera.ViewportToWorldPoint(viewportPosition);
            unsnappedPosition = anchorPosition;
            transform.position += snappedAnchorPosition - anchorPosition;
            snappedCamera = camera;
            renderSnapApplied = true;

            ApplyPixelGridAnchor(transform.position);
        }

        private void EndCameraRendering(
            ScriptableRenderContext context,
            Camera camera)
        {
            if (renderSnapApplied && snappedCamera == camera)
            {
                RestoreRenderPosition();
            }
        }

        private static float SnapViewportCoordinate(
            float viewportCoordinate,
            int renderResolution)
        {
            float renderPixelCoordinate = viewportCoordinate * renderResolution;
            float snappedPixelCenter = Mathf.Round(renderPixelCoordinate - 0.5f) + 0.5f;
            return snappedPixelCenter / renderResolution;
        }

        private void RestoreRenderPosition()
        {
            if (!renderSnapApplied)
            {
                return;
            }

            transform.position = unsnappedPosition;
            snappedCamera = null;
            renderSnapApplied = false;
            ApplyPixelGridAnchor(transform.position);
        }

        private void ApplyPixelGridAnchor(Vector3 anchorPosition)
        {
            if (propertyBlock == null)
            {
                propertyBlock = new MaterialPropertyBlock();
            }

            Vector4 anchor = new Vector4(
                anchorPosition.x,
                anchorPosition.y,
                anchorPosition.z,
                1f);
            // Every fragment keeps its own spatial light position. Only undo
            // the temporary presentation-root snap, so camera motion cannot
            // shift the character through a shadow, cookie, or light band.
            Vector3 lightingPositionOffset = renderSnapApplied
                ? unsnappedPosition - anchorPosition
                : Vector3.zero;
            Vector4 lightingOffset = new Vector4(
                lightingPositionOffset.x,
                lightingPositionOffset.y,
                lightingPositionOffset.z,
                0f);

            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer == null)
                {
                    continue;
                }

                ownedRenderer.GetPropertyBlock(propertyBlock);
                propertyBlock.SetVector(PixelGridAnchorId, anchor);
                propertyBlock.SetVector(LightingPositionOffsetId, lightingOffset);
                ownedRenderer.SetPropertyBlock(propertyBlock);
                propertyBlock.Clear();
            }
        }

        private void ReleaseChildRenderers()
        {
            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer != null)
                {
                    ownedRenderer.renderingLayerMask &=
                        ~(RenderingLayerMask |
                            ScreenPixelRenderingLayerMask |
                            ClassicOutlineRenderingLayerMask);
                }
            }

            ownedRenderers.Clear();
        }

        private void SynchronizeScreenPixelRegistration()
        {
            bool shouldRegister = screenSpacePixelColor && isActiveAndEnabled;
            if (shouldRegister == screenPixelRegistered)
            {
                return;
            }

            activeScreenPixelSubjectCount += shouldRegister ? 1 : -1;
            activeScreenPixelSubjectCount = Mathf.Max(
                0,
                activeScreenPixelSubjectCount);
            screenPixelRegistered = shouldRegister;
        }
    }
}
