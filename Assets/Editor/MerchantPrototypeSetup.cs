using System;
using System.Collections.Generic;
using FantasySurvival.Interaction;
using FantasySurvival.Inventory;
using FantasySurvival.SaveSystem;
using FantasySurvival.Trading;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.EditorTools
{
    public static class MerchantPrototypeSetup
    {
        private const string ShellPrefabPath = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private const string BaseScenePath = "Assets/Scenes/GameMap1.unity";
        private const string ItemDatabasePath = "Assets/GameData/Items/ItemDatabase.asset";
        private const string MerchantObjectName = "Test_MerchantNPC_Base";
        private const string MerchantMaterialPath = "Assets/GameData/Trading/TestMerchantGraybox.mat";

        private static readonly string[] DefinitionPaths =
        {
            "Assets/GameData/Items/Definitions/Handgun.asset",
            "Assets/GameData/Items/Definitions/Handgun2.asset",
            "Assets/GameData/Items/Definitions/Rifle.asset",
            "Assets/GameData/Items/Definitions/SniperRifle.asset",
            "Assets/GameData/Items/Definitions/SubmachineGun.asset"
        };

        private static readonly TradeCurrency[] DefinitionCurrencies =
        {
            TradeCurrency.Silver,
            TradeCurrency.Gold,
            TradeCurrency.Silver,
            TradeCurrency.Gold,
            TradeCurrency.Silver
        };

        [MenuItem("Tools/Fantasy Survival/Merchant/Apply Prototype")]
        public static void ApplyAll()
        {
            EnsureEditorReadyAndScenesClean();
            ConfigureTradeDefinitions();
            ConfigureShellPrefab();
            ConfigureBaseScene();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log(
                "Merchant prototype configured: Player-only Gold/Silver wallet, " +
                "merchant stock IDs 1-5, tabs, and GameMap1 cube NPC.");
        }

        private static void ConfigureTradeDefinitions()
        {
            for (int index = 0; index < DefinitionPaths.Length; index++)
            {
                ItemDefinition definition =
                    AssetDatabase.LoadAssetAtPath<ItemDefinition>(DefinitionPaths[index]);
                if (definition == null)
                {
                    throw new BuildFailedException(
                        $"Required item definition is missing: {DefinitionPaths[index]}");
                }

                var serialized = new SerializedObject(definition);
                serialized.FindProperty("isTradable").boolValue = true;
                serialized.FindProperty("tradeCurrency").enumValueIndex =
                    (int)DefinitionCurrencies[index] - 1;
                serialized.FindProperty("tradePrice").intValue = 100;
                serialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(definition);
            }

            ItemDefinition storageCase = AssetDatabase.LoadAssetAtPath<ItemDefinition>(
                "Assets/GameData/Items/Definitions/StorageCase.asset");
            if (storageCase == null)
            {
                throw new BuildFailedException("StorageCase item definition is missing.");
            }

            var storageSerialized = new SerializedObject(storageCase);
            storageSerialized.FindProperty("isTradable").boolValue = false;
            storageSerialized.FindProperty("tradePrice").intValue = 0;
            storageSerialized.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(storageCase);
        }

        private static void ConfigureShellPrefab()
        {
            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            if (root == null)
            {
                throw new BuildFailedException($"Could not load prefab: {ShellPrefabPath}");
            }

            try
            {
                InventoryUIManager manager = root.GetComponentInChildren<InventoryUIManager>(true);
                if (manager == null)
                {
                    throw new BuildFailedException("PersistentGameplayShell has no InventoryUIManager.");
                }

                var managerSerialized = new SerializedObject(manager);
                GameObject playerPanel = GetRequiredObjectReference<GameObject>(
                    managerSerialized,
                    "playerInventoryPanel");
                GameObject externalPanel = GetRequiredObjectReference<GameObject>(
                    managerSerialized,
                    "externalInventoryPanel");
                StandardStashView playerView = GetRequiredObjectReference<StandardStashView>(
                    managerSerialized,
                    "playerStashView");
                StandardStashView externalView = GetRequiredObjectReference<StandardStashView>(
                    managerSerialized,
                    "externalStashView");

                Font font = root.GetComponentInChildren<Text>(true)?.font;
                if (font == null)
                {
                    font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                }

                GameObject walletRoot = RecreateOwnedUiRoot(playerPanel.transform, "WalletPanel");
                RectTransform playerGridRect = playerView.transform as RectTransform;
                float playerGridTop = GetGridTop(playerGridRect);
                ConfigurePanelRect(
                    walletRoot.GetComponent<RectTransform>(),
                    new Vector2(playerGridRect.anchoredPosition.x, playerGridTop + 26f),
                    new Vector2(530f, 40f));
                Image walletBackground = walletRoot.AddComponent<Image>();
                walletBackground.color = new Color(0.08f, 0.09f, 0.11f, 0.94f);
                walletBackground.raycastTarget = false;
                var walletLayout = walletRoot.AddComponent<HorizontalLayoutGroup>();
                walletLayout.padding = new RectOffset(16, 16, 4, 4);
                walletLayout.spacing = 12f;
                walletLayout.childAlignment = TextAnchor.MiddleCenter;
                walletLayout.childControlWidth = true;
                walletLayout.childControlHeight = true;
                walletLayout.childForceExpandWidth = true;
                walletLayout.childForceExpandHeight = true;

                Text goldText = CreateText(walletRoot.transform, "GoldText", "금  5,000", font, 20);
                Text silverText = CreateText(walletRoot.transform, "SilverText", "은  5,000", font, 20);

                GameObject controlsRoot = RecreateOwnedUiRoot(externalPanel.transform, "MerchantControls");
                RectTransform externalGridRect = externalView.transform as RectTransform;
                float externalGridTop = GetGridTop(externalGridRect);
                ConfigurePanelRect(
                    controlsRoot.GetComponent<RectTransform>(),
                    new Vector2(externalGridRect.anchoredPosition.x, externalGridTop + 52f),
                    new Vector2(530f, 92f));
                Image controlsBackground = controlsRoot.AddComponent<Image>();
                controlsBackground.color = new Color(0.08f, 0.09f, 0.11f, 0.96f);
                controlsBackground.raycastTarget = true;

                GameObject tabsRoot = CreateRectObject(controlsRoot.transform, "Tabs");
                SetAnchoredRect(
                    tabsRoot.GetComponent<RectTransform>(),
                    new Vector2(0f, 28f),
                    new Vector2(510f, 28f));
                var tabsLayout = tabsRoot.AddComponent<HorizontalLayoutGroup>();
                tabsLayout.spacing = 6f;
                tabsLayout.childAlignment = TextAnchor.MiddleCenter;
                tabsLayout.childControlWidth = true;
                tabsLayout.childControlHeight = true;
                tabsLayout.childForceExpandWidth = true;
                tabsLayout.childForceExpandHeight = true;

                Button allButton = CreateButton(tabsRoot.transform, "AllTabButton", "전체", font);
                Button equipmentButton = CreateButton(
                    tabsRoot.transform,
                    "EquipmentTabButton",
                    "장비",
                    font);
                Button otherButton = CreateButton(tabsRoot.transform, "OtherTabButton", "기타", font);

                Text catalogText = CreateText(
                    controlsRoot.transform,
                    "CatalogText",
                    "상품 가격",
                    font,
                    15);
                catalogText.alignment = TextAnchor.MiddleCenter;
                SetAnchoredRect(
                    catalogText.rectTransform,
                    new Vector2(0f, -4f),
                    new Vector2(510f, 24f));

                Text statusText = CreateText(
                    controlsRoot.transform,
                    "StatusText",
                    "Shift+클릭 또는 드래그로 구매·판매",
                    font,
                    14);
                statusText.alignment = TextAnchor.MiddleCenter;
                SetAnchoredRect(
                    statusText.rectTransform,
                    new Vector2(0f, -29f),
                    new Vector2(510f, 22f));

                managerSerialized.FindProperty("goldAmountText").objectReferenceValue = goldText;
                managerSerialized.FindProperty("silverAmountText").objectReferenceValue = silverText;
                managerSerialized.FindProperty("merchantControlsRoot").objectReferenceValue = controlsRoot;
                managerSerialized.FindProperty("merchantAllTabButton").objectReferenceValue = allButton;
                managerSerialized.FindProperty("merchantEquipmentTabButton").objectReferenceValue = equipmentButton;
                managerSerialized.FindProperty("merchantOtherTabButton").objectReferenceValue = otherButton;
                managerSerialized.FindProperty("merchantCatalogText").objectReferenceValue = catalogText;
                managerSerialized.FindProperty("merchantStatusText").objectReferenceValue = statusText;
                SetStartingItemIds(managerSerialized.FindProperty("startingItemIds"));
                managerSerialized.ApplyModifiedPropertiesWithoutUndo();

                controlsRoot.SetActive(false);
                EditorUtility.SetDirty(manager);
                ValidateShellPrefab(root, manager);
                PrefabUtility.SaveAsPrefabAsset(root, ShellPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static void ConfigureBaseScene()
        {
            SceneSetup[] previousSetup = EditorSceneManager.GetSceneManagerSetup();
            try
            {
                Scene scene = EditorSceneManager.OpenScene(BaseScenePath, OpenSceneMode.Single);
                ItemDatabase itemDatabase =
                    AssetDatabase.LoadAssetAtPath<ItemDatabase>(ItemDatabasePath);
                if (itemDatabase == null)
                {
                    throw new BuildFailedException($"ItemDatabase is missing: {ItemDatabasePath}");
                }

                GameObject merchantObject = FindRootByName(scene, MerchantObjectName);
                if (merchantObject == null)
                {
                    merchantObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    merchantObject.name = MerchantObjectName;
                    Undo.RegisterCreatedObjectUndo(merchantObject, "Create Test Merchant");
                    SceneManager.MoveGameObjectToScene(merchantObject, scene);
                }

                Undo.RecordObject(merchantObject.transform, "Configure Test Merchant Transform");
                merchantObject.transform.SetPositionAndRotation(
                    new Vector3(-2f, 1f, 1f),
                    Quaternion.identity);
                merchantObject.transform.localScale = new Vector3(1f, 2f, 1f);

                Renderer renderer = merchantObject.GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.sharedMaterial = GetOrCreateMerchantMaterial();
                    EditorUtility.SetDirty(renderer);
                }

                Merchant merchant = merchantObject.GetComponent<Merchant>();
                if (merchant == null)
                {
                    merchant = Undo.AddComponent<Merchant>(merchantObject);
                }

                if (merchantObject.GetComponent<MerchantInteractable>() == null)
                {
                    Undo.AddComponent<MerchantInteractable>(merchantObject);
                }

                var merchantSerialized = new SerializedObject(merchant);
                merchantSerialized.FindProperty("merchantId").stringValue = "base:merchant_test";
                merchantSerialized.FindProperty("itemDatabase").objectReferenceValue = itemDatabase;
                merchantSerialized.FindProperty("inventoryWidth").intValue = 8;
                merchantSerialized.FindProperty("inventoryHeight").intValue = 9;
                SetStartingItemIds(merchantSerialized.FindProperty("startingItemIds"));
                merchantSerialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(merchant);

                BasePersistenceController persistence = FindSingleComponent<BasePersistenceController>(scene);
                var persistenceSerialized = new SerializedObject(persistence);
                SerializedProperty merchantsProperty =
                    persistenceSerialized.FindProperty("persistentMerchants");
                AppendUniqueMerchantReference(merchantsProperty, merchant);
                persistenceSerialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(persistence);

                EditorSceneManager.MarkSceneDirty(scene);
                ValidateBaseScene(scene, merchant, persistence);
                if (!EditorSceneManager.SaveScene(scene))
                {
                    throw new BuildFailedException("Unity could not save the configured GameMap1 scene.");
                }
            }
            finally
            {
                if (previousSetup.Length > 0)
                {
                    EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
                }
            }
        }

        private static void ValidateShellPrefab(GameObject root, InventoryUIManager manager)
        {
            var serialized = new SerializedObject(manager);
            string[] requiredReferences =
            {
                "goldAmountText",
                "silverAmountText",
                "merchantControlsRoot",
                "merchantAllTabButton",
                "merchantEquipmentTabButton",
                "merchantOtherTabButton",
                "merchantCatalogText",
                "merchantStatusText"
            };

            foreach (string propertyName in requiredReferences)
            {
                if (serialized.FindProperty(propertyName)?.objectReferenceValue == null)
                {
                    throw new BuildFailedException(
                        $"InventoryUIManager merchant reference '{propertyName}' was not configured.");
                }
            }

            if (CountMissingScripts(root) != 0)
            {
                throw new BuildFailedException("PersistentGameplayShell contains missing scripts after merchant setup.");
            }
        }

        private static void ValidateBaseScene(
            Scene scene,
            Merchant merchant,
            BasePersistenceController persistence)
        {
            Merchant[] merchants = FindComponentsInScene<Merchant>(scene);
            int matchingIdCount = 0;
            foreach (Merchant candidate in merchants)
            {
                if (candidate.MerchantId == "base:merchant_test")
                {
                    matchingIdCount++;
                }
            }

            if (matchingIdCount != 1 || merchant.GetComponent<MerchantInteractable>() == null ||
                merchant.GetComponent<Collider>() == null)
            {
                throw new BuildFailedException(
                    "GameMap1 test merchant validation failed: invalid component or duplicate ID.");
            }

            if (!merchant.TryValidateAuthoring(out string error))
            {
                throw new BuildFailedException(
                    $"GameMap1 test merchant authoring is invalid: {error}");
            }

            var persistenceSerialized = new SerializedObject(persistence);
            SerializedProperty bindings = persistenceSerialized.FindProperty("persistentMerchants");
            bool containsMerchant = false;
            for (int index = 0; index < bindings.arraySize; index++)
            {
                if (bindings.GetArrayElementAtIndex(index).objectReferenceValue == merchant)
                {
                    containsMerchant = true;
                    break;
                }
            }

            if (!containsMerchant)
            {
                throw new BuildFailedException(
                    "BasePersistenceController does not reference the authored merchant.");
            }

            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (CountMissingScripts(root) != 0)
                {
                    throw new BuildFailedException("GameMap1 contains missing scripts after merchant setup.");
                }
            }
        }

        private static Material GetOrCreateMerchantMaterial()
        {
            const string folderPath = "Assets/GameData/Trading";
            if (!AssetDatabase.IsValidFolder(folderPath))
            {
                AssetDatabase.CreateFolder("Assets/GameData", "Trading");
            }

            Material material = AssetDatabase.LoadAssetAtPath<Material>(MerchantMaterialPath);
            if (material == null)
            {
                Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
                if (shader == null)
                {
                    throw new BuildFailedException("No compatible graybox shader is available.");
                }

                material = new Material(shader) { name = "TestMerchantGraybox" };
                AssetDatabase.CreateAsset(material, MerchantMaterialPath);
            }

            Color color = new Color(0.16f, 0.58f, 0.55f, 1f);
            if (material.HasProperty("_BaseColor"))
            {
                material.SetColor("_BaseColor", color);
            }
            if (material.HasProperty("_Color"))
            {
                material.SetColor("_Color", color);
            }
            EditorUtility.SetDirty(material);
            return material;
        }

        private static GameObject RecreateOwnedUiRoot(Transform parent, string name)
        {
            Transform existing = parent.Find(name);
            if (existing != null)
            {
                UnityEngine.Object.DestroyImmediate(existing.gameObject);
            }

            return CreateRectObject(parent, name);
        }

        private static GameObject CreateRectObject(Transform parent, string name)
        {
            var gameObject = new GameObject(name, typeof(RectTransform));
            gameObject.transform.SetParent(parent, false);
            return gameObject;
        }

        private static Text CreateText(
            Transform parent,
            string name,
            string value,
            Font font,
            int fontSize)
        {
            GameObject gameObject = CreateRectObject(parent, name);
            Text text = gameObject.AddComponent<Text>();
            text.font = font;
            text.fontSize = fontSize;
            text.text = value;
            text.alignment = TextAnchor.MiddleCenter;
            text.color = Color.white;
            text.raycastTarget = false;
            return text;
        }

        private static Button CreateButton(
            Transform parent,
            string name,
            string label,
            Font font)
        {
            GameObject gameObject = CreateRectObject(parent, name);
            Image image = gameObject.AddComponent<Image>();
            image.color = new Color(0.22f, 0.24f, 0.28f, 1f);
            Button button = gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            ColorBlock colors = button.colors;
            colors.highlightedColor = new Color(0.34f, 0.37f, 0.43f, 1f);
            colors.pressedColor = new Color(0.14f, 0.16f, 0.19f, 1f);
            colors.selectedColor = colors.highlightedColor;
            button.colors = colors;

            Text text = CreateText(gameObject.transform, "Label", label, font, 16);
            RectTransform textRect = text.rectTransform;
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = Vector2.zero;
            textRect.offsetMax = Vector2.zero;
            return button;
        }

        private static void ConfigurePanelRect(
            RectTransform rect,
            Vector2 anchoredPosition,
            Vector2 size)
        {
            SetAnchoredRect(rect, anchoredPosition, size);
            rect.SetAsLastSibling();
        }

        private static void SetAnchoredRect(
            RectTransform rect,
            Vector2 anchoredPosition,
            Vector2 size)
        {
            rect.anchorMin = new Vector2(0.5f, 0.5f);
            rect.anchorMax = new Vector2(0.5f, 0.5f);
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.anchoredPosition = anchoredPosition;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
        }

        private static float GetGridTop(RectTransform grid)
        {
            if (grid == null)
            {
                throw new BuildFailedException("Inventory grid RectTransform is missing.");
            }

            return grid.anchoredPosition.y + grid.rect.height * 0.5f;
        }

        private static T GetRequiredObjectReference<T>(
            SerializedObject owner,
            string propertyName) where T : UnityEngine.Object
        {
            SerializedProperty property = owner.FindProperty(propertyName);
            T value = property?.objectReferenceValue as T;
            if (value == null)
            {
                throw new BuildFailedException(
                    $"Required serialized reference '{propertyName}' is missing.");
            }

            return value;
        }

        private static void SetStartingItemIds(SerializedProperty property)
        {
            if (property == null || !property.isArray)
            {
                throw new BuildFailedException("Starting item ID array is missing.");
            }

            property.arraySize = 5;
            for (int index = 0; index < 5; index++)
            {
                property.GetArrayElementAtIndex(index).intValue = index + 1;
            }
        }

        private static void AppendUniqueMerchantReference(
            SerializedProperty property,
            Merchant merchant)
        {
            if (property == null || !property.isArray)
            {
                throw new BuildFailedException("Persistent merchant binding array is missing.");
            }

            for (int index = 0; index < property.arraySize; index++)
            {
                if (property.GetArrayElementAtIndex(index).objectReferenceValue == merchant)
                {
                    return;
                }
            }

            int newIndex = property.arraySize;
            property.arraySize++;
            property.GetArrayElementAtIndex(newIndex).objectReferenceValue = merchant;
        }

        private static T FindSingleComponent<T>(Scene scene) where T : Component
        {
            T[] components = FindComponentsInScene<T>(scene);
            if (components.Length != 1)
            {
                throw new BuildFailedException(
                    $"GameMap1 must contain exactly one {typeof(T).Name}, found {components.Length}.");
            }

            return components[0];
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
                count += GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(
                    transform.gameObject);
            }

            return count;
        }

        private static void EnsureEditorReadyAndScenesClean()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException(
                    "Merchant setup requires an idle Unity Editor in Edit Mode.");
            }

            for (int index = 0; index < SceneManager.sceneCount; index++)
            {
                Scene scene = SceneManager.GetSceneAt(index);
                if (scene.isDirty)
                {
                    throw new BuildFailedException(
                        $"Merchant setup stopped because open scene '{scene.name}' has unsaved changes.");
                }
            }
        }
    }
}
