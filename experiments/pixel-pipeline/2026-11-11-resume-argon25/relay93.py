from pathlib import Path
import sys,json
import relay33
H=Path(__file__).resolve().parent;G=H/'face93';mode=sys.argv[1];long=mode.startswith('long-');mode=mode[5:]if long else mode;fixed=mode.startswith('fix-');mode=mode[4:]if fixed else mode;packed=mode.startswith('packed-');mode=mode[7:]if packed else mode
if packed:G=G/'packed1'
if fixed:G=G/'witness-fix'
if long:G=G/'motion480'
assert mode in ['final','post','console','import','capture']and not(packed and mode=='import');relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text())['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==0;assert((H/'face93/witness-fix'if long else G if fixed else H/'face93')/'import/COMPLETE.json').exists()
 if packed:assert json.loads((G/'CPU_CODEC93.json').read_text())['old262144ByteCapUnchanged']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read current Editor/input/native/resources only','console':'Read Console errors only','import':'Create-only private ProjectedRibbon93 shader-only asset; no C# import/Refresh/default/scene/save/Play/GPU submit','capture':'One normal actual frame of native projected variable-width ribbon and existing92 finite colour/history. CPU-preflight bbox8192pixel/variant, source65536triangles/16draws per set, shader VS120/PS391 instructions with no loops/private arrays/compute.34planes367744B readback, native alpha/depth/current exterior gate, normal exit/full external-state restore; no115/default change.'}[mode]
if packed and mode=='capture':relay33.TITLE_OVERRIDE='One normal frame, same already-dispatched ribbon shader/geometry and92 colour/history; fix observation packing only to24planes259584B within unchanged262144B request/codec cap. CPU exact runtime codec tests required. No new shader/import/compute/default change; normal exit/full state restore.'
if fixed:relay33.TITLE_OVERRIDE={'final':'Read current Editor/input/native/resources only','console':'Read Console errors only','import':'Reimport only our private ProjectedRibbon93 shader after exact beforeSHA/GUID/meta backup and explicit-if witness fix. No source/scene/material/CSharp/default/save/Play changes.','capture':'One normal actual frame of guarded geometric witness. Same native-width ribbon/92 colour/history, fixed262144B cap with24planes259584B packing. Shader changed only out-parameter calls from chained logical expression to explicit guarded branches; no loops/private arrays/compute/115. Normal exit/full state restore.'}[mode]
if long and mode=='capture':relay33.TITLE_OVERRIDE='480 normal reciprocal move/turn frames,8s simulation. Same successfully observed440-instruction ribbon and92 finite colour/history;24planes259584B within unchanged262144B request/codec cap. No new shader/compute/import/default change. Explicit240s wall observation budget for doubled passed240-frame workload; never time-based release/retry. Normal exit/full input/native/resource restore.'
sys.argv=[sys.argv[0],mode];relay33.main()
