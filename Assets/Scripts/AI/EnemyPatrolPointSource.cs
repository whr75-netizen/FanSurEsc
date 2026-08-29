using UnityEngine;

namespace FantasySurvival.AI
{
    /// <summary>
    /// Read-only scene-lifetime source for patrol points derived from a map layout.
    /// Implementations retain ownership of their candidate collection; consumers query
    /// individual points without copying the collection or searching the scene.
    /// </summary>
    public interface IEnemyPatrolPointSource
    {
        bool IsPatrolPointSourceReady { get; }
        int PatrolPointCount { get; }

        bool TryGetPatrolPoint(int index, out Vector3 worldPosition);
    }
}
