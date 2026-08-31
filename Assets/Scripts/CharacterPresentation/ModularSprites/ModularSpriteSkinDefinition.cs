using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation.ModularSprites
{
    [Serializable]
    public sealed class ModularSpriteSkinPart
    {
        [SerializeField] private string partId = string.Empty;
        [SerializeField] private Sprite[] facingSprites =
            new Sprite[ModularSpriteRigData.FacingCount];

        public string PartId => partId;
        public IReadOnlyList<Sprite> FacingSprites => facingSprites;

        public ModularSpriteSkinPart()
        {
        }

        public ModularSpriteSkinPart(string partId, Sprite[] facingSprites)
        {
            this.partId = partId ?? string.Empty;
            this.facingSprites = facingSprites != null
                ? (Sprite[])facingSprites.Clone()
                : Array.Empty<Sprite>();
        }

        public bool TryGetSprite(ModularSpriteFacing8 facing, out Sprite sprite)
        {
            int index = (int)facing;
            if (facingSprites == null || index < 0 || index >= facingSprites.Length)
            {
                sprite = null;
                return false;
            }

            sprite = facingSprites[index];
            return sprite != null;
        }
    }

    [Serializable]
    public sealed class ModularSpriteSkinData
    {
        [SerializeField] private string id = string.Empty;
        [SerializeField] private ModularSpriteSkinPart[] parts =
            Array.Empty<ModularSpriteSkinPart>();

        public string Id => id;
        public IReadOnlyList<ModularSpriteSkinPart> Parts => parts;

        public ModularSpriteSkinData()
        {
        }

        public ModularSpriteSkinData(string id, ModularSpriteSkinPart[] parts)
        {
            this.id = id ?? string.Empty;
            this.parts = parts != null
                ? (ModularSpriteSkinPart[])parts.Clone()
                : Array.Empty<ModularSpriteSkinPart>();
        }

        public bool TryGetPart(string partId, out ModularSpriteSkinPart part)
        {
            if (parts != null)
            {
                for (int index = 0; index < parts.Length; index++)
                {
                    ModularSpriteSkinPart candidate = parts[index];
                    if (candidate != null &&
                        string.Equals(candidate.PartId, partId, StringComparison.Ordinal))
                    {
                        part = candidate;
                        return true;
                    }
                }
            }

            part = null;
            return false;
        }

        public bool TryValidate(
            ModularSpriteRigData rig,
            bool requireAssignedSprites,
            out string error)
        {
            if (rig == null)
            {
                error = "Skin requires a rig.";
                return false;
            }

            if (!rig.TryValidate(out error))
            {
                error = "Skin requires a valid rig. " + error;
                return false;
            }

            if (string.IsNullOrWhiteSpace(id))
            {
                error = "Skin has no stable ID.";
                return false;
            }

            if (parts == null || parts.Length != rig.Parts.Count)
            {
                error = $"Skin '{id}' must define all {rig.Parts.Count} rig parts exactly once.";
                return false;
            }

            var partIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < parts.Length; index++)
            {
                ModularSpriteSkinPart part = parts[index];
                if (part == null || string.IsNullOrWhiteSpace(part.PartId))
                {
                    error = $"Skin '{id}' part {index} has no stable ID.";
                    return false;
                }

                if (!partIds.Add(part.PartId))
                {
                    error = $"Skin '{id}' contains duplicate part '{part.PartId}'.";
                    return false;
                }

                if (part.FacingSprites == null ||
                    part.FacingSprites.Count != ModularSpriteRigData.FacingCount)
                {
                    error = $"Skin '{id}' part '{part.PartId}' must define {ModularSpriteRigData.FacingCount} facing sprite slots.";
                    return false;
                }

                for (int facingIndex = 0;
                     facingIndex < part.FacingSprites.Count;
                     facingIndex++)
                {
                    Sprite sprite = part.FacingSprites[facingIndex];
                    if (sprite == null)
                    {
                        if (requireAssignedSprites)
                        {
                            error = $"Skin '{id}' part '{part.PartId}' is missing facing {(ModularSpriteFacing8)facingIndex}.";
                            return false;
                        }

                        continue;
                    }

                    if (!Mathf.Approximately(sprite.pixelsPerUnit, rig.PixelsPerUnit))
                    {
                        error = $"Skin '{id}' part '{part.PartId}' facing {(ModularSpriteFacing8)facingIndex} uses {sprite.pixelsPerUnit} PPU instead of rig PPU {rig.PixelsPerUnit}.";
                        return false;
                    }
                }
            }

            for (int rigPartIndex = 0; rigPartIndex < rig.Parts.Count; rigPartIndex++)
            {
                string rigPartId = rig.Parts[rigPartIndex].Id;
                if (!partIds.Contains(rigPartId))
                {
                    error = $"Skin '{id}' is missing rig part '{rigPartId}'.";
                    return false;
                }
            }

            error = null;
            return true;
        }
    }

    [CreateAssetMenu(
        fileName = "ModularSpriteSkin",
        menuName = "Fantasy Survival/Character Presentation/Modular Sprite Skin")]
    public sealed class ModularSpriteSkinDefinition : ScriptableObject
    {
        [SerializeField] private ModularSpriteSkinData data = new ModularSpriteSkinData();

        public ModularSpriteSkinData Data => data;

        public bool TryValidate(
            ModularSpriteRigDefinition rig,
            bool requireAssignedSprites,
            out string error)
        {
            if (data == null || rig == null)
            {
                error = "Skin data and rig are required.";
                return false;
            }

            return data.TryValidate(rig.Data, requireAssignedSprites, out error);
        }
    }
}
