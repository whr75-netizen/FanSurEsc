from pathlib import Path
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent
p=H/'face81/post/final/RUN.cs.txt';assert not(p.parent/'REQUEST.json').exists();s=p.read_text();needle='CreateOnly40.Text(Path.Combine(Root,"final","STATE.json"),state.ToString());';assert s.count(needle)==1
extra='state["curve81Materials"]=Resources.FindObjectsOfTypeAll<Material>().Count(m=>m&&m.name=="31 owned current curve81");state["curve81Meshes"]=Resources.FindObjectsOfTypeAll<UnityEngine.Mesh>().Count(m=>m&&m.name=="31 owned current curve81 mesh");'
if extra not in s:s=s.replace(needle,extra+needle);p.write_text(s,encoding='utf-8',newline='\n')
compile_unity_language(p,H/'face81/build/post81-curveCounts.dll');print('CPU compiled public owned curve material/mesh counts')
