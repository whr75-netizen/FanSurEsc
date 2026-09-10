using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation.ModularSprites
{
    /// <summary>
    /// Displays authored parts in the actor's local XY plane. Sprite pivots are their
    /// attachment points; rig and motion assets remain the source of pose data.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class ModularSpriteActor : MonoBehaviour
    {
        [SerializeField] private ModularSpriteRigDefinition rig;
        [SerializeField] private ModularSpriteSkinDefinition skin;
        [SerializeField] private ModularSpriteMotionDefinition motion;
        [SerializeField] private Material unlitMaterial;
        [SerializeField] private ModularSpriteFacing8 facing = ModularSpriteFacing8.South;
        [SerializeField] private bool autoPlay = true;

        private GameObject[] generatedParts = Array.Empty<GameObject>();
        private SpriteRenderer[] renderers = Array.Empty<SpriteRenderer>();
        private ModularSpriteSkinPart[] skinParts = Array.Empty<ModularSpriteSkinPart>();
        private ModularSpriteBonePose[] localPoses = Array.Empty<ModularSpriteBonePose>();
        private ModularSpriteSolvedBonePose[] solvedPoses = Array.Empty<ModularSpriteSolvedBonePose>();
        private readonly Dictionary<string, int> partIndices =
            new Dictionary<string, int>(StringComparer.Ordinal);
        private double elapsedSeconds;
        private int sampledFrameIndex = -1;
        private ModularSpriteFacing8 appliedFacing = (ModularSpriteFacing8)(-1);
        private bool initialized;

        public bool IsInitialized => initialized;
        public string LastError { get; private set; }
        public int SampledFrameIndex => sampledFrameIndex;
        public bool AutoPlay
        {
            get => autoPlay;
            set => autoPlay = value;
        }

        public ModularSpriteFacing8 Facing
        {
            get => facing;
            set
            {
                facing = value;
                if (initialized)
                {
                    SampleAt(elapsedSeconds);
                }
            }
        }

        public bool Configure(
            ModularSpriteRigDefinition rigDefinition,
            ModularSpriteSkinDefinition skinDefinition,
            ModularSpriteMotionDefinition motionDefinition,
            Material material = null)
        {
            rig = rigDefinition;
            skin = skinDefinition;
            motion = motionDefinition;
            unlitMaterial = material;
            elapsedSeconds = 0d;
            return Initialize();
        }

        public bool Initialize()
        {
            ReleaseGeneratedParts();
            if (rig == null || skin == null || motion == null)
            {
                return Fail("Rig, skin, and motion references are required.");
            }

            if (!rig.TryValidate(out string error) ||
                !skin.TryValidate(rig, false, out error) ||
                !motion.TryValidate(rig, out error))
            {
                return Fail(error);
            }

            int partCount = rig.Data.Parts.Count;
            generatedParts = new GameObject[partCount];
            renderers = new SpriteRenderer[partCount];
            skinParts = new ModularSpriteSkinPart[partCount];
            localPoses = new ModularSpriteBonePose[rig.Data.Bones.Count];
            solvedPoses = new ModularSpriteSolvedBonePose[rig.Data.Bones.Count];
            for (int index = 0; index < partCount; index++)
            {
                ModularSpritePartDefinition part = rig.Data.Parts[index];
                skin.Data.TryGetPart(part.Id, out skinParts[index]);
                partIndices.Add(part.Id, index);

                // Generated presentation must not become additional authored scene data.
                var partObject = new GameObject("Sprite Part - " + part.Id)
                {
                    hideFlags = HideFlags.DontSave,
                    layer = gameObject.layer
                };
                generatedParts[index] = partObject;
                partObject.transform.SetParent(transform, false);
                SpriteRenderer partRenderer = partObject.AddComponent<SpriteRenderer>();
                partRenderer.enabled = false;
                if (unlitMaterial != null)
                {
                    partRenderer.sharedMaterial = unlitMaterial;
                }

                renderers[index] = partRenderer;
            }

            initialized = true;
            LastError = null;
            return SampleAt(elapsedSeconds);
        }

        public bool SampleAt(double seconds)
        {
            if (!initialized)
            {
                return false;
            }

            elapsedSeconds = double.IsNaN(seconds) || double.IsInfinity(seconds) || seconds < 0d
                ? 0d
                : seconds;
            if (facing != appliedFacing && !ApplyFacing())
            {
                return false;
            }

            int frameIndex = motion.Data.GetFrameIndex(elapsedSeconds);
            if (frameIndex == sampledFrameIndex)
            {
                return true;
            }

            if (!motion.Data.TrySample(elapsedSeconds, localPoses, out frameIndex, out string error) ||
                !ModularSpritePoseSolver.TrySolve(rig.Data, localPoses, solvedPoses, out error))
            {
                return Fail(error);
            }

            float unitsPerPixel = 1f / rig.Data.PixelsPerUnit;
            for (int index = 0; index < renderers.Length; index++)
            {
                SpriteRenderer partRenderer = renderers[index];
                if (partRenderer == null)
                {
                    return Fail("A generated sprite part was removed; initialize the actor again.");
                }

                ModularSpriteSolvedBonePose pose = solvedPoses[rig.Data.Parts[index].BoneIndex];
                Transform partTransform = partRenderer.transform;
                partTransform.localPosition = new Vector3(
                    pose.PositionPixels.x * unitsPerPixel,
                    pose.PositionPixels.y * unitsPerPixel,
                    0f);
                partTransform.localRotation = Quaternion.Euler(0f, 0f, pose.WorldRotationDegrees);
            }

            sampledFrameIndex = frameIndex;
            return true;
        }

        private bool ApplyFacing()
        {
            if (!rig.Data.TryGetLayerOrder(facing, out ModularSpriteFacingLayerOrder layerOrder))
            {
                return Fail("The requested facing has no rig layer order.");
            }

            for (int order = 0; order < layerOrder.PartIdsBackToFront.Count; order++)
            {
                int partIndex = partIndices[layerOrder.PartIdsBackToFront[order]];
                SpriteRenderer partRenderer = renderers[partIndex];
                if (partRenderer == null)
                {
                    return Fail("A generated sprite part was removed; initialize the actor again.");
                }

                bool hasSprite = skinParts[partIndex].TryGetSprite(facing, out Sprite sprite);
                partRenderer.sprite = sprite;
                partRenderer.sortingOrder = order;
                partRenderer.enabled = hasSprite && isActiveAndEnabled;
            }

            appliedFacing = facing;
            return true;
        }

        private void OnEnable()
        {
            // AddComponent can precede Configure, so unconfigured objects do no work.
            if (rig != null && skin != null && motion != null)
            {
                Initialize();
            }
        }

        private void Update()
        {
            if (initialized && autoPlay)
            {
                SampleAt(elapsedSeconds + Time.deltaTime);
            }
        }

        private void OnDisable()
        {
            ReleaseGeneratedParts();
        }

        private void OnDestroy()
        {
            ReleaseGeneratedParts();
        }

        private bool Fail(string error)
        {
            ReleaseGeneratedParts();
            LastError = error;
            Debug.LogError("Modular sprite actor: " + error, this);
            return false;
        }

        private void ReleaseGeneratedParts()
        {
            initialized = false;
            sampledFrameIndex = -1;
            appliedFacing = (ModularSpriteFacing8)(-1);
            for (int index = 0; index < generatedParts.Length; index++)
            {
                GameObject partObject = generatedParts[index];
                if (partObject == null)
                {
                    continue;
                }

                partObject.SetActive(false);
                // Preserve anything another author attached to a generated part.
                while (partObject.transform.childCount > 0)
                {
                    partObject.transform.GetChild(0).SetParent(transform, true);
                }

                if (Application.isPlaying)
                {
                    Destroy(partObject);
                }
                else
                {
                    DestroyImmediate(partObject);
                }
            }

            generatedParts = Array.Empty<GameObject>();
            renderers = Array.Empty<SpriteRenderer>();
            skinParts = Array.Empty<ModularSpriteSkinPart>();
            localPoses = Array.Empty<ModularSpriteBonePose>();
            solvedPoses = Array.Empty<ModularSpriteSolvedBonePose>();
            partIndices.Clear();
        }
    }
}
