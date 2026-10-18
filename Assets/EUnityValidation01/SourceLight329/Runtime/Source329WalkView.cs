using System;using UnityEngine;using UnityEngine.Playables;using UnityEngine.Animations;using UnityEngine.Rendering;
#if UNITY_EDITOR
using UnityEditor;
#endif
[ExecuteAlways]public sealed class Source329WalkView:MonoBehaviour{
 public Animator target;public AnimationClip clip;public Camera viewCamera;public RenderPipelineAsset previewPipeline;public Vector4 shadeProfile=new(.72f,0,.5f,1);public bool playing=true,showBones=false,showControls=true;public float speed=1;[Range(0,40)]public float sourceFrame=20;
 PlayableGraph graph;AnimationClipPlayable motion;RenderPipelineAsset oldG,oldQ;Vector4 oldShade;bool bound;double last;Vector3 rootPosition;
 void OnEnable(){oldG=GraphicsSettings.defaultRenderPipeline;oldQ=QualitySettings.renderPipeline;oldShade=Shader.GetGlobalVector("_Source329ShadeProfile");bound=true;last=Time.realtimeSinceStartupAsDouble;
#if UNITY_EDITOR
 EditorApplication.update+=EditorTick;
#endif
 Initialise();}
 public void Initialise(){if(graph.IsValid())graph.Destroy();if(!target||!clip)return;rootPosition=target.transform.position;foreach(var skin in target.GetComponentsInChildren<SkinnedMeshRenderer>(true)){skin.forceMatrixRecalculationPerRender=true;skin.updateWhenOffscreen=true;}target.enabled=true;target.applyRootMotion=false;target.cullingMode=AnimatorCullingMode.AlwaysAnimate;graph=PlayableGraph.Create("329 original source Walk current surface");graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);motion=AnimationClipPlayable.Create(graph,clip);motion.SetApplyFootIK(false);motion.SetApplyPlayableIK(false);motion.SetSpeed(0);var output=AnimationPlayableOutput.Create(graph,"329 actual original Animator",target);output.SetSourcePlayable(motion);graph.Play();Sample(sourceFrame);Apply();}
 public void Apply(){if(previewPipeline)GraphicsSettings.defaultRenderPipeline=QualitySettings.renderPipeline=previewPipeline;Shader.SetGlobalVector("_Source329ShadeProfile",shadeProfile);if(viewCamera){viewCamera.aspect=960f/544;viewCamera.allowMSAA=false;}}
 public void Sample(float frame){sourceFrame=Mathf.Clamp(frame,0,40);if(graph.IsValid()){target.transform.position=rootPosition;motion.SetTime(clip.length*sourceFrame/40);graph.Evaluate(0);}Apply();}
 void Advance(){double now=Time.realtimeSinceStartupAsDouble;float dt=(float)Math.Min(now-last,.1);last=now;if(playing)Sample(Mathf.Repeat(sourceFrame+dt*40/clip.length*speed,40));else Apply();}
 void Update(){if(Application.isPlaying&&target&&clip)Advance();}
#if UNITY_EDITOR
 void EditorTick(){if(!Application.isPlaying&&target&&clip){Advance();if(playing)EditorApplication.QueuePlayerLoopUpdate();}}
#endif
 void OnDisable(){
#if UNITY_EDITOR
 EditorApplication.update-=EditorTick;
#endif
 if(graph.IsValid())graph.Destroy();if(bound){if(GraphicsSettings.defaultRenderPipeline==previewPipeline)GraphicsSettings.defaultRenderPipeline=oldG;if(QualitySettings.renderPipeline==previewPipeline)QualitySettings.renderPipeline=oldQ;Shader.SetGlobalVector("_Source329ShadeProfile",oldShade);bound=false;}}
 void OnGUI(){if(!showControls||!target||!clip)return;GUILayout.BeginArea(new Rect(12,12,610,105),GUI.skin.box);GUILayout.Label("329 actual Unity Walk | common source + derived shade | unadopted diagnostic");GUILayout.BeginHorizontal();if(GUILayout.Button(playing?"Pause":"Play"))playing=!playing;if(GUILayout.Button("0.25x / 1x"))speed=speed<.5f?1:.25f;if(GUILayout.Button("<")){playing=false;Sample(Mathf.Max(0,Mathf.Round(sourceFrame)-1));}if(GUILayout.Button(">")){playing=false;Sample(Mathf.Min(40,Mathf.Round(sourceFrame)+1));}if(GUILayout.Button(shadeProfile.w>.5f?"B derived shade":"A source base")){shadeProfile.w=shadeProfile.w>.5f?0:1;Apply();}showBones=GUILayout.Toggle(showBones,"Bones");GUILayout.EndHorizontal();float f=GUILayout.HorizontalSlider(sourceFrame,0,40);if(Mathf.Abs(f-sourceFrame)>.01f){playing=false;Sample(f);}GUILayout.Label("source frame "+sourceFrame.ToString("F2")+" /40, "+speed+"x");GUILayout.EndArea();if(showBones&&viewCamera)DrawBones();}
 void DrawBones(){foreach(var side in new[]{new[]{HumanBodyBones.Chest,HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm,HumanBodyBones.LeftHand},new[]{HumanBodyBones.Chest,HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm,HumanBodyBones.RightHand},new[]{HumanBodyBones.Hips,HumanBodyBones.LeftUpperLeg,HumanBodyBones.LeftLowerLeg,HumanBodyBones.LeftFoot,HumanBodyBones.LeftToes},new[]{HumanBodyBones.Hips,HumanBodyBones.RightUpperLeg,HumanBodyBones.RightLowerLeg,HumanBodyBones.RightFoot,HumanBodyBones.RightToes},new[]{HumanBodyBones.Hips,HumanBodyBones.Spine,HumanBodyBones.Chest,HumanBodyBones.Neck,HumanBodyBones.Head}})for(int i=1;i<side.Length;i++){var a=target.GetBoneTransform(side[i-1]);var b=target.GetBoneTransform(side[i]);if(!a||!b)continue;var p=viewCamera.WorldToScreenPoint(a.position);var q=viewCamera.WorldToScreenPoint(b.position);Line(new Vector2(p.x,Screen.height-p.y),new Vector2(q.x,Screen.height-q.y));}}
 static void Line(Vector2 a,Vector2 b){var matrix=GUI.matrix;var color=GUI.color;GUI.color=new Color(.25f,1,.8f);GUIUtility.RotateAroundPivot(Mathf.Atan2(b.y-a.y,b.x-a.x)*Mathf.Rad2Deg,a);GUI.DrawTexture(new Rect(a.x,a.y,Vector2.Distance(a,b),1),Texture2D.whiteTexture);GUI.matrix=matrix;GUI.color=color;}
}
