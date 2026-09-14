using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    [CreateAssetMenu(menuName = "Fantasy Survival/Isometric Urban Style", fileName = "IsometricUrbanStyle")]
    public sealed class IsometricUrbanStyle : ScriptableObject
    {
        public const string ShaderName = "FantasySurvival/World/Isometric Atlas Surface";

        [Serializable]
        public sealed class AtlasPatch
        {
            public Texture2D texture;
            [Tooltip("Optional component mask in the same atlas coordinates and dimensions. RGB source pixels are preserved.")]
            public Texture2D mask;
            [Tooltip("Source pixel centers, with the image origin at top left. Canonical corners: 00, 01, 11, 10.")]
            public Vector2 p00, p01, p11, p10;

            private static readonly Vector2[] Square =
            {
                Vector2.zero, Vector2.up, Vector2.one, Vector2.right
            };

            public AtlasPatch() { }

            public AtlasPatch(Vector2 p00, Vector2 p01, Vector2 p11, Vector2 p10)
            {
                this.p00 = p00;
                this.p01 = p01;
                this.p11 = p11;
                this.p10 = p10;
            }

            public Vector2 GetUv(Vector2 canonicalUv)
            {
                if (!IsFinite(canonicalUv.x) || !IsFinite(canonicalUv.y) ||
                    canonicalUv.x < 0f || canonicalUv.x > 1f || canonicalUv.y < 0f || canonicalUv.y > 1f)
                    throw new ArgumentOutOfRangeException(nameof(canonicalUv), "Patch UV must lie in the unit square.");
                GetHomography(out Vector4 row0, out Vector4 row1, out Vector4 row2);
                return Transform(canonicalUv, row0, row1, row2);
            }

            public void GetHomography(out Vector4 row0, out Vector4 row1, out Vector4 row2)
            {
                if (!TryGetHomography(out row0, out row1, out row2, out string error))
                    throw new InvalidOperationException(error);
            }

            public bool TryValidate(out string error)
            {
                return TryGetHomography(out _, out _, out _, out error);
            }

            private bool TryGetHomography(out Vector4 row0, out Vector4 row1, out Vector4 row2, out string error)
            {
                row0 = row1 = row2 = Vector4.zero;
                if (texture == null || texture.width < 2 || texture.height < 2)
                {
                    error = "An atlas texture of at least 2 by 2 pixels is required.";
                    return false;
                }
                if (mask != null && (mask.width != texture.width || mask.height != texture.height))
                {
                    error = "The optional component mask must have the same dimensions as its source atlas.";
                    return false;
                }

                Vector2[] points = { p00, p01, p11, p10 };
                float winding = 0f;
                for (int i = 0; i < points.Length; i++)
                {
                    Vector2 point = points[i];
                    if (!IsFinite(point.x) || !IsFinite(point.y) || point.x < 0f || point.x >= texture.width ||
                        point.y < 0f || point.y >= texture.height)
                    {
                        error = "Every landmark must be a finite pixel center inside the source atlas.";
                        return false;
                    }
                }

                for (int i = 0; i < points.Length; i++)
                {
                    Vector2 a = points[(i + 1) % 4] - points[i];
                    Vector2 b = points[(i + 2) % 4] - points[(i + 1) % 4];
                    float cross = a.x * b.y - a.y * b.x;
                    if (Mathf.Abs(cross) < 0.01f || (i > 0 && Mathf.Sign(cross) != winding))
                    {
                        error = "Landmarks must form a nondegenerate convex quadrilateral in 00, 01, 11, 10 order.";
                        return false;
                    }
                    winding = Mathf.Sign(cross);
                }

                // Four correspondences solve H with h33 = 1. This is planar perspective mapping,
                // not a per-triangle affine UV fit: https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html
                var system = new double[8, 9];
                var target = new Vector2[4];
                for (int i = 0; i < 4; i++)
                {
                    target[i] = new Vector2((points[i].x + 0.5f) / texture.width,
                        1f - (points[i].y + 0.5f) / texture.height);
                    double x = Square[i].x, y = Square[i].y, u = target[i].x, v = target[i].y;
                    int r = i * 2;
                    system[r, 0] = x; system[r, 1] = y; system[r, 2] = 1d;
                    system[r, 6] = -u * x; system[r, 7] = -u * y; system[r, 8] = u;
                    system[r + 1, 3] = x; system[r + 1, 4] = y; system[r + 1, 5] = 1d;
                    system[r + 1, 6] = -v * x; system[r + 1, 7] = -v * y; system[r + 1, 8] = v;
                }

                // Partial-pivot Gauss-Jordan elimination in double precision; only eight unknowns.
                for (int column = 0; column < 8; column++)
                {
                    int pivot = column;
                    for (int r = column + 1; r < 8; r++)
                        if (Math.Abs(system[r, column]) > Math.Abs(system[pivot, column]))
                            pivot = r;
                    if (Math.Abs(system[pivot, column]) < 1e-12)
                    {
                        error = "The atlas homography is singular.";
                        return false;
                    }
                    for (int c = column; c <= 8; c++)
                    {
                        double swap = system[column, c];
                        system[column, c] = system[pivot, c];
                        system[pivot, c] = swap;
                    }
                    double divisor = system[column, column];
                    for (int c = column; c <= 8; c++)
                        system[column, c] /= divisor;
                    for (int r = 0; r < 8; r++)
                    {
                        if (r == column) continue;
                        double factor = system[r, column];
                        for (int c = column; c <= 8; c++)
                            system[r, c] -= factor * system[column, c];
                    }
                }

                row0 = new Vector4((float)system[0, 8], (float)system[1, 8], (float)system[2, 8], 0f);
                row1 = new Vector4((float)system[3, 8], (float)system[4, 8], (float)system[5, 8], 0f);
                row2 = new Vector4((float)system[6, 8], (float)system[7, 8], 1f, 0f);
                if (!IsFinite(row0) || !IsFinite(row1) || !IsFinite(row2))
                {
                    error = "The atlas homography contains a non-finite coefficient.";
                    return false;
                }

                for (int i = 0; i < 4; i++)
                {
                    // The denominator is affine. Positive values at all four corners exclude a
                    // projective pole throughout the square. 1e-5 UV is at most 0.015px for these atlases.
                    float denominator = row2.x * Square[i].x + row2.y * Square[i].y + row2.z;
                    if (denominator <= 1e-6f ||
                        (Transform(Square[i], row0, row1, row2) - target[i]).sqrMagnitude > 1e-10f)
                    {
                        error = "The atlas mapping crosses a projective pole or exceeds the corner correspondence tolerance.";
                        return false;
                    }
                }
                error = null;
                return true;
            }

            private static Vector2 Transform(Vector2 uv, Vector4 row0, Vector4 row1, Vector4 row2)
            {
                float denominator = row2.x * uv.x + row2.y * uv.y + row2.z;
                return new Vector2((row0.x * uv.x + row0.y * uv.y + row0.z) / denominator,
                    (row1.x * uv.x + row1.y * uv.y + row1.z) / denominator);
            }
        }

        [Serializable]
        public sealed class WallModule
        {
            public AtlasPatch image;
            [Tooltip("Authored image landmarks on one vertical wall plane, in original top-left pixel coordinates.")]
            public Vector2 baseLeft, baseRight, topLeft;

            /// <summary>Inverts pixel = baseLeft + s*(baseRight-baseLeft) + t*(topLeft-baseLeft).</summary>
            public Vector2 PlaneCoordinate(Vector2 pixel)
            {
                if (!IsFinite(pixel.x) || !IsFinite(pixel.y))
                    throw new ArgumentOutOfRangeException(nameof(pixel), "Source pixel coordinates must be finite.");
                if (!TryBasis(out Vector2 horizontal, out Vector2 vertical, out float determinant, out string error))
                    throw new InvalidOperationException(error);
                Vector2 delta = pixel - baseLeft;
                // Values outside 0..1 intentionally preserve caps, sills and other authored overhangs.
                return new Vector2((delta.x * vertical.y - delta.y * vertical.x) / determinant,
                    (horizontal.x * delta.y - horizontal.y * delta.x) / determinant);
            }

            public bool TryValidate(out string error)
            {
                if (image == null) { error = "The wall module image patch is missing."; return false; }
                if (!image.TryValidate(out error)) return false;
                if (!TryBasis(out _, out _, out _, out error)) return false;
                Vector2[] landmarks = { baseLeft, baseRight, topLeft };
                for (int i = 0; i < landmarks.Length; i++)
                {
                    Vector2 p = landmarks[i];
                    if (p.x < 0f || p.y < 0f || p.x >= image.texture.width || p.y >= image.texture.height)
                    {
                        error = "Every wall plane landmark must lie inside the source atlas.";
                        return false;
                    }
                }
                error = null;
                return true;
            }

            private bool TryBasis(out Vector2 horizontal, out Vector2 vertical, out float determinant, out string error)
            {
                horizontal = baseRight - baseLeft;
                vertical = topLeft - baseLeft;
                determinant = horizontal.x * vertical.y - horizontal.y * vertical.x;
                float scale = horizontal.magnitude * vertical.magnitude;
                if (!IsFinite(baseLeft.x) || !IsFinite(baseLeft.y) || !IsFinite(horizontal.x) ||
                    !IsFinite(horizontal.y) || !IsFinite(vertical.x) || !IsFinite(vertical.y) ||
                    !IsFinite(determinant) || !IsFinite(scale) || scale < 1e-4f ||
                    Mathf.Abs(determinant) <= Mathf.Max(1e-4f, scale * 1e-6f))
                {
                    error = "Wall plane landmarks must form a finite, nondegenerate two-dimensional basis.";
                    return false;
                }
                error = null;
                return true;
            }
        }

        [Header("Source atlases and authored planar landmarks")]
        public Shader surfaceShader;
        // XZ quad order is SW, NW, NE, SE. At yaw 45 this maps to image bottom, left, top, right.
        // These are source surface annotations; the painted tile thickness is deliberately excluded.
        public AtlasPatch ground = RoadPatch();
        public AtlasPatch sidewalk = new AtlasPatch(new Vector2(542, 466), new Vector2(390, 374),
            new Vector2(548, 277), new Vector2(701, 375));
        public AtlasPatch road = RoadPatch();
        public AtlasPatch interior = new AtlasPatch(new Vector2(198, 734), new Vector2(55, 655),
            new Vector2(197, 573), new Vector2(339, 655));
        public AtlasPatch wall = new AtlasPatch(new Vector2(145, 160), new Vector2(145, 53),
            new Vector2(253, 102), new Vector2(253, 208));
        public Texture2D propAtlas;
        public Rect propPixelRect = new Rect(787f, 14f, 185f, 254f);

        [Header("Complete source wall modules")]
        // Manual source annotations (about +/-2px), not recovered 3D geometry. Full alpha components
        // retain the original caps, windows and entrances. The rectangle alone also contains nearby
        // sheet fragments: assign a connected-component mask to isolate the intended source pixels.
        // Surface anchors use the outer front wall plane; painted depth remains a single-view image.
        public WallModule plainModule = new WallModule
        {
            image = RectanglePatch(103, 1, 295, 260),
            baseLeft = new Vector2(110, 178), baseRight = new Vector2(271, 253), topLeft = new Vector2(110, 22)
        };
        public WallModule windowModule = new WallModule
        {
            image = RectanglePatch(795, 2, 981, 272),
            baseLeft = new Vector2(804, 198), baseRight = new Vector2(949, 265), topLeft = new Vector2(804, 26)
        };
        public WallModule entranceModule = new WallModule
        {
            image = RectanglePatch(1128, 265, 1349, 574),
            baseLeft = new Vector2(1138, 492), baseRight = new Vector2(1325, 568), topLeft = new Vector2(1138, 284)
        };

        [Header("World dimensions")]
        [Min(0.1f)] public float wallHeight = 3.4f;
        [Min(0.1f)] public float wallModuleWidth = 3.4f;
        [Min(0.1f)] public float doorWidth = 2.4f;
        [Min(0.01f)] public float wallThickness = 0.2f;

        /// <summary>Returns a new material. Its caller owns and destroys it; this asset holds no mutable material state.</summary>
        public Material CreateMaterial(AtlasPatch patch, bool transparent, string materialName, Color tint)
        {
            if (patch == null) throw new ArgumentNullException(nameof(patch));
            patch.GetHomography(out Vector4 row0, out Vector4 row1, out Vector4 row2);
            Shader shader = surfaceShader != null ? surfaceShader : Shader.Find(ShaderName);
            if (shader == null) throw new InvalidOperationException("The isometric atlas surface shader is missing.");
            var material = new Material(shader) { name = materialName };
            material.SetTexture("_BaseMap", patch.texture);
            material.SetTexture("_MaskMap", patch.mask != null ? patch.mask : Texture2D.whiteTexture);
            material.SetColor("_BaseColor", tint);
            material.SetVector("_Homography0", row0);
            material.SetVector("_Homography1", row1);
            material.SetVector("_Homography2", row2);
            material.SetFloat("_ZWrite", transparent ? 0f : 1f);
            material.SetFloat("_SrcBlend", (float)(transparent ? BlendMode.SrcAlpha : BlendMode.One));
            material.SetFloat("_DstBlend", (float)(transparent ? BlendMode.OneMinusSrcAlpha : BlendMode.Zero));
            material.SetOverrideTag("RenderType", transparent ? "Transparent" : "Opaque");
            material.renderQueue = (int)(transparent ? RenderQueue.Transparent : RenderQueue.Geometry);
            return material;
        }

        public bool TryValidate(out string error)
        {
            AtlasPatch[] patches = { ground, sidewalk, road, interior, wall };
            string[] names = { nameof(ground), nameof(sidewalk), nameof(road), nameof(interior), nameof(wall) };
            for (int i = 0; i < patches.Length; i++)
            {
                if (patches[i] == null) { error = names[i] + ": patch is missing."; return false; }
                if (!patches[i].TryValidate(out error)) { error = names[i] + ": " + error; return false; }
            }
            WallModule[] modules = { plainModule, windowModule, entranceModule };
            string[] moduleNames = { nameof(plainModule), nameof(windowModule), nameof(entranceModule) };
            for (int i = 0; i < modules.Length; i++)
            {
                // Old style assets remain valid until the optional complete-module inputs are assigned.
                if (modules[i]?.image?.texture == null) continue;
                if (!modules[i].TryValidate(out error)) { error = moduleNames[i] + ": " + error; return false; }
            }
            if (surfaceShader == null || surfaceShader.name != ShaderName)
            {
                error = "Assign the isometric atlas surface shader to preserve its build dependency.";
                return false;
            }
            if (!Positive(wallHeight) || !Positive(wallModuleWidth) || !Positive(doorWidth) ||
                !Positive(wallThickness) || wallThickness >= wallModuleWidth || wallThickness >= wallHeight)
            {
                error = "World dimensions must be finite and positive, with thickness smaller than the wall width and height.";
                return false;
            }
            if (propAtlas != null && (!IsFinite(propPixelRect.x) || !IsFinite(propPixelRect.y) ||
                !Positive(propPixelRect.width) || !Positive(propPixelRect.height) || propPixelRect.xMin < 0f ||
                propPixelRect.yMin < 0f || propPixelRect.xMax > propAtlas.width || propPixelRect.yMax > propAtlas.height))
            {
                error = "The optional prop rectangle must lie inside its atlas in top-left pixel coordinates.";
                return false;
            }
            error = null;
            return true;
        }

        private static AtlasPatch RoadPatch() => new AtlasPatch(new Vector2(186, 215), new Vector2(35, 127),
            new Vector2(195, 31), new Vector2(347, 122));
        private static AtlasPatch RectanglePatch(float left, float top, float right, float bottom) =>
            new AtlasPatch(new Vector2(left, bottom), new Vector2(left, top),
                new Vector2(right, top), new Vector2(right, bottom));
        private static bool Positive(float value) => IsFinite(value) && value > 0f;
        private static bool IsFinite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
        private static bool IsFinite(Vector4 value) => IsFinite(value.x) && IsFinite(value.y) && IsFinite(value.z) && IsFinite(value.w);
    }
}
