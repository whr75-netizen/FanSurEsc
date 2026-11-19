// CLEAN-ROOM TEMPLATE (Staged outside Assets/ until user approves Unity import)
// Target clean-room destination: Assets/Rendering/PixelLayerTree/Runtime/PixelLayerTreeSchema.cs
// Zero dependency on legacy Product77 / Native395 / Full319View335 / Eye348.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.PixelLayerTree
{
    public enum LayerDomain
    {
        Source3D = 0,
        LocalGrid = 1,
        Compose2D = 2,
        Finish2D = 3
    }

    public enum LayerGridSpace
    {
        RootGrid = 0,
        LocalEyeGrid = 1,
        Final2DGrid = 2
    }

    public enum LayerClipMode
    {
        None = 0,
        ClipToParent = 1,
        ClipToMask = 2
    }

    public enum LayerOccludeMode
    {
        Base = 0,
        DepthZTest = 1,
        LayerOverParent = 2
    }

    public enum LayerPaletteMode
    {
        IndexOnlyRQ = 0,
        FinalLUTResolve = 1
    }

    public enum LayerDesignStatus
    {
        Confirmed = 0,
        TbdDesign = 1
    }

    /// <summary>
    /// Single uniform descriptor supporting 20~50+ infinitely extensible nested layers
    /// (e.g., "1", "2-1", "2-2-1", "3-2-3-1"). Order-by-construction prevents frog-eyes,
    /// double outlines, and mixels without per-bug patch code.
    /// </summary>
    [Serializable]
    public sealed class LayerNodeDescriptor
    {
        public string id;
        public string parentId;
        public string displayName;
        public int numericNodeId;
        public LayerDomain domain;
        public LayerGridSpace gridSpace;
        public LayerClipMode clipMode;
        public LayerOccludeMode occludeMode;
        public LayerPaletteMode paletteMode;
        public LayerDesignStatus designStatus;
        public int paletteRegionSlot;
        public bool protectFromOuterSilhouette;
    }

    /// <summary>
    /// Declarative hierarchical layer tree asset. Adding a new costume part or facial
    /// sub-feature appends one LayerNodeDescriptor without modifying pipeline engine code.
    /// </summary>
    [CreateAssetMenu(menuName = "FantasySurvival/Pixel Layer Tree", fileName = "CharacterPixelLayerTree")]
    public sealed class PixelLayerTreeAsset : ScriptableObject
    {
        [Header("Unified Single Logical Grid (Zero Mixels)")]
        public int logicalWidth = 480;
        public int logicalHeight = 272;
        public int displayIntegerScale = 2;

        [Header("Physical Depth Silhouette Threshold (Chin-over-Neck etc.)")]
        public float physicalDepthSilhouetteThreshold = 0.025f;

        [Header("Recursive Hierarchical Layer Stack")]
        public List<LayerNodeDescriptor> nodes = new List<LayerNodeDescriptor>();

        /// <summary>
        /// Computes inherited parent clipping mask chain for any depth (e.g., 3-2-3-1 inherits 3-2-3 -> 3-2-2 -> 3-2-1).
        /// </summary>
        public List<string> GetInheritedClipChain(string nodeId)
        {
            var map = new Dictionary<string, LayerNodeDescriptor>(nodes.Count);
            foreach (var n in nodes)
            {
                if (!string.IsNullOrEmpty(n.id)) map[n.id] = n;
            }

            var chain = new List<string>();
            if (!map.TryGetValue(nodeId, out var current)) return chain;

            int guard = 0;
            while (current != null && guard++ < 64)
            {
                if (current.clipMode == LayerClipMode.ClipToParent && !string.IsNullOrEmpty(current.parentId))
                {
                    chain.Add(current.parentId);
                }
                if (string.IsNullOrEmpty(current.parentId) || !map.TryGetValue(current.parentId, out current))
                {
                    break;
                }
            }

            chain.Reverse();
            return chain;
        }
    }
}
