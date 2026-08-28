using System;
using UnityEngine;

namespace FantasySurvival.Actions
{
    public enum PlayerActionCancelReason
    {
        Requested,
        ConditionFailed,
        SourceUnavailable,
        PlayerDied,
        SceneTravel,
        MovementInput,
        AttackInput,
        EquipmentSwitchInput,
        ControllerDisabled
    }

    public enum PlayerActionScope
    {
        // Acts on another world object: movement interrupts and the source is the UI anchor.
        External = 0,
        // Acts on the Player: movement is allowed and the Player is the UI anchor.
        Self = 1
    }

    /// <summary>
    /// Owns the Player's single in-progress timed action. Callers retain ownership of
    /// gameplay effects and apply them only from the completion callback.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(PlayerStats))]
    public sealed class PlayerActionController : MonoBehaviour
    {
        private bool hasActiveAction;
        private bool actionsBlocked;
        private UnityEngine.Object activeSource;
        private PlayerActionScope activeScope = PlayerActionScope.External;
        private string activeActionId;
        private float durationSeconds;
        private float elapsedSeconds;
        private Func<bool> canContinue;
        private Action onCompleted;
        private Action<PlayerActionCancelReason> onCancelled;
        private PlayerStats playerStats;

        public event Action ActionStarted;
        public event Action ActionEnded;

        public bool IsBusy => hasActiveAction;
        public bool ActionsBlocked => actionsBlocked;
        public string ActiveActionId => hasActiveAction ? activeActionId : string.Empty;
        public PlayerActionScope ActiveScope => activeScope;
        public float DurationSeconds => hasActiveAction ? durationSeconds : 0f;
        public float ElapsedSeconds => hasActiveAction ? elapsedSeconds : 0f;
        public float RemainingSeconds => hasActiveAction
            ? Mathf.Max(0f, durationSeconds - elapsedSeconds)
            : 0f;
        public float Progress01 => hasActiveAction && durationSeconds > 0f
            ? Mathf.Clamp01(elapsedSeconds / durationSeconds)
            : 0f;
        public Transform ActiveWorldAnchor
        {
            get
            {
                if (!hasActiveAction || activeSource == null)
                {
                    return null;
                }

                if (activeScope == PlayerActionScope.Self)
                {
                    return transform;
                }

                if (activeSource is Component component)
                {
                    return component.transform;
                }

                return activeSource is GameObject gameObject
                    ? gameObject.transform
                    : null;
            }
        }

        private void Awake()
        {
            playerStats = GetComponent<PlayerStats>();
            if (playerStats == null)
            {
                Debug.LogError($"{nameof(PlayerActionController)} requires {nameof(PlayerStats)}.", this);
                enabled = false;
            }
        }

        private void OnEnable()
        {
            if (playerStats == null)
            {
                playerStats = GetComponent<PlayerStats>();
            }

            if (playerStats != null)
            {
                playerStats.Died += HandlePlayerDied;
            }
        }

        private void OnDisable()
        {
            if (playerStats != null)
            {
                playerStats.Died -= HandlePlayerDied;
            }

            CancelActive(PlayerActionCancelReason.ControllerDisabled);
        }

        private void Update()
        {
            if (!hasActiveAction)
            {
                return;
            }

            if (activeSource == null)
            {
                CancelActive(PlayerActionCancelReason.SourceUnavailable);
                return;
            }

            if (!CanContinueActiveAction())
            {
                CancelActive(PlayerActionCancelReason.ConditionFailed);
                return;
            }

            elapsedSeconds = Mathf.Min(durationSeconds, elapsedSeconds + Time.deltaTime);
            if (elapsedSeconds >= durationSeconds)
            {
                CompleteActive();
            }
        }

        public bool TryBegin(
            string actionId,
            UnityEngine.Object source,
            PlayerActionScope scope,
            float actionDurationSeconds,
            Action completion)
        {
            return TryBegin(
                actionId,
                source,
                scope,
                actionDurationSeconds,
                null,
                completion,
                null);
        }

        public bool TryBegin(
            string actionId,
            UnityEngine.Object source,
            PlayerActionScope scope,
            float actionDurationSeconds,
            Func<bool> continuation,
            Action completion,
            Action<PlayerActionCancelReason> cancellation = null)
        {
            if (!isActiveAndEnabled || actionsBlocked || hasActiveAction || source == null ||
                (scope != PlayerActionScope.External && scope != PlayerActionScope.Self) ||
                string.IsNullOrWhiteSpace(actionId) || completion == null ||
                float.IsNaN(actionDurationSeconds) || float.IsInfinity(actionDurationSeconds) ||
                actionDurationSeconds < 0f || playerStats == null || !playerStats.IsAlive)
            {
                return false;
            }

            if (continuation != null && !continuation())
            {
                return false;
            }

            if (actionDurationSeconds <= 0f)
            {
                completion();
                return true;
            }

            hasActiveAction = true;
            activeSource = source;
            activeScope = scope;
            activeActionId = actionId;
            durationSeconds = actionDurationSeconds;
            elapsedSeconds = 0f;
            canContinue = continuation;
            onCompleted = completion;
            onCancelled = cancellation;
            ActionStarted?.Invoke();
            return true;
        }

        public bool IsActionOwnedBy(UnityEngine.Object source)
        {
            return hasActiveAction && source != null && activeSource == source;
        }

        internal void SetActionsBlocked(
            bool blocked,
            PlayerActionCancelReason cancelReason = PlayerActionCancelReason.Requested)
        {
            actionsBlocked = blocked;
            if (blocked)
            {
                CancelActive(cancelReason);
            }
        }

        public bool TryCancel(
            UnityEngine.Object source,
            PlayerActionCancelReason reason = PlayerActionCancelReason.Requested)
        {
            return IsActionOwnedBy(source) && CancelActive(reason);
        }

        public bool CancelActive(
            PlayerActionCancelReason reason = PlayerActionCancelReason.Requested)
        {
            if (!hasActiveAction)
            {
                return false;
            }

            if (reason == PlayerActionCancelReason.MovementInput &&
                activeScope == PlayerActionScope.Self)
            {
                // Self-use actions keep running while the Player walks or runs.
                return false;
            }

            Action<PlayerActionCancelReason> cancellation = onCancelled;
            ClearActive();
            try
            {
                ActionEnded?.Invoke();
            }
            finally
            {
                cancellation?.Invoke(reason);
            }
            return true;
        }

        private bool CanContinueActiveAction()
        {
            if (canContinue == null)
            {
                return true;
            }

            try
            {
                return canContinue();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception, this);
                return false;
            }
        }

        private void CompleteActive()
        {
            Action completion = onCompleted;
            ClearActive();
            try
            {
                ActionEnded?.Invoke();
            }
            finally
            {
                completion?.Invoke();
            }
        }

        private void ClearActive()
        {
            hasActiveAction = false;
            activeSource = null;
            activeScope = PlayerActionScope.External;
            activeActionId = null;
            durationSeconds = 0f;
            elapsedSeconds = 0f;
            canContinue = null;
            onCompleted = null;
            onCancelled = null;
        }

        private void HandlePlayerDied(PlayerStats _, FantasySurvival.Combat.DamageContext __)
        {
            CancelActive(PlayerActionCancelReason.PlayerDied);
        }
    }
}
