using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>One four-connected Ground component in the canonical surface grid.</summary>
    public sealed class UrbanBlockRegion
    {
        internal UrbanBlockRegion(int stableId, IReadOnlyList<int> cellIndices)
        {
            StableId = stableId;
            var copy = new int[cellIndices.Count];
            for (int i = 0; i < copy.Length; i++) copy[i] = cellIndices[i];
            CellIndices = Array.AsReadOnly(copy);
        }

        /// <summary>The component's smallest row-major cell index, not a Regions index.</summary>
        public int StableId { get; }
        public IReadOnlyList<int> CellIndices { get; }
    }

    /// <summary>
    /// Immutable block ownership derived from the immutable surface grid.
    /// Diagonal point contact never connects two Ground components.
    /// </summary>
    public sealed class UrbanBlockMap
    {
        private readonly UrbanSurfaceGrid grid;
        private readonly int[] blockIds;

        private UrbanBlockMap(UrbanSurfaceGrid grid, int[] blockIds, List<UrbanBlockRegion> regions)
        {
            this.grid = grid;
            this.blockIds = blockIds;
            Regions = Array.AsReadOnly(regions.ToArray());
        }

        public IReadOnlyList<UrbanBlockRegion> Regions { get; }

        public static UrbanBlockMap Build(UrbanSurfaceGrid grid)
        {
            if (grid == null) throw new ArgumentNullException(nameof(grid));

            var blockIds = new int[grid.CellCount];
            for (int i = 0; i < blockIds.Length; i++) blockIds[i] = -1;
            var queue = new int[grid.CellCount];
            var regions = new List<UrbanBlockRegion>();

            // Row-major discovery makes the first cell the component's stable ID.
            for (int start = 0; start < blockIds.Length; start++)
            {
                int startX = start % grid.Width;
                int startZ = start / grid.Width;
                if (blockIds[start] >= 0 || grid.GetKind(startX, startZ) != UrbanSurfaceTileKind.Ground) continue;

                var cells = new List<int>();
                int head = 0;
                int tail = 1;
                queue[0] = start;
                blockIds[start] = start;
                while (head < tail)
                {
                    int index = queue[head++];
                    cells.Add(index);
                    int x = index % grid.Width;
                    int z = index / grid.Width;
                    EnqueueGround(grid, blockIds, queue, ref tail, x - 1, z, start);
                    EnqueueGround(grid, blockIds, queue, ref tail, x + 1, z, start);
                    EnqueueGround(grid, blockIds, queue, ref tail, x, z - 1, start);
                    EnqueueGround(grid, blockIds, queue, ref tail, x, z + 1, start);
                }

                cells.Sort();
                regions.Add(new UrbanBlockRegion(start, cells));
            }

            return new UrbanBlockMap(grid, blockIds, regions);
        }

        public int GetBlockId(int x, int z)
        {
            return grid.ContainsCell(x, z) ? blockIds[z * grid.Width + x] : -1;
        }

        /// <summary>
        /// Requires the complete rectangle to lie inside the map and every cell
        /// with positive-area intersection to belong to one Ground component.
        /// Corners and center alone cannot establish containment near notches.
        /// </summary>
        public bool TryGetContainingBlock(UrbanOrientedRect rectangle, out int blockId)
        {
            blockId = -1;
            Rect bounds = rectangle.Aabb;
            Vector2 origin = grid.LocalOrigin;
            float tileSize = grid.TileSize;
            if (bounds.xMin < origin.x || bounds.yMin < origin.y ||
                bounds.xMax > origin.x + grid.Width * tileSize ||
                bounds.yMax > origin.y + grid.Height * tileSize)
            {
                return false;
            }

            int minX = Mathf.Clamp(Mathf.FloorToInt((bounds.xMin - origin.x) / tileSize), 0, grid.Width - 1);
            int maxX = Mathf.Clamp(Mathf.FloorToInt((bounds.xMax - origin.x) / tileSize), 0, grid.Width - 1);
            int minZ = Mathf.Clamp(Mathf.FloorToInt((bounds.yMin - origin.y) / tileSize), 0, grid.Height - 1);
            int maxZ = Mathf.Clamp(Mathf.FloorToInt((bounds.yMax - origin.y) / tileSize), 0, grid.Height - 1);
            int containingId = -1;
            Vector2 cellSize = Vector2.one * tileSize;
            for (int z = minZ; z <= maxZ; z++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    var cell = new UrbanOrientedRect(grid.GetCellCenter(x, z), cellSize, Vector2.up);
                    if (!rectangle.Overlaps(cell, 0f)) continue;

                    int cellBlockId = GetBlockId(x, z);
                    if (cellBlockId < 0 || (containingId >= 0 && containingId != cellBlockId)) return false;
                    containingId = cellBlockId;
                }
            }

            blockId = containingId;
            return containingId >= 0;
        }

        private static void EnqueueGround(UrbanSurfaceGrid grid, int[] blockIds, int[] queue,
            ref int tail, int x, int z, int blockId)
        {
            if (!grid.ContainsCell(x, z)) return;
            int index = z * grid.Width + x;
            if (blockIds[index] >= 0 || grid.GetKind(x, z) != UrbanSurfaceTileKind.Ground) return;
            blockIds[index] = blockId;
            queue[tail++] = index;
        }
    }
}
