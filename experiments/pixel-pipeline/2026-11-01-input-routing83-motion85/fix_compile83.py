from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;O=HERE/'run';assert not (O/'Probe83_REQUEST.json').exists()
s=(O/'Probe83.cs').read_text();s=s.replace('UseIrisSurface583','UseIrisSurface582')
# This input-only observer never calls any capture/geometry/frozen-render methods.
# Remove the unused tail rather than keep a second hidden render test surface.
start=s.index(' CpuSourceCapture64.Frame Frame(');s=s[:start]+'}\n';(O/'Probe83.cs').write_bytes(s.encode())
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';P=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',P/'CreateOnly73.cs',P/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',O/'InputEventProbe83.cs',O/'MotionScope83.cs']
bundle(deps+[O/'Probe83.cs'],O/'RUN_Probe83.cs.txt');c=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("83 minimal input-only observer/event probe compiled only");return;}\n void Prepared83(ExecutionResult result)\n {',1);(O/'Compile83Fixed.cs').write_bytes(c.encode());bundle(deps+[O/'Compile83Fixed.cs'],O/'RUN_Compile83Fixed.cs.txt')
r=(O/'relay76.py').read_text().replace("'Verify83')","'Verify83','Compile83Fixed')");(O/'relay76.py').write_bytes(r.encode());print('83 prepared source compile correction; removed unused capture methods; no Play dispatched')
