using System;using UnityEngine;using UnityEngine.Rendering;

[Serializable]public sealed class Contour295Eye{public int owner;public Vector2[]parent,iris;public Vector2 pivot,irisAnchor;}
[Serializable]public sealed class Contour295Input{public string sourcePath,sourceSHA256,policy;public Vector2 sample;public Contour295Eye[]eyes;}
public static class Contour295Binding{
 public static void Bind(EyeSkinReview291View review,Contour295Input input,ComputeShader compose,ComputeShader curtain){
  for(int i=0;i<2;i++){var e=input.eyes[i];if(e.owner!=(i==0?2:1)||e.parent.Length!=24||e.iris.Length!=16)throw new Exception("Invalid original contour topology/owner");
   Vector4[] Pack(Vector2[]p){var a=new Vector4[32];for(int k=0;k<p.Length;k++)a[k]=p[k];return a;}
   compose.SetVectorArray("_Parent295_"+i,Pack(e.parent));compose.SetVectorArray("_Iris295_"+i,Pack(e.iris));compose.SetInt("_ParentCount295_"+i,e.parent.Length);compose.SetInt("_IrisCount295_"+i,e.iris.Length);
   var box=review.source.curtain.Design.eyes[i].bounds;compose.SetInts("_ColourBounds295_"+i,Mathf.FloorToInt(box.x)-1,Mathf.FloorToInt(box.y)-1,Mathf.CeilToInt(box.z)+1,Mathf.CeilToInt(box.w)+1);
   curtain.SetVectorArray("_Parent261_"+i,Pack(e.parent));curtain.SetVectorArray("_Iris261_"+i,Pack(e.iris));curtain.SetInt("_ParentCount261_"+i,e.parent.Length);curtain.SetInt("_IrisCount261_"+i,e.iris.Length);
   float x0=float.PositiveInfinity,y0=x0,x1=float.NegativeInfinity,y1=x1;foreach(var p in e.parent){x0=Mathf.Min(x0,p.x);y0=Mathf.Min(y0,p.y);x1=Mathf.Max(x1,p.x);y1=Mathf.Max(y1,p.y);}curtain.SetVector("_Bounds261_"+i,new Vector4(x0,y0,x1,y1));
  }
 }
}

[ExecuteAlways]public sealed class EyeContour295View:MonoBehaviour{
 public EyeSkinReview291View review;public TextAsset contourInput;public ComputeShader continuousCompose,continuousCurtain,frozenCompose,frozenCurtain;
 public bool continuous=true,playing,blinkPlaying,showFace=true;public float speed=.25f;
 public string status="ART HOLD: original continuous contour transport; final eye design and arm shading unaccepted";
 Contour295Input input;double last,accumulated,blinkTime;RenderPipelineAsset oldG,oldQ;bool captured;
 public Contour295Input Input=>input??=JsonUtility.FromJson<Contour295Input>(contourInput.text);
 void OnEnable(){if(!review||!contourInput)return;oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;captured=true;GraphicsSettings.defaultRenderPipeline=QualitySettings.renderPipeline=review.auto.previewPipeline;last=Time.realtimeSinceStartupAsDouble;Apply();
 #if UNITY_EDITOR
 UnityEditor.EditorApplication.update+=EditorTick;
 #endif
 }
 void OnDisable(){
 #if UNITY_EDITOR
 UnityEditor.EditorApplication.update-=EditorTick;
 #endif
 if(captured){GraphicsSettings.defaultRenderPipeline=oldG;QualitySettings.renderPipeline=oldQ;captured=false;}}
 public void Apply(){if(!review||!contourInput)return;review.enabled=false;review.projectedEyes=true;review.physicalChinEdge=false;review.walkPlaying=false;review.blinkPlaying=false;review.mappedCompose=continuous?continuousCompose:frozenCompose;review.mappedCurtain=continuous?continuousCurtain:frozenCurtain;review.Apply();if(continuous)Contour295Binding.Bind(review,Input,continuousCompose,continuousCurtain);}
 void Advance(){double now=Time.realtimeSinceStartupAsDouble,dt=Math.Min(.1,Math.Max(0,now-last));last=now;if(playing){accumulated+=dt*speed*16/1.333333373;if(accumulated>=1){int n=(int)accumulated;accumulated-=n;review.phaseIndex=(review.phaseIndex+n)%16;}}if(blinkPlaying){blinkTime=(blinkTime+dt)%.8;review.closure=Curtain261View.Curve((float)(blinkTime/.8));}Apply();}
 void Update(){if(Application.isPlaying){Advance();review.viewCamera.Render();}}
 #if UNITY_EDITOR
 void EditorTick(){if(!this||!enabled||Application.isPlaying||!review)return;Advance();review.viewCamera.Render();UnityEditor.EditorApplication.QueuePlayerLoopUpdate();}
 #endif
 public void Step(int n){playing=false;review.phaseIndex=(review.phaseIndex+n+16)%16;Apply();}
 void OnGUI(){if(!review)return;if(review.display){GUI.DrawTexture(new Rect(0,0,960,544),review.display,ScaleMode.StretchToFill,false);if(showFace){GUI.DrawTextureWithTexCoords(new Rect(624,172,312,372),review.display,new Rect(194/480f,1-162/272f,52/480f,62/272f),false);GUI.Label(new Rect(624,150,312,24),"Same frame face / integer 6x");}}
  GUI.Box(new Rect(10,10,390,252),"A295 continuous eye contour / ART HOLD");continuous=GUI.Toggle(new Rect(22,40,370,25),continuous,"Original 24/16 contours (off: frozen pixels)");if(GUI.Button(new Rect(22,76,72,25),playing?"Pause":"Walk"))playing=!playing;if(GUI.Button(new Rect(102,76,42,25),"<"))Step(-1);if(GUI.Button(new Rect(152,76,42,25),">"))Step(1);GUI.Label(new Rect(206,78,170,24),"Phase "+review.phaseIndex+" / 16");speed=GUI.HorizontalSlider(new Rect(22,116,236,18),speed,.1f,1);GUI.Label(new Rect(274,107,100,25),speed.ToString("0.00")+"x");if(GUI.Button(new Rect(22,140,78,25),blinkPlaying?"Stop lid":"Blink"))blinkPlaying=!blinkPlaying;review.closure=GUI.HorizontalSlider(new Rect(113,150,267,18),review.closure,0,1);if(GUI.Button(new Rect(22,178,358,25),new[]{"Game -13.33 / 30","Front / 30","Yaw -30 / 30","Yaw +30 / 30","Front / 18"}[Mathf.Clamp(review.cameraIndex,0,4)]))review.cameraIndex=(review.cameraIndex+1)%5;showFace=GUI.Toggle(new Rect(22,215,360,25),showFace,"Same-grid face enlargement");if(GUI.changed)Apply();
 }
}
