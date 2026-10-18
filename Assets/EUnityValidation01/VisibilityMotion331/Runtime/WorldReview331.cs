using UnityEngine;
using FantasySurvival.WorldGeneration;

[ExecuteAlways,DefaultExecutionOrder(100)]public sealed class WorldReview331:MonoBehaviour
{
 public Source329WalkView view;public CurrentSurface330 surface;public Camera camera;public NativePixelBuilding building;public Vector3 feet,followOffset;public bool showControls=true;
 UrbanOcclusionFader fader;bool initialised;
 void Start()=>Initialise();
 public void Initialise(){if(initialised||!building||!camera)return;building.enabled=false;fader=building.GetComponent<UrbanOcclusionFader>();fader.enabled=false;fader.RegisterBuilding(building.transform,building.interior,null,null,building.frontWalls,building.frontColliders);fader.RegisterBuilding(building.transform,building.interior,null,null,building.backWalls,building.backColliders,false);fader.RegisterStorey(building.transform,building.interior,1,2.45f,building.roof,building.roofColliders,System.Array.Empty<Renderer>(),System.Array.Empty<Collider>(),System.Array.Empty<Renderer>(),true);initialised=true;RefreshVisibility(1);}
 public void RefreshVisibility(float dt){if(fader&&view&&view.target)fader.EvaluateVisibility(camera,view.target.transform.position+Vector3.up*.5f,dt);}
 void LateUpdate(){Initialise();RefreshVisibility(Application.isPlaying?Time.deltaTime:1);}
 void OnGUI(){
  if(!camera||!camera.targetTexture)return;
  float k=Mathf.Max(1,Mathf.Floor(Mathf.Min(Screen.width/960f,Screen.height/544f)));var rect=new Rect((Screen.width-960*k)/2,(Screen.height-544*k)/2,960*k,544*k);GUI.DrawTexture(rect,camera.targetTexture,ScaleMode.StretchToFill,false);
  if(!showControls||!view)return;
  GUILayout.BeginArea(new Rect(10,10,680,115),GUI.skin.box);GUILayout.Label("331 | Actual GameMap1 interior | same camera / PPU / actor scale");GUILayout.BeginHorizontal();
  if(GUILayout.Button(view.playing?"Pause":"Play"))view.playing=!view.playing;
  if(GUILayout.Button("0.25x / 1x"))view.speed=view.speed<.5f?1:.25f;
  if(GUILayout.Button("<")){view.playing=false;view.Sample(Mathf.Max(0,Mathf.Round(view.sourceFrame)-1));}
  if(GUILayout.Button(">")){view.playing=false;view.Sample(Mathf.Min(40,Mathf.Round(view.sourceFrame)+1));}
  if(GUILayout.Button(view.shadeProfile.w>.5f?"B current shade":"A original base")){view.shadeProfile.w=1-view.shadeProfile.w;view.Apply();}
  GUILayout.EndHorizontal();float f=GUILayout.HorizontalSlider(view.sourceFrame,0,40);if(Mathf.Abs(f-view.sourceFrame)>.01){view.playing=false;view.Sample(f);}GUILayout.Label("source frame "+view.sourceFrame.ToString("F2")+" | fixed960x544, logical480x272, 2x | nativePPU "+(building?building.nativePixelsPerUnit:0));GUILayout.EndArea();
 }
}
