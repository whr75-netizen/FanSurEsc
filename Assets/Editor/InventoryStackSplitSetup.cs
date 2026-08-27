using FantasySurvival.Inventory;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.UI;

namespace FantasySurvival.EditorTools
{
    public static class InventoryStackSplitSetup
    {
        private const string ShellPrefabPath =
            "Assets/Prefabs/PersistentGameplayShell.prefab";

        [MenuItem("Tools/Fantasy Survival/Inventory/Apply Stack Split UI")]
        public static void Apply()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                throw new BuildFailedException(
                    "Wait for Edit Mode compilation and asset import before applying stack split UI.");
            }

            GameObject root = PrefabUtility.LoadPrefabContents(ShellPrefabPath);
            if (root == null)
            {
                throw new BuildFailedException($"Could not load prefab: {ShellPrefabPath}");
            }

            try
            {
                ConfigurePrefab(root);
                PrefabUtility.SaveAsPrefabAsset(root, ShellPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }

            AssetDatabase.Refresh();
            Debug.Log("Inventory stack split context menu and quantity dialog configured.");
        }

        private static void ConfigurePrefab(GameObject root)
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
                    "PersistentGameplayShell inventory Canvas path is missing.");
            }

            Canvas parentCanvas = canvasRect.GetComponent<Canvas>();
            if (parentCanvas == null)
            {
                throw new BuildFailedException("CellParent has no Canvas component.");
            }

            Font font = root.GetComponentInChildren<Text>(true)?.font;
            if (font == null)
            {
                font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            }

            GameObject overlay = GetOrCreateRectObject(canvasRect, "StackSplitOverlay");
            RectTransform overlayRect = overlay.GetComponent<RectTransform>();
            StretchToParent(overlayRect, Vector2.zero, Vector2.zero);
            overlayRect.SetAsLastSibling();

            Canvas overlayCanvas = GetOrAddComponent<Canvas>(overlay);
            overlayCanvas.overrideSorting = true;
            overlayCanvas.sortingOrder = 160;
            GetOrAddComponent<GraphicRaycaster>(overlay);
            CanvasGroup overlayGroup = GetOrAddComponent<CanvasGroup>(overlay);
            overlayGroup.alpha = 1f;
            overlayGroup.interactable = true;
            overlayGroup.blocksRaycasts = true;
            Image blocker = GetOrAddComponent<Image>(overlay);
            blocker.color = new Color(0f, 0f, 0f, 0.28f);
            blocker.raycastTarget = true;

            RectTransform contextPanel = ConfigurePanel(
                overlay.transform,
                "ContextPanel",
                new Vector2(220f, 206f));
            contextPanel.anchorMin = new Vector2(0.5f, 0.5f);
            contextPanel.anchorMax = new Vector2(0.5f, 0.5f);
            contextPanel.pivot = new Vector2(0f, 1f);

            Text contextItemText = ConfigureText(
                contextPanel,
                "ItemName",
                font,
                15,
                FontStyle.Bold,
                new Vector2(10f, -8f),
                new Vector2(200f, 25f),
                TextAnchor.MiddleLeft,
                Color.white);
            Button useActionButton = ConfigureButton(
                contextPanel,
                "UseButton",
                "사용",
                font,
                new Vector2(10f, -42f),
                new Vector2(200f, 32f));
            Button equipActionButton = ConfigureButton(
                contextPanel,
                "EquipButton",
                "장착",
                font,
                new Vector2(10f, -82f),
                new Vector2(200f, 32f));
            Button splitActionButton = ConfigureButton(
                contextPanel,
                "SplitButton",
                "나누기",
                font,
                new Vector2(10f, -122f),
                new Vector2(200f, 32f));
            Button contextCancelButton = ConfigureButton(
                contextPanel,
                "CloseButton",
                "닫기",
                font,
                new Vector2(10f, -162f),
                new Vector2(200f, 30f));

            RectTransform quantityPanel = ConfigurePanel(
                overlay.transform,
                "QuantityPanel",
                new Vector2(340f, 220f));
            quantityPanel.anchorMin = new Vector2(0.5f, 0.5f);
            quantityPanel.anchorMax = new Vector2(0.5f, 0.5f);
            quantityPanel.pivot = new Vector2(0.5f, 0.5f);
            quantityPanel.anchoredPosition = Vector2.zero;

            Text titleText = ConfigureText(
                quantityPanel,
                "TitleText",
                font,
                20,
                FontStyle.Bold,
                new Vector2(20f, -14f),
                new Vector2(300f, 30f),
                TextAnchor.MiddleCenter,
                Color.white);
            Text rangeText = ConfigureText(
                quantityPanel,
                "RangeText",
                font,
                13,
                FontStyle.Normal,
                new Vector2(20f, -50f),
                new Vector2(300f, 22f),
                TextAnchor.MiddleCenter,
                new Color(0.78f, 0.8f, 0.84f, 1f));
            InputField quantityInput = ConfigureInputField(
                quantityPanel,
                "QuantityInput",
                font,
                new Vector2(60f, -82f),
                new Vector2(220f, 38f));
            Text errorText = ConfigureText(
                quantityPanel,
                "ErrorText",
                font,
                12,
                FontStyle.Normal,
                new Vector2(20f, -126f),
                new Vector2(300f, 24f),
                TextAnchor.MiddleCenter,
                new Color(1f, 0.43f, 0.4f, 1f));
            Button confirmButton = ConfigureButton(
                quantityPanel,
                "ConfirmButton",
                "확인",
                font,
                new Vector2(32f, -166f),
                new Vector2(132f, 36f));
            Button cancelButton = ConfigureButton(
                quantityPanel,
                "CancelButton",
                "취소",
                font,
                new Vector2(176f, -166f),
                new Vector2(132f, 36f));

            InventoryStackSplitDialog dialog =
                GetOrAddComponent<InventoryStackSplitDialog>(overlay);
            SerializedObject dialogSerialized = new SerializedObject(dialog);
            dialogSerialized.FindProperty("rootCanvas").objectReferenceValue = overlayCanvas;
            dialogSerialized.FindProperty("contextPanel").objectReferenceValue = contextPanel;
            dialogSerialized.FindProperty("contextItemText").objectReferenceValue = contextItemText;
            dialogSerialized.FindProperty("useActionButton").objectReferenceValue = useActionButton;
            dialogSerialized.FindProperty("equipActionButton").objectReferenceValue = equipActionButton;
            dialogSerialized.FindProperty("splitActionButton").objectReferenceValue = splitActionButton;
            dialogSerialized.FindProperty("contextCancelButton").objectReferenceValue = contextCancelButton;
            dialogSerialized.FindProperty("quantityPanel").objectReferenceValue = quantityPanel;
            dialogSerialized.FindProperty("titleText").objectReferenceValue = titleText;
            dialogSerialized.FindProperty("rangeText").objectReferenceValue = rangeText;
            dialogSerialized.FindProperty("errorText").objectReferenceValue = errorText;
            dialogSerialized.FindProperty("quantityInput").objectReferenceValue = quantityInput;
            dialogSerialized.FindProperty("confirmButton").objectReferenceValue = confirmButton;
            dialogSerialized.FindProperty("cancelButton").objectReferenceValue = cancelButton;
            dialogSerialized.ApplyModifiedPropertiesWithoutUndo();

            SerializedObject managerSerialized = new SerializedObject(manager);
            managerSerialized.FindProperty("stackSplitDialog").objectReferenceValue = dialog;
            managerSerialized.ApplyModifiedPropertiesWithoutUndo();

            contextPanel.gameObject.SetActive(false);
            quantityPanel.gameObject.SetActive(false);
            overlay.SetActive(false);

            if (!dialog.TryValidateReferences(out string validationError))
            {
                throw new BuildFailedException(validationError);
            }

            if (overlayCanvas.sortingOrder <= parentCanvas.sortingOrder ||
                !overlayCanvas.overrideSorting || !overlayGroup.blocksRaycasts ||
                !overlayGroup.interactable)
            {
                throw new BuildFailedException(
                    "Stack split overlay sorting or input blocking is invalid.");
            }

            if (CountMissingScripts(root) != 0)
            {
                throw new BuildFailedException(
                    "PersistentGameplayShell contains missing scripts after stack split setup.");
            }
        }

        private static RectTransform ConfigurePanel(
            Transform parent,
            string name,
            Vector2 size)
        {
            GameObject panelObject = GetOrCreateRectObject(parent, name);
            RectTransform rect = panelObject.GetComponent<RectTransform>();
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
            Image image = GetOrAddComponent<Image>(panelObject);
            image.color = new Color(0.075f, 0.08f, 0.095f, 0.98f);
            image.raycastTarget = true;
            return rect;
        }

        private static Text ConfigureText(
            Transform parent,
            string name,
            Font font,
            int fontSize,
            FontStyle fontStyle,
            Vector2 topLeft,
            Vector2 size,
            TextAnchor alignment,
            Color color)
        {
            GameObject textObject = GetOrCreateRectObject(parent, name);
            RectTransform rect = textObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = topLeft;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
            Text text = GetOrAddComponent<Text>(textObject);
            text.font = font;
            text.fontSize = fontSize;
            text.fontStyle = fontStyle;
            text.alignment = alignment;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Truncate;
            text.color = color;
            text.raycastTarget = false;
            text.text = string.Empty;
            return text;
        }

        private static Button ConfigureButton(
            Transform parent,
            string name,
            string label,
            Font font,
            Vector2 topLeft,
            Vector2 size)
        {
            GameObject buttonObject = GetOrCreateRectObject(parent, name);
            RectTransform rect = buttonObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = topLeft;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
            Image image = GetOrAddComponent<Image>(buttonObject);
            image.color = new Color(0.22f, 0.24f, 0.29f, 1f);
            Button button = GetOrAddComponent<Button>(buttonObject);
            button.targetGraphic = image;

            Text text = ConfigureText(
                buttonObject.transform,
                "Label",
                font,
                15,
                FontStyle.Bold,
                Vector2.zero,
                size,
                TextAnchor.MiddleCenter,
                Color.white);
            RectTransform textRect = text.rectTransform;
            StretchToParent(textRect, Vector2.zero, Vector2.zero);
            text.text = label;
            return button;
        }

        private static InputField ConfigureInputField(
            Transform parent,
            string name,
            Font font,
            Vector2 topLeft,
            Vector2 size)
        {
            GameObject inputObject = GetOrCreateRectObject(parent, name);
            RectTransform rect = inputObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = topLeft;
            rect.sizeDelta = size;
            rect.localScale = Vector3.one;
            Image background = GetOrAddComponent<Image>(inputObject);
            background.color = new Color(0.16f, 0.17f, 0.2f, 1f);

            Text valueText = ConfigureText(
                inputObject.transform,
                "Text",
                font,
                18,
                FontStyle.Normal,
                new Vector2(10f, 0f),
                new Vector2(size.x - 20f, size.y),
                TextAnchor.MiddleCenter,
                Color.white);
            StretchToParent(valueText.rectTransform, new Vector2(10f, 2f), new Vector2(-10f, -2f));
            Text placeholder = ConfigureText(
                inputObject.transform,
                "Placeholder",
                font,
                16,
                FontStyle.Italic,
                Vector2.zero,
                size,
                TextAnchor.MiddleCenter,
                new Color(0.6f, 0.62f, 0.66f, 1f));
            StretchToParent(placeholder.rectTransform, new Vector2(10f, 2f), new Vector2(-10f, -2f));
            placeholder.text = "1";

            InputField input = GetOrAddComponent<InputField>(inputObject);
            input.targetGraphic = background;
            input.textComponent = valueText;
            input.placeholder = placeholder;
            input.contentType = InputField.ContentType.IntegerNumber;
            input.lineType = InputField.LineType.SingleLine;
            input.characterLimit = 6;
            return input;
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

            GameObject created = new GameObject(name, typeof(RectTransform));
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

        private static int CountMissingScripts(GameObject root)
        {
            int count = GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(root);
            foreach (Transform child in root.transform)
            {
                count += CountMissingScripts(child.gameObject);
            }

            return count;
        }
    }
}
