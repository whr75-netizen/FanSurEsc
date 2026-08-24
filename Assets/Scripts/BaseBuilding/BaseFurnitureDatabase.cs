using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.BaseBuilding
{
    [CreateAssetMenu(
        fileName = "BaseFurnitureDatabase",
        menuName = "Fantasy Survival/Base/Base Furniture Database")]
    public sealed class BaseFurnitureDatabase : ScriptableObject
    {
        [SerializeField] private List<BaseFurnitureDefinition> definitions =
            new List<BaseFurnitureDefinition>();

        private Dictionary<string, BaseFurnitureDefinition> definitionsByKey;

        public IReadOnlyList<BaseFurnitureDefinition> Definitions => definitions;

        public bool TryGet(string definitionKey, out BaseFurnitureDefinition definition)
        {
            EnsureIndex();
            definition = null;
            return definitionKey != null && definitionsByKey.TryGetValue(definitionKey, out definition);
        }

        public bool TryValidate(out string error)
        {
            var seen = new HashSet<string>(StringComparer.Ordinal);
            if (definitions == null)
            {
                error = "Base furniture definition list is missing.";
                return false;
            }

            for (int index = 0; index < definitions.Count; index++)
            {
                BaseFurnitureDefinition definition = definitions[index];
                if (definition == null)
                {
                    error = $"Base furniture database contains an empty entry at index {index}.";
                    return false;
                }

                if (!definition.TryValidate(out error))
                {
                    return false;
                }

                if (!seen.Add(definition.DefinitionKey))
                {
                    error = $"Base furniture database contains duplicate key '{definition.DefinitionKey}'.";
                    return false;
                }
            }

            // Rebuild after validation so runtime lookups cannot keep a stale editor-time cache
            // when the serialized list was changed without an OnEnable cycle.
            BuildIndex(false);
            error = null;
            return true;
        }

        private void OnEnable()
        {
            BuildIndex(false);
        }

        private void OnValidate()
        {
            BuildIndex(true);
        }

        private void EnsureIndex()
        {
            if (definitionsByKey == null)
            {
                BuildIndex(false);
            }
        }

        private void BuildIndex(bool logErrors)
        {
            definitionsByKey = new Dictionary<string, BaseFurnitureDefinition>(StringComparer.Ordinal);
            if (definitions == null)
            {
                return;
            }

            foreach (BaseFurnitureDefinition definition in definitions)
            {
                if (definition == null)
                {
                    if (logErrors)
                    {
                        Debug.LogError($"[{name}] Base furniture database contains an empty entry.", this);
                    }
                    continue;
                }

                if (!definition.TryValidate(out string error))
                {
                    if (logErrors)
                    {
                        Debug.LogError($"[{name}] {error}", this);
                    }
                    continue;
                }

                if (definitionsByKey.ContainsKey(definition.DefinitionKey))
                {
                    if (logErrors)
                    {
                        Debug.LogError(
                            $"[{name}] Duplicate furniture key '{definition.DefinitionKey}'.",
                            this);
                    }
                    continue;
                }

                definitionsByKey.Add(definition.DefinitionKey, definition);
            }
        }
    }
}
