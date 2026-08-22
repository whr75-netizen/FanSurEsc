namespace FantasySurvival.Combat
{
    public enum WeaponFireMode
    {
        SemiAutomatic,
        Automatic
    }

    /// <summary>
    /// Owns only the runtime cadence of one runtime weapon item.
    /// Input edge/hold selection and the actual attack stay outside this class.
    /// </summary>
    public sealed class WeaponFireCadence
    {
        private float nextAllowedFireTime;

        public float NextAllowedFireTime => nextAllowedFireTime;

        public bool TryConsume(
            WeaponFireMode fireMode,
            bool pressedThisFrame,
            bool held,
            float currentTime,
            float roundsPerMinute)
        {
            bool triggerRequested = fireMode == WeaponFireMode.Automatic
                ? held
                : pressedThisFrame;

            if (!triggerRequested || roundsPerMinute <= 0f || currentTime < nextAllowedFireTime)
            {
                return false;
            }

            float interval = 60f / roundsPerMinute;
            float phasePreservingNextTime = nextAllowedFireTime + interval;

            // Preserve the configured cadence across ordinary frame rounding, but never
            // replay missed shots after a hitch as a burst on subsequent frames.
            nextAllowedFireTime = nextAllowedFireTime > 0f && phasePreservingNextTime > currentTime
                ? phasePreservingNextTime
                : currentTime + interval;
            return true;
        }

        public void Reset()
        {
            nextAllowedFireTime = 0f;
        }
    }
}
