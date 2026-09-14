using System;
using System.Collections.Generic;
using FantasySurvival.AI;
using FantasySurvival.WorldLighting;
using Unity.AI.Navigation;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Rendering;
using UnityEngine.Serialization;

namespace FantasySurvival.WorldGeneration
{
    [DefaultExecutionOrder(-10000)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(NavMeshSurface))]
    public sealed class ProceduralUrbanMapGenerator : MonoBehaviour, IEnemyPatrolPointSource
    {
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");
        private static readonly int BaseMapId = Shader.PropertyToID("_BaseMap");
        private static readonly int MainTexId = Shader.PropertyToID("_MainTex");
        private static readonly int GlossinessId = Shader.PropertyToID("_Glossiness");
        private static readonly int SmoothnessId = Shader.PropertyToID("_Smoothness");

        private static readonly Color GroundColor = new Color(0.19f, 0.18f, 0.16f, 1f);
        private static readonly Color SecondaryRoadColor = new Color(0.18f, 0.20f, 0.22f, 1f);
        private static readonly Color PrimaryRoadColor = new Color(0.25f, 0.27f, 0.29f, 1f);
        private static readonly Color SidewalkColor = new Color(0.46f, 0.44f, 0.40f, 1f);
        private static readonly Color MedicalPoiBuildingColor = new Color(0.18f, 0.62f, 0.46f, 1f);
        private const float SurfaceHeight = 0.005f;
        private const float SidewalkSurfaceHeight = 0.12f;
        public const float PavementElevation = 0.2f;
        [Header("Existing Scene Anchors")]
        [SerializeField] private Transform entryAnchor;
        [SerializeField] private Transform returnPortal;
        [SerializeField] private GameObject legacyGround;
        [SerializeField] private Transform[] additionalProtectedAnchors;
        [SerializeField] private NavMeshSurface navMeshSurface;

        [Header("Seed")]
        [SerializeField] private bool randomizeSeedOnAwake = true;
        [SerializeField] private int fixedSeed = 41721;

        [Header("Fixed Tile Map")]
        [SerializeField, Min(17)] private int mapTilesPerAxis = 145;
        [SerializeField, Min(2)] private int blocksPerAxis = 6;
        [SerializeField, Min(1)] private int borderTiles = 12;
        [SerializeField, Min(0.25f)] private float tileWorldSize = 2f;

        [Header("Optional Isometric Atlas Prototype")]
        [SerializeField] private IsometricUrbanStyle isometricStyle;
        public IsometricUrbanStyle IsometricStyle => isometricStyle;
        public int CheckpointGeneratorVersion => isometricStyle != null ? 1004 : CurrentLayout.GeneratorVersion;
        private UrbanOcclusionFader occlusionFader;

        [Header("Octilinear Road Graph")]
        [SerializeField, Min(7)] private int secondaryRoadWidthTiles = 7;
        [SerializeField, Min(7)] private int primaryRoadWidthTiles = 9;
        [SerializeField, Range(0f, 1f)] private float additionalRoadChance = 0.65f;
        [SerializeField, Range(0f, 1f)] private float diagonalRoadChance = 0.2f;
        [SerializeField, Min(1)] private int sidewalkWidthTiles = 1;

        [Header("Prototype Exterior Buildings")]
        [SerializeField] private GameObject[] buildingVisualPrefabs;
        [SerializeField, Min(0f)] private float buildingSetback;
        [SerializeField, Min(0f)] private float lotGap;
        [SerializeField, Min(3)] private int minBuildingFrontageTiles = 4;
        [SerializeField, Min(3)] private int maxBuildingFrontageTiles = 5;
        [SerializeField, Min(3)] private int minBuildingDepthTiles = 4;
        [SerializeField, Min(3)] private int maxBuildingDepthTiles = 4;
        [SerializeField, Range(0f, 1f)] private float buildingDensity = 1f;
        [SerializeField, Min(1f)] private float minBuildingHeight = 10.5f;
        [SerializeField, Min(1f)] private float maxBuildingHeight = 18f;
        [SerializeField, Min(0f)] private float anchorClearance = 10f;
        [SerializeField, Min(0f)] private float protectedAnchorClearance = 8f;

        [Header("Street Furniture Sockets")]
        [SerializeField] private bool instantiateStreetTrees = true;
        [SerializeField] private bool instantiateStreetLamps = true;
        [SerializeField] private GameObject streetLampPrefab;
        [FormerlySerializedAs("instantiatePrototypeStreetFurniture")]
        [SerializeField] private bool instantiatePrototypeClutter;
        [SerializeField, Min(1)] private int junctionFurnitureClearanceTiles = 3;
        [SerializeField, Min(2)] private int streetTreeSpacingTiles = 7;
        [SerializeField, Min(2)] private int streetLampSpacingTiles = 18;
        [SerializeField, Min(2)] private int clutterSpacingTiles = 5;
        [SerializeField, Range(0f, 1f)] private float clutterChance = 0.22f;

        [Header("Derived Navigation")]
        [SerializeField] private bool buildRuntimeNavMesh = true;
        [SerializeField, Min(0.5f)] private float navMeshSampleRadius = 2.5f;

        private Transform generatedContent;
        private Material runtimeMaterial;
        private readonly Dictionary<Material, Material> runtimeBuildingMaterials =
            new Dictionary<Material, Material>();
        private Material[] runtimeSurfaceMaterials;
        private IsometricUrbanStyle.SurfaceVariantSampler[] runtimeSurfaceSamplers;
        private int[][] runtimeSurfaceVariantMaterials;
        private Mesh runtimeSurfaceMesh;
        private NavMeshData runtimeNavMeshData;
        private UrbanMapLayout pendingNavigationLayout;
        private bool hasStarted;
        private bool legacyGroundWasActive;
        private bool legacyGroundStateCaptured;

        public UrbanMapLayout CurrentLayout { get; private set; }
        public int CurrentSeed { get; private set; }
        private bool HasStreetFurnitureVisualsEnabled =>
            instantiateStreetTrees || instantiateStreetLamps || instantiatePrototypeClutter;
        public bool NavigationPathComplete { get; private set; }
        public bool NavigationBuildPending => pendingNavigationLayout != null;
        public Transform GeneratedContent => generatedContent;
        public GameObject StreetLampPrefab => streetLampPrefab;
        public UrbanMapGenerationParameters GenerationParameters => CreateParameters();
        public bool IsPatrolPointSourceReady =>
            CurrentLayout != null &&
            generatedContent != null &&
            !NavigationBuildPending &&
            NavigationPathComplete;
        public int PatrolPointCount => CurrentLayout?.Candidates?.Count ?? 0;

        /// <summary>
        /// Published after deterministic geometry and the portal pose exist, but before the
        /// derived NavMesh is built. Early scene bindings use this boundary to assign authored
        /// entities before their normal Awake methods capture home positions or initialize data.
        /// </summary>
        public event Action<UrbanMapLayout> LayoutGeometryGenerated;

        public bool TryGetPatrolPoint(int index, out Vector3 worldPosition)
        {
            if (!IsPatrolPointSourceReady ||
                index < 0 ||
                index >= CurrentLayout.Candidates.Count)
            {
                worldPosition = default;
                return false;
            }

            UrbanSpatialCandidate candidate = CurrentLayout.Candidates[index];
            worldPosition = generatedContent.TransformPoint(
                new Vector3(candidate.LocalPosition.x, 0f, candidate.LocalPosition.y));
            return true;
        }

        private void Awake()
        {
            // RaidCheckpointSceneBinding runs earlier and may have already generated the
            // recovered seed. Re-randomizing here would replace the authoritative layout
            // before the world checkpoint can be applied.
            if (CurrentLayout != null)
            {
                return;
            }

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

            ClearRuntimeBuildingMaterials();

            ClearRuntimeSurfaceResources();

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
            if (!HasValidConfiguration())
            {
                return false;
            }

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
            Quaternion mapRotation = Quaternion.Euler(0f, layout.CityRotationDegrees, 0f);
            Vector3 rotatedEntry = mapRotation * new Vector3(
                layout.EntryLocalPosition.x,
                0f,
                layout.EntryLocalPosition.y);
            generatedContent.SetPositionAndRotation(
                new Vector3(entryAnchor.position.x, 0f, entryAnchor.position.z) - rotatedEntry,
                mapRotation);

            if (isometricStyle != null)
            {
                occlusionFader = generatedContent.gameObject.AddComponent<UrbanOcclusionFader>();
                var view = generatedContent.gameObject.AddComponent<IsometricUrbanView>();
                view.cityYaw = generatedContent.eulerAngles.y;
            }

            CreateSurfaceTiles(layout);
            CreateBuildings(layout);
            if (HasStreetFurnitureVisualsEnabled)
            {
                CreateStreetFurniture(layout);
            }
            CreateBoundaries(layout);
            PlaceExistingPortal(layout);

            Physics.SyncTransforms();
            LayoutGeometryGenerated?.Invoke(layout);

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

        public ulong ComputeCheckpointWorldHash(UrbanRaidSpawnManifest manifest)
        {
            ulong hash = UrbanMapLayoutValidator.ComputeStableWorldHash(CurrentLayout, manifest);
            if (isometricStyle == null) return hash;
            // Physical mode and dimensions must invalidate incompatible old recovery worlds.
            unchecked
            {
                Add(CheckpointGeneratorVersion);
                Add(BitConverter.SingleToInt32Bits(isometricStyle.wallHeight));
                Add(BitConverter.SingleToInt32Bits(isometricStyle.wallThickness));
                Add(BitConverter.SingleToInt32Bits(isometricStyle.doorWidth));
                Add(BitConverter.SingleToInt32Bits(PavementElevation));
            }
            return hash;
            void Add(int value) { unchecked { hash = (hash ^ (uint)value) * 1099511628211UL; } }
        }

        public bool TryValidateReachableLocalPoint(
            Vector2 localPosition,
            string pointLabel,
            out string error)
        {
            string label = string.IsNullOrWhiteSpace(pointLabel) ? "raid spawn" : pointLabel;
            if (CurrentLayout == null || generatedContent == null)
            {
                error = $"Cannot validate {label} before the generated urban layout exists.";
                return false;
            }

            if (NavigationBuildPending || !NavigationPathComplete || runtimeNavMeshData == null)
            {
                error = $"Cannot validate {label} before the generated urban NavMesh is ready.";
                return false;
            }

            Vector3 entryWorld = generatedContent.TransformPoint(
                new Vector3(CurrentLayout.EntryLocalPosition.x, 0f, CurrentLayout.EntryLocalPosition.y));
            Vector3 targetWorld = generatedContent.TransformPoint(
                new Vector3(localPosition.x, 0f, localPosition.y));
            if (!NavMesh.SamplePosition(entryWorld, out NavMeshHit startHit, navMeshSampleRadius, NavMesh.AllAreas))
            {
                error = $"Generated urban map has no NavMesh near RaidEntry while validating {label}.";
                return false;
            }

            if (!NavMesh.SamplePosition(targetWorld, out NavMeshHit targetHit, navMeshSampleRadius, NavMesh.AllAreas))
            {
                error = $"Generated urban map has no NavMesh near {label} at local {localPosition}.";
                return false;
            }

            var path = new NavMeshPath();
            bool calculated = NavMesh.CalculatePath(
                startHit.position,
                targetHit.position,
                NavMesh.AllAreas,
                path);
            if (!calculated || path.status != NavMeshPathStatus.PathComplete)
            {
                error =
                    $"Generated urban map has no complete RaidEntry-to-{label} path. " +
                    $"Calculated={calculated}, Status={path.status}.";
                return false;
            }

            error = null;
            return true;
        }

        public void ClearGeneratedContent()
        {
            NavigationPathComplete = false;
            CurrentLayout = null;
            pendingNavigationLayout = null;

            ClearRuntimeNavMeshData();
            ClearRuntimeSurfaceResources();

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
                $"Roads={layout.Roads.Count}, Parcels={layout.Parcels.Count}, " +
                $"Buildings={layout.Buildings.Count}, " +
                $"Tiles={layout.SurfaceGrid.Width}x{layout.SurfaceGrid.Height}, " +
                $"FurnitureSockets={layout.StreetFurniture.Count}, " +
                $"FurnitureVisuals={CountEnabledStreetFurniture(layout)}, " +
                $"Candidates={layout.Candidates.Count}, " +
                $"POIs={layout.Pois.Count}, " +
                $"NavPathComplete={NavigationPathComplete}, Hash={layoutHash:X16}.",
                this);
        }

        private bool HasValidConfiguration()
        {
            if (isometricStyle != null && !isometricStyle.TryValidate(out string artworkError))
            {
                Debug.LogError("Invalid isometric map artwork: " + artworkError, this);
                return false;
            }
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

            if (!buildRuntimeNavMesh)
            {
                Debug.LogError(
                    "ProceduralUrbanMapGenerator requires runtime NavMesh generation for " +
                    "raid arrival and content reachability validation.",
                    this);
                return false;
            }

            if (navMeshSurface == null)
            {
                Debug.LogError("ProceduralUrbanMapGenerator requires a NavMeshSurface.", this);
                return false;
            }

            if (isometricStyle == null && (buildingVisualPrefabs == null || buildingVisualPrefabs.Length == 0))
            {
                Debug.LogError(
                    "ProceduralUrbanMapGenerator requires at least one building visual prefab.",
                    this);
                return false;
            }

            for (int index = 0; isometricStyle == null && index < buildingVisualPrefabs.Length; index++)
            {
                if (buildingVisualPrefabs[index] == null)
                {
                    Debug.LogError(
                        $"ProceduralUrbanMapGenerator building visual prefab slot {index} is empty.",
                        this);
                    return false;
                }
            }

            if (instantiateStreetLamps && !HasValidStreetLampPrefab())
            {
                return false;
            }

            return true;
        }

        private bool HasValidStreetLampPrefab()
        {
            if (streetLampPrefab == null)
            {
                Debug.LogError(
                    "ProceduralUrbanMapGenerator requires the existing street-lamp prefab " +
                    "when street lamps are enabled.",
                    this);
                return false;
            }

            BoxCollider footprint = streetLampPrefab.GetComponent<BoxCollider>();
            NavMeshObstacle obstacle = streetLampPrefab.GetComponent<NavMeshObstacle>();
            NightActivatedStreetLamp nightController =
                streetLampPrefab.GetComponentInChildren<NightActivatedStreetLamp>(true);
            StylizedLightShaftEmitter shaftEmitter =
                streetLampPrefab.GetComponentInChildren<StylizedLightShaftEmitter>(true);
            Light sourceLight = nightController != null ? nightController.SourceLight : null;
            if (footprint == null || obstacle == null || nightController == null ||
                shaftEmitter == null || sourceLight == null || sourceLight.type != LightType.Spot ||
                shaftEmitter.GetComponent<Light>() != sourceLight)
            {
                Debug.LogError(
                    "ProceduralUrbanMapGenerator street-lamp prefab must retain its root " +
                    "BoxCollider/NavMeshObstacle and one connected night Spot Light with " +
                    "a stylized shaft emitter.",
                    this);
                return false;
            }

            return true;
        }

        private UrbanMapGenerationParameters CreateParameters()
        {
            return new UrbanMapGenerationParameters(
                mapTilesPerAxis,
                blocksPerAxis,
                borderTiles,
                tileWorldSize,
                secondaryRoadWidthTiles,
                primaryRoadWidthTiles,
                additionalRoadChance,
                diagonalRoadChance,
                sidewalkWidthTiles,
                buildingSetback,
                lotGap,
                minBuildingFrontageTiles,
                maxBuildingFrontageTiles,
                minBuildingDepthTiles,
                maxBuildingDepthTiles,
                buildingDensity,
                isometricStyle != null ? isometricStyle.wallHeight * 2f : minBuildingHeight,
                isometricStyle != null ? isometricStyle.wallHeight * 2f : maxBuildingHeight,
                anchorClearance,
                protectedAnchorClearance,
                junctionFurnitureClearanceTiles,
                streetTreeSpacingTiles,
                streetLampSpacingTiles,
                clutterSpacingTiles,
                clutterChance);
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

        private void CreateSurfaceTiles(UrbanMapLayout layout)
        {
            EnsureRuntimeSurfaceMaterials();

            Rect bounds = layout.LocalBounds;
            var ground = new GameObject("GeneratedGround");
            ground.transform.SetParent(generatedContent, false);
            ground.transform.localPosition = new Vector3(bounds.center.x, -0.25f, bounds.center.y);
            var groundCollider = ground.AddComponent<BoxCollider>();
            groundCollider.size = new Vector3(bounds.width, 0.5f, bounds.height);

            UrbanSurfaceGrid grid = layout.SurfaceGrid;
            var vertices = new List<Vector3>(grid.CellCount * 4);
            var normals = new List<Vector3>(grid.CellCount * 4);
            var uv = new List<Vector2>(grid.CellCount * 4);
            var trianglesBySurface = new List<int>[runtimeSurfaceMaterials.Length];
            for (int surfaceIndex = 0; surfaceIndex < trianglesBySurface.Length; surfaceIndex++)
            {
                trianglesBySurface[surfaceIndex] = new List<int>();
            }

            float halfTile = grid.TileSize * 0.5f;
            for (int z = 0; z < grid.Height; z++)
            {
                for (int x = 0; x < grid.Width; x++)
                {
                    UrbanSurfaceTileKind kind = grid.GetKind(x, z);
                    Vector2 center = grid.GetCellCenter(x, z);
                    float surfaceHeight = GetSurfaceHeight(kind);
                    int vertexStart = vertices.Count;
                    vertices.Add(new Vector3(center.x - halfTile, surfaceHeight, center.y - halfTile));
                    vertices.Add(new Vector3(center.x - halfTile, surfaceHeight, center.y + halfTile));
                    vertices.Add(new Vector3(center.x + halfTile, surfaceHeight, center.y + halfTile));
                    vertices.Add(new Vector3(center.x + halfTile, surfaceHeight, center.y - halfTile));
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    uv.Add(Vector2.zero);
                    uv.Add(Vector2.up);
                    uv.Add(Vector2.one);
                    uv.Add(Vector2.right);

                    int materialIndex = (int)kind;
                    if (isometricStyle != null)
                    {
                        // The family catalog chooses decoration only. Road-port masks and
                        // the separate directional marking geometry remain authoritative.
                        int variant = runtimeSurfaceSamplers[materialIndex].SelectVariant(CurrentSeed, x, z);
                        if (variant > 0)
                            materialIndex = runtimeSurfaceVariantMaterials[materialIndex][variant - 1];
                    }
                    List<int> triangles = trianglesBySurface[materialIndex];
                    triangles.Add(vertexStart);
                    triangles.Add(vertexStart + 1);
                    triangles.Add(vertexStart + 2);
                    triangles.Add(vertexStart);
                    triangles.Add(vertexStart + 2);
                    triangles.Add(vertexStart + 3);
                }
            }

            AddSidewalkCurbFaces(grid, vertices, normals, uv, trianglesBySurface);

            runtimeSurfaceMesh = new Mesh
            {
                name = "Runtime Urban Surface Tile Mesh",
                hideFlags = HideFlags.DontSave,
                indexFormat = IndexFormat.UInt32,
                subMeshCount = runtimeSurfaceMaterials.Length
            };
            runtimeSurfaceMesh.SetVertices(vertices);
            runtimeSurfaceMesh.SetNormals(normals);
            runtimeSurfaceMesh.SetUVs(0, uv);
            for (int surfaceIndex = 0; surfaceIndex < trianglesBySurface.Length; surfaceIndex++)
            {
                runtimeSurfaceMesh.SetTriangles(trianglesBySurface[surfaceIndex], surfaceIndex, false);
            }
            runtimeSurfaceMesh.RecalculateBounds();

            var surfaceObject = new GameObject("GeneratedSurfaceTiles");
            surfaceObject.transform.SetParent(generatedContent, false);
            var filter = surfaceObject.AddComponent<MeshFilter>();
            filter.sharedMesh = runtimeSurfaceMesh;
            if (isometricStyle != null)
                surfaceObject.AddComponent<MeshCollider>().sharedMesh = runtimeSurfaceMesh;
            var renderer = surfaceObject.AddComponent<MeshRenderer>();
            renderer.sharedMaterials = runtimeSurfaceMaterials;
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = true;
            if (isometricStyle != null)
                UrbanRoadMarkings.Create(generatedContent, layout, isometricStyle, SurfaceHeight);
        }

        private void EnsureRuntimeSurfaceMaterials()
        {
            if (runtimeSurfaceMaterials != null)
            {
                return;
            }

            if (isometricStyle != null)
            {
                // Keep the first four slots aligned with UrbanSurfaceTileKind. Structural
                // curb geometry still uses the base sidewalk material, even if its weight is zero.
                var materials = new List<Material>
                {
                    isometricStyle.CreateMaterial(isometricStyle.ground, false, "Atlas Ground", Color.white),
                    isometricStyle.CreateMaterial(isometricStyle.sidewalk, false, "Atlas Sidewalk", Color.white),
                    isometricStyle.CreateMaterial(isometricStyle.road, false, "Atlas Secondary Road", Color.white),
                    isometricStyle.CreateMaterial(isometricStyle.road, false, "Atlas Primary Road", Color.white)
                };
                runtimeSurfaceSamplers = new IsometricUrbanStyle.SurfaceVariantSampler[4];
                runtimeSurfaceVariantMaterials = new int[4][];
                AddFamily(0, isometricStyle.groundVariants, isometricStyle.ground, "Ground");
                AddFamily(1, isometricStyle.sidewalkVariants, isometricStyle.sidewalk, "Sidewalk");
                AddFamily(2, isometricStyle.roadVariants, isometricStyle.road, "Road");
                // Primary and secondary roads are one compatible family. They share the
                // compiled CDF and variant materials, retaining distinct base slots and grid kinds.
                runtimeSurfaceSamplers[3] = runtimeSurfaceSamplers[2];
                runtimeSurfaceVariantMaterials[3] = runtimeSurfaceVariantMaterials[2];
                runtimeSurfaceMaterials = materials.ToArray();
                return;

                void AddFamily(int kind, IsometricUrbanStyle.SurfaceVariantCatalog catalog,
                    IsometricUrbanStyle.AtlasPatch familyBase, string familyName)
                {
                    runtimeSurfaceSamplers[kind] = catalog.CreateSampler();
                    int[] indices = new int[catalog.variants.Length];
                    for (int index = 0; index < indices.Length; index++)
                    {
                        IsometricUrbanStyle.WeightedSurfaceVariant variant = catalog.variants[index];
                        indices[index] = -1;
                        if (variant.weight == 0f) continue;
                        indices[index] = materials.Count;
                        materials.Add(isometricStyle.CreateMaterial(variant.ResolvePatch(familyBase), false,
                            $"Atlas {familyName} Variant {index}: {variant.name}", Color.white));
                    }
                    runtimeSurfaceVariantMaterials[kind] = indices;
                }
            }

            EnsureRuntimeMaterial();
            Color[] colors = { GroundColor, SidewalkColor, SecondaryRoadColor, PrimaryRoadColor };
            runtimeSurfaceMaterials = new Material[colors.Length];
            for (int index = 0; index < colors.Length; index++)
            {
                var material = new Material(runtimeMaterial)
                {
                    name = $"Runtime Urban Surface {((UrbanSurfaceTileKind)index)}",
                    hideFlags = HideFlags.DontSave
                };
                if (material.HasProperty(BaseColorId))
                {
                    material.SetColor(BaseColorId, colors[index]);
                }
                if (material.HasProperty(ColorId))
                {
                    material.SetColor(ColorId, colors[index]);
                }
                runtimeSurfaceMaterials[index] = material;
            }
        }

        private void ClearRuntimeSurfaceResources()
        {
            runtimeSurfaceSamplers = null;
            runtimeSurfaceVariantMaterials = null;
            if (runtimeSurfaceMesh != null)
            {
                Destroy(runtimeSurfaceMesh);
                runtimeSurfaceMesh = null;
            }

            if (runtimeSurfaceMaterials == null)
            {
                return;
            }

            for (int index = 0; index < runtimeSurfaceMaterials.Length; index++)
            {
                if (runtimeSurfaceMaterials[index] != null)
                {
                    Destroy(runtimeSurfaceMaterials[index]);
                }
            }

            runtimeSurfaceMaterials = null;
        }

        private void CreateBuildings(UrbanMapLayout layout)
        {
            bool hasMedicalPoi = layout.TryGetPoi(
                UrbanPoiKind.Medical,
                out UrbanPoiPlacement medicalPoi);
            for (int index = 0; index < layout.Buildings.Count; index++)
            {
                UrbanBuildingPlacement building = layout.Buildings[index];
                bool isMedicalPoi = hasMedicalPoi && medicalPoi.BuildingIndex == index;
                Color tint = isMedicalPoi ? MedicalPoiBuildingColor : Color.white;
                CreateBuilding(
                    isMedicalPoi
                        ? $"Building_{index:000}_MedicalPoi"
                        : $"Building_{index:000}_Palette_{building.PaletteIndex}",
                    building,
                    layout.Parcels[building.SourceParcelIndex].FacadeDirection,
                    tint,
                    building.PaletteIndex,
                    isMedicalPoi);
            }
        }

        private void CreateStreetFurniture(UrbanMapLayout layout)
        {
            for (int index = 0; index < layout.StreetFurniture.Count; index++)
            {
                UrbanStreetFurniturePlacement placement = layout.StreetFurniture[index];
                if (!ShouldInstantiateStreetFurniture(placement.Kind))
                {
                    continue;
                }

                if (placement.Kind == UrbanStreetFurnitureKind.StreetLamp)
                {
                    CreateStreetLamp(placement);
                    continue;
                }

                var root = new GameObject(
                    $"StreetFurniture_{placement.StableId:000}_{placement.Kind}");
                root.transform.SetParent(generatedContent, false);
                root.transform.localPosition = new Vector3(
                    placement.LocalPosition.x,
                    isometricStyle != null ? GetLocalSupportHeight(placement.LocalPosition) : SidewalkSurfaceHeight,
                    placement.LocalPosition.y);
                root.transform.localRotation = Quaternion.Euler(0f, placement.LocalYawDegrees, 0f);
                root.tag = "Obstacle";

                Vector3 colliderSize;
                Vector3 colliderCenter;
                switch (placement.Kind)
                {
                    case UrbanStreetFurnitureKind.StreetTree:
                        colliderSize = new Vector3(0.8f, 4.5f, 0.8f);
                        colliderCenter = new Vector3(0f, 2.25f, 0f);
                        CreatePrimitive(
                            "Trunk",
                            PrimitiveType.Cylinder,
                            new Vector3(0f, 2f, 0f),
                            Quaternion.identity,
                            new Vector3(0.55f, 2f, 0.55f),
                            new Color(0.25f, 0.16f, 0.09f, 1f),
                            false, false, false, true, true, root.transform);
                        CreatePrimitive(
                            "Canopy",
                            PrimitiveType.Sphere,
                            new Vector3(0f, 5.1f, 0f),
                            Quaternion.identity,
                            new Vector3(3.1f, 3.4f, 3.1f),
                            new Color(0.18f, 0.38f, 0.19f, 1f),
                            false, false, false, true, true, root.transform);
                        break;

                    case UrbanStreetFurnitureKind.Bicycle:
                        colliderSize = new Vector3(1.7f, 1.1f, 0.7f);
                        colliderCenter = new Vector3(0f, 0.55f, 0f);
                        CreatePrimitive(
                            "BicycleProxy",
                            PrimitiveType.Cube,
                            new Vector3(0f, 0.55f, 0f),
                            Quaternion.identity,
                            colliderSize,
                            new Color(0.20f, 0.35f, 0.48f, 1f),
                            false, false, false, true, true, root.transform);
                        break;

                    default:
                        colliderSize = new Vector3(1f, 1.35f, 1f);
                        colliderCenter = new Vector3(0f, 0.675f, 0f);
                        CreatePrimitive(
                            "TrashBinProxy",
                            PrimitiveType.Cube,
                            colliderCenter,
                            Quaternion.identity,
                            colliderSize,
                            new Color(0.22f, 0.29f, 0.25f, 1f),
                            false, false, false, true, true, root.transform);
                        break;
                }

                var collider = root.AddComponent<BoxCollider>();
                collider.center = colliderCenter;
                collider.size = colliderSize;
                NavMeshModifier modifier = root.AddComponent<NavMeshModifier>();
                modifier.overrideArea = true;
                modifier.area = 1;
            }
        }

        private void CreateStreetLamp(UrbanStreetFurniturePlacement placement)
        {
            GameObject root = Instantiate(streetLampPrefab, generatedContent, false);
            root.name = $"StreetFurniture_{placement.StableId:000}_{placement.Kind}";
            root.transform.localPosition = new Vector3(
                placement.LocalPosition.x,
                isometricStyle != null ? GetLocalSupportHeight(placement.LocalPosition) : SidewalkSurfaceHeight,
                placement.LocalPosition.y);

            // Layout yaw describes the road tangent. The authored lamp arm points along
            // local -Z, so rotate each sidewalk side inward without changing layout/hash data.
            float inwardYaw = placement.LocalYawDegrees + 90f * placement.Side;
            root.transform.localRotation = Quaternion.Euler(0f, inwardYaw, 0f);
        }

        public bool ShouldInstantiateStreetFurniture(UrbanStreetFurnitureKind kind)
        {
            switch (kind)
            {
                case UrbanStreetFurnitureKind.StreetTree:
                    return instantiateStreetTrees;
                case UrbanStreetFurnitureKind.StreetLamp:
                    return instantiateStreetLamps;
                case UrbanStreetFurnitureKind.Bicycle:
                case UrbanStreetFurnitureKind.TrashBin:
                    return instantiatePrototypeClutter;
                default:
                    return false;
            }
        }

        private int CountEnabledStreetFurniture(UrbanMapLayout layout)
        {
            int count = 0;
            for (int index = 0; index < layout.StreetFurniture.Count; index++)
            {
                if (ShouldInstantiateStreetFurniture(layout.StreetFurniture[index].Kind))
                {
                    count++;
                }
            }

            return count;
        }

        public float GetLocalSupportHeight(Vector2 localPosition)
        {
            if (isometricStyle == null) return 0f;
            UrbanSurfaceGrid grid = CurrentLayout.SurfaceGrid;
            if (!grid.TryLocalToCell(localPosition, out int x, out int z))
                throw new ArgumentOutOfRangeException(nameof(localPosition), "Support position is outside the map grid.");
            float height = GetSurfaceHeight(grid.GetKind(x, z));
            foreach (UrbanBuildingPlacement building in CurrentLayout.Buildings)
            {
                Vector2 d = localPosition - building.Center;
                if (Mathf.Abs(d.x) < building.Size.x * .5f && Mathf.Abs(d.y) < building.Size.y * .5f)
                    return SurfaceHeight + PavementElevation + EnterableSpriteBuilding.FloorLift;
            }
            return height;
        }

        private float GetSurfaceHeight(UrbanSurfaceTileKind kind)
        {
            if (isometricStyle != null)
                return SurfaceHeight + (kind == UrbanSurfaceTileKind.Ground || kind == UrbanSurfaceTileKind.Sidewalk ? PavementElevation : 0f);
            return kind == UrbanSurfaceTileKind.Sidewalk
                ? SidewalkSurfaceHeight
                : SurfaceHeight;
        }

        private void AddSidewalkCurbFaces(
            UrbanSurfaceGrid grid,
            List<Vector3> vertices,
            List<Vector3> normals,
            List<Vector2> uv,
            IReadOnlyList<List<int>> trianglesBySurface)
        {
            float halfTile = grid.TileSize * 0.5f;
            List<int> sidewalkTriangles = trianglesBySurface[(int)UrbanSurfaceTileKind.Sidewalk];
            for (int z = 0; z < grid.Height; z++)
            {
                for (int x = 0; x < grid.Width; x++)
                {
                    if (!IsRaisedPavementCell(grid, x, z))
                    {
                        continue;
                    }

                    Vector2 center = grid.GetCellCenter(x, z);
                    float bottom = SurfaceHeight;
                    float top = GetSurfaceHeight(grid.GetKind(x, z));
                    float uvHeight = isometricStyle != null ? (top - bottom) / grid.TileSize : 1f;
                    float west = center.x - halfTile;
                    float east = center.x + halfTile;
                    float south = center.y - halfTile;
                    float north = center.y + halfTile;

                    if (!IsRaisedPavementCell(grid, x, z + 1))
                    {
                        AddVerticalSurfaceQuad(
                            vertices, normals, uv, sidewalkTriangles,
                            new Vector3(west, bottom, north),
                            new Vector3(east, bottom, north),
                            new Vector3(east, top, north),
                            new Vector3(west, top, north),
                            Vector3.forward, uvHeight);
                    }

                    if (!IsRaisedPavementCell(grid, x + 1, z))
                    {
                        AddVerticalSurfaceQuad(
                            vertices, normals, uv, sidewalkTriangles,
                            new Vector3(east, bottom, north),
                            new Vector3(east, bottom, south),
                            new Vector3(east, top, south),
                            new Vector3(east, top, north),
                            Vector3.right, uvHeight);
                    }

                    if (!IsRaisedPavementCell(grid, x, z - 1))
                    {
                        AddVerticalSurfaceQuad(
                            vertices, normals, uv, sidewalkTriangles,
                            new Vector3(east, bottom, south),
                            new Vector3(west, bottom, south),
                            new Vector3(west, top, south),
                            new Vector3(east, top, south),
                            Vector3.back, uvHeight);
                    }

                    if (!IsRaisedPavementCell(grid, x - 1, z))
                    {
                        AddVerticalSurfaceQuad(
                            vertices, normals, uv, sidewalkTriangles,
                            new Vector3(west, bottom, south),
                            new Vector3(west, bottom, north),
                            new Vector3(west, top, north),
                            new Vector3(west, top, south),
                            Vector3.left, uvHeight);
                    }
                }
            }
        }

        private bool IsRaisedPavementCell(UrbanSurfaceGrid grid, int x, int z)
        {
            return grid.ContainsCell(x, z) &&
                   (grid.GetKind(x, z) == UrbanSurfaceTileKind.Sidewalk ||
                    isometricStyle != null && grid.GetKind(x, z) == UrbanSurfaceTileKind.Ground);
        }

        private static void AddVerticalSurfaceQuad(
            List<Vector3> vertices,
            List<Vector3> normals,
            List<Vector2> uv,
            List<int> triangles,
            Vector3 bottomStart,
            Vector3 bottomEnd,
            Vector3 topEnd,
            Vector3 topStart,
            Vector3 normal, float uvHeight = 1f)
        {
            int vertexStart = vertices.Count;
            vertices.Add(bottomStart);
            vertices.Add(bottomEnd);
            vertices.Add(topEnd);
            vertices.Add(topStart);
            normals.Add(normal);
            normals.Add(normal);
            normals.Add(normal);
            normals.Add(normal);
            uv.Add(Vector2.zero);
            uv.Add(Vector2.right);
            uv.Add(new Vector2(1f, uvHeight));
            uv.Add(new Vector2(0f, uvHeight));
            triangles.Add(vertexStart);
            triangles.Add(vertexStart + 1);
            triangles.Add(vertexStart + 2);
            triangles.Add(vertexStart);
            triangles.Add(vertexStart + 2);
            triangles.Add(vertexStart + 3);
        }

        private void CreateBuilding(
            string objectName,
            UrbanBuildingPlacement building,
            Vector2 facadeDirection,
            Color tintColor,
            int paletteIndex,
            bool reserveFacadeCenter = false)
        {
            var root = new GameObject(objectName);
            root.transform.SetParent(generatedContent, false);
            root.transform.localPosition = new Vector3(building.Center.x,
                isometricStyle != null ? SurfaceHeight + PavementElevation : 0f, building.Center.y);
            if (isometricStyle != null)
            {
                var room = root.AddComponent<EnterableSpriteBuilding>();
                room.Build(isometricStyle, building.Size, facadeDirection, tileWorldSize, tintColor, occlusionFader, reserveFacadeCenter, building.Height);
                return;
            }
            root.tag = "Obstacle";

            var collider = root.AddComponent<BoxCollider>();
            collider.center = new Vector3(0f, building.Height * 0.5f, 0f);
            collider.size = new Vector3(building.Size.x, building.Height, building.Size.y);

            NavMeshModifier modifier = root.AddComponent<NavMeshModifier>();
            modifier.overrideArea = true;
            modifier.area = 1;

            GameObject prefab = buildingVisualPrefabs[PositiveModulo(
                paletteIndex,
                buildingVisualPrefabs.Length)];
            var visualRoot = new GameObject("BuildingVisual");
            visualRoot.transform.SetParent(root.transform, false);
            float facadeYaw = Mathf.Atan2(facadeDirection.x, facadeDirection.y) * Mathf.Rad2Deg;
            visualRoot.transform.localRotation = Quaternion.Euler(
                0f,
                facadeYaw,
                0f);

            GameObject visual = Instantiate(prefab, visualRoot.transform, false);
            visual.name = $"Prefab_{prefab.name}";
            Collider[] visualColliders = visual.GetComponentsInChildren<Collider>(true);
            for (int index = 0; index < visualColliders.Length; index++)
            {
                visualColliders[index].enabled = false;
            }

            Renderer[] renderers = visual.GetComponentsInChildren<Renderer>(false);
            if (renderers.Length == 0)
            {
                throw new InvalidOperationException(
                    $"Building visual prefab '{prefab.name}' has no active Renderer.");
            }

            for (int rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                Renderer renderer = renderers[rendererIndex];
                Material[] sourceMaterials = renderer.sharedMaterials;
                var replacementMaterials = new Material[Mathf.Max(1, sourceMaterials.Length)];
                for (int materialIndex = 0; materialIndex < replacementMaterials.Length; materialIndex++)
                {
                    Material sourceMaterial = materialIndex < sourceMaterials.Length
                        ? sourceMaterials[materialIndex]
                        : null;
                    replacementMaterials[materialIndex] = GetOrCreateBuildingMaterial(sourceMaterial);
                }
                renderer.sharedMaterials = replacementMaterials;
                renderer.shadowCastingMode = ShadowCastingMode.On;
                renderer.receiveShadows = true;
                var propertyBlock = new MaterialPropertyBlock();
                propertyBlock.SetColor(BaseColorId, tintColor);
                propertyBlock.SetColor(ColorId, tintColor);
                renderer.SetPropertyBlock(propertyBlock);
            }

            Bounds sourceBounds = CalculateLocalRendererBounds(root.transform, renderers);
            float horizontalScale = Mathf.Min(
                building.Size.x / Mathf.Max(0.01f, sourceBounds.size.x),
                building.Size.y / Mathf.Max(0.01f, sourceBounds.size.z)) * 0.94f;
            float verticalScale = building.Height / Mathf.Max(0.01f, sourceBounds.size.y);
            visualRoot.transform.localScale = new Vector3(
                horizontalScale,
                verticalScale,
                horizontalScale);

            Bounds fittedBounds = CalculateLocalRendererBounds(root.transform, renderers);
            visualRoot.transform.localPosition = new Vector3(
                -fittedBounds.center.x,
                -fittedBounds.min.y,
                -fittedBounds.center.z);
        }

        private static Bounds CalculateLocalRendererBounds(
            Transform localSpace,
            IReadOnlyList<Renderer> renderers)
        {
            bool initialized = false;
            Bounds result = default;
            for (int rendererIndex = 0; rendererIndex < renderers.Count; rendererIndex++)
            {
                Bounds worldBounds = renderers[rendererIndex].bounds;
                Vector3 minimum = worldBounds.min;
                Vector3 maximum = worldBounds.max;
                for (int corner = 0; corner < 8; corner++)
                {
                    Vector3 worldCorner = new Vector3(
                        (corner & 1) == 0 ? minimum.x : maximum.x,
                        (corner & 2) == 0 ? minimum.y : maximum.y,
                        (corner & 4) == 0 ? minimum.z : maximum.z);
                    Vector3 localCorner = localSpace.InverseTransformPoint(worldCorner);
                    if (!initialized)
                    {
                        result = new Bounds(localCorner, Vector3.zero);
                        initialized = true;
                    }
                    else
                    {
                        result.Encapsulate(localCorner);
                    }
                }
            }

            return result;
        }

        private Material GetOrCreateBuildingMaterial(Material sourceMaterial)
        {
            if (sourceMaterial == null)
            {
                return runtimeMaterial;
            }

            if (runtimeBuildingMaterials.TryGetValue(sourceMaterial, out Material existing))
            {
                return existing;
            }

            var compatible = new Material(runtimeMaterial)
            {
                name = $"Runtime Urban Palette {sourceMaterial.name}",
                hideFlags = HideFlags.DontSave
            };
            Texture palette = sourceMaterial.HasProperty(BaseMapId)
                ? sourceMaterial.GetTexture(BaseMapId)
                : sourceMaterial.HasProperty(MainTexId)
                    ? sourceMaterial.GetTexture(MainTexId)
                    : null;
            if (palette != null)
            {
                Vector2 textureScale = sourceMaterial.HasProperty(BaseMapId)
                    ? sourceMaterial.GetTextureScale(BaseMapId)
                    : sourceMaterial.GetTextureScale(MainTexId);
                Vector2 textureOffset = sourceMaterial.HasProperty(BaseMapId)
                    ? sourceMaterial.GetTextureOffset(BaseMapId)
                    : sourceMaterial.GetTextureOffset(MainTexId);
                if (compatible.HasProperty(BaseMapId))
                {
                    compatible.SetTexture(BaseMapId, palette);
                    compatible.SetTextureScale(BaseMapId, textureScale);
                    compatible.SetTextureOffset(BaseMapId, textureOffset);
                }
                if (compatible.HasProperty(MainTexId))
                {
                    compatible.SetTexture(MainTexId, palette);
                    compatible.SetTextureScale(MainTexId, textureScale);
                    compatible.SetTextureOffset(MainTexId, textureOffset);
                }
            }

            if (compatible.HasProperty(BaseColorId))
            {
                compatible.SetColor(BaseColorId, Color.white);
            }
            if (compatible.HasProperty(ColorId))
            {
                compatible.SetColor(ColorId, Color.white);
            }
            if (sourceMaterial.HasProperty(GlossinessId) &&
                compatible.HasProperty(SmoothnessId))
            {
                compatible.SetFloat(
                    SmoothnessId,
                    sourceMaterial.GetFloat(GlossinessId));
            }
            runtimeBuildingMaterials.Add(sourceMaterial, compatible);
            return compatible;
        }

        private void ClearRuntimeBuildingMaterials()
        {
            foreach (KeyValuePair<Material, Material> entry in runtimeBuildingMaterials)
            {
                if (entry.Value != null)
                {
                    Destroy(entry.Value);
                }
            }

            runtimeBuildingMaterials.Clear();
        }

        private static int PositiveModulo(int value, int modulus)
        {
            int result = value % modulus;
            return result < 0 ? result + modulus : result;
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
            var boundary = new GameObject(objectName);
            boundary.transform.SetParent(generatedContent, false);
            boundary.transform.localPosition = localPosition;
            boundary.tag = "Obstacle";
            var collider = boundary.AddComponent<BoxCollider>();
            collider.size = localScale;
            NavMeshModifier modifier = boundary.AddComponent<NavMeshModifier>();
            modifier.overrideArea = true;
            modifier.area = 1;
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
            bool castsShadows,
            bool receivesShadows,
            Transform parent = null)
        {
            GameObject instance = GameObject.CreatePrimitive(primitiveType);
            instance.name = objectName;
            instance.transform.SetParent(parent != null ? parent : generatedContent, false);
            instance.transform.localPosition = localPosition;
            instance.transform.localRotation = localRotation;
            instance.transform.localScale = localScale;

            Renderer renderer = instance.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.sharedMaterial = runtimeMaterial;
                renderer.shadowCastingMode = castsShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
                renderer.receiveShadows = receivesShadows;
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
