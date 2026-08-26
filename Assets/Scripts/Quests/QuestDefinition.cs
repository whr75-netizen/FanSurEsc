using UnityEngine;

namespace FantasySurvival.Quests
{
    [CreateAssetMenu(fileName = "QuestDefinition", menuName = "Fantasy Survival/Quest Definition")]
    public sealed class QuestDefinition : ScriptableObject
    {
        [SerializeField] private string questId = "core:quest:prototype_hunt";
        [SerializeField] private string displayName = "첫 생환 시험";
        [SerializeField, TextArea(2, 5)] private string description =
            "원정에서 적 1명을 처치하고 살아서 기지로 돌아오십시오.";
        [SerializeField, Min(1)] private int requiredEnemyKills = 1;
        [SerializeField] private bool requiresSuccessfulExtraction = true;

        public string QuestId => questId;
        public string DisplayName => displayName;
        public string Description => description;
        public int RequiredEnemyKills => Mathf.Max(1, requiredEnemyKills);
        public bool RequiresSuccessfulExtraction => requiresSuccessfulExtraction;

        public bool TryValidate(out string error)
        {
            if (string.IsNullOrWhiteSpace(questId))
            {
                error = "Quest ID is missing.";
                return false;
            }

            if (string.IsNullOrWhiteSpace(displayName))
            {
                error = $"Quest '{questId}' has no display name.";
                return false;
            }

            if (requiredEnemyKills < 1)
            {
                error = $"Quest '{questId}' must require at least one enemy kill.";
                return false;
            }

            error = null;
            return true;
        }

        private void OnValidate()
        {
            requiredEnemyKills = Mathf.Max(1, requiredEnemyKills);
        }
    }
}
