using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Collider))]
    public sealed class ReturnPortalInteractable : Interactable
    {
        [SerializeField] private string destinationScene = "GameMap1";
        [SerializeField] private string destinationSpawnId = "BaseReturn";

        public override string InteractionPrompt => "Return To GameMap1";

        public override bool CanInteract(PlayerInteractor interactor)
        {
            return base.CanInteract(interactor) && !DirectSceneTravel.IsLoading;
        }

        public override void Interact(PlayerInteractor interactor)
        {
            DirectSceneTravel.TryLoad(destinationScene, destinationSpawnId);
        }
    }
}
