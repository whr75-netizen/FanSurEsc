using System;
using System.Collections.Generic;
using FantasySurvival.AI;
using Unity.AI.Navigation;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    [DefaultExecutionOrder(-10000)]
    [DisallowMultipleComponent]
    [RequireComponent(typeof(NavMeshSurface))]
    public sealed class ProceduralUrbanMapGenerator : MonoBehaviour, IEnemyPatrolPointSource
    {
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");

        private static readonly Color GroundColor = new Color(0.19f, 0.18f, 0.16f, 1f);
        private static readonly Color SecondaryRoadColor = new Color(0.18f, 0.20f, 0.22f, 1f);
        private static readonly Color PrimaryRoadColor = new Color(0.25f, 0.27f, 0.29f, 1f);
        private static readonly Color SidewalkColor = new Color(0.36f, 0.35f, 0.33f, 1f);
        private static readonly Color BoundaryColor = new Color(0.24f, 0.12f, 0.11f, 1f);
        private static readonly Color MedicalPoiBuildingColor = new Color(0.18f, 0.62f, 0.46f, 1f);
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

        [Header("Fixed Tile Map")]
        [SerializeField, Min(17)] private int mapTilesPerAxis = 145;
        [SerializeField, Min(2)] private int blocksPerAxis = 6;
        [SerializeField, Min(1)] private int borderTiles = 12;
        [SerializeField, Min(0.25f)] private float tileWorldSize = 2f;

        [Header("Octilinear Road Graph")]
        [SerializeField, Min(1)] private int secondaryRoadWidthTiles = 3;
        [SerializeField, Min(1)] private int primaryRoadWidthTiles = 5;
        [SerializeField, Range(0f, 1f)] private float additionalRoadChance = 0.35f;
        [SerializeField, Range(0f, 1f)] private float diagonalRoadChance = 0.2f;
        [SerializeField, Min(1)] private int sidewalkWidthTiles = 1;

        [Header("Prototype Buildings")]
        [SerializeField] private GameObject[] buildingVisualPrefabs;
        [SerializeField, Min(0f)] private float buildingSetback = 2f;
        [SerializeField, Min(0f)] private float lotGap = 2f;
        [SerializeField, Range(0f, 1f)] private float buildingDensity = 0.8f;
        [SerializeField, Min(1f)] private float minBuildingHeight = 10.5f;
        [SerializeField, Min(1f)] private float maxBuildingHeight = 18f;
        [SerializeField, Min(0f)] private float anchorClearance = 10f;
        [SerializeField, Min(0f)] private float protectedAnchorClearance = 8f;

        [Header("Street Furniture Sockets")]
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
        private Material[] runtimeSurfaceMaterials;
        private Mesh runtimeSurfaceMesh;
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

            CreateSurfaceTiles(layout);
            CreateBuildings(layout);
            CreateStreetFurniture(layout);
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
                $"Roads={layout.Roads.Count}, Buildings={layout.Buildings.Count}, " +
                $"Tiles={layout.SurfaceGrid.Width}x{layout.SurfaceGrid.Height}, " +
                $"Furniture={layout.StreetFurniture.Count}, Candidates={layout.Candidates.Count}, " +
                $"POIs={layout.Pois.Count}, " +
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

            if (buildingVisualPrefabs == null || buildingVisualPrefabs.Length == 0)
            {
                Debug.LogError(
                    "ProceduralUrbanMapGenerator requires at least one building visual prefab.",
                    this);
                return false;
            }

            for (int index = 0; index < buildingVisualPrefabs.Length; index++)
            {
                if (buildingVisualPrefabs[index] == null)
                {
                    Debug.LogError(
                        $"ProceduralUrbanMapGenerator building visual prefab slot {index} is empty.",
                        this);
                    return false;
                }
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
                buildingDensity,
                minBuildingHeight,
                maxBuildingHeight,
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
                    Vector2 center = grid.GetCellCenter(x, z);
                    int vertexStart = vertices.Count;
                    vertices.Add(new Vector3(center.x - halfTile, 0.005f, center.y - halfTile));
                    vertices.Add(new Vector3(center.x - halfTile, 0.005f, center.y + halfTile));
                    vertices.Add(new Vector3(center.x + halfTile, 0.005f, center.y + halfTile));
                    vertices.Add(new Vector3(center.x + halfTile, 0.005f, center.y - halfTile));
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    normals.Add(Vector3.up);
                    uv.Add(Vector2.zero);
                    uv.Add(Vector2.up);
                    uv.Add(Vector2.one);
                    uv.Add(Vector2.right);

                    List<int> triangles = trianglesBySurface[(int)grid.GetKind(x, z)];
                    triangles.Add(vertexStart);
                    triangles.Add(vertexStart + 1);
                    triangles.Add(vertexStart + 2);
                    triangles.Add(vertexStart);
                    triangles.Add(vertexStart + 2);
                    triangles.Add(vertexStart + 3);
                }
            }

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
            var renderer = surfaceObject.AddComponent<MeshRenderer>();
            renderer.sharedMaterials = runtimeSurfaceMaterials;
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = true;
        }

        private void EnsureRuntimeSurfaceMaterials()
        {
            if (runtimeSurfaceMaterials != null)
            {
                return;
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
                Color color = isMedicalPoi
                    ? MedicalPoiBuildingColor
                    : BuildingColors[Mathf.Abs(building.PaletteIndex) % BuildingColors.Length];
                CreateBuilding(
                    isMedicalPoi
                        ? $"Building_{index:000}_MedicalPoi"
                        : $"Building_{index:000}_Palette_{building.PaletteIndex}",
                    building,
                    FindBuildingFacadeDirection(layout, index),
                    color,
                    building.PaletteIndex);
            }
        }

        private void CreateStreetFurniture(UrbanMapLayout layout)
        {
            for (int index = 0; index < layout.StreetFurniture.Count; index++)
            {
                UrbanStreetFurniturePlacement placement = layout.StreetFurniture[index];
                var root = new GameObject(
                    $"StreetFurniture_{placement.StableId:000}_{placement.Kind}");
                root.transform.SetParent(generatedContent, false);
                root.transform.localPosition = new Vector3(
                    placement.LocalPosition.x,
                    0f,
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

                    case UrbanStreetFurnitureKind.StreetLamp:
                        colliderSize = new Vector3(0.65f, 8.5f, 0.65f);
                        colliderCenter = new Vector3(0f, 4.25f, 0f);
                        CreatePrimitive(
                            "Pole",
                            PrimitiveType.Cylinder,
                            new Vector3(0f, 4.25f, 0f),
                            Quaternion.identity,
                            new Vector3(0.32f, 4.25f, 0.32f),
                            new Color(0.16f, 0.17f, 0.18f, 1f),
                            false, false, false, true, true, root.transform);
                        CreatePrimitive(
                            "LampHead",
                            PrimitiveType.Cube,
                            new Vector3(0f, 8.35f, 0.45f),
                            Quaternion.identity,
                            new Vector3(0.9f, 0.45f, 1.4f),
                            new Color(0.76f, 0.68f, 0.38f, 1f),
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

        private void CreateBuilding(
            string objectName,
            UrbanBuildingPlacement building,
            Vector2 facadeDirection,
            Color bodyColor,
            int paletteIndex)
        {
            var root = new GameObject(objectName);
            root.transform.SetParent(generatedContent, false);
            root.transform.localPosition = new Vector3(building.Center.x, 0f, building.Center.y);
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
                    replacementMaterials[materialIndex] = runtimeMaterial;
                }
                renderer.sharedMaterials = replacementMaterials;
                renderer.shadowCastingMode = ShadowCastingMode.On;
                renderer.receiveShadows = true;
                var propertyBlock = new MaterialPropertyBlock();
                propertyBlock.SetColor(BaseColorId, bodyColor);
                propertyBlock.SetColor(ColorId, bodyColor);
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

        private static Vector2 FindBuildingFacadeDirection(UrbanMapLayout layout, int buildingIndex)
        {
            for (int index = 0; index < layout.Candidates.Count; index++)
            {
                UrbanSpatialCandidate candidate = layout.Candidates[index];
                if (candidate.Kind == UrbanSpatialCandidateKind.BuildingApproach &&
                    candidate.SourceBuildingIndex == buildingIndex)
                {
                    return candidate.LocalDirection;
                }
            }

            return Vector2.down;
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
                castsShadows: false,
                receivesShadows: true);
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
