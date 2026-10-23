using System;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
internal class CommandScript : IRunCommand
{
    public void Execute(ExecutionResult result)
    {
        if (Application.dataPath != "C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets") throw new Exception("Wrong project");
        const string path = "Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab";
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (!asset) throw new Exception("Existing presentation asset missing");
        result.Log("530 PREFAB ASSET READ ONLY; no Instantiate/Play/Render; dirty=" + EditorSceneManager.GetActiveScene().isDirty);
        foreach (var f in asset.GetComponentsInChildren<Full319View335>(true))
        {
            result.Log("full=" + f.name + " style=" + f.styleEnabled + " main=" + f.faceMain + " provider=" + f.faceProvider + " integrated=" + f.integrated);
            var r = f.motion.surface.source[1]; var m = r.sharedMaterials[3];
            result.Log("face=" + m.name + " shader=" + m.shader.name + " tex=" + (m.GetTexture("_MainTex") ? m.GetTexture("_MainTex").name : "null") + " colour=" + m.GetColor("_Color").ToString("R"));
            var p = new SerializedObject(m).FindProperty("m_SavedProperties.m_Floats");
            if (p != null) for (int i = 0; i < p.arraySize; i++)
            {
                var e = p.GetArrayElementAtIndex(i); var k = e.FindPropertyRelative("first").stringValue;
                if (k.Contains("Stage") || k.Contains("Debug") || k.Contains("Probe")) result.Log("face saved[" + k + "]=" + e.FindPropertyRelative("second").floatValue.ToString("R"));
            }
            var providers = asset.GetComponentsInChildren<MonoBehaviour>(true).Where(x => x && x.GetType().FullName.Contains("Vrm"));
            result.Log("VRM components=" + string.Join(",", providers.Select(x => x.GetType().FullName + ":enabled=" + x.enabled)));
            var b = new MaterialPropertyBlock(); r.GetPropertyBlock(b, 3); result.Log("face indexed MPB3 empty=" + b.isEmpty + " stage=" + b.GetFloat("_Auto245Stage"));
        }
    }
}
