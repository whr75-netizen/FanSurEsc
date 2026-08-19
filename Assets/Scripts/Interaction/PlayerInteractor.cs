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
            if (blocked)
            {
                currentInteractable = null;
            }
        }

        private void OnDisable()
        {
            currentInteractable = null;
            interactionBlocked = false;
        }

        private void RefreshCurrentInteractable()
        {
            if (interactionBlocked)
            {
                currentInteractable = null;
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
