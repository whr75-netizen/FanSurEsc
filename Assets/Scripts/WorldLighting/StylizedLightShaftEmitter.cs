using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Opts one Spot Light into the shared local-volumetric render pass.
    /// This component owns no light state; it only describes the participating
    /// medium used by dedicated lamps and similar fixtures.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Light))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stylized Light Shaft Emitter")]
    public sealed class StylizedLightShaftEmitter : MonoBehaviour
    {
        private static readonly List<StylizedLightShaftEmitter> ActiveEmitters = new();

        [SerializeField] private Light sourceLight;
        [Tooltip("Atmospheric single-scattering strength. This does not change the source Light intensity.")]
        [SerializeField, Min(0f)] private float intensityMultiplier = 0.075f;
        [Tooltip("How quickly the participating medium absorbs/out-scatters light along the camera ray.")]
        [SerializeField, Min(0f)] private float extinctionCoefficient = 0.08f;
        [Tooltip("Forward-scattering bias. Zero is isotropic; positive values favor looking toward the light.")]
        [SerializeField, Range(-0.35f, 0.65f)] private float anisotropy = 0.12f;

        internal Light SourceLight => sourceLight;
        internal Vector3 OriginWorld =>
            sourceLight != null ? sourceLight.transform.position : transform.position;
        internal float Length => sourceLight != null
            ? Mathf.Max(0.05f, sourceLight.range)
            : 4.6f;
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
                    Mathf.Tan(halfAngleRadians) * Length);
            }
        }
        internal float IntensityMultiplier => intensityMultiplier;
        internal float ExtinctionCoefficient => extinctionCoefficient;
        internal float Anisotropy => anisotropy;
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

            intensityMultiplier = Mathf.Max(0f, intensityMultiplier);
            extinctionCoefficient = Mathf.Max(0f, extinctionCoefficient);
            anisotropy = Mathf.Clamp(anisotropy, -0.35f, 0.65f);
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
                Vector3 end = origin + emitter.DirectionWorld * emitter.Length;
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
            Vector3 end = origin + direction * Length;
            Color sourceColor = sourceLight != null
                ? sourceLight.color
                : new Color(1f, 0.62f, 0.28f, 1f);
            Gizmos.color = new Color(sourceColor.r, sourceColor.g, sourceColor.b, 0.55f);
            Gizmos.DrawLine(origin, end);
            Gizmos.DrawWireSphere(end, EndRadius);
        }
    }
}
