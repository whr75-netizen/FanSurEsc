from pathlib import Path
H=Path(__file__).resolve().parent/'capture'
for name in ['Compile102.cs','Capture102.cs','RUN_Compile102.cs.txt','RUN_Capture102.cs.txt']:
 p=H/name;s=p.read_text(encoding='utf-8');s=s.replace('HairDrawScope100 motion82','Sequence102 motion82').replace('new HairDrawScope100(n,output)','new Sequence102(n,output)');p.write_text(s,encoding='utf-8')
p=H/'relay102.py';s=p.read_text(encoding='utf-8');s=s.replace("'Import102')","'Import102','CompileSequence102')");p.write_text(s,encoding='utf-8')
out=H/'RUN_CompileSequence102.cs.txt';assert not out.exists();out.write_bytes((H/'RUN_Compile102.cs.txt').read_bytes());print('Sequence102 2hair +7evaluatedClose states connected; no Unity calls')
