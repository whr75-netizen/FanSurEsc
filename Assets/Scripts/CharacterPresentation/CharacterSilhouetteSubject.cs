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
        public const uint PixelCellRenderingLayerMask = 1u << 28;

        public enum OutlineGroup
        {
            Combined = 0,
            Eyes = 1,
            Eyebrows = 2,
            Hair = 3,
            Skin = 4
        }

        [System.Serializable]
        public struct RendererOutlineGroup
        {
            public Renderer renderer;
            public OutlineGroup outlineGroup;
        }

        [SerializeField]
        [Tooltip("Quantize the already-lit visible character color in screen space. " +
            "The screen path supplies its own matching one-cell silhouette outline.")]
        private bool screenSpacePixelColor;

        [SerializeField]
        [Tooltip("Render this subject only through the isolated pixel-cell surface path.")]
        private bool pixelCellSurface;

        [SerializeField, Range(1, 8)]
        private int pixelCellSize = 2;

        [SerializeField]
        [Tooltip("Optional explicit groups on this presentation root. Unmapped renderers keep " +
            "the combined outline. At a group boundary only the higher ID side receives ink: " +
            "Eyes 1, Eyebrows 2, Hair 3, Skin 4. Screen-pixel color subjects ignore this mapping.")]
        private RendererOutlineGroup[] outlineGroups = System.Array.Empty<RendererOutlineGroup>();

        private static readonly int PixelGridAnchorId =
            Shader.PropertyToID("_CharacterPixelGridAnchorWS");
        private static readonly int LightingPositionOffsetId =
            Shader.PropertyToID("_CharacterLightingPositionOffsetWS");
        private static readonly int OutlineGroupId =
            Shader.PropertyToID("_CharacterOutlineGroup");
        private static readonly int CellSurfaceId = Shader.PropertyToID("_CharacterCellSurface");
        private static readonly int CellSizeId = Shader.PropertyToID("_CharacterCellSize");
        private static readonly int CellSubjectId = Shader.PropertyToID("_CharacterCellSubjectId");

        private static int activeSubjectCount;
        private static int activeScreenPixelSubjectCount;
        private static readonly HashSet<CharacterSilhouetteSubject> activeSubjects =
            new HashSet<CharacterSilhouetteSubject>();
        private static int nextCellSubjectId = 1;

        private bool registered;
        private int pixelCellSubjectId;
        private bool screenPixelRegistered;
        private bool renderSnapApplied;
        private Camera snappedCamera;
        private Vector3 unsnappedPosition;
        private readonly HashSet<Renderer> ownedRenderers = new HashSet<Renderer>();
        private readonly Dictionary<Renderer, int> rendererOutlineGroups = new Dictionary<Renderer, int>();
        private MaterialPropertyBlock propertyBlock;

        public static bool HasActiveSubject => activeSubjectCount > 0;
        public static bool HasActiveScreenPixelSubject =>
            activeScreenPixelSubjectCount > 0;
        public bool ScreenSpacePixelColor => screenSpacePixelColor;
        public bool PixelCellSurface => pixelCellSurface;
        public int PixelCellSize => pixelCellSize;
        public static bool HasActivePixelCellSubject => MaximumPixelCellSize > 0;
        public static int MaximumPixelCellSize
        {
            get
            {
                int maximum = 0;
                foreach (CharacterSilhouetteSubject subject in activeSubjects)
                {
                    if (subject != null && subject.isActiveAndEnabled && subject.pixelCellSurface)
                        maximum = Mathf.Max(maximum, Mathf.Clamp(subject.pixelCellSize, 1, 8));
                }
                return maximum;
            }
        }

        private void OnEnable()
        {
            if (propertyBlock == null)
            {
                propertyBlock = new MaterialPropertyBlock();
            }

            pixelCellSubjectId = AllocateCellSubjectId();
            if (!registered)
            {
                activeSubjectCount++;
                registered = true;
            }

            activeSubjects.Add(this);
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
            activeSubjects.Remove(this);
            pixelCellSubjectId = 0;

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
            pixelCellSize = Mathf.Clamp(pixelCellSize, 1, 8);
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

        public void SetPixelCellSize(int pixelSize)
        {
            int clampedSize = Mathf.Clamp(pixelSize, 1, 8);
            if (pixelCellSize == clampedSize)
                return;

            pixelCellSize = clampedSize;
            if (isActiveAndEnabled)
                ApplyPixelGridAnchor(transform.position);
        }

        private static int AllocateCellSubjectId()
        {
            // Transient render identity only; released on disable and never saved.
            for (int attempt = 0; attempt < ushort.MaxValue; attempt++)
            {
                int candidate = nextCellSubjectId;
                nextCellSubjectId = candidate == ushort.MaxValue ? 1 : candidate + 1;
                bool inUse = false;
                foreach (CharacterSilhouetteSubject subject in activeSubjects)
                {
                    if (subject != null && subject.pixelCellSubjectId == candidate)
                    {
                        inUse = true;
                        break;
                    }
                }
                if (!inUse)
                    return candidate;
            }
            throw new System.InvalidOperationException("All 65535 character cell subject IDs are in use.");
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
                    ClearOutlineGroup(ownedRenderer);
                    ownedRenderer.renderingLayerMask &=
                        ~(RenderingLayerMask |
                            ScreenPixelRenderingLayerMask |
                            ClassicOutlineRenderingLayerMask |
                            PixelCellRenderingLayerMask);
                }
            }

            rendererOutlineGroups.Clear();
            if (outlineGroups != null)
            {
                foreach (RendererOutlineGroup mapping in outlineGroups)
                {
                    if (mapping.renderer != null && currentRenderers.Contains(mapping.renderer))
                    {
                        rendererOutlineGroups[mapping.renderer] = Mathf.Clamp((int)mapping.outlineGroup, 0, 4);
                    }
                }
            }

            ownedRenderers.Clear();
            foreach (Renderer childRenderer in renderers)
            {
                // Bit 31 remains the shared character marker used by local
                // lighting. Each subject uses exactly one presentation path.
                childRenderer.renderingLayerMask |= RenderingLayerMask;
                childRenderer.renderingLayerMask &= ~(ScreenPixelRenderingLayerMask |
                    ClassicOutlineRenderingLayerMask | PixelCellRenderingLayerMask);
                if (pixelCellSurface)
                {
                    childRenderer.renderingLayerMask |= PixelCellRenderingLayerMask;
                }
                else if (screenSpacePixelColor)
                {
                    childRenderer.renderingLayerMask |= ScreenPixelRenderingLayerMask;
                }
                else
                {
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
                int outlineGroup = 0;
                if (!screenSpacePixelColor || pixelCellSurface)
                    rendererOutlineGroups.TryGetValue(ownedRenderer, out outlineGroup);
                propertyBlock.SetFloat(OutlineGroupId, outlineGroup);
                propertyBlock.SetFloat(CellSurfaceId, pixelCellSurface ? 1f : 0f);
                propertyBlock.SetFloat(CellSizeId, Mathf.Clamp(pixelCellSize, 1, 8));
                propertyBlock.SetFloat(CellSubjectId, pixelCellSubjectId);
                ownedRenderer.SetPropertyBlock(propertyBlock);
                propertyBlock.Clear();
            }
        }

        private void ClearOutlineGroup(Renderer childRenderer)
        {
            if (propertyBlock == null)
                propertyBlock = new MaterialPropertyBlock();
            childRenderer.GetPropertyBlock(propertyBlock);
            propertyBlock.SetFloat(OutlineGroupId, 0f);
            propertyBlock.SetFloat(CellSurfaceId, 0f);
            propertyBlock.SetFloat(CellSizeId, 0f);
            propertyBlock.SetFloat(CellSubjectId, 0f);
            childRenderer.SetPropertyBlock(propertyBlock);
            propertyBlock.Clear();
        }

        private void ReleaseChildRenderers()
        {
            foreach (Renderer ownedRenderer in ownedRenderers)
            {
                if (ownedRenderer != null)
                {
                    ClearOutlineGroup(ownedRenderer);
                    ownedRenderer.renderingLayerMask &=
                        ~(RenderingLayerMask |
                            ScreenPixelRenderingLayerMask |
                            ClassicOutlineRenderingLayerMask |
                            PixelCellRenderingLayerMask);
                }
            }

            ownedRenderers.Clear();
            rendererOutlineGroups.Clear();
        }

        private void SynchronizeScreenPixelRegistration()
        {
            bool shouldRegister = screenSpacePixelColor && !pixelCellSurface && isActiveAndEnabled;
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
