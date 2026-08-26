using FantasySurvival.Quests;
using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.Interaction
{
    [DisallowMultipleComponent]
    public sealed class QuestGiverInteractable : Interactable
    {
        [SerializeField] private QuestDefinition questDefinition;
        [SerializeField] private string interactionPrompt = "의뢰 확인 / 닫기";

        private QuestPanelController questPanel;

        public QuestDefinition QuestDefinition => questDefinition;
        public override string InteractionPrompt => string.IsNullOrWhiteSpace(interactionPrompt)
            ? "의뢰 확인 / 닫기"
            : interactionPrompt;

        public override bool CanInteract(PlayerInteractor interactor)
        {
            QuestPanelController panel = ResolvePanel();
            return base.CanInteract(interactor) && questDefinition != null &&
                   panel != null && panel.IsConfigured;
        }

        public override void Interact(PlayerInteractor interactor)
        {
            QuestPanelController panel = ResolvePanel();
            if (panel == null || !panel.TryToggle(this, questDefinition))
            {
                Debug.LogWarning("Quest interaction could not open its persistent quest panel.", this);
            }
        }

        public override bool IsInteractionActive(PlayerInteractor interactor)
        {
            QuestPanelController panel = ResolvePanel();
            return panel != null && panel.IsOpenFor(this);
        }

        public override bool TryCancelInteraction(PlayerInteractor interactor)
        {
            QuestPanelController panel = ResolvePanel();
            return panel == null || panel.TryClose(this);
        }

        private QuestPanelController ResolvePanel()
        {
            if (questPanel == null && PersistentGameplayShell.Instance != null)
            {
                questPanel = PersistentGameplayShell.Instance.QuestPanel;
            }

            return questPanel;
        }

        private void OnDisable()
        {
            if (questPanel != null)
            {
                questPanel.TryClose(this);
            }
        }
    }
}
