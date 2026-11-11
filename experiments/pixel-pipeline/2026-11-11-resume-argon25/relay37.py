from pathlib import Path
import sys,json,hashlib
import relay33
assert sys.argv[1]in ['capture','final','console'];relay33.G=Path(__file__).resolve().parent/'face37'
if sys.argv[1]=='capture':
 h=relay33.G.parent;r=relay33.PROJECT;expected=[(r/'Assets/EUnityValidation01/SourceBoundary35/FineSourceLight35.shader',json.loads((h/'face35/PREPARED35.json').read_text())['newShaderSHA']),(r/'Assets/EUnityValidation01/SourceBoundary36/SourceArea36.compute',json.loads((h/'face36/PREPARED36.json').read_text())['sourceSHA'])];assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v for p,v in expected)
 state=(relay33.G/'preflight/final/PUBLIC_AFTER.txt').read_text();assert all(x in state for x in ['playing=False','transition=False','compiling=False','projectDirty=31','input=568105589213756420','dirty=False'])
relay33.main()
