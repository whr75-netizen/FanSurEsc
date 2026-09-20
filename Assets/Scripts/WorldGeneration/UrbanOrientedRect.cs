using System;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>
    /// A rectangle in map-local XZ space. Size is local frontage/depth, and local
    /// positive Z faces FacadeDirection. Finite coordinates and positive sizes
    /// are validated by the owning layout contract.
    /// </summary>
    public readonly struct UrbanOrientedRect
    {
        public UrbanOrientedRect(Vector2 center, Vector2 size, Vector2 facadeDirection)
        {
            float scale = Mathf.Max(Mathf.Abs(facadeDirection.x), Mathf.Abs(facadeDirection.y));
            if (scale == 0f)
            {
                throw new ArgumentException("Facade direction must be nonzero.", nameof(facadeDirection));
            }

            // Scale before normalizing so small, nonzero directions do not become
            // Vector2.normalized's zero vector, or overflow their squared length.
            Vector2 scaledDirection = facadeDirection / scale;
            FacadeDirection = scaledDirection / Mathf.Sqrt(scaledDirection.sqrMagnitude);
            Center = center;
            Size = size;
        }

        public Vector2 Center { get; }
        public Vector2 Size { get; }
        public Vector2 FacadeDirection { get; }
        public Vector2 Right => new Vector2(FacadeDirection.y, -FacadeDirection.x);
        public float LocalYawDegrees => Mathf.Atan2(FacadeDirection.x, FacadeDirection.y) * Mathf.Rad2Deg;

        /// <summary>Enclosing axis-aligned bounds; use Overlaps for exact collision.</summary>
        public Rect Aabb
        {
            get
            {
                Vector2 right = Right;
                Vector2 half = Size * .5f;
                Vector2 extent = new Vector2(
                    Mathf.Abs(right.x) * half.x + Mathf.Abs(FacadeDirection.x) * half.y,
                    Mathf.Abs(right.y) * half.x + Mathf.Abs(FacadeDirection.y) * half.y);
                return new Rect(Center - extent, extent * 2f);
            }
        }

        public Vector2 ToMap(Vector2 localPoint)
        {
            return Center + Right * localPoint.x + FacadeDirection * localPoint.y;
        }

        public Vector2 ToLocal(Vector2 mapPoint)
        {
            Vector2 delta = mapPoint - Center;
            return new Vector2(Vector2.Dot(delta, Right), Vector2.Dot(delta, FacadeDirection));
        }

        public bool Contains(Vector2 mapPoint, float tolerance = .001f)
        {
            Vector2 local = ToLocal(mapPoint);
            return Mathf.Abs(local.x) <= Size.x * .5f + tolerance &&
                   Mathf.Abs(local.y) <= Size.y * .5f + tolerance;
        }

        public bool Contains(UrbanOrientedRect other, float tolerance = .001f)
        {
            Vector2 delta = other.Center - Center;
            Vector2 right = Right;
            return Mathf.Abs(Vector2.Dot(delta, right)) + other.ProjectedRadius(right) <= Size.x * .5f + tolerance &&
                   Mathf.Abs(Vector2.Dot(delta, FacadeDirection)) + other.ProjectedRadius(FacadeDirection) <= Size.y * .5f + tolerance;
        }

        /// <summary>
        /// SAT on both rectangles' two axes. Boundary contact, or penetration no
        /// greater than tolerance on any separating axis, is not overlap.
        /// Pass zero tolerance when every positive-area intersection must count.
        /// </summary>
        public bool Overlaps(UrbanOrientedRect other, float tolerance = .001f)
        {
            Vector2 delta = other.Center - Center;
            return HasPositiveOverlap(other, delta, Right, tolerance) &&
                   HasPositiveOverlap(other, delta, FacadeDirection, tolerance) &&
                   HasPositiveOverlap(other, delta, other.Right, tolerance) &&
                   HasPositiveOverlap(other, delta, other.FacadeDirection, tolerance);
        }

        public UrbanOrientedRect Expanded(float margin)
        {
            return new UrbanOrientedRect(Center, Size + Vector2.one * (2f * margin), FacadeDirection);
        }

        public float DistanceSquared(Vector2 mapPoint)
        {
            Vector2 local = ToLocal(mapPoint);
            float dx = Mathf.Max(0f, Mathf.Abs(local.x) - Size.x * .5f);
            float dz = Mathf.Max(0f, Mathf.Abs(local.y) - Size.y * .5f);
            return dx * dx + dz * dz;
        }

        public static UrbanOrientedRect FromRect(Rect rect)
        {
            return new UrbanOrientedRect(rect.center, rect.size, Vector2.up);
        }

        /// <summary>A square-capped corridor; a and b must be distinct.</summary>
        public static UrbanOrientedRect FromSegment(Vector2 a, Vector2 b, float halfWidth)
        {
            Vector2 delta = b - a;
            return new UrbanOrientedRect((a + b) * .5f,
                new Vector2(2f * halfWidth, delta.magnitude + 2f * halfWidth), delta);
        }

        private float ProjectedRadius(Vector2 axis)
        {
            return Mathf.Abs(Vector2.Dot(Right, axis)) * Size.x * .5f +
                   Mathf.Abs(Vector2.Dot(FacadeDirection, axis)) * Size.y * .5f;
        }

        private bool HasPositiveOverlap(UrbanOrientedRect other, Vector2 delta, Vector2 axis, float tolerance)
        {
            return ProjectedRadius(axis) + other.ProjectedRadius(axis) -
                   Mathf.Abs(Vector2.Dot(delta, axis)) > tolerance;
        }
    }
}
