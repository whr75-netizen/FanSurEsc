from pathlib import Path
import json,sys,relay33
from observer_transport94 import hold
H=Path(__file__).resolve().parent;mode=sys.argv[1];name=sys.argv[2]if len(sys.argv)>2 else'one';relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid']
if mode.startswith('import-'):
 relay33.G=H/'face98'/mode;mode='import';title='Create-only private bounded raster shader; no CSharp Assets, default, Play, SaveAssets or existing overwrite'
else:
 relay33.G=H/'face98'/name
 if mode=='post':relay33.G=relay33.G/'post';mode='final'
 title={'final':'Read stable Editor/native/input/resource state only','console':'Read Console without clearing','capture':'Run prepared current-frame CPU same-point source/destination line selection and two fixed raster composites with same-feature redundancy proof on a private clone. No115/new compute/GPU selection readback/InputSettings replacement/default change. Bounded acknowledged packet, normal Play exit, owned resource release and full temporary-state restoration.'}[mode]
 if mode=='capture':
  s=json.loads((relay33.G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and not s['updating']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0
  assert all((H/'face98'/('import-'+shader)/'import/COMPLETE.json').exists()for shader in['CoupledRibbon98B','SourceFootprint98']);relay33.OBSERVATION_HOLD=hold
assert(relay33.G/mode/('ARGS.json'if mode.startswith('console')else'RUN.cs.txt')).is_file(),'98 prepared command missing; no relay process started'
relay33.TITLE_OVERRIDE=title;sys.argv=[sys.argv[0],mode];relay33.main()
