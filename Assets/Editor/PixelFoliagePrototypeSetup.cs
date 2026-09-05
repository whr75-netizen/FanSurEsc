using System;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.EditorTools
{
    public static class PixelFoliagePrototypeSetup
    {
        public const string DataFolder = "Assets/GameData/Foliage";
        public const string PrefabPath = "Assets/Prefabs/Foliage/PrototypePixelFoliage.prefab";
        private const string AtlasPath = DataFolder + "/FoliageWindAtlas.png";

        [MenuItem("Tools/Fantasy Survival/Environment/Create Pixel Foliage Prototype")]
        private static void CreateFromMenu()
        {
            Selection.activeGameObject = CreatePrototype(Vector3.zero);
        }

        public static GameObject CreatePrototype(Vector3 position)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("Create foliage in stable Edit Mode.");
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (prefab == null)
            {
                EnsureFolder(DataFolder);
                EnsureFolder("Assets/Prefabs/Foliage");
                ConfigureAtlas();
                Shader shader = Shader.Find("FantasySurvival/PixelFoliage");
                if (shader == null || !shader.isSupported)
                    throw new InvalidOperationException("PixelFoliage shader is unavailable.");
                var atlas = AssetDatabase.LoadAssetAtPath<Texture2D>(AtlasPath);
                Material grassMaterial = CreateMaterial("PixelGrass", shader, atlas,
                    new Color(0.37f, 0.51f, 0.23f), true);
                Material leafMaterial = CreateMaterial("PixelLeaves", shader, atlas,
                    new Color(0.34f, 0.49f, 0.20f), true);
                Material groundMaterial = CreateMaterial("PixelGrassGround", shader, atlas,
                    new Color(0.37f, 0.51f, 0.23f), false);
                Shader lit = Shader.Find("Universal Render Pipeline/Lit");
                var trunkMaterial = new Material(lit) { name = "PixelFoliageTrunk" };
                trunkMaterial.SetColor("_BaseColor", new Color(0.30f, 0.21f, 0.13f));
                trunkMaterial.SetFloat("_Smoothness", 0f);
                AssetDatabase.CreateAsset(trunkMaterial, DataFolder + "/PixelFoliageTrunk.mat");

                var root = new GameObject("PrototypePixelFoliage");
                try
                {
                    var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
                    ground.name = "Ground_ColorReference";
                    ground.transform.SetParent(root.transform, false);
                    ground.transform.localPosition = new Vector3(0f, 0.012f, 0f);
                    ground.transform.localScale = new Vector3(0.6f, 1f, 0.4f);
                    UnityEngine.Object.DestroyImmediate(ground.GetComponent<Collider>());
                    ground.GetComponent<MeshRenderer>().sharedMaterial = groundMaterial;
                    ground.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;

                    PixelFoliagePatch grass = CreatePatch(root.transform, "Grass", false,
                        360, new Vector2(0.4f, 0.65f), grassMaterial);
                    grass.transform.localPosition = new Vector3(0f, 0.02f, 0f);
                    Rebuild(grass);

                    var tree = new GameObject("Tree");
                    tree.transform.SetParent(root.transform, false);
                    tree.transform.localPosition = new Vector3(-0.7f, 0f, 0.5f);
                    PixelFoliagePatch leaves = CreatePatch(tree.transform, "Leaves", true,
                        420, new Vector2(0.55f, 0.85f), leafMaterial);
                    Rebuild(leaves);

                    var trunk = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                    trunk.name = "Trunk";
                    trunk.transform.SetParent(tree.transform, false);
                    trunk.transform.localPosition = new Vector3(0f, 1.25f, 0f);
                    trunk.transform.localScale = new Vector3(0.42f, 1.25f, 0.42f);
                    trunk.GetComponent<MeshRenderer>().sharedMaterial = trunkMaterial;
                    // The primitive has a static collider, not a dynamic rigidbody.
                    // Foliage cards are visual only; only the trunk blocks movement.
                    prefab = PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
                }
                finally { UnityEngine.Object.DestroyImmediate(root); }
            }
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            Undo.RegisterCreatedObjectUndo(instance, "Create pixel foliage prototype");
            instance.transform.position = position;
            return instance;
        }

        public static void Rebuild(PixelFoliagePatch patch)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Foliage meshes are authored in Edit Mode.");
            Mesh generated = patch.Kind == PixelFoliagePatch.PatchKind.Grass
                ? PixelFoliageMeshBuilder.BuildGrass(patch.Seed, patch.Count, patch.Area, patch.SizeRange)
                : PixelFoliageMeshBuilder.BuildLeaves(patch.Seed, patch.Count,
                    patch.CrownCenters, patch.CrownRadii, patch.SizeRange);
            AssignOwnedMesh(patch.GetComponent<MeshFilter>(), generated, patch.name);
            if (patch.Kind == PixelFoliagePatch.PatchKind.Leaves)
            {
                Transform proxy = patch.transform.Find("Crown_ShadowOnly");
                if (proxy == null)
                {
                    var go = new GameObject("Crown_ShadowOnly", typeof(MeshFilter), typeof(MeshRenderer));
                    Undo.RegisterCreatedObjectUndo(go, "Create crown shadow proxy");
                    go.transform.SetParent(patch.transform, false);
                    proxy = go.transform;
                }
                AssignOwnedMesh(proxy.GetComponent<MeshFilter>(),
                    PixelFoliageMeshBuilder.BuildCrownProxy(patch.CrownCenters, patch.CrownRadii), "CrownProxy");
                MeshRenderer renderer = proxy.GetComponent<MeshRenderer>();
                Undo.RecordObject(renderer, "Configure crown shadow proxy");
                renderer.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>(DataFolder + "/PixelFoliageTrunk.mat");
                renderer.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
                renderer.receiveShadows = false;
            }
            EditorUtility.SetDirty(patch);
        }

        private static void AssignOwnedMesh(MeshFilter filter, Mesh generated, string name)
        {
            EnsureFolder(DataFolder);
            string oldPath = AssetDatabase.GetAssetPath(filter.sharedMesh);
            if (filter.sharedMesh != null && !oldPath.StartsWith(DataFolder + "/", StringComparison.Ordinal))
            {
                UnityEngine.Object.DestroyImmediate(generated);
                throw new InvalidOperationException("Refusing to overwrite a mesh outside the foliage authoring folder.");
            }
            Undo.RecordObject(filter, "Assign foliage mesh");
            if (filter.sharedMesh == null)
            {
                string path = AssetDatabase.GenerateUniqueAssetPath(DataFolder + "/" + name + ".asset");
                AssetDatabase.CreateAsset(generated, path);
                filter.sharedMesh = generated;
            }
            else
            {
                Mesh existing = filter.sharedMesh;
                Undo.RegisterCompleteObjectUndo(existing, "Rebuild foliage mesh");
                EditorUtility.CopySerialized(generated, existing);
                UnityEngine.Object.DestroyImmediate(generated);
                EditorUtility.SetDirty(existing);
                AssetDatabase.SaveAssetIfDirty(existing);
            }
            EditorUtility.SetDirty(filter);
        }

        private static PixelFoliagePatch CreatePatch(Transform parent, string name,
            bool leaves, int count, Vector2 sizes, Material material)
        {
            var go = new GameObject(name, typeof(PixelFoliagePatch));
            go.transform.SetParent(parent, false);
            PixelFoliagePatch patch = go.GetComponent<PixelFoliagePatch>();
            var serialized = new SerializedObject(patch);
            serialized.FindProperty("kind").enumValueIndex = leaves ? 1 : 0;
            serialized.FindProperty("count").intValue = count;
            serialized.FindProperty("sizeRange").vector2Value = sizes;
            if (leaves)
            {
                Vector3[] centers = { new Vector3(0f, 3.1f, 0f), new Vector3(-1.1f, 2.7f, 0.2f), new Vector3(1.05f, 2.9f, 0.1f) };
                Vector3[] radii = { new Vector3(1.25f, 1.15f, 1.05f), new Vector3(0.95f, 0.85f, 0.9f), new Vector3(0.95f, 0.95f, 0.85f) };
                var c = serialized.FindProperty("crownCenters");
                var r = serialized.FindProperty("crownRadii");
                c.arraySize = r.arraySize = centers.Length;
                for (int i = 0; i < centers.Length; i++)
                { c.GetArrayElementAtIndex(i).vector3Value = centers[i]; r.GetArrayElementAtIndex(i).vector3Value = radii[i]; }
            }
            serialized.ApplyModifiedPropertiesWithoutUndo();
            MeshRenderer renderer = go.GetComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = true;
            return patch;
        }

        private static Material CreateMaterial(string name, Shader shader, Texture2D atlas, Color color, bool sprite)
        {
            var material = new Material(shader) { name = name };
            material.SetTexture("_BaseMap", atlas);
            material.SetColor("_BaseColor", color);
            material.SetFloat("_SpriteMode", sprite ? 1f : 0f);
            material.SetFloat("_AnimationFps", 0.4f);
            material.SetFloat("_ColorVariation", 0f);
            material.SetFloat("_ShadeSteps", 2f);
            AssetDatabase.CreateAsset(material, DataFolder + "/" + name + ".mat");
            return material;
        }

        private static void ConfigureAtlas()
        {
            var importer = AssetImporter.GetAtPath(AtlasPath) as TextureImporter;
            if (importer == null) throw new InvalidOperationException("FoliageWindAtlas.png must be imported first.");
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = true;
            importer.alphaSource = TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.npotScale = TextureImporterNPOTScale.ToNearest;
            importer.maxTextureSize = 128; // Four 32px frames across; material-local, not camera downsampling.
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            int slash = path.LastIndexOf('/');
            string parent = path.Substring(0, slash);
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, path.Substring(slash + 1));
        }
    }

    [CustomEditor(typeof(PixelFoliagePatch))]
    internal sealed class PixelFoliagePatchEditor : UnityEditor.Editor
    {
        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();
            EditorGUILayout.HelpBox("Settings are baked explicitly. Rebuilding changes this shared mesh asset, including other instances that use it. Colours, frame rate and lighting are on the material.", MessageType.Info);
            using (new EditorGUI.DisabledScope(EditorApplication.isPlayingOrWillChangePlaymode))
            {
                if (GUILayout.Button("Rebuild Foliage Mesh"))
                    PixelFoliagePrototypeSetup.Rebuild((PixelFoliagePatch)target);
            }
        }
    }
}
