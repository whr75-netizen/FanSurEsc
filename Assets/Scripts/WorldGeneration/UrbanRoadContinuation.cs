using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>
    /// A straight outward extension derived from a boundary road endpoint. This is
    /// surface geometry, not an extra graph edge or a source of spawn candidates.
    /// All positions and distances use the layout's local XZ plane in metres.
    /// </summary>
    public readonly struct UrbanRoadContinuation
    {
        private const float GeometryTolerance = 0.0001f;

        private UrbanRoadContinuation(
            int sourceRoadIndex,
            int nodeIndex,
            Vector2 start,
            Vector2 tangent,
            float width,
            bool isPrimary)
        {
            SourceRoadIndex = sourceRoadIndex;
            NodeIndex = nodeIndex;
            Start = start;
            Tangent = tangent;
            Width = width;
            IsPrimary = isPrimary;
        }

        public int SourceRoadIndex { get; }
        public int NodeIndex { get; }
        public Vector2 Start { get; }
        public Vector2 Tangent { get; }
        public float Width { get; }
        public bool IsPrimary { get; }

        /// <summary>Tests a point against the infinite outward half-strip.</summary>
        public bool Contains(Vector2 point)
        {
            if (Width <= 0f || !IsFinite(point))
            {
                return false;
            }

            Vector2 offset = point - Start;
            float along = Vector2.Dot(offset, Tangent);
            float across = Tangent.x * offset.y - Tangent.y * offset.x;
            return along >= -GeometryTolerance &&
                   Mathf.Abs(across) <= Width * 0.5f + GeometryTolerance;
        }

        /// <summary>
        /// Returns the ray's exit distance from an AABB containing Start. The
        /// gameplay bounds and any larger display bounds satisfy this contract.
        /// </summary>
        public float ExitDistance(Rect bounds)
        {
            if (!IsFinite(bounds.min) || !IsFinite(bounds.max) ||
                bounds.width <= 0f || bounds.height <= 0f || Width <= 0f ||
                Start.x < bounds.xMin - GeometryTolerance ||
                Start.x > bounds.xMax + GeometryTolerance ||
                Start.y < bounds.yMin - GeometryTolerance ||
                Start.y > bounds.yMax + GeometryTolerance)
            {
                throw new ArgumentException(
                    "Road continuation bounds must be finite, positive, and contain the start.",
                    nameof(bounds));
            }

            float xDistance = Tangent.x > GeometryTolerance
                ? (bounds.xMax - Start.x) / Tangent.x
                : Tangent.x < -GeometryTolerance
                    ? (bounds.xMin - Start.x) / Tangent.x
                    : float.PositiveInfinity;
            float zDistance = Tangent.y > GeometryTolerance
                ? (bounds.yMax - Start.y) / Tangent.y
                : Tangent.y < -GeometryTolerance
                    ? (bounds.yMin - Start.y) / Tangent.y
                    : float.PositiveInfinity;
            float distance = Mathf.Min(xDistance, zDistance);
            if (!IsFinite(distance))
            {
                throw new InvalidOperationException("Road continuation has no finite exit direction.");
            }

            return Mathf.Max(0f, distance);
        }

        /// <summary>
        /// Preserves source road order and derives at most one continuation per
        /// endpoint, including a corner endpoint that faces two boundary planes.
        /// No graph positions, graph ports, or random streams are changed.
        /// </summary>
        public static List<UrbanRoadContinuation> Create(
            IReadOnlyList<Vector2> nodes,
            IReadOnlyList<UrbanRoadSegment> roads)
        {
            if (nodes == null) throw new ArgumentNullException(nameof(nodes));
            if (roads == null) throw new ArgumentNullException(nameof(roads));
            var continuations = new List<UrbanRoadContinuation>();
            if (nodes.Count == 0)
            {
                if (roads.Count != 0)
                    throw new ArgumentException("Road continuations require their source nodes.", nameof(nodes));
                return continuations;
            }

            Vector2 minimum = nodes[0];
            Vector2 maximum = nodes[0];
            for (int index = 0; index < nodes.Count; index++)
            {
                if (!IsFinite(nodes[index]))
                    throw new ArgumentException("Road continuation nodes must be finite.", nameof(nodes));
                minimum = Vector2.Min(minimum, nodes[index]);
                maximum = Vector2.Max(maximum, nodes[index]);
            }

            for (int roadIndex = 0; roadIndex < roads.Count; roadIndex++)
            {
                UrbanRoadSegment road = roads[roadIndex];
                Vector2 segment = road.End - road.Start;
                if (road.FromNodeIndex < 0 || road.FromNodeIndex >= nodes.Count ||
                    road.ToNodeIndex < 0 || road.ToNodeIndex >= nodes.Count ||
                    road.FromNodeIndex == road.ToNodeIndex ||
                    !IsFinite(road.Start) || !IsFinite(road.End) ||
                    !IsFinite(road.Width) || road.Width <= 0f ||
                    !IsFinite(segment.sqrMagnitude) ||
                    segment.sqrMagnitude <= GeometryTolerance * GeometryTolerance ||
                    (road.Start - nodes[road.FromNodeIndex]).sqrMagnitude >
                        GeometryTolerance * GeometryTolerance ||
                    (road.End - nodes[road.ToNodeIndex]).sqrMagnitude >
                        GeometryTolerance * GeometryTolerance)
                {
                    throw new ArgumentException(
                        $"Road {roadIndex} has invalid continuation geometry or node bindings.", nameof(roads));
                }

                Vector2 tangent = segment.normalized;
                AddEndpoint(road.FromNodeIndex, road.Start, -tangent);
                AddEndpoint(road.ToNodeIndex, road.End, tangent);

                void AddEndpoint(int nodeIndex, Vector2 point, Vector2 outward)
                {
                    bool leavesNodeBounds =
                        (Mathf.Abs(point.x - minimum.x) <= GeometryTolerance && outward.x < -GeometryTolerance) ||
                        (Mathf.Abs(point.x - maximum.x) <= GeometryTolerance && outward.x > GeometryTolerance) ||
                        (Mathf.Abs(point.y - minimum.y) <= GeometryTolerance && outward.y < -GeometryTolerance) ||
                        (Mathf.Abs(point.y - maximum.y) <= GeometryTolerance && outward.y > GeometryTolerance);
                    if (leavesNodeBounds)
                    {
                        continuations.Add(new UrbanRoadContinuation(
                            roadIndex, nodeIndex, point, outward, road.Width, road.IsPrimary));
                    }
                }
            }

            return continuations;
        }

        private static bool IsFinite(Vector2 value) => IsFinite(value.x) && IsFinite(value.y);
        private static bool IsFinite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);
    }
}
