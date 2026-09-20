using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>
    /// Presentation derived from the existing road graph and surface grid. It owns no
    /// navigation or layout state. Atlas top faces are mapped in each road's metric basis.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class UrbanRoadMarkings : MonoBehaviour
    {
        private enum MarkKind { Yellow, White, Crosswalk }

        private readonly List<Mesh> meshes = new List<Mesh>();
        private readonly List<Material> materials = new List<Material>();
        private readonly List<Vector2[]> acceptedQuads = new List<Vector2[]>();
        private UrbanSurfaceGrid grid;
        private IsometricUrbanStyle.AtlasPatch[] markingPatches;
        private bool metricPaint;

        public int YellowQuadCount { get; private set; }
        public int WhiteQuadCount { get; private set; }
        public int CrosswalkQuadCount { get; private set; }
        public int RejectedBoundaryQuadCount { get; private set; }
        public int MarkingRendererCount => meshes.Count;
        public bool AllQuadsInsideRoad => TryValidateContainment(out _);

        // Original Roads.png pixel landmarks, top-left origin. Every patch excludes
        // the illustrated slab sides. Canonical +X follows the painted straight lines.
        public static IsometricUrbanStyle.AtlasPatch CrackedRoadPatch(Texture2D atlas) =>
            Patch(atlas, 547, 217, 392, 124, 546, 31, 701, 124);
        public static IsometricUrbanStyle.AtlasPatch CrackedSidewalkPatch(Texture2D atlas) =>
            Patch(atlas, 901, 470, 744, 376, 897, 281, 1057, 374);
        public static IsometricUrbanStyle.AtlasPatch ManholePatch(Texture2D atlas) =>
            Patch(atlas, 902, 716, 746, 621, 901, 526, 1059, 621);

        public static void Create(Transform parent, UrbanMapLayout layout, IsometricUrbanStyle style,
            float surfaceHeight, UrbanSurfaceGrid displayGrid = null)
        {
            var owner = new GameObject("GeneratedRoadMarkings");
            owner.transform.SetParent(parent, false);
            owner.AddComponent<UrbanRoadMarkings>().Build(layout, style, surfaceHeight, displayGrid);
        }

        /// <summary>Rechecks the actual accepted geometry, not just construction counters.</summary>
        public bool TryValidateContainment(out int outsideQuadCount)
        {
            outsideQuadCount = 0;
            if (grid == null) return false;
            for (int index = 0; index < acceptedQuads.Count; index++)
                if (!IsEntirelyRoad(grid, acceptedQuads[index])) outsideQuadCount++;
            return outsideQuadCount == 0;
        }

        public bool TryValidateSourcePatches(out string error)
        {
            if (markingPatches == null) { error = "Road markings have not been built."; return false; }
            for (int index = 0; index < markingPatches.Length; index++)
                if (!markingPatches[index].TryValidate(out error)) return false;
            error = null;
            return true;
        }

        private void Build(UrbanMapLayout layout, IsometricUrbanStyle style, float surfaceHeight,
            UrbanSurfaceGrid displayGrid)
        {
            grid = displayGrid ?? layout.SurfaceGrid;
            metricPaint = style.useMetricRoadPaint;
            if (metricPaint && (style.yellowLine?.texture == null || style.whiteLine?.texture == null || style.crosswalk?.texture == null))
                throw new InvalidOperationException("Metric road paint requires persistent marking textures; legacy atlas coordinates do not apply.");
            Texture2D atlas = style.road.texture;
            markingPatches = new[]
            {
                style.yellowLine != null && style.yellowLine.texture != null ? style.yellowLine : Patch(atlas, 1257, 222, 1096, 126, 1253, 31, 1417, 127),
                style.whiteLine != null && style.whiteLine.texture != null ? style.whiteLine : Patch(atlas, 902, 218, 743, 124, 899, 31, 1058, 125),
                style.crosswalk != null && style.crosswalk.texture != null ? style.crosswalk : Patch(atlas, 191, 471, 30, 376, 192, 282, 349, 376)
            };
            if (!TryValidateSourcePatches(out string error)) throw new InvalidOperationException(error);

            var batches = new GeometryBatch[3];
            for (int index = 0; index < batches.Length; index++) batches[index] = new GeometryBatch();
            var incident = new List<int>[layout.Nodes.Count];
            for (int node = 0; node < incident.Length; node++) incident[node] = new List<int>();
            for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = layout.Roads[roadIndex];
                incident[road.FromNodeIndex].Add(roadIndex);
                incident[road.ToNodeIndex].Add(roadIndex);
            }

            float tile = grid.TileSize;
            // Paint sits 7 mm above the existing surface, preventing coplanar depth fighting.
            float height = surfaceHeight + 0.007f;
            for (int roadIndex = 0; roadIndex < layout.Roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = layout.Roads[roadIndex];
                Vector2 start = road.Start;
                Vector2 end = road.End;
                int startNode = road.FromNodeIndex, endNode = road.ToNodeIndex;
                Vector2 tangent = (end - start).normalized;
                // A common signed basis keeps repeated imagery aligned across collinear edges.
                if (tangent.x < -0.0001f || (Mathf.Abs(tangent.x) < 0.0001f && tangent.y < 0f))
                {
                    Vector2 swap = start; start = end; end = swap;
                    int nodeSwap = startNode; startNode = endNode; endNode = nodeSwap;
                    tangent = -tangent;
                }
                Vector2 normal = new Vector2(-tangent.y, tangent.x);
                float length = Vector2.Distance(start, end);
                float startClearance = JunctionClearance(startNode, layout, incident, tangent,
                    road.Width * 0.5f, out bool startJunction);
                float endClearance = JunctionClearance(endNode, layout, incident, tangent,
                    road.Width * 0.5f, out bool endJunction);
                float lineStart = startJunction ? startClearance + tile : 0f;
                float lineEnd = length - (endJunction ? endClearance + tile : 0f);
                AddLaneLines(batches, start, tangent, normal, lineStart, lineEnd,
                    road.Width, tile, height);

                if (startJunction && startClearance + tile < length - endClearance)
                    AddCrosswalk(batches, start, tangent, normal, startClearance,
                        road.Width, tile, height);
                if (endJunction && endClearance + tile < length - startClearance)
                    AddCrosswalk(batches, end, -tangent, -normal, endClearance,
                        road.Width, tile, height);
            }

            var displayBounds = new Rect(grid.LocalOrigin,
                new Vector2(grid.Width * tile, grid.Height * tile));
            List<UrbanRoadContinuation> continuations = UrbanRoadContinuation.Create(layout.Nodes, layout.Roads);
            for (int index = 0; index < continuations.Count; index++)
            {
                UrbanRoadContinuation continuation = continuations[index];
                float length = continuation.ExitDistance(displayBounds);
                if (length <= 0f) continue;
                Vector2 start = continuation.Start;
                Vector2 tangent = continuation.Tangent;
                float clearance = JunctionClearance(continuation.NodeIndex, layout, incident, tangent,
                    continuation.Width * 0.5f, out bool junction);
                float lineStart = junction ? clearance + tile : 0f;
                float lineEnd = length;
                if (tangent.x < -0.0001f || (Mathf.Abs(tangent.x) < 0.0001f && tangent.y < 0f))
                {
                    start += tangent * length;
                    tangent = -tangent;
                    lineEnd = length - lineStart;
                    lineStart = 0f;
                }
                Vector2 normal = new Vector2(-tangent.y, tangent.x);
                AddLaneLines(batches, start, tangent, normal, lineStart, lineEnd,
                    continuation.Width, tile, height);
                // Display boundaries are not graph intersections or pedestrian crossings.
                // Only the existing graph loop above creates crosswalks.
            }

            for (int kind = 0; kind < batches.Length; kind++)
            {
                GeometryBatch batch = batches[kind];
                if (batch.triangles.Count == 0) continue;
                var mesh = new Mesh
                {
                    name = "Road " + (MarkKind)kind + " Atlas Mesh",
                    hideFlags = HideFlags.DontSave,
                    indexFormat = IndexFormat.UInt32
                };
                mesh.SetVertices(batch.vertices);
                mesh.SetNormals(batch.normals);
                mesh.SetUVs(0, batch.uv);
                mesh.SetTriangles(batch.triangles, 0);
                mesh.RecalculateBounds();
                meshes.Add(mesh);
                Material material = style.CreateMaterial(markingPatches[kind], false,
                    "Road " + (MarkKind)kind + " Source Atlas", metricPaint
                    ? (kind==0 ? new Color(.83f,.67f,.32f) : new Color(.82f,.81f,.75f)) : Color.white);
                materials.Add(material);
                var surface = new GameObject("Road " + (MarkKind)kind);
                surface.transform.SetParent(transform, false);
                surface.AddComponent<MeshFilter>().sharedMesh = mesh;
                MeshRenderer renderer = surface.AddComponent<MeshRenderer>();
                renderer.sharedMaterial = material;
                renderer.shadowCastingMode = ShadowCastingMode.Off;
                renderer.receiveShadows = true;
            }
        }

        private void AddLaneLines(GeometryBatch[] batches, Vector2 origin, Vector2 tangent,
            Vector2 normal, float lineStart, float lineEnd, float roadWidth, float tile, float height)
        {
            if (lineEnd <= lineStart + 0.0001f) return;
            if(metricPaint)
            {
                // Physical paint widths are independent of the two-metre terrain cells.
                const float stroke=.125f;
                if(roadWidth>=9f)
                {
                    AddCandidate(batches,MarkKind.Yellow,origin,tangent,normal,lineStart,lineEnd,-.1875f,-.0625f,height);
                    AddCandidate(batches,MarkKind.Yellow,origin,tangent,normal,lineStart,lineEnd,.0625f,.1875f,height);
                    float parkingBoundary=roadWidth*.5f-2f;
                    foreach(float side in new[]{-1f,1f})
                        Dashes(MarkKind.White,side*parkingBoundary,3f,6f);
                }
                else Dashes(MarkKind.Yellow,0f,3f,6f);
                return;

                void Dashes(MarkKind kind,float lateral,float length,float period)
                {
                    float phase=Vector2.Dot(origin,tangent);
                    float first=Mathf.Floor((phase+lineStart)/period)*period-phase;
                    for(float d=first;d<lineEnd;d+=period)
                    {
                        float a=Mathf.Max(lineStart,d),b=Mathf.Min(lineEnd,d+length);
                        if(b>a)AddCandidate(batches,kind,origin,tangent,normal,a,b,lateral-stroke*.5f,lateral+stroke*.5f,height);
                    }
                }
            }
            float phase = Vector2.Dot(origin, tangent);
            float first = Mathf.Floor((phase + lineStart) / tile) * tile - phase;
            for (float distance = first; distance < lineEnd - 0.0001f; distance += tile)
            {
                float from = Mathf.Max(distance, lineStart), to = Mathf.Min(distance + tile, lineEnd);
                float uvFrom = (from - distance) / tile, uvTo = (to - distance) / tile;
                AddCandidate(batches, MarkKind.Yellow, origin, tangent, normal,
                    from, to, -tile * 0.5f, tile * 0.5f, height, 1f, uvFrom, uvTo);
                // Each half of the existing 14/18 m road is divided into two equal lanes.
                float laneDivider = roadWidth * 0.25f;
                AddCandidate(batches, MarkKind.White, origin, tangent, normal, from,
                    to, laneDivider - tile * 0.5f, laneDivider + tile * 0.5f, height, 1f, uvFrom, uvTo);
                AddCandidate(batches, MarkKind.White, origin, tangent, normal, from,
                    to, -laneDivider - tile * 0.5f, -laneDivider + tile * 0.5f, height, 1f, uvFrom, uvTo);
            }
        }

        private void AddCrosswalk(GeometryBatch[] batches, Vector2 origin, Vector2 tangent,
            Vector2 normal, float distance, float roadWidth, float tile, float height)
        {
            if(metricPaint)
            {
                float half=roadWidth*.5f-.5f;
                for(float across=-half;across<half;across+=1f)
                    AddCandidate(batches,MarkKind.Crosswalk,origin,tangent,normal,distance,distance+2f,
                        across,Mathf.Min(across+.5f,half),height);
                return;
            }
            // Crosswalk sampling swaps the two source axes below; the stripe axis
            // follows road travel while repetition spans the road width.
            // Repeat full-size patches laterally and crop the last patch instead of stretching it.
            float halfWidth = Mathf.Max(0f, roadWidth * 0.5f - tile * 0.5f);
            for (float across = -halfWidth; across < halfWidth - 0.0001f; across += tile)
            {
                float end = Mathf.Min(across + tile, halfWidth);
                AddCandidate(batches, MarkKind.Crosswalk, origin, tangent, normal,
                    distance, distance + tile, across, end, height, (end - across) / tile);
            }
        }

        private void AddCandidate(GeometryBatch[] batches, MarkKind kind, Vector2 origin,
            Vector2 tangent, Vector2 normal, float start, float end, float left, float right,
            float height, float uvAcross = 1f, float uvAlongFrom = 0f, float uvAlongTo = 1f)
        {
            Vector2[] quad =
            {
                origin + tangent * start + normal * left,
                origin + tangent * start + normal * right,
                origin + tangent * end + normal * right,
                origin + tangent * end + normal * left
            };
            if (!IsEntirelyRoad(grid, quad)) { RejectedBoundaryQuadCount++; return; }
            acceptedQuads.Add(quad);
            GeometryBatch batch = batches[(int)kind];
            int first = batch.vertices.Count;
            for (int index = 0; index < 4; index++)
            {
                batch.vertices.Add(new Vector3(quad[index].x, height, quad[index].y));
                batch.normals.Add(Vector3.up);
            }
            if (kind == MarkKind.Crosswalk)
            {
                batch.uv.Add(new Vector2(0f, uvAlongFrom));
                batch.uv.Add(new Vector2(uvAcross, uvAlongFrom));
                batch.uv.Add(new Vector2(uvAcross, uvAlongTo));
                batch.uv.Add(new Vector2(0f, uvAlongTo));
            }
            else
            {
                batch.uv.Add(new Vector2(uvAlongFrom, 0f));
                batch.uv.Add(new Vector2(uvAlongFrom, uvAcross));
                batch.uv.Add(new Vector2(uvAlongTo, uvAcross));
                batch.uv.Add(new Vector2(uvAlongTo, 0f));
            }
            batch.triangles.Add(first); batch.triangles.Add(first + 1); batch.triangles.Add(first + 2);
            batch.triangles.Add(first); batch.triangles.Add(first + 2); batch.triangles.Add(first + 3);
            switch (kind)
            {
                case MarkKind.Yellow: YellowQuadCount++; break;
                case MarkKind.White: WhiteQuadCount++; break;
                case MarkKind.Crosswalk: CrosswalkQuadCount++; break;
            }
        }

        private static float JunctionClearance(int node, UrbanMapLayout layout,
            IReadOnlyList<List<int>> incident, Vector2 tangent, float ownHalfWidth, out bool junction)
        {
            List<int> roads = incident[node];
            junction = roads.Count > 2;
            if (roads.Count == 2)
            {
                UrbanRoadSegment first = layout.Roads[roads[0]], second = layout.Roads[roads[1]];
                Vector2 a = (first.End - first.Start).normalized;
                Vector2 b = (second.End - second.Start).normalized;
                junction = Mathf.Abs(Vector2.Dot(a, b)) < 0.9999f;
            }
            if (!junction) return 0f;
            float clearance = 0f;
            for (int index = 0; index < roads.Count; index++)
            {
                UrbanRoadSegment other = layout.Roads[roads[index]];
                Vector2 direction = (other.End - other.Start).normalized;
                float sine = Mathf.Abs(tangent.x * direction.y - tangent.y * direction.x);
                if (sine < 0.0001f) continue;
                // Projection of the complete approach width onto the crossing strip normal.
                // A simple half-width trim would still paint inside an acute 45-degree join.
                float cosine = Mathf.Abs(Vector2.Dot(tangent, direction));
                clearance = Mathf.Max(clearance, (other.Width * 0.5f + ownHalfWidth * cosine) / sine);
            }
            return clearance;
        }

        private static bool IsEntirelyRoad(UrbanSurfaceGrid surface, Vector2[] quad)
        {
            Vector2 minimum = quad[0], maximum = quad[0];
            for (int index = 1; index < quad.Length; index++)
            {
                minimum = Vector2.Min(minimum, quad[index]);
                maximum = Vector2.Max(maximum, quad[index]);
            }
            Vector2 origin = surface.LocalOrigin;
            float size = surface.TileSize;
            if (minimum.x < origin.x - 0.0001f || minimum.y < origin.y - 0.0001f ||
                maximum.x > origin.x + surface.Width * size + 0.0001f ||
                maximum.y > origin.y + surface.Height * size + 0.0001f) return false;
            int x0 = Mathf.Clamp(Mathf.FloorToInt((minimum.x - origin.x) / size), 0, surface.Width - 1);
            int z0 = Mathf.Clamp(Mathf.FloorToInt((minimum.y - origin.y) / size), 0, surface.Height - 1);
            int x1 = Mathf.Clamp(Mathf.FloorToInt((maximum.x - origin.x) / size), 0, surface.Width - 1);
            int z1 = Mathf.Clamp(Mathf.FloorToInt((maximum.y - origin.y) / size), 0, surface.Height - 1);
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                {
                    if (UrbanSurfaceGrid.IsRoad(surface.GetKind(x, z))) continue;
                    var cell = new Rect(origin.x + x * size, origin.y + z * size, size, size);
                    if (OverlapsArea(quad, cell)) return false;
                }
            return true;
        }

        // Separating-axis test: positive-area overlap with any non-road cell rejects the
        // whole quad. Checking only its corners would miss a diagonal crossing a missing cell.
        private static bool OverlapsArea(Vector2[] quad, Rect cell)
        {
            if (Separated(quad, cell, Vector2.right) || Separated(quad, cell, Vector2.up)) return false;
            for (int edge = 0; edge < 2; edge++)
            {
                Vector2 direction = quad[edge + 1] - quad[edge];
                Vector2 axis = new Vector2(-direction.y, direction.x).normalized;
                if (Separated(quad, cell, axis)) return false;
            }
            return true;
        }

        private static bool Separated(Vector2[] quad, Rect cell, Vector2 axis)
        {
            float minimum = Vector2.Dot(quad[0], axis), maximum = minimum;
            for (int index = 1; index < quad.Length; index++)
            {
                float value = Vector2.Dot(quad[index], axis);
                minimum = Mathf.Min(minimum, value); maximum = Mathf.Max(maximum, value);
            }
            float center = Vector2.Dot(cell.center, axis);
            float radius = cell.width * 0.5f * Mathf.Abs(axis.x) + cell.height * 0.5f * Mathf.Abs(axis.y);
            return maximum <= center - radius + 0.00001f || minimum >= center + radius - 0.00001f;
        }

        private static IsometricUrbanStyle.AtlasPatch Patch(Texture2D atlas,
            float x00, float y00, float x01, float y01, float x11, float y11, float x10, float y10)
        {
            return new IsometricUrbanStyle.AtlasPatch(new Vector2(x00, y00), new Vector2(x01, y01),
                new Vector2(x11, y11), new Vector2(x10, y10)) { texture = atlas };
        }

        private void OnDestroy()
        {
            for (int index = 0; index < meshes.Count; index++) if (meshes[index] != null) Destroy(meshes[index]);
            for (int index = 0; index < materials.Count; index++) if (materials[index] != null) Destroy(materials[index]);
        }

        private sealed class GeometryBatch
        {
            public readonly List<Vector3> vertices = new List<Vector3>();
            public readonly List<Vector3> normals = new List<Vector3>();
            public readonly List<Vector2> uv = new List<Vector2>();
            public readonly List<int> triangles = new List<int>();
        }
    }
}
