using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static partial class PixelDeskLightingProbe
{
    public static void SetScreenPixelSize(int size)
    {
        if(EditorApplication.isPlaying||size<1||size>8)throw new InvalidOperationException("Edit mode; size 1..8.");
        var root=GameObject.Find(RootName).transform.Find("B_Actual12Meshes_LiveShading").gameObject;
        var subject=root.GetComponent<FantasySurvival.CharacterPresentation.CharacterSilhouetteSubject>();
        if(subject==null)subject=Undo.AddComponent<FantasySurvival.CharacterPresentation.CharacterSilhouetteSubject>(root);
        var serialized=new SerializedObject(subject);
        serialized.FindProperty("pixelCellSurface").boolValue=true;
        serialized.FindProperty("pixelCellSize").intValue=size;
        serialized.FindProperty("screenSpacePixelColor").boolValue=false;
        serialized.FindProperty("adaptiveToneExperiment").boolValue=false;
        serialized.ApplyModifiedProperties();PrefabUtility.RecordPrefabInstancePropertyModifications(subject);
        EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
    }

    [Serializable] public class RepairEvidence
    {
        public string lighting; public float imageOpaqueBottom, modelMinimumY;
        public int actualMeshCount; public bool materialPreserved;
    }

    // Existing source projection is preserved; only the card's depth placement changes.
    public static void RepairExisting()
    {
        if(EditorApplication.isPlaying||SceneManager.GetActiveScene().name!="GameMap1")
            throw new InvalidOperationException("Edit-mode base scene required.");
        var root=GameObject.Find(RootName);var spec=ReadSpec();
        var image=root.transform.Find("A_FinalPNG_FixedShading/FinalPNG_174x155");
        var model=root.transform.Find("B_Actual12Meshes_LiveShading");
        var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(AssetsPath+"/desk.png");
        var pixels=texture.GetPixels32();int bottom=texture.height;
        for(int y=0;y<texture.height;y++)
            for(int x=0;x<texture.width;x++)if(pixels[y*texture.width+x].a>0)bottom=Math.Min(bottom,y);
        Vector3 right=Map(spec.camera.r),up=Map(spec.camera.u),view=Map(spec.camera.d);
        float halfW=spec.camera.width/(2*spec.camera.ppu),halfH=spec.camera.height/(2*spec.camera.ppu);
        float centerHeight=(halfH-bottom/spec.camera.ppu)/up.y;
        Vector3 center=V(spec.camera.bounds_center_unity);
        center+=view*((centerHeight-center.y)/view.y);
        Vector3 vertical=Vector3.up/up.y;
        var mesh=image.GetComponent<MeshFilter>().sharedMesh;Undo.RecordObject(mesh,"Stand reference PNG on ground");
        mesh.vertices=new[]{center-right*halfW-vertical*halfH,center+right*halfW-vertical*halfH,
            center+right*halfW+vertical*halfH,center-right*halfW+vertical*halfH};
        var normal=new Vector3(view.x,0,view.z).normalized;
        mesh.normals=new[]{normal,normal,normal,normal};mesh.RecalculateBounds();EditorUtility.SetDirty(mesh);
        // This measured empty patch is outside the grass/puddle/receiver-pillar bounds.
        // Translate the comparison pair together; never alter part transforms.
        Undo.RecordObject(root.transform,"Move comparison to clear base ground");
        root.transform.position=new Vector3(-2.298097f,0,2.298097f)+new Vector3(2.5f,0,-3.5f);
        PrefabUtility.RecordPrefabInstancePropertyModifications(root.transform);
        var materials=model.GetComponentsInChildren<MeshRenderer>().Select(r=>r.sharedMaterial).ToArray();
        foreach(var material in materials)
        {
            Undo.RecordObject(material,"Use existing character RGB lighting strength");
            material.SetFloat("_SteppedLocalLightStrength",.55f);material.SetFloat("_DiagnosticMode",0);
            EditorUtility.SetDirty(material);
        }
        var report=new RepairEvidence{lighting="UniversalFragmentPBR + existing RGB local light * 0.55",
            imageOpaqueBottom=center.y-(halfH-bottom/spec.camera.ppu)/up.y,
            modelMinimumY=model.GetComponentsInChildren<MeshRenderer>().Min(r=>r.bounds.min.y),
            actualMeshCount=model.GetComponentsInChildren<MeshRenderer>().Length,
            materialPreserved=materials.All(m=>m.GetTexture("_BaseMap")==AssetDatabase.LoadAssetAtPath<Texture2D>(AssetsPath+"/wood-grain.png"))};
        if(Mathf.Abs(report.imageOpaqueBottom)>.00001f||report.modelMinimumY<-.00001f||!report.materialPreserved)
            throw new InvalidOperationException("Source/ground contract failed.");
        Directory.CreateDirectory("LocalOnly/PixelUnityProbe23");
        File.WriteAllText("LocalOnly/PixelUnityProbe23/repair.json",JsonUtility.ToJson(report,true));
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
    }
}
