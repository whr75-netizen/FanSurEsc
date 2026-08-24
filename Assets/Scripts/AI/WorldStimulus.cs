using System;
using UnityEngine;

namespace FantasySurvival.AI
{
    public enum WorldStimulusKind
    {
        GunshotSound,
        FootstepSound,
        ProjectileThreat,
        MagicThreat
    }

    public enum WorldStimulusResponse
    {
        Investigate,
        EngageInstigator
    }

    public readonly struct WorldStimulus
    {
        public WorldStimulus(
            WorldStimulusKind kind,
            WorldStimulusResponse response,
            Vector3 position,
            float radius,
            GameObject instigator)
        {
            Kind = kind;
            Response = response;
            Position = position;
            Radius = radius;
            Instigator = instigator;
        }

        public WorldStimulusKind Kind { get; }
        public WorldStimulusResponse Response { get; }
        public Vector3 Position { get; }
        public float Radius { get; }
        public GameObject Instigator { get; }
        public bool IsValid => Radius > 0f && !float.IsNaN(Radius);
    }

    /// <summary>
    /// Stateless notification channel for sparse gameplay stimuli. It does not own AI state.
    /// Producers report an event once; active listeners decide whether it is relevant.
    /// </summary>
    public static class WorldStimulusChannel
    {
        public static event Action<WorldStimulus> Emitted;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStaticState()
        {
            Emitted = null;
        }

        public static void Emit(WorldStimulus stimulus)
        {
            if (!stimulus.IsValid)
            {
                return;
            }

            try
            {
                Emitted?.Invoke(stimulus);
            }
            catch (Exception exception)
            {
                // A completed gameplay event must not be able to cancel its producer.
                // Keep the allocation-free multicast path; a faulty listener is logged.
                Debug.LogException(exception);
            }
        }
    }
}
