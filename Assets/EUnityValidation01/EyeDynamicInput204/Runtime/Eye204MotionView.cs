using System;using UnityEngine;using UnityEngine.Animations;using UnityEngine.Playables;
[DefaultExecutionOrder(1900)]public sealed class Eye204MotionView:MonoBehaviour{
 public Eye202View layers;public Animator target;public AnimationClip existingWalk;public int pose;public bool automaticPreview;public string currentLabel="P0 original fixture";
 PlayableGraph graph;AnimationClipPlayable playable;Transform[]restBones;Vector3[]restPositions,restScales;Quaternion[]restRotations;
 public float SampleSeconds=>pose==0?0:existingWalk.length*(pose==1?.25f:.75f);
 public void CacheRest(){if(restBones!=null)return;restBones=target.GetComponentsInChildren<Transform>(true);restPositions=new Vector3[restBones.Length];restScales=new Vector3[restBones.Length];restRotations=new Quaternion[restBones.Length];for(int i=0;i<restBones.Length;i++){restPositions[i]=restBones[i].localPosition;restRotations[i]=restBones[i].localRotation;restScales[i]=restBones[i].localScale;}}
 public void Release(){if(graph.IsValid())graph.Destroy();}
 public void SetPose(int p){CacheRest();pose=Mathf.Clamp(p,0,2);if(pose==0){Release();target.enabled=false;for(int i=0;i<restBones.Length;i++){restBones[i].localPosition=restPositions[i];restBones[i].localRotation=restRotations[i];restBones[i].localScale=restScales[i];}currentLabel="P0 original fixture";}
  else{if(!target.avatar||!target.avatar.isValid||!target.avatar.isHuman||!existingWalk||!existingWalk.humanMotion)throw new InvalidOperationException("Existing valid Humanoid Avatar and humanMotion clip required; no rig/clip creation allowed");if(!graph.IsValid()){target.enabled=true;target.applyRootMotion=false;target.cullingMode=AnimatorCullingMode.AlwaysAnimate;graph=PlayableGraph.Create("Eye204 Existing walk only");graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);playable=AnimationClipPlayable.Create(graph,existingWalk);playable.SetApplyFootIK(false);playable.SetApplyPlayableIK(false);playable.SetSpeed(0);var output=AnimationPlayableOutput.Create(graph,"Existing Walk_Loop to existing VRM Avatar",target);output.SetSourcePlayable(playable);graph.Play();}playable.SetTime(SampleSeconds);graph.Evaluate(0);currentLabel=pose==1?"Existing Walk_Loop 25%":"Existing Walk_Loop 75%";}
  layers.game.actor.Apply();
 }
 void Start(){CacheRest();SetPose(0);}void LateUpdate(){if(automaticPreview){layers.game.actor.Apply();layers.RenderReference(true);}}
 void OnGUI(){GUI.Label(new Rect(8,8,1150,45),"Eye204 actual per-pose MRT INPUT validation / "+currentLabel+"\nFixed Game130 camera + B25. Almond authoring unchanged. Dynamic final eye composition blocked at binding/lid/depth input; no P0 image warp.");if(layers&&layers.game.Logical)GUI.DrawTexture(new Rect(15,96,1440,816),layers.game.Logical,ScaleMode.StretchToFill,false);for(int p=0;p<3;p++)if(GUI.Button(new Rect(15+p*200,60,190,28),p==0?"P0 fixture":p==1?"Walk 25%":"Walk 75%"))SetPose(p);}
 void OnDisable(){Release();}void OnDestroy(){Release();}
}
