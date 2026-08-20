using FantasySurvival.SceneFlow;
using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.SaveSystem
{
    [DefaultExecutionOrder(1000)]
    [DisallowMultipleComponent]
    public sealed class BasePersistenceController : MonoBehaviour
    {
        private const float StatusDuration = 8f;

        private string statusMessage = "F5 or Save Slot 1 to save the current inventory.";
        private float statusUntil;

        private void Start()
        {
            ApplyPendingStartRequest();
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F5))
            {
                SaveSlotOne();
            }
        }

        private void OnGUI()
        {
            const float width = 300f;
            const float height = 112f;
            Rect panel = new Rect(Screen.width - width - 16f, 16f, width, height);
            GUI.Box(panel, "Save Prototype");

            if (GUI.Button(new Rect(panel.x + 12f, panel.y + 28f, width - 24f, 30f), "Save Slot 1  (F5)"))
            {
                SaveSlotOne();
            }

            string visibleStatus = Time.unscaledTime <= statusUntil || statusUntil <= 0f
                ? statusMessage
                : "F5 or Save Slot 1 to save.";
            GUI.Label(new Rect(panel.x + 12f, panel.y + 64f, width - 24f, 42f), visibleStatus);
        }

        public bool SaveSlotOne()
        {
            if (!TryGetInventory(out InventoryUIManager inventory, out string error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            inventory.CloseAllInventories();

            if (!InventorySaveCodec.TryCapture(
                    inventory.PlayerInventoryData,
                    inventory.ItemDatabase,
                    out InventoryGridSaveData inventorySave,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            GameSaveData saveData = GameSaveManager.CreateSave(inventorySave);
            if (!GameSaveManager.TryWriteSlotOne(
                    saveData,
                    inventory.ItemDatabase,
                    inventory.PlayerInventoryData.CapacityWidth,
                    inventory.PlayerInventoryData.CapacityHeight,
                    out error))
            {
                SetStatus($"Save failed: {error}", true);
                return false;
            }

            SetStatus($"Saved slot 1 at {GameSaveManager.GetDisplayTimestamp(saveData)}", false);
            return true;
        }

        private void ApplyPendingStartRequest()
        {
            if (!GameStartRequest.TryConsume(out GameStartMode mode, out GameSaveData saveData))
            {
                return;
            }

            if (!TryGetInventory(out InventoryUIManager inventory, out string error))
            {
                SetStatus($"Start request failed: {error}", true);
                return;
            }

            if (mode == GameStartMode.NewGame)
            {
                if (!inventory.TryResetToStartingInventory(out error))
                {
                    SetStatus($"New game failed: {error}", true);
                    return;
                }

                SetStatus("New game started at the base. Existing save slot was not overwritten.", false);
                return;
            }

            if (mode != GameStartMode.LoadGame || saveData == null)
            {
                SetStatus("Start request was invalid.", true);
                return;
            }

            StandardStashViewData current = inventory.PlayerInventoryData;
            if (current == null)
            {
                SetStatus("Load failed: current inventory configuration is missing.", true);
                return;
            }

            if (!InventorySaveCodec.TryRestore(
                    saveData.playerInventory,
                    inventory.ItemDatabase,
                    current.CapacityWidth,
                    current.CapacityHeight,
                    out StandardStashViewData restored,
                    out error))
            {
                SetStatus($"Load failed; current inventory was kept: {error}", true);
                return;
            }

            if (!inventory.TryReplacePlayerInventory(restored, out error))
            {
                SetStatus($"Load failed; current inventory was kept: {error}", true);
                return;
            }

            SetStatus($"Loaded slot 1 from {GameSaveManager.GetDisplayTimestamp(saveData)}", false);
        }

        private static bool TryGetInventory(out InventoryUIManager inventory, out string error)
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            inventory = shell != null ? shell.InventoryUI : null;
            if (inventory == null || !inventory.isActiveAndEnabled)
            {
                error = "persistent player inventory is unavailable.";
                return false;
            }

            error = null;
            return true;
        }

        private void SetStatus(string message, bool isError)
        {
            statusMessage = message;
            statusUntil = Time.unscaledTime + StatusDuration;

            if (isError)
            {
                Debug.LogError(message, this);
            }
            else
            {
                Debug.Log(message, this);
            }
        }
    }
}
