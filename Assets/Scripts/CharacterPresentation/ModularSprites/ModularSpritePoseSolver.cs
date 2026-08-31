using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation.ModularSprites
{
    public readonly struct ModularSpriteSolvedBonePose
    {
        public Vector2Int PositionPixels { get; }
        public float WorldRotationDegrees { get; }

        public ModularSpriteSolvedBonePose(
            Vector2Int positionPixels,
            float worldRotationDegrees)
        {
            PositionPixels = positionPixels;
            WorldRotationDegrees = worldRotationDegrees;
        }
    }

    /// <summary>
    /// Deterministic presentation math. Rig and motion authoring are validated separately so
    /// the per-frame solve needs no hierarchy traversal, lookup dictionary, or allocation.
    /// </summary>
    public static class ModularSpritePoseSolver
    {
        public const float FacingSectorDegrees = 45f;
        public const float FacingHalfSectorDegrees = FacingSectorDegrees * 0.5f;
        public const float MaximumFacingHysteresisDegrees = 22.4f;

        private const float MinimumDirectionSqrMagnitude = 0.000001f;

        public static ModularSpriteFacing8 QuantizeFacing(
            Vector2 direction,
            ModularSpriteFacing8 zeroDirectionFallback = ModularSpriteFacing8.South)
        {
            if (direction.sqrMagnitude <= MinimumDirectionSqrMagnitude)
            {
                return zeroDirectionFallback;
            }

            float angleFromNorthClockwise = GetAngleFromNorthClockwise(direction);
            int facingIndex = Mathf.FloorToInt(
                (angleFromNorthClockwise + FacingHalfSectorDegrees) / FacingSectorDegrees) %
                ModularSpriteRigData.FacingCount;
            return (ModularSpriteFacing8)facingIndex;
        }

        public static ModularSpriteFacing8 ResolveFacing(
            Vector2 direction,
            ModularSpriteFacing8 previousFacing,
            float hysteresisDegrees)
        {
            if (direction.sqrMagnitude <= MinimumDirectionSqrMagnitude)
            {
                return previousFacing;
            }

            float angleFromNorthClockwise = GetAngleFromNorthClockwise(direction);
            float previousCenter = (int)previousFacing * FacingSectorDegrees;
            float difference = Mathf.Abs(Mathf.DeltaAngle(previousCenter, angleFromNorthClockwise));
            float clampedHysteresis = Mathf.Clamp(
                hysteresisDegrees,
                0f,
                MaximumFacingHysteresisDegrees);

            if (difference <= FacingHalfSectorDegrees + clampedHysteresis)
            {
                return previousFacing;
            }

            return QuantizeFacing(direction, previousFacing);
        }

        public static bool TrySolve(
            ModularSpriteRigData rig,
            IReadOnlyList<ModularSpriteBonePose> localPoses,
            ModularSpriteSolvedBonePose[] destination,
            out string error)
        {
            if (rig == null)
            {
                error = "A rig is required to solve a modular sprite pose.";
                return false;
            }

            int boneCount = rig.Bones.Count;
            if (localPoses == null || localPoses.Count != boneCount)
            {
                error = $"Pose must contain one local value for each of the {boneCount} rig bones.";
                return false;
            }

            if (destination == null || destination.Length != boneCount)
            {
                error = $"Pose destination must contain exactly {boneCount} entries.";
                return false;
            }

            for (int boneIndex = 0; boneIndex < boneCount; boneIndex++)
            {
                ModularSpriteBoneDefinition bone = rig.Bones[boneIndex];
                if (bone == null)
                {
                    error = $"Rig bone {boneIndex} is null.";
                    return false;
                }

                int parentIndex = bone.ParentIndex;
                if (parentIndex >= boneIndex)
                {
                    error = $"Rig bone '{bone.Id}' is not stored after its parent.";
                    return false;
                }

                ModularSpriteBonePose localPose = localPoses[boneIndex];
                Vector2 localOffset = bone.BindOffsetPixels + localPose.LocalOffsetPixels;
                float parentRotation = parentIndex >= 0
                    ? destination[parentIndex].WorldRotationDegrees
                    : 0f;
                Vector2Int parentPosition = parentIndex >= 0
                    ? destination[parentIndex].PositionPixels
                    : Vector2Int.zero;

                Vector2Int worldPosition = parentIndex >= 0
                    ? TransformAndSnap(parentPosition, localOffset, parentRotation)
                    : SnapToPixel(localOffset);
                float worldRotation = NormalizeDegrees(
                    parentRotation + bone.BindRotationDegrees +
                    localPose.LocalRotationDegrees);

                destination[boneIndex] = new ModularSpriteSolvedBonePose(
                    worldPosition,
                    worldRotation);
            }

            error = null;
            return true;
        }

        public static Vector2Int TransformAndSnap(
            Vector2Int originPixels,
            Vector2 localOffsetPixels,
            float rotationDegrees)
        {
            float radians = rotationDegrees * Mathf.Deg2Rad;
            float sine = Mathf.Sin(radians);
            float cosine = Mathf.Cos(radians);
            var rotated = new Vector2(
                localOffsetPixels.x * cosine - localOffsetPixels.y * sine,
                localOffsetPixels.x * sine + localOffsetPixels.y * cosine);
            return originPixels + SnapToPixel(rotated);
        }

        public static Vector2Int SnapToPixel(Vector2 value)
        {
            return new Vector2Int(
                Mathf.RoundToInt(value.x),
                Mathf.RoundToInt(value.y));
        }

        private static float GetAngleFromNorthClockwise(Vector2 direction)
        {
            float angle = Mathf.Atan2(direction.x, direction.y) * Mathf.Rad2Deg;
            return Mathf.Repeat(angle, 360f);
        }

        private static float NormalizeDegrees(float degrees)
        {
            return Mathf.Repeat(degrees + 180f, 360f) - 180f;
        }
    }
}
