using System;
using System.Collections.Generic;
using FantasySurvival.Information;
using FantasySurvival.Quests;
using FantasySurvival.Raids;
using FantasySurvival.SceneFlow;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace FantasySurvival.EditorTools
{
    public static class InformationWindowPrototypeSetup
    {
        private const string ShellPrefabPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private const string InformationCanvasName = "InformationCanvas";
        private const int InformationSortingOrder = 20000;

        private static readonly string[] EnemyDefinitionPaths =
        {
            "Assets/GameData/Enemies/Definitions/KenneyZombie.asset",
            "Assets/GameData/Enemies/Definitions/PrototypeRangedEnemy.asset"
        };

        [MenuItem("Tools/Fantasy Survival/Information/Apply Prototype")]
        public static void ApplyAll()
        {
            EnsureEditorReadyAndScenesClean();
            ConfigureShellPrefab();
            ValidateShellPrefab();
            Debug.Log(
                "Information window configured: persistent U-key overlay, five read-only tabs, " +
                "and Play Session aggregate records.");
        }

        [MenuItem("Tools/Fantasy Survival/Information/Validate Prototype")]
        public static void ValidateAll()
        {
            EnsureEditorReadyAndScenesClean();
            ValidateShellPrefab();
            Debug.Log("Information window prototype validation passed.");
        }

        private static void ConfigureShellPrefab()
        {
            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            Require(root != null, $"Could not load prefab: {ShellPrefabPath}");

            try
            {
                PersistentGameplayShell shell = root.GetComponent<PersistentGameplayShell>();
                QuestJournal questJournal = root.GetComponent<QuestJournal>();
                RaidCheckpointController raidCheckpoint = root.GetComponent<RaidCheckpointController>();
                InventoryUIManager inventory = root.GetComponentInChildren<InventoryUIManager>(true);
                PlayerWeaponController[] weaponControllers =
                    root.GetComponentsInChildren<PlayerWeaponController>(true);
                Require(weaponControllers.Length == 1,
                    $"Expected one PlayerWeaponController, found {weaponControllers.Length}.");
                PlayerWeaponController weaponController = weaponControllers[0];
                EventSystem eventSystem = root.GetComponentInChildren<EventSystem>(true);
                Require(shell != null, "PersistentGameplayShell root component is missing.");
                Require(questJournal != null, "PersistentGameplayShell QuestJournal is missing.");
                Require(raidCheckpoint != null,
                    "PersistentGameplayShell RaidCheckpointController is missing.");
                Require(inventory != null, "PersistentGameplayShell InventoryUIManager is missing.");
                Require(weaponController != null,
                    "PersistentGameplayShell PlayerWeaponController is missing.");
                Require(eventSystem != null, "PersistentGameplayShell EventSystem is missing.");

                PlayerSessionRecords[] existingRecords =
                    root.GetComponentsInChildren<PlayerSessionRecords>(true);
                Require(existingRecords.Length <= 1,
                    $"Expected at most one PlayerSessionRecords, found {existingRecords.Length}.");
                Require(existingRecords.Length == 0 || existingRecords[0].gameObject == root,
                    "PlayerSessionRecords must be owned by the shell root.");
                PlayerSessionRecords records = existingRecords.Length == 1
                    ? existingRecords[0]
                    : root.AddComponent<PlayerSessionRecords>();
                records.enabled = true;
                var recordsSerialized = new SerializedObject(records);
                recordsSerialized.FindProperty("questJournal").objectReferenceValue = questJournal;
                recordsSerialized.FindProperty("raidCheckpoint").objectReferenceValue = raidCheckpoint;
                recordsSerialized.ApplyModifiedPropertiesWithoutUndo();

                InformationWindowController[] existingControllers =
                    root.GetComponentsInChildren<InformationWindowController>(true);
                Require(existingControllers.Length <= 1,
                    $"Expected at most one InformationWindowController, found {existingControllers.Length}.");
                Require(existingControllers.Length == 0 || existingControllers[0].gameObject == root,
                    "InformationWindowController must be owned by the shell root.");
                InformationWindowController controller = existingControllers.Length == 1
                    ? existingControllers[0]
                    : root.AddComponent<InformationWindowController>();
                controller.enabled = true;

                // This subtree is wholly owned by this graybox authoring command.
                // Reapplying deliberately rebuilds only InformationCanvas and rewires all refs.
                Transform existingCanvas = root.transform.Find(InformationCanvasName);
                if (existingCanvas != null)
                {
                    UnityEngine.Object.DestroyImmediate(existingCanvas.gameObject);
                }

                Font font = root.GetComponentInChildren<Text>(true)?.font;
                if (font == null)
                {
                    font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                }
                Require(font != null, "A built-in UI font could not be loaded.");

                GameObject canvasObject = CreateRectObject(root.transform, InformationCanvasName);
                ConfigureFullScreenRect(canvasObject.GetComponent<RectTransform>());
                Canvas canvas = canvasObject.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvas.sortingOrder = InformationSortingOrder;
                CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1920f, 1080f);
                scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
                scaler.matchWidthOrHeight = 0.5f;
                canvasObject.AddComponent<GraphicRaycaster>();

                GameObject backdrop = CreatePanel(
                    canvasObject.transform,
                    "Backdrop",
                    new Color(0.015f, 0.018f, 0.025f, 0.88f),
                    true);
                ConfigureFullScreenRect(backdrop.GetComponent<RectTransform>());

                GameObject window = CreatePanel(
                    canvasObject.transform,
                    "Window",
                    new Color(0.07f, 0.075f, 0.09f, 1f),
                    true);
                SetCenteredRect(window.GetComponent<RectTransform>(), Vector2.zero,
                    new Vector2(1080f, 680f));

                Text heading = CreateText(
                    window.transform,
                    "Heading",
                    "정보  [U]",
                    font,
                    30,
                    TextAnchor.MiddleLeft);
                heading.fontStyle = FontStyle.Bold;
                SetTopStretchRect(heading.rectTransform, 28f, 22f, 148f, 54f);

                Button closeButton = CreateButton(
                    window.transform,
                    "CloseButton",
                    "닫기",
                    font,
                    17,
                    out _);
                SetTopRightRect(closeButton.transform as RectTransform,
                    new Vector2(-24f, -22f), new Vector2(100f, 42f));

                GameObject tabPanel = CreatePanel(
                    window.transform,
                    "TabPanel",
                    new Color(0.10f, 0.11f, 0.14f, 1f),
                    false);
                RectTransform tabPanelRect = tabPanel.GetComponent<RectTransform>();
                tabPanelRect.anchorMin = new Vector2(0f, 0f);
                tabPanelRect.anchorMax = new Vector2(0f, 1f);
                tabPanelRect.pivot = new Vector2(0f, 0.5f);
                tabPanelRect.anchoredPosition = new Vector2(24f, -30f);
                tabPanelRect.sizeDelta = new Vector2(210f, -112f);

                Button characterButton = CreateTabButton(tabPanel.transform, "CharacterTab", "캐릭터", font, 0);
                Button recordsButton = CreateTabButton(tabPanel.transform, "RecordsTab", "기록", font, 1);
                Button encyclopediaButton = CreateTabButton(tabPanel.transform, "EncyclopediaTab", "사전", font, 2);
                Button questsButton = CreateTabButton(tabPanel.transform, "QuestsTab", "의뢰", font, 3);
                Button upgradesButton = CreateTabButton(tabPanel.transform, "UpgradesTab", "업그레이드", font, 4);

                GameObject contentPanel = CreatePanel(
                    window.transform,
                    "ContentPanel",
                    new Color(0.105f, 0.11f, 0.135f, 1f),
                    false);
                RectTransform contentPanelRect = contentPanel.GetComponent<RectTransform>();
                contentPanelRect.anchorMin = Vector2.zero;
                contentPanelRect.anchorMax = Vector2.one;
                contentPanelRect.offsetMin = new Vector2(254f, 24f);
                contentPanelRect.offsetMax = new Vector2(-24f, -88f);
                contentPanel.AddComponent<RectMask2D>();

                Text sectionTitle = CreateText(
                    contentPanel.transform,
                    "SectionTitle",
                    "캐릭터",
                    font,
                    25,
                    TextAnchor.MiddleLeft);
                sectionTitle.fontStyle = FontStyle.Bold;
                SetTopStretchRect(sectionTitle.rectTransform, 24f, 18f, 24f, 44f);

                Text content = CreateText(
                    contentPanel.transform,
                    "SectionBody",
                    "현재 정보를 불러오는 중입니다.",
                    font,
                    17,
                    TextAnchor.UpperLeft);
                content.horizontalOverflow = HorizontalWrapMode.Wrap;
                content.verticalOverflow = VerticalWrapMode.Truncate;
                content.lineSpacing = 1.05f;
                content.rectTransform.anchorMin = Vector2.zero;
                content.rectTransform.anchorMax = Vector2.one;
                content.rectTransform.offsetMin = new Vector2(24f, 20f);
                content.rectTransform.offsetMax = new Vector2(-24f, -76f);

                var controllerSerialized = new SerializedObject(controller);
                controllerSerialized.FindProperty("shell").objectReferenceValue = shell;
                controllerSerialized.FindProperty("weaponController").objectReferenceValue = weaponController;
                SerializedProperty enemies = controllerSerialized.FindProperty("enemyDefinitions");
                enemies.arraySize = EnemyDefinitionPaths.Length;
                for (int index = 0; index < EnemyDefinitionPaths.Length; index++)
                {
                    EnemyDefinition definition =
                        AssetDatabase.LoadAssetAtPath<EnemyDefinition>(EnemyDefinitionPaths[index]);
                    Require(definition != null,
                        $"Enemy definition is missing: {EnemyDefinitionPaths[index]}");
                    enemies.GetArrayElementAtIndex(index).objectReferenceValue = definition;
                }
                controllerSerialized.FindProperty("toggleKey").intValue = (int)KeyCode.U;
                controllerSerialized.FindProperty("informationCanvas").objectReferenceValue = canvasObject;
                controllerSerialized.FindProperty("sectionTitleText").objectReferenceValue = sectionTitle;
                controllerSerialized.FindProperty("contentText").objectReferenceValue = content;
                controllerSerialized.FindProperty("characterTabButton").objectReferenceValue = characterButton;
                controllerSerialized.FindProperty("recordsTabButton").objectReferenceValue = recordsButton;
                controllerSerialized.FindProperty("encyclopediaTabButton").objectReferenceValue = encyclopediaButton;
                controllerSerialized.FindProperty("questsTabButton").objectReferenceValue = questsButton;
                controllerSerialized.FindProperty("upgradesTabButton").objectReferenceValue = upgradesButton;
                controllerSerialized.FindProperty("closeButton").objectReferenceValue = closeButton;
                controllerSerialized.ApplyModifiedPropertiesWithoutUndo();

                var shellSerialized = new SerializedObject(shell);
                shellSerialized.FindProperty("playerSessionRecords").objectReferenceValue = records;
                shellSerialized.FindProperty("informationWindow").objectReferenceValue = controller;
                shellSerialized.ApplyModifiedPropertiesWithoutUndo();

                canvasObject.SetActive(false);
                EditorUtility.SetDirty(records);
                EditorUtility.SetDirty(controller);
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

        private static Button CreateTabButton(
            Transform parent,
            string name,
            string label,
            Font font,
            int index)
        {
            Button button = CreateButton(parent, name, label, font, 18, out _);
            RectTransform rect = button.transform as RectTransform;
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(1f, 1f);
            rect.pivot = new Vector2(0.5f, 1f);
            rect.anchoredPosition = new Vector2(0f, -18f - index * 62f);
            rect.sizeDelta = new Vector2(-28f, 48f);
            return button;
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
            PersistentGameplayShell shell = root.GetComponent<PersistentGameplayShell>();
            PlayerSessionRecords[] records =
                root.GetComponentsInChildren<PlayerSessionRecords>(true);
            InformationWindowController[] controllers =
                root.GetComponentsInChildren<InformationWindowController>(true);
            Require(shell != null, "PersistentGameplayShell root component is missing.");
            Require(records.Length == 1,
                $"Expected one root PlayerSessionRecords, found {records.Length}.");
            Require(controllers.Length == 1,
                $"Expected one root InformationWindowController, found {controllers.Length}.");
            Require(shell.PlayerSessionRecords == records[0] &&
                    shell.InformationWindow == controllers[0],
                "PersistentGameplayShell information references are missing or point elsewhere.");
            Require(records[0].gameObject == root && records[0].enabled,
                "PlayerSessionRecords must be enabled on the shell root.");
            Require(controllers[0].gameObject == root && controllers[0].enabled,
                "InformationWindowController must be enabled on the shell root.");
            Require(records[0].IsConfigured, "PlayerSessionRecords is not fully configured.");
            Require(controllers[0].IsConfigured,
                "InformationWindowController is not fully configured.");

            List<Transform> informationCanvases =
                FindDirectChildren(root.transform, InformationCanvasName);
            Require(informationCanvases.Count == 1,
                $"Expected one direct child '{InformationCanvasName}', found {informationCanvases.Count}.");
            Transform canvasTransform = informationCanvases[0];
            Require(!canvasTransform.gameObject.activeSelf,
                "InformationCanvas must start inactive.");

            Canvas canvas = canvasTransform.GetComponent<Canvas>();
            CanvasScaler scaler = canvasTransform.GetComponent<CanvasScaler>();
            Require(canvas != null && canvas.enabled &&
                    canvas.renderMode == RenderMode.ScreenSpaceOverlay &&
                    canvas.sortingOrder == InformationSortingOrder,
                "InformationCanvas render/sorting configuration is invalid.");
            GraphicRaycaster raycaster = canvasTransform.GetComponent<GraphicRaycaster>();
            Require(scaler != null && scaler.enabled &&
                    scaler.uiScaleMode == CanvasScaler.ScaleMode.ScaleWithScreenSize &&
                    scaler.referenceResolution == new Vector2(1920f, 1080f) &&
                    scaler.screenMatchMode == CanvasScaler.ScreenMatchMode.MatchWidthOrHeight &&
                    Mathf.Approximately(scaler.matchWidthOrHeight, 0.5f) &&
                    raycaster != null && raycaster.enabled,
                "InformationCanvas scaling or raycaster configuration is invalid.");

            Transform backdrop = canvasTransform.Find("Backdrop");
            Transform window = canvasTransform.Find("Window");
            Transform tabPanel = window != null ? window.Find("TabPanel") : null;
            Transform contentPanel = window != null ? window.Find("ContentPanel") : null;
            Require(backdrop != null && window != null && tabPanel != null && contentPanel != null,
                "InformationCanvas graybox hierarchy is incomplete.");
            RectTransform backdropRect = backdrop as RectTransform;
            Image backdropImage = backdrop.GetComponent<Image>();
            RectTransform windowRect = window as RectTransform;
            Image windowImage = window.GetComponent<Image>();
            Require(backdropRect != null && backdropRect.anchorMin == Vector2.zero &&
                    backdropRect.anchorMax == Vector2.one && backdropRect.offsetMin == Vector2.zero &&
                    backdropRect.offsetMax == Vector2.zero && backdropImage != null &&
                    backdropImage.raycastTarget,
                "Information backdrop must fill the screen and block pointer input.");
            Require(windowRect != null && windowRect.sizeDelta == new Vector2(1080f, 680f) &&
                    windowImage != null && windowImage.raycastTarget &&
                    contentPanel.GetComponent<RectMask2D>() != null,
                "Information window size, raycast surface, or content mask is invalid.");

            EventSystem[] eventSystems = root.GetComponentsInChildren<EventSystem>(true);
            Require(eventSystems.Length == 1 && eventSystems[0] == shell.PlayerEventSystem,
                $"Persistent shell EventSystem count/identity is invalid: {eventSystems.Length}.");

            var recordsSerialized = new SerializedObject(records[0]);
            Require(recordsSerialized.FindProperty("questJournal").objectReferenceValue ==
                    shell.QuestJournal,
                "PlayerSessionRecords does not reference the shell QuestJournal.");
            Require(recordsSerialized.FindProperty("raidCheckpoint").objectReferenceValue ==
                    shell.RaidCheckpoint,
                "PlayerSessionRecords does not reference the shell RaidCheckpointController.");

            var controllerSerialized = new SerializedObject(controllers[0]);
            Require(controllerSerialized.FindProperty("shell").objectReferenceValue == shell,
                "InformationWindowController does not reference the persistent shell.");
            Require(controllerSerialized.FindProperty("informationCanvas").objectReferenceValue ==
                    canvasTransform.gameObject,
                "InformationWindowController does not reference InformationCanvas.");
            PlayerWeaponController[] weaponControllers =
                root.GetComponentsInChildren<PlayerWeaponController>(true);
            Require(weaponControllers.Length == 1 &&
                    controllerSerialized.FindProperty("weaponController").objectReferenceValue ==
                    weaponControllers[0],
                "InformationWindowController weapon reference is missing or ambiguous.");
            Require(controllerSerialized.FindProperty("toggleKey").intValue == (int)KeyCode.U,
                "InformationWindowController prototype key is not U.");

            string[] ownedUiProperties =
            {
                "sectionTitleText", "contentText", "characterTabButton", "recordsTabButton",
                "encyclopediaTabButton", "questsTabButton", "upgradesTabButton", "closeButton"
            };
            foreach (string propertyName in ownedUiProperties)
            {
                UnityEngine.Object reference =
                    controllerSerialized.FindProperty(propertyName).objectReferenceValue;
                Component component = reference as Component;
                Require(component != null && component.transform.IsChildOf(canvasTransform),
                    $"Information UI reference '{propertyName}' is missing or outside InformationCanvas.");
            }

            SerializedProperty enemies = controllerSerialized.FindProperty("enemyDefinitions");
            Require(enemies.arraySize == EnemyDefinitionPaths.Length,
                $"Expected {EnemyDefinitionPaths.Length} enemy definitions, found {enemies.arraySize}.");
            var uniqueEnemies = new HashSet<EnemyDefinition>();
            for (int index = 0; index < EnemyDefinitionPaths.Length; index++)
            {
                EnemyDefinition expected =
                    AssetDatabase.LoadAssetAtPath<EnemyDefinition>(EnemyDefinitionPaths[index]);
                EnemyDefinition actual = enemies.GetArrayElementAtIndex(index).objectReferenceValue
                    as EnemyDefinition;
                Require(expected != null && actual == expected && actual.AI != null &&
                        uniqueEnemies.Add(actual),
                    $"Enemy definition reference {index} is missing, duplicated, or unexpected.");
            }

            Require(CountMissingScripts(root) == 0,
                "PersistentGameplayShell contains missing scripts after information setup.");
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
            int fontSize,
            out Text labelText)
        {
            GameObject gameObject = CreateRectObject(parent, name);
            Image image = gameObject.AddComponent<Image>();
            image.color = new Color(0.22f, 0.24f, 0.3f, 1f);
            Button button = gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            ColorBlock colors = button.colors;
            colors.highlightedColor = new Color(0.36f, 0.39f, 0.49f, 1f);
            colors.pressedColor = new Color(0.13f, 0.15f, 0.2f, 1f);
            colors.selectedColor = colors.highlightedColor;
            colors.disabledColor = new Color(0.12f, 0.38f, 0.5f, 1f);
            button.colors = colors;

            labelText = CreateText(
                gameObject.transform,
                "Label",
                label,
                font,
                fontSize,
                TextAnchor.MiddleCenter);
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

        private static void SetCenteredRect(RectTransform rect, Vector2 position, Vector2 size)
        {
            Require(rect != null, "A required UI RectTransform is missing.");
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
        }

        private static void SetTopStretchRect(
            RectTransform rect,
            float left,
            float top,
            float right,
            float height)
        {
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = Vector2.one;
            rect.pivot = new Vector2(0.5f, 1f);
            rect.offsetMin = new Vector2(left, -top - height);
            rect.offsetMax = new Vector2(-right, -top);
        }

        private static void SetTopRightRect(RectTransform rect, Vector2 position, Vector2 size)
        {
            Require(rect != null, "A required UI RectTransform is missing.");
            rect.anchorMin = Vector2.one;
            rect.anchorMax = Vector2.one;
            rect.pivot = Vector2.one;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
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

        private static List<Transform> FindDirectChildren(Transform parent, string name)
        {
            var matches = new List<Transform>();
            for (int index = 0; index < parent.childCount; index++)
            {
                Transform child = parent.GetChild(index);
                if (child.name == name)
                {
                    matches.Add(child);
                }
            }
            return matches;
        }

        private static void EnsureEditorReadyAndScenesClean()
        {
            if (AssetDatabase.IsAssetImportWorkerProcess() ||
                EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException(
                    "Information setup requires the main Unity Editor idle in Edit Mode.");
            }

            for (int index = 0; index < SceneManager.sceneCount; index++)
            {
                Scene scene = SceneManager.GetSceneAt(index);
                if (scene.isDirty)
                {
                    throw new BuildFailedException(
                        $"Information setup stopped because open scene '{scene.name}' has unsaved changes.");
                }
            }
        }

        private static void Require(bool condition, string message)
        {
            if (!condition)
            {
                throw new BuildFailedException(message ?? "Information prototype validation failed.");
            }
        }
    }
}
