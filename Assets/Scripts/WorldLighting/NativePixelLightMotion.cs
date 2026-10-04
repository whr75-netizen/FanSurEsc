using UnityEngine;

namespace FantasySurvival.WorldLighting
{
    /// <summary>Moves the existing stepped light; it owns no lighting calculation.</summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(SteppedLocalLight))]
    public sealed class NativePixelLightMotion : MonoBehaviour
    {
        public Vector3 localCenter = new Vector3(0f, 1.35f, 0f);
        [Min(0f)] public float amplitude = 3f;
        [Min(0.01f)] public float periodSeconds = 8f;

        public Vector3 PositionAt(float seconds)
        {
            return localCenter + Vector3.right *
                (amplitude * Mathf.Sin(seconds * (2f * Mathf.PI / periodSeconds)));
        }

        private void OnEnable() => transform.localPosition = PositionAt(0f);

        private void Update() => transform.localPosition = PositionAt(Time.timeSinceLevelLoad);
    }
}
