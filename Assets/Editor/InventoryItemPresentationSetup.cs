using FantasySurvival.Inventory;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.UI;
using VariableInventorySystem;

namespace FantasySurvival.EditorTools
{
    public static class InventoryItemPresentationSetup
    {
        private const string CellPrefabPath =
            "Assets/VariableInventorySystem/Sample/Resources/StandardCell.prefab";
        private const string ShellPrefabPath =
            "Assets/Prefabs/PersistentGameplayShell.prefab";

        [MenuItem("Tools/Fantasy Survival/Inventory/Apply Item Presentation UI")]
        public static void ApplyAll()
        {
            EnsureEditorReady();
            ApplyPrefabAssets();
            AssetDatabase.Refresh();
            Debug.Log(
                "Item presentation UI configured: one shared item tooltip and " +
                "separate merchant price and stack quantity badges.");
        }

        internal static void ApplyPrefabAssets()
        {
            ConfigureCellPrefab();
            ConfigureShellPrefab();
        }

        private static void ConfigureCellPrefab()
        {
            GameObject root = PrefabUtility.LoadPrefabContents(CellPrefabPath);
            if (root == null)
            {
                throw new BuildFailedException($"Could not load prefab: {CellPrefabPath}");
            }

            try
            {
                StandardCell cell = root.GetComponent<StandardCell>();
                if (cell == null)
                {
                    throw new BuildFailedException("StandardCell prefab has no StandardCell component.");
                }

                var cellSerialized = new SerializedObject(cell);
                RectTransform sizeRoot =
                    cellSerialized.FindProperty("sizeRoot")?.objectReferenceValue as RectTransform;
                if (sizeRoot == null)
                {
                    throw new BuildFailedException("StandardCell sizeRoot reference is missing.");
                }

                Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                GameObject badgeRoot = GetOrCreateRectObject(sizeRoot, "TradePriceBadge");
                RectTransform badgeRect = badgeRoot.GetComponent<RectTransform>();
                badgeRect.anchorMin = new Vector2(1f, 0f);
                badgeRect.anchorMax = new Vector2(1f, 0f);
                badgeRect.pivot = new Vector2(1f, 0f);
                badgeRect.anchoredPosition = new Vector2(-3f, 3f);
                badgeRect.sizeDelta = new Vector2(58f, 19f);
                badgeRect.localScale = Vector3.one;
                badgeRect.SetAsLastSibling();

                Image badgeBackground = GetOrAddComponent<Image>(badgeRoot);
                badgeBackground.color = new Color(0.22f, 0.23f, 0.25f, 0.96f);
                badgeBackground.raycastTarget = false;

                CanvasGroup badgeCanvasGroup = GetOrAddComponent<CanvasGroup>(badgeRoot);
                badgeCanvasGroup.alpha = 1f;
                badgeCanvasGroup.interactable = false;
                badgeCanvasGroup.blocksRaycasts = false;
                badgeCanvasGroup.ignoreParentGroups = false;

                GameObject priceObject = GetOrCreateRectObject(badgeRoot.transform, "PriceText");
                RectTransform priceRect = priceObject.GetComponent<RectTransform>();
                StretchToParent(priceRect, new Vector2(3f, 1f), new Vector2(-3f, -1f));
                Text priceText = GetOrAddComponent<Text>(priceObject);
                priceText.font = font;
                priceText.fontSize = 13;
                priceText.resizeTextForBestFit = true;
                priceText.resizeTextMinSize = 8;
                priceText.resizeTextMaxSize = 13;
                priceText.alignment = TextAnchor.MiddleCenter;
                priceText.color = new Color(0.9f, 0.9f, 0.92f, 1f);
                priceText.raycastTarget = false;
                priceText.text = "은 100";

                cellSerialized.FindProperty("itemBadgeRoot").objectReferenceValue = badgeRoot;
                cellSerialized.FindProperty("itemBadgeText").objectReferenceValue = priceText;

                GameObject quantityBadgeRoot = GetOrCreateRectObject(sizeRoot, "ItemQuantityBadge");
                RectTransform quantityBadgeRect = quantityBadgeRoot.GetComponent<RectTransform>();
                quantityBadgeRect.anchorMin = new Vector2(1f, 1f);
                quantityBadgeRect.anchorMax = new Vector2(1f, 1f);
                quantityBadgeRect.pivot = new Vector2(1f, 1f);
                quantityBadgeRect.anchoredPosition = new Vector2(-3f, -3f);
                quantityBadgeRect.sizeDelta = new Vector2(48f, 18f);
                quantityBadgeRect.localScale = Vector3.one;
                quantityBadgeRect.SetAsLastSibling();

                Image quantityBackground = GetOrAddComponent<Image>(quantityBadgeRoot);
                quantityBackground.color = new Color(0.08f, 0.09f, 0.11f, 0.94f);
                quantityBackground.raycastTarget = false;

                CanvasGroup quantityCanvasGroup = GetOrAddComponent<CanvasGroup>(quantityBadgeRoot);
                quantityCanvasGroup.alpha = 1f;
                quantityCanvasGroup.interactable = false;
                quantityCanvasGroup.blocksRaycasts = false;
                quantityCanvasGroup.ignoreParentGroups = false;

                GameObject quantityObject = GetOrCreateRectObject(
                    quantityBadgeRoot.transform,
                    "QuantityText");
                RectTransform quantityRect = quantityObject.GetComponent<RectTransform>();
                StretchToParent(quantityRect, new Vector2(2f, 1f), new Vector2(-2f, -1f));
                Text quantityText = GetOrAddComponent<Text>(quantityObject);
                quantityText.font = font;
                quantityText.fontSize = 12;
                quantityText.resizeTextForBestFit = true;
                quantityText.resizeTextMinSize = 8;
                quantityText.resizeTextMaxSize = 12;
                quantityText.alignment = TextAnchor.MiddleCenter;
                quantityText.color = Color.white;
                quantityText.raycastTarget = false;
                quantityText.text = "1/10";

                cellSerialized.FindProperty("quantityBadgeRoot").objectReferenceValue =
                    quantityBadgeRoot;
                cellSerialized.FindProperty("quantityBadgeText").objectReferenceValue =
                    quantityText;
                cellSerialized.ApplyModifiedPropertiesWithoutUndo();
                badgeRoot.SetActive(false);
                quantityBadgeRoot.SetActive(false);

                ValidateCellPrefab(root, cell);
                PrefabUtility.SaveAsPrefabAsset(root, CellPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
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

                Transform canvasTransform = root.transform.Find("CellParentObject/CellParent");
                if (!(canvasTransform is RectTransform canvasRect))
                {
                    throw new BuildFailedException(
                        "PersistentGameplayShell tooltip Canvas path is missing: " +
                        "CellParentObject/CellParent");
                }

                Canvas rootCanvas = canvasTransform.GetComponent<Canvas>();
                if (rootCanvas == null)
                {
                    throw new BuildFailedException("CellParent has no Canvas component.");
                }

                Font font = root.GetComponentInChildren<Text>(true)?.font;
                if (font == null)
                {
                    font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                }

                GameObject tooltipObject = GetOrCreateRectObject(canvasRect, "ItemTooltip");
                RectTransform tooltipRect = tooltipObject.GetComponent<RectTransform>();
                tooltipRect.anchorMin = new Vector2(0.5f, 0.5f);
                tooltipRect.anchorMax = new Vector2(0.5f, 0.5f);
                tooltipRect.pivot = new Vector2(0f, 1f);
                tooltipRect.anchoredPosition = Vector2.zero;
                tooltipRect.sizeDelta = new Vector2(320f, 270f);
                tooltipRect.localScale = Vector3.one;
                tooltipRect.SetAsLastSibling();

                Canvas tooltipCanvas = GetOrAddComponent<Canvas>(tooltipObject);
                tooltipCanvas.overrideSorting = true;
                tooltipCanvas.sortingOrder = 100;

                CanvasGroup tooltipGroup = GetOrAddComponent<CanvasGroup>(tooltipObject);
                tooltipGroup.alpha = 1f;
                tooltipGroup.interactable = false;
                tooltipGroup.blocksRaycasts = false;
                tooltipGroup.ignoreParentGroups = false;

                Image tooltipBackground = GetOrAddComponent<Image>(tooltipObject);
                tooltipBackground.color = new Color(0.075f, 0.08f, 0.095f, 0.97f);
                tooltipBackground.raycastTarget = false;

                Text nameText = ConfigureText(
                    tooltipObject.transform,
                    "NameText",
                    font,
                    21,
                    FontStyle.Bold,
                    new Vector2(12f, -10f),
                    new Vector2(296f, 30f),
                    Color.white);
                Text descriptionText = ConfigureText(
                    tooltipObject.transform,
                    "DescriptionText",
                    font,
                    13,
                    FontStyle.Normal,
                    new Vector2(12f, -48f),
                    new Vector2(296f, 54f),
                    new Color(0.77f, 0.79f, 0.83f, 1f));
                Text statsText = ConfigureText(
                    tooltipObject.transform,
                    "StatsText",
                    font,
                    14,
                    FontStyle.Normal,
                    new Vector2(12f, -110f),
                    new Vector2(296f, 148f),
                    new Color(0.92f, 0.92f, 0.94f, 1f));

                InventoryItemTooltipView tooltipView =
                    GetOrAddComponent<InventoryItemTooltipView>(tooltipObject);
                var tooltipSerialized = new SerializedObject(tooltipView);
                tooltipSerialized.FindProperty("rootCanvas").objectReferenceValue = rootCanvas;
                tooltipSerialized.FindProperty("panel").objectReferenceValue = tooltipRect;
                tooltipSerialized.FindProperty("nameText").objectReferenceValue = nameText;
                tooltipSerialized.FindProperty("descriptionText").objectReferenceValue = descriptionText;
                tooltipSerialized.FindProperty("statsText").objectReferenceValue = statsText;
                tooltipSerialized.ApplyModifiedPropertiesWithoutUndo();

                var managerSerialized = new SerializedObject(manager);
                managerSerialized.FindProperty("itemTooltipView").objectReferenceValue = tooltipView;
                managerSerialized.ApplyModifiedPropertiesWithoutUndo();
                tooltipObject.SetActive(false);

                ValidateShellPrefab(root, manager, tooltipView);
                PrefabUtility.SaveAsPrefabAsset(root, ShellPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        private static Text ConfigureText(
            Transform parent,
            string name,
            Font font,
            int fontSize,
            FontStyle fontStyle,
            Vector2 topLeftOffset,
            Vector2 size,
            Color color)
        {
            GameObject textObject = GetOrCreateRectObject(parent, name);
            RectTransform rect = textObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = topLeftOffset;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;

            Text text = GetOrAddComponent<Text>(textObject);
            text.font = font;
            text.fontSize = fontSize;
            text.fontStyle = fontStyle;
            text.alignment = TextAnchor.UpperLeft;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Truncate;
            text.color = color;
            text.raycastTarget = false;
            text.text = string.Empty;
            return text;
        }

        private static GameObject GetOrCreateRectObject(Transform parent, string name)
        {
            Transform existing = parent.Find(name);
            if (existing != null)
            {
                if (!(existing is RectTransform))
                {
                    throw new BuildFailedException($"UI object '{name}' is not a RectTransform.");
                }

                return existing.gameObject;
            }

            var created = new GameObject(name, typeof(RectTransform));
            created.transform.SetParent(parent, false);
            return created;
        }

        private static T GetOrAddComponent<T>(GameObject gameObject) where T : Component
        {
            T component = gameObject.GetComponent<T>();
            return component != null ? component : gameObject.AddComponent<T>();
        }

        private static void StretchToParent(
            RectTransform rect,
            Vector2 offsetMin,
            Vector2 offsetMax)
        {
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.offsetMin = offsetMin;
            rect.offsetMax = offsetMax;
            rect.localScale = Vector3.one;
        }

        private static void ValidateCellPrefab(GameObject root, StandardCell cell)
        {
            var serialized = new SerializedObject(cell);
            GameObject badgeRoot =
                serialized.FindProperty("itemBadgeRoot")?.objectReferenceValue as GameObject;
            if (badgeRoot == null ||
                serialized.FindProperty("itemBadgeText")?.objectReferenceValue == null)
            {
                throw new BuildFailedException("StandardCell price badge references are incomplete.");
            }

            GameObject quantityBadgeRoot =
                serialized.FindProperty("quantityBadgeRoot")?.objectReferenceValue as GameObject;
            if (quantityBadgeRoot == null ||
                serialized.FindProperty("quantityBadgeText")?.objectReferenceValue == null)
            {
                throw new BuildFailedException("StandardCell quantity badge references are incomplete.");
            }

            CanvasGroup group = badgeRoot.GetComponent<CanvasGroup>();
            if (group == null || group.blocksRaycasts || group.interactable)
            {
                throw new BuildFailedException("StandardCell price badge can intercept pointer input.");
            }

            CanvasGroup quantityGroup = quantityBadgeRoot.GetComponent<CanvasGroup>();
            if (quantityGroup == null || quantityGroup.blocksRaycasts || quantityGroup.interactable)
            {
                throw new BuildFailedException("StandardCell quantity badge can intercept pointer input.");
            }

            if (CountMissingScripts(root) != 0)
            {
                throw new BuildFailedException("StandardCell contains missing scripts after UI setup.");
            }
        }

        private static void ValidateShellPrefab(
            GameObject root,
            InventoryUIManager manager,
            InventoryItemTooltipView tooltipView)
        {
            var managerSerialized = new SerializedObject(manager);
            if (managerSerialized.FindProperty("itemTooltipView")?.objectReferenceValue != tooltipView)
            {
                throw new BuildFailedException("InventoryUIManager tooltip reference was not configured.");
            }

            if (!tooltipView.TryValidateReferences(out string tooltipError))
            {
                throw new BuildFailedException(tooltipError);
            }

            Canvas tooltipCanvas = tooltipView.GetComponent<Canvas>();
            CanvasGroup tooltipGroup = tooltipView.GetComponent<CanvasGroup>();
            if (tooltipCanvas == null || !tooltipCanvas.overrideSorting ||
                tooltipCanvas.sortingOrder < 2 || tooltipGroup == null ||
                tooltipGroup.blocksRaycasts || tooltipGroup.interactable)
            {
                throw new BuildFailedException(
                    "Item tooltip sorting or pointer pass-through configuration is invalid.");
            }

            if (CountMissingScripts(root) != 0)
            {
                throw new BuildFailedException(
                    "PersistentGameplayShell contains missing scripts after item UI setup.");
            }
        }

        private static int CountMissingScripts(GameObject root)
        {
            int count = GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(root);
            foreach (Transform child in root.transform)
            {
                count += CountMissingScripts(child.gameObject);
            }

            return count;
        }

        private static void EnsureEditorReady()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                throw new BuildFailedException("Exit Play Mode before applying item presentation UI.");
            }

            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException(
                    "Wait for Unity compilation and asset import to finish before applying item presentation UI.");
            }
        }
    }
}
