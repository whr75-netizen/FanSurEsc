using UnityEngine;

namespace FantasySurvival.Interaction
{
    public abstract class Interactable : MonoBehaviour
    {
        public abstract string InteractionPrompt { get; }

        public virtual bool CanInteract(PlayerInteractor interactor)
        {
            return interactor != null && isActiveAndEnabled && gameObject.activeInHierarchy;
        }

        public abstract void Interact(PlayerInteractor interactor);
    }
}
