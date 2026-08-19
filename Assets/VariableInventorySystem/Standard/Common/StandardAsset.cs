namespace VariableInventorySystem
{
    public class StandardAsset : IVariableInventoryAsset
    {
        public string Path { get; }
        public UnityEngine.Texture2D Texture { get; }

        public StandardAsset(string path)
        {
            Path = path;
        }

        public StandardAsset(UnityEngine.Texture2D texture)
        {
            Texture = texture;
        }
    }
}
