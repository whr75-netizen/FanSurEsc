"""Small negative/source-identity and UV-ST fixtures; no Unity or full packet replay."""
from pathlib import Path
import json,numpy as np
from analyse_capture68 import identity_check,plane,STATE
state=json.loads(STATE.read_text(encoding='utf-8'));packet=Path(state['output']);h,_=plane(packet/state['planes'][0]['file']);identity_check(h,state);passed=1
for key in ['sourceId','frameIndex','mainRenderedSerial335']:
 bad=dict(state);bad[key]=str(bad[key])+'-different' if key=='sourceId' else bad[key]+1
 try:identity_check(h,bad)
 except AssertionError:passed+=1
 else:raise AssertionError('Mismatched '+key+' accepted')
tri=np.array([[.1,.2],[.7,.25],[.2,.9]]);weights=np.array([.2,.3,.5]);st=np.array([1.7,.8,-.1,.15]);sample=(weights@tri)*st[:2]+st[2:];source=(sample-st[2:])/st[:2];b=np.linalg.solve(np.stack([tri[1]-tri[0],tri[2]-tri[0]],axis=1),source-tri[0]);assert np.max(np.abs(np.r_[1-b.sum(),b]-weights))<1e-12;passed+=1
receipt={'passed':passed,'scope':['matching actual plane identity','reject different sourceId','reject different frame','reject different render serial','nonidentity texture ST UV barycentric fixture'],'limits':'Not renderer/temporal/feature-shape tests'}
(packet/'offline68/READER_TEST68.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
