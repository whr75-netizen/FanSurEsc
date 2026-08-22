using System.Collections;
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
        [SerializeField, Min(0f)] private float hitSeparationSeconds = 0.06f;

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
            StopAllCoroutines();

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
            if (!enabled || audioSource == null || hitClip == null)
            {
                return;
            }

            if (hitSeparationSeconds <= 0f)
            {
                audioSource.PlayOneShot(hitClip, hitVolume);
                return;
            }

            StartCoroutine(PlayHitSeparated());
        }

        private IEnumerator PlayHitSeparated()
        {
            yield return new WaitForSeconds(hitSeparationSeconds);

            if (enabled && audioSource != null && hitClip != null)
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
            hitSeparationSeconds = Mathf.Max(0f, hitSeparationSeconds);
        }
#endif
    }
}
