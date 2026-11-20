using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// Scale-compensated mesh baking with zero-shrinkage Taubin low-pass clothing smoothing
// (applied only to baked clothing submeshes 1..N at runtime; never mutates source assets)
// and cached local-space pose buffers for stepped pixel-art cadence with smooth 60+ FPS movement.
[ExecuteAlways, DefaultExecutionOrder(-200)]
public sealed class ScaleBake378 : MonoBehaviour
{
    public HeadLocal367 host;
    public CurrentSurface330 original;

    Mesh[] meshes;
    bool ready, oldEnabled;
    bool[] priorSourceEnabled;
    Action previous, hook;

    List<Vector3>[] localVertsBuf, localNormsBuf, outVertsBuf, outNormsBuf;
    List<Vector4>[] localTangentsBuf, outTangentsBuf;
    bool[] hasLocalCache;
    int lastEvaluatedFrame = -1;
    int lastSmoothConfigHash = -1;

    // Precomputed static topology for zero-shrinkage Taubin clothing smoothing on source[0] submeshes 1..N.
    const byte KindPinned = 0, KindInterior = 1, KindBoundaryCurve = 2;
    bool clothSmootherReady;
    int clothCanonCount;
    int[] vertToCanon;
    int[] clothVertIndices;
    byte[] canonKind;
    int[] nbrStart, nbrCount, nbrFlat;
    int[] bndA, bndB;
    Vector3[] canonOrig, canonPos, canonTmp;

    void OnEnable() => Initialise();

    public void Initialise()
    {
        if (ready || !host || !original || original.source == null) return;
        oldEnabled = original.enabled;
        original.enabled = false;
        priorSourceEnabled = original.source.Select(s => s.enabled).ToArray();
        meshes = original.source.Select((s, i) => new Mesh
        {
            name = "378 scale-compensated current surface " + i,
            hideFlags = HideFlags.DontSave
        }).ToArray();

        int n = meshes.Length;
        localVertsBuf = new List<Vector3>[n];
        localNormsBuf = new List<Vector3>[n];
        localTangentsBuf = new List<Vector4>[n];
        outVertsBuf = new List<Vector3>[n];
        outNormsBuf = new List<Vector3>[n];
        outTangentsBuf = new List<Vector4>[n];
        hasLocalCache = new bool[n];
        for (int i = 0; i < n; i++)
        {
            localVertsBuf[i] = new List<Vector3>();
            localNormsBuf[i] = new List<Vector3>();
            localTangentsBuf[i] = new List<Vector4>();
            outVertsBuf[i] = new List<Vector3>();
            outNormsBuf[i] = new List<Vector3>();
            outTangentsBuf[i] = new List<Vector4>();
        }

        if (n > 0 && original.source[0] && original.source[0].sharedMesh)
            BuildClothSmoother(original.source[0].sharedMesh);

        foreach (var s in original.source) s.enabled = false;
        previous = host.afterPose;
        hook = AfterPose;
        host.afterPose = hook;
        ready = true;
        Evaluate(true, true);
    }

    void BuildClothSmoother(Mesh sourceMesh)
    {
        clothSmootherReady = false;
        if (!sourceMesh || sourceMesh.subMeshCount < 2) return;
        var restVerts = sourceMesh.vertices;
        int vertCount = restVerts.Length;
        if (vertCount == 0) return;

        var bodyMask = new bool[vertCount];
        var clothMask = new bool[vertCount];
        var sm0 = sourceMesh.GetIndices(0);
        for (int i = 0; i < sm0.Length; i++) bodyMask[sm0[i]] = true;

        var clothSubIndices = new int[sourceMesh.subMeshCount - 1][];
        for (int sm = 1; sm < sourceMesh.subMeshCount; sm++)
        {
            var idx = sourceMesh.GetIndices(sm);
            clothSubIndices[sm - 1] = idx;
            for (int i = 0; i < idx.Length; i++) clothMask[idx[i]] = true;
        }

        // Weld coincident rest-pose coordinates into canonical spatial IDs so UV seams never crack.
        var posToCanon = new Dictionary<(int, int, int), int>(vertCount);
        vertToCanon = new int[vertCount];
        var canonIsBody = new List<bool>(vertCount);
        var canonIsCloth = new List<bool>(vertCount);
        var clothVertList = new List<int>(vertCount);

        for (int v = 0; v < vertCount; v++)
        {
            var p = restVerts[v];
            var key = (Mathf.RoundToInt(p.x * 10000f), Mathf.RoundToInt(p.y * 10000f), Mathf.RoundToInt(p.z * 10000f));
            if (!posToCanon.TryGetValue(key, out int cid))
            {
                cid = canonIsBody.Count;
                posToCanon.Add(key, cid);
                canonIsBody.Add(false);
                canonIsCloth.Add(false);
            }
            vertToCanon[v] = cid;
            if (bodyMask[v]) canonIsBody[cid] = true;
            if (clothMask[v])
            {
                canonIsCloth[cid] = true;
                clothVertList.Add(v);
            }
        }

        clothCanonCount = canonIsBody.Count;
        if (clothVertList.Count == 0 || clothCanonCount == 0) return;
        clothVertIndices = clothVertList.ToArray();

        // Build undirected canonical edge multiplicity and adjacency across clothing submeshes.
        var edgeCounts = new Dictionary<long, int>(clothVertList.Count * 3);
        var adjSets = new HashSet<int>[clothCanonCount];
        void AddEdge(int a, int b)
        {
            if (a == b) return;
            int lo = a < b ? a : b;
            int hi = a < b ? b : a;
            long key = ((long)lo << 32) | (uint)hi;
            edgeCounts.TryGetValue(key, out int c);
            edgeCounts[key] = c + 1;
            if (adjSets[a] == null) adjSets[a] = new HashSet<int>();
            if (adjSets[b] == null) adjSets[b] = new HashSet<int>();
            adjSets[a].Add(b);
            adjSets[b].Add(a);
        }

        for (int s = 0; s < clothSubIndices.Length; s++)
        {
            var idx = clothSubIndices[s];
            for (int t = 0; t + 2 < idx.Length; t += 3)
            {
                int a = vertToCanon[idx[t]];
                int b = vertToCanon[idx[t + 1]];
                int c = vertToCanon[idx[t + 2]];
                AddEdge(a, b);
                AddEdge(b, c);
                AddEdge(c, a);
            }
        }

        // Identify open hem/cuff/collar boundary edges (edge shared by only 1 triangle).
        var bndNeighbors = new List<int>[clothCanonCount];
        foreach (var kv in edgeCounts)
        {
            if (kv.Value != 1) continue;
            int a = (int)(kv.Key >> 32);
            int b = (int)(kv.Key & 0xFFFFFFFFL);
            if (bndNeighbors[a] == null) bndNeighbors[a] = new List<int>(2);
            if (bndNeighbors[b] == null) bndNeighbors[b] = new List<int>(2);
            bndNeighbors[a].Add(b);
            bndNeighbors[b].Add(a);
        }

        canonKind = new byte[clothCanonCount];
        nbrStart = new int[clothCanonCount];
        nbrCount = new int[clothCanonCount];
        bndA = new int[clothCanonCount];
        bndB = new int[clothCanonCount];
        var flatNbrs = new List<int>(clothCanonCount * 6);

        for (int c = 0; c < clothCanonCount; c++)
        {
            nbrStart[c] = flatNbrs.Count;
            if (!canonIsCloth[c] || canonIsBody[c] || adjSets[c] == null || adjSets[c].Count == 0)
            {
                canonKind[c] = KindPinned;
                continue;
            }
            var bn = bndNeighbors[c];
            if (bn == null || bn.Count == 0)
            {
                canonKind[c] = KindInterior;
                foreach (int nb in adjSets[c]) flatNbrs.Add(nb);
                nbrCount[c] = flatNbrs.Count - nbrStart[c];
            }
            else if (bn.Count == 2)
            {
                canonKind[c] = KindBoundaryCurve;
                bndA[c] = bn[0];
                bndB[c] = bn[1];
            }
            else
            {
                // Sharp junction or corner: pin to preserve garment attachment & crisp lapel tips.
                canonKind[c] = KindPinned;
            }
        }

        nbrFlat = flatNbrs.ToArray();
        canonOrig = new Vector3[clothCanonCount];
        canonPos = new Vector3[clothCanonCount];
        canonTmp = new Vector3[clothCanonCount];
        clothSmootherReady = true;
    }

    void SmoothClothVerticesInPlace(List<Vector3> localVerts)
    {
        if (!clothSmootherReady || !PixelRenderPipelineControl399.EnableClothMeshSmoothing) return;
        float strength = PixelRenderPipelineControl399.ClothSmoothStrength;
        int iterations = PixelRenderPipelineControl399.ClothSmoothIterations;
        if (strength <= 0.001f || iterations <= 0 || localVerts.Count != vertToCanon.Length) return;

        // Populate canonical positions from current baked pose.
        for (int i = 0; i < clothVertIndices.Length; i++)
        {
            int v = clothVertIndices[i];
            int c = vertToCanon[v];
            var p = localVerts[v];
            canonOrig[c] = p;
            canonPos[c] = p;
        }

        // Gabriel Taubin (SIGGRAPH 1995) zero-shrinkage surface low-pass filter:
        // lambda = +0.50, mu = -0.53 attenuates high-frequency cloth wrinkles while preserving volume.
        const float lambda = 0.50f;
        const float mu = -0.53f;
        const float bndLambda = 0.40f;
        const float bndMu = -0.42f;

        for (int iter = 0; iter < iterations; iter++)
        {
            // Step 1: +lambda shrink pass (canonPos -> canonTmp)
            for (int c = 0; c < clothCanonCount; c++)
            {
                byte kind = canonKind[c];
                if (kind == KindInterior)
                {
                    int start = nbrStart[c];
                    int count = nbrCount[c];
                    Vector3 sum = Vector3.zero;
                    for (int k = 0; k < count; k++) sum += canonPos[nbrFlat[start + k]];
                    Vector3 avg = sum / count;
                    canonTmp[c] = canonPos[c] + lambda * (avg - canonPos[c]);
                }
                else if (kind == KindBoundaryCurve)
                {
                    Vector3 avg = 0.5f * (canonPos[bndA[c]] + canonPos[bndB[c]]);
                    canonTmp[c] = canonPos[c] + bndLambda * (avg - canonPos[c]);
                }
                else
                {
                    canonTmp[c] = canonPos[c];
                }
            }

            // Step 2: mu inflate pass (canonTmp -> canonPos)
            for (int c = 0; c < clothCanonCount; c++)
            {
                byte kind = canonKind[c];
                if (kind == KindInterior)
                {
                    int start = nbrStart[c];
                    int count = nbrCount[c];
                    Vector3 sum = Vector3.zero;
                    for (int k = 0; k < count; k++) sum += canonTmp[nbrFlat[start + k]];
                    Vector3 avg = sum / count;
                    canonPos[c] = canonTmp[c] + mu * (avg - canonTmp[c]);
                }
                else if (kind == KindBoundaryCurve)
                {
                    Vector3 avg = 0.5f * (canonTmp[bndA[c]] + canonTmp[bndB[c]]);
                    canonPos[c] = canonTmp[c] + bndMu * (avg - canonTmp[c]);
                }
                else
                {
                    canonPos[c] = canonTmp[c];
                }
            }
        }

        // Write blended smooth positions back to all cloth vertices (shared canonical IDs keep UV seams airtight).
        for (int i = 0; i < clothVertIndices.Length; i++)
        {
            int v = clothVertIndices[i];
            int c = vertToCanon[v];
            if (canonKind[c] == KindPinned) continue;
            localVerts[v] = Vector3.LerpUnclamped(canonOrig[c], canonPos[c], strength);
        }
    }

    int CurrentSmoothConfigHash()
    {
        unchecked
        {
            int h = PixelRenderPipelineControl399.EnableClothMeshSmoothing ? 1 : 0;
            h = h * 31 + PixelRenderPipelineControl399.ClothSmoothIterations;
            h = h * 31 + Mathf.RoundToInt(PixelRenderPipelineControl399.ClothSmoothStrength * 100f);
            h = h * 31 + (PixelRenderPipelineControl399.ClothSmoothKeepOriginalNormals ? 1 : 0);
            return h;
        }
    }

    void AfterPose()
    {
        previous?.Invoke();
        Evaluate(false, true);
    }

    public void Evaluate() => Evaluate(false, true);
    public void Evaluate(bool force) => Evaluate(force, true);

    public void Evaluate(bool force, bool rebakePose)
    {
        if (!ready) return;
        int smoothHash = CurrentSmoothConfigHash();
        if (smoothHash != lastSmoothConfigHash)
        {
            lastSmoothConfigHash = smoothHash;
            rebakePose = true;
            force = true;
        }
        if (!force && Application.isPlaying && lastEvaluatedFrame == Time.frameCount) return;
        lastEvaluatedFrame = Time.frameCount;

        for (int i = 0; i < meshes.Length; i++)
        {
            var src = original.source[i];
            var m = meshes[i];
            var lvb = localVertsBuf[i];
            var lnb = localNormsBuf[i];
            var ltb = localTangentsBuf[i];

            if (rebakePose || !hasLocalCache[i])
            {
                src.BakeMesh(m, true);
                m.GetVertices(lvb);
                if (i == 0 && PixelRenderPipelineControl399.EnableClothMeshSmoothing)
                {
                    SmoothClothVerticesInPlace(lvb);
                    if (!PixelRenderPipelineControl399.ClothSmoothKeepOriginalNormals)
                    {
                        m.SetVertices(lvb);
                        m.RecalculateNormals();
                    }
                }
                m.GetNormals(lnb);
                m.GetTangents(ltb);
                hasLocalCache[i] = true;
            }

            // Always transform cached local pose into current world/output transform so movement stays 60+ FPS smooth.
            var matrix = original.outputs[i].transform.worldToLocalMatrix * src.localToWorldMatrix;
            var normal = matrix.inverse.transpose;
            var ovb = outVertsBuf[i];
            var onb = outNormsBuf[i];
            var otb = outTangentsBuf[i];

            ovb.Clear();
            if (ovb.Capacity < lvb.Count) ovb.Capacity = lvb.Count;
            for (int v = 0; v < lvb.Count; v++) ovb.Add(matrix.MultiplyPoint3x4(lvb[v]));
            m.SetVertices(ovb);

            onb.Clear();
            if (onb.Capacity < lnb.Count) onb.Capacity = lnb.Count;
            for (int v = 0; v < lnb.Count; v++) onb.Add(normal.MultiplyVector(lnb[v]).normalized);
            m.SetNormals(onb);

            otb.Clear();
            if (otb.Capacity < ltb.Count) otb.Capacity = ltb.Count;
            for (int v = 0; v < ltb.Count; v++)
            {
                var t = ltb[v];
                var p = matrix.MultiplyVector(new Vector3(t.x, t.y, t.z));
                otb.Add(new Vector4(p.x, p.y, p.z, t.w));
            }
            m.SetTangents(otb);

            m.RecalculateBounds();
            original.outputs[i].sharedMesh = m;
        }
    }

    void OnDisable()
    {
        if (!ready) return;
        if (host && host.afterPose == hook) host.afterPose = previous;
        for (int i = 0; i < meshes.Length; i++)
        {
            if (original && original.outputs[i] && original.outputs[i].sharedMesh == meshes[i])
                original.outputs[i].sharedMesh = null;
            if (meshes[i]) DestroyImmediate(meshes[i]);
        }
        if (original)
        {
            for (int i = 0; i < original.source.Length; i++)
                if (original.source[i]) original.source[i].enabled = priorSourceEnabled[i];
            original.enabled = oldEnabled;
        }
        clothSmootherReady = false;
        lastEvaluatedFrame = -1;
        ready = false;
    }
}
