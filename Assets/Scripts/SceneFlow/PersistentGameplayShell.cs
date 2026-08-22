using System;
using FantasySurvival.Interaction;
using UnityEngine;
using UnityEngine.EventSystems;

namespace FantasySurvival.SceneFlow
{
    /// <summary>
    /// Keeps the actual gameplay Player, camera, inventory UI and input objects alive
    /// while gameplay scenes are replaced.
    /// </summary>
    [DefaultExecutionOrder(-10000)]
    [DisallowMultipleComponent]
    public sealed class PersistentGameplayShell : MonoBehaviour
    {
        public static PersistentGameplayShell Instance { get; private set; }

        [SerializeField] private Transform playerTransform;
        [SerializeField] private Camera playerCamera;
        [SerializeField] private EventSystem eventSystem;
        [SerializeField] private InventoryUIManager inventoryUI;
        [SerializeField] private PlayerMovement playerMovement;
        [SerializeField] private PlayerInteractor playerInteractor;

        private bool travelPrepared;
        private bool movementWasEnabled;
        private bool inventoryInputWasBlocked;
        private bool interactionWasBlocked;

        public Transform PlayerTransform => playerTransform;
        public Camera PlayerCamera => playerCamera;
        public EventSystem PlayerEventSystem => eventSystem;
        public InventoryUIManager InventoryUI => inventoryUI;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Instance = null;
        }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                gameObject.SetActive(false);
                Destroy(gameObject);
                return;
            }

            Instance = this;
            DontDestroyOnLoad(gameObject);

            if (!HasRequiredReferences())
            {
                Debug.LogError("PersistentGameplayShell has missing required references.", this);
            }
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        public bool PrepareForTravel()
        {
            if (travelPrepared)
            {
                return true;
            }

            if (!HasRequiredReferences())
            {
                Debug.LogError("Cannot travel because PersistentGameplayShell has missing required references.", this);
                return false;
            }

            movementWasEnabled = playerMovement.enabled;
            inventoryInputWasBlocked = inventoryUI.InputBlocked;
            interactionWasBlocked = playerInteractor.InteractionBlocked;
            travelPrepared = true;

            try
            {
                if (!inventoryUI.CloseAllInventories())
                {
                    Debug.LogError("Cannot travel because the active inventory drag could not be restored.", this);
                    RestoreTravelState();
                    return false;
                }
                eventSystem.SetSelectedGameObject(null);
                playerMovement.enabled = false;
                inventoryUI.SetInputBlocked(true);
                playerInteractor.SetInteractionBlocked(true);
                return true;
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                RestoreTravelState();
                return false;
            }
        }

        public void FinishArrival()
        {
            RestoreTravelState();
        }

        public void CancelTravelPreparation()
        {
            RestoreTravelState();
        }

        private void RestoreTravelState()
        {
            if (!travelPrepared)
            {
                return;
            }

            if (eventSystem != null)
            {
                eventSystem.SetSelectedGameObject(null);
            }

            if (playerMovement != null)
            {
                playerMovement.enabled = movementWasEnabled;
            }
            if (inventoryUI != null)
            {
                inventoryUI.SetInputBlocked(inventoryInputWasBlocked);
            }
            if (playerInteractor != null)
            {
                playerInteractor.SetInteractionBlocked(interactionWasBlocked);
            }
            travelPrepared = false;
        }

        private bool HasRequiredReferences()
        {
            return playerTransform != null && playerCamera != null && eventSystem != null &&
                   inventoryUI != null && playerMovement != null && playerInteractor != null;
        }
    }
}
