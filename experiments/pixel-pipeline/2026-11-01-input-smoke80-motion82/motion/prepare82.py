from pathlib import Path
import sys,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'run';OUT=HERE/'run82';OUT.mkdir(exist_ok=True)
assert not list(OUT.glob('*_REQUEST.json')),'Existing82 must be inspected before rebuild'
state=json.loads(sorted(OLD.glob('STATE81*'))[-1].read_text());assert state['PlayExited']and not state.get('restorationError')and all(state['editInputRestoration81'][k]for k in ['sameAliveReference','exactJSON','devicesSame','deviceEnabledStates','keyboardSame'])
r=(OLD/'relay76.py').read_text().replace("'Verify81')","'Verify81','Read82','Compile82','Capture82','Post82','Verify82')");(OUT/'relay76.py').write_bytes(r.encode());(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
m=(OLD/'MotionScope81.cs').read_text().replace('81','82')
m=m.replace('public Arr58 warmup=new Arr58();','public Arr58 warmup=new Arr58();public Arr58 dynamicInput=new Arr58();\n void AfterInput82(){if(keyboard==null||UnityEngine.InputSystem.LowLevel.InputState.currentUpdateType!=InputUpdateType.Dynamic)return;if(dynamicInput.Count<80)dynamicInput.Add(new Obj58{["frame"]=Time.frameCount,["requested"]=V(requested),["actual"]=V(GameInputBindings.ReadMovement()),["enabled"]=keyboard.enabled,["current"]=Keyboard.current==keyboard,["keys"]=new Arr58(Keys(requested).Select(k=>new Obj58{["key"]=k.ToString(),["pressed"]=keyboard[k].isPressed}))});}')
m=m.replace('movement.speed=native.host.Cell*.25f/Delta;animator.speed=0;Queue(direction);','movement.speed=native.host.Cell*.25f/Delta;animator.speed=0;InputSystem.onAfterUpdate+=AfterInput82;Queue(direction);')
m=m.replace('public void Dispose(){if(disposed)return;disposed=true;','public void Dispose(){if(disposed)return;disposed=true;InputSystem.onAfterUpdate-=AfterInput82;')
(OUT/'MotionScope82.cs').write_bytes(m.encode())
s=(OLD/'Capture81.cs').read_text().replace(str(OLD),str(OUT)).replace('81','82')
# RunCommand Editor update and all synchronous readbacks execute on the main
# thread. No frame can advance until Capture returns (validated by existing
# frame/serial stamps); pausing here switches InputSystem away from game state.
s=s.replace('if(!probeShader){EditorApplication.isPaused=true;Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");EditorApplication.isPaused=false;return;}','if(!probeShader){Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");return;}')
s=s.replace('EditorApplication.isPaused=true;readyAllocated=','readyAllocated=')
s=s.replace('report["motionWarmup82"]=motion82.warmup;','report["motionWarmup82"]=motion82.warmup;report["dynamicInput82"]=motion82.dynamicInput;')
s=s.replace('Save("paused-already-rendered")','Save("already-rendered-main-thread-readback")')
assert 'EditorApplication.isPaused=true'not in s
(OUT/'Capture82.cs').write_bytes(s.encode())
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64'
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',OUT/'MotionScope82.cs']
bundle(deps+[OUT/'Capture82.cs'],OUT/'RUN_Capture82.cs.txt');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("82 no-pause normal-input motion observer compiled only");return;}\n void Prepared82(ExecutionResult result)\n {',1);(OUT/'Compile82.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile82.cs'],OUT/'RUN_Compile82.cs.txt')
for mode,prev,filename in [('Read82','Read81','CURRENT82.json'),('Post82','Post81','POST82.json')]:
 c=(OLD/(prev+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT81.json',filename).replace('POST81.json',filename);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
v=(ROOT/'input-smoke80/Verify80.cs').read_text().replace('ROOT80',str(OUT)).replace('VERIFY80.json','VERIFY82.json');(OUT/'Verify82.cs').write_bytes(v.encode());bundle([B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',OUT/'Verify82.cs'],OUT/'RUN_Verify82.cs.txt')
assert not re.search(r'InputSystem\.settings\s*=(?!=)',s+m)
print('82 prepared: sole causal change removes observer pause; Dynamic input trace added; synchronous frame stamps retained')
