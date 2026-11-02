from pathlib import Path
import sys
H=Path(__file__).resolve().parent;G=H/'gpu-carrier';R=H.parent
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
s=(G/'Import111G.cs').read_text();s=s.replace('using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;','using System;\nusing System.IO;\nusing System.Linq;\nusing UnityEngine;\nusing UnityEditor;').replace('IMPORT111G.json','IMPORT111Gb.json')
with(G/'Import111Gb.cs').open('x',encoding='utf8')as f:f.write(s)
bundle([R/'apply-capture66/Json58Linear66.cs',R/'eye-observer73/CreateOnly73.cs',G/'Import111Gb.cs'],G/'RUN_Import111Gb.cs.txt')
p=G/'relay111g.py';s=p.read_text().replace("('Import111G',","('Import111Gb','Import111G',");p.write_text(s)
print('Prepared corrected import bundle; original failed source/request retained.')
