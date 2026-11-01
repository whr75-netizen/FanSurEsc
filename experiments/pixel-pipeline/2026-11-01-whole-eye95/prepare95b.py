from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; OLD=HERE/'capture'; OUT=HERE/'capture-scale-correct'
assert not OUT.exists(); OUT.mkdir()
sys.path.insert(0,str(ROOT/'boundary-input69')); from prepare73 import bundle
B=ROOT/'apply-capture66'; O=ROOT/'eye-observer73'; U=ROOT/'uv-features64'
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',HERE/'NativeRetarget95.cs',HERE/'GraphSources95.cs',HERE/'MotionScope95.cs']
base=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
for mode in ['Compile','Capture','Read','Post','Verify']:
    text=(OLD/(mode+'95.cs')).read_text().replace(str(OLD),str(OUT)).replace('eye95-','eye95b-').replace('STATE95-','STATE95B-').replace('TRACE95-','TRACE95B-').replace('CURRENT95.json','CURRENT95B.json').replace('POST95.json','POST95B.json').replace('VERIFY95.json','VERIFY95B.json').replace('PRIOR47_CURRENT95.json','PRIOR47_CURRENT95B.json')
    p=OUT/(mode+'95B.cs');p.write_text(text,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'95B.cs.txt'))
relay=(OLD/'relay95.py').read_text().replace("'Verify95')","'Verify95','Read95B','Compile95B','Capture95B','Post95B','Verify95B')")
(OUT/'relay95.py').write_text(relay,encoding='utf-8');(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
print('Single correction: owned reference BakeMesh(useScale:true), matching ScaleBake378. Previous failed output untouched.')
