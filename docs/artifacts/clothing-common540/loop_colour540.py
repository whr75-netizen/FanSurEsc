from pathlib import Path
import json,struct
import numpy as np
O=Path(__file__).resolve().parent;R=O/'FullLoop540';x,y=233,99
def cell(frame,mode,stage):
 b=(R/f'{frame:03d}_{mode}_{stage}.bin').read_bytes();w,h,ox,oy=struct.unpack_from('<4i',b);a=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a[y-oy,x-ox].tolist()
j={'xy':[x,y],'samples':{},'scope':'Diagnostic loop-end address, not a product condition. Endpoints are not asserted identical source poses.'}
for mode in ['OFF','CLOTH']:
 values={str(f):{s:cell(f,mode,s)for s in ['PREPARED','POSTLINE','FINAL','META','UV']}for f in [0,80]};j['samples'][mode]=values
 stages=[s for s in ['PREPARED','POSTLINE','FINAL']if max(abs(a-b)for a,b in zip(values['0'][s],values['80'][s]))>1e-6];j[mode+'FirstChangedSavedStage']=stages[0]if stages else None
(O/'LOOP_COLOUR540.json').write_text(json.dumps(j,indent=2));print(json.dumps(j))
