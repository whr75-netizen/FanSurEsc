from pathlib import Path
import sys,json,relay33
H=Path(__file__).resolve().parent
relay33.G=H/'face99/original99';relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.TITLE_OVERRIDE='Read matching original material texture CPU pixels into a new local evidence file. No GPU, Play, imports, source mutation or setting change.'
sys.argv=[sys.argv[0],'details'];relay33.main()
