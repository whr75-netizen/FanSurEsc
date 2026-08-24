using UnityEngine;
using VariableInventorySystem;

namespace FantasySurvival.BaseBuilding
{
    [DisallowMultipleComponent]
    public sealed class BaseFurnitureInstance : MonoBehaviour
    {
        [Tooltip("Stable ID for this placed base object, for example core:home/chest_a.")]
        [SerializeField] private string persistentId;
        [SerializeField] private BaseFurnitureDefinition definition;
        [Tooltip("Optional storage capability. Leave empty for furniture without an inventory.")]
        [SerializeField] private Chest storageChest;

        private BaseFurnitureStateStore boundStore;
        private StandardStashViewData previousChestData;

        public string PersistentId => persistentId;
        public string DefinitionKey => definition != null ? definition.DefinitionKey : null;
        public BaseFurnitureDefinition Definition => definition;
        public Chest StorageChest => storageChest;
        public bool IsBound => boundStore != null;

        public bool TryValidateAuthoring(out string error)
        {
            if (!BaseContentKey.IsValid(persistentId))
            {
                error = $"Persistent ID '{persistentId}' must use a lowercase namespace:path key.";
                return false;
            }

            if (definition == null)
            {
                error = "Furniture definition is missing.";
                return false;
            }

            if (!definition.TryValidate(out error))
            {
                return false;
            }

            if (storageChest != null && storageChest.gameObject != gameObject)
            {
                error = "The storage Chest must be on the same GameObject as its furniture instance.";
                return false;
            }

            if (definition.HasStorage != (storageChest != null))
            {
                error = definition.HasStorage
                    ? "The furniture definition requires a storage Chest component."
                    : "The furniture has a storage Chest, but its definition does not declare storage.";
                return false;
            }

            if (storageChest != null &&
                (storageChest.chestWidth != definition.StorageWidth ||
                 storageChest.chestHeight != definition.StorageHeight))
            {
                error = $"Chest capacity {storageChest.chestWidth}x{storageChest.chestHeight} does not match " +
                        $"definition capacity {definition.StorageWidth}x{definition.StorageHeight}.";
                return false;
            }

            error = null;
            return true;
        }

        internal bool TryCreateInitialState(
            out BaseFurnitureRuntimeState state,
            out string error)
        {
            state = null;
            if (!TryValidateAuthoring(out error))
            {
                return false;
            }

            StandardStashViewData storage = null;
            if (storageChest != null &&
                !storageChest.TryCreateAuthoredInventory(out storage, out error))
            {
                return false;
            }

            state = new BaseFurnitureRuntimeState(persistentId, definition.DefinitionKey, storage);
            error = null;
            return true;
        }

        internal bool CanBind(BaseFurnitureRuntimeState state, out string error)
        {
            if (state == null || state.InstanceId != persistentId || state.DefinitionKey != DefinitionKey)
            {
                error = "Runtime furniture state does not match this placed instance.";
                return false;
            }

            if (storageChest == null)
            {
                if (state.Storage != null)
                {
                    error = "Saved storage data exists, but this furniture no longer has a Chest component.";
                    return false;
                }

                error = null;
                return true;
            }

            return storageChest.CanBindInventory(state.Storage, out error);
        }

        internal bool TryApplyBinding(
            BaseFurnitureStateStore store,
            BaseFurnitureRuntimeState state,
            out string error)
        {
            if (store == null)
            {
                error = "Base furniture state store is missing.";
                return false;
            }

            if (!CanBind(state, out error))
            {
                return false;
            }

            previousChestData = storageChest != null ? storageChest.chestInventoryData : null;
            if (storageChest != null && !storageChest.TryBindInventory(state.Storage, out error))
            {
                previousChestData = null;
                return false;
            }

            boundStore = store;
            error = null;
            return true;
        }

        internal void RollBackPendingBinding()
        {
            if (storageChest != null && previousChestData != null)
            {
                storageChest.TryBindInventory(previousChestData, out _);
            }

            boundStore = null;
            previousChestData = null;
        }

        private void OnDisable()
        {
            if (boundStore != null)
            {
                boundStore.ReleaseBinding(persistentId, this);
                boundStore = null;
            }

            previousChestData = null;
        }
    }
}
