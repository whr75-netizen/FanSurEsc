using System;
using FantasySurvival.WorldLighting;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.EditorTools
{
    /// <summary>Explicit authoring upgrade of the existing lighting yard; never runs in gameplay.</summary>
    public static class FoliageLightingTestSetup
    {
        public const string YardPath = "Assets/Prefabs/Lighting/PrototypeSunShaftContrastTestArea.prefab";
        private const string Folder = "Assets/GameData/Foliage/LightingTest";

        [MenuItem("Tools/Fantasy Survival/Environment/Populate Existing Lighting Yard")]
        public static void Populate()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("Stable Edit Mode required.");
            if (!AssetDatabase.IsValidFolder(Folder))
                AssetDatabase.CreateFolder(PixelFoliagePrototypeSetup.DataFolder, "LightingTest");
            var grass = Required<Material>(PixelFoliagePrototypeSetup.DataFolder + "/PixelGrass.mat");
            var leaves = Required<Material>(PixelFoliagePrototypeSetup.DataFolder + "/PixelLeaves.mat");
            var surface = Required<Material>(PixelFoliagePrototypeSetup.DataFolder + "/PixelGrassGround.mat");
            var trunk = Required<Material>(PixelFoliagePrototypeSetup.DataFolder + "/PixelFoliageTrunk.mat");

            var centers = new[] { new Vector3(0, 10.5f, 0), new Vector3(-2.1f, 9.1f, 0.8f), new Vector3(2.2f, 9.6f, -0.5f) };
            var radii = new[] { new Vector3(2.6f, 2.15f, 2.4f), new Vector3(2.15f, 1.65f, 1.9f), new Vector3(2.15f, 1.8f, 2.15f) };
            Mesh crown = ExistingOrCreate("MatureLeaves", () => PixelFoliageMeshBuilder.BuildLeaves(
                8711, 900, centers, radii, new Vector2(0.65f, 1.0f)));
            Mesh shadow = ExistingOrCreate("MatureCrownShadow", () => PixelFoliageMeshBuilder.BuildCrownProxy(centers, radii));
            Mesh groveGrass = ExistingOrCreate("GroveGrass", () => PixelFoliageMeshBuilder.BuildGrass(
                1709, 3600, new Vector2(23f, 28f), new Vector2(0.25f, 0.5f)));
            Mesh controlGrass = ExistingOrCreate("ControlGrass", () => PixelFoliageMeshBuilder.BuildGrass(
                2017, 1700, new Vector2(17f, 18f), new Vector2(0.25f, 0.5f)));

            GameObject root = PrefabUtility.LoadPrefabContents(YardPath);
            try
            {
                // The base scene's Ground is at y=0. Keep the yard slab above
                // that plane and below the raised receivers, not coplanar.
                Transform slab = RequiredChild(root.transform, "ValidationYard_100x64");
                Vector3 slabPosition = slab.localPosition;
                slabPosition.y = 0f;
                slab.localPosition = slabPosition;
                Transform grove = RequiredChild(root.transform, "05_TreeGrove_IrregularOcclusion");
                AddGrass(grove, groveGrass, grass, surface);
                for (int i = 1; i <= 9; i++)
                {
                    Transform tree = RequiredChild(grove, "Tree_" + i.ToString("D2"));
                    Transform oldCrown = RequiredChild(tree, "Canopy");
                    oldCrown.gameObject.SetActive(false); // Retain the graybox for reversible comparison.
                    Transform stem = RequiredChild(tree, "Trunk");
                    stem.localPosition = new Vector3(0, 4.4f, 0);
                    stem.localScale = new Vector3(0.95f, 8.8f, 0.95f);
                    stem.GetComponent<MeshRenderer>().sharedMaterial = trunk;
                    AddMesh(tree, "MatureLeaves", crown, leaves, ShadowCastingMode.Off);
                    AddMesh(tree, "MatureShadowProxy", shadow, trunk, ShadowCastingMode.ShadowsOnly);
                }
                foreach (string zone in new[] { "01_OpenControl_NoPattern", "02_FullRoof_UniformShadow", "03_Skylight_5x6_Aperture" })
                    AddGrass(RequiredChild(root.transform, zone), controlGrass, grass, surface);
                PrefabUtility.SaveAsPrefabAsset(root, YardPath);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }

        private static void AddGrass(Transform zone, Mesh mesh, Material grass, Material surface)
        {
            Transform receiver = null;
            foreach (Transform child in zone)
                if (child.name.StartsWith("Receiver_", StringComparison.Ordinal)) receiver = child;
            if (receiver == null) throw new InvalidOperationException("Receiver missing in " + zone.name);
            receiver.GetComponent<MeshRenderer>().sharedMaterial = surface;
            var renderer = AddMesh(zone, "PixelGrass", mesh, grass, ShadowCastingMode.Off);
            renderer.transform.localPosition = new Vector3(0, receiver.localPosition.y + receiver.localScale.y * 0.5f + 0.005f, 0);
        }

        private static MeshRenderer AddMesh(Transform parent, string name, Mesh mesh, Material material, ShadowCastingMode shadows)
        {
            Transform child = parent.Find(name);
            if (child == null)
            {
                var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer));
                go.transform.SetParent(parent, false);
                child = go.transform;
            }
            child.GetComponent<MeshFilter>().sharedMesh = mesh;
            var renderer = child.GetComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = shadows;
            renderer.receiveShadows = shadows != ShadowCastingMode.ShadowsOnly;
            return renderer;
        }

        private static Mesh ExistingOrCreate(string name, Func<Mesh> build)
        {
            string path = Folder + "/" + name + ".asset";
            Mesh mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (mesh != null) return mesh; // Never silently overwrite an authored mesh.
            mesh = build();
            AssetDatabase.CreateAsset(mesh, path);
            return mesh;
        }

        private static T Required<T>(string path) where T : UnityEngine.Object =>
            AssetDatabase.LoadAssetAtPath<T>(path) ?? throw new InvalidOperationException("Missing asset: " + path);
        private static Transform RequiredChild(Transform parent, string name) =>
            parent.Find(name) ?? throw new InvalidOperationException("Missing child: " + parent.name + "/" + name);
    }
}
