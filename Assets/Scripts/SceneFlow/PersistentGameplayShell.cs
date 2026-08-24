using System;
using FantasySurvival.Interaction;
using FantasySurvival.Raids;
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
        [SerializeField] private PlayerStats playerStats;
        [SerializeField] private RaidSession raidSession;
        [SerializeField] private GameplayEscapeMenuController escapeMenu;
        [SerializeField] private GameplaySceneTransitionFader sceneTransitionFader;

        private bool travelPrepared;
        private bool movementWasEnabled;
        private bool inventoryInputWasBlocked;
        private bool interactionWasBlocked;
        private bool damageWasBlocked;

        public Transform PlayerTransform => playerTransform;
        public Camera PlayerCamera => playerCamera;
        public EventSystem PlayerEventSystem => eventSystem;
        public InventoryUIManager InventoryUI => inventoryUI;
        public PlayerMovement PlayerMovement => playerMovement;
        public PlayerInteractor PlayerInteractor => playerInteractor;
        public PlayerStats PlayerStats => playerStats;
        public RaidSession RaidSession => raidSession;
        public GameplayEscapeMenuController EscapeMenu => escapeMenu;
        public GameplaySceneTransitionFader SceneTransitionFader => sceneTransitionFader;
        public bool IsTravelPrepared => travelPrepared;

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
            damageWasBlocked = playerStats.DamageBlocked;
            travelPrepared = true;

            try
            {
                if (!inventoryUI.CloseAllInventories())
                {
                    Debug.LogError("Cannot travel because the active inventory drag could not be restored.", this);
                    RestoreTravelState(true);
                    return false;
                }
                eventSystem.SetSelectedGameObject(null);
                playerMovement.enabled = false;
                inventoryUI.SetInputBlocked(true);
                playerInteractor.SetInteractionBlocked(true);
                playerStats.SetDamageBlocked(true);
                return true;
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                RestoreTravelState(true);
                return false;
            }
        }

        public void FinishArrival(Action onFinished = null)
        {
            RevealSceneAndRestoreTravelState(false, onFinished);
        }

        public void CancelTravelPreparation(Action onCancelled = null)
        {
            RevealSceneAndRestoreTravelState(true, onCancelled);
        }

        public bool BeginTravelTransition(Action onCovered, Action onInterrupted)
        {
            if (!travelPrepared || sceneTransitionFader == null)
            {
                return false;
            }

            return sceneTransitionFader.TryCover(onCovered, onInterrupted);
        }

        public void EndGameplaySession()
        {
            if (Instance != this)
            {
                return;
            }

            Instance = null;
            travelPrepared = false;
            gameObject.SetActive(false);
            Destroy(gameObject);
        }

        private void RevealSceneAndRestoreTravelState(
            bool restorePreviousDamageBlock,
            Action onRestored = null)
        {
            if (!travelPrepared)
            {
                onRestored?.Invoke();
                return;
            }

            if (sceneTransitionFader == null || !sceneTransitionFader.isActiveAndEnabled)
            {
                RestoreTravelState(restorePreviousDamageBlock);
                onRestored?.Invoke();
                return;
            }

            sceneTransitionFader.Reveal(() =>
            {
                RestoreTravelState(restorePreviousDamageBlock);
                onRestored?.Invoke();
            });
        }

        private void RestoreTravelState(bool restorePreviousDamageBlock)
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
            if (restorePreviousDamageBlock && playerStats != null)
            {
                playerStats.SetDamageBlocked(damageWasBlocked);
            }
            travelPrepared = false;
            damageWasBlocked = false;
        }

        private bool HasRequiredReferences()
        {
            return playerTransform != null && playerCamera != null && eventSystem != null &&
                   inventoryUI != null && playerMovement != null && playerInteractor != null &&
                   playerStats != null && raidSession != null && raidSession.IsConfigured &&
                   escapeMenu != null && escapeMenu.IsConfigured &&
                   sceneTransitionFader != null && sceneTransitionFader.IsConfigured;
        }
    }
}
