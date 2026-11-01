"""Exact existing public source transform, no fitted transform in production."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;R=H.parent;D=H/'direct'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle

def main():
    D.mkdir(exist_ok=False)
    for mode in ('Compile','Capture','Post','Verify'):
        for run in (False,True):
            name=('RUN_'if run else'')+mode+'102'+('.cs.txt'if run else'.cs')
            s=(H/name).read_text(encoding='utf-8').replace(str(H),str(D))
            if mode in ('Compile','Capture'):
                needle='report["headMatrix105"]=M(e.headMatrix);'
                assert s.count(needle)==1
                s=s.replace(needle,needle+'var maps105=new Arr58();for(int i105=0;i105<e.centres.Length;i105++)maps105.Add(new Obj58{["eye"]=(int)Mathf.Round(e.centres[i105].w),["inverseHomography"]=M(e.full.eyeInverse[i105])});report["existingEyeInverse105"]=maps105;')
            (D/name).write_text(s,encoding='utf-8')
    (D/'GLOBAL_NAMES66.json').write_bytes((H/'GLOBAL_NAMES66.json').read_bytes())
    (D/'relay102.py').write_bytes((H/'relay102.py').read_bytes())
    print('Prepared exact existing eyeInverse per eye (128bytes/frame), same 3 states. No Assets/Unity change.')
if __name__=='__main__':main()
