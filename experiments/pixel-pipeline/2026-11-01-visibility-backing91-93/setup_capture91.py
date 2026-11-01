from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
OUT=HERE/'capture91';OUT.mkdir(exist_ok=False)
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';OLD=ROOT/'native-feature89/capture89f'
IMPORT=HERE/'import91';IMPORT.mkdir(exist_ok=False)
text=(ROOT/'native-feature89/Import89.cs').read_text().replace('ROOT89',str(IMPORT)).replace('BEFORE89.json','BEFORE91.json').replace('IMPORTED89.json','IMPORTED91.json').replace('new[]{"NativeSurface89.shader","NativeSkin89.shader"}','new[]{"OriginalProducer91.shader","RetargetProducer91.shader","CurrentBacking91.shader"}')
text=text.replace('if(!InputSystem.settings)', 'if(SystemInfo.supportedRenderTargetCount<8)throw new NotSupportedException("8 MRT needed for bounded source probe");\n  if(!InputSystem.settings)')
(IMPORT/'Import91.cs').write_text(text,encoding='utf-8')
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
for mode in ['PreImport91','Import91']:bundle(deps+[IMPORT/'Import91.cs'],IMPORT/('RUN_'+mode+'.cs.txt'))
relay=(HERE/'relay91.py').read_text().replace("'ReadAlpha91')","'ReadAlpha91','PreImport91','Import91','Read91','Compile91','Capture91','Post91','Verify91')")
(IMPORT/'relay91.py').write_text(relay,encoding='utf-8');(OUT/'relay91.py').write_text(relay,encoding='utf-8');(OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
for mode,oldmode,outname in [('Read91','Read89F','CURRENT91.json'),('Post91','Post89F','POST91.json')]:
 c=(OLD/(oldmode+'.cs')).read_text().replace(str(OLD),str(OUT)).replace('CURRENT89F.json',outname).replace('POST89F.json',outname)
 (OUT/(mode+'.cs')).write_text(c,encoding='utf-8');bundle([B/'Json58Linear66.cs',O/'CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
c=(OLD/'Verify89F.cs').read_text().replace(str(OLD),str(OUT)).replace('VERIFY89F.json','VERIFY91.json');(OUT/'Verify91.cs').write_text(c,encoding='utf-8');bundle(deps+[OUT/'Verify91.cs'],OUT/'RUN_Verify91.cs.txt')
print('Prepared read-only native backup and new shader-only import wrapper. No import/Play executed.')
