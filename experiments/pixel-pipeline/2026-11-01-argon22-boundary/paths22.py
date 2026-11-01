from pathlib import Path
import sys
H=Path(__file__).resolve().parent;R=H.parent
OLD=next(p for p in [R/'joint-resolver110',R/'2026-11-01-joint-resolver110']if p.exists())
sys.path.insert(0,str(OLD))
