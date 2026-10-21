using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// Default-OFF replacement of the hair source, not a correction of a rendered mask.
// Canonical coordinates: top-left, 480x272, one unit per final logical pixel.
public static class HeadRegion502
{
    public static bool Enabled;
    // Default-OFF accuracy experiment inside the already default-OFF region path.
    // False retains the504 input for same-pose comparisons; no extra render layer.
    public static bool UseVisibleArea505;
    public static int AreaUncertainCells505, AreaSelectionAmbiguous505;
    public static string Status = "disabled";
    public static readonly List<Vector2[]> SourceLoops = new();
    // RDP approximation diagnostics. SelectedLoops owns the chosen boundary;
    // its fidelity input is the original closed source region, not this fit.
    public static readonly List<Vector2[]> Curves = new();
    public static readonly List<Vector2[]> SelectedLoops = new();
    public static readonly List<Packet> Packets = new();
    public static readonly bool[] Hair = new bool[480 * 272];
    public static readonly bool[] Parent = new bool[480 * 272];
    public static double BuildMilliseconds;
    public static int Unsupported;
    public const int ExtractionScale = 8;
    public const float CurveError = .1875f;
    public const float BoundaryCost = .14f;

    [Serializable] public sealed class Packet
    {
        public int x, y, submesh, primitive;
        public Vector3 barycentric, world;
        public Vector2 uv, projected;
        public float depth, distance;
    }
    sealed class Triangle
    {
        public int sm, primitive, ia, ib, ic;
        public Vector2 a, b, c;
        public float minX, maxX, minY, maxY;
    }
    sealed class Piece
    {
        public Mesh mesh;
        public readonly List<Vector3> vertices = new(), normals = new();
        public readonly List<Vector4> tangents = new(), source = new(), primitive = new();
        public readonly List<Vector2> uv = new();
        public readonly List<int> indices = new();
        public Piece(string name) { mesh = new Mesh { name = name, hideFlags = HideFlags.DontSave, indexFormat = IndexFormat.UInt32 }; }
        public void Clear() { vertices.Clear(); normals.Clear(); tangents.Clear(); source.Clear(); primitive.Clear(); uv.Clear(); indices.Clear(); }
        public void Upload(Bounds bounds)
        {
            mesh.Clear(); mesh.SetVertices(vertices); mesh.SetNormals(normals); mesh.SetTangents(tangents);
            mesh.SetUVs(0, uv); mesh.SetUVs(3, primitive); mesh.SetUVs(4, source); mesh.SetTriangles(indices, 0); mesh.bounds = bounds;
        }
    }
    static Full319View335 current;
    static Piece[,] pieces;
    static Texture2D mask;
    static ComputeShader gate;
    static readonly Dictionary<(Material, int), Material> materials = new();
    static readonly string[] ShaderNames = { "Probe", "Native", "World", "Independent", "Legacy" };
    static readonly List<Triangle> triangles = new();
    static Vector3[] vertices, normals, world;
    static Vector4[] tangents;
    static Vector2[] uv, projected;
    static Matrix4x4 inverseProjection, cameraToWorld, worldToLocal;
    static float Cross(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;
    static float Area(IList<Vector2> p) { double a = 0; for (int i = 0; i < p.Count; i++) { var u = p[i]; var v = p[(i + 1) % p.Count]; a += (double)u.x * v.y - (double)u.y * v.x; } return (float)(a * .5); }
    static Vector3 Bary(Vector2 p, Triangle t)
    {
        float d = Cross(t.b - t.a, t.c - t.a);
        if (Mathf.Abs(d) < 1e-10f) return new Vector3(-1, -1, -1);
        float v = Cross(p - t.a, t.c - t.a) / d, w = Cross(t.b - t.a, p - t.a) / d;
        return new Vector3(1 - v - w, v, w);
    }

    // Analytic triangle/scanline intersections are unioned on a 1/8-cell extraction
    // lattice. This is a bounded contour extractor, never the final coverage rule.
    static bool[] Union(Vector2[] points, int[][] indices, out RectInt bounds)
    {
        int x0 = Mathf.Clamp(Mathf.FloorToInt(points.Min(p => p.x)) - 2, 0, 479);
        int y0 = Mathf.Clamp(Mathf.FloorToInt(points.Min(p => p.y)) - 2, 0, 271);
        int x1 = Mathf.Clamp(Mathf.CeilToInt(points.Max(p => p.x)) + 2, x0 + 1, 480);
        int y1 = Mathf.Clamp(Mathf.CeilToInt(points.Max(p => p.y)) + 2, y0 + 1, 272);
        bounds = new RectInt(x0, y0, x1 - x0, y1 - y0);
        int w = bounds.width * ExtractionScale, h = bounds.height * ExtractionScale;
        var filled = new bool[w * h];
        foreach (var ix in indices) for (int k = 0; k < ix.Length; k += 3)
        {
            var p = new[] { points[ix[k]], points[ix[k + 1]], points[ix[k + 2]] };
            int ya = Mathf.Max(0, Mathf.CeilToInt((p.Min(q => q.y) - y0) * ExtractionScale - .5f));
            int yb = Mathf.Min(h - 1, Mathf.FloorToInt((p.Max(q => q.y) - y0) * ExtractionScale - .5f));
            for (int y = ya; y <= yb; y++)
            {
                float line = y0 + (y + .5f) / ExtractionScale, lo = float.PositiveInfinity, hi = float.NegativeInfinity;
                for (int e = 0; e < 3; e++)
                {
                    var a = p[e]; var b = p[(e + 1) % 3];
                    if ((a.y <= line && b.y > line) || (b.y <= line && a.y > line))
                    { float x = a.x + (line - a.y) * (b.x - a.x) / (b.y - a.y); lo = Mathf.Min(lo, x); hi = Mathf.Max(hi, x); }
                }
                if (lo > hi) continue;
                int xa = Mathf.Max(0, Mathf.CeilToInt((lo - x0) * ExtractionScale - .5f));
                int xb = Mathf.Min(w - 1, Mathf.FloorToInt((hi - x0) * ExtractionScale - .5f));
                for (int x = xa; x <= xb; x++) filled[y * w + x] = true;
            }
        }
        return filled;
    }
    static List<Vector2[]> Boundaries(bool[] filled, RectInt bounds, int scale)
    {
        int w = bounds.width * scale, h = bounds.height * scale, stride = w + 1;
        bool On(int x, int y) => x >= 0 && y >= 0 && x < w && y < h && filled[y * w + x];
        var edges = new Dictionary<int, List<int>>();
        void Edge(int x, int y, int u, int v)
        { int a = y * stride + x, b = v * stride + u; if (!edges.TryGetValue(a, out var next)) edges[a] = next = new List<int>(2); next.Add(b); }
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) if (On(x, y))
        {
            if (!On(x, y - 1)) Edge(x, y, x + 1, y);
            if (!On(x + 1, y)) Edge(x + 1, y, x + 1, y + 1);
            if (!On(x, y + 1)) Edge(x + 1, y + 1, x, y + 1);
            if (!On(x - 1, y)) Edge(x, y + 1, x, y);
        }
        int Dir(int a, int b) => b == a + 1 ? 0 : b == a + stride ? 1 : b == a - 1 ? 2 : 3;
        var loops = new List<Vector2[]>();
        while (edges.Count > 0)
        {
            int start = edges.Keys.Min(), at = start, prior = -1, limit = edges.Sum(e => e.Value.Count) + 1;
            var loop = new List<Vector2>();
            do
            {
                if (--limit < 0 || !edges.TryGetValue(at, out var next)) throw new Exception("Open extracted region boundary");
                loop.Add(new Vector2(bounds.x + (at % stride) / (float)scale, bounds.y + (at / stride) / (float)scale));
                int to = next[0];
                if (next.Count > 1 && prior >= 0)
                {
                    int direction = Dir(prior, at), best = -1;
                    foreach (int n in next) { int turn = (Dir(at, n) - direction + 4) % 4; int score = turn == 1 ? 4 : turn == 0 ? 3 : turn == 3 ? 2 : 1; if (score > best) { best = score; to = n; } }
                }
                next.Remove(to); if (next.Count == 0) edges.Remove(at); prior = at; at = to;
            } while (at != start);
            if (loop.Count >= 4) loops.Add(loop.ToArray());
        }
        return loops;
    }
    static void Simplify(Vector2[] p, int a, int b, SortedSet<int> keep)
    {
        var d = p[b] - p[a]; float far = CurveError * CurveError; int found = -1;
        for (int i = a + 1; i < b; i++) { float t = d.sqrMagnitude > 0 ? Mathf.Clamp01(Vector2.Dot(p[i] - p[a], d) / d.sqrMagnitude) : 0; float e = (p[i] - p[a] - t * d).sqrMagnitude; if (e > far) { far = e; found = i; } }
        if (found >= 0) { keep.Add(found); Simplify(p, a, found, keep); Simplify(p, found, b, keep); }
    }
    static Vector2[] ClosedCurve(Vector2[] ring)
    {
        var p = ring.Concat(new[] { ring[0] }).ToArray(); int split = 1;
        for (int i = 2; i < ring.Length; i++) if ((p[i] - p[0]).sqrMagnitude > (p[split] - p[0]).sqrMagnitude) split = i;
        var keep = new SortedSet<int> { 0, split, ring.Length };
        Simplify(p, 0, split, keep); Simplify(p, split, ring.Length, keep);
        return keep.Where(i => i < ring.Length).Select(i => p[i]).ToArray();
    }
    static List<Vector2> Clip(List<Vector2> p, int axis, float value, bool positive)
    {
        var result = new List<Vector2>(); if (p.Count == 0) return result;
        var a = p[p.Count - 1]; float da = (a[axis] - value) * (positive ? 1 : -1);
        foreach (var b in p)
        {
            float db = (b[axis] - value) * (positive ? 1 : -1);
            if ((da >= 0) != (db >= 0)) result.Add(Vector2.LerpUnclamped(a, b, da / (da - db)));
            if (db >= 0) result.Add(b); a = b; da = db;
        }
        return result;
    }
    static float[] CellAreas(List<Vector2[]> curves, RectInt bounds)
    {
        var areas = new float[bounds.width * bounds.height];
        foreach (var ring in curves)
        {
            if (ring.Length < 3) continue;
            int x0 = Mathf.Max(bounds.x, Mathf.FloorToInt(ring.Min(p => p.x))), x1 = Mathf.Min(bounds.xMax - 1, Mathf.FloorToInt(ring.Max(p => p.x)));
            int y0 = Mathf.Max(bounds.y, Mathf.FloorToInt(ring.Min(p => p.y))), y1 = Mathf.Min(bounds.yMax - 1, Mathf.FloorToInt(ring.Max(p => p.y)));
            for (int y = y0; y <= y1; y++) for (int x = x0; x <= x1; x++)
            {
                var p = Clip(ring.ToList(), 0, x, true); p = Clip(p, 0, x + 1, false); p = Clip(p, 1, y, true); p = Clip(p, 1, y + 1, false);
                if (p.Count >= 3) areas[(y - bounds.y) * bounds.width + x - bounds.x] += Area(p);
            }
        }
        for (int i = 0; i < areas.Length; i++) areas[i] = Mathf.Clamp01(areas[i]); return areas;
    }
    // Exact integral of the closed1/8-cell source-region polygons. The extraction
    // grid already partitions each logical cell into64 equal-area squares. This
    // measures fidelity; it is not a threshold or a selected output mask.
    static float[] SourceCellAreas504(bool[] region, int width, int height)
    {
        int scale = ExtractionScale, stride = width * scale;
        if (region.Length != stride * height * scale) throw new ArgumentException("Source region dimensions differ");
        var count = new int[width * height];
        for (int y = 0; y < height * scale; y++) for (int x = 0; x < stride; x++)
            if (region[y * stride + x]) count[(y / scale) * width + x / scale]++;
        float inverseArea = 1f / (scale * scale);
        return count.Select(n => n * inverseArea).ToArray();
    }
    // Binary s/t cut: source-region area loss + shared boundary length. All cells are
    // selected together. This has no input raster threshold, morphology, per-strand
    // topology constraint, animation history, or coordinate/phase special case.
    public static bool[] SelectRegions(float[] areas, int width, int height)
    {
        var flow = new Cut(areas.Length + 2); int source = areas.Length, sink = source + 1;
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
        {
            int i = y * width + x;
            bool border = x == 0 || y == 0 || x == width - 1 || y == height - 1;
            flow.Add(source, i, areas[i]); flow.Add(i, sink, border ? 100000 : 1 - areas[i]);
            if (x + 1 < width) flow.Link(i, i + 1, BoundaryCost * .58578644f);
            if (y + 1 < height) flow.Link(i, i + width, BoundaryCost * .58578644f);
            if (y + 1 < height && x + 1 < width) flow.Link(i, i + width + 1, BoundaryCost * .29289322f);
            if (y + 1 < height && x > 0) flow.Link(i, i + width - 1, BoundaryCost * .29289322f);
        }
        return flow.Solve(source, sink).Take(areas.Length).ToArray();
    }
    sealed class Cut
    {
        sealed class E { public int to, reverse; public float capacity; }
        readonly List<E>[] graph; readonly int[] level, cursor;
        public Cut(int n) { graph = Enumerable.Range(0, n).Select(_ => new List<E>()).ToArray(); level = new int[n]; cursor = new int[n]; }
        public void Add(int a, int b, float c) { var e = new E { to = b, reverse = graph[b].Count, capacity = c }; var r = new E { to = a, reverse = graph[a].Count }; graph[a].Add(e); graph[b].Add(r); }
        public void Link(int a, int b, float c) { Add(a, b, c); Add(b, a, c); }
        float Send(int at, int sink, float value)
        {
            if (at == sink) return value;
            for (; cursor[at] < graph[at].Count; cursor[at]++)
            {
                var e = graph[at][cursor[at]]; if (e.capacity <= 1e-7f || level[e.to] != level[at] + 1) continue;
                float sent = Send(e.to, sink, Mathf.Min(value, e.capacity)); if (sent <= 1e-7f) continue;
                e.capacity -= sent; graph[e.to][e.reverse].capacity += sent; return sent;
            }
            return 0;
        }
        bool Levels(int source, int sink)
        {
            Array.Fill(level, -1); var q = new Queue<int>(); level[source] = 0; q.Enqueue(source);
            while (q.Count > 0) { int a = q.Dequeue(); foreach (var e in graph[a]) if (e.capacity > 1e-7f && level[e.to] < 0) { level[e.to] = level[a] + 1; q.Enqueue(e.to); } }
            return level[sink] >= 0;
        }
        public bool[] Solve(int source, int sink)
        {
            while (Levels(source, sink)) { Array.Clear(cursor, 0, cursor.Length); while (Send(source, sink, float.PositiveInfinity) > 1e-7f) { } }
            return level.Select(x => x >= 0).ToArray();
        }
    }
    static Packet Select(Full319View335 f, int x, int y)
    {
        var centre = new Vector2(x + .5f, y + .5f); Packet best = null; float error = float.PositiveInfinity;
        foreach (var t in triangles)
        {
            if (centre.x < t.minX - 1.1f || centre.x > t.maxX + 1.1f || centre.y < t.minY - 1.1f || centre.y > t.maxY + 1.1f) continue;
            var b = Bary(centre, t); Vector2 q = centre;
            if (b.x < 0 || b.y < 0 || b.z < 0)
            {
                float e = float.PositiveInfinity; var vs = new[] { t.a, t.b, t.c };
                for (int j = 0; j < 3; j++) { var a = vs[j]; var d = vs[(j + 1) % 3] - a; var p = a + d * (d.sqrMagnitude > 0 ? Mathf.Clamp01(Vector2.Dot(centre - a, d) / d.sqrMagnitude) : 0); if ((p - centre).sqrMagnitude < e) { e = (p - centre).sqrMagnitude; q = p; } }
                b = Bary(q, t); if (b.x < -.001f || b.y < -.001f || b.z < -.001f) continue;
            }
            b = Vector3.Lerp(b, Vector3.one / 3, .00001f); q = t.a * b.x + t.b * b.y + t.c * b.z;
            float distance = (q - centre).sqrMagnitude; if (distance > 1.1f * 1.1f || distance > error + 1e-7f) continue;
            var pWorld = world[t.ia] * b.x + world[t.ib] * b.y + world[t.ic] * b.z;
            float z = -f.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(pWorld).z;
            if (best != null && Mathf.Abs(distance - error) < 1e-7f && z >= best.depth) continue;
            error = distance; best = new Packet { x = x, y = y, submesh = t.sm, primitive = t.primitive, barycentric = b, world = pWorld, uv = uv[t.ia] * b.x + uv[t.ib] * b.y + uv[t.ic] * b.z, projected = q, depth = z, distance = Mathf.Sqrt(distance) };
        }
        return best;
    }
    static void AddQuad(Full319View335 f, Packet p, Piece piece, int[] ix)
    {
        int a = ix[p.primitive * 3], b = ix[p.primitive * 3 + 1], c = ix[p.primitive * 3 + 2]; var weights = p.barycentric;
        var local = vertices[a] * weights.x + vertices[b] * weights.y + vertices[c] * weights.z;
        var normal = (normals[a] * weights.x + normals[b] * weights.y + normals[c] * weights.z).normalized;
        var tangent = tangents.Length == vertices.Length ? tangents[a] * weights.x + tangents[b] * weights.y + tangents[c] * weights.z : new Vector4(1, 0, 0, 1);
        int start = piece.vertices.Count;
        foreach (var corner in new[] { new Vector2(p.x, p.y), new Vector2(p.x + 1, p.y), new Vector2(p.x + 1, p.y + 1), new Vector2(p.x, p.y + 1) })
        {
            var view = inverseProjection * new Vector4(corner.x / 240 - 1, 1 - corner.y / 136, 0, 1); view /= view.w;
            var target = cameraToWorld.MultiplyPoint3x4(new Vector3(view.x, view.y, -p.depth));
            piece.vertices.Add(worldToLocal.MultiplyPoint3x4(target)); piece.normals.Add(normal); piece.tangents.Add(tangent); piece.uv.Add(p.uv);
            piece.primitive.Add(new Vector4(p.primitive, p.x, p.y, 1)); piece.source.Add(new Vector4(local.x, local.y, local.z, 1));
        }
        bool forward = Cross(projected[b] - projected[a], projected[c] - projected[a]) > 0;
        foreach (int i in forward ? new[] { 0, 1, 2, 0, 2, 3 } : new[] { 0, 2, 1, 0, 3, 2 }) piece.indices.Add(start + i);
    }
    public static void Prepare(Full319View335 f)
    {
        if (!Enabled || !HeadLocal367.IsHead(f)) return;
        var watch = System.Diagnostics.Stopwatch.StartNew(); current = null; Packets.Clear(); SourceLoops.Clear(); Curves.Clear(); SelectedLoops.Clear(); Unsupported = 0;
        AreaUncertainCells505 = AreaSelectionAmbiguous505 = 0;
        Array.Clear(Hair, 0, Hair.Length); Array.Clear(Parent, 0, Parent.Length);
        try
        {
            var mf = f.motion.surface.outputs[2]; var mesh = mf.sharedMesh;
            vertices = mesh.vertices; normals = mesh.normals; tangents = mesh.tangents; uv = mesh.uv;
            world = vertices.Select(mf.transform.TransformPoint).ToArray(); projected = world.Select(f.Project).ToArray();
            var indices = Enumerable.Range(0, mesh.subMeshCount).Select(sm => mesh.GetIndices(sm)).ToArray();
            var union = Union(projected, indices, out var bounds); SourceLoops.AddRange(Boundaries(union, bounds, ExtractionScale));
            Curves.AddRange(SourceLoops.Select(ClosedCurve).Where(p => p.Length >= 3));
            bool[] selected;
            if (UseVisibleArea505)
            {
                var area = HeadArea505.Build(f, bounds);
                selected = SelectRegions(area.lower, bounds.width, bounds.height);
                AreaUncertainCells505 = area.lower.Zip(area.upper, (a, b) => b - a > 1e-7f).Count(x => x);
                if (AreaUncertainCells505 != 0)
                {
                    var upper = SelectRegions(area.upper, bounds.width, bounds.height);
                    AreaSelectionAmbiguous505 = selected.Zip(upper, (a, b) => a != b).Count(x => x);
                    if (AreaSelectionAmbiguous505 != 0)
                        throw new InvalidOperationException("505 alpha-area bounds leave " + AreaSelectionAmbiguous505 + " region cells undecided");
                }
            }
            else
            {
                var areas = SourceCellAreas504(union, bounds.width, bounds.height);
                selected = SelectRegions(areas, bounds.width, bounds.height);
            }
            SelectedLoops.AddRange(Boundaries(selected, bounds, 1));
            for (int y = 0; y < bounds.height; y++) for (int x = 0; x < bounds.width; x++) if (selected[y * bounds.width + x]) Hair[(y + bounds.y) * 480 + x + bounds.x] = true;
            triangles.Clear();
            for (int sm = 0; sm < indices.Length; sm++) for (int k = 0; k < indices[sm].Length; k += 3)
            {
                int a = indices[sm][k], b = indices[sm][k + 1], c = indices[sm][k + 2]; var pa = projected[a]; var pb = projected[b]; var pc = projected[c];
                if (Mathf.Abs(Cross(pb - pa, pc - pa)) < 1e-10f) continue;
                triangles.Add(new Triangle { sm = sm, primitive = k / 3, ia = a, ib = b, ic = c, a = pa, b = pb, c = pc, minX = Mathf.Min(pa.x, Mathf.Min(pb.x, pc.x)), maxX = Mathf.Max(pa.x, Mathf.Max(pb.x, pc.x)), minY = Mathf.Min(pa.y, Mathf.Min(pb.y, pc.y)), maxY = Mathf.Max(pa.y, Mathf.Max(pb.y, pc.y)) });
            }
            if (pieces == null) { pieces = new Piece[4, 3]; for (int s = 0; s < 4; s++) for (int part = 0; part < 3; part++) pieces[s, part] = new Piece("502 owned closed-region cells " + s + "/" + part); }
            foreach (var piece in pieces) piece.Clear();
            inverseProjection = f.effectiveProjection.inverse; cameraToWorld = f.motion.camera.cameraToWorldMatrix; worldToLocal = mf.transform.worldToLocalMatrix;
            for (int y = bounds.y; y < bounds.yMax; y++) for (int x = bounds.x; x < bounds.xMax; x++) if (Hair[y * 480 + x])
            {
                var p = Select(f, x, y); if (p == null) { Unsupported++; continue; }
                Packets.Add(p); AddQuad(f, p, pieces[p.submesh, 0], indices[p.submesh]);
                int part = p.submesh == 0 && p.primitive >= 574 && p.primitive <= 857 ? 1 : 2;
                AddQuad(f, p, pieces[p.submesh, part], indices[p.submesh]);
            }
            if (Unsupported != 0) throw new Exception("Designed region has " + Unsupported + " cells without a bounded original triangle donor");
            foreach (var piece in pieces) piece.Upload(mesh.bounds);
            // The protected face/feature domain is the existing source union, not
            // a box/hull or a new eye design. Hair is the only redesigned family.
            Array.Copy(Hair, Parent, Hair.Length);
            var face = f.motion.surface.outputs[1]; var fm = face.sharedMesh;
            var fp = fm.vertices.Select(v => f.Project(face.transform.TransformPoint(v))).ToArray();
            var fi = Enumerable.Range(0, fm.subMeshCount).Select(sm => fm.GetIndices(sm)).ToArray();
            foreach (var ix in fi) for (int k = 0; k < ix.Length; k += 3)
            {
                var a = fp[ix[k]]; var b = fp[ix[k + 1]]; var c = fp[ix[k + 2]];
                var t = new Triangle { a = a, b = b, c = c };
                int x0 = Mathf.Max(0, Mathf.FloorToInt(Mathf.Min(a.x, Mathf.Min(b.x, c.x)))), x1 = Mathf.Min(479, Mathf.FloorToInt(Mathf.Max(a.x, Mathf.Max(b.x, c.x))));
                int y0 = Mathf.Max(0, Mathf.FloorToInt(Mathf.Min(a.y, Mathf.Min(b.y, c.y)))), y1 = Mathf.Min(271, Mathf.FloorToInt(Mathf.Max(a.y, Mathf.Max(b.y, c.y))));
                for (int y = y0; y <= y1; y++) for (int x = x0; x <= x1; x++) { var weights = Bary(new Vector2(x + .5f, y + .5f), t); if (weights.x >= 0 && weights.y >= 0 && weights.z >= 0) Parent[y * 480 + x] = true; }
            }
            if (!mask) mask = new Texture2D(480, 272, TextureFormat.RGBAFloat, false, true) { name = "502 canonical parent/hair ownership", filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.DontSave };
            var colours = new Color[Hair.Length]; for (int y = 0; y < 272; y++) for (int x = 0; x < 480; x++) { int i = y * 480 + x; colours[(271 - y) * 480 + x] = new Color(Parent[i] ? 1 : 0, Hair[i] ? 1 : 0, 0, 0); }
            mask.SetPixels(colours); mask.Apply(false, false); current = f; Status = "ready";
        }
        catch (Exception e) { Status = "unsupported: " + e.Message; }
        finally { watch.Stop(); BuildMilliseconds = watch.Elapsed.TotalMilliseconds; }
    }
    public static bool Ready => Enabled && current && Status == "ready";
    public static Texture2D Mask => mask;
    public static bool Draw(RasterCommandBuffer cmd, Full319View335 f, int renderer, int sm, Mesh original, Matrix4x4 matrix, Material material, int kind, int part = 0, float rasterScale = 1)
    {
        if (!Ready || current != f || renderer == 0) return false;
        var key = (material, kind);
        if (!materials.TryGetValue(key, out var owned) || !owned)
        {
            var shader = Shader.Find("EValidation/HeadRegion502" + ShaderNames[kind]); if (!shader) throw new Exception("502 shader missing: " + ShaderNames[kind]);
            owned = new Material(material) { shader = shader, hideFlags = HideFlags.DontSave }; owned.shaderKeywords = material.shaderKeywords; materials[key] = owned;
        }
        owned.SetTexture("_Region502Mask", mask); cmd.SetGlobalMatrix("_Region502ViewProjection", current.effectiveProjection * current.motion.camera.worldToCameraMatrix);
        cmd.SetGlobalFloat("_Region502Scale", kind == 1 || kind == 2 ? 2 : rasterScale);
        cmd.SetGlobalVector("_Region502OwnedShift", current.motion.clipShift);
        cmd.SetGlobalInt("_Region502Quad", renderer == 2 ? 1 : 0); cmd.SetGlobalInt("_Region502Hair", renderer == 2 ? 1 : 0);
        if (renderer == 2) cmd.DrawMesh(pieces[sm, part].mesh, matrix, owned, 0, 0); else cmd.DrawMesh(original, matrix, owned, sm, 0);
        return true;
    }
    public static void Gate(CommandBuffer cmd, Full319View335 f)
    {
        if (!Ready) return;
        if (!gate) gate = UnityEngine.Resources.Load<ComputeShader>("HeadRegion502");
        if (!gate) throw new Exception("502 authority gate missing");
        int k = gate.FindKernel("Gate"); var host = HeadLocal367.Active;
        bool local = current == f; if (!local && (!host || f != host.main)) return;
        cmd.SetComputeTextureParam(gate, k, "_Mask", mask);
        cmd.SetComputeIntParams(gate, "_Offset", local ? 0 : host.offset.x, local ? 0 : host.offset.y);
        void T(string name, RTHandle t) => cmd.SetComputeTextureParam(gate, k, name, t.rt);
        T("_Before", f.before); T("_Colour", f.colour); T("_Owner", f.owner); T("_Meta", f.preparedMeta); T("_UV", f.preparedUV);
        cmd.DispatchCompute(gate, k, 60, 34, 1);
    }
    public static void Release()
    {
        Enabled = false; UseVisibleArea505 = false; HeadArea505.Release(); current = null; Status = "disabled";
        if (pieces != null) foreach (var piece in pieces) if (piece.mesh) UnityEngine.Object.DestroyImmediate(piece.mesh); pieces = null;
        foreach (var material in materials.Values) if (material) UnityEngine.Object.DestroyImmediate(material); materials.Clear();
        if (mask) UnityEngine.Object.DestroyImmediate(mask); mask = null; gate = null; Packets.Clear();
    }
}
