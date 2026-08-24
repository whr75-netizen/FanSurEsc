using System;
using System.Collections.Generic;
using VariableInventorySystem;

namespace FantasySurvival.BaseBuilding
{
    public sealed class BaseFurnitureRuntimeState
    {
        public BaseFurnitureRuntimeState(
            string instanceId,
            string definitionKey,
            StandardStashViewData storage)
        {
            InstanceId = instanceId;
            DefinitionKey = definitionKey;
            Storage = storage;
        }

        public string InstanceId { get; }
        public string DefinitionKey { get; }
        public StandardStashViewData Storage { get; }
    }

    public sealed class BaseFurnitureStateStore
    {
        private readonly Dictionary<string, BaseFurnitureRuntimeState> statesById =
            new Dictionary<string, BaseFurnitureRuntimeState>(StringComparer.Ordinal);
        private readonly Dictionary<string, BaseFurnitureInstance> activeBindings =
            new Dictionary<string, BaseFurnitureInstance>(StringComparer.Ordinal);

        public int StateCount => statesById.Count;
        public bool HasActiveBindings => activeBindings.Count > 0;
        internal IEnumerable<BaseFurnitureRuntimeState> States => statesById.Values;

        public bool TryValidateBindings(
            IReadOnlyList<BaseFurnitureInstance> instances,
            out string error)
        {
            return TryValidateBindings(instances, true, out error);
        }

        public bool TryValidateBindings(
            IReadOnlyList<BaseFurnitureInstance> instances,
            bool allowCreateMissingStates,
            out string error)
        {
            if (instances == null)
            {
                error = "Base furniture binding list is missing.";
                return false;
            }

            var seenIds = new HashSet<string>(StringComparer.Ordinal);
            for (int index = 0; index < instances.Count; index++)
            {
                BaseFurnitureInstance instance = instances[index];
                if (instance == null)
                {
                    error = $"Base furniture binding at index {index} is missing.";
                    return false;
                }

                if (!instance.TryValidateAuthoring(out error))
                {
                    error = $"[{instance.name}] {error}";
                    return false;
                }

                if (!seenIds.Add(instance.PersistentId))
                {
                    error = $"Base furniture ID '{instance.PersistentId}' is assigned more than once in the scene.";
                    return false;
                }

                if (activeBindings.TryGetValue(instance.PersistentId, out BaseFurnitureInstance active) &&
                    active != null && active != instance)
                {
                    error = $"Base furniture ID '{instance.PersistentId}' is already bound by '{active.name}'.";
                    return false;
                }

                if (statesById.TryGetValue(instance.PersistentId, out BaseFurnitureRuntimeState existing))
                {
                    if (!string.Equals(existing.DefinitionKey, instance.DefinitionKey, StringComparison.Ordinal))
                    {
                        error = $"Base furniture ID '{instance.PersistentId}' changed definition from " +
                                $"'{existing.DefinitionKey}' to '{instance.DefinitionKey}'. A migration is required.";
                        return false;
                    }

                    if (!instance.CanBind(existing, out error))
                    {
                        error = $"[{instance.name}] {error}";
                        return false;
                    }
                }
                else if (!allowCreateMissingStates)
                {
                    error = $"Base state is missing required furniture ID '{instance.PersistentId}'.";
                    return false;
                }
                else if (!instance.TryCreateInitialState(out _, out error))
                {
                    error = $"[{instance.name}] {error}";
                    return false;
                }
            }

            if (!allowCreateMissingStates && statesById.Count != seenIds.Count)
            {
                foreach (string stateId in statesById.Keys)
                {
                    if (!seenIds.Contains(stateId))
                    {
                        error = $"Base state contains furniture ID '{stateId}' that is not placed in this base layout.";
                        return false;
                    }
                }

                error = "Base state furniture count does not match the placed base layout.";
                return false;
            }

            error = null;
            return true;
        }

        public bool TryBindAll(
            IReadOnlyList<BaseFurnitureInstance> instances,
            out string error)
        {
            return TryBindAll(instances, true, out error);
        }

        public bool TryBindAll(
            IReadOnlyList<BaseFurnitureInstance> instances,
            bool allowCreateMissingStates,
            out string error)
        {
            if (!TryValidateBindings(instances, allowCreateMissingStates, out error))
            {
                return false;
            }

            var pendingStates = new List<BaseFurnitureRuntimeState>();
            var pendingBindings = new List<BaseFurnitureInstance>();
            for (int index = 0; index < instances.Count; index++)
            {
                BaseFurnitureInstance instance = instances[index];
                if (!statesById.TryGetValue(instance.PersistentId, out BaseFurnitureRuntimeState state))
                {
                    if (!instance.TryCreateInitialState(out state, out error))
                    {
                        RollBackBindings(pendingBindings);
                        return false;
                    }

                    pendingStates.Add(state);
                }

                if (!instance.TryApplyBinding(this, state, out error))
                {
                    RollBackBindings(pendingBindings);
                    return false;
                }

                pendingBindings.Add(instance);
            }

            foreach (BaseFurnitureRuntimeState state in pendingStates)
            {
                statesById.Add(state.InstanceId, state);
            }

            foreach (BaseFurnitureInstance instance in pendingBindings)
            {
                activeBindings[instance.PersistentId] = instance;
            }

            error = null;
            return true;
        }

        internal bool TryAddRestoredState(BaseFurnitureRuntimeState state, out string error)
        {
            if (state == null || !BaseContentKey.IsValid(state.InstanceId) ||
                !BaseContentKey.IsValid(state.DefinitionKey))
            {
                error = "Restored base furniture state has an invalid stable ID or definition key.";
                return false;
            }

            if (statesById.ContainsKey(state.InstanceId))
            {
                error = $"Restored base state contains duplicate furniture ID '{state.InstanceId}'.";
                return false;
            }

            statesById.Add(state.InstanceId, state);
            error = null;
            return true;
        }

        internal void ReleaseBinding(string instanceId, BaseFurnitureInstance instance)
        {
            if (string.IsNullOrEmpty(instanceId) || instance == null)
            {
                return;
            }

            if (activeBindings.TryGetValue(instanceId, out BaseFurnitureInstance current) && current == instance)
            {
                activeBindings.Remove(instanceId);
            }
        }

        private static void RollBackBindings(List<BaseFurnitureInstance> bindings)
        {
            for (int index = bindings.Count - 1; index >= 0; index--)
            {
                bindings[index].RollBackPendingBinding();
            }
        }
    }
}
