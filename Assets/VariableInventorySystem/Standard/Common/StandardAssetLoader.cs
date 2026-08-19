using System;
using System.Collections;
using UnityEngine;

namespace VariableInventorySystem
{
    public class StandardAssetLoader
    {
        public virtual IEnumerator LoadAsync(IVariableInventoryAsset imageAsset, Action<Texture2D> onLoad)
        {
            var standardAsset = imageAsset as StandardAsset;
            if (standardAsset == null)
            {
                onLoad?.Invoke(null);
                yield break;
            }

            if (standardAsset.Texture != null)
            {
                onLoad?.Invoke(standardAsset.Texture);
                yield break;
            }

            var loader = Resources.LoadAsync<Texture2D>(standardAsset.Path);
            yield return loader;
            onLoad?.Invoke(loader.asset as Texture2D);
        }
    }
}
