using FantasySurvival.Combat;
using FantasySurvival.SceneFlow;
using UnityEngine;

namespace FantasySurvival.Quests
{
    /// <summary>
    /// Relays a confirmed EnemyStats death to the session QuestJournal. It owns no
    /// health, death, quest progress, or persistence state.
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(EnemyStats))]
    public sealed class QuestKillCreditReporter : MonoBehaviour
    {
        private EnemyStats enemyStats;

        private void Awake()
        {
            enemyStats = GetComponent<EnemyStats>();
        }

        private void OnEnable()
        {
            if (enemyStats == null)
            {
                enemyStats = GetComponent<EnemyStats>();
            }

            if (enemyStats != null)
            {
                enemyStats.Died += HandleEnemyDied;
            }
        }

        private void OnDisable()
        {
            if (enemyStats != null)
            {
                enemyStats.Died -= HandleEnemyDied;
            }
        }

        private static void HandleEnemyDied(EnemyStats source, DamageContext context)
        {
            PersistentGameplayShell shell = PersistentGameplayShell.Instance;
            Transform player = shell != null ? shell.PlayerTransform : null;
            Transform damageSource = context.Source != null ? context.Source.transform : null;
            if (shell == null || shell.QuestJournal == null || player == null ||
                damageSource == null ||
                (damageSource != player && !damageSource.IsChildOf(player)))
            {
                // Checkpoint corpse restoration deliberately emits Died with a null
                // damage source, so it can never be counted as a new Player kill.
                return;
            }

            shell.QuestJournal.TryRecordPlayerEnemyKill();
        }
    }
}
