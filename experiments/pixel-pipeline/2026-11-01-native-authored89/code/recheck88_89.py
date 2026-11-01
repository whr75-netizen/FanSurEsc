"""Run unchanged88 assertions with a NEW report path; preserve original report."""
from pathlib import Path
import sys
source=Path(__file__).resolve().parent.parent/'feature-layer88/test88.py'
sys.path.insert(0,str(source.parent))
text=source.read_text();old="q=HERE/'TEST88.json'";assert text.count(old)==1
destination=Path(__file__).resolve().parent/'REGRESSION88_IN89.json'
assert not destination.exists()
text=text.replace(old,'q=Path('+repr(str(destination))+')')
exec(compile(text,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
