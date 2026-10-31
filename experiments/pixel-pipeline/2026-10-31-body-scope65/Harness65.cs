// Compiles with the extracted candidate fragment and exact BeginProbe method.
// These are instrumented CPU fakes, not Unity/GPU runtime classes.
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace UnityEngine
{
    class Mesh { }
    class Transform { }
    class ComputeBuffer
    {
        public static int Created, Released;
        public static bool FailAllocate, FailUpload;
        public bool Dead;
        public float[] Data;
        public ComputeBuffer(int length, int stride)
        {
            if (FailAllocate) { FailAllocate = false; throw new InvalidOperationException("allocate"); }
            if (length <= 0 || stride != 4) throw new ArgumentException();
            Created++;
        }
        public void SetData(float[] data)
        {
            if (FailUpload) { FailUpload = false; throw new InvalidOperationException("upload"); }
            if (Dead) throw new ObjectDisposedException("buffer");
            Data = (float[])data.Clone();
        }
        public void Release()
        {
            if (Dead) throw new InvalidOperationException("double release");
            Dead = true; Released++;
        }
    }
    class Material
    {
        public ComputeBuffer Binding;
        public void SetBuffer(string name, ComputeBuffer buffer)
        {
            if (name != "_BodyScope551" || buffer.Dead) throw new InvalidOperationException("bad binding");
            Binding = buffer;
        }
        public static implicit operator bool(Material m) { return !ReferenceEquals(m, null); }
    }
}
namespace UnityEngine.Rendering
{
    class RasterCommandBuffer
    {
        public readonly Dictionary<string, int> Ints = new Dictionary<string, int>();
        public readonly object UnknownGlobalBuffer = new object();
        public void SetGlobalInt(string name, int value) { Ints[name] = value; }
        public void SetGlobalBuffer(string name, ComputeBuffer buffer)
        { throw new InvalidOperationException("global buffer overwrite forbidden"); }
    }
}
class Motion { public Material[] materials = new[] { new Material(), new Material(), new Material() }; }
class Full319View335 { public Motion motion = new Motion(); }

static class ClothRegion524
{
    static Full319View335 current;
    static bool UseBodyScope551, ready;
    static int PartBits540;
    static bool Active540(int sm) { return (PartBits540 & (1 << sm)) != 0; }
    static bool Ready(Full319View335 f) { return ready && current == f; }
    // CANDIDATE_OWNER
    // CANDIDATE_BEGIN_PROBE

    static int cases;
    static void Check(bool condition, string label)
    { if (!condition) throw new Exception(label); }
    static void ExpectFailure(Action action, string label)
    {
        try { action(); } catch (ArgumentException) { return; } catch (InvalidOperationException) { return; }
        throw new Exception("missing failure: " + label);
    }
    static void Case(string label, Action test)
    {
        ReleaseAllScopes551(); current = null; ready = false; UseBodyScope551 = false;
        PartBits540 = 0; ComputeBuffer.FailAllocate = ComputeBuffer.FailUpload = false;
        int c = ComputeBuffer.Created, r = ComputeBuffer.Released;
        test();
        ReleaseAllScopes551();
        Check(ComputeBuffer.Created - c == ComputeBuffer.Released - r, label + " leaked fake resource");
        cases++; Console.WriteLine("PASS " + label);
    }
    static void Commit(BodyScopeResources551 o, Mesh mesh, Transform head, bool flip)
    {
        o.Commit(mesh, head, new[] { !flip, flip, true },
                 new[] { flip ? 0f : 1f, flip ? 1f : 0f, 1f }, 2);
    }
    static int Main()
    {
        try
        {
            Case("lazy_create_repeated_acquire", delegate {
                var f = new Full319View335(); int n = ComputeBuffer.Created;
                var o = ScopeOwner551(f);
                Check(n == ComputeBuffer.Created && scopes551.Count == 1, "owner lookup allocated GPU");
                var a = ScopeBuffer551(f);
                Check(ReferenceEquals(a, ScopeBuffer551(f)) && a.Data[0] == 1f, "duplicate dummy");
                Check(ComputeBuffer.Created == n + 1, "unexpected create count");
            });
            Case("two_renderer_instances_isolated", delegate {
                var a = new Full319View335(); var b = new Full319View335();
                var x = ScopeBuffer551(a); var y = ScopeBuffer551(b);
                Check(!ReferenceEquals(x, y), "shared native resource");
                ReleaseScope551(a); Check(x.Dead && !y.Dead, "foreign owner released");
                Check(ReferenceEquals(y, ScopeBuffer551(b)), "survivor changed");
            });
            Case("transaction_success_cpu_gpu_pair", delegate {
                var f = new Full319View335(); var o = ScopeOwner551(f); var old = o.Buffer();
                var mesh = new Mesh(); var head = new Transform(); Commit(o, mesh, head, false);
                selectedScope551 = o; UseBodyScope551 = true;
                Check(old.Dead && o.Count == 2 && o.Mesh == mesh && o.Head == head, "commit");
                for (int i = 0; i < 3; i++) Check(InScope551(0, i) == (o.Buffer().Data[i] > .5f), "CPU/GPU eligibility");
                Check(!InScope551(0, -1) && !InScope551(0, 3) && InScope551(1, 999), "scope bounds");
            });
            Case("allocation_failure_keeps_previous", delegate {
                var o = ScopeOwner551(new Full319View335()); var m = new Mesh(); var h = new Transform();
                Commit(o, m, h, false); var old = o.Buffer(); var included = o.Included;
                ComputeBuffer.FailAllocate = true;
                ExpectFailure(delegate { Commit(o, new Mesh(), new Transform(), true); }, "allocate");
                Check(o.Buffer() == old && !old.Dead && o.Included == included && o.Mesh == m && o.Head == h, "lost committed pair");
            });
            Case("upload_failure_releases_only_candidate", delegate {
                var o = ScopeOwner551(new Full319View335()); Commit(o, new Mesh(), new Transform(), false);
                var old = o.Buffer(); var mask = o.Included; int r = ComputeBuffer.Released;
                ComputeBuffer.FailUpload = true;
                ExpectFailure(delegate { Commit(o, new Mesh(), new Transform(), true); }, "upload");
                Check(o.Buffer() == old && !old.Dead && o.Included == mask && ComputeBuffer.Released == r + 1, "transaction not atomic");
            });
            Case("first_upload_failure_retry", delegate {
                var f = new Full319View335(); int r = ComputeBuffer.Released;
                ComputeBuffer.FailUpload = true; ExpectFailure(delegate { ScopeBuffer551(f); }, "first upload");
                Check(ComputeBuffer.Released == r + 1, "failed dummy leaked");
                Check(ScopeBuffer551(f).Data[0] == 1, "retry");
            });
            Case("invalid_mask_no_allocation", delegate {
                var o = ScopeOwner551(new Full319View335()); int n = ComputeBuffer.Created;
                ExpectFailure(delegate { o.Commit(new Mesh(), new Transform(), new bool[0], new float[0], 0); }, "empty");
                ExpectFailure(delegate { o.Commit(new Mesh(), new Transform(), new bool[1], new float[2], 0); }, "length");
                Check(ComputeBuffer.Created == n && o.Included == null, "invalid mask changed owner");
            });
            Case("cancel_after_partial_initialization", delegate {
                var f = new Full319View335(); ComputeBuffer buffer = null;
                try { buffer = ScopeBuffer551(f); throw new OperationCanceledException(); }
                catch (OperationCanceledException) { }
                finally { ReleaseScope551(f); }
                Check(buffer.Dead && scopes551.Count == 0, "cancel leaked");
            });
            Case("exception_before_ready_cleanup_hook", delegate {
                var f = new Full319View335(); var b = ScopeBuffer551(f); ready = false;
                // Same ordering as patched Full319View335.OnDisable: release before !ready return.
                ReleaseScope551(f); if (ready) throw new Exception("fixture");
                Check(b.Dead && scopes551.Count == 0, "incomplete init leaked");
            });
            Case("disable_repeated_and_reenter", delegate {
                var f = new Full319View335(); var a = ScopeBuffer551(f); ReleaseScope551(f); ReleaseScope551(f);
                var b = ScopeBuffer551(f); Check(a.Dead && !b.Dead && a != b, "reentry generation");
                ReleaseAllScopes551(); ReleaseScope551(f); ReleaseAllScopes551();
            });
            Case("release_one_preserves_other_cpu_selection", delegate {
                var a = new Full319View335(); var b = new Full319View335();
                ScopeBuffer551(a); var o = ScopeOwner551(b); Commit(o, new Mesh(), new Transform(), false);
                selectedScope551 = o; current = b; ReleaseScope551(a);
                Check(selectedScope551 == o && current == b && ScopeIncluded551 == 2, "other selection cleared");
                ReleaseScope551(b); Check(selectedScope551 == null && current == null, "selection retained");
            });
            Case("exact_BeginProbe_local_binding_global_untouched", delegate {
                var a = new Full319View335(); var b = new Full319View335(); var cmd = new RasterCommandBuffer();
                var unknown = cmd.UnknownGlobalBuffer; current = a; ready = UseBodyScope551 = true; PartBits540 = 1;
                BeginProbe(cmd, a); var ab = ScopeBuffer551(a);
                foreach (var material in a.motion.materials) Check(material.Binding == ab, "missed owned material");
                Check(cmd.Ints["_BodyScope551Enabled"] == 1, "enabled semantics changed");
                BeginProbe(cmd, b); var bb = ScopeBuffer551(b);
                foreach (var material in b.motion.materials) Check(material.Binding == bb, "wrong renderer");
                foreach (var material in a.motion.materials) Check(material.Binding == ab, "foreign material changed");
                Check(cmd.Ints["_BodyScope551Enabled"] == 0 && ReferenceEquals(unknown, cmd.UnknownGlobalBuffer), "global state");
            });
            Case("global_release_idempotent_owned_only", delegate {
                var f = new Full319View335(); var owned = ScopeBuffer551(f);
                var borrowed = new ComputeBuffer(1, 4); borrowed.SetData(new[] { 1f });
                ReleaseAllScopes551(); ReleaseAllScopes551();
                Check(owned.Dead && !borrowed.Dead, "released borrowed resource"); borrowed.Release();
            });
            Console.WriteLine("CASES " + cases + " CREATED " + ComputeBuffer.Created + " RELEASED " + ComputeBuffer.Released);
            return 0;
        }
        catch (Exception e) { Console.Error.WriteLine(e); return 1; }
    }
}
