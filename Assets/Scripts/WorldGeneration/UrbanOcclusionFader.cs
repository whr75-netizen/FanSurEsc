using System;
using System.Collections.Generic;
using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>Fades registered building surfaces without changing collision or navigation.</summary>
    [DefaultExecutionOrder(500)]
    [DisallowMultipleComponent]
    public sealed class UrbanOcclusionFader : MonoBehaviour
    {
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private const float FadeSeconds = 0.15f;
        private const float WallOpacity = 0.18f;
        private const float InteriorRoofOpacity = 0.04f;

        private sealed class Surface
        {
            public Renderer Renderer;
            public Collider Collider;
            public Color BaseColor;
            public float Opacity = 1f;
        }

        private sealed class Building
        {
            public Transform Root;
            public Bounds Interior;
            public Bounds OcclusionBounds;
            public Surface Roof;
            public Surface[] Walls;
        }

        private readonly List<Building> buildings = new List<Building>();
        private MaterialPropertyBlock properties;

        private void Awake()
        {
            properties = new MaterialPropertyBlock();
        }

        public int InsideBuildingCount { get; private set; }
        public int FadedRendererCount { get; private set; }

        public void RegisterBuilding(
            Transform root,
            Bounds localInterior,
            Renderer roof,
            Collider roofCollider,
            Renderer[] walls,
            Collider[] wallColliders)
        {
            if (properties == null) properties = new MaterialPropertyBlock();
            if (root == null)
                throw new ArgumentNullException(nameof(root));
            if (walls == null || wallColliders == null || walls.Length != wallColliders.Length)
                throw new ArgumentException("Wall renderers and colliders must have matching arrays.");

            var building = new Building
            {
                Root = root,
                Interior = localInterior,
                OcclusionBounds = localInterior,
                Roof = CreateSurface(roof, roofCollider),
                Walls = new Surface[walls.Length]
            };
            IncludeColliderBounds(building, roofCollider);
            for (int index = 0; index < walls.Length; index++)
            {
                building.Walls[index] = CreateSurface(walls[index], wallColliders[index]);
                IncludeColliderBounds(building, wallColliders[index]);
            }
            buildings.Add(building);
        }

        private void LateUpdate()
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            if (shell != null && shell.PlayerCamera != null && shell.PlayerTransform != null)
                EvaluateVisibility(shell.PlayerCamera, shell.PlayerTransform.position, Time.deltaTime);
        }

        public void EvaluateVisibility(Camera camera, Vector3 playerFeet, float deltaTime)
        {
            InsideBuildingCount = 0;
            FadedRendererCount = 0;
            if (camera == null)
                return;

            Ray torsoRay = CreateSightRay(camera, playerFeet + Vector3.up * 0.8f, out float torsoDistance);
            Ray headRay = CreateSightRay(camera, playerFeet + Vector3.up * 1.5f, out float headDistance);
            float fadeStep = Mathf.Max(0f, deltaTime) / FadeSeconds;
            for (int index = 0; index < buildings.Count; index++)
            {
                Building building = buildings[index];
                if (building.Root == null || !building.Root.gameObject.activeInHierarchy)
                    continue;

                bool inside = building.Interior.Contains(
                    building.Root.InverseTransformPoint(playerFeet + Vector3.up * 0.5f));
                if (inside)
                    InsideBuildingCount++;

                Bounds worldBounds = TransformBounds(building.Root.localToWorldMatrix, building.OcclusionBounds);
                bool mayOcclude = inside ||
                    IntersectsSegment(worldBounds, torsoRay, torsoDistance) ||
                    IntersectsSegment(worldBounds, headRay, headDistance);

                UpdateSurface(building.Roof, inside ? InteriorRoofOpacity : WallOpacity,
                    inside, mayOcclude, torsoRay, torsoDistance, headRay, headDistance, fadeStep);
                for (int wallIndex = 0; wallIndex < building.Walls.Length; wallIndex++)
                {
                    UpdateSurface(building.Walls[wallIndex], WallOpacity,
                        inside, mayOcclude, torsoRay, torsoDistance, headRay, headDistance, fadeStep);
                }
            }
        }

        private void UpdateSurface(Surface surface, float fadedOpacity, bool inside, bool mayOcclude,
            Ray torsoRay, float torsoDistance, Ray headRay, float headDistance, float fadeStep)
        {
            if (surface == null || surface.Renderer == null)
                return;

            bool blocked = inside || (mayOcclude &&
                (BlocksSegment(surface.Collider, torsoRay, torsoDistance) ||
                 BlocksSegment(surface.Collider, headRay, headDistance)));
            SetOpacity(surface, Mathf.MoveTowards(surface.Opacity, blocked ? fadedOpacity : 1f, fadeStep));
            if (surface.Opacity < 0.999f && surface.Renderer.enabled &&
                surface.Renderer.gameObject.activeInHierarchy)
                FadedRendererCount++;
        }

        private Surface CreateSurface(Renderer renderer, Collider collider)
        {
            if (renderer == null)
                return null;

            Material material = renderer.sharedMaterial;
            Color color = material != null && material.HasProperty(BaseColorId)
                ? material.GetColor(BaseColorId) : Color.white;
            renderer.GetPropertyBlock(properties);
            if (properties.HasColor(BaseColorId))
                color = properties.GetColor(BaseColorId);
            return new Surface { Renderer = renderer, Collider = collider, BaseColor = color };
        }

        private void SetOpacity(Surface surface, float opacity)
        {
            if (surface == null || surface.Renderer == null || surface.Opacity == opacity)
                return;

            surface.Renderer.GetPropertyBlock(properties);
            Color color = properties.HasColor(BaseColorId)
                ? properties.GetColor(BaseColorId) : surface.BaseColor;
            color.a = surface.BaseColor.a * opacity;
            properties.SetColor(BaseColorId, color);
            surface.Renderer.SetPropertyBlock(properties);
            surface.Opacity = opacity;
        }

        private static Ray CreateSightRay(Camera camera, Vector3 target, out float distance)
        {
            // Viewport rays stay parallel for an orthographic camera and also handle perspective.
            Ray ray = camera.ViewportPointToRay(camera.WorldToViewportPoint(target));
            distance = Mathf.Max(0f, Vector3.Dot(target - ray.origin, ray.direction));
            return ray;
        }

        private static bool IntersectsSegment(Bounds bounds, Ray ray, float distance)
        {
            return distance > 0f && bounds.IntersectRay(ray, out float entry) && entry <= distance;
        }

        private static bool BlocksSegment(Collider collider, Ray ray, float distance)
        {
            // Test physical wall segments, so rays through the doorway remain unobstructed.
            return collider != null && collider.enabled && !collider.isTrigger &&
                collider.gameObject.activeInHierarchy && distance > 0f &&
                collider.Raycast(ray, out _, distance);
        }

        private static void IncludeColliderBounds(Building building, Collider collider)
        {
            if (collider != null)
                building.OcclusionBounds.Encapsulate(
                    TransformBounds(building.Root.worldToLocalMatrix, collider.bounds));
        }

        private static Bounds TransformBounds(Matrix4x4 matrix, Bounds bounds)
        {
            Vector3 x = matrix.MultiplyVector(new Vector3(bounds.extents.x, 0f, 0f));
            Vector3 y = matrix.MultiplyVector(new Vector3(0f, bounds.extents.y, 0f));
            Vector3 z = matrix.MultiplyVector(new Vector3(0f, 0f, bounds.extents.z));
            Vector3 extents = new Vector3(
                Mathf.Abs(x.x) + Mathf.Abs(y.x) + Mathf.Abs(z.x),
                Mathf.Abs(x.y) + Mathf.Abs(y.y) + Mathf.Abs(z.y),
                Mathf.Abs(x.z) + Mathf.Abs(y.z) + Mathf.Abs(z.z));
            return new Bounds(matrix.MultiplyPoint3x4(bounds.center), extents * 2f);
        }

        private void OnDisable()
        {
            for (int index = 0; index < buildings.Count; index++)
            {
                SetOpacity(buildings[index].Roof, 1f);
                for (int wallIndex = 0; wallIndex < buildings[index].Walls.Length; wallIndex++)
                    SetOpacity(buildings[index].Walls[wallIndex], 1f);
            }
            InsideBuildingCount = 0;
            FadedRendererCount = 0;
        }
    }
}
