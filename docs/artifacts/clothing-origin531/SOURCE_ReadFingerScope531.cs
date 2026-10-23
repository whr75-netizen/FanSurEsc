using UnityEngine;
using UnityEditor;
using System.Linq;
internal class CommandScript:IRunCommand
{
    public void Execute(ExecutionResult result)
    {
        if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets")throw new System.Exception("Wrong project");
        if(EditorApplication.isPlaying)throw new System.Exception("Asset-only Edit inspection required");
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab");
        var f=asset.GetComponentInChildren<Full319View335>(true);var skin=f.motion.surface.source[0];var mesh=skin.sharedMesh;var weights=mesh.boneWeights;
        bool Finger(int b)=>skin.bones[b].name.StartsWith("J_Bip_",System.StringComparison.Ordinal)&&new[]{"_Thumb","_Index","_Middle","_Ring","_Little","_Pinky"}.Any(s=>skin.bones[b].name.IndexOf(s,System.StringComparison.Ordinal)>=0);
        for(int sm=0;sm<mesh.subMeshCount;sm++)
        {
            var ids=mesh.GetTriangles(sm).Distinct().ToArray();int positive=0;float maximum=0;
            foreach(int id in ids){var w=weights[id];float v=(Finger(w.boneIndex0)?w.weight0:0)+(Finger(w.boneIndex1)?w.weight1:0)+(Finger(w.boneIndex2)?w.weight2:0)+(Finger(w.boneIndex3)?w.weight3:0);if(v>0)positive++;maximum=Mathf.Max(maximum,v);}
            result.Log("531 material="+sm+" usedVertices="+ids.Length+" positiveFingerWeightVertices="+positive+" maxFingerWeight="+maximum.ToString("R"));
        }
        result.Log("finger bones="+string.Join(",",skin.bones.Where((b,i)=>Finger(i)).Select(b=>b.name)));
        result.Log("Edit="+!EditorApplication.isPlaying+" cloth="+ClothRegion524.Enabled+" curves="+ClothRegion524.UseOpacityCurves527);
    }
}
