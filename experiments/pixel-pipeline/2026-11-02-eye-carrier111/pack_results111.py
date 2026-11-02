from pathlib import Path
import zipfile,json,ast,re
H=Path(__file__).resolve().parent
files=sorted([*H.glob('ANALYSIS111-frame*.json'),*H.glob('DESTINATIONS111-frame*.json'),*H.glob('LAYER_ABLATION111-frame*.json')]);assert len(files)==24
with zipfile.ZipFile(H/'ANALYSIS111.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    for p in files:z.write(p,p.name)
index=json.loads((H/'CODE_INDEX111.json').read_text())
for p in [*H.glob('*.cs'),*(H/'gpu-carrier').glob('*.cs'),*(H/'gpu-carrier').glob('*.shader')]:
    rows=[]
    for n,line in enumerate(p.read_text(encoding='utf8').splitlines(),1):
        if re.search(r'\b(Bind|Record|RecordGraph|Draw|DrawGraph|Dispose|ExportSource111|Eye333Fragment|Execute|CaptureCarrier111)\s*\(',line):rows.append({'functionOrCallLine':line.strip()[:120],'line':n})
    index[p.relative_to(H).as_posix()]=rows
(H/'CODE_INDEX111.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps({'analysisFiles':len(files),'archiveBytes':(H/'ANALYSIS111.zip').stat().st_size}))
