using System;
using FantasySurvival.CharacterPresentation.ModularSprites;
using UnityEditor;
using UnityEngine;

namespace FantasySurvival.EditorTools
{
    /// <summary>
    /// Art-independent Edit Mode checks for the modular sprite data contract and pose math.
    /// No scene, prefab, asset, or Player presentation is created or changed.
    /// </summary>
    public static class ModularSpriteRigValidation
    {
        private const string MenuPath =
            "Tools/Fantasy Survival/Character Presentation/Validate Modular Sprite Rig";

        [MenuItem(MenuPath)]
        public static void Run()
        {
            ValidateFacingQuantizationAndHysteresis();
            ModularSpriteRigData rig = CreateValidRig();
            ValidateRigContracts(rig);
            ValidateSkinContracts(rig);
            ValidateFixedFrameMotionSampling(rig);
            ValidateForwardKinematicsAndPixelSnap(rig);

            Debug.Log(
                "Modular sprite validation passed: 8-direction facing and hysteresis, " +
                "rig cycle/duplicate/layer contracts, skin slots, fixed-frame motion, " +
                "and integer-pixel forward kinematics.");
        }

        [MenuItem(MenuPath, true)]
        private static bool CanRun()
        {
            return !EditorApplication.isPlayingOrWillChangePlaymode;
        }

        private static void ValidateFacingQuantizationAndHysteresis()
        {
            Vector2[] directions =
            {
                Vector2.up,
                new Vector2(1f, 1f),
                Vector2.right,
                new Vector2(1f, -1f),
                Vector2.down,
                new Vector2(-1f, -1f),
                Vector2.left,
                new Vector2(-1f, 1f)
            };

            for (int facingIndex = 0;
                 facingIndex < ModularSpriteRigData.FacingCount;
                 facingIndex++)
            {
                ModularSpriteFacing8 expected = (ModularSpriteFacing8)facingIndex;
                Require(
                    ModularSpritePoseSolver.QuantizeFacing(directions[facingIndex]) == expected,
                    $"Direction {directions[facingIndex]} did not quantize to {expected}.");
            }

            Require(
                ModularSpritePoseSolver.ResolveFacing(
                    Vector2.zero,
                    ModularSpriteFacing8.West,
                    5f) == ModularSpriteFacing8.West,
                "Zero input did not retain the previous facing.");
            Require(
                ModularSpritePoseSolver.ResolveFacing(
                    DirectionFromNorthClockwise(24f),
                    ModularSpriteFacing8.North,
                    5f) == ModularSpriteFacing8.North,
                "Facing changed inside the configured hysteresis band.");
            Require(
                ModularSpritePoseSolver.ResolveFacing(
                    DirectionFromNorthClockwise(30f),
                    ModularSpriteFacing8.North,
                    5f) == ModularSpriteFacing8.NorthEast,
                "Facing did not change after leaving the hysteresis band.");
        }

        private static void ValidateRigContracts(ModularSpriteRigData rig)
        {
            Require(rig.TryValidate(out string error), error);

            ModularSpriteBoneDefinition[] cyclicBones =
            {
                new ModularSpriteBoneDefinition("root", 1, Vector2Int.zero),
                new ModularSpriteBoneDefinition("knee", 0, new Vector2Int(0, -6))
            };
            var cyclicRig = new ModularSpriteRigData(
                16,
                cyclicBones,
                CreateParts(),
                CreateLayerOrders());
            Require(
                !cyclicRig.TryValidate(out error) && error.Contains("cycle"),
                "A cyclic rig hierarchy was accepted.");

            ModularSpritePartDefinition[] duplicateParts = CreateParts();
            duplicateParts[1] = new ModularSpritePartDefinition("upper_leg", 1, true);
            var duplicatePartRig = new ModularSpriteRigData(
                16,
                CreateBones(),
                duplicateParts,
                CreateLayerOrders());
            Require(
                !duplicatePartRig.TryValidate(out error) && error.Contains("duplicated"),
                "Duplicate rig part IDs were accepted.");

            ModularSpriteFacingLayerOrder[] invalidLayers = CreateLayerOrders();
            invalidLayers[0] = new ModularSpriteFacingLayerOrder(
                ModularSpriteFacing8.North,
                new[] { "knee_cap", "upper_leg", "upper_leg", "foot" });
            var duplicateLayerRig = new ModularSpriteRigData(
                16,
                CreateBones(),
                CreateParts(),
                invalidLayers);
            Require(
                !duplicateLayerRig.TryValidate(out error) && error.Contains("more than once"),
                "A facing layer order containing a duplicate part was accepted.");
        }

        private static void ValidateSkinContracts(ModularSpriteRigData rig)
        {
            ModularSpriteSkinPart[] parts = CreateSkinParts();
            var skin = new ModularSpriteSkinData("validation.skin", parts);
            Require(skin.TryValidate(rig, false, out string error), error);

            parts[1] = new ModularSpriteSkinPart(
                "upper_leg",
                new Sprite[ModularSpriteRigData.FacingCount]);
            var duplicateSkin = new ModularSpriteSkinData("validation.duplicate", parts);
            Require(
                !duplicateSkin.TryValidate(rig, false, out error) &&
                error.Contains("duplicate"),
                "A skin containing a duplicate part was accepted.");

            var texture = new Texture2D(1, 1);
            Sprite mismatchedSprite = Sprite.Create(
                texture,
                new Rect(0f, 0f, 1f, 1f),
                new Vector2(0.5f, 0.5f),
                rig.PixelsPerUnit * 2f);
            try
            {
                Sprite[] mismatchedFacings =
                    new Sprite[ModularSpriteRigData.FacingCount];
                mismatchedFacings[0] = mismatchedSprite;
                parts = CreateSkinParts();
                parts[0] = new ModularSpriteSkinPart(
                    "upper_leg",
                    mismatchedFacings);
                var mismatchedPpuSkin = new ModularSpriteSkinData(
                    "validation.mismatched-ppu",
                    parts);
                Require(
                    !mismatchedPpuSkin.TryValidate(rig, false, out error) &&
                    error.Contains("PPU"),
                    "An assigned Sprite with mismatched PPU was accepted when empty slots were optional.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(mismatchedSprite);
                UnityEngine.Object.DestroyImmediate(texture);
            }
        }

        private static void ValidateFixedFrameMotionSampling(ModularSpriteRigData rig)
        {
            var frames = new ModularSpriteMotionFrame[3];
            for (int frameIndex = 0; frameIndex < frames.Length; frameIndex++)
            {
                var poses = new ModularSpriteBonePose[rig.Bones.Count];
                poses[1] = new ModularSpriteBonePose(
                    Vector2Int.zero,
                    frameIndex * 10f);
                frames[frameIndex] = new ModularSpriteMotionFrame(poses);
            }

            var motion = new ModularSpriteMotionData(
                "validation.walk",
                4,
                true,
                frames);
            Require(motion.TryValidate(rig, out string error), error);
            Require(motion.GetFrameIndex(0d) == 0, "Motion did not start at frame 0.");
            Require(motion.GetFrameIndex(0.249d) == 0, "Motion advanced before its fixed frame boundary.");
            Require(motion.GetFrameIndex(0.25d) == 1, "Motion did not advance at its fixed frame boundary.");
            Require(motion.GetFrameIndex(0.5d) == 2, "Motion did not sample frame 2 at 0.5 seconds.");
            Require(motion.GetFrameIndex(0.75d) == 0, "Looping motion did not wrap deterministically.");

            var destination = new ModularSpriteBonePose[rig.Bones.Count];
            Require(
                motion.TrySample(0.25d, destination, out int sampledFrameIndex, out error),
                error);
            Require(
                sampledFrameIndex == 1 &&
                Mathf.Approximately(destination[1].LocalRotationDegrees, 10f),
                "Fixed-frame sampling returned the wrong bone pose.");
        }

        private static void ValidateForwardKinematicsAndPixelSnap(ModularSpriteRigData rig)
        {
            var localPoses = new ModularSpriteBonePose[rig.Bones.Count];
            localPoses[1] = new ModularSpriteBonePose(Vector2Int.zero, 90f);
            var solved = new ModularSpriteSolvedBonePose[rig.Bones.Count];

            Require(
                ModularSpritePoseSolver.TrySolve(rig, localPoses, solved, out string error),
                error);
            Require(
                solved[1].PositionPixels == new Vector2Int(0, -6),
                $"Knee solved to {solved[1].PositionPixels} instead of (0, -6).");
            Require(
                solved[2].PositionPixels == new Vector2Int(5, -6),
                $"Ankle solved to {solved[2].PositionPixels} instead of (5, -6).");

            Vector2Int expectedAnkle = ModularSpritePoseSolver.TransformAndSnap(
                solved[1].PositionPixels,
                rig.Bones[2].BindOffsetPixels,
                solved[1].WorldRotationDegrees);
            Require(
                expectedAnkle == solved[2].PositionPixels,
                "The child joint did not coincide with its parent segment endpoint.");

            localPoses[0] = new ModularSpriteBonePose(Vector2Int.zero, 45f);
            localPoses[1] = default;
            Require(
                ModularSpritePoseSolver.TrySolve(rig, localPoses, solved, out error),
                error);
            Require(
                solved[1].PositionPixels == new Vector2Int(4, -4),
                $"Rotated joint was not snapped to the expected integer pixel: {solved[1].PositionPixels}.");
        }

        private static ModularSpriteRigData CreateValidRig()
        {
            return new ModularSpriteRigData(
                16,
                CreateBones(),
                CreateParts(),
                CreateLayerOrders());
        }

        private static ModularSpriteBoneDefinition[] CreateBones()
        {
            return new[]
            {
                new ModularSpriteBoneDefinition("hip", -1, Vector2Int.zero),
                new ModularSpriteBoneDefinition("knee", 0, new Vector2Int(0, -6)),
                new ModularSpriteBoneDefinition("ankle", 1, new Vector2Int(0, -5))
            };
        }

        private static ModularSpritePartDefinition[] CreateParts()
        {
            return new[]
            {
                new ModularSpritePartDefinition("upper_leg", 0),
                new ModularSpritePartDefinition("knee_cap", 1, true),
                new ModularSpritePartDefinition("lower_leg", 1),
                new ModularSpritePartDefinition("foot", 2)
            };
        }

        private static ModularSpriteFacingLayerOrder[] CreateLayerOrders()
        {
            string[] backToFront = { "knee_cap", "upper_leg", "lower_leg", "foot" };
            var result = new ModularSpriteFacingLayerOrder[ModularSpriteRigData.FacingCount];
            for (int facingIndex = 0; facingIndex < result.Length; facingIndex++)
            {
                result[facingIndex] = new ModularSpriteFacingLayerOrder(
                    (ModularSpriteFacing8)facingIndex,
                    backToFront);
            }

            return result;
        }

        private static ModularSpriteSkinPart[] CreateSkinParts()
        {
            ModularSpritePartDefinition[] rigParts = CreateParts();
            var result = new ModularSpriteSkinPart[rigParts.Length];
            for (int index = 0; index < result.Length; index++)
            {
                result[index] = new ModularSpriteSkinPart(
                    rigParts[index].Id,
                    new Sprite[ModularSpriteRigData.FacingCount]);
            }

            return result;
        }

        private static Vector2 DirectionFromNorthClockwise(float degrees)
        {
            float radians = degrees * Mathf.Deg2Rad;
            return new Vector2(Mathf.Sin(radians), Mathf.Cos(radians));
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new InvalidOperationException(message);
            }
        }
    }
}
