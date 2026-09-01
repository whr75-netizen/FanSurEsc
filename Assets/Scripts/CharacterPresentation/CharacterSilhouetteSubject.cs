using System.Collections.Generic;
using UnityEngine;

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

        private static int activeSubjectCount;

        private bool registered;
        private readonly HashSet<Renderer> ownedRenderers = new HashSet<Renderer>();

        public static bool HasActiveSubject => activeSubjectCount > 0;

        private void OnEnable()
        {
            if (!registered)
            {
                activeSubjectCount++;
                registered = true;
            }

            ApplyToChildRenderers();
        }

        private void OnDisable()
        {
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
