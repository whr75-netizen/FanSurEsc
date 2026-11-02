from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent
def create(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n')as f:f.write(s)
src=(R/'joint-lid107/capture/RUN_ReadFinal107.cs.txt').read_text(encoding='utf8')
old=r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\joint-lid107\capture-final\CURRENT102.json'
assert src.count(old)==1
src=src.replace(old,str(H/'capture/CURRENT111.json')).replace('66 read only:','111 read only:')
create(H/'capture/RUN_Read111.cs.txt',src)
wrapper=(R/'joint-lid107/capture/relay107.py').read_text(encoding='utf8');start=wrapper.index("assert mode in (");end=wrapper.index('\n',start)
wrapper=wrapper[:start]+"assert mode in ('Read111','Compile111','Capture111','Post111','Import111')"+wrapper[end:]
create(H/'capture/relay111.py',wrapper)
print('Prepared NEW read-only command; not executed.')
