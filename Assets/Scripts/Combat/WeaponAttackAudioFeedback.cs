using UnityEngine;

namespace FantasySurvival.Combat
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(AudioSource))]
    public sealed class WeaponAttackAudioFeedback : MonoBehaviour
    {
        [SerializeField] private AudioSource audioSource;
        [SerializeField] private AudioClip fireClip;
        [SerializeField] private AudioClip hitClip;
        [SerializeField, Range(0f, 1f)] private float fireVolume = 0.45f;
        [SerializeField, Range(0f, 1f)] private float hitVolume = 0.65f;

        public AudioSource AudioSource => audioSource;
        public AudioClip FireClip => fireClip;
        public AudioClip HitClip => hitClip;
        public bool IsConfigured =>
            audioSource != null && fireClip != null && hitClip != null;

        private void Awake()
        {
            if (IsConfigured)
            {
                return;
            }

            Debug.LogError(
                $"{nameof(WeaponAttackAudioFeedback)} on '{name}' requires an " +
                $"{nameof(AudioSource)}, fire clip, and hit clip.",
                this);
            enabled = false;
        }

        private void OnDisable()
        {
            if (audioSource != null)
            {
                audioSource.Stop();
            }
        }

        public void PlayFire()
        {
            if (enabled && fireClip != null)
            {
                audioSource.PlayOneShot(fireClip, fireVolume);
            }
        }

        public void PlayHit()
        {
            if (enabled && hitClip != null)
            {
                audioSource.PlayOneShot(hitClip, hitVolume);
            }
        }

#if UNITY_EDITOR
        private void OnValidate()
        {
            if (audioSource == null)
            {
                audioSource = GetComponent<AudioSource>();
            }

            fireVolume = Mathf.Clamp01(fireVolume);
            hitVolume = Mathf.Clamp01(hitVolume);
        }
#endif
    }
}
