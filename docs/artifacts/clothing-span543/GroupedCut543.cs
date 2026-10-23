using System;
using System.Linq;
using System.Collections.Generic;
public static class GroupedCut543
{
 const float BoundaryCost=.14f;
    public static bool[] Select(float[] areas, int width, int height, List<int[]> groups)
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
        foreach(var group in groups)for(int j=1;j<group.Length;j++)flow.Link(group[0],group[j],100000);
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
}
