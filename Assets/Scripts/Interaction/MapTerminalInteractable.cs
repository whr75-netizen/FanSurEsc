using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Collider))]
    [RequireComponent(typeof(MapSelectionOverlay))]
    public sealed class MapTerminalInteractable : Interactable
    {
        private MapSelectionOverlay selectionOverlay;

        public override string InteractionPrompt => "Open Test Map Selection";

        private void Awake()
        {
            selectionOverlay = GetComponent<MapSelectionOverlay>();
        }

        public override void Interact(PlayerInteractor interactor)
        {
            if (selectionOverlay == null)
            {
                Debug.LogError("MapSelectionOverlay is missing.", this);
                return;
            }

            var inventoryUI = interactor.GetComponent<InventoryUIManager>();
            if (inventoryUI != null)
            {
                inventoryUI.CloseAllInventories();
            }

            selectionOverlay.Show(interactor);
        }
    }
}
