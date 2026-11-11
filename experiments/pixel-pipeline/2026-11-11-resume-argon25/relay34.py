"""Reuse the official33 transport under a fresh immutable34 operation root."""
from pathlib import Path
import sys,json,hashlib
import relay33
mode=sys.argv[1];assert mode in ['preflight','capture','final','console']
relay33.G=Path(__file__).resolve().parent/'face34'
if mode=='capture':
 plan=json.loads((relay33.G/'PREPARED34.json').read_text());repo=relay33.PROJECT
 assert all(hashlib.sha256((repo/'Assets/EUnityValidation01/SourceBoundary33'/p).read_bytes()).hexdigest()==v for p,v in plan['shaderVariantsReused'].items())
 before=(relay33.G/'preflight/PUBLIC_AFTER.txt').read_text();assert all(s in before for s in ['playing=False','transition=False','compiling=False','updating=False','projectDirty=31','input=568105589213756420','dirty=False'])
if mode=='preflight':
 # Reuse the read-only final-state command type; operation files are distinct.
 relay33.G=relay33.G/'preflight-scope';relay33.G.mkdir(exist_ok=True)
 p=relay33.G/'final';p.mkdir(exist_ok=True);source=relay33.G.parent/'preflight/RUN.cs.txt'
 if not(p/'REQUEST.json').exists():(p/'RUN.cs.txt').write_bytes(source.read_bytes())
 sys.argv[1]='final'
relay33.main()
