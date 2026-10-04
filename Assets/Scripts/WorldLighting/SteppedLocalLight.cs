using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Defines one presentation-only local light. The renderer consumes these
    /// values. Room lamps also drive an explicitly paired Unity direct light.
    /// </summary>
    // Registration only: there is no edit-time Update or separate light state.
    // Native surface materials and Scene View consume this same source list.
    [ExecuteAlways]
    [DisallowMultipleComponent]
    [AddComponentMenu("Fantasy Survival/World Lighting/Stepped Local Light")]
    public sealed class SteppedLocalLight : MonoBehaviour
    {
        public enum LightingRole { Local, RoomLamp }
        private static readonly List<SteppedLocalLight> ActiveLights = new();

        [SerializeField] private LightingRole role;
        [Tooltip("Room lamps only: isotropic diffuse irradiance inside assigned room volumes. This approximates indirect light; it is not baked GI.")]
        [SerializeField, Min(0f)] private float roomIndirectMultiplier = 1.5f;
        [Tooltip("Room lamps only: Unity point-light intensity relative to this owner's intensity.")]
        [SerializeField, Min(0f)] private float roomDirectMultiplier = 30f;
        [Tooltip("Derived shadowed direct light. Configure and switch this SteppedLocalLight owner, not the paired Unity Light.")]
        [SerializeField] private Light roomDirectLight;

        [Tooltip("RGB controls the tint; alpha scales the additive light contribution.")]
        [SerializeField, ColorUsage(true, true)] private Color color =
            new Color(1f, 0.62f, 0.28f, 1f);
        [SerializeField, Min(0.01f)] private float radius = 4.5f;
        [SerializeField, Min(0f)] private float intensity = 1.15f;
        [SerializeField, Range(2, 16)] private int surfaceBands = 5;
        [Tooltip("Native readable surfaces use the base scene's additive RGB blend. Surface bands count illuminated levels; zero light is separate. Other lights keep their original shading.")]
        [SerializeField] private bool additiveNativePresentation;
        [SerializeField, Range(2, 16)] private int haloBands = 4;
        [SerializeField, Range(0f, 1f)] private float haloStrength = 0.18f;
        [SerializeField, Range(1f, 2f)] private float haloRadiusMultiplier = 1.25f;
        [SerializeField, Range(0f, 1f)] private float normalInfluence = 0.82f;
        [SerializeField, Min(0.01f)] private float worldCellSize = 0.12f;
        [Tooltip("Optional room volume. Two assigned boxes form a union; no boxes preserves unrestricted lighting. This is a room boundary, not a wall or furniture shadow solver.")]
        [SerializeField] private BoxCollider illuminationVolume;
        [SerializeField] private BoxCollider illuminationVolume2;

        public Color Color => color;
        public float Radius => radius;
        public float Intensity => intensity;
        public int SurfaceBands => surfaceBands;
        public bool AdditiveNativePresentation => additiveNativePresentation;
        public int HaloBands => haloBands;
        public float HaloStrength => haloStrength;
        public float HaloRadiusMultiplier => haloRadiusMultiplier;
        public float NormalInfluence => normalInfluence;
        public float WorldCellSize => worldCellSize;
        public BoxCollider IlluminationVolume => illuminationVolume;
        public BoxCollider IlluminationVolume2 => illuminationVolume2;
        public LightingRole Role => role;
        public float RoomIndirectMultiplier => roomIndirectMultiplier;
        public float RoomDirectMultiplier => roomDirectMultiplier;
        public Light RoomDirectLight => roomDirectLight;

        // The custom radial presentation radius is not a room lamp's direct-light cutoff.
        // At every assigned room corner d <= R/2, URP's smooth range fade is >= (15/16)^2.
        public float RoomDirectRange
        {
            get
            {
                if (role != LightingRole.RoomLamp) return radius;
                Vector3 origin = roomDirectLight != null ? roomDirectLight.transform.position : transform.position;
                float farthestSquared = Mathf.Max(MaximumCornerDistanceSquared(illuminationVolume, origin),
                    MaximumCornerDistanceSquared(illuminationVolume2, origin));
                return Mathf.Max(radius, 2f * Mathf.Sqrt(farthestSquared));
            }
        }

        private static float MaximumCornerDistanceSquared(BoxCollider volume, Vector3 origin)
        {
            if (volume == null) return 0f;
            float farthestSquared = 0f;
            Vector3 halfSize = volume.size * 0.5f;
            for (int corner = 0; corner < 8; corner++)
            {
                Vector3 sign = new Vector3((corner & 1) == 0 ? -1f : 1f,
                    (corner & 2) == 0 ? -1f : 1f, (corner & 4) == 0 ? -1f : 1f);
                Vector3 world = volume.transform.TransformPoint(volume.center + Vector3.Scale(halfSize, sign));
                farthestSquared = Mathf.Max(farthestSquared, (world - origin).sqrMagnitude);
            }
            return farthestSquared;
        }

        public void SetLightingEnabled(bool value)
        {
            enabled = value;
            SynchronizeRoomDirectLight();
        }

        public void SynchronizeRoomDirectLight()
        {
            if (roomDirectLight == null) return;
            bool validRoom = illuminationVolume != null || illuminationVolume2 != null;
            roomDirectLight.enabled = role == LightingRole.RoomLamp && validRoom &&
                isActiveAndEnabled && intensity > 0f && color.a > 0f;
            if (role != LightingRole.RoomLamp) return;
            roomDirectLight.type = LightType.Point;
            roomDirectLight.color = new Color(color.r, color.g, color.b, 1f);
            roomDirectLight.intensity = intensity * roomDirectMultiplier * Mathf.Clamp01(color.a);
            roomDirectLight.range = RoomDirectRange;
            roomDirectLight.shadows = LightShadows.Hard;
        }

        private void OnEnable()
        {
            if (!ActiveLights.Contains(this))
            {
                ActiveLights.Add(this);
            }
            SynchronizeRoomDirectLight();
        }

        private void OnDisable()
        {
            ActiveLights.Remove(this);
            if (roomDirectLight != null && role == LightingRole.RoomLamp)
                roomDirectLight.enabled = false;
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
            roomIndirectMultiplier = Mathf.Max(0f, roomIndirectMultiplier);
            roomDirectMultiplier = Mathf.Max(0f, roomDirectMultiplier);
            SynchronizeRoomDirectLight();
        }

        internal static int FillShaderData(
            Vector4[] positionsAndRadii,
            Vector4[] colorsAndIntensities,
            Vector4[] quantizationSettings,
            Vector4[] roomLightingSettings,
            float[] worldCellSizes,
            float[] haloRadiusMultipliers,
            float[] selectionDistances,
            Matrix4x4[] volumeWorldToLocal,
            Vector4[] volumeCenters,
            Vector4[] volumeExtents,
            Matrix4x4[] volume2WorldToLocal,
            Vector4[] volume2Centers,
            Vector4[] volume2Extents,
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
            clampedLimit = Mathf.Min(clampedLimit, roomLightingSettings.Length);
            clampedLimit = Mathf.Min(clampedLimit, worldCellSizes.Length);
            clampedLimit = Mathf.Min(clampedLimit, haloRadiusMultipliers.Length);
            clampedLimit = Mathf.Min(clampedLimit, selectionDistances.Length);
            clampedLimit = Mathf.Min(clampedLimit, volumeWorldToLocal.Length);
            clampedLimit = Mathf.Min(clampedLimit, volumeCenters.Length);
            clampedLimit = Mathf.Min(clampedLimit, volumeExtents.Length);
            clampedLimit = Mathf.Min(clampedLimit, volume2WorldToLocal.Length);
            clampedLimit = Mathf.Min(clampedLimit, volume2Centers.Length);
            clampedLimit = Mathf.Min(clampedLimit, volume2Extents.Length);
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
                if (light.role == LightingRole.RoomLamp)
                {
                    if (light.roomDirectLight == null ||
                        (light.illuminationVolume == null && light.illuminationVolume2 == null))
                        continue;
                    if (light.illuminationVolume != null) influenceBounds.Encapsulate(RoomWorldBounds(light.illuminationVolume));
                    if (light.illuminationVolume2 != null) influenceBounds.Encapsulate(RoomWorldBounds(light.illuminationVolume2));
                }
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
                    roomLightingSettings[insertIndex] = roomLightingSettings[insertIndex - 1];
                    worldCellSizes[insertIndex] = worldCellSizes[insertIndex - 1];
                    haloRadiusMultipliers[insertIndex] =
                        haloRadiusMultipliers[insertIndex - 1];
                    selectionDistances[insertIndex] =
                        selectionDistances[insertIndex - 1];
                    volumeWorldToLocal[insertIndex] = volumeWorldToLocal[insertIndex - 1];
                    volumeCenters[insertIndex] = volumeCenters[insertIndex - 1];
                    volumeExtents[insertIndex] = volumeExtents[insertIndex - 1];
                    volume2WorldToLocal[insertIndex] = volume2WorldToLocal[insertIndex - 1];
                    volume2Centers[insertIndex] = volume2Centers[insertIndex - 1];
                    volume2Extents[insertIndex] = volume2Extents[insertIndex - 1];
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
                    // Sign selects the native presentation; magnitude remains
                    // the band count in the same authoritative shader record.
                    light.additiveNativePresentation ? -light.surfaceBands : light.surfaceBands,
                    light.haloBands,
                    light.haloStrength,
                    light.normalInfluence);
                roomLightingSettings[insertIndex] = light.role == LightingRole.RoomLamp ?
                    new Vector4(light.roomIndirectMultiplier, 1f, 0f, 0f) : Vector4.zero;
                worldCellSizes[insertIndex] = light.worldCellSize;
                haloRadiusMultipliers[insertIndex] = light.haloRadiusMultiplier;
                selectionDistances[insertIndex] = distanceSquared;
                WriteVolumeData(light.illuminationVolume, insertIndex,
                    volumeWorldToLocal, volumeCenters, volumeExtents);
                WriteVolumeData(light.illuminationVolume2, insertIndex,
                    volume2WorldToLocal, volume2Centers, volume2Extents);
            }

            truncated = eligibleCount > clampedLimit;
            return count;
        }

        private static Bounds RoomWorldBounds(BoxCollider volume)
        {
            // Room volumes may be disabled/non-physical; Collider.bounds is then empty.
            // Transform the authored box's basis, including parent scale/rotation.
            Vector3 h = volume.size * .5f;
            Vector3 x = volume.transform.TransformVector(new Vector3(h.x, 0, 0));
            Vector3 y = volume.transform.TransformVector(new Vector3(0, h.y, 0));
            Vector3 z = volume.transform.TransformVector(new Vector3(0, 0, h.z));
            Vector3 e = new Vector3(Mathf.Abs(x.x)+Mathf.Abs(y.x)+Mathf.Abs(z.x),
                Mathf.Abs(x.y)+Mathf.Abs(y.y)+Mathf.Abs(z.y),
                Mathf.Abs(x.z)+Mathf.Abs(y.z)+Mathf.Abs(z.z));
            return new Bounds(volume.transform.TransformPoint(volume.center), e * 2f);
        }

        private static void WriteVolumeData(BoxCollider volume, int index,
            Matrix4x4[] worldToLocal, Vector4[] centers, Vector4[] extents)
        {
            if (volume == null)
            {
                worldToLocal[index] = Matrix4x4.identity;
                centers[index] = Vector4.zero;
                extents[index] = Vector4.zero;
                return;
            }

            // Use collider-local bounds, not its world AABB: building rotation
            // and inherited scale must not enlarge the permitted room region.
            Vector3 center = volume.center;
            Vector3 halfSize = volume.size * 0.5f;
            worldToLocal[index] = volume.transform.worldToLocalMatrix;
            centers[index] = new Vector4(center.x, center.y, center.z, 1f);
            extents[index] = new Vector4(halfSize.x, halfSize.y, halfSize.z, 0f);
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(color.r, color.g, color.b, 0.65f);
            Gizmos.DrawWireSphere(transform.position, radius);
        }
    }
}
