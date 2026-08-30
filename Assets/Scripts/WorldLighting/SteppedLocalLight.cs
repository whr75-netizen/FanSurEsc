using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Defines one presentation-only local light. The renderer consumes these
    /// values without creating a Unity Light or mutating gameplay state.
    /// </summary>
    [DisallowMultipleComponent]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stepped Local Light")]
    public sealed class SteppedLocalLight : MonoBehaviour
    {
        private static readonly List<SteppedLocalLight> ActiveLights = new();

        [Tooltip("RGB controls the tint; alpha scales the additive light contribution.")]
        [SerializeField, ColorUsage(true, true)] private Color color =
            new Color(1f, 0.62f, 0.28f, 1f);
        [SerializeField, Min(0.01f)] private float radius = 4.5f;
        [SerializeField, Min(0f)] private float intensity = 1.15f;
        [SerializeField, Range(2, 16)] private int surfaceBands = 5;
        [SerializeField, Range(2, 16)] private int haloBands = 4;
        [SerializeField, Range(0f, 1f)] private float haloStrength = 0.18f;
        [SerializeField, Range(1f, 2f)] private float haloRadiusMultiplier = 1.25f;
        [SerializeField, Range(0f, 1f)] private float normalInfluence = 0.82f;
        [SerializeField, Min(0.01f)] private float worldCellSize = 0.12f;

        public Color Color => color;
        public float Radius => radius;
        public float Intensity => intensity;
        public int SurfaceBands => surfaceBands;
        public int HaloBands => haloBands;
        public float HaloStrength => haloStrength;
        public float HaloRadiusMultiplier => haloRadiusMultiplier;
        public float NormalInfluence => normalInfluence;
        public float WorldCellSize => worldCellSize;

        private void OnEnable()
        {
            if (!ActiveLights.Contains(this))
            {
                ActiveLights.Add(this);
            }
        }

        private void OnDisable()
        {
            ActiveLights.Remove(this);
        }

        private void OnValidate()
        {
            radius = Mathf.Max(0.01f, radius);
            intensity = Mathf.Max(0f, intensity);
            surfaceBands = Mathf.Clamp(surfaceBands, 2, 16);
            haloBands = Mathf.Clamp(haloBands, 2, 16);
            haloStrength = Mathf.Clamp01(haloStrength);
            haloRadiusMultiplier = Mathf.Clamp(haloRadiusMultiplier, 1f, 2f);
            normalInfluence = Mathf.Clamp01(normalInfluence);
            worldCellSize = Mathf.Max(0.01f, worldCellSize);
        }

        internal static int FillShaderData(
            Vector4[] positionsAndRadii,
            Vector4[] colorsAndIntensities,
            Vector4[] quantizationSettings,
            float[] worldCellSizes,
            float[] haloRadiusMultipliers,
            float[] selectionDistances,
            Camera camera,
            Plane[] frustumPlanes,
            Scene activeScene,
            Transform persistentGameplayRoot,
            int limit,
            out bool truncated)
        {
            for (int index = ActiveLights.Count - 1; index >= 0; index--)
            {
                if (ActiveLights[index] == null)
                {
                    ActiveLights.RemoveAt(index);
                }
            }

            int count = 0;
            int clampedLimit = Mathf.Min(limit, positionsAndRadii.Length);
            clampedLimit = Mathf.Min(clampedLimit, colorsAndIntensities.Length);
            clampedLimit = Mathf.Min(clampedLimit, quantizationSettings.Length);
            clampedLimit = Mathf.Min(clampedLimit, worldCellSizes.Length);
            clampedLimit = Mathf.Min(clampedLimit, haloRadiusMultipliers.Length);
            clampedLimit = Mathf.Min(clampedLimit, selectionDistances.Length);
            if (clampedLimit <= 0 ||
                camera == null ||
                frustumPlanes == null ||
                frustumPlanes.Length < 6)
            {
                truncated = false;
                return 0;
            }

            Vector3 cameraPosition = camera.transform.position;
            int eligibleCount = 0;
            for (int index = 0; index < ActiveLights.Count; index++)
            {
                SteppedLocalLight light = ActiveLights[index];
                bool belongsToPersistentGameplay =
                    persistentGameplayRoot != null &&
                    (light.transform == persistentGameplayRoot ||
                     light.transform.IsChildOf(persistentGameplayRoot));
                if (!light.isActiveAndEnabled ||
                    light.intensity <= 0f ||
                    light.color.a <= 0f ||
                    (light.gameObject.scene != activeScene &&
                     !belongsToPersistentGameplay))
                {
                    continue;
                }

                Vector3 position = light.transform.position;
                float influenceRadius = light.radius * light.haloRadiusMultiplier;
                Bounds influenceBounds = new Bounds(
                    position,
                    Vector3.one * (influenceRadius * 2f));
                if (!GeometryUtility.TestPlanesAABB(frustumPlanes, influenceBounds))
                {
                    continue;
                }

                eligibleCount++;
                float distanceSquared = (position - cameraPosition).sqrMagnitude;
                if (count >= clampedLimit &&
                    distanceSquared >= selectionDistances[clampedLimit - 1])
                {
                    continue;
                }

                int insertIndex = Mathf.Min(count, clampedLimit - 1);
                if (count < clampedLimit)
                {
                    count++;
                }

                while (insertIndex > 0 &&
                       distanceSquared < selectionDistances[insertIndex - 1])
                {
                    positionsAndRadii[insertIndex] = positionsAndRadii[insertIndex - 1];
                    colorsAndIntensities[insertIndex] =
                        colorsAndIntensities[insertIndex - 1];
                    quantizationSettings[insertIndex] =
                        quantizationSettings[insertIndex - 1];
                    worldCellSizes[insertIndex] = worldCellSizes[insertIndex - 1];
                    haloRadiusMultipliers[insertIndex] =
                        haloRadiusMultipliers[insertIndex - 1];
                    selectionDistances[insertIndex] =
                        selectionDistances[insertIndex - 1];
                    insertIndex--;
                }

                Color linearColor = light.color.linear;
                positionsAndRadii[insertIndex] = new Vector4(
                    position.x,
                    position.y,
                    position.z,
                    light.radius);
                colorsAndIntensities[insertIndex] = new Vector4(
                    linearColor.r,
                    linearColor.g,
                    linearColor.b,
                    light.intensity * Mathf.Clamp01(linearColor.a));
                quantizationSettings[insertIndex] = new Vector4(
                    light.surfaceBands,
                    light.haloBands,
                    light.haloStrength,
                    light.normalInfluence);
                worldCellSizes[insertIndex] = light.worldCellSize;
                haloRadiusMultipliers[insertIndex] = light.haloRadiusMultiplier;
                selectionDistances[insertIndex] = distanceSquared;
            }

            truncated = eligibleCount > clampedLimit;
            return count;
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(color.r, color.g, color.b, 0.65f);
            Gizmos.DrawWireSphere(transform.position, radius);
        }
    }
}
