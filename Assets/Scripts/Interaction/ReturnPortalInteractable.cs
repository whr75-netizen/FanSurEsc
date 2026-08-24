using FantasySurvival.Raids;
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

        public override string InteractionPrompt => "Extract And Return To Base";

        public override bool CanInteract(PlayerInteractor interactor)
        {
            RaidSession raidSession = PersistentGameplayShell.Instance != null
                ? PersistentGameplayShell.Instance.RaidSession
                : null;
            return base.CanInteract(interactor) &&
                   !DirectSceneTravel.IsLoading &&
                   raidSession != null &&
                   raidSession.IsRaidActive;
        }

        public override void Interact(PlayerInteractor interactor)
        {
            RaidSession raidSession = PersistentGameplayShell.Instance != null
                ? PersistentGameplayShell.Instance.RaidSession
                : null;
            if (raidSession == null ||
                !raidSession.TryResolveExtraction(destinationScene, destinationSpawnId))
            {
                Debug.LogWarning("Extraction request was rejected because no active raid was available.", this);
            }
        }
    }
}
