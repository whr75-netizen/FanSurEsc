from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face93'
def main():
 for d in ['build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['final','post/final'])
 for d in ['final','post/final']:
  s=(H/'face92/motion240'/d/'RUN.cs.txt').read_text().replace('resume-20261111\\face92\\motion240','resume-20261111\\face93');(G/d/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/d/'RUN.cs.txt',G/'build'/(d.replace('/','-')+'93.dll'))
 (G/'console/ARGS.json').write_text((H/'face92/motion240/console/ARGS.json').read_text());print(json.dumps({'onlyReadStateCommandCompiled':True,'UnityExecuted':False}))
if __name__=='__main__':main()
