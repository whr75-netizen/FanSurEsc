from pathlib import Path
import hashlib,json,uuid
R=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
A=P/'Assets/Editor/RendererCompare60Probe';assert not A.exists()
base=json.loads((R/'DISK_BASELINE60.json').read_text())
assert all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in base['protected'].items())
sources=list((R/'probe-assets').iterdir());assert len(sources)==8 and not any(p.suffix=='.cs'for p in sources)
A.mkdir()
for p in sources:(A/p.name).write_bytes(p.read_bytes())
folderMeta=A.with_name(A.name+'.meta');assert not folderMeta.exists()
folderMeta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf8')
(R/'ASSET_PUBLISH60.json').write_text(json.dumps({'files':[str(p.relative_to(P))for p in A.iterdir()]+[str(folderMeta.relative_to(P))],'CSharpImport':False,'PlayExecuted':False},indent=2),encoding='utf8')
print('Isolated shader assets copied: 9 paths. No Unity import/Play yet.')
