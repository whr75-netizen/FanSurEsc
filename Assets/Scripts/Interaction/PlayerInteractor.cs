using System;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    public sealed class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] private KeyCode interactionKey = KeyCode.E;
        [SerializeField, Min(0.1f)] private float interactionRange = 3f;
        [SerializeField] private bool showDebugPrompt = true;

        private const int InitialNearbyColliderCapacity = 32;
        private const int MaxPooledNearbyColliderCapacity = 256;

        private Collider[] nearbyColliders = new Collider[InitialNearbyColliderCapacity];
        private Interactable currentInteractable;
        private bool interactionBlocked;

        public Interactable CurrentInteractable => currentInteractable;
        public bool InteractionBlocked => interactionBlocked;
        public float InteractionRange => interactionRange;

        private void Update()
        {
            RefreshCurrentInteractable();

            if (!interactionBlocked && Input.GetKeyDown(interactionKey))
            {
                TryInteract();
            }
        }

        public bool TryInteract()
        {
            if (interactionBlocked)
            {
                return false;
            }

            RefreshCurrentInteractable();
            if (currentInteractable == null || !currentInteractable.CanInteract(this))
            {
                return false;
            }

            currentInteractable.Interact(this);
            return true;
        }

        public void SetInteractionBlocked(bool blocked)
        {
            interactionBlocked = blocked;
            if (blocked && TryCancelCurrentInteraction())
            {
                currentInteractable = null;
            }
        }

        private void OnDisable()
        {
            if (TryCancelCurrentInteraction())
            {
                currentInteractable = null;
            }

            interactionBlocked = false;
        }

        public bool IsWithinInteractionRange(Transform target)
        {
            if (target == null)
            {
                return false;
            }

            Vector3 offset = target.position - transform.position;
            return offset.sqrMagnitude <= interactionRange * interactionRange;
        }

        private void RefreshCurrentInteractable()
        {
            if (interactionBlocked)
            {
                if (TryCancelCurrentInteraction())
                {
                    currentInteractable = null;
                }

                return;
            }

            if (TryKeepCurrentInteraction())
            {
                return;
            }

            Interactable nearest = null;
            float nearestDistance = interactionRange;
            int hitCount;
            do
            {
                hitCount = Physics.OverlapSphereNonAlloc(
                    transform.position,
                    interactionRange,
                    nearbyColliders,
                    Physics.AllLayers,
                    QueryTriggerInteraction.Collide);

                if (hitCount < nearbyColliders.Length ||
                    nearbyColliders.Length >= MaxPooledNearbyColliderCapacity)
                {
                    break;
                }

                Array.Resize(
                    ref nearbyColliders,
                    Mathf.Min(nearbyColliders.Length * 2, MaxPooledNearbyColliderCapacity));
            }
            while (true);

            if (hitCount >= nearbyColliders.Length)
            {
                // Saturation is exceptional. Allocate only in this case so nearest-target
                // correctness is not silently lost in a collider-dense area.
                Collider[] completeResults = Physics.OverlapSphere(
                    transform.position,
                    interactionRange,
                    Physics.AllLayers,
                    QueryTriggerInteraction.Collide);
                SelectNearest(completeResults, completeResults.Length, ref nearest, ref nearestDistance);
                currentInteractable = nearest;
                return;
            }

            SelectNearest(nearbyColliders, hitCount, ref nearest, ref nearestDistance);
            currentInteractable = nearest;
        }

        private void SelectNearest(
            Collider[] colliders,
            int count,
            ref Interactable nearest,
            ref float nearestDistance)
        {
            for (int i = 0; i < count; i++)
            {
                Collider nearbyCollider = colliders[i];
                Interactable candidate = nearbyCollider != null
                    ? nearbyCollider.GetComponentInParent<Interactable>()
                    : null;

                if (candidate == null || !candidate.CanInteract(this))
                {
                    continue;
                }

                float distance = Vector3.Distance(transform.position, candidate.transform.position);
                if (distance <= nearestDistance)
                {
                    nearest = candidate;
                    nearestDistance = distance;
                }
            }
        }

        private bool TryKeepCurrentInteraction()
        {
            if (currentInteractable == null || !currentInteractable.IsInteractionActive(this))
            {
                return false;
            }

            if (currentInteractable.CanInteract(this) &&
                IsWithinInteractionRange(currentInteractable.transform))
            {
                return true;
            }

            if (!currentInteractable.TryCancelInteraction(this))
            {
                return true;
            }

            currentInteractable = null;
            return false;
        }

        private bool TryCancelCurrentInteraction()
        {
            if (currentInteractable == null || !currentInteractable.IsInteractionActive(this))
            {
                return true;
            }

            return currentInteractable.TryCancelInteraction(this);
        }

        private void OnGUI()
        {
            if (!showDebugPrompt || interactionBlocked || currentInteractable == null)
            {
                return;
            }

            const float width = 280f;
            const float height = 34f;
            var rect = new Rect((Screen.width - width) * 0.5f, Screen.height - 80f, width, height);
            GUI.Box(rect, $"[{interactionKey}] {currentInteractable.InteractionPrompt}");
        }
    }
}
