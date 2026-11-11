"""Prepare one compute-only import and four-state capture; no execution."""
from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;G=H/'gate';PRE=H.parent
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(PRE));from prepare_live import compile_cs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(G/'IMPORT_REQUEST.json').exists()and not(G/'phase-run/PHASE_REQUEST.json').exists(),'Never change submitted commands'
 (G/'import').mkdir(exist_ok=True)
 s=(PRE/'RUN_Import25.cs.txt').read_text();s=s.replace(str(PRE/'import'),str(G/'import'))
 s=replace(s,'const string folder="Assets/EUnityValidation01/HeadHair25",compute=folder+"/ForwardEye113_HeadHair25.compute",surface=folder+"/HeadHair25.shader";',
  'const string folder="Assets/EUnityValidation01/SharedSkin26",compute=folder+"/SharedSkin26.compute",surface="Assets/EUnityValidation01/HeadHair25/HeadHair25.shader";')
 s=replace(s,'AssetDatabase.CreateFolder("Assets/EUnityValidation01","HeadHair25")','AssetDatabase.CreateFolder("Assets/EUnityValidation01","SharedSkin26")')
 p=re.compile(r'var paths=new\[\]\{[^\n]+?\};var hashes=new\[\]\{[^\n]+?\};var targets=new\[\]\{compute,surface\};')
 assert len(p.findall(s))==1
 line='var paths=new[]{@"'+str(G/'SharedSkin26.compute')+'"};var hashes=new[]{"'+sha(G/'SharedSkin26.compute')+'"};var targets=new[]{compute};'
 s=p.sub(lambda _:line,s)
 assert s.count('for(int i=0;i<2;i++)')==2;s=s.replace('for(int i=0;i<2;i++)','for(int i=0;i<paths.Length;i++)')
 source=G/'RUN_Import25.cs.txt';source.write_text(s,encoding='utf-8',newline='\n');compile_cs(source)
 relay=(PRE/'relay.py').read_text().replace('Import two isolated head-grid shaders without Play','Import one isolated shared-skin shader without Play').replace('Two phase captures on reviewed113 path then normal exit and restore','Four evaluated Open Close75 Close100 reopen states then normal exit and restore')
 (G/'relay.py').write_text(relay,encoding='utf-8',newline='\n')
 record=json.loads((G/'PREPARED_GATE26.json').read_text());assert record['computeSHA256']==sha(G/'SharedSkin26.compute')
 result={'importSourceSHA256':sha(source),'captureSourceSHA256':sha(G/'phase-run/RUN_Capture25.cs.txt'),'computeSHA256':sha(G/'SharedSkin26.compute'),
  'cacheSHA256':sha(H/'SHARED_SOURCE_MASK26.json'),'compiledCPU':True,'newAssets':1,'newKernels':0,'actualFramesBound':4,'GPUOrUnityExecuted':False}
 (G/'LIVE_PREPARED.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
