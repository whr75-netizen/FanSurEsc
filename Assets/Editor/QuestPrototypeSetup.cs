using System.Collections.Generic;
using FantasySurvival.Interaction;
using FantasySurvival.Quests;
using FantasySurvival.Raids;
using FantasySurvival.SceneFlow;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace FantasySurvival.EditorTools
{
    public static class QuestPrototypeSetup
    {
        private const string ShellPrefabPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private const string BaseScenePath = "Assets/Scenes/GameMap1.unity";
        private const string QuestFolder = "Assets/GameData/Quests";
        private const string QuestAssetPath = QuestFolder + "/PrototypeHuntQuest.asset";
        private const string QuestMaterialPath = QuestFolder + "/TestQuestGiverGraybox.mat";
        private const string QuestNpcName = "Test_QuestNPC_Base";
        private const string QuestCanvasName = "QuestCanvas";
        private const string ObstacleTag = "Obstacle";

        private static readonly string[] EnemyPrefabPaths =
        {
            "Assets/Prefabs/Enemies/KenneyZombiePatrol.prefab",
            "Assets/Prefabs/Enemies/PrototypeRangedEnemy.prefab"
        };

        private static readonly Vector3[] QuestNpcPositionCandidates =
        {
            new Vector3(2f, 1f, 2f),
            new Vector3(3f, 1f, -2f),
            new Vector3(-3f, 1f, -2f),
            new Vector3(4f, 1f, 3f),
            new Vector3(-4f, 1f, 3f)
        };

        [MenuItem("Tools/Fantasy Survival/Quest/Apply Prototype")]
        public static void ApplyAll()
        {
            EnsureEditorReadyAndScenesClean();
            EnsureFolder(QuestFolder);
            QuestDefinition definition = ConfigureQuestDefinition();
            ValidateProgressRules(definition);
            ConfigureShellPrefab(definition);
            ConfigureEnemyPrefabs();
            ConfigureBaseScene(definition);
            AssetDatabase.Refresh();
            ValidateShellPrefab();
            ValidateEnemyPrefabs();
            ValidateBaseScene();
            Debug.Log(
                "Quest prototype configured: Play Session quest journal/UI, GameMap1 cube NPC, " +
                "Player kill relays, and one-kill successful-extraction completion flow.");
        }

        [MenuItem("Tools/Fantasy Survival/Quest/Validate Prototype")]
        public static void ValidateAll()
        {
            EnsureEditorReadyAndScenesClean();
            QuestDefinition definition = AssetDatabase.LoadAssetAtPath<QuestDefinition>(QuestAssetPath);
            Require(definition != null, $"Quest definition is missing: {QuestAssetPath}");
            Require(definition.TryValidate(out string definitionError), definitionError);
            ValidateShellPrefab();
            ValidateEnemyPrefabs();
            ValidateBaseScene();
            ValidateProgressRules(definition);
            Debug.Log("Quest prototype validation passed.");
        }

        private static QuestDefinition ConfigureQuestDefinition()
        {
            QuestDefinition definition = AssetDatabase.LoadAssetAtPath<QuestDefinition>(QuestAssetPath);
            if (definition == null)
            {
                definition = ScriptableObject.CreateInstance<QuestDefinition>();
                AssetDatabase.CreateAsset(definition, QuestAssetPath);
            }

            var serialized = new SerializedObject(definition);
            serialized.FindProperty("questId").stringValue = "core:quest:prototype_hunt";
            serialized.FindProperty("displayName").stringValue = "첫 생환 시험";
            serialized.FindProperty("description").stringValue =
                "원정에서 적 1명을 처치하고 살아서 기지로 돌아오십시오.";
            serialized.FindProperty("requiredEnemyKills").intValue = 1;
            serialized.FindProperty("requiresSuccessfulExtraction").boolValue = true;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(definition);
            AssetDatabase.SaveAssetIfDirty(definition);
            Require(definition.TryValidate(out string error), error);
            return definition;
        }

        private static void ConfigureShellPrefab(QuestDefinition definition)
        {
            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            Require(root != null, $"Could not load prefab: {ShellPrefabPath}");

            try
            {
                PersistentGameplayShell shell = root.GetComponent<PersistentGameplayShell>();
                RaidSession raidSession = root.GetComponent<RaidSession>();
                RaidCheckpointController checkpoint = root.GetComponent<RaidCheckpointController>();
                InventoryUIManager inventory = root.GetComponentInChildren<InventoryUIManager>(true);
                EventSystem eventSystem = root.GetComponentInChildren<EventSystem>(true);
                Require(shell != null, "PersistentGameplayShell root component is missing.");
                Require(raidSession != null, "PersistentGameplayShell RaidSession is missing.");
                Require(checkpoint != null, "PersistentGameplayShell RaidCheckpointController is missing.");
                Require(inventory != null, "PersistentGameplayShell InventoryUIManager is missing.");
                Require(eventSystem != null, "PersistentGameplayShell EventSystem is missing.");

                QuestJournal journal = root.GetComponent<QuestJournal>();
                if (journal == null)
                {
                    journal = root.AddComponent<QuestJournal>();
                }

                var journalSerialized = new SerializedObject(journal);
                journalSerialized.FindProperty("prototypeQuest").objectReferenceValue = definition;
                journalSerialized.FindProperty("raidSession").objectReferenceValue = raidSession;
                journalSerialized.FindProperty("raidCheckpoint").objectReferenceValue = checkpoint;
                journalSerialized.ApplyModifiedPropertiesWithoutUndo();

                Transform existingCanvas = root.transform.Find(QuestCanvasName);
                if (existingCanvas != null)
                {
                    Object.DestroyImmediate(existingCanvas.gameObject);
                }

                Font font = root.GetComponentInChildren<Text>(true)?.font;
                if (font == null)
                {
                    font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                }

                GameObject canvasObject = CreateRectObject(root.transform, QuestCanvasName);
                ConfigureFullScreenRect(canvasObject.GetComponent<RectTransform>());
                Canvas canvas = canvasObject.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvas.sortingOrder = 12000;
                CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1920f, 1080f);
                scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
                scaler.matchWidthOrHeight = 0.5f;
                canvasObject.AddComponent<GraphicRaycaster>();
                QuestPanelController panel = canvasObject.AddComponent<QuestPanelController>();

                GameObject dialogRoot = CreatePanel(
                    canvasObject.transform,
                    "QuestDialog",
                    new Color(0.055f, 0.06f, 0.075f, 0.97f),
                    true);
                SetCenteredRect(dialogRoot.GetComponent<RectTransform>(), Vector2.zero, new Vector2(560f, 320f));

                Text titleText = CreateText(
                    dialogRoot.transform,
                    "TitleText",
                    "첫 생환 시험",
                    font,
                    28,
                    TextAnchor.MiddleCenter);
                titleText.fontStyle = FontStyle.Bold;
                SetCenteredRect(titleText.rectTransform, new Vector2(0f, 115f), new Vector2(500f, 42f));

                Text descriptionText = CreateText(
                    dialogRoot.transform,
                    "DescriptionText",
                    "원정에서 적 1명을 처치하고 살아서 기지로 돌아오십시오.",
                    font,
                    18,
                    TextAnchor.MiddleCenter);
                SetCenteredRect(
                    descriptionText.rectTransform,
                    new Vector2(0f, 45f),
                    new Vector2(500f, 80f));

                Text statusText = CreateText(
                    dialogRoot.transform,
                    "StatusText",
                    "목표: 적 처치 0/1 후 생환",
                    font,
                    18,
                    TextAnchor.MiddleCenter);
                statusText.color = new Color(0.72f, 0.9f, 1f, 1f);
                SetCenteredRect(statusText.rectTransform, new Vector2(0f, -35f), new Vector2(500f, 50f));

                Button primaryButton = CreateButton(
                    dialogRoot.transform,
                    "PrimaryButton",
                    "수락",
                    font,
                    out Text primaryButtonText);
                SetCenteredRect(
                    primaryButton.transform as RectTransform,
                    new Vector2(-75f, -115f),
                    new Vector2(260f, 48f));

                Button closeButton = CreateButton(
                    dialogRoot.transform,
                    "CloseButton",
                    "닫기",
                    font,
                    out _);
                SetCenteredRect(
                    closeButton.transform as RectTransform,
                    new Vector2(170f, -115f),
                    new Vector2(150f, 48f));

                GameObject trackerRoot = CreatePanel(
                    canvasObject.transform,
                    "QuestTracker",
                    new Color(0.055f, 0.06f, 0.075f, 0.9f),
                    false);
                RectTransform trackerRect = trackerRoot.GetComponent<RectTransform>();
                trackerRect.anchorMin = Vector2.one;
                trackerRect.anchorMax = Vector2.one;
                trackerRect.pivot = Vector2.one;
                trackerRect.anchoredPosition = new Vector2(-24f, -24f);
                trackerRect.sizeDelta = new Vector2(390f, 78f);

                Text trackerText = CreateText(
                    trackerRoot.transform,
                    "TrackerText",
                    "첫 생환 시험\n적 처치 0/1",
                    font,
                    17,
                    TextAnchor.MiddleLeft);
                trackerText.rectTransform.anchorMin = Vector2.zero;
                trackerText.rectTransform.anchorMax = Vector2.one;
                trackerText.rectTransform.offsetMin = new Vector2(18f, 8f);
                trackerText.rectTransform.offsetMax = new Vector2(-18f, -8f);

                var panelSerialized = new SerializedObject(panel);
                panelSerialized.FindProperty("journal").objectReferenceValue = journal;
                panelSerialized.FindProperty("inventoryUI").objectReferenceValue = inventory;
                panelSerialized.FindProperty("eventSystem").objectReferenceValue = eventSystem;
                panelSerialized.FindProperty("dialogRoot").objectReferenceValue = dialogRoot;
                panelSerialized.FindProperty("titleText").objectReferenceValue = titleText;
                panelSerialized.FindProperty("descriptionText").objectReferenceValue = descriptionText;
                panelSerialized.FindProperty("statusText").objectReferenceValue = statusText;
                panelSerialized.FindProperty("primaryButton").objectReferenceValue = primaryButton;
                panelSerialized.FindProperty("primaryButtonText").objectReferenceValue = primaryButtonText;
                panelSerialized.FindProperty("closeButton").objectReferenceValue = closeButton;
                panelSerialized.FindProperty("trackerRoot").objectReferenceValue = trackerRoot;
                panelSerialized.FindProperty("trackerText").objectReferenceValue = trackerText;
                panelSerialized.ApplyModifiedPropertiesWithoutUndo();

                var shellSerialized = new SerializedObject(shell);
                shellSerialized.FindProperty("questJournal").objectReferenceValue = journal;
                shellSerialized.FindProperty("questPanel").objectReferenceValue = panel;
                shellSerialized.ApplyModifiedPropertiesWithoutUndo();

                dialogRoot.SetActive(false);
                trackerRoot.SetActive(false);
                EditorUtility.SetDirty(journal);
                EditorUtility.SetDirty(panel);
                EditorUtility.SetDirty(shell);
                ValidateShellPrefab(root);
                GameObject savedRoot = PrefabUtility.SaveAsPrefabAsset(
                    root,
                    ShellPrefabPath,
                    out bool savedSuccessfully);
                Require(savedSuccessfully && savedRoot != null,
                    $"Unity could not save the configured shell prefab: {ShellPrefabPath}");
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static void ConfigureEnemyPrefabs()
        {
            foreach (string prefabPath in EnemyPrefabPaths)
            {
                GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
                Require(root != null, $"Could not load enemy prefab: {prefabPath}");
                try
                {
                    EnemyStats[] stats = root.GetComponentsInChildren<EnemyStats>(true);
                    Require(stats.Length == 1,
                        $"Enemy prefab must contain exactly one EnemyStats: {prefabPath}");
                    QuestKillCreditReporter reporter =
                        stats[0].GetComponent<QuestKillCreditReporter>();
                    if (reporter == null)
                    {
                        reporter = stats[0].gameObject.AddComponent<QuestKillCreditReporter>();
                    }

                    Require(reporter.GetComponent<EnemyStats>() == stats[0],
                        $"Quest kill reporter is not attached to EnemyStats: {prefabPath}");
                    Require(CountMissingScripts(root) == 0,
                        $"Enemy prefab contains missing scripts after quest setup: {prefabPath}");
                    EditorUtility.SetDirty(reporter);
                    GameObject savedRoot = PrefabUtility.SaveAsPrefabAsset(
                        root,
                        prefabPath,
                        out bool savedSuccessfully);
                    Require(savedSuccessfully && savedRoot != null,
                        $"Unity could not save the configured enemy prefab: {prefabPath}");
                }
                finally
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
        }

        private static void ConfigureBaseScene(QuestDefinition definition)
        {
            SceneSetup[] previousSetup = EditorSceneManager.GetSceneManagerSetup();
            try
            {
                Scene scene = EditorSceneManager.OpenScene(BaseScenePath, OpenSceneMode.Single);
                GameObject npc = FindRootByName(scene, QuestNpcName);
                if (npc == null)
                {
                    npc = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    npc.name = QuestNpcName;
                    Undo.RegisterCreatedObjectUndo(npc, "Create Test Quest NPC");
                    SceneManager.MoveGameObjectToScene(npc, scene);
                }

                Undo.RecordObject(npc, "Configure Test Quest NPC Collision");
                npc.tag = ObstacleTag;

                Collider npcCollider = npc.GetComponent<Collider>();
                if (npcCollider == null)
                {
                    npcCollider = Undo.AddComponent<BoxCollider>(npc);
                }
                Undo.RecordObject(npcCollider, "Configure Test Quest NPC Collision");
                npcCollider.isTrigger = false;

                QuestGiverInteractable interactable = npc.GetComponent<QuestGiverInteractable>();
                if (interactable == null)
                {
                    interactable = Undo.AddComponent<QuestGiverInteractable>(npc);
                }

                Undo.RecordObject(npc.transform, "Configure Test Quest NPC Transform");
                npc.transform.SetPositionAndRotation(ChooseQuestNpcPosition(scene, interactable), Quaternion.identity);
                npc.transform.localScale = new Vector3(1f, 2f, 1f);

                Renderer renderer = npc.GetComponent<Renderer>();
                if (renderer != null)
                {
                    Undo.RecordObject(renderer, "Configure Test Quest NPC Material");
                    renderer.sharedMaterial = GetOrCreateQuestMaterial();
                }

                var serialized = new SerializedObject(interactable);
                serialized.FindProperty("questDefinition").objectReferenceValue = definition;
                serialized.FindProperty("interactionPrompt").stringValue = "의뢰 확인 / 닫기";
                serialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(interactable);
                EditorSceneManager.MarkSceneDirty(scene);
                ValidateBaseScene(scene);
                Require(
                    EditorSceneManager.SaveScene(scene),
                    $"Unity could not save the configured base scene: {BaseScenePath}");
            }
            finally
            {
                EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
            }
        }

        private static Vector3 ChooseQuestNpcPosition(
            Scene scene,
            QuestGiverInteractable questInteractable)
        {
            Interactable[] interactables = FindComponentsInScene<Interactable>(scene);
            const float minimumSeparation = 2.25f;
            float minimumSeparationSquared = minimumSeparation * minimumSeparation;
            foreach (Vector3 candidate in QuestNpcPositionCandidates)
            {
                bool clear = true;
                foreach (Interactable other in interactables)
                {
                    if (other == null || other == questInteractable)
                    {
                        continue;
                    }

                    Vector3 delta = other.transform.position - candidate;
                    delta.y = 0f;
                    if (delta.sqrMagnitude < minimumSeparationSquared)
                    {
                        clear = false;
                        break;
                    }
                }

                if (clear)
                {
                    return candidate;
                }
            }

            throw new BuildFailedException(
                "No deterministic graybox Quest NPC position is clear of existing interactables.");
        }

        private static Material GetOrCreateQuestMaterial()
        {
            Material material = AssetDatabase.LoadAssetAtPath<Material>(QuestMaterialPath);
            if (material == null)
            {
                Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
                Require(shader != null, "No supported shader is available for the Quest NPC material.");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, QuestMaterialPath);
            }

            Color color = new Color(0.48f, 0.24f, 0.68f, 1f);
            if (material.HasProperty("_BaseColor"))
            {
                material.SetColor("_BaseColor", color);
            }
            if (material.HasProperty("_Color"))
            {
                material.SetColor("_Color", color);
            }
            EditorUtility.SetDirty(material);
            AssetDatabase.SaveAssetIfDirty(material);
            return material;
        }

        private static void ValidateShellPrefab()
        {
            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            Require(root != null, $"Could not load prefab: {ShellPrefabPath}");
            try
            {
                ValidateShellPrefab(root);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static void ValidateShellPrefab(GameObject root)
        {
            QuestJournal[] journals = root.GetComponentsInChildren<QuestJournal>(true);
            QuestPanelController[] panels = root.GetComponentsInChildren<QuestPanelController>(true);
            PersistentGameplayShell shell = root.GetComponent<PersistentGameplayShell>();
            QuestDefinition expectedDefinition =
                AssetDatabase.LoadAssetAtPath<QuestDefinition>(QuestAssetPath);
            Require(journals.Length == 1, $"Expected one QuestJournal, found {journals.Length}.");
            Require(panels.Length == 1, $"Expected one QuestPanelController, found {panels.Length}.");
            Require(shell != null && shell.QuestJournal == journals[0] && shell.QuestPanel == panels[0],
                "PersistentGameplayShell Quest references are missing or point to another object.");
            Require(expectedDefinition != null && journals[0].Definition == expectedDefinition,
                "QuestJournal does not reference the prototype QuestDefinition asset.");
            Require(journals[0].IsConfigured, "QuestJournal is not fully configured.");
            Require(panels[0].IsConfigured, "QuestPanelController is not fully configured.");
            Transform canvasTransform = root.transform.Find(QuestCanvasName);
            Require(canvasTransform != null && panels[0].transform == canvasTransform,
                "QuestPanelController is not on the owned QuestCanvas root.");
            Canvas canvas = canvasTransform.GetComponent<Canvas>();
            CanvasScaler scaler = canvasTransform.GetComponent<CanvasScaler>();
            Require(canvas != null && canvas.renderMode == RenderMode.ScreenSpaceOverlay &&
                    canvas.sortingOrder == 12000,
                "QuestCanvas render/sorting configuration is invalid.");
            Require(scaler != null &&
                    scaler.uiScaleMode == CanvasScaler.ScaleMode.ScaleWithScreenSize &&
                    canvasTransform.GetComponent<GraphicRaycaster>() != null,
                "QuestCanvas scaling or raycaster configuration is invalid.");

            var panelSerialized = new SerializedObject(panels[0]);
            Require(panelSerialized.FindProperty("journal").objectReferenceValue == journals[0],
                "QuestPanelController does not reference the shell's QuestJournal.");
            Require(panelSerialized.FindProperty("inventoryUI").objectReferenceValue == shell.InventoryUI,
                "QuestPanelController does not reference the shell's InventoryUIManager.");
            Require(panelSerialized.FindProperty("eventSystem").objectReferenceValue ==
                    shell.PlayerEventSystem,
                "QuestPanelController does not reference the shell's EventSystem.");
            string[] ownedUiProperties =
            {
                "dialogRoot", "titleText", "descriptionText", "statusText",
                "primaryButton", "primaryButtonText", "closeButton", "trackerRoot", "trackerText"
            };
            foreach (string propertyName in ownedUiProperties)
            {
                Object reference = panelSerialized.FindProperty(propertyName).objectReferenceValue;
                Component component = reference as Component;
                GameObject gameObject = reference as GameObject;
                Transform referenceTransform = component != null
                    ? component.transform
                    : gameObject != null ? gameObject.transform : null;
                Require(referenceTransform != null && referenceTransform.IsChildOf(canvasTransform),
                    $"Quest UI reference '{propertyName}' is missing or outside QuestCanvas.");
            }
            Require(CountMissingScripts(root) == 0,
                "PersistentGameplayShell contains missing scripts after quest setup.");
        }

        private static void ValidateEnemyPrefabs()
        {
            foreach (string prefabPath in EnemyPrefabPaths)
            {
                GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
                Require(root != null, $"Could not load enemy prefab: {prefabPath}");
                try
                {
                    EnemyStats[] stats = root.GetComponentsInChildren<EnemyStats>(true);
                    QuestKillCreditReporter[] reporters =
                        root.GetComponentsInChildren<QuestKillCreditReporter>(true);
                    Require(stats.Length == 1 && reporters.Length == 1,
                        $"Enemy prefab quest relay count is invalid: {prefabPath}");
                    Require(reporters[0].gameObject == stats[0].gameObject,
                        $"Enemy quest relay must share the EnemyStats owner: {prefabPath}");
                    Require(CountMissingScripts(root) == 0,
                        $"Enemy prefab contains missing scripts: {prefabPath}");
                }
                finally
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
        }

        private static void ValidateBaseScene()
        {
            SceneSetup[] previousSetup = EditorSceneManager.GetSceneManagerSetup();
            try
            {
                Scene scene = EditorSceneManager.OpenScene(BaseScenePath, OpenSceneMode.Single);
                ValidateBaseScene(scene);
            }
            finally
            {
                EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
            }
        }

        private static void ValidateBaseScene(Scene scene)
        {
            QuestGiverInteractable[] interactables = FindComponentsInScene<QuestGiverInteractable>(scene);
            Require(interactables.Length == 1,
                $"GameMap1 must contain exactly one QuestGiverInteractable, found {interactables.Length}.");
            QuestGiverInteractable interactable = interactables[0];
            QuestDefinition expectedDefinition =
                AssetDatabase.LoadAssetAtPath<QuestDefinition>(QuestAssetPath);
            Require(interactable.gameObject.name == QuestNpcName,
                $"Quest NPC must use the stable authoring name '{QuestNpcName}'.");
            Collider npcCollider = interactable.GetComponent<Collider>();
            Require(npcCollider != null && !npcCollider.isTrigger,
                "Quest NPC needs a solid Collider for interaction and movement blocking.");
            Require(interactable.CompareTag(ObstacleTag),
                $"Quest NPC must use the '{ObstacleTag}' tag for PlayerMovement blocking.");
            Require(interactable.GetComponent<Rigidbody>() == null,
                "Quest NPC must remain a fixed obstacle without a Rigidbody.");
            Require(expectedDefinition != null && interactable.QuestDefinition == expectedDefinition,
                "Quest NPC definition reference is missing or incorrect.");
            Require(CountMissingScripts(interactable.gameObject) == 0,
                "Quest NPC contains missing scripts.");
        }

        private static void ValidateProgressRules(QuestDefinition definition)
        {
            var failedAttempt = new QuestProgressState(definition);
            Require(failedAttempt.TryAccept(), "Failure-path quest could not be accepted.");
            Require(failedAttempt.TryRecordEnemyKill(), "Failure-path kill was not recorded.");
            Require(failedAttempt.Status == QuestProgressStatus.Active,
                "A kill was incorrectly completed before extraction.");
            Require(failedAttempt.ApplyCommittedRaidOutcome(RaidOutcome.PlayerDied),
                "Failure-path settlement did not update the quest.");
            Require(failedAttempt.Status == QuestProgressStatus.Active && failedAttempt.EnemyKills == 0,
                "Failed raid must keep the quest active and clear only this attempt's kills.");

            var successfulAttempt = new QuestProgressState(definition);
            Require(successfulAttempt.TryAccept(), "Success-path quest could not be accepted.");
            Require(successfulAttempt.TryRecordEnemyKill(), "Success-path kill was not recorded.");
            Require(successfulAttempt.ApplyCommittedRaidOutcome(RaidOutcome.Extracted),
                "Successful extraction did not update the quest.");
            Require(successfulAttempt.Status == QuestProgressStatus.ReadyToTurnIn,
                "Quest became complete before NPC turn-in or failed to become reportable.");
            Require(successfulAttempt.TryTurnIn(), "Quest could not be turned in.");
            Require(successfulAttempt.Status == QuestProgressStatus.Completed,
                "Quest turn-in did not reach Completed.");
            Require(!successfulAttempt.TryTurnIn(), "Quest turn-in was not idempotent.");
        }

        private static GameObject CreatePanel(
            Transform parent,
            string name,
            Color color,
            bool raycastTarget)
        {
            GameObject panel = CreateRectObject(parent, name);
            Image image = panel.AddComponent<Image>();
            image.color = color;
            image.raycastTarget = raycastTarget;
            return panel;
        }

        private static Text CreateText(
            Transform parent,
            string name,
            string value,
            Font font,
            int fontSize,
            TextAnchor alignment)
        {
            GameObject gameObject = CreateRectObject(parent, name);
            Text text = gameObject.AddComponent<Text>();
            text.font = font;
            text.fontSize = fontSize;
            text.text = value;
            text.alignment = alignment;
            text.color = Color.white;
            text.raycastTarget = false;
            return text;
        }

        private static Button CreateButton(
            Transform parent,
            string name,
            string label,
            Font font,
            out Text labelText)
        {
            GameObject gameObject = CreateRectObject(parent, name);
            Image image = gameObject.AddComponent<Image>();
            image.color = new Color(0.23f, 0.25f, 0.31f, 1f);
            Button button = gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            ColorBlock colors = button.colors;
            colors.highlightedColor = new Color(0.37f, 0.4f, 0.5f, 1f);
            colors.pressedColor = new Color(0.14f, 0.16f, 0.21f, 1f);
            colors.selectedColor = colors.highlightedColor;
            button.colors = colors;

            labelText = CreateText(gameObject.transform, "Label", label, font, 17, TextAnchor.MiddleCenter);
            labelText.rectTransform.anchorMin = Vector2.zero;
            labelText.rectTransform.anchorMax = Vector2.one;
            labelText.rectTransform.offsetMin = Vector2.zero;
            labelText.rectTransform.offsetMax = Vector2.zero;
            return button;
        }

        private static GameObject CreateRectObject(Transform parent, string name)
        {
            var gameObject = new GameObject(name, typeof(RectTransform));
            gameObject.transform.SetParent(parent, false);
            return gameObject;
        }

        private static void ConfigureFullScreenRect(RectTransform rect)
        {
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
            rect.localScale = Vector3.one;
        }

        private static void SetCenteredRect(
            RectTransform rect,
            Vector2 anchoredPosition,
            Vector2 size)
        {
            Require(rect != null, "A required UI RectTransform is missing.");
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = anchoredPosition;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
        }

        private static T[] FindComponentsInScene<T>(Scene scene) where T : Component
        {
            var components = new List<T>();
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                components.AddRange(root.GetComponentsInChildren<T>(true));
            }
            return components.ToArray();
        }

        private static GameObject FindRootByName(Scene scene, string objectName)
        {
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (root.name == objectName)
                {
                    return root;
                }
            }
            return null;
        }

        private static int CountMissingScripts(GameObject root)
        {
            int count = 0;
            foreach (Transform transform in root.GetComponentsInChildren<Transform>(true))
            {
                count += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(transform.gameObject);
            }
            return count;
        }

        private static void EnsureFolder(string path)
        {
            string[] parts = path.Split('/');
            string current = parts[0];
            for (int index = 1; index < parts.Length; index++)
            {
                string next = current + "/" + parts[index];
                if (!AssetDatabase.IsValidFolder(next))
                {
                    AssetDatabase.CreateFolder(current, parts[index]);
                }
                current = next;
            }
        }

        private static void EnsureEditorReadyAndScenesClean()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException("Quest setup requires an idle Unity Editor in Edit Mode.");
            }

            for (int index = 0; index < SceneManager.sceneCount; index++)
            {
                Scene scene = SceneManager.GetSceneAt(index);
                if (scene.isDirty)
                {
                    throw new BuildFailedException(
                        $"Quest setup stopped because open scene '{scene.name}' has unsaved changes.");
                }
            }
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new BuildFailedException(message ?? "Quest prototype validation failed.");
            }
        }
    }
}
