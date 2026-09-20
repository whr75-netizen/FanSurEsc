using System;
using System.Collections.Generic;
using FantasySurvival.SceneFlow;
using UnityEngine;
using UnityEngine.Rendering;

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
            public bool OriginalEnabled;
            public Collider Collider;
            public Color BaseColor;
            public float Opacity = 1f;
            public Material OpaqueMaterial;
            public Material FadedMaterial;
        }

        private sealed class Building
        {
            public Transform Root;
            public Bounds Interior;
            public Bounds OcclusionBounds;
            public Surface Roof;
            public Surface[] Walls;
        }

        private sealed class ContentVisibility
        {
            public Renderer Renderer;
            public bool OriginalEnabled;
        }

        private sealed class Storey
        {
            public Transform Root;
            public Bounds WholeInterior;
            public Bounds OcclusionBounds;
            public int FloorIndex;
            public float StoreyHeight;
            public bool IsRoof;
            public Surface[] Floors;
            public Surface[] Walls;
            public ContentVisibility[] Contents;
        }

        private readonly List<Building> buildings = new List<Building>();
        private readonly List<Storey> storeys = new List<Storey>();
        private readonly HashSet<Transform> insideStoreyRoots = new HashSet<Transform>();
        private readonly Dictionary<Material, Material> fadeMaterials = new Dictionary<Material, Material>();
        private MaterialPropertyBlock properties;

        private void Awake()
        {
            properties = new MaterialPropertyBlock();
        }

        public int InsideBuildingCount { get; private set; }
        public int FadedRendererCount { get; private set; }
        public int HiddenUpperStoreyRendererCount { get; private set; }

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

        /// <summary>
        /// Registers a floor against the same building-local interior volume. Visibility never
        /// changes its colliders: upper floors remain walkable while their rendering is cut away.
        /// </summary>
        public void RegisterStorey(Transform root, Bounds wholeInterior, int floorIndex,
            float storeyHeight, Renderer[] floors, Collider[] floorColliders,
            Renderer[] walls, Collider[] wallColliders, Renderer[] contents, bool roof = false)
        {
            if (root == null)
                throw new ArgumentNullException(nameof(root));
            if (floorIndex < 0 || !float.IsFinite(storeyHeight) || storeyHeight <= 0f)
                throw new ArgumentOutOfRangeException(nameof(storeyHeight),
                    "Floor index must be nonnegative and storey height must be finite and positive.");
            ValidateSurfaceArrays(floors, floorColliders, nameof(floors));
            ValidateSurfaceArrays(walls, wallColliders, nameof(walls));
            if (contents == null)
                throw new ArgumentNullException(nameof(contents));
            if (properties == null) properties = new MaterialPropertyBlock();

            var storey = new Storey
            {
                Root = root,
                WholeInterior = wholeInterior,
                OcclusionBounds = wholeInterior,
                FloorIndex = floorIndex,
                StoreyHeight = storeyHeight,
                IsRoof = roof,
                Floors = new Surface[floors.Length],
                Walls = new Surface[walls.Length],
                Contents = new ContentVisibility[contents.Length]
            };
            for (int index = 0; index < floors.Length; index++)
            {
                storey.Floors[index] = CreateSurface(floors[index], floorColliders[index]);
                IncludeColliderBounds(storey, floorColliders[index]);
            }
            for (int index = 0; index < walls.Length; index++)
            {
                storey.Walls[index] = CreateSurface(walls[index], wallColliders[index]);
                IncludeColliderBounds(storey, wallColliders[index]);
            }
            for (int index = 0; index < contents.Length; index++)
                storey.Contents[index] = new ContentVisibility
                {
                    Renderer = contents[index],
                    OriginalEnabled = contents[index] != null && contents[index].enabled
                };
            storeys.Add(storey);
        }

        private static void ValidateSurfaceArrays(Renderer[] renderers, Collider[] colliders, string name)
        {
            if (renderers == null || colliders == null || renderers.Length != colliders.Length)
                throw new ArgumentException("Renderers and colliders must have matching arrays.", name);
        }

        public static int CalculateActiveFloor(float localPlayerRootY, float storeyHeight)
        {
            // Player root is 0.5 m above its feet. The 0.08 m boundary tolerance accommodates
            // the floor surface and CharacterController contact offset, not a visual offset.
            return Mathf.Max(0, Mathf.FloorToInt((localPlayerRootY - 0.5f + 0.08f) / storeyHeight));
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
            HiddenUpperStoreyRendererCount = 0;
            insideStoreyRoots.Clear();
            if (camera == null)
                return;

            // Root is .5m above the ground; the normalized presentation is about 1.8m high.
            Ray torsoRay = CreateSightRay(camera, playerFeet + Vector3.up * 0.4f, out float torsoDistance);
            Ray headRay = CreateSightRay(camera, playerFeet + Vector3.up * 1.15f, out float headDistance);
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

            for (int index = 0; index < storeys.Count; index++)
            {
                Storey storey = storeys[index];
                if (storey.Root == null)
                    continue;
                if (!storey.Root.gameObject.activeInHierarchy)
                {
                    RestoreStorey(storey);
                    continue;
                }

                Vector3 localPlayer = storey.Root.InverseTransformPoint(playerFeet);
                bool inside = storey.WholeInterior.Contains(localPlayer);
                if (inside && insideStoreyRoots.Add(storey.Root))
                    InsideBuildingCount++;
                int activeFloor = CalculateActiveFloor(localPlayer.y, storey.StoreyHeight);
                bool hide = inside && (storey.IsRoof || storey.FloorIndex > activeFloor);
                SetStoreyVisibility(storey, hide);
                if (hide)
                    continue;

                Bounds worldBounds = TransformBounds(storey.Root.localToWorldMatrix, storey.OcclusionBounds);
                bool mayOcclude = inside ||
                    IntersectsSegment(worldBounds, torsoRay, torsoDistance) ||
                    IntersectsSegment(worldBounds, headRay, headDistance);
                // The occupied floor stays opaque. Exterior floors/roofs can still fade when
                // their real collider obstructs the view; current-storey walls retain the old fade.
                for (int floor = 0; floor < storey.Floors.Length; floor++)
                {
                    Surface surface = storey.Floors[floor];
                    if (inside)
                        SetOpacity(surface, Mathf.MoveTowards(surface != null ? surface.Opacity : 1f, 1f, fadeStep));
                    else
                        UpdateSurface(surface, WallOpacity, false, mayOcclude,
                            torsoRay, torsoDistance, headRay, headDistance, fadeStep);
                }
                for (int wall = 0; wall < storey.Walls.Length; wall++)
                    UpdateSurface(storey.Walls[wall], WallOpacity,
                        inside && storey.FloorIndex == activeFloor, mayOcclude,
                        torsoRay, torsoDistance, headRay, headDistance, fadeStep);
            }
        }

        private void SetStoreyVisibility(Storey storey, bool hide)
        {
            for (int index = 0; index < storey.Floors.Length; index++)
                SetSurfaceVisibility(storey.Floors[index], hide);
            for (int index = 0; index < storey.Walls.Length; index++)
                SetSurfaceVisibility(storey.Walls[index], hide);
            for (int index = 0; index < storey.Contents.Length; index++)
            {
                ContentVisibility content = storey.Contents[index];
                if (content.Renderer == null)
                    continue;
                content.Renderer.enabled = content.OriginalEnabled && !hide;
                if (hide && content.OriginalEnabled)
                    HiddenUpperStoreyRendererCount++;
            }
        }

        private void SetSurfaceVisibility(Surface surface, bool hide)
        {
            if (surface == null || surface.Renderer == null)
                return;
            surface.Renderer.enabled = surface.OriginalEnabled && !hide;
            if (hide && surface.OriginalEnabled)
                HiddenUpperStoreyRendererCount++;
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
            Material faded = material;
            if (material != null && material.renderQueue < (int)RenderQueue.Transparent)
            {
                if (!fadeMaterials.TryGetValue(material, out faded))
                {
                    faded = new Material(material) { name = material.name + " (occlusion fade)", hideFlags = HideFlags.DontSave };
                    faded.SetFloat("_ZWrite", 0f);
                    faded.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
                    faded.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                    faded.SetOverrideTag("RenderType", "Transparent");
                    faded.renderQueue = (int)RenderQueue.Transparent;
                    fadeMaterials.Add(material, faded);
                }
            }
            return new Surface { Renderer = renderer, Collider = collider, BaseColor = color,
                OriginalEnabled = renderer.enabled,
                OpaqueMaterial = material, FadedMaterial = faded };
        }

        private void SetOpacity(Surface surface, float opacity)
        {
            if (surface == null || surface.Renderer == null || surface.Opacity == opacity)
                return;

            surface.Renderer.GetPropertyBlock(properties);
            // Fully visible boxes use normal depth writes. Only occluding surfaces enter the blend pass.
            Material targetMaterial = opacity < 0.999f ? surface.FadedMaterial : surface.OpaqueMaterial;
            if (surface.Renderer.sharedMaterial != targetMaterial)
                surface.Renderer.sharedMaterial = targetMaterial;
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

        private static void IncludeColliderBounds(Storey storey, Collider collider)
        {
            if (collider != null)
                storey.OcclusionBounds.Encapsulate(
                    TransformBounds(storey.Root.worldToLocalMatrix, collider.bounds));
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
            for (int index = 0; index < storeys.Count; index++)
                RestoreStorey(storeys[index]);
            InsideBuildingCount = 0;
            FadedRendererCount = 0;
            HiddenUpperStoreyRendererCount = 0;
            insideStoreyRoots.Clear();
        }

        private void RestoreStorey(Storey storey)
        {
            SetStoreyVisibility(storey, false);
            for (int index = 0; index < storey.Floors.Length; index++)
                SetOpacity(storey.Floors[index], 1f);
            for (int index = 0; index < storey.Walls.Length; index++)
                SetOpacity(storey.Walls[index], 1f);
        }

        private void OnDestroy()
        {
            foreach (Material material in fadeMaterials.Values)
                if (material != null) Destroy(material);
            fadeMaterials.Clear();
        }
    }
}
