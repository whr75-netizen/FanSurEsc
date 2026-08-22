using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace FantasySurvivalEscapeGame.Rendering
{
    /// <summary>
    /// Uses URP's maintained full-screen pass implementation, but limits the effect to
    /// runtime Game cameras so Scene View and edit-time authoring preview cameras stay untouched.
    /// </summary>
    [DisallowMultipleRendererFeature("3D Pixel Art (Game Cameras)")]
    public sealed class PixelArtRendererFeature : FullScreenPassRendererFeature
    {
        public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
        {
            if (!Application.isPlaying || renderingData.cameraData.cameraType != CameraType.Game)
                return;

            base.AddRenderPasses(renderer, ref renderingData);
        }
    }
}
