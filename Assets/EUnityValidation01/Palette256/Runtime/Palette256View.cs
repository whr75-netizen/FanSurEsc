using UnityEngine;
[ExecuteAlways]public sealed class Palette256View:MonoBehaviour{
 public GrayCorrect255View source;public Material[]metadata;public ComputeShader lines;public bool useExistingPalette=true;public Vector4 deepCream,deepSkin;
 void OnEnable(){Apply();}void Update(){Apply();}
 public void Apply(){if(!source)return;source.fix=true;source.Apply();Palette256Feature.Camera=GrayCorrect255Feature.Camera;Palette256Feature.Renderers=GrayCorrect255Feature.Renderers;Palette256Feature.Metadata=metadata;Palette256Feature.BodyProxy=GrayCorrect255Feature.BodyProxy;Palette256Feature.Adapter=GrayCorrect255Feature.Adapter;Palette256Feature.Lines=lines;Palette256Feature.Present=GrayCorrect255Feature.Present;Palette256Feature.Enabled=GrayCorrect255Feature.Enabled;Palette256Feature.LineTone=GrayCorrect255Feature.LineTone;Palette256Feature.Fix=true;Palette256Feature.TriangleVertices=GrayCorrect255Feature.TriangleVertices;Palette256Feature.UsePalette=useExistingPalette;Palette256Feature.DeepCream=deepCream;Palette256Feature.DeepSkin=deepSkin;}
}
