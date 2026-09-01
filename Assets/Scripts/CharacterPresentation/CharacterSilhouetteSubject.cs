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

        private static readonly int PixelGridAnchorId =
            Shader.PropertyToID("_CharacterPixelGridAnchorWS");

        private static int activeSubjectCount;

        private bool registered;
        private bool renderSnapApplied;
        private Camera snappedCamera;
        private Vector3 unsnappedPosition;
        private readonly HashSet<Renderer> ownedRenderers = new HashSet<Renderer>();
        private MaterialPropertyBlock propertyBlock;

        public static bool HasActiveSubject => activeSubjectCount > 0;

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

        [ContextMenu("Refresh Silhouette Renderers")]
        public void ApplyToChildRenderers()
        {
            Renderer[] renderers = GetComponentsInChildren<Renderer>(true);
            HashSet<Renderer> currentRenderers = new HashSet<Renderer>(renderers);

            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer != null && !currentRenderers.Contains(ownedRenderer))
                {
                    ownedRenderer.renderingLayerMask &= ~RenderingLayerMask;
                }
            }

            ownedRenderers.Clear();
            foreach (Renderer childRenderer in renderers)
            {
                childRenderer.renderingLayerMask |= RenderingLayerMask;
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

            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer == null)
                {
                    continue;
                }

                ownedRenderer.GetPropertyBlock(propertyBlock);
                propertyBlock.SetVector(PixelGridAnchorId, anchor);
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
                    ownedRenderer.renderingLayerMask &= ~RenderingLayerMask;
                }
            }

            ownedRenderers.Clear();
        }
    }
}
