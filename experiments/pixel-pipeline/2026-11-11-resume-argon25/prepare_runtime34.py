"""Add geometric normal/source RGB copies to the executed33 observer only."""
from pathlib import Path
import re,json,hashlib,sys
H=Path(__file__).resolve().parent;G=H/'face34';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True)
 old=(H/'face33/capture/RUN.cs.txt').read_text();code=re.sub(r'\b[A-Za-z_]\w*33\b',lambda m:m[0][:-2]+'34',old)
 # C# type names are private per invocation. GPU asset paths remain the already
 # imported, actually validated33 variants. No shader/C# Assets changes.
 code=code.replace('Assets/EUnityValidation01/SourceBoundary34/SourceOutline34.shader','Assets/EUnityValidation01/SourceBoundary33/SourceOutline33.shader').replace('Assets/EUnityValidation01/SourceBoundary34/QMeta34.shader','Assets/EUnityValidation01/SourceBoundary33/QMeta33.shader').replace('Assets/EUnityValidation01/SourceBoundary34/LineClass34.compute','Assets/EUnityValidation01/SourceBoundary33/LineClass33.compute').replace('face34/import/COMPLETE.json','face33/import/COMPLETE.json')
 def rep(a,b):
  nonlocal code
  assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
 rep('QFields=new RTHandle[10]','QFields=new RTHandle[13]')
 rep('for(int i=0;i<5;i++){var src=LegacyInputs34()[i]','for(int i=0;i<8;i++){var src=LegacyInputs34()[i]')
 rep('for(int i=0;i<5;i++)cmd.CopyTexture(LegacyInputs34()[i]','for(int i=0;i<8;i++)cmd.CopyTexture(LegacyInputs34()[i]')
 rep('eye.full.motion.raw[2],eye.full.motion.raw[6]};','eye.full.motion.raw[2],eye.full.motion.raw[6],eye.full.motion.raw[1],eye.full.motion.raw[0],eye.full.style480[0]};')
 rep('new[]{0,3,4,5,6,7,8,9}','new[]{0,3,4,5,6,7,8,9,10,11,12}')
 rep('"raw role-owner-depth-alpha","raw normal","raw UV"','"raw(depth,role+1,instance,primitive+1)","effectiveNormal/frontBack","raw(UV,primitive+1,renderer+1)","geometryNormal/role+1","sourceRGBA","existing colour afterQApply"')
 # New frame, not paired with33 by assumption. All normal comparison is within34.
 code=code.replace('33 one-frame','34 paired-normal').replace('id="face33-"','id="face34-"')
 p=G/'capture';p.mkdir(exist_ok=True);out=p/'RUN.cs.txt';assert not(p/'REQUEST.json').exists();out.write_text(code,encoding='utf-8',newline='\n');compile_source([out],G/'build/capture34.dll')
 f=G/'preflight';f.mkdir(exist_ok=True);state=(H/'face33/final/RUN.cs.txt').read_text().replace('face33\\final','face34\\preflight');(f/'RUN.cs.txt').write_text(state,encoding='utf-8',newline='\n');compile_source([f/'RUN.cs.txt'],G/'build/preflight34.dll')
 manifest={'baseline':'3ae55c7b','captureCommandSHA256':sha(out),'preflightSHA256':sha(f/'RUN.cs.txt'),'CPUCompile':'passed','AssetsChanges':0,'shaderVariantsReused':json.loads((H/'face33/PREPARED33.json').read_text())['shaders'],'addedCopies':{'q10':'raw[1] geometric normal/role+1','q11':'raw[0] original source RGBA','q12':'style480[0] actual postQApply colour'},'dispatches':'unchanged33 bounded classifier; no additional compute kernel','scope':'one paired-normal observation, no automatic product normal replacement'}
 (G/'PREPARED34.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n');print(json.dumps(manifest))
if __name__=='__main__':main()
