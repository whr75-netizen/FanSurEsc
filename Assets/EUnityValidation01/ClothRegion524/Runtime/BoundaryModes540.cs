#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

// Explicit executable trial modes; no prefab/scene or user settings are saved.
public static class BoundaryModes540
{
    [MenuItem("EValidation/Boundary540/Off (current product)")]
    public static void Off(){ClothRegion524.Enabled=false;ClothRegion524.UseOpacityCurves527=ClothRegion524.UseAreaCurves532=ClothRegion524.UseWholeRegions539=ClothRegion524.UseSpans543=ClothRegion524.UseCompact544=false;Shader.SetGlobalInt("_Cloth524Enabled",0);Refresh();}
    [MenuItem("EValidation/Boundary540/Clothes (outerwear-bottom-shoes)")]
    public static void Clothes(){Trial543(false,ClothRegion524.Clothing540);}
    [MenuItem("EValidation/Boundary540/Experimental Body0 plus clothes (includes hands)")]
    public static void BodyAndClothes(){Trial543(false,ClothRegion524.BodyAndClothing540);}
    [MenuItem("EValidation/Boundary540/Experimental543 Shape only")]
    public static void Shape543(){Trial543(true,ClothRegion524.Clothing540);}
    [MenuItem("EValidation/Boundary540/Clothes543 (validated spans)")]
    public static void Clothes543(){Trial543(true,ClothRegion524.Clothing540,true);}
    static void Trial543(bool shape,int parts,bool compact=false)
    {
        bool oldShape=ClothRegion524.UseSpans543,oldCompact=ClothRegion524.UseCompact544;
        try{ClothRegion524.UseSpans543=shape;ClothRegion524.UseCompact544=compact;Enable(parts);}catch{ClothRegion524.UseSpans543=oldShape;ClothRegion524.UseCompact544=oldCompact;throw;}
    }
    static void Enable(int parts)
    {
        var g=Object.FindFirstObjectByType<Gameplay397>();
        if(!EditorApplication.isPlaying||!g||!g.connected||!g.player||!g.player.ready)throw new System.InvalidOperationException("Boundary540 needs the initialized current gameplay runtime");
        int oldParts=ClothRegion524.PartBits540;bool oldEnabled=ClothRegion524.Enabled,oldOpacity=ClothRegion524.UseOpacityCurves527,oldArea=ClothRegion524.UseAreaCurves532,oldWhole=ClothRegion524.UseWholeRegions539;
        try
        {
            ClothRegion524.PartBits540=parts;ClothRegion524.Enabled=true;ClothRegion524.UseOpacityCurves527=true;ClothRegion524.UseAreaCurves532=false;ClothRegion524.UseWholeRegions539=true;Refresh();
            if(!ClothRegion524.Ready(g.player.host.main))throw new System.InvalidOperationException(ClothRegion524.Status);
        }
        catch
        {
            ClothRegion524.PartBits540=oldParts;ClothRegion524.Enabled=oldEnabled;ClothRegion524.UseOpacityCurves527=oldOpacity;ClothRegion524.UseAreaCurves532=oldArea;ClothRegion524.UseWholeRegions539=oldWhole;Shader.SetGlobalInt("_Cloth524Enabled",0);throw;
        }
    }
    static void Refresh(){var g=Object.FindFirstObjectByType<Gameplay397>();if(EditorApplication.isPlaying&&g&&g.connected&&g.player&&g.player.ready)g.player.host.RenderFrame();}
}
#endif
