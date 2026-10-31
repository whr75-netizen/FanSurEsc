    // 65: one owner per Full319View335. No global buffer setter/getter or borrowed buffer.
    sealed class BodyScopeResources551 : IDisposable
    {
        public Mesh Mesh { get; private set; }
        public Transform Head { get; private set; }
        public bool[] Included { get; private set; }
        public int Count { get; private set; }
        ComputeBuffer buffer;

        static ComputeBuffer Upload(float[] data)
        {
            ComputeBuffer candidate = null;
            try
            {
                candidate = new ComputeBuffer(data.Length, sizeof(float));
                candidate.SetData(data);
                return candidate;
            }
            catch
            {
                if (candidate != null) candidate.Release();
                throw;
            }
        }

        public ComputeBuffer Buffer()
        {
            // Even disabled kernels need a valid binding. Allocate only on first use.
            if (buffer == null) buffer = Upload(new[] { 1f });
            return buffer;
        }

        public void Commit(Mesh mesh, Transform head, bool[] included, float[] data, int count)
        {
            if (included == null || data == null || data.Length == 0 || included.Length != data.Length)
                throw new ArgumentException("551 scope mask/buffer length mismatch");
            // A failed allocation/upload must keep the previous CPU/GPU pair intact.
            var candidate = Upload(data);
            var previous = buffer;
            buffer = candidate;
            Mesh = mesh; Head = head; Included = included; Count = count;
            if (previous != null) previous.Release();
        }

        public void Dispose()
        {
            var previous = buffer;
            buffer = null;
            Mesh = null; Head = null; Included = null; Count = 0;
            if (previous != null) previous.Release();
        }
    }

    static readonly Dictionary<Full319View335, BodyScopeResources551> scopes551 = new Dictionary<Full319View335, BodyScopeResources551>();
    static BodyScopeResources551 selectedScope551;
    static bool[] included551 { get { return selectedScope551 == null ? null : selectedScope551.Included; } }
    public static int ScopeIncluded551 { get { return selectedScope551 == null ? 0 : selectedScope551.Count; } }
    public static bool InScope551(int sm,int primitive)
    { return !UseBodyScope551||sm!=0||(included551!=null&&primitive>=0&&primitive<included551.Length&&included551[primitive]); }
    static BodyScopeResources551 ScopeOwner551(Full319View335 f)
    {
        if (ReferenceEquals(f, null)) throw new ArgumentNullException("f");
        BodyScopeResources551 owner;
        if (!scopes551.TryGetValue(f, out owner))
        {
            owner = new BodyScopeResources551();
            scopes551.Add(f, owner);
        }
        return owner;
    }
    static ComputeBuffer ScopeBuffer551(Full319View335 f) { return ScopeOwner551(f).Buffer(); }
    public static void ReleaseScope551(Full319View335 f)
    {
        BodyScopeResources551 owner;
        if (!scopes551.TryGetValue(f, out owner)) return;
        scopes551.Remove(f);
        if (ReferenceEquals(selectedScope551, owner)) selectedScope551 = null;
        if (current == f) current = null;
        owner.Dispose();
    }
    static void ReleaseAllScopes551()
    {
        foreach (var owner in scopes551.Values) owner.Dispose();
        scopes551.Clear(); selectedScope551 = null;
    }
