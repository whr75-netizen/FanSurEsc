from pathlib import Path
H=Path(__file__).resolve().parent;G=H/'gpu-carrier';s=(H/'capture/RUN_Read111.cs.txt').read_text();old=str(H/'capture/CURRENT111.json');assert s.count(old)==1;s=s.replace(old,str(G/'CURRENT_POST111G.json'))
with(G/'RUN_Post111G.cs.txt').open('x',encoding='utf8')as f:f.write(s)
print('Prepared read-only post state command.')
