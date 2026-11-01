from pathlib import Path
import sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'gpu88';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
s=(ROOT/'feature-audit86/Import87.cs').read_text().replace('ROOT87',str(OUT)).replace('CachedSourceRole87.compute','FeatureLayer88.compute').replace('BEFORE87.json','BEFORE88.json').replace('IMPORTED87.json','IMPORTED88.json').replace('"Compose"','"Draw"');(OUT/'Import88.cs').write_bytes(s.encode())
for name in ['PreImport88','Import88']:bundle(deps+[OUT/'Import88.cs'],OUT/('RUN_'+name+'.cs.txt'))
s=(HERE/'GPU88.cs').read_text().replace('ROOT88',str(OUT)).replace('INPUTS88',str(HERE/'validated'));(OUT/'GPU88.cs').write_bytes(s.encode());bundle(deps+[OUT/'GPU88.cs'],OUT/'RUN_GPU88.cs.txt');c=s.replace(' public void Execute(ExecutionResult result){',' public void Execute(ExecutionResult result){result.Log("88 complete isolated GPU runner compiled only");return;}void Prepared88(ExecutionResult result){',1);(OUT/'Compile88.cs').write_bytes(c.encode());bundle(deps+[OUT/'Compile88.cs'],OUT/'RUN_Compile88.cs.txt')
for mode,prev,new in [('Read88','Read87','CURRENT88.json'),('Post88','Post87','POST88.json')]:
 c=(ROOT/'feature-audit86/run87'/(prev+'.cs')).read_text().replace(str(ROOT/'feature-audit86/run87'),str(OUT)).replace('CURRENT87.json',new).replace('POST87.json',new);(OUT/(mode+'.cs')).write_bytes(c.encode());bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
r=(ROOT/'feature-audit86/run87/relay76.py').read_text().replace("'Verify87')","'Verify87','PreImport88','Import88','Read88','Compile88','GPU88','Post88')");(OUT/'relay76.py').write_bytes(r.encode());print('Prepared shader-only import and24 bounded saved-input GPU packets; no Play/settings/global writes.')
