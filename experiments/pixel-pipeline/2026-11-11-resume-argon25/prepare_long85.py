"""120 bounded normal source frames, same shader, no timeout extension.

Pulse supported movement one frame in16, otherwise idle: retain facing and
limit displacement instead of teleporting/resetting the actor or camera.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face85/pulse120'
def main():
 for p in ['build','final','post/final','capture','console']:(G/p).mkdir(parents=True,exist_ok=True)
 assert not any((G/p/'REQUEST.json').exists()for p in ['final','capture'])
 s=(H/'face85/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face85\\capture','resume-20261111\\face85\\pulse120\\capture').replace('face85-source-Q-history-motion-','face85-source-Q-pulse120-')
 s=s.replace('motion40.FirstTarget,6,1,motion40.Snapshot','motion40.FirstTarget,120,16,motion40.Snapshot').replace('["plannedSourceFrames"]=6','["plannedSourceFrames"]=120')
 a=' void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(!turned&&Time.frameCount>=FirstTarget+2){Queue(direction+2);turned=true;}}';b=' void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget-1)return;bool walk=(Time.frameCount-FirstTarget+1)%16==0;InputSystem.QueueStateEvent(ownedKeyboard,new KeyboardState(walk?Keys(D[direction]):new Key[0]));}';assert s.count(a)==1;s=s.replace(a,b)
 a='var expected=D[((index<3?direction:direction+2)+8)%8];var actual=GameInputBindings.ReadMovement();bool match=actual.sqrMagnitude>0&&Vector2.Dot(actual.normalized,expected.normalized)>.999f;';b='var expected=index%16==0?D[direction]:Vector2.zero;var actual=GameInputBindings.ReadMovement();bool match=expected==Vector2.zero?actual.sqrMagnitude<1e-12f:actual.sqrMagnitude>0&&Vector2.Dot(actual.normalized,expected.normalized)>.999f;';assert s.count(a)==1;s=s.replace(a,b).replace('["stage"]=index<3?"walk":"turn"','["stage"]=index%16==0?"walk-pulse":"idle"')
 # Finish fields must report the final authoritative counters, not last 5s trace.
 a='void Finish(){if(host!=null)report["stream77"]=host.Summary();';b='void Finish(){if(host!=null){report["stream77"]=host.Summary();report["submitted77"]=host.Submitted;report["received77"]=host.Received;}';assert s.count(a)==1;s=s.replace(a,b)
 # Invalidate history on source/view/frame/level change instead of throwing or
 # carrying old state. Do not acquire a lease when history is disabled.
 a='volatile bool invalid81;bool previousLease85;';b=a+'int levels85;bool TryHistory85(){var p=Previous75;return p!=null&&p.Failure==null&&!p.Disposed&&p.eye==eye&&p.model==model&&p.topology==topology&&p.cameraIdentity==cameraIdentity&&p.frame==frame-1&&p.historyRecorded75&&p.projection75&&p.projectionTriangles75==projectionTriangles75&&p.levels85==levels85;}';assert s.count(a)==1;s=s.replace(a,b)
 s=s.replace('bool history85=ReadyHistory75();','bool history85=TryHistory85();d.history85=history85;').replace('public SourceOutline40 owner;public MaterialPropertyBlock properties;}','public SourceOutline40 owner;public MaterialPropertyBlock properties;public bool history85;}').replace('if(o.Previous75!=null){System.Threading.Interlocked.Increment','if(d.history85){System.Threading.Interlocked.Increment')
 s=s.replace('void PrepareCurve81(){previousLease85=false;','void PrepareCurve81(){previousLease85=false;levels85=eye.full.faceShadeSteps;')
 # Export actual deformed vertex normals for the separate native-width contract.
 a='  FrameInfo40["light84"]=new Obj40{';assert s.count(a)==1
 extra='''  if(SavePose77){var n=mesh.normals;var normalMatrix=matrix.inverse.transpose;if(n.Length!=v.Length)throw new InvalidOperationException("86 original deformed vertex normals missing; no substitute");using(var bw=new BinaryWriter(new FileStream(Path.Combine(root77,"normals-frame"+frame+".bin"),FileMode.CreateNew))){bw.Write("native-outline-normals86/v1");bw.Write(FrameKey);bw.Write(frame);bw.Write(n.Length);foreach(var normal in n){var world=normalMatrix.MultiplyVector(normal);bool valid=float.IsFinite(world.x)&&float.IsFinite(world.y)&&float.IsFinite(world.z)&&world.sqrMagnitude>0;bw.Write(valid);world=valid?world.normalized:Vector3.zero;bw.Write(world.x);bw.Write(world.y);bw.Write(world.z);}}}
''';s=s.replace(a,extra+a)
 a='["unknownNeverRepaired"]=true';b='''["unknownNeverRepaired"]=true,["nativeNormals86File"]=SavePose77?"normals-frame"+frame+".bin":"not-sampled",["originalWidth86"]=new Obj40{["widthMetres"]=width,["mode"]=originals[renderer][submesh].GetFloat("_OutlineWidthMode"),["parameterMapEnabled"]=originals[renderer][submesh].IsKeywordEnabled("_MTOON_PARAMETERMAP")||Shader.IsKeywordEnabled("_MTOON_PARAMETERMAP"),["textureImageHash"]=originals[renderer][submesh].GetTexture("_OutlineWidthTex").imageContentsHash.ToString(),["textureSRGB"]=UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(originals[renderer][submesh].GetTexture("_OutlineWidthTex").graphicsFormat),["filter"]=originals[renderer][submesh].GetTexture("_OutlineWidthTex").filterMode.ToString(),["wrapU"]=originals[renderer][submesh].GetTexture("_OutlineWidthTex").wrapModeU.ToString(),["wrapV"]=originals[renderer][submesh].GetTexture("_OutlineWidthTex").wrapModeV.ToString()}}''';assert s.count(a)==1;s=s.replace(a,b)
 s=s.replace('wrapModeV.ToString()}}};invalid81=false;','wrapModeV.ToString()}};invalid81=false;')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/long85.dll')
 for p in ['final','post/final']:
  t=(H/'face85'/p/'RUN.cs.txt').read_text().replace('resume-20261111\\face85','resume-20261111\\face85\\pulse120');(G/p/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/p/'RUN.cs.txt',G/'build'/(p.replace('/','-')+'85.dll'))
 (G/'console/ARGS.json').write_text((H/'face85/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':120,'simulationSeconds':2,'normalInput':'existing bound movement, one frame in16 then idle; no pose/camera/settings object replacement','same85ShaderNoImport':True,'existing120SecondDeadlineUnchanged':True,'levelsViewModelGapInvalidatesHistory':True,'priorTextureLeaseBeforeDraw':True,'actualNativeNormalsForWidth86Sampled':True,'GPUExecuted':False};(G/'CPU_PREPARED_LONG85.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
