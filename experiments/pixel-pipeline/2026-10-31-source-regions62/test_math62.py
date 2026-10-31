from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from region62 import lab,rgb8
R=Path(__file__).resolve().parent;module=R.parent/'source-palette54/colour-math.cjs'
if not module.exists():module=R.parent/'2026-10-31-source-palette54/colour-math.cjs'
rng=np.random.default_rng(6201);samples=np.vstack([[[0,0,0],[255,255,255],[255,0,0],[0,255,0],[0,0,255],[50,28,29]],rng.integers(0,256,(512,3))]).astype('uint8')
js='const fs=require("fs"),m=require(process.argv[1]),a=JSON.parse(fs.readFileSync(0,"utf8"));process.stdout.write(JSON.stringify(a.map(m.rgbLab)));'
r=subprocess.run(['node','-e',js,str(module.resolve())],input=json.dumps(samples.tolist()),capture_output=True,encoding='utf8');assert r.returncode==0,r.stderr
expected=np.array(json.loads(r.stdout));actual=lab(samples);error=float(np.max(np.abs(expected-actual)));assert error<1e-14,error
out=np.array([rgb8(L,float(np.hypot(a,b)),float(np.arctan2(b,a)))for L,a,b in actual]);mismatch=int(np.count_nonzero(np.any(out!=samples,axis=1)));assert mismatch==0,mismatch
(R/'MATH_TEST62.json').write_text(json.dumps({'samples':len(samples),'existing54MathSHA256':hashlib.sha256(module.read_bytes()).hexdigest(),'maxLabError':error,'sRGB8RoundtripMismatches':mismatch,'initialCandidateMathError':'Two OKLab matrix coefficients transposed; invalid purple PNG saved separately, not adopted'},indent=2),encoding='utf8');print('math passed',len(samples),error,mismatch)
