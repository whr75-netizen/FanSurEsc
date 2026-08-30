using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.WorldLighting
{
    /// <summary>
    /// Applies the authoritative sky controller's continuous night visibility
    /// to one scene-local street-lamp Spot Light. It owns no clock or weather.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Light))]
    [AddComponentMenu("Fantasy Survival/World Lighting/Night Activated Street Lamp")]
    public sealed class NightActivatedStreetLamp : MonoBehaviour
    {
        private const float EnabledThreshold = 0.001f;
        private static readonly int LampVisibilityId =
            Shader.PropertyToID("_LampVisibility");

        [SerializeField] private Light sourceLight;
        [SerializeField] private Renderer[] emissiveRenderers;
        [SerializeField, Min(0f)] private float maximumIntensity = 24f;

        private SkyLightingCycleController boundSkyController;
        private MaterialPropertyBlock rendererProperties;
        private bool missingSkyWarningReported;

        public Light SourceLight => sourceLight;
        public float MaximumIntensity => maximumIntensity;
        public float Visibility { get; private set; }

        private void Reset()
        {
            sourceLight = GetComponent<Light>();
        }

        private void Awake()
        {
            ResolveSourceLight();
        }

        private void OnEnable()
        {
            if (Application.isPlaying)
            {
                BindSkyController();
            }
        }

        private void Start()
        {
            if (Application.isPlaying && boundSkyController == null)
            {
                BindSkyController();
            }
        }

        private void OnDisable()
        {
            UnbindSkyController();
            if (Application.isPlaying)
            {
                ApplyVisibility(0f);
            }
        }

        private void OnValidate()
        {
            ResolveSourceLight();
            maximumIntensity = Mathf.Max(0f, maximumIntensity);
        }

        private void ResolveSourceLight()
        {
            if (sourceLight == null)
            {
                sourceLight = GetComponent<Light>();
            }
        }

        private void BindSkyController()
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            SkyLightingCycleController nextController = shell != null
                ? shell.GetComponent<SkyLightingCycleController>()
                : null;
            if (nextController == boundSkyController)
            {
                if (nextController != null)
                {
                    ApplyVisibility(nextController.CurrentNightActivatedLightVisibility);
                }
                return;
            }

            UnbindSkyController();
            boundSkyController = nextController;
            if (boundSkyController == null)
            {
                ApplyVisibility(0f);
                if (!missingSkyWarningReported)
                {
                    Debug.LogWarning(
                        "NightActivatedStreetLamp could not find the persistent sky controller; " +
                        "the lamp remains off.",
                        this);
                    missingSkyWarningReported = true;
                }
                return;
            }

            missingSkyWarningReported = false;
            boundSkyController.NightActivatedLightVisibilityChanged +=
                HandleNightVisibilityChanged;
            ApplyVisibility(boundSkyController.CurrentNightActivatedLightVisibility);
        }

        private void UnbindSkyController()
        {
            if (boundSkyController != null)
            {
                boundSkyController.NightActivatedLightVisibilityChanged -=
                    HandleNightVisibilityChanged;
                boundSkyController = null;
            }
        }

        private void HandleNightVisibilityChanged(float visibility)
        {
            ApplyVisibility(visibility);
        }

        private void ApplyVisibility(float visibility)
        {
            ResolveSourceLight();
            Visibility = Mathf.Clamp01(visibility);
            ApplyRendererVisibility(Visibility);
            if (sourceLight == null)
            {
                return;
            }

            float appliedIntensity = maximumIntensity * Visibility;
            sourceLight.intensity = appliedIntensity;
            sourceLight.enabled = appliedIntensity > EnabledThreshold;
        }

        private void ApplyRendererVisibility(float visibility)
        {
            if (emissiveRenderers == null || emissiveRenderers.Length == 0)
            {
                return;
            }

            rendererProperties ??= new MaterialPropertyBlock();
            for (int index = 0; index < emissiveRenderers.Length; index++)
            {
                Renderer target = emissiveRenderers[index];
                if (target == null)
                {
                    continue;
                }

                target.GetPropertyBlock(rendererProperties);
                rendererProperties.SetFloat(LampVisibilityId, visibility);
                target.SetPropertyBlock(rendererProperties);
                rendererProperties.Clear();
            }
        }
    }
}
