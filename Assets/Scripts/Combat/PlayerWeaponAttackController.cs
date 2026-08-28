using System.Collections.Generic;
using FantasySurvival.Actions;
using FantasySurvival.AI;
using FantasySurvival.Controls;
using FantasySurvival.Inventory;
using UnityEngine;
using UnityEngine.EventSystems;

namespace FantasySurvival.Combat
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PlayerActionController))]
    public sealed class PlayerWeaponAttackController : MonoBehaviour
    {
        private const string ReloadActionId = "weapon.reload";
        private const int RaycastBufferSize = 32;
        private const float MinAimDirectionSqrMagnitude = 0.0001f;

        [SerializeField] private PlayerWeaponController weaponController;
        [SerializeField] private InventoryUIManager inventoryManager;
        [SerializeField] private Camera aimCamera;
        [SerializeField] private Transform rayOrigin;
        [SerializeField] private EventSystem pointerEventSystem;
        [SerializeField] private WeaponAttackAudioFeedback audioFeedback;
        [SerializeField] private LayerMask hitMask = ~0;
        private readonly Dictionary<InventoryItemData, WeaponFireCadence> weaponCadences =
            new Dictionary<InventoryItemData, WeaponFireCadence>();
        private readonly RaycastHit[] raycastHits = new RaycastHit[RaycastBufferSize];
        private PlayerActionController actionController;

        public float NextAllowedFireTime
        {
            get
            {
                InventoryItemData activeWeapon = weaponController != null
                    ? weaponController.ActiveWeapon
                    : null;
                return activeWeapon != null && weaponCadences.TryGetValue(activeWeapon, out WeaponFireCadence cadence)
                    ? cadence.NextAllowedFireTime
                    : 0f;
            }
        }

        private void Awake()
        {
            actionController = GetComponent<PlayerActionController>();
            if (HasRequiredReferences())
            {
                return;
            }

            Debug.LogError(
                $"{nameof(PlayerWeaponAttackController)} on '{name}' has missing required references.",
                this);
            enabled = false;
        }

        private void OnDisable()
        {
            actionController?.TryCancel(
                this,
                PlayerActionCancelReason.ControllerDisabled);
            weaponCadences.Clear();
        }

        private void Update()
        {
            ProcessReloadInput(
                GameInputBindings.WasPressedThisFrame(GameInputActionId.RotateItem));
            ProcessFireInput(
                GameInputBindings.WasPressedThisFrame(GameInputActionId.Attack),
                GameInputBindings.IsPressed(GameInputActionId.Attack),
                Input.mousePosition,
                Time.time);
        }

        public bool ProcessFireInput(
            bool pressedThisFrame,
            bool held,
            Vector2 screenPosition,
            float currentTime)
        {
            if (!CanReceiveAttackInput())
            {
                return false;
            }

            InventoryItemData activeWeapon = weaponController.ActiveWeapon;
            ItemDefinition definition = activeWeapon?.Definition;
            if (definition == null || !definition.IsWeapon)
            {
                return false;
            }

            bool attackRequested = definition.WeaponFireMode == WeaponFireMode.Automatic
                ? held
                : pressedThisFrame;
            if (!attackRequested)
            {
                return false;
            }

            // A valid gameplay attack input supersedes the timed action, but the
            // weapon's own aim and cadence rules still decide whether a shot fires.
            actionController.CancelActive(PlayerActionCancelReason.AttackInput);

            if (!TryGetShotDirection(screenPosition, out Vector3 shotDirection))
            {
                return false;
            }

            WeaponFireCadence cadence = GetOrCreateCadence(activeWeapon);
            if (activeWeapon.LoadedAmmunition <= 0)
            {
                return false;
            }

            if (!cadence.TryConsume(
                    definition.WeaponFireMode,
                    pressedThisFrame,
                    held,
                    currentTime,
                    definition.RoundsPerMinute))
            {
                return false;
            }

            PlayerInventoryState playerState = inventoryManager.PlayerState;
            if (playerState == null ||
                !playerState.TryConsumeLoadedRound(activeWeapon, out _))
            {
                return false;
            }

            EmitRaycastShot(definition, shotDirection);
            return true;
        }

        public bool ProcessReloadInput(bool pressedThisFrame)
        {
            if (!pressedThisFrame || !CanReceiveGameplayActionInput())
            {
                return false;
            }

            InventoryItemData activeWeapon = weaponController.ActiveWeapon;
            PlayerInventoryState playerState = inventoryManager.PlayerState;
            if (activeWeapon?.Definition == null || !activeWeapon.Definition.IsWeapon ||
                playerState == null ||
                !playerState.TryGetReloadableRoundCount(
                    activeWeapon,
                    out int reloadableRounds,
                    out _) ||
                reloadableRounds <= 0)
            {
                return false;
            }

            if (actionController.IsActionOwnedBy(this))
            {
                return false;
            }

            if (actionController.IsBusy)
            {
                actionController.CancelActive(PlayerActionCancelReason.Requested);
            }

            return actionController.TryBegin(
                ReloadActionId,
                this,
                activeWeapon.Definition.ReloadDurationSeconds,
                () => CanContinueReload(playerState, activeWeapon),
                () => CompleteReload(playerState, activeWeapon));
        }

        private bool CanContinueReload(
            PlayerInventoryState expectedPlayerState,
            InventoryItemData expectedWeapon)
        {
            return expectedPlayerState != null && expectedWeapon != null &&
                   ReferenceEquals(inventoryManager.PlayerState, expectedPlayerState) &&
                   ReferenceEquals(weaponController.ActiveWeapon, expectedWeapon) &&
                   ReferenceEquals(expectedWeapon.InventoryOwner, expectedPlayerState.Equipment);
        }

        private void CompleteReload(
            PlayerInventoryState expectedPlayerState,
            InventoryItemData expectedWeapon)
        {
            if (!CanContinueReload(expectedPlayerState, expectedWeapon))
            {
                return;
            }

            if (!expectedPlayerState.TryReloadWeapon(
                    expectedWeapon,
                    out _,
                    out _))
            {
                return;
            }

            inventoryManager.RefreshPlayerItemPresentation(expectedPlayerState);
        }

        private WeaponFireCadence GetOrCreateCadence(InventoryItemData weapon)
        {
            if (weaponCadences.TryGetValue(weapon, out WeaponFireCadence cadence))
            {
                return cadence;
            }

            cadence = new WeaponFireCadence();
            weaponCadences.Add(weapon, cadence);
            return cadence;
        }

        private bool CanReceiveAttackInput()
        {
            if (!CanReceiveGameplayActionInput())
            {
                return false;
            }

            return pointerEventSystem == null || !pointerEventSystem.IsPointerOverGameObject();
        }

        private bool CanReceiveGameplayActionInput()
        {
            return Time.timeScale > 0f && !inventoryManager.BlocksGameplayInput;
        }

        private bool TryGetShotDirection(Vector2 screenPosition, out Vector3 shotDirection)
        {
            Ray screenRay = aimCamera.ScreenPointToRay(screenPosition);
            var attackPlane = new Plane(Vector3.up, rayOrigin.position);
            if (!attackPlane.Raycast(screenRay, out float enter))
            {
                shotDirection = default;
                return false;
            }

            shotDirection = screenRay.GetPoint(enter) - rayOrigin.position;
            shotDirection.y = 0f;
            if (shotDirection.sqrMagnitude <= MinAimDirectionSqrMagnitude)
            {
                shotDirection = default;
                return false;
            }

            shotDirection.Normalize();
            return true;
        }

        private void EmitRaycastShot(ItemDefinition definition, Vector3 direction)
        {
            audioFeedback?.PlayFire();

            Vector3 origin = rayOrigin.position;
            TryApplyRaycastDamage(definition, direction, origin);

            WorldStimulusChannel.Emit(new WorldStimulus(
                WorldStimulusKind.GunshotSound,
                WorldStimulusResponse.Investigate,
                origin,
                definition.WeaponNoiseRadius,
                gameObject));
        }

        private void TryApplyRaycastDamage(
            ItemDefinition definition,
            Vector3 direction,
            Vector3 origin)
        {
            int hitCount = Physics.RaycastNonAlloc(
                origin,
                direction,
                raycastHits,
                definition.WeaponRange,
                hitMask,
                QueryTriggerInteraction.Collide);

            RaycastHit[] hits = raycastHits;
            if (hitCount == raycastHits.Length)
            {
                // The non-alloc buffer cannot prove it contains the nearest hit when full.
                // Allocate only in this dense edge case so a wall cannot be skipped.
                hits = Physics.RaycastAll(
                    origin,
                    direction,
                    definition.WeaponRange,
                    hitMask,
                    QueryTriggerInteraction.Collide);
                hitCount = hits.Length;
            }

            float nearestDistance = float.PositiveInfinity;
            IDamageable nearestDamageable = null;
            RaycastHit nearestHit = default;
            bool foundBlockingHit = false;

            for (int index = 0; index < hitCount; index++)
            {
                RaycastHit hit = hits[index];
                Collider hitCollider = hit.collider;
                if (hitCollider == null || hitCollider.transform.IsChildOf(transform))
                {
                    continue;
                }

                IDamageable damageable = hitCollider.GetComponentInParent<IDamageable>();
                if (hitCollider.isTrigger &&
                    (damageable == null || !damageable.IsAlive))
                {
                    // Utility triggers and dead corpse-loot triggers must not become
                    // invisible walls in front of a living target.
                    continue;
                }

                if (hit.distance >= nearestDistance)
                {
                    continue;
                }

                nearestDistance = hit.distance;
                nearestDamageable = damageable;
                nearestHit = hit;
                foundBlockingHit = true;
            }

            if (!foundBlockingHit || nearestDamageable == null || !nearestDamageable.IsAlive)
            {
                return;
            }

            DamageResult result = nearestDamageable.ApplyDamage(
                new DamageContext(definition.WeaponDamage, gameObject, nearestHit.point));
            if (result.WasApplied)
            {
                audioFeedback?.PlayHit();
            }
        }

        private bool HasRequiredReferences()
        {
            return actionController != null && weaponController != null && inventoryManager != null &&
                   aimCamera != null && rayOrigin != null;
        }
    }
}
