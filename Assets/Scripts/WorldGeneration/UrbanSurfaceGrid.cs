using System;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    public enum UrbanSurfaceTileKind : byte
    {
        Ground = 0,
        Sidewalk = 1,
        SecondaryRoad = 2,
        PrimaryRoad = 3
    }

    [Flags]
    public enum UrbanTileConnection : byte
    {
        None = 0,
        N = 1 << 0,
        NE = 1 << 1,
        E = 1 << 2,
        SE = 1 << 3,
        S = 1 << 4,
        SW = 1 << 5,
        W = 1 << 6,
        NW = 1 << 7
    }

    /// <summary>
    /// Immutable, scene-independent surface data derived from an urban layout.
    /// Each cell owns exactly one surface kind, so ground, sidewalk, and road
    /// presentation never need overlapping coplanar meshes. Surface masks describe
    /// neighboring areas for 16/47-style border autotiling, while road-port masks
    /// separately preserve actual graph connectivity. Keeping these two meanings
    /// separate prevents touching diagonal pixels from inventing a road connection.
    /// Primary and secondary roads remain distinct data but belong to one compatible
    /// road family when surface masks are built, keeping their intersections continuous.
    /// </summary>
    public sealed class UrbanSurfaceGrid
    {
        private readonly UrbanSurfaceTileKind[] kinds;
        private readonly UrbanTileConnection[] surfaceConnectionMasks;
        private readonly UrbanTileConnection[] roadPortMasks;

        public UrbanSurfaceGrid(
            int width,
            int height,
            float tileSize,
            Vector2 localOrigin,
            UrbanSurfaceTileKind[] kinds,
            UrbanTileConnection[] surfaceConnectionMasks,
            UrbanTileConnection[] roadPortMasks)
        {
            if (width <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(width), width, "Width must be positive.");
            }

            if (height <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(height), height, "Height must be positive.");
            }

            if (float.IsNaN(tileSize) || float.IsInfinity(tileSize) || tileSize <= 0f)
            {
                throw new ArgumentOutOfRangeException(nameof(tileSize), tileSize, "Tile size must be finite and positive.");
            }

            if (float.IsNaN(localOrigin.x) || float.IsInfinity(localOrigin.x) ||
                float.IsNaN(localOrigin.y) || float.IsInfinity(localOrigin.y))
            {
                throw new ArgumentOutOfRangeException(nameof(localOrigin), localOrigin, "Local origin must be finite.");
            }

            var requestedCellCount = (long)width * height;
            if (requestedCellCount > int.MaxValue)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(width),
                    requestedCellCount,
                    "Grid dimensions are too large.");
            }

            var cellCount = (int)requestedCellCount;

            if (kinds == null)
            {
                throw new ArgumentNullException(nameof(kinds));
            }

            if (surfaceConnectionMasks == null)
            {
                throw new ArgumentNullException(nameof(surfaceConnectionMasks));
            }

            if (roadPortMasks == null)
            {
                throw new ArgumentNullException(nameof(roadPortMasks));
            }

            if (kinds.Length != cellCount)
            {
                throw new ArgumentException(
                    $"Expected {cellCount} surface kinds but received {kinds.Length}.",
                    nameof(kinds));
            }

            if (surfaceConnectionMasks.Length != cellCount)
            {
                throw new ArgumentException(
                    $"Expected {cellCount} surface connection masks but received {surfaceConnectionMasks.Length}.",
                    nameof(surfaceConnectionMasks));
            }

            if (roadPortMasks.Length != cellCount)
            {
                throw new ArgumentException(
                    $"Expected {cellCount} road-port masks but received {roadPortMasks.Length}.",
                    nameof(roadPortMasks));
            }

            for (var index = 0; index < kinds.Length; index++)
            {
                if (kinds[index] != UrbanSurfaceTileKind.Ground &&
                    kinds[index] != UrbanSurfaceTileKind.Sidewalk &&
                    kinds[index] != UrbanSurfaceTileKind.SecondaryRoad &&
                    kinds[index] != UrbanSurfaceTileKind.PrimaryRoad)
                {
                    throw new ArgumentOutOfRangeException(
                        nameof(kinds),
                        kinds[index],
                        $"Cell {index} has an unsupported surface kind.");
                }
            }

            Width = width;
            Height = height;
            TileSize = tileSize;
            LocalOrigin = localOrigin;

            // Keep ownership inside this value object. Callers may safely reuse or
            // mutate their source buffers after construction.
            this.kinds = (UrbanSurfaceTileKind[])kinds.Clone();
            this.surfaceConnectionMasks = (UrbanTileConnection[])surfaceConnectionMasks.Clone();
            this.roadPortMasks = (UrbanTileConnection[])roadPortMasks.Clone();
        }

        public int Width { get; }
        public int Height { get; }
        public int CellCount => kinds.Length;
        public float TileSize { get; }

        /// <summary>The lower-left corner of cell (0, 0) in layout-local XZ space.</summary>
        public Vector2 LocalOrigin { get; }

        public static bool IsRoad(UrbanSurfaceTileKind kind)
        {
            return kind == UrbanSurfaceTileKind.SecondaryRoad ||
                   kind == UrbanSurfaceTileKind.PrimaryRoad;
        }

        /// <summary>
        /// Defines which neighboring cells share one autotile connection family.
        /// In particular, primary and secondary road cells connect to each other.
        /// </summary>
        public static bool AreAutotileCompatible(
            UrbanSurfaceTileKind source,
            UrbanSurfaceTileKind neighbor)
        {
            return source == neighbor || (IsRoad(source) && IsRoad(neighbor));
        }

        /// <summary>
        /// Builds a canonical blob/47-tile mask. A diagonal corner is connected
        /// only when both cardinal sides supporting that corner are connected.
        /// This keeps a merely touching diagonal cell from selecting a filled
        /// corner sprite while leaving exact road direction to RoadPortMask.
        /// </summary>
        public static UrbanTileConnection ComposeCanonicalSurfaceMask(
            bool north,
            bool northEast,
            bool east,
            bool southEast,
            bool south,
            bool southWest,
            bool west,
            bool northWest)
        {
            UrbanTileConnection mask = UrbanTileConnection.None;
            if (north) mask |= UrbanTileConnection.N;
            if (east) mask |= UrbanTileConnection.E;
            if (south) mask |= UrbanTileConnection.S;
            if (west) mask |= UrbanTileConnection.W;
            if (northEast && north && east) mask |= UrbanTileConnection.NE;
            if (southEast && south && east) mask |= UrbanTileConnection.SE;
            if (southWest && south && west) mask |= UrbanTileConnection.SW;
            if (northWest && north && west) mask |= UrbanTileConnection.NW;
            return mask;
        }

        /// <summary>Maps one unit cell step to the matching exact road port.</summary>
        public static UrbanTileConnection ConnectionFromUnitStep(int deltaX, int deltaZ)
        {
            if (deltaX == 0 && deltaZ == 1) return UrbanTileConnection.N;
            if (deltaX == 1 && deltaZ == 1) return UrbanTileConnection.NE;
            if (deltaX == 1 && deltaZ == 0) return UrbanTileConnection.E;
            if (deltaX == 1 && deltaZ == -1) return UrbanTileConnection.SE;
            if (deltaX == 0 && deltaZ == -1) return UrbanTileConnection.S;
            if (deltaX == -1 && deltaZ == -1) return UrbanTileConnection.SW;
            if (deltaX == -1 && deltaZ == 0) return UrbanTileConnection.W;
            if (deltaX == -1 && deltaZ == 1) return UrbanTileConnection.NW;

            throw new ArgumentOutOfRangeException(
                nameof(deltaX),
                $"Cell step ({deltaX}, {deltaZ}) is not one of the eight tile directions.");
        }

        public bool ContainsCell(int x, int z)
        {
            return x >= 0 && x < Width && z >= 0 && z < Height;
        }

        public UrbanSurfaceTileKind GetKind(int x, int z)
        {
            return kinds[GetIndex(x, z)];
        }

        public UrbanTileConnection GetSurfaceConnectionMask(int x, int z)
        {
            return surfaceConnectionMasks[GetIndex(x, z)];
        }

        public UrbanTileConnection GetRoadPortMask(int x, int z)
        {
            return roadPortMasks[GetIndex(x, z)];
        }

        public Vector2 GetCellCenter(int x, int z)
        {
            GetIndex(x, z);
            return LocalOrigin + new Vector2((x + 0.5f) * TileSize, (z + 0.5f) * TileSize);
        }

        public bool TryLocalToCell(Vector2 localPosition, out int x, out int z)
        {
            if (float.IsNaN(localPosition.x) || float.IsInfinity(localPosition.x) ||
                float.IsNaN(localPosition.y) || float.IsInfinity(localPosition.y))
            {
                x = -1;
                z = -1;
                return false;
            }

            var relative = localPosition - LocalOrigin;
            x = Mathf.FloorToInt(relative.x / TileSize);
            z = Mathf.FloorToInt(relative.y / TileSize);
            return ContainsCell(x, z);
        }

        private int GetIndex(int x, int z)
        {
            if (!ContainsCell(x, z))
            {
                throw new ArgumentOutOfRangeException(
                    nameof(x),
                    $"Cell ({x}, {z}) is outside the {Width} x {Height} surface grid.");
            }

            return checked((z * Width) + x);
        }
    }
}
