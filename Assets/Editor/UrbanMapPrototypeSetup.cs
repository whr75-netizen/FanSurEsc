using System;
using System.Collections.Generic;
using FantasySurvival.Interaction;
using FantasySurvival.SceneFlow;
using FantasySurvival.WorldGeneration;
using Unity.AI.Navigation;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.SceneManagement;

namespace FantasySurvival.EditorTools
{
    public static class UrbanMapPrototypeSetup
    {
        private const string GameMapTestPath = "Assets/Scenes/GameMapTest.unity";
        private const string GeneratorObjectName = "ProceduralUrbanMap";

        [MenuItem("Tools/Fantasy Survival/Urban Map/Configure GameMapTest")]
        public static void ConfigureGameMapTest()
        {
            EnsureOpenScenesAreClean();
            SceneSetup[] previousSetup = EditorSceneManager.GetSceneManagerSetup();

            try
            {
                Scene scene = EditorSceneManager.OpenScene(GameMapTestPath, OpenSceneMode.Single);
                SceneSpawnPoint raidEntry = FindComponentInScene<SceneSpawnPoint>(scene, point => point.SpawnId == "RaidEntry");
                ReturnPortalInteractable portal = FindComponentInScene<ReturnPortalInteractable>(scene, _ => true);
                EnemyAIController[] enemies = FindComponentsInScene<EnemyAIController>(scene);
                GameObject legacyGround = FindRootByName(scene, "Plane");

                if (raidEntry == null || portal == null || legacyGround == null)
                {
                    throw new BuildFailedException(
                        "GameMapTest is missing RaidEntry, ReturnPortal, or the legacy Plane required by the urban map prototype setup.");
                }

                GameObject generatorObject = FindRootByName(scene, GeneratorObjectName);
                if (generatorObject == null)
                {
                    generatorObject = new GameObject(GeneratorObjectName);
                    Undo.RegisterCreatedObjectUndo(generatorObject, "Create Procedural Urban Map");
                    SceneManager.MoveGameObjectToScene(generatorObject, scene);
                }

                ProceduralUrbanMapGenerator generator = generatorObject.GetComponent<ProceduralUrbanMapGenerator>();
                if (generator == null)
                {
                    generator = Undo.AddComponent<ProceduralUrbanMapGenerator>(generatorObject);
                }

                NavMeshSurface surface = generatorObject.GetComponent<NavMeshSurface>();
                if (surface == null)
                {
                    surface = Undo.AddComponent<NavMeshSurface>(generatorObject);
                }

                Undo.RecordObject(surface, "Configure Procedural Urban NavMesh");
                surface.collectObjects = CollectObjects.Children;
                surface.useGeometry = NavMeshCollectGeometry.PhysicsColliders;
                surface.layerMask = ~0;
                surface.ignoreNavMeshAgent = true;
                surface.ignoreNavMeshObstacle = true;
                surface.minRegionArea = 1f;
                surface.buildHeightMesh = false;

                Undo.RecordObject(generator, "Configure Procedural Urban Map");
                var serializedGenerator = new SerializedObject(generator);
                serializedGenerator.FindProperty("entryAnchor").objectReferenceValue = raidEntry.transform;
                serializedGenerator.FindProperty("returnPortal").objectReferenceValue = portal.transform;
                serializedGenerator.FindProperty("legacyGround").objectReferenceValue = legacyGround;
                serializedGenerator.FindProperty("navMeshSurface").objectReferenceValue = surface;
                serializedGenerator.FindProperty("randomizeSeedOnAwake").boolValue = true;

                SerializedProperty protectedAnchors = serializedGenerator.FindProperty("additionalProtectedAnchors");
                protectedAnchors.arraySize = enemies.Length;
                for (int enemyIndex = 0; enemyIndex < enemies.Length; enemyIndex++)
                {
                    protectedAnchors.GetArrayElementAtIndex(enemyIndex).objectReferenceValue =
                        enemies[enemyIndex].transform;
                }

                serializedGenerator.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(generatorObject);
                EditorSceneManager.MarkSceneDirty(scene);

                ValidateConfiguredScene(scene);
                ValidateLayoutSeeds(
                    generator.PlanLayout,
                    generator.GenerationParameters,
                    "GameMapTest serialized settings");

                if (!EditorSceneManager.SaveScene(scene))
                {
                    throw new BuildFailedException("Unity could not save the validated GameMapTest urban map setup.");
                }

                Debug.Log(
                    $"Configured GameMapTest with one scene-local ProceduralUrbanMapGenerator, " +
                    $"NavMeshSurface, and {enemies.Length} protected enemy anchors.");
            }
            finally
            {
                if (previousSetup.Length > 0)
                {
                    EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
                }
            }
        }

        [MenuItem("Tools/Fantasy Survival/Urban Map/Validate Layout Seeds")]
        public static void ValidateLayoutSeeds()
        {
            UrbanMapGenerationParameters parameters = UrbanMapGenerationParameters.CreateDefault();
            var emptyProtectedPoints = new List<Vector2>();
            ValidateLayoutSeeds(
                seed => UrbanMapLayoutPlanner.Generate(seed, Vector2.zero, emptyProtectedPoints, parameters),
                parameters,
                "default settings");
        }

        private static void ValidateLayoutSeeds(
            Func<int, UrbanMapLayout> layoutFactory,
            UrbanMapGenerationParameters parameters,
            string validationLabel)
        {
            const int seedCount = 256;
            float minimumWidth = float.PositiveInfinity;
            float maximumWidth = float.NegativeInfinity;
            float minimumDepth = float.PositiveInfinity;
            float maximumDepth = float.NegativeInfinity;
            int minimumBuildings = int.MaxValue;
            int maximumBuildings = int.MinValue;
            var hashes = new HashSet<ulong>();

            for (int seed = 0; seed < seedCount; seed++)
            {
                UrbanMapLayout layout = layoutFactory(seed);
                if (!UrbanMapLayoutValidator.TryValidate(layout, parameters, out string error))
                {
                    throw new BuildFailedException($"Urban layout seed {seed} failed validation: {error}");
                }

                ulong firstHash = UrbanMapLayoutValidator.ComputeStableHash(layout);
                UrbanMapLayout repeated = layoutFactory(seed);
                ulong repeatedHash = UrbanMapLayoutValidator.ComputeStableHash(repeated);
                if (firstHash != repeatedHash)
                {
                    throw new BuildFailedException($"Urban layout seed {seed} is not deterministic.");
                }

                if (layout.Buildings.Count == 0)
                {
                    throw new BuildFailedException($"Urban layout seed {seed} generated no graybox buildings.");
                }

                hashes.Add(firstHash);
                minimumWidth = Mathf.Min(minimumWidth, layout.LocalBounds.width);
                maximumWidth = Mathf.Max(maximumWidth, layout.LocalBounds.width);
                minimumDepth = Mathf.Min(minimumDepth, layout.LocalBounds.height);
                maximumDepth = Mathf.Max(maximumDepth, layout.LocalBounds.height);
                minimumBuildings = Mathf.Min(minimumBuildings, layout.Buildings.Count);
                maximumBuildings = Mathf.Max(maximumBuildings, layout.Buildings.Count);
            }

            if (hashes.Count < seedCount * 0.95f)
            {
                throw new BuildFailedException(
                    $"Only {hashes.Count} unique urban layouts were generated from {seedCount} tested seeds.");
            }

            if (Mathf.Approximately(minimumWidth, maximumWidth) || Mathf.Approximately(minimumDepth, maximumDepth))
            {
                throw new BuildFailedException("Urban map dimensions did not vary across tested seeds.");
            }

            Debug.Log(
                $"Urban layout validation ({validationLabel}) passed for {seedCount} seeds. Unique={hashes.Count}, " +
                $"Width={minimumWidth:F1}-{maximumWidth:F1}, Depth={minimumDepth:F1}-{maximumDepth:F1}, " +
                $"Buildings={minimumBuildings}-{maximumBuildings}.");
        }

        public static void ConfigureAndValidateBatch()
        {
            ConfigureGameMapTest();
            ValidateLayoutSeeds();
        }

        private static void ValidateConfiguredScene(Scene scene)
        {
            ProceduralUrbanMapGenerator[] generators = FindComponentsInScene<ProceduralUrbanMapGenerator>(scene);
            if (generators.Length != 1)
            {
                throw new BuildFailedException(
                    $"GameMapTest must contain exactly one ProceduralUrbanMapGenerator, but found {generators.Length}.");
            }

            if (generators[0].GetComponent<NavMeshSurface>() == null)
            {
                throw new BuildFailedException("GameMapTest ProceduralUrbanMapGenerator has no NavMeshSurface.");
            }

            int missingScriptCount = 0;
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                Transform[] transforms = roots[index].GetComponentsInChildren<Transform>(true);
                for (int transformIndex = 0; transformIndex < transforms.Length; transformIndex++)
                {
                    missingScriptCount += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(
                        transforms[transformIndex].gameObject);
                }
            }

            if (missingScriptCount != 0)
            {
                throw new BuildFailedException($"GameMapTest contains {missingScriptCount} missing scripts after setup.");
            }
        }

        private static void EnsureOpenScenesAreClean()
        {
            for (int sceneIndex = 0; sceneIndex < SceneManager.sceneCount; sceneIndex++)
            {
                Scene openScene = SceneManager.GetSceneAt(sceneIndex);
                if (openScene.isDirty)
                {
                    throw new BuildFailedException(
                        $"Urban map setup stopped because open scene '{openScene.name}' has unsaved changes. Save or revert it first.");
                }
            }
        }

        private static T FindComponentInScene<T>(Scene scene, Predicate<T> predicate) where T : Component
        {
            T[] components = FindComponentsInScene<T>(scene);
            for (int index = 0; index < components.Length; index++)
            {
                if (predicate(components[index]))
                {
                    return components[index];
                }
            }

            return null;
        }

        private static T[] FindComponentsInScene<T>(Scene scene) where T : Component
        {
            var components = new List<T>();
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                components.AddRange(roots[index].GetComponentsInChildren<T>(true));
            }

            return components.ToArray();
        }

        private static GameObject FindRootByName(Scene scene, string objectName)
        {
            GameObject[] roots = scene.GetRootGameObjects();
            for (int index = 0; index < roots.Length; index++)
            {
                if (roots[index].name == objectName)
                {
                    return roots[index];
                }
            }

            return null;
        }
    }
}
