from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'view-isolation99/capture';OUT=HERE/'capture'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
 refresh=sys.argv[1:]==['--refresh-compile-only']
 if refresh:
  import json
  q=json.loads((OUT/'Compile100_REPLY.json').read_text(encoding='utf-8'))['data'];assert q['isCompilationSuccessful']is False and q['isExecutionSuccessful']is False
  backup=OUT/'RUN_Compile100_FAILED1.cs.txt';assert not backup.exists();backup.write_bytes((OUT/'RUN_Compile100.cs.txt').read_bytes())
 else:OUT.mkdir(exist_ok=False)
 base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs'];deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',HERE/'HairDrawScope100.cs']
 for mode in (['Compile','Capture']if refresh else['Read','Compile','Capture','Post','Verify']):
  s=(OLD/(mode+'99.cs')).read_text(encoding='utf-8').replace(str(OLD),str(OUT)).replace('eye99-','eye100-').replace('STATE99-','STATE100-').replace('TRACE99-','TRACE100-').replace('CURRENT99.json','CURRENT100.json').replace('POST99.json','POST100.json').replace('VERIFY99.json','VERIFY100.json').replace('PRIOR47_CURRENT99.json','PRIOR47_CURRENT100.json')
  if mode in ['Compile','Capture']:
   s=s.replace(' NativeRetarget96 retarget89;GraphSources96 current91;LiveGraph96 joint96;LiveFinal96 final96;GpuTiming98 timing98;',' bool armed100;')
   s=s.replace('HoldScope99 motion82','HairDrawScope100 motion82').replace('new HoldScope99(','new HairDrawScope100(')
   a=s.index(' void Arm76(');b=s.index(' string sequenceDirectory',a)
   s=s[:a]+''' void Arm76(NativePlayer395 n){native=n;probeEye=n.host.headEyes;if(!probeEye||!n.host.headEnabled)throw new InvalidOperationException("100 current head path required");oldShader=probeEye.candidateShader;borrowedRest77=probeEye.restTriangles;calibrated89=true;armed100=true;report["runtimeProduct77Shader"]=AssetDatabase.GetAssetPath(oldShader);report["runtimeProduct77ShaderSHA"]=SHA(AssetDatabase.GetAssetPath(oldShader));report["noExperimental98or99"]=true;}
 void Release76(){motion82?.Dispose();report["motionRestoration82"]=motion82?.RestoreReport;report["borrowedRestReferenceUntouched82"]=probeEye&&probeEye.restTriangles==borrowedRest77;report["borrowedRestDisposedByObserver82"]=false;report["ownedProbeReleased76"]=true;}
'''+s[b:]
   s=s.replace('if(!probeShader','if(!armed100').replace('if(probeShader&&','if(armed100&&')
   s=s.replace('   final96.PresentCurrent(probeROI);TickViews99(n);','')
   s=s.replace('   VerifySourceCache77();report["gpuSourceCache77"]=cacheReport77;Capture(n,gp);','   Capture(n,gp);')
   s=s.replace('if(retarget89!=null&&!retarget89.Disposed)throw new InvalidOperationException("Retarget source resources not disposed");','')
   s=s.replace('Bounded10-state actual existing two-view observation budget','Bounded3-state product77 hair isolation budget')
   s=s[:s.index(' void Capture(')]+(HERE/'CaptureFragment100.cs').read_text(encoding='utf-8')+'\n}\n'
   assert 'final96'not in s and 'retarget89'not in s and 'CaptureB99'not in s
  p=OUT/(mode+'100.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'100.cs.txt'))
 (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes());s=(OLD/'relay99.py').read_text();s=s.replace("'Post99','Verify99')","'Post99','Verify99','Read100','Compile100','Capture100','Post100','Verify100')");(OUT/'relay100.py').write_text(s,encoding='utf-8');print('100 original product-only, three states, runtime draw descriptors only, no Assets import')
if __name__=='__main__':main()
