using System;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;

internal class CommandScript : IRunCommand
{
    static string TextureName(Texture t) => t ? t.name + ":" + AssetDatabase.GetAssetPath(t) : "null";
    static string MaterialState(string label, Material m)
    {
        if (!m) return label + "=null";
        var s = new StringBuilder(label + "=" + m.name + " shader=" + (m.shader ? m.shader.name : "null"));
        if (m.shader) s.Append(" supported=" + m.shader.isSupported);
        foreach (var p in new[] { "_Auto245Stage", "_Auto245Local", "_Auto245MembershipEnabled", "_Auto249Probe", "_M_DebugMode" })
            s.Append(" " + p + "=" + (m.HasProperty(p) ? m.GetFloat(p).ToString("R") : "global/notMaterialProperty"));
        if (m.HasProperty("_MainTex")) s.Append(" tex=" + TextureName(m.GetTexture("_MainTex")));
        if (m.HasProperty("_Color")) s.Append(" color=" + m.GetColor("_Color").ToString("R"));
        var saved = new SerializedObject(m).FindProperty("m_SavedProperties.m_Floats");
        if (saved != null) for (int i = 0; i < saved.arraySize; i++)
        {
            var e = saved.GetArrayElementAtIndex(i); var key = e.FindPropertyRelative("first").stringValue;
            if (key.Contains("Stage") || key.Contains("DebugMode") || key.Contains("Probe")) s.Append(" saved[" + key + "]=" + e.FindPropertyRelative("second").floatValue.ToString("R"));
        }
        return s.ToString();
    }
    static string RT(string label, RTHandle t) => label + "=" + (t != null && t.rt ? t.rt.name + ":created=" + t.rt.IsCreated() : "null");
    public void Execute(ExecutionResult result)
    {
        if (Application.dataPath != "C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets") throw new Exception("Wrong project");
        result.Log("530 readonly play=" + EditorApplication.isPlaying + " paused=" + EditorApplication.isPaused + " compiling=" + EditorApplication.isCompiling + " scene=" + EditorSceneManager.GetActiveScene().path + " dirty=" + EditorSceneManager.GetActiveScene().isDirty);
        foreach (var p in new[] { "_Auto245Stage", "_Auto245Local", "_Auto245MembershipEnabled", "_Auto249Probe", "_Style297Enabled" }) result.Log("global " + p + "=" + Shader.GetGlobalFloat(p).ToString("R"));
        foreach (var f in UnityEngine.Object.FindObjectsByType<Full319View335>(FindObjectsInactive.Include, FindObjectsSortMode.None))
        {
            result.Log("full=" + f.name + " enabled=" + f.enabled + " style=" + f.styleEnabled + " faceMain=" + f.faceMain + " provider=" + f.faceProvider + " integrated=" + f.integrated);
            if (f.motion && f.motion.materials != null && f.motion.materials.Length > 7) result.Log(MaterialState("probeFace7", f.motion.materials[7]));
            if (f.independentMats != null && f.independentMats.Length > 7) result.Log(MaterialState("independentFace7", f.independentMats[7]));
            if (f.legacySignalsMats != null && f.legacySignalsMats.Length > 7) result.Log(MaterialState("legacyFace7", f.legacySignalsMats[7]));
            result.Log(MaterialState("providerFace", f.legacyProviderMat));
            if (f.motion && f.motion.surface && f.motion.surface.source != null && f.motion.surface.source.Length > 1 && f.motion.surface.source[1])
            {
                var r = f.motion.surface.source[1];
                result.Log("sourceFaceRenderer enabled=" + r.enabled + " layer=" + r.gameObject.layer + " shadow=" + r.shadowCastingMode);
                if (r.sharedMaterials.Length > 3) result.Log(MaterialState("originalFaceSkin3", r.sharedMaterials[3]));
                var block = new MaterialPropertyBlock(); r.GetPropertyBlock(block, 3);
                result.Log("sourceFaceIndexedMPB3 empty=" + block.isEmpty + " tex=" + TextureName(block.GetTexture("_MainTex")) + " stage=" + block.GetFloat("_Auto245Stage"));
            }
            result.Log(RT("prepared", f.prepared)); result.Log(RT("colour", f.colour));
            if (f.layers != null && f.layers.Length > 8) result.Log(RT("faceLayer8", f.layers[8].rgba));
        }
    }
}
