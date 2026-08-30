using FantasySurvival.SceneFlow;
using FantasySurvival.WorldLighting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.Rendering
{
    [DisallowMultipleRendererFeature("Pixel Rain (Persistent Gameplay Camera)")]
    public sealed class PixelRainRendererFeature : FullScreenPassRendererFeature
    {
        public override void AddRenderPasses(
            ScriptableRenderer renderer,
            ref RenderingData renderingData)
        {
            Camera camera = renderingData.cameraData.camera;
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (!Application.isPlaying ||
                renderingData.cameraData.cameraType != CameraType.Game ||
                shell == null ||
                shell.PlayerCamera != camera ||
                !shell.TryGetComponent(out PixelRainPresentation presentation) ||
                !presentation.ShouldRender)
            {
                return;
            }

            base.AddRenderPasses(renderer, ref renderingData);
        }
    }
}
