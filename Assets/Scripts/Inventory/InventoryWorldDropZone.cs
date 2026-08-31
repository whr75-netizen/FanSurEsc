using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    /// <summary>
    /// Transparent uGUI receiver behind all inventory panels. It is raycastable
    /// only during an ordinary pointer drag and only outside the configured panel
    /// rectangles, so invalid cells and panel padding keep their original rollback.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Image))]
    public sealed class InventoryWorldDropZone :
        MonoBehaviour,
        IDropHandler,
        ICanvasRaycastFilter
    {
        private StandardCore inventoryCore;
        private InventoryUIManager inventoryUI;
        private RectTransform[] blockedAreas = Array.Empty<RectTransform>();

        public void Configure(
            StandardCore core,
            InventoryUIManager owner,
            params RectTransform[] areas)
        {
            inventoryCore = core;
            inventoryUI = owner;
            blockedAreas = areas ?? Array.Empty<RectTransform>();

            Image image = GetComponent<Image>();
            image.color = Color.clear;
            image.raycastTarget = true;
        }

        public bool IsRaycastLocationValid(Vector2 screenPoint, Camera eventCamera)
        {
            if (inventoryCore == null || inventoryUI == null ||
                !inventoryUI.IsAnyInventoryOpen ||
                !inventoryCore.IsPointerDragCarryActive)
            {
                return false;
            }

            for (int index = 0; index < blockedAreas.Length; index++)
            {
                RectTransform area = blockedAreas[index];
                if (area != null && area.gameObject.activeInHierarchy &&
                    RectTransformUtility.RectangleContainsScreenPoint(
                        area,
                        screenPoint,
                        eventCamera))
                {
                    return false;
                }
            }

            return !inventoryCore.IsScreenPointOverRegisteredInventory(
                screenPoint,
                eventCamera);
        }

        public void OnDrop(PointerEventData eventData)
        {
            if (eventData == null ||
                !IsRaycastLocationValid(
                    eventData.position,
                    eventData.enterEventCamera))
            {
                return;
            }

            if (inventoryCore.TryDropPointerCarryToExternalReceiver())
            {
                inventoryCore.CloseAllCasePopups();
            }
        }
    }
}
