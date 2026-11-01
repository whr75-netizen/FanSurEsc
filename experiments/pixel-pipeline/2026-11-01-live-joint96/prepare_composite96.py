from pathlib import Path
import json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'final-eye95'
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import camera
sys.path.insert(0,str(HERE));from prepare_inputs96 import string
def main():
    state=json.loads((OLD/'capture-scale-correct/STATE95B-0018-finished.json').read_text())
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));m=d['m'];a=d['a'];ref=m['nativeFinalReference89'];nr=ref['nativeROI'];roi=m['currentSources91']['roiTopLeft'];off=np.asarray(m['trace86']['headJoinOffset'])+np.asarray(m['camera86']['deliveredDelta'][:2]);anchor=np.asarray(m['retarget89']['anchor'])+np.asarray(m['retarget89']['bounds'][:2]);depth=camera(d['path']/'source.camera')['view'][2,3]-camera(d['path']/'main.camera')['view'][2,3]
        with(HERE/f'fixtures/composition{e["frame"]}.bin').open('xb')as f:
            string(f,'whole-eye96-composition/v1');f.write(struct.pack('<i',e['frame']))
            for p in [nr,d['roi'],roi,d['eyeROI'],[*ref['origin'],ref['scale'],0],[*off,0,0],[*anchor,0,0]]:f.write(np.asarray(p,'<f4').tobytes())
            f.write(struct.pack('<f',depth));records=d['records'].astype('<f4');f.write(struct.pack('<i',records.shape[0]*records.shape[1]));f.write(records.tobytes())
            for name in ['native-final-rgba','native-final-owner','native-final-depth','old-eye-owner','old-intrinsic','current91-g2-0','current91-g2-1','current91-g2-3']:
                ar=a[name];f.write(struct.pack('<2i',ar.shape[1],ar.shape[0]));f.write(ar.astype('<f4').tobytes())
    print('Prepared seven composition input fixtures, actual source only.')
if __name__=='__main__':main()
