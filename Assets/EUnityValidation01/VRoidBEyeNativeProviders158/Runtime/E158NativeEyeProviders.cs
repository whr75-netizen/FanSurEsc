using UnityEngine;
[DefaultExecutionOrder(500),DisallowMultipleComponent]
public sealed class E158NativeEyeProviders:MonoBehaviour{
 public Transform head,rightEye,leftEye;public SkinnedMeshRenderer face;public Camera referenceCamera;
 public Vector4 scales=new Vector4(1.44f,1.4575f,1.275f,1.275f);
 public Vector3 neutralWorldAnchor0=new Vector3(-.0384477472f,1.4086835707f,-.0668277323f),neutralWorldAnchor1=new Vector3(.0384476991f,1.4086833432f,-.0668277486f);
 public Vector3 headLocalAnchor0,headLocalAnchor1,eyeLocalAnchor0,eyeLocalAnchor1;
 public Quaternion neutralHeadLocalRotation,neutralRightEyeLocalRotation,neutralLeftEyeLocalRotation;
 public Vector3 headAnchor0,headAnchor1,eyeAnchor0,eyeAnchor1;
 public bool localBEnabled=true,playing=true;public float speed=1,holdSeconds=1;public int poseIndex;public string lastState;
 MaterialPropertyBlock block;float elapsed;int materialCount;
 public void Initialize(){neutralHeadLocalRotation=head.localRotation;neutralRightEyeLocalRotation=rightEye.localRotation;neutralLeftEyeLocalRotation=leftEye.localRotation;headLocalAnchor0=head.InverseTransformPoint(neutralWorldAnchor0);headLocalAnchor1=head.InverseTransformPoint(neutralWorldAnchor1);eyeLocalAnchor0=rightEye.InverseTransformPoint(neutralWorldAnchor0);eyeLocalAnchor1=leftEye.InverseTransformPoint(neutralWorldAnchor1);Apply();}
 public void SetPose(int index){poseIndex=((index%3)+3)%3;head.localRotation=neutralHeadLocalRotation*Quaternion.Euler(poseIndex==0?Vector3.zero:poseIndex==1?new Vector3(4,8,0):new Vector3(4,-8,0));Apply();}
 public void SetGaze(float yaw){rightEye.localRotation=neutralRightEyeLocalRotation*Quaternion.Euler(0,yaw,0);leftEye.localRotation=neutralLeftEyeLocalRotation*Quaternion.Euler(0,yaw,0);Apply();}
 public void SetBlink(int index,float value){face.SetBlendShapeWeight(index,value*100);Apply();}
 public void Apply(){if(block==null){block=new MaterialPropertyBlock();materialCount=face.sharedMaterials.Length;}headAnchor0=head.TransformPoint(headLocalAnchor0);headAnchor1=head.TransformPoint(headLocalAnchor1);eyeAnchor0=rightEye.TransformPoint(eyeLocalAnchor0);eyeAnchor1=leftEye.TransformPoint(eyeLocalAnchor1);for(int i=0;i<materialCount;i++){face.GetPropertyBlock(block,i);block.SetFloat("_E158Enabled",localBEnabled?1:0);block.SetVector("_E158Scales",scales);block.SetVector("_E158HeadAnchor0",headAnchor0);block.SetVector("_E158HeadAnchor1",headAnchor1);block.SetVector("_E158EyeAnchor0",eyeAnchor0);block.SetVector("_E158EyeAnchor1",eyeAnchor1);face.SetPropertyBlock(block,i);}lastState=localBEnabled?"Native sclera/lid Head skin; iris/glint Eye skin; original face UV alpha and actual depth":"Unmodified P1 baseline";}
 void Start(){SetPose(poseIndex);}void LateUpdate(){if(!Application.isPlaying)return;if(playing){elapsed+=Time.unscaledDeltaTime*speed;if(elapsed>=holdSeconds){elapsed%=holdSeconds;SetPose(poseIndex+1);}}Apply();}
 void OnGUI(){if(!Application.isPlaying)return;float y=Screen.height-58;GUI.Box(new Rect(8,y,Mathf.Min(528,Screen.width-16),50),"");if(GUI.Button(new Rect(14,y+5,65,22),playing?"Pause":"Play"))playing=!playing;if(GUI.Button(new Rect(84,y+5,50,22),"0.25x"))speed=.25f;if(GUI.Button(new Rect(139,y+5,38,22),"1x"))speed=1;if(GUI.Button(new Rect(182,y+5,32,22),"<")){playing=false;SetPose(poseIndex-1);}if(GUI.Button(new Rect(219,y+5,32,22),">")){playing=false;SetPose(poseIndex+1);}GUI.Label(new Rect(261,y+6,245,20),"Native eye providers / pose "+poseIndex);GUI.Label(new Rect(14,y+29,510,18),"Original face opening retained; B aperture adoption awaits review");}
}
