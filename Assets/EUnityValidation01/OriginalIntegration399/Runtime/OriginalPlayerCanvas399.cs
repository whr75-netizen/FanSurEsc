using UnityEngine;
using UnityEngine.UI;

// Displays the validated native render texture beneath the existing screen-space HUD.
// This adds no input, movement, animation, camera or pixel-processing authority.
[DefaultExecutionOrder(900)]
public sealed class OriginalPlayerCanvas399 : MonoBehaviour
{
    private Gameplay397 gameplay;
    private NativePlayer395 player;
    private Canvas canvas;
    private RawImage image;
    private int previousWidth, previousHeight;

    private void LateUpdate()
    {
        if (!gameplay) gameplay=GetComponent<Gameplay397>();
        if (!player) player=GetComponent<NativePlayer395>();
        if (!gameplay || !gameplay.connected || !player.localCamera || !player.localCamera.targetTexture) return;
        if (!canvas)
        {
            foreach (var preview in GetComponentsInChildren<Camera>(true))
                if (preview!=player.gameCamera && preview!=player.localCamera) preview.enabled=false;
            var root=new GameObject("Native character and world display",typeof(RectTransform),typeof(Canvas));
            root.transform.SetParent(transform,false);
            canvas=root.GetComponent<Canvas>();
            canvas.renderMode=RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder=short.MinValue;
            canvas.pixelPerfect=true;
            var picture=new GameObject("Native pixels",typeof(RectTransform),typeof(RawImage));
            picture.transform.SetParent(root.transform,false);
            image=picture.GetComponent<RawImage>();
            image.color=Color.white;
            image.raycastTarget=false;
            image.rectTransform.anchorMin=image.rectTransform.anchorMax=Vector2.zero;
            image.rectTransform.pivot=Vector2.zero;
        }
        image.texture=player.localCamera.targetTexture;
        if (previousWidth!=Screen.width || previousHeight!=Screen.height)
        {
            previousWidth=Screen.width; previousHeight=Screen.height;
            int width=image.texture.width, height=image.texture.height;
            int scale=Mathf.Max(1,Mathf.FloorToInt(Mathf.Min((float)Screen.width/width,(float)Screen.height/height)));
            image.rectTransform.sizeDelta=new Vector2(width*scale,height*scale);
            image.rectTransform.anchoredPosition=new Vector2(Mathf.Floor((Screen.width-width*scale)*.5f),Mathf.Floor((Screen.height-height*scale)*.5f));
        }
    }
}
