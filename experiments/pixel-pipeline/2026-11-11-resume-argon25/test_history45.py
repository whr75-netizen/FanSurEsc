from pathlib import Path
import json,struct,hashlib
import numpy as np
import test_carrier43 as compiler
from test_carrier43 import write_string
from surface_paths34 import native
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face45';B=G/'build';B.mkdir(parents=True,exist_ok=True);compiler.B=B
def compile_run(main):
 src='using System;using System.IO;using System.Linq;using System.Collections.Generic;using UnityEngine;\n'
 for name in ['CurveHistory45.cs',main+'.cs']:
  src+='\n'+'\n'.join(x for x in(H/name).read_text().splitlines()if not x.startswith('using '))
 out=B/(main+'.cs.txt');out.write_text(src,encoding='utf-8',newline='\n')
 return compiler.compile_run(main,str(out.relative_to(H)),[G/'ACTUAL_INPUT45.bin']if main=='ReplayHistory45'else[])
def main():
 unit=compile_run('CurveHistoryTests45');(G/'CPU_HISTORY45.json').write_text(json.dumps(unit,indent=2),encoding='utf-8')
 surface,binding=native();fixture=G/'ACTUAL_INPUT45.bin';integer=lambda f,v:f.write(struct.pack('<i',int(v)))
 with fixture.open('wb')as out:
  write_string(out,'source-history45/v1');integer(out,binding['rendererOrdinal']);integer(out,binding['subMesh']);integer(out,len(surface.uv));out.write(surface.uv.astype('<f4').tobytes());integer(out,12)
  for case in ['capture','world/capture']:
   c=H/'face44'/case;r=json.loads((c/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['pendingOwners']==0 and not r['errors']
   for f in r['frames']:
    g=geometry(c/('geometry-frame'+str(f['frame'])+'.bin'));assert g['sourceId']==f['sourceId'];p=next(p for p in r['planes']if p['frame']==f['frame']and p['name']=='atlas40');a=np.fromfile(c/p['file'],dtype='<f4').reshape(p['height'],p['width'],4);w=f['QROI'][2];mask=a[:,3*w:4*w,3]==1;proof=a[:,4*w:5*w][mask];visible=a[:,11*w:12*w,3][mask]==1;anchor=f['frameInfo']['sourceAnchor'];info=f['frameInfo']['nativeComposite42']
    for value in [g['sourceId'],g['model'],anchor['actorInstance'],anchor['camera']]:write_string(out,value)
    integer(out,g['frame']);out.write(struct.pack('<q',info['presentSerialExecuted']));integer(out,len(g['points']));out.write(g['points']['world'].astype('<f4').tobytes());tri=g['indices'][binding['subMesh']].astype('<i4');integer(out,tri.size);out.write(tri.tobytes());out.write(g['points']['weld'].astype('<i4').tobytes());integer(out,len(proof))
    for sample,shown in zip(proof,visible):integer(out,round(sample[1]));out.write(struct.pack('<f?',float(sample[2]),bool(shown)))
 actual=compile_run('ReplayHistory45');actual['fixtureSHA256']=hashlib.sha256(fixture.read_bytes()).hexdigest();actual['sourceSHA256']=hashlib.sha256((H/'CurveHistory45.cs').read_bytes()).hexdigest();(G/'ACTUAL_HISTORY45.json').write_text(json.dumps(actual,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in actual.items()if k!='rows'}))
if __name__=='__main__':main()
