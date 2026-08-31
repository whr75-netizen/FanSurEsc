using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation.ModularSprites
{
    public enum ModularSpriteFacing8
    {
        North = 0,
        NorthEast = 1,
        East = 2,
        SouthEast = 3,
        South = 4,
        SouthWest = 5,
        West = 6,
        NorthWest = 7
    }

    [Serializable]
    public sealed class ModularSpriteBoneDefinition
    {
        [SerializeField] private string id = string.Empty;
        [SerializeField] private int parentIndex = -1;
        [SerializeField] private Vector2Int bindOffsetPixels;
        [SerializeField] private float bindRotationDegrees;

        public string Id => id;
        public int ParentIndex => parentIndex;
        public Vector2Int BindOffsetPixels => bindOffsetPixels;
        public float BindRotationDegrees => bindRotationDegrees;

        public ModularSpriteBoneDefinition()
        {
        }

        public ModularSpriteBoneDefinition(
            string id,
            int parentIndex,
            Vector2Int bindOffsetPixels,
            float bindRotationDegrees = 0f)
        {
            this.id = id ?? string.Empty;
            this.parentIndex = parentIndex;
            this.bindOffsetPixels = bindOffsetPixels;
            this.bindRotationDegrees = bindRotationDegrees;
        }
    }

    [Serializable]
    public sealed class ModularSpritePartDefinition
    {
        [SerializeField] private string id = string.Empty;
        [SerializeField] private int boneIndex;
        [SerializeField] private bool jointCorrection;

        public string Id => id;
        public int BoneIndex => boneIndex;
        public bool IsJointCorrection => jointCorrection;

        public ModularSpritePartDefinition()
        {
        }

        public ModularSpritePartDefinition(string id, int boneIndex, bool jointCorrection = false)
        {
            this.id = id ?? string.Empty;
            this.boneIndex = boneIndex;
            this.jointCorrection = jointCorrection;
        }
    }

    [Serializable]
    public sealed class ModularSpriteFacingLayerOrder
    {
        [SerializeField] private ModularSpriteFacing8 facing;
        [SerializeField] private string[] partIdsBackToFront = Array.Empty<string>();

        public ModularSpriteFacing8 Facing => facing;
        public IReadOnlyList<string> PartIdsBackToFront => partIdsBackToFront;

        public ModularSpriteFacingLayerOrder()
        {
        }

        public ModularSpriteFacingLayerOrder(
            ModularSpriteFacing8 facing,
            string[] partIdsBackToFront)
        {
            this.facing = facing;
            this.partIdsBackToFront = partIdsBackToFront != null
                ? (string[])partIdsBackToFront.Clone()
                : Array.Empty<string>();
        }
    }

    [Serializable]
    public sealed class ModularSpriteRigData
    {
        public const int FacingCount = 8;

        [SerializeField, Min(1)] private int pixelsPerUnit = 16;
        [SerializeField] private ModularSpriteBoneDefinition[] bones =
            Array.Empty<ModularSpriteBoneDefinition>();
        [SerializeField] private ModularSpritePartDefinition[] parts =
            Array.Empty<ModularSpritePartDefinition>();
        [SerializeField] private ModularSpriteFacingLayerOrder[] facingLayerOrders =
            Array.Empty<ModularSpriteFacingLayerOrder>();

        public int PixelsPerUnit => pixelsPerUnit;
        public IReadOnlyList<ModularSpriteBoneDefinition> Bones => bones;
        public IReadOnlyList<ModularSpritePartDefinition> Parts => parts;
        public IReadOnlyList<ModularSpriteFacingLayerOrder> FacingLayerOrders =>
            facingLayerOrders;

        public ModularSpriteRigData()
        {
        }

        public ModularSpriteRigData(
            int pixelsPerUnit,
            ModularSpriteBoneDefinition[] bones,
            ModularSpritePartDefinition[] parts,
            ModularSpriteFacingLayerOrder[] facingLayerOrders)
        {
            this.pixelsPerUnit = pixelsPerUnit;
            this.bones = bones != null
                ? (ModularSpriteBoneDefinition[])bones.Clone()
                : Array.Empty<ModularSpriteBoneDefinition>();
            this.parts = parts != null
                ? (ModularSpritePartDefinition[])parts.Clone()
                : Array.Empty<ModularSpritePartDefinition>();
            this.facingLayerOrders = facingLayerOrders != null
                ? (ModularSpriteFacingLayerOrder[])facingLayerOrders.Clone()
                : Array.Empty<ModularSpriteFacingLayerOrder>();
        }

        public bool TryGetLayerOrder(
            ModularSpriteFacing8 facing,
            out ModularSpriteFacingLayerOrder layerOrder)
        {
            if (facingLayerOrders != null)
            {
                for (int index = 0; index < facingLayerOrders.Length; index++)
                {
                    ModularSpriteFacingLayerOrder candidate = facingLayerOrders[index];
                    if (candidate != null && candidate.Facing == facing)
                    {
                        layerOrder = candidate;
                        return true;
                    }
                }
            }

            layerOrder = null;
            return false;
        }

        public bool TryValidate(out string error)
        {
            if (pixelsPerUnit <= 0)
            {
                error = "Pixels per unit must be greater than zero.";
                return false;
            }

            if (bones == null || bones.Length == 0)
            {
                error = "The rig must contain at least one bone.";
                return false;
            }

            if (!TryValidateBones(out error) || !TryValidateParts(out error) ||
                !TryValidateFacingLayerOrders(out error))
            {
                return false;
            }

            error = null;
            return true;
        }

        private bool TryValidateBones(out string error)
        {
            var ids = new HashSet<string>(StringComparer.Ordinal);
            int rootCount = 0;

            for (int index = 0; index < bones.Length; index++)
            {
                ModularSpriteBoneDefinition bone = bones[index];
                if (bone == null)
                {
                    error = $"Bone {index} is null.";
                    return false;
                }

                if (string.IsNullOrWhiteSpace(bone.Id))
                {
                    error = $"Bone {index} has no stable ID.";
                    return false;
                }

                if (!ids.Add(bone.Id))
                {
                    error = $"Bone ID '{bone.Id}' is duplicated.";
                    return false;
                }

                if (!IsFinite(bone.BindRotationDegrees))
                {
                    error = $"Bone '{bone.Id}' has a non-finite bind rotation.";
                    return false;
                }

                if (bone.ParentIndex == -1)
                {
                    rootCount++;
                    continue;
                }

                if (bone.ParentIndex < -1)
                {
                    error = $"Bone '{bone.Id}' has invalid parent index {bone.ParentIndex}.";
                    return false;
                }

                if (bone.ParentIndex >= bones.Length)
                {
                    error = $"Bone '{bone.Id}' has parent index {bone.ParentIndex} outside the rig.";
                    return false;
                }
            }

            var visitStates = new byte[bones.Length];
            for (int index = 0; index < bones.Length; index++)
            {
                if (!TryVisitBone(index, visitStates, out error))
                {
                    return false;
                }
            }

            if (rootCount != 1)
            {
                error = $"The rig must contain exactly one root bone, but found {rootCount}.";
                return false;
            }

            for (int index = 0; index < bones.Length; index++)
            {
                int parentIndex = bones[index].ParentIndex;
                if (parentIndex >= index)
                {
                    error = $"Bone '{bones[index].Id}' must appear after its parent so poses can be solved without per-frame hierarchy allocation.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private bool TryVisitBone(int index, byte[] visitStates, out string error)
        {
            if (visitStates[index] == 2)
            {
                error = null;
                return true;
            }

            if (visitStates[index] == 1)
            {
                error = $"Bone hierarchy contains a cycle at '{bones[index].Id}'.";
                return false;
            }

            visitStates[index] = 1;
            int parentIndex = bones[index].ParentIndex;
            if (parentIndex >= 0 && !TryVisitBone(parentIndex, visitStates, out error))
            {
                return false;
            }

            visitStates[index] = 2;
            error = null;
            return true;
        }

        private bool TryValidateParts(out string error)
        {
            if (parts == null || parts.Length == 0)
            {
                error = "The rig must contain at least one render part.";
                return false;
            }

            var ids = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < parts.Length; index++)
            {
                ModularSpritePartDefinition part = parts[index];
                if (part == null)
                {
                    error = $"Part {index} is null.";
                    return false;
                }

                if (string.IsNullOrWhiteSpace(part.Id))
                {
                    error = $"Part {index} has no stable ID.";
                    return false;
                }

                if (!ids.Add(part.Id))
                {
                    error = $"Part ID '{part.Id}' is duplicated.";
                    return false;
                }

                if (part.BoneIndex < 0 || part.BoneIndex >= bones.Length)
                {
                    error = $"Part '{part.Id}' targets bone index {part.BoneIndex} outside the rig.";
                    return false;
                }
            }

            error = null;
            return true;
        }

        private bool TryValidateFacingLayerOrders(out string error)
        {
            if (facingLayerOrders == null || facingLayerOrders.Length != FacingCount)
            {
                error = $"The rig must define one layer order for each of the {FacingCount} facings.";
                return false;
            }

            var partIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < parts.Length; index++)
            {
                partIds.Add(parts[index].Id);
            }

            var facings = new HashSet<ModularSpriteFacing8>();
            for (int index = 0; index < facingLayerOrders.Length; index++)
            {
                ModularSpriteFacingLayerOrder layerOrder = facingLayerOrders[index];
                if (layerOrder == null)
                {
                    error = $"Facing layer order {index} is null.";
                    return false;
                }

                if (!IsDefinedFacing(layerOrder.Facing) || !facings.Add(layerOrder.Facing))
                {
                    error = $"Facing '{layerOrder.Facing}' is invalid or duplicated.";
                    return false;
                }

                IReadOnlyList<string> orderedPartIds = layerOrder.PartIdsBackToFront;
                if (orderedPartIds == null || orderedPartIds.Count != parts.Length)
                {
                    error = $"Facing '{layerOrder.Facing}' must order all {parts.Length} parts exactly once.";
                    return false;
                }

                var orderedIds = new HashSet<string>(StringComparer.Ordinal);
                for (int partIndex = 0; partIndex < orderedPartIds.Count; partIndex++)
                {
                    string partId = orderedPartIds[partIndex];
                    if (string.IsNullOrWhiteSpace(partId) || !partIds.Contains(partId))
                    {
                        error = $"Facing '{layerOrder.Facing}' references unknown part '{partId}'.";
                        return false;
                    }

                    if (!orderedIds.Add(partId))
                    {
                        error = $"Facing '{layerOrder.Facing}' orders part '{partId}' more than once.";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        private static bool IsDefinedFacing(ModularSpriteFacing8 facing)
        {
            int value = (int)facing;
            return value >= 0 && value < FacingCount;
        }

        private static bool IsFinite(float value)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value);
        }
    }

    [CreateAssetMenu(
        fileName = "ModularSpriteRig",
        menuName = "Fantasy Survival/Character Presentation/Modular Sprite Rig")]
    public sealed class ModularSpriteRigDefinition : ScriptableObject
    {
        [SerializeField] private ModularSpriteRigData data = new ModularSpriteRigData();

        public ModularSpriteRigData Data => data;

        public bool TryValidate(out string error)
        {
            if (data == null)
            {
                error = "Rig data is missing.";
                return false;
            }

            return data.TryValidate(out error);
        }
    }
}
