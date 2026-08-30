using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Opts one Spot Light into the shared atmospheric shaft presentation.
    /// This component owns no light state and only describes the downward
    /// presentation volume used by dedicated lamps and similar fixtures.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Light))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stylized Light Shaft Emitter")]
    public sealed class StylizedLightShaftEmitter : MonoBehaviour
    {
        private static readonly List<StylizedLightShaftEmitter> ActiveEmitters = new();

        [SerializeField] private Light sourceLight;
        [SerializeField, Min(0.05f)] private float length = 4.6f;
        [SerializeField, Range(0.1f, 1.25f)] private float coneRadiusScale = 0.92f;
        [SerializeField, Min(0f)] private float intensityMultiplier = 0.075f;
        [SerializeField, Range(2, 8)] private int densityBands = 4;
        [SerializeField, Range(0f, 1f)] private float noiseStrength = 0.12f;
        [SerializeField, Min(0.01f)] private float worldCellSize = 0.12f;

        internal Light SourceLight => sourceLight;
        internal Vector3 OriginWorld =>
            sourceLight != null ? sourceLight.transform.position : transform.position;
        internal float Length => length;
        internal float EndRadius
        {
            get
            {
                float spotAngle = sourceLight != null && sourceLight.type == LightType.Spot
                    ? sourceLight.spotAngle
                    : 60f;
                float halfAngleRadians = Mathf.Clamp(spotAngle * 0.5f, 1f, 89f) *
                                         Mathf.Deg2Rad;
                return Mathf.Max(
                    0.02f,
                    Mathf.Tan(halfAngleRadians) * length * coneRadiusScale);
            }
        }
        internal float IntensityMultiplier => intensityMultiplier;
        internal int DensityBands => densityBands;
        internal float NoiseStrength => noiseStrength;
        internal float WorldCellSize => worldCellSize;
        internal Vector3 DirectionWorld
        {
            get
            {
                Vector3 direction = sourceLight != null
                    ? sourceLight.transform.forward
                    : transform.forward;
                return direction.sqrMagnitude > 0.000001f
                    ? direction.normalized
                    : Vector3.down;
            }
        }

        private void Reset()
        {
            sourceLight = GetComponent<Light>();
        }

        private void Awake()
        {
            if (sourceLight == null)
            {
                sourceLight = GetComponent<Light>();
            }
        }

        private void OnEnable()
        {
            if (!ActiveEmitters.Contains(this))
            {
                ActiveEmitters.Add(this);
            }
        }

        private void OnDisable()
        {
            ActiveEmitters.Remove(this);
        }

        private void OnValidate()
        {
            if (sourceLight == null)
            {
                sourceLight = GetComponent<Light>();
            }

            length = Mathf.Max(0.05f, length);
            coneRadiusScale = Mathf.Clamp(coneRadiusScale, 0.1f, 1.25f);
            intensityMultiplier = Mathf.Max(0f, intensityMultiplier);
            densityBands = Mathf.Clamp(densityBands, 2, 8);
            noiseStrength = Mathf.Clamp01(noiseStrength);
            worldCellSize = Mathf.Max(0.01f, worldCellSize);
        }

        internal static int FillVisibleEmitters(
            StylizedLightShaftEmitter[] results,
            float[] selectionDistances,
            Camera camera,
            Plane[] frustumPlanes,
            Scene activeScene,
            Transform persistentGameplayRoot,
            int limit,
            out bool truncated)
        {
            for (int index = ActiveEmitters.Count - 1; index >= 0; index--)
            {
                if (ActiveEmitters[index] == null)
                {
                    ActiveEmitters.RemoveAt(index);
                }
            }

            int clampedLimit = Mathf.Min(limit, results.Length);
            clampedLimit = Mathf.Min(clampedLimit, selectionDistances.Length);
            if (clampedLimit <= 0 ||
                camera == null ||
                frustumPlanes == null ||
                frustumPlanes.Length < 6)
            {
                truncated = false;
                return 0;
            }

            int count = 0;
            int eligibleCount = 0;
            Vector3 cameraPosition = camera.transform.position;
            for (int index = 0; index < ActiveEmitters.Count; index++)
            {
                StylizedLightShaftEmitter emitter = ActiveEmitters[index];
                Light light = emitter.sourceLight;
                bool belongsToPersistentGameplay =
                    persistentGameplayRoot != null &&
                    (emitter.transform == persistentGameplayRoot ||
                     emitter.transform.IsChildOf(persistentGameplayRoot));
                if (!emitter.isActiveAndEnabled ||
                    light == null ||
                    !light.isActiveAndEnabled ||
                    light.type != LightType.Spot ||
                    !light.enabled ||
                    light.intensity <= 0f ||
                    emitter.intensityMultiplier <= 0f ||
                    (emitter.gameObject.scene != activeScene &&
                     !belongsToPersistentGameplay))
                {
                    continue;
                }

                Vector3 origin = emitter.OriginWorld;
                Vector3 end = origin + emitter.DirectionWorld * emitter.length;
                Vector3 radius = Vector3.one * emitter.EndRadius;
                Bounds bounds = new Bounds();
                bounds.SetMinMax(
                    Vector3.Min(origin, end) - radius,
                    Vector3.Max(origin, end) + radius);
                if (!GeometryUtility.TestPlanesAABB(frustumPlanes, bounds))
                {
                    continue;
                }

                eligibleCount++;
                float distanceSquared = bounds.SqrDistance(cameraPosition);
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
                    results[insertIndex] = results[insertIndex - 1];
                    selectionDistances[insertIndex] = selectionDistances[insertIndex - 1];
                    insertIndex--;
                }

                results[insertIndex] = emitter;
                selectionDistances[insertIndex] = distanceSquared;
            }

            truncated = eligibleCount > clampedLimit;
            return count;
        }

        private void OnDrawGizmosSelected()
        {
            Vector3 direction = DirectionWorld;
            Vector3 origin = OriginWorld;
            Vector3 end = origin + direction * length;
            Color sourceColor = sourceLight != null
                ? sourceLight.color
                : new Color(1f, 0.62f, 0.28f, 1f);
            Gizmos.color = new Color(sourceColor.r, sourceColor.g, sourceColor.b, 0.55f);
            Gizmos.DrawLine(origin, end);
            Gizmos.DrawWireSphere(end, EndRadius);
        }
    }
}
