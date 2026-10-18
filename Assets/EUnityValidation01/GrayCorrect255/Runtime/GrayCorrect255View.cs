using UnityEngine;
[ExecuteAlways]public sealed class GrayCorrect255View:MonoBehaviour{
 public Eye253R3View source;public Material[]metadata;public ComputeShader correctedLines;public bool fix;public Texture2D triangleVertices;public Material[]originalSource,correctedSource;
 void OnEnable(){Apply();}void Update(){Apply();}
 public void Apply(){if(!source)return;source.sourceMaterials=fix?correctedSource:originalSource;source.Apply();GrayCorrect255Feature.Fix=fix;GrayCorrect255Feature.TriangleVertices=triangleVertices;GrayCorrect255Feature.Camera=EyeSurface253R3Feature.Camera;GrayCorrect255Feature.Renderers=EyeSurface253R3Feature.Renderers;GrayCorrect255Feature.Metadata=metadata;GrayCorrect255Feature.BodyProxy=EyeSurface253R3Feature.BodyProxy;GrayCorrect255Feature.Adapter=EyeSurface253R3Feature.Adapter;GrayCorrect255Feature.Lines=fix&&correctedLines?correctedLines:EyeSurface253R3Feature.Lines;GrayCorrect255Feature.Present=EyeSurface253R3Feature.Present;GrayCorrect255Feature.Enabled=EyeSurface253R3Feature.Enabled;GrayCorrect255Feature.LineTone=EyeSurface253R3Feature.LineTone;}
}
