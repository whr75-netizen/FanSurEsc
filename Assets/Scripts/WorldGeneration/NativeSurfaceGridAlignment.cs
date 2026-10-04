using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>One render-space grid translation for a cached surface and its original solid.</summary>
    [ExecuteAlways, DisallowMultipleComponent]
    public sealed class NativeSurfaceGridAlignment : MonoBehaviour
    {
        public const string SurfaceShader = "FantasySurvival/World/Native Palette Surface 16";
        public static readonly int OffsetId = Shader.PropertyToID("_NativeRenderOffsetWS");
        private readonly List<Pair> pairs = new List<Pair>();
        private MaterialPropertyBlock block;

        private sealed class Pair
        {
            public Renderer surface, caster;
            public Bounds surfaceBounds, casterBounds;
        }

        public int PairCount => pairs.Count;

        private void OnEnable()
        {
            if (block == null) block = new MaterialPropertyBlock();
            Rebind();
            RenderPipelineManager.beginCameraRendering += BeforeCamera;
        }

        private void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= BeforeCamera;
            foreach (var p in pairs)
            {
                Write(p.surface, Vector4.zero, p.surfaceBounds);
                Write(p.caster, Vector4.zero, p.casterBounds);
            }
            pairs.Clear();
        }

        public void Rebind()
        {
            // Restore our overrides before reading the original bounds again.
            foreach (var p in pairs)
            {
                Write(p.surface, Vector4.zero, p.surfaceBounds);
                Write(p.caster, Vector4.zero, p.casterBounds);
            }
            pairs.Clear();
            foreach (var r in GetComponentsInChildren<MeshRenderer>(true))
            {
                if (r.sharedMaterial == null || r.sharedMaterial.shader.name != SurfaceShader) continue;
                var child = r.transform.Find("Native16 physical shadow");
                var caster = child != null ? child.GetComponent<Renderer>() : null;
                if (caster == null) continue;
                pairs.Add(new Pair { surface = r, caster = caster,
                    surfaceBounds = r.localBounds, casterBounds = caster.localBounds });
            }
        }

        private void BeforeCamera(ScriptableRenderContext context, Camera camera) => Apply(camera);

        public void Apply(Camera camera)
        {
            foreach (var p in pairs)
            {
                if (p.surface == null || p.caster == null) continue;
                Vector3 offset = Calculate(camera, p.surface);
                // w=1 means the shared path owns alignment, including unsupported cameras (δ=0).
                var value = new Vector4(offset.x, offset.y, offset.z, 1);
                Write(p.surface, value, p.surfaceBounds);
                Write(p.caster, value, p.casterBounds);
            }
        }

        private void Write(Renderer renderer, Vector4 value, Bounds original)
        {
            if (renderer == null) return;
            renderer.GetPropertyBlock(block);
            block.SetVector(OffsetId, value);
            renderer.SetPropertyBlock(block);
            original.center += renderer.transform.InverseTransformVector((Vector3)value);
            renderer.localBounds = original;
        }

        public static Vector2 RasterSize(Camera camera)
        {
            // URP17 camera descriptor: renderScale is bypassed for SceneView/Preview/Reflection.
            float scale = 1;
            if (camera.cameraType == CameraType.Game &&
                GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset asset)
                scale = Mathf.Abs(asset.renderScale - 1) < .05f ? 1 : asset.renderScale;
            return new Vector2(Mathf.Max(1, (int)(camera.pixelWidth * scale)),
                Mathf.Max(1, (int)(camera.pixelHeight * scale)));
        }

        public static Vector2 Raster(Camera camera, Vector3 world, Vector2 size)
        {
            Vector4 p = camera.projectionMatrix * camera.worldToCameraMatrix * new Vector4(world.x, world.y, world.z, 1);
            return new Vector2((p.x / p.w * .5f + .5f) * size.x,
                (p.y / p.w * .5f + .5f) * size.y);
        }

        public static Vector3 Calculate(Camera camera, Renderer surface)
        {
            if (camera == null || !camera.orthographic || camera.allowDynamicResolution ||
                camera.stereoEnabled || camera.rect != new Rect(0, 0, 1, 1)) return Vector3.zero;
            var material = surface.sharedMaterial;
            if (material == null || material.GetFloat("_NativeGridEnabled") < .5f) return Vector3.zero;
            Matrix4x4 model = surface.localToWorldMatrix, view = camera.worldToCameraMatrix;
            Vector3 anchor = model.MultiplyPoint3x4(material.GetVector("_NativeGridAnchorOS"));
            Vector3 u = model.MultiplyVector(material.GetVector("_NativeGridTexelUOS"));
            Vector3 v = model.MultiplyVector(material.GetVector("_NativeGridTexelVOS"));
            Vector3 uv = view.MultiplyVector(u), vv = view.MultiplyVector(v);
            if (uv.x <= 1e-6f || vv.y <= 1e-6f || Mathf.Abs(uv.y) > uv.x * 1e-4f ||
                Mathf.Abs(vv.x) > vv.y * 1e-4f || Mathf.Abs(uv.x - vv.y) > uv.x * 1e-4f) return Vector3.zero;
            Vector2 size = RasterSize(camera), a = Raster(camera, anchor, size);
            Vector2 ur = Raster(camera, anchor + u, size) - a, vr = Raster(camera, anchor + v, size) - a;
            float q = Mathf.Round(Mathf.Abs(ur.x));
            if (q < 1 || Mathf.Abs(Mathf.Abs(ur.x) - q) > .01f ||
                Mathf.Abs(Mathf.Abs(vr.y) - q) > .01f || Mathf.Abs(ur.y) > .01f || Mathf.Abs(vr.x) > .01f)
                return Vector3.zero;
            Vector3 va = view.MultiplyVector(anchor);
            Vector2 s = new Vector2(va.x / uv.x, va.y / vv.y);
            Vector2 zero = Raster(camera, Vector3.zero, size);
            Vector2 dr = new Vector2((Mathf.Round(s.x) - s.x) * ur.x + Mathf.Round(zero.x / q) * q - zero.x,
                (Mathf.Round(s.y) - s.y) * vr.y + Mathf.Round(zero.y / q) * q - zero.y);
            Vector3 dv = new Vector3(dr.x / (size.x * camera.projectionMatrix.m00 * .5f),
                dr.y / (size.y * camera.projectionMatrix.m11 * .5f), 0);
            Vector3 offset = view.inverse.MultiplyVector(dv);
            return float.IsNaN(offset.x + offset.y + offset.z) || float.IsInfinity(offset.x + offset.y + offset.z)
                ? Vector3.zero : offset;
        }
    }
}
