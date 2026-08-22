using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    public sealed class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] private KeyCode interactionKey = KeyCode.E;
        [SerializeField, Min(0.1f)] private float interactionRange = 3f;
        [SerializeField] private bool showDebugPrompt = true;

        private const int NearbyColliderCapacity = 32;

        private readonly Collider[] nearbyColliders = new Collider[NearbyColliderCapacity];
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
            int hitCount = Physics.OverlapSphereNonAlloc(
                transform.position,
                interactionRange,
                nearbyColliders,
                Physics.AllLayers,
                QueryTriggerInteraction.Collide);

            for (int i = 0; i < hitCount; i++)
            {
                Collider nearbyCollider = nearbyColliders[i];
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

            currentInteractable = nearest;
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
