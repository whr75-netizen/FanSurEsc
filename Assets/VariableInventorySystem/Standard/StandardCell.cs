using UnityEngine;
using UnityEngine.UI;

namespace VariableInventorySystem
{
    public class StandardCell : VariableInventoryCell
    {
        [SerializeField] Vector2 defaultCellSize;
        [SerializeField] Vector2 margineSpace;

        [SerializeField] RectTransform sizeRoot;
        [SerializeField] RectTransform target;
        [SerializeField] Graphic background;
        [SerializeField] RawImage cellImage;
        [SerializeField] Graphic highlight;
        [SerializeField] GameObject itemBadgeRoot;
        [SerializeField] Text itemBadgeText;

        [SerializeField] StandardButton button;

        public override Vector2 DefaultCellSize => defaultCellSize;
        public override Vector2 MargineSpace => margineSpace;
        protected override IVariableInventoryCellActions ButtonActions => button;
        protected virtual StandardAssetLoader Loader { get; set; }

        protected bool isSelectable = true;
        private bool contentVisible = true;
        private string badgeText;
        private int imageRequestVersion;
        protected IVariableInventoryAsset currentImageAsset;

        public Vector2 GetCellSize()
        {
            var width = ((CellData?.Width ?? 1) * (defaultCellSize.x + margineSpace.x)) - margineSpace.x;
            var height = ((CellData?.Height ?? 1) * (defaultCellSize.y + margineSpace.y)) - margineSpace.y;
            return new Vector2(width, height);
        }

        public Vector2 GetRotateCellSize()
        {
            var isRotate = CellData?.IsRotate ?? false;
            var cellSize = GetCellSize();
            if (isRotate)
            {
                var tmp = cellSize.x;
                cellSize.x = cellSize.y;
                cellSize.y = tmp;
            }

            return cellSize;
        }

        public override void SetSelectable(bool value)
        {
            ButtonActions.SetActive(value);
            isSelectable = value;
        }

        public virtual void SetHighLight(bool value)
        {
            highlight.gameObject.SetActive(value);
        }

        public void SetContentVisible(bool visible)
        {
            contentVisible = visible;
            OnApply();
        }

        public void SetBadgeText(string value)
        {
            badgeText = value;
            RefreshBadge();
        }

        protected override void OnApply()
        {
            SetHighLight(false);
            target.gameObject.SetActive(CellData != null && contentVisible);
            ApplySize();

            if (CellData == null)
            {
                imageRequestVersion++;
                currentImageAsset = null;
                cellImage.texture = null;
                cellImage.gameObject.SetActive(false);
                background.gameObject.SetActive(false);
            }
            else
            {
                // update cell image
                if (currentImageAsset != CellData.ImageAsset)
                {
                    currentImageAsset = CellData.ImageAsset;
                    IVariableInventoryAsset requestedAsset = currentImageAsset;
                    int requestVersion = ++imageRequestVersion;

                    cellImage.gameObject.SetActive(false);
                    if (Loader == null)
                    {
                        Loader = new StandardAssetLoader();
                    }

                    StartCoroutine(Loader.LoadAsync(requestedAsset, tex =>
                    {
                        if (requestVersion != imageRequestVersion || CellData == null ||
                            currentImageAsset != requestedAsset)
                        {
                            return;
                        }

                        cellImage.texture = tex;
                        cellImage.gameObject.SetActive(contentVisible && tex != null);
                    }));
                }
                else
                {
                    cellImage.gameObject.SetActive(contentVisible && cellImage.texture != null);
                }

                background.gameObject.SetActive(contentVisible && isSelectable);
            }

            RefreshBadge();
        }

        private void RefreshBadge()
        {
            if (itemBadgeRoot == null || itemBadgeText == null)
            {
                return;
            }

            bool show = CellData != null && contentVisible &&
                        !string.IsNullOrWhiteSpace(badgeText);
            if (show)
            {
                itemBadgeText.text = badgeText;
            }

            itemBadgeRoot.SetActive(show);
        }

        protected virtual void ApplySize()
        {
            sizeRoot.sizeDelta = GetRotateCellSize();
            target.sizeDelta = GetCellSize();
            target.localEulerAngles = Vector3.forward * (CellData?.IsRotate ?? false ? 90 : 0);
        }
    }
}
