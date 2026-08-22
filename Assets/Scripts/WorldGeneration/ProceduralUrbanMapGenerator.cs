using System;
using System.Collections.Generic;
using Unity.AI.Navigation;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    [DefaultExecutionOrder(-10000)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(NavMeshSurface))]
    public sealed class ProceduralUrbanMapGenerator : MonoBehaviour
    {
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");

        private static readonly Color GroundColor = new Color(0.19f, 0.18f, 0.16f, 1f);
        private static readonly Color SecondaryRoadColor = new Color(0.18f, 0.20f, 0.22f, 1f);
        private static readonly Color PrimaryRoadColor = new Color(0.25f, 0.27f, 0.29f, 1f);
        private static readonly Color BoundaryColor = new Color(0.24f, 0.12f, 0.11f, 1f);
        private static readonly Color[] BuildingColors =
        {
            new Color(0.43f, 0.31f, 0.27f, 1f),
            new Color(0.34f, 0.39f, 0.43f, 1f),
            new Color(0.42f, 0.42f, 0.34f, 1f),
            new Color(0.31f, 0.36f, 0.32f, 1f),
            new Color(0.40f, 0.29f, 0.34f, 1f)
        };

        [Header("Existing Scene Anchors")]
        [SerializeField] private Transform entryAnchor;
        [SerializeField] private Transform returnPortal;
        [SerializeField] private GameObject legacyGround;
        [SerializeField] private Transform[] additionalProtectedAnchors;
        [SerializeField] private NavMeshSurface navMeshSurface;

        [Header("Seed")]
        [SerializeField] private bool randomizeSeedOnAwake = true;
        [SerializeField] private int fixedSeed = 41721;

        [Header("City Shape")]
        [SerializeField, Min(2)] private int minBlocksX = 4;
        [SerializeField, Min(2)] private int maxBlocksX = 6;
        [SerializeField, Min(2)] private int minBlocksZ = 4;
        [SerializeField, Min(2)] private int maxBlocksZ = 6;
        [SerializeField, Min(4f)] private float minBlockSize = 14f;
        [SerializeField, Min(4f)] private float maxBlockSize = 20f;
        [SerializeField, Min(0f)] private float intersectionJitter = 1.35f;
        [SerializeField] private Vector2 cityRotationRange = new Vector2(35f, 55f);
        [SerializeField, Min(2f)] private float outerMargin = 6f;

        [Header("Roads")]
        [SerializeField, Min(1f)] private float secondaryRoadWidth = 3.2f;
        [SerializeField, Min(1f)] private float primaryRoadWidth = 5.2f;
        [SerializeField, Range(0f, 0.45f)] private float minorRoadRemovalChance = 0.18f;

        [Header("Graybox Buildings")]
        [SerializeField, Min(0f)] private float buildingSetback = 1.2f;
        [SerializeField, Min(0f)] private float lotGap = 0.9f;
        [SerializeField, Range(0f, 1f)] private float buildingDensity = 0.78f;
        [SerializeField, Min(1f)] private float minBuildingHeight = 2.75f;
        [SerializeField, Min(1f)] private float maxBuildingHeight = 8.5f;
        [SerializeField, Min(0f)] private float anchorClearance = 4.5f;
        [SerializeField, Min(0f)] private float protectedAnchorClearance = 3.5f;

        [Header("Derived Navigation")]
        [SerializeField] private bool buildRuntimeNavMesh = true;
        [SerializeField, Min(0.5f)] private float navMeshSampleRadius = 2.5f;

        private Transform generatedContent;
        private Material runtimeMaterial;
        private NavMeshData runtimeNavMeshData;
        private UrbanMapLayout pendingNavigationLayout;
        private bool hasStarted;
        private bool legacyGroundWasActive;
        private bool legacyGroundStateCaptured;

        public UrbanMapLayout CurrentLayout { get; private set; }
        public int CurrentSeed { get; private set; }
        public bool NavigationPathComplete { get; private set; }
        public bool NavigationBuildPending => pendingNavigationLayout != null;
        public Transform GeneratedContent => generatedContent;
        public UrbanMapGenerationParameters GenerationParameters => CreateParameters();

        private void Awake()
        {
            if (!HasValidConfiguration())
            {
                enabled = false;
                return;
            }

            int seed = randomizeSeedOnAwake ? CreateRuntimeSeed() : fixedSeed;
            GenerateWithSeed(seed);
        }

        private void Start()
        {
            hasStarted = true;
            if (pendingNavigationLayout != null && CurrentLayout == pendingNavigationLayout)
            {
                CompleteNavigationBuild(pendingNavigationLayout);
            }
        }

        private void OnDestroy()
        {
            ClearRuntimeNavMeshData();

            if (runtimeMaterial != null)
            {
                Destroy(runtimeMaterial);
                runtimeMaterial = null;
            }

            if (legacyGroundStateCaptured && legacyGround != null)
            {
                legacyGround.SetActive(legacyGroundWasActive);
            }
        }

        /// <summary>
        /// Generates the authoritative layout and graybox geometry for a seed.
        /// </summary>
        /// <returns>
        /// True when generation was accepted. During the component's early Awake this can
        /// include a NavMesh build scheduled for Start; NavigationBuildPending and
        /// NavigationPathComplete expose the derived navigation state explicitly.
        /// </returns>
        public bool GenerateWithSeed(int seed)
        {
            UrbanMapLayout layout;

            try
            {
                layout = PlanLayout(seed);
            }
            catch (Exception exception)
            {
                Debug.LogError($"Urban map generation failed for seed {seed}: {exception.Message}", this);
                return false;
            }

            ClearGeneratedContent();
            CaptureAndDisableLegacyGround();
            EnsureRuntimeMaterial();

            CurrentSeed = seed;
            CurrentLayout = layout;
            generatedContent = new GameObject($"GeneratedUrbanMap_Seed_{seed}").transform;
            generatedContent.SetParent(transform, false);
            generatedContent.SetPositionAndRotation(
                new Vector3(entryAnchor.position.x, 0f, entryAnchor.position.z),
                Quaternion.Euler(0f, layout.CityRotationDegrees, 0f));

            CreateGround(layout);
            CreateRoads(layout);
            CreateBuildings(layout);
            CreateBoundaries(layout);
            PlaceExistingPortal(layout);

            Physics.SyncTransforms();

            if (!buildRuntimeNavMesh)
            {
                NavigationPathComplete = true;
                LogGenerationSummary(layout);
                return true;
            }

            NavigationPathComplete = false;
            if (Application.isPlaying && !hasStarted)
            {
                // NavMeshSurface.OnEnable runs after this component's early Awake.
                // Defer the derived bake until Start so the built data is registered.
                pendingNavigationLayout = layout;
                return true;
            }

            CompleteNavigationBuild(layout);
            return NavigationPathComplete;
        }

        public UrbanMapLayout PlanLayout(int seed)
        {
            if (entryAnchor == null)
            {
                throw new InvalidOperationException("Cannot plan an urban map without the existing RaidEntry Transform.");
            }

            UrbanMapGenerationParameters parameters = CreateParameters();
            if (!parameters.TryValidate(out string settingsError))
            {
                throw new InvalidOperationException($"Cannot plan an urban map: {settingsError}");
            }

            return UrbanMapLayoutPlanner.Generate(
                seed,
                ToPlanar(entryAnchor.position),
                CollectProtectedWorldPositions(),
                parameters);
        }

        public void ClearGeneratedContent()
        {
            NavigationPathComplete = false;
            CurrentLayout = null;
            pendingNavigationLayout = null;

            ClearRuntimeNavMeshData();

            if (generatedContent == null)
            {
                return;
            }

            generatedContent.gameObject.SetActive(false);
            Destroy(generatedContent.gameObject);
            generatedContent = null;
        }

        private void CompleteNavigationBuild(UrbanMapLayout layout)
        {
            pendingNavigationLayout = null;
            Physics.SyncTransforms();
            NavigationPathComplete = BuildAndValidateNavigation(layout);
            LogGenerationSummary(layout);
        }

        private void LogGenerationSummary(UrbanMapLayout layout)
        {
            ulong layoutHash = UrbanMapLayoutValidator.ComputeStableHash(layout);
            Debug.Log(
                $"Urban map generated. Version={layout.GeneratorVersion}, Seed={layout.Seed}, " +
                $"Size={layout.LocalBounds.width:F1}x{layout.LocalBounds.height:F1}, " +
                $"Roads={layout.Roads.Count}, Buildings={layout.Buildings.Count}, " +
                $"NavPathComplete={NavigationPathComplete}, Hash={layoutHash:X16}.",
                this);
        }

        private bool HasValidConfiguration()
        {
            if (entryAnchor == null)
            {
                Debug.LogError("ProceduralUrbanMapGenerator requires the existing RaidEntry Transform.", this);
                return false;
            }

            if (returnPortal == null)
            {
                Debug.LogError("ProceduralUrbanMapGenerator requires the existing ReturnPortal Transform.", this);
                return false;
            }

            if (navMeshSurface == null)
            {
                navMeshSurface = GetComponent<NavMeshSurface>();
            }

            if (buildRuntimeNavMesh && navMeshSurface == null)
            {
                Debug.LogError("ProceduralUrbanMapGenerator requires a NavMeshSurface.", this);
                return false;
            }

            return true;
        }

        private UrbanMapGenerationParameters CreateParameters()
        {
            return new UrbanMapGenerationParameters(
                minBlocksX,
                maxBlocksX,
                minBlocksZ,
                maxBlocksZ,
                minBlockSize,
                maxBlockSize,
                intersectionJitter,
                Mathf.Min(cityRotationRange.x, cityRotationRange.y),
                Mathf.Max(cityRotationRange.x, cityRotationRange.y),
                secondaryRoadWidth,
                primaryRoadWidth,
                minorRoadRemovalChance,
                outerMargin,
                buildingSetback,
                lotGap,
                buildingDensity,
                minBuildingHeight,
                maxBuildingHeight,
                anchorClearance,
                protectedAnchorClearance);
        }

        private List<Vector2> CollectProtectedWorldPositions()
        {
            var positions = new List<Vector2>();
            if (additionalProtectedAnchors == null)
            {
                return positions;
            }

            for (int index = 0; index < additionalProtectedAnchors.Length; index++)
            {
                Transform anchor = additionalProtectedAnchors[index];
                if (anchor != null)
                {
                    positions.Add(ToPlanar(anchor.position));
                }
            }

            return positions;
        }

        private void CaptureAndDisableLegacyGround()
        {
            if (legacyGround == null)
            {
                return;
            }

            if (!legacyGroundStateCaptured)
            {
                legacyGroundWasActive = legacyGround.activeSelf;
                legacyGroundStateCaptured = true;
            }

            legacyGround.SetActive(false);
        }

        private void EnsureRuntimeMaterial()
        {
            if (runtimeMaterial != null)
            {
                return;
            }

            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }

            if (shader == null)
            {
                throw new InvalidOperationException("No compatible lit shader is available for generated graybox geometry.");
            }

            runtimeMaterial = new Material(shader)
            {
                name = "Runtime Urban Graybox Material",
                hideFlags = HideFlags.DontSave
            };
        }

        private void CreateGround(UrbanMapLayout layout)
        {
            Rect bounds = layout.LocalBounds;
            CreatePrimitive(
                "GeneratedGround",
                PrimitiveType.Cube,
                new Vector3(bounds.center.x, -0.25f, bounds.center.y),
                Quaternion.identity,
                new Vector3(bounds.width, 0.5f, bounds.height),
                GroundColor,
                hasCollider: true,
                blocksPlayer: false,
                markNotWalkable: false,
                castsShadows: false);
        }

        private void CreateRoads(UrbanMapLayout layout)
        {
            for (int index = 0; index < layout.Roads.Count; index++)
            {
                UrbanRoadSegment road = layout.Roads[index];
                Vector2 direction = road.End - road.Start;
                float yaw = Mathf.Atan2(direction.x, direction.y) * Mathf.Rad2Deg;
                Vector2 midpoint = (road.Start + road.End) * 0.5f;

                CreatePrimitive(
                    road.IsPrimary ? $"PrimaryRoad_{index:000}" : $"Road_{index:000}",
                    PrimitiveType.Cube,
                    new Vector3(midpoint.x, 0.035f, midpoint.y),
                    Quaternion.Euler(0f, yaw, 0f),
                    new Vector3(road.Width, 0.07f, road.Length + 0.15f),
                    road.IsPrimary ? PrimaryRoadColor : SecondaryRoadColor,
                    hasCollider: false,
                    blocksPlayer: false,
                    markNotWalkable: false,
                    castsShadows: false);
            }
        }

        private void CreateBuildings(UrbanMapLayout layout)
        {
            for (int index = 0; index < layout.Buildings.Count; index++)
            {
                UrbanBuildingPlacement building = layout.Buildings[index];
                Color color = BuildingColors[Mathf.Abs(building.PaletteIndex) % BuildingColors.Length];
                CreatePrimitive(
                    $"Building_{index:000}_Palette_{building.PaletteIndex}",
                    PrimitiveType.Cube,
                    new Vector3(building.Center.x, building.Height * 0.5f, building.Center.y),
                    Quaternion.identity,
                    new Vector3(building.Size.x, building.Height, building.Size.y),
                    color,
                    hasCollider: true,
                    blocksPlayer: true,
                    markNotWalkable: true,
                    castsShadows: true);
            }
        }

        private void CreateBoundaries(UrbanMapLayout layout)
        {
            Rect bounds = layout.LocalBounds;
            const float thickness = 1f;
            const float height = 1.2f;

            CreateBoundary("Boundary_West", new Vector3(bounds.xMin, height * 0.5f, bounds.center.y), new Vector3(thickness, height, bounds.height + thickness * 2f));
            CreateBoundary("Boundary_East", new Vector3(bounds.xMax, height * 0.5f, bounds.center.y), new Vector3(thickness, height, bounds.height + thickness * 2f));
            CreateBoundary("Boundary_South", new Vector3(bounds.center.x, height * 0.5f, bounds.yMin), new Vector3(bounds.width, height, thickness));
            CreateBoundary("Boundary_North", new Vector3(bounds.center.x, height * 0.5f, bounds.yMax), new Vector3(bounds.width, height, thickness));
        }

        private void CreateBoundary(string objectName, Vector3 localPosition, Vector3 localScale)
        {
            CreatePrimitive(
                objectName,
                PrimitiveType.Cube,
                localPosition,
                Quaternion.identity,
                localScale,
                BoundaryColor,
                hasCollider: true,
                blocksPlayer: true,
                markNotWalkable: true,
                castsShadows: false);
        }

        private GameObject CreatePrimitive(
            string objectName,
            PrimitiveType primitiveType,
            Vector3 localPosition,
            Quaternion localRotation,
            Vector3 localScale,
            Color color,
            bool hasCollider,
            bool blocksPlayer,
            bool markNotWalkable,
            bool castsShadows)
        {
            GameObject instance = GameObject.CreatePrimitive(primitiveType);
            instance.name = objectName;
            instance.transform.SetParent(generatedContent, false);
            instance.transform.localPosition = localPosition;
            instance.transform.localRotation = localRotation;
            instance.transform.localScale = localScale;

            Renderer renderer = instance.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.sharedMaterial = runtimeMaterial;
                renderer.shadowCastingMode = castsShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                renderer.receiveShadows = castsShadows;
                var propertyBlock = new MaterialPropertyBlock();
                propertyBlock.SetColor(BaseColorId, color);
                propertyBlock.SetColor(ColorId, color);
                renderer.SetPropertyBlock(propertyBlock);
            }

            Collider collider = instance.GetComponent<Collider>();
            if (!hasCollider && collider != null)
            {
                collider.enabled = false;
                Destroy(collider);
            }

            if (blocksPlayer)
            {
                instance.tag = "Obstacle";
            }

            if (markNotWalkable)
            {
                NavMeshModifier modifier = instance.AddComponent<NavMeshModifier>();
                modifier.overrideArea = true;
                modifier.area = 1;
            }

            return instance;
        }

        private void PlaceExistingPortal(UrbanMapLayout layout)
        {
            Vector3 portalPosition = generatedContent.TransformPoint(
                new Vector3(layout.PortalLocalPosition.x, 0.5f, layout.PortalLocalPosition.y));
            returnPortal.SetPositionAndRotation(portalPosition, generatedContent.rotation);
        }

        private bool BuildAndValidateNavigation(UrbanMapLayout layout)
        {
            navMeshSurface.collectObjects = CollectObjects.Children;
            navMeshSurface.useGeometry = NavMeshCollectGeometry.PhysicsColliders;
            navMeshSurface.layerMask = ~0;
            navMeshSurface.ignoreNavMeshAgent = true;
            navMeshSurface.ignoreNavMeshObstacle = true;
            navMeshSurface.BuildNavMesh();
            runtimeNavMeshData = navMeshSurface.navMeshData;

            Vector3 entryWorld = generatedContent.TransformPoint(
                new Vector3(layout.EntryLocalPosition.x, 0f, layout.EntryLocalPosition.y));
            Vector3 portalApproachWorld = generatedContent.TransformPoint(
                new Vector3(layout.PortalApproachLocalPosition.x, 0f, layout.PortalApproachLocalPosition.y));

            if (!NavMesh.SamplePosition(entryWorld, out NavMeshHit startHit, navMeshSampleRadius, NavMesh.AllAreas))
            {
                Debug.LogError(
                    $"Generated urban map seed {layout.Seed} has no NavMesh near RaidEntry. " +
                    DescribeNavigation(entryWorld, portalApproachWorld),
                    this);
                return false;
            }

            if (!NavMesh.SamplePosition(portalApproachWorld, out NavMeshHit endHit, navMeshSampleRadius, NavMesh.AllAreas))
            {
                Debug.LogError(
                    $"Generated urban map seed {layout.Seed} has no NavMesh near ReturnPortal. " +
                    DescribeNavigation(entryWorld, portalApproachWorld),
                    this);
                return false;
            }

            var path = new NavMeshPath();
            bool calculated = NavMesh.CalculatePath(startHit.position, endHit.position, NavMesh.AllAreas, path);
            if (!calculated || path.status != NavMeshPathStatus.PathComplete)
            {
                Debug.LogError(
                    $"Generated urban map seed {layout.Seed} does not have a complete RaidEntry-to-ReturnPortal NavMesh path. " +
                    $"Calculated={calculated}, Status={path.status}.",
                    this);
                return false;
            }

            return true;
        }

        private string DescribeNavigation(Vector3 entryWorld, Vector3 portalApproachWorld)
        {
            Bounds sourceBounds = runtimeNavMeshData == null ? default : runtimeNavMeshData.sourceBounds;
            NavMeshTriangulation triangulation = NavMesh.CalculateTriangulation();
            string triangulationBounds = "empty";
            Transform ground = generatedContent == null ? null : generatedContent.Find("GeneratedGround");
            Collider groundCollider = ground == null ? null : ground.GetComponent<Collider>();
            string groundDescription = groundCollider == null
                ? "missing"
                : $"enabled={groundCollider.enabled}, boundsCenter={groundCollider.bounds.center}, boundsSize={groundCollider.bounds.size}";

            if (triangulation.vertices != null && triangulation.vertices.Length > 0)
            {
                var bounds = new Bounds(triangulation.vertices[0], Vector3.zero);
                for (int index = 1; index < triangulation.vertices.Length; index++)
                {
                    bounds.Encapsulate(triangulation.vertices[index]);
                }

                triangulationBounds = $"center={bounds.center}, size={bounds.size}";
            }

            return
                $"Entry={entryWorld}, PortalApproach={portalApproachWorld}, " +
                $"SurfacePosition={navMeshSurface.transform.position}, SurfaceRotation={navMeshSurface.transform.eulerAngles}, " +
                $"SurfaceActive={navMeshSurface.isActiveAndEnabled}, " +
                $"HasData={runtimeNavMeshData != null}, SourceBoundsCenter={sourceBounds.center}, " +
                $"SourceBoundsSize={sourceBounds.size}, Vertices={triangulation.vertices?.Length ?? 0}, " +
                $"TriangulationBounds={triangulationBounds}, GroundCollider={groundDescription}.";
        }

        private void ClearRuntimeNavMeshData()
        {
            if (runtimeNavMeshData == null)
            {
                return;
            }

            if (navMeshSurface != null && navMeshSurface.navMeshData == runtimeNavMeshData)
            {
                navMeshSurface.RemoveData();
                navMeshSurface.navMeshData = null;
            }

            Destroy(runtimeNavMeshData);
            runtimeNavMeshData = null;
        }

        private static Vector2 ToPlanar(Vector3 position)
        {
            return new Vector2(position.x, position.z);
        }

        private int CreateRuntimeSeed()
        {
            unchecked
            {
                long ticks = DateTime.UtcNow.Ticks;
                return Environment.TickCount ^ (int)ticks ^ (int)(ticks >> 32);
            }
        }
    }
}
