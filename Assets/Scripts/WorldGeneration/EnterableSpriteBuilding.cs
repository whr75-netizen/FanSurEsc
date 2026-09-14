using System.Collections.Generic;
using FantasySurvival.WorldLighting;
using Unity.AI.Navigation;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>One-storey prototype assembled in the existing map's XZ physics space.</summary>
    public sealed class EnterableSpriteBuilding : MonoBehaviour
    {
        private readonly List<Mesh> ownedMeshes = new List<Mesh>();
        private readonly List<Material> ownedMaterials = new List<Material>();
        public Vector3 InteriorCenter => transform.TransformPoint(new Vector3(0f, 0.5f, 0f));
        public Vector3 DoorOutside { get; private set; }
        public Vector3 DoorInside { get; private set; }
        public Vector3 SolidWallPoint { get; private set; }
        public Bounds LocalInterior { get; private set; }
        public Renderer RoofRenderer { get; private set; }
        public Collider RoofCollider { get; private set; }
        public Renderer[] WallRenderers { get; private set; }
        public Collider[] WallColliders { get; private set; }

        public void Build(IsometricUrbanStyle style, Vector2 size, Vector2 facade,
            float tileSize, Color tint, UrbanOcclusionFader fader, bool reserveFacadeCenter = false)
        {
            float width = size.x, depth = size.y, h = style.wallHeight;
            float t = style.wallThickness;
            LocalInterior = new Bounds(new Vector3(0f, h * 0.5f, 0f),
                new Vector3(width - t * 2f, h, depth - t * 2f));
            Material wallMaterial = Own(style.CreateMaterial(style.wall, true, "Sprite building walls", tint));
            Material floorMaterial = Own(style.CreateMaterial(style.interior, false, "Sprite interior floor", Color.white));
            Material roofMaterial = Own(style.CreateMaterial(style.sidewalk, true, "Sprite building roof", Color.white));
            Material plainModuleMaterial = style.plainModule.image.texture != null
                ? Own(style.CreateMaterial(style.plainModule.image, true, "Original wall module", tint)) : null;
            Material windowModuleMaterial = style.windowModule.image.texture != null
                ? Own(style.CreateMaterial(style.windowModule.image, true, "Original window module", tint)) : plainModuleMaterial;
            CreateTiledHorizontal("Interior Floor", width - t, depth - t, 0.016f, tileSize, floorMaterial);

            var walls = new List<Renderer>();
            var colliders = new List<Collider>();
            bool doorOnZ = Mathf.Abs(facade.y) >= Mathf.Abs(facade.x);
            float sign = doorOnZ ? Mathf.Sign(facade.y) : Mathf.Sign(facade.x);
            if (sign == 0f) sign = 1f;
            for (int side = 0; side < 4; side++)
            {
                bool onZ = side < 2;
                float sideSign = side % 2 == 0 ? -1f : 1f;
                float length = onZ ? width : depth;
                float coordinate = sideSign * (onZ ? depth : width) * 0.5f;
                bool doorway = onZ == doorOnZ && sideSign == sign;
                if (doorway)
                {
                    float door = Mathf.Min(style.doorWidth, length - t * 4f);
                    // Medical POIs already own a loot socket at the facade centre.
                    // Put the new doorway in the right half of that facade, keeping the socket intact.
                    float doorCenter = reserveFacadeCenter ? Mathf.Min(length * 0.25f, (length - door) * 0.5f - t) : 0f;
                    float doorLeft = doorCenter - door * 0.5f, doorRight = doorCenter + door * 0.5f;
                    AddWall(onZ, coordinate, -length * 0.5f, doorLeft + length * 0.5f, 0f, h);
                    AddWall(onZ, coordinate, doorRight, length * 0.5f - doorRight, 0f, h);
                    float lintel = Mathf.Max(0.15f, h - 2.65f);
                    AddWall(onZ, coordinate, doorLeft, door, h - lintel, lintel);
                    if (style.entranceModule.image.texture != null)
                    {
                        Material entrance = Own(style.CreateMaterial(style.entranceModule.image, true, "Original open entrance module", tint));
                        var moduleVertices = new List<Vector3>();
                        var moduleUv = new List<Vector2>();
                        var moduleTriangles = new List<int>();
                        AddArtworkQuad(style.entranceModule, onZ, coordinate, doorCenter - style.wallModuleWidth * 0.5f,
                            style.wallModuleWidth, 0f, h, moduleVertices, moduleUv, moduleTriangles);
                        var artwork = CreateMeshObject("Original open entrance", moduleVertices, moduleUv, moduleTriangles, entrance);
                        walls.Add(artwork.GetComponent<Renderer>());
                        colliders.Add(null); // Artwork is not an invisible physical blocker across the doorway.
                    }
                    Vector3 outward = onZ ? Vector3.forward * sign : Vector3.right * sign;
                    Vector3 center = onZ ? new Vector3(doorCenter, 0f, coordinate) : new Vector3(coordinate, 0f, doorCenter);
                    DoorOutside = transform.TransformPoint(center + outward * 1.4f + Vector3.up * 0.5f);
                    DoorInside = transform.TransformPoint(center - outward * 1.4f + Vector3.up * 0.5f);
                }
                else
                {
                    AddWall(onZ, coordinate, -length * 0.5f, length, 0f, h);
                    SolidWallPoint = transform.TransformPoint(onZ
                        ? new Vector3(0f, 0.8f, coordinate) : new Vector3(coordinate, 0.8f, 0f));
                }
            }
            GameObject roof = CreateTiledHorizontal("Roof - visibility only fades", width + t, depth + t, h, tileSize, roofMaterial);
            RoofRenderer = roof.GetComponent<Renderer>();
            var roofBox = roof.AddComponent<BoxCollider>();
            roofBox.center = new Vector3(0f, h, 0f);
            roofBox.size = new Vector3(width + t, t, depth + t);
            roof.tag = "Obstacle";
            MarkNotWalkable(roof);
            roof.AddComponent<RainShelterOccluder>();
            RoofCollider = roofBox;
            WallRenderers = walls.ToArray();
            WallColliders = colliders.ToArray();
            fader.RegisterBuilding(transform, LocalInterior, RoofRenderer, roofBox, WallRenderers, WallColliders);
            if (style.propAtlas != null && style.propPixelRect.width > 0f && style.propPixelRect.height > 0f)
                AddInteriorProp(style, width, depth);

            void AddWall(bool onZ, float coordinate, float start, float length, float bottom, float height)
            {
                if (length <= 0f) return;
                var vertices = new List<Vector3>();
                var uv = new List<Vector2>();
                var triangles = new List<int>();
                int modules = Mathf.Max(1, Mathf.RoundToInt(length / style.wallModuleWidth));
                float step = length / modules;
                for (int i = 0; i < modules; i++)
                {
                    vertices.Clear(); uv.Clear(); triangles.Clear();
                    float a = start + step * i, b = a + step;
                    Vector3 left = onZ ? new Vector3(a, bottom, coordinate) : new Vector3(coordinate, bottom, a);
                    Vector3 right = onZ ? new Vector3(b, bottom, coordinate) : new Vector3(coordinate, bottom, b);
                    bool useModule = bottom == 0f && plainModuleMaterial != null;
                    bool useWindow = useModule && i % 2 == 1 && windowModuleMaterial != null;
                    Material material = useWindow ? windowModuleMaterial : useModule ? plainModuleMaterial : wallMaterial;
                    if (useModule)
                        AddArtworkQuad(useWindow ? style.windowModule : style.plainModule, onZ, coordinate,
                            a, step, bottom, height, vertices, uv, triangles);
                    else
                        AddQuad(vertices, uv, triangles, left, left + Vector3.up * height,
                            right + Vector3.up * height, right);
                    GameObject wall = CreateMeshObject("Wall " + walls.Count, vertices, uv, triangles, material);
                    wall.tag = "Obstacle";
                    var box = wall.AddComponent<BoxCollider>();
                    box.center = onZ ? new Vector3(a + step * 0.5f, bottom + height * 0.5f, coordinate)
                        : new Vector3(coordinate, bottom + height * 0.5f, a + step * 0.5f);
                    box.size = onZ ? new Vector3(step, height, t) : new Vector3(t, height, step);
                    MarkNotWalkable(wall);
                    walls.Add(wall.GetComponent<Renderer>());
                    colliders.Add(box);
                }
            }
        }

        private static void AddArtworkQuad(IsometricUrbanStyle.WallModule module, bool onZ,
            float coordinate, float start, float length, float bottom, float height,
            List<Vector3> vertices, List<Vector2> uv, List<int> triangles)
        {
            Vector3 Convert(Vector2 pixel)
            {
                Vector2 plane = module.PlaneCoordinate(pixel);
                float along = start + plane.x * length;
                float up = bottom + plane.y * height;
                return onZ ? new Vector3(along, up, coordinate) : new Vector3(coordinate, up, along);
            }
            AddQuad(vertices, uv, triangles, Convert(module.image.p00), Convert(module.image.p01),
                Convert(module.image.p11), Convert(module.image.p10));
        }

        private static void MarkNotWalkable(GameObject target)
        {
            var modifier = target.AddComponent<NavMeshModifier>();
            modifier.overrideArea = true;
            modifier.area = 1;
        }

        private void AddInteriorProp(IsometricUrbanStyle style, float width, float depth)
        {
            Rect r = style.propPixelRect;
            var patch = new IsometricUrbanStyle.AtlasPatch
            {
                texture = style.propAtlas,
                p00 = new Vector2(r.xMin, r.yMax), p01 = new Vector2(r.xMin, r.yMin),
                p11 = new Vector2(r.xMax, r.yMin), p10 = new Vector2(r.xMax, r.yMax)
            };
            Material material = Own(style.CreateMaterial(patch, false, "Atlas room prop", Color.white));
            var vertices = new List<Vector3>();
            var uv = new List<Vector2>();
            var triangles = new List<int>();
            Vector3 anchor = new Vector3(-width * 0.5f + 1.15f, 0.03f, -depth * 0.5f + 1.15f);
            Quaternion orientation = Quaternion.Euler(30f, 45f, 0f);
            float height = 1.35f, halfWidth = height * r.width / r.height * 0.5f;
            AddQuad(vertices, uv, triangles,
                anchor + orientation * new Vector3(-halfWidth, 0f, 0f),
                anchor + orientation * new Vector3(-halfWidth, height, 0f),
                anchor + orientation * new Vector3(halfWidth, height, 0f),
                anchor + orientation * new Vector3(halfWidth, 0f, 0f));
            GameObject prop = CreateMeshObject("Interior atlas prop", vertices, uv, triangles, material);
            var box = prop.AddComponent<BoxCollider>();
            box.center = anchor + Vector3.up * 0.55f;
            box.size = new Vector3(0.65f, 1.1f, 0.65f);
            prop.tag = "Obstacle";
            MarkNotWalkable(prop);
        }

        private GameObject CreateTiledHorizontal(string name, float width, float depth, float height,
            float tileSize, Material material)
        {
            var vertices = new List<Vector3>();
            var uv = new List<Vector2>();
            var triangles = new List<int>();
            int nx = Mathf.Max(1, Mathf.CeilToInt(width / tileSize));
            int nz = Mathf.Max(1, Mathf.CeilToInt(depth / tileSize));
            for (int z = 0; z < nz; z++)
            for (int x = 0; x < nx; x++)
            {
                float x0 = -width * 0.5f + width * x / nx, x1 = -width * 0.5f + width * (x + 1) / nx;
                float z0 = -depth * 0.5f + depth * z / nz, z1 = -depth * 0.5f + depth * (z + 1) / nz;
                AddQuad(vertices, uv, triangles, new Vector3(x0, height, z0), new Vector3(x0, height, z1),
                    new Vector3(x1, height, z1), new Vector3(x1, height, z0));
            }
            return CreateMeshObject(name, vertices, uv, triangles, material);
        }

        private GameObject CreateMeshObject(string name, List<Vector3> vertices, List<Vector2> uv,
            List<int> triangles, Material material)
        {
            var mesh = new Mesh { name = name, hideFlags = HideFlags.DontSave };
            mesh.SetVertices(vertices);
            mesh.SetUVs(0, uv);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            ownedMeshes.Add(mesh);
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var renderer = go.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            return go;
        }

        private static void AddQuad(List<Vector3> vertices, List<Vector2> uv, List<int> triangles,
            Vector3 p00, Vector3 p01, Vector3 p11, Vector3 p10)
        {
            int start = vertices.Count;
            vertices.Add(p00); vertices.Add(p01); vertices.Add(p11); vertices.Add(p10);
            uv.Add(Vector2.zero); uv.Add(Vector2.up); uv.Add(Vector2.one); uv.Add(Vector2.right);
            triangles.Add(start); triangles.Add(start + 1); triangles.Add(start + 2);
            triangles.Add(start); triangles.Add(start + 2); triangles.Add(start + 3);
        }

        private Material Own(Material material) { ownedMaterials.Add(material); return material; }

        private void OnDestroy()
        {
            foreach (Mesh mesh in ownedMeshes) if (mesh != null) Destroy(mesh);
            foreach (Material material in ownedMaterials) if (material != null) Destroy(material);
        }
    }
}
