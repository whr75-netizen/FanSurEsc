from pathlib import Path
import sys,json,relay33
H=Path(__file__).resolve().parent
relay33.G=H/'face99/world-assets99';relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.TITLE_OVERRIDE='Read current world source assets through public Editor MeshUtility read-only snapshots into new local evidence; dispose only owned CPU snapshots. No GPU/Play/import/ReadWrite or original state change.'
sys.argv=[sys.argv[0],'details'];relay33.main()
