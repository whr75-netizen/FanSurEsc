using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation.ModularSprites
{
    [Serializable]
    public struct ModularSpriteBonePose
    {
        [SerializeField] private Vector2Int localOffsetPixels;
        [SerializeField] private float localRotationDegrees;

        public Vector2Int LocalOffsetPixels => localOffsetPixels;
        public float LocalRotationDegrees => localRotationDegrees;

        public ModularSpriteBonePose(Vector2Int localOffsetPixels, float localRotationDegrees)
        {
            this.localOffsetPixels = localOffsetPixels;
            this.localRotationDegrees = localRotationDegrees;
        }
    }

    [Serializable]
    public sealed class ModularSpriteMotionFrame
    {
        [SerializeField] private ModularSpriteBonePose[] bonePoses =
            Array.Empty<ModularSpriteBonePose>();

        public IReadOnlyList<ModularSpriteBonePose> BonePoses => bonePoses;

        public ModularSpriteMotionFrame()
        {
        }

        public ModularSpriteMotionFrame(ModularSpriteBonePose[] bonePoses)
        {
            this.bonePoses = bonePoses != null
                ? (ModularSpriteBonePose[])bonePoses.Clone()
                : Array.Empty<ModularSpriteBonePose>();
        }

        public bool TryCopyTo(ModularSpriteBonePose[] destination, out string error)
        {
            if (bonePoses == null)
            {
                error = "Motion frame pose data is missing.";
                return false;
            }

            if (destination == null || destination.Length != bonePoses.Length)
            {
                error = $"Motion frame requires a destination array of {bonePoses.Length} bone poses.";
                return false;
            }

            Array.Copy(bonePoses, destination, bonePoses.Length);
            error = null;
            return true;
        }
    }

    [Serializable]
    public sealed class ModularSpriteMotionData
    {
        [SerializeField] private string id = string.Empty;
        [SerializeField, Min(1)] private int framesPerSecond = 8;
        [SerializeField] private bool loop = true;
        [SerializeField] private ModularSpriteMotionFrame[] frames =
            Array.Empty<ModularSpriteMotionFrame>();

        public string Id => id;
        public int FramesPerSecond => framesPerSecond;
        public bool Loop => loop;
        public IReadOnlyList<ModularSpriteMotionFrame> Frames => frames;
        public double DurationSeconds => framesPerSecond > 0 && frames != null
            ? (double)frames.Length / framesPerSecond
            : 0d;

        public ModularSpriteMotionData()
        {
        }

        public ModularSpriteMotionData(
            string id,
            int framesPerSecond,
            bool loop,
            ModularSpriteMotionFrame[] frames)
        {
            this.id = id ?? string.Empty;
            this.framesPerSecond = framesPerSecond;
            this.loop = loop;
            this.frames = frames != null
                ? (ModularSpriteMotionFrame[])frames.Clone()
                : Array.Empty<ModularSpriteMotionFrame>();
        }

        public bool TryValidate(ModularSpriteRigData rig, out string error)
        {
            if (rig == null)
            {
                error = "Motion requires a rig.";
                return false;
            }

            if (!rig.TryValidate(out error))
            {
                error = "Motion requires a valid rig. " + error;
                return false;
            }

            if (string.IsNullOrWhiteSpace(id))
            {
                error = "Motion has no stable ID.";
                return false;
            }

            if (framesPerSecond <= 0)
            {
                error = "Motion frames per second must be greater than zero.";
                return false;
            }

            if (frames == null || frames.Length == 0)
            {
                error = $"Motion '{id}' contains no frames.";
                return false;
            }

            for (int frameIndex = 0; frameIndex < frames.Length; frameIndex++)
            {
                ModularSpriteMotionFrame frame = frames[frameIndex];
                if (frame == null || frame.BonePoses == null ||
                    frame.BonePoses.Count != rig.Bones.Count)
                {
                    error = $"Motion '{id}' frame {frameIndex} must contain one pose for each of the {rig.Bones.Count} bones.";
                    return false;
                }

                for (int boneIndex = 0; boneIndex < frame.BonePoses.Count; boneIndex++)
                {
                    float rotation = frame.BonePoses[boneIndex].LocalRotationDegrees;
                    if (float.IsNaN(rotation) || float.IsInfinity(rotation))
                    {
                        error = $"Motion '{id}' frame {frameIndex}, bone {boneIndex} has a non-finite rotation.";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        public int GetFrameIndex(double elapsedSeconds)
        {
            if (frames == null || frames.Length == 0 || framesPerSecond <= 0)
            {
                return -1;
            }

            double safeTime = double.IsNaN(elapsedSeconds) ||
                              double.IsInfinity(elapsedSeconds) ||
                              elapsedSeconds < 0d
                ? 0d
                : elapsedSeconds;
            double frameNumber = Math.Floor(safeTime * framesPerSecond + 0.000000001d);

            if (loop)
            {
                return (int)(frameNumber % frames.Length);
            }

            return (int)Math.Min(frameNumber, frames.Length - 1d);
        }

        public bool TrySample(
            double elapsedSeconds,
            ModularSpriteBonePose[] destination,
            out int frameIndex,
            out string error)
        {
            frameIndex = GetFrameIndex(elapsedSeconds);
            if (frameIndex < 0)
            {
                error = $"Motion '{id}' cannot be sampled because it has no valid frames.";
                return false;
            }

            return frames[frameIndex].TryCopyTo(destination, out error);
        }
    }

    [CreateAssetMenu(
        fileName = "ModularSpriteMotion",
        menuName = "Fantasy Survival/Character Presentation/Modular Sprite Motion")]
    public sealed class ModularSpriteMotionDefinition : ScriptableObject
    {
        [SerializeField] private ModularSpriteMotionData data = new ModularSpriteMotionData();

        public ModularSpriteMotionData Data => data;

        public bool TryValidate(ModularSpriteRigDefinition rig, out string error)
        {
            if (data == null || rig == null)
            {
                error = "Motion data and rig are required.";
                return false;
            }

            return data.TryValidate(rig.Data, out error);
        }
    }
}
