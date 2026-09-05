using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.EditorTools
{
    /// <summary>Editor-only geometry. Callers own the returned, unsaved meshes.</summary>
    public static class PixelFoliageMeshBuilder
    {
        public static Mesh BuildGrass(int seed, int count, Vector2 area, Vector2 heightRange)
        {
            ValidateCountAndRange(count, heightRange);
            if (!PositiveFinite(area.x) || !PositiveFinite(area.y))
                throw new ArgumentOutOfRangeException(nameof(area), "Both area dimensions must be finite and positive.");

            var random = new System.Random(seed);
            var anchors = new Vector3[count];
            var normals = new Vector3[count];
            var sizes = new Vector2[count];
            int rows = Mathf.Clamp(Mathf.RoundToInt(Mathf.Sqrt(count * area.y / area.x)), 1, count);
            for (int row = 0; row < rows; row++)
            {
                int start = (int)((long)row * count / rows);
                int end = (int)((long)(row + 1) * count / rows);
                for (int i = start; i < end; i++)
                {
                    float x = ((i - start + Next(random, 0.15f, 0.85f)) / (end - start) - 0.5f) * area.x;
                    float z = ((row + Next(random, 0.15f, 0.85f)) / rows - 0.5f) * area.y;
                    float height = Next(random, heightRange.x, heightRange.y);
                    anchors[i] = new Vector3(x, 0f, z);
                    normals[i] = Vector3.up;
                    sizes[i] = new Vector2(height * 0.8f, height);
                }
            }
            return BuildCards("Pixel Grass Cards", anchors, normals, sizes, 0f, 0f, random);
        }

        public static Mesh BuildLeaves(int seed, int count, Vector3[] centers, Vector3[] radii, Vector2 sizeRange)
        {
            ValidateCountAndRange(count, sizeRange);
            ValidateEllipsoids(centers, radii);
            var random = new System.Random(seed);
            var anchors = new Vector3[count];
            var normals = new Vector3[count];
            var sizes = new Vector2[count];
            var weights = new double[radii.Length];
            double totalWeight = 0d;
            for (int b = 0; b < radii.Length; b++)
            {
                Vector3 r = radii[b];
                const double power = 1.6075d;
                weights[b] = Math.Pow((Math.Pow((double)r.x * r.y, power) +
                    Math.Pow((double)r.x * r.z, power) + Math.Pow((double)r.y * r.z, power)) / 3d, 1d / power);
                totalWeight += weights[b];
            }

            double accumulated = 0d;
            int start = 0;
            for (int b = 0; b < centers.Length; b++)
            {
                accumulated += weights[b];
                int end = b == centers.Length - 1 ? count : (int)Math.Round(count * accumulated / totalWeight);
                int blobCount = end - start;
                float rotation = Next(random, 0f, Mathf.PI * 2f);
                for (int j = 0; j < blobCount; j++)
                {
                    float y = 1f - 2f * (j + Next(random, 0.25f, 0.75f)) / blobCount;
                    float angle = rotation + j * 2.39996323f + Next(random, -0.12f, 0.12f);
                    float ring = Mathf.Sqrt(Mathf.Max(0f, 1f - y * y));
                    var direction = new Vector3(Mathf.Cos(angle) * ring, y, Mathf.Sin(angle) * ring);
                    int i = start + j;
                    anchors[i] = centers[b] + Vector3.Scale(direction, radii[b]);
                    normals[i] = EllipsoidNormal(direction, radii[b]);
                    float size = Next(random, sizeRange.x, sizeRange.y);
                    sizes[i] = new Vector2(size, size);
                }
                start = end;
            }
            return BuildCards("Pixel Leaf Cards", anchors, normals, sizes, 0.5f, 1f, random);
        }

        /// <summary>Closed ellipsoids for an opaque crown/depth proxy, with outward winding.</summary>
        public static Mesh BuildCrownProxy(Vector3[] centers, Vector3[] radii)
        {
            ValidateEllipsoids(centers, radii);
            const int segments = 12;
            const int rings = 7;
            var vertices = new List<Vector3>();
            var normals = new List<Vector3>();
            var triangles = new List<int>();
            for (int b = 0; b < centers.Length; b++)
            {
                int first = vertices.Count;
                for (int y = 0; y <= rings; y++)
                {
                    float latitude = Mathf.PI * y / rings;
                    for (int x = 0; x <= segments; x++)
                    {
                        float longitude = 2f * Mathf.PI * x / segments;
                        var direction = new Vector3(Mathf.Sin(latitude) * Mathf.Cos(longitude),
                            Mathf.Cos(latitude), Mathf.Sin(latitude) * Mathf.Sin(longitude));
                        vertices.Add(centers[b] + Vector3.Scale(direction, radii[b]));
                        normals.Add(EllipsoidNormal(direction, radii[b]));
                    }
                }
                for (int y = 0; y < rings; y++)
                {
                    for (int x = 0; x < segments; x++)
                    {
                        int a = first + y * (segments + 1) + x;
                        int c = a + segments + 1;
                        // Omit the degenerate half of each polar cell.
                        if (y > 0) AddTriangle(triangles, a, a + 1, c);
                        if (y < rings - 1) AddTriangle(triangles, a + 1, c + 1, c);
                    }
                }
            }
            var mesh = new Mesh { name = "Pixel Foliage Crown Proxy", indexFormat = IndexFormatFor(vertices.Count) };
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static Mesh BuildCards(string name, Vector3[] anchors, Vector3[] normals, Vector2[] sizes,
            float pivotY, float atlasRow, System.Random random)
        {
            int count = anchors.Length;
            var vertices = new Vector3[count * 4];
            var vertexNormals = new Vector3[vertices.Length];
            var colors = new Color[vertices.Length];
            var uv0 = new Vector2[vertices.Length];
            var uv1 = new List<Vector4>(vertices.Length);
            var uv2 = new List<Vector4>(vertices.Length);
            var triangles = new int[count * 6];
            var bounds = new Bounds(anchors[0], Vector3.zero);
            for (int i = 0; i < count; i++)
            {
                var dimensions = new Vector4(sizes[i].x, sizes[i].y, pivotY, atlasRow);
                var variation = new Vector4(Next(random, 0f, 1f), Next(random, 0.93f, 1.07f), 0f, 0f);
                for (int corner = 0; corner < 4; corner++)
                {
                    int v = i * 4 + corner;
                    vertices[v] = anchors[i];
                    vertexNormals[v] = normals[i];
                    colors[v] = Color.white;
                    uv0[v] = new Vector2(corner == 1 || corner == 2 ? 1f : 0f, corner >= 2 ? 1f : 0f);
                    uv1.Add(dimensions);
                    uv2.Add(variation);
                }
                int index = i * 6;
                int first = i * 4;
                triangles[index] = first;
                triangles[index + 1] = first + 1;
                triangles[index + 2] = first + 2;
                triangles[index + 3] = first;
                triangles[index + 4] = first + 2;
                triangles[index + 5] = first + 3;
                float reachY = sizes[i].y * Mathf.Max(pivotY, 1f - pivotY);
                // All vertices are anchors: bounds must include every billboard orientation.
                // The extra 25% admits modest shader wind; larger displacement needs caller expansion.
                float reach = Mathf.Sqrt(sizes[i].x * sizes[i].x * 0.25f + reachY * reachY) * 1.25f;
                bounds.Encapsulate(new Bounds(anchors[i], Vector3.one * (2f * reach)));
            }
            var mesh = new Mesh { name = name, indexFormat = IndexFormatFor(vertices.Length) };
            mesh.vertices = vertices;
            mesh.normals = vertexNormals;
            mesh.colors = colors;
            mesh.uv = uv0;
            mesh.SetUVs(1, uv1);
            mesh.SetUVs(2, uv2);
            mesh.SetTriangles(triangles, 0, false);
            mesh.bounds = bounds;
            return mesh;
        }

        private static Vector3 EllipsoidNormal(Vector3 direction, Vector3 radius)
        {
            // direction/radius equals (position-center)/(radius*radius).
            return new Vector3(direction.x / radius.x, direction.y / radius.y, direction.z / radius.z).normalized;
        }

        private static void ValidateCountAndRange(int count, Vector2 range)
        {
            if (count <= 0 || count > int.MaxValue / 6)
                throw new ArgumentOutOfRangeException(nameof(count), "Card count must be positive and fit mesh arrays.");
            if (!PositiveFinite(range.x) || !PositiveFinite(range.y) || range.x > range.y)
                throw new ArgumentOutOfRangeException(nameof(range), "Size range must be finite, positive and ordered.");
        }

        private static void ValidateEllipsoids(Vector3[] centers, Vector3[] radii)
        {
            if (centers == null) throw new ArgumentNullException(nameof(centers));
            if (radii == null) throw new ArgumentNullException(nameof(radii));
            if (centers.Length == 0 || centers.Length != radii.Length)
                throw new ArgumentException("Matching nonempty center and radius arrays are required.");
            for (int i = 0; i < centers.Length; i++)
            {
                Vector3 c = centers[i];
                Vector3 r = radii[i];
                if (!Finite(c.x) || !Finite(c.y) || !Finite(c.z))
                    throw new ArgumentOutOfRangeException(nameof(centers), "Centers must have finite components.");
                if (!PositiveFinite(r.x) || !PositiveFinite(r.y) || !PositiveFinite(r.z))
                    throw new ArgumentOutOfRangeException(nameof(radii), "Radii must have finite positive components.");
            }
        }

        private static bool Finite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
        private static bool PositiveFinite(float value) => value > 0f && Finite(value);
        private static float Next(System.Random random, float min, float max) => Mathf.Lerp(min, max, (float)random.NextDouble());
        private static IndexFormat IndexFormatFor(int vertexCount) => vertexCount > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16;
        private static void AddTriangle(List<int> triangles, int a, int b, int c)
        {
            triangles.Add(a);
            triangles.Add(b);
            triangles.Add(c);
        }
    }
}
