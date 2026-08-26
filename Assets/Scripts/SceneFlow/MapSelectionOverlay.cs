using System.Collections;
using FantasySurvival.Interaction;
using FantasySurvival.Raids;
using UnityEngine;

namespace FantasySurvival.SceneFlow
{
    [DisallowMultipleComponent]
    public sealed class MapSelectionOverlay : MonoBehaviour
    {
        [SerializeField] private string destinationScene = "GameMapTest";
        [SerializeField] private string destinationSpawnId = "RaidEntry";
        [SerializeField] private string mapDisplayName = "GameMapTest";

        private PlayerInteractor sourceInteractor;
        private PlayerMovement sourceMovement;
        private InventoryUIManager sourceInventoryUI;
        private GameplayEscapeMenuController escapeMenu;
        private bool movementWasEnabled;
        private bool inventoryInputWasBlocked;
        private bool isVisible;

        public bool IsVisible => isVisible;

        public void Show(PlayerInteractor interactor)
        {
            if (isVisible || interactor == null || DirectSceneTravel.IsLoading)
            {
                return;
            }

            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            GameplayEscapeMenuController inputOwner = shell != null ? shell.EscapeMenu : null;
            if (inputOwner == null || !inputOwner.TryRegisterMapSelectionOverlay(this))
            {
                Debug.LogError("Map selection requires the persistent ESC menu input owner.", this);
                return;
            }

            escapeMenu = inputOwner;
            // A persistent quest dialog owns an InventoryUI input lock. Close it
            // before snapshotting the map overlay's previous lock state so its
            // cancellation cannot restore a stale value after this overlay opens.
            shell.QuestPanel?.TryClose();
            sourceInteractor = interactor;
            sourceMovement = interactor.GetComponent<PlayerMovement>();
            sourceInventoryUI = interactor.GetComponent<InventoryUIManager>();
            movementWasEnabled = sourceMovement != null && sourceMovement.enabled;
            inventoryInputWasBlocked = sourceInventoryUI != null && sourceInventoryUI.InputBlocked;

            sourceInteractor.SetInteractionBlocked(true);
            if (sourceMovement != null)
            {
                sourceMovement.enabled = false;
            }
            if (sourceInventoryUI != null)
            {
                sourceInventoryUI.SetInputBlocked(true);
            }

            isVisible = true;
        }

        public void Cancel()
        {
            CloseOverlay();
        }

        public bool SelectConfiguredMap()
        {
            if (!isVisible)
            {
                return false;
            }

            PlayerInteractor previousInteractor = sourceInteractor;
            CloseOverlay();

            RaidSession raidSession = PersistentGameplayShell.Instance != null
                ? PersistentGameplayShell.Instance.RaidSession
                : null;
            if (raidSession != null && raidSession.TryBeginRaid(destinationScene, destinationSpawnId))
            {
                return true;
            }

            if (previousInteractor != null)
            {
                StartCoroutine(ReopenAfterTravelCleanup(previousInteractor));
            }

            return false;
        }

        private IEnumerator ReopenAfterTravelCleanup(PlayerInteractor interactor)
        {
            while (DirectSceneTravel.IsLoading)
            {
                yield return null;
            }

            if (isActiveAndEnabled && interactor != null)
            {
                Show(interactor);
            }
        }

        private void OnDisable()
        {
            CloseOverlay();
        }

        private void CloseOverlay()
        {
            if (!isVisible && sourceInteractor == null && sourceMovement == null &&
                sourceInventoryUI == null && escapeMenu == null)
            {
                return;
            }

            isVisible = false;

            if (sourceInteractor != null)
            {
                sourceInteractor.SetInteractionBlocked(false);
            }

            if (sourceMovement != null)
            {
                sourceMovement.enabled = movementWasEnabled;
            }
            if (sourceInventoryUI != null)
            {
                sourceInventoryUI.SetInputBlocked(inventoryInputWasBlocked);
            }

            sourceInteractor = null;
            sourceMovement = null;
            sourceInventoryUI = null;
            if (escapeMenu != null)
            {
                escapeMenu.UnregisterMapSelectionOverlay(this);
                escapeMenu = null;
            }
            movementWasEnabled = false;
            inventoryInputWasBlocked = false;
        }

        private void OnGUI()
        {
            if (!isVisible)
            {
                return;
            }

            const float width = 340f;
            const float height = 180f;
            var panel = new Rect((Screen.width - width) * 0.5f, (Screen.height - height) * 0.5f, width, height);

            GUI.depth = -100;
            GUI.Box(panel, "TEST MAP SELECTION");

            if (GUI.Button(new Rect(panel.x + 40f, panel.y + 55f, width - 80f, 45f), mapDisplayName))
            {
                SelectConfiguredMap();
            }

            if (GUI.Button(new Rect(panel.x + 40f, panel.y + 115f, width - 80f, 35f), "Cancel"))
            {
                Cancel();
            }
        }
    }
}
