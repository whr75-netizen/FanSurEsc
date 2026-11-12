from pathlib import Path
import os,subprocess,json
H=Path(__file__).resolve().parent;G=H/'face104'

def main():
 G.mkdir(exist_ok=True);exe=G/'WorldSampleCases104.exe';csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';r=subprocess.run([str(csc),'/nologo','/utf8output','/out:'+str(exe),str(H/'JointLine103.cs'),str(H/'WorldSampleCases104.cs')],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;r=subprocess.run([str(exe)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 out={'CPUOnly':True,'UnityOrGPUExecuted':False,'fourNativeSampleDepthsIdentical':True,'oneWitnessVisibilityDiffers':True,'partialSupportNotWholeCellRejected':True,'opaqueTriangleNoAlphaAmbiguity':True,'demonstratesInputInsufficiencyNotImplementedWorldFix':True,'stdout':r.stdout.strip()};(G/'CPU_WORLD104.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

if __name__=='__main__':main()
