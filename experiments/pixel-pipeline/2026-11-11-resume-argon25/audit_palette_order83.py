"""Separate continuous OKLCH transformation from RGB8 order loss. CPU only."""
from pathlib import Path
import json,os,subprocess,numpy as np
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face82'
def main():
 exe=G/'build/palette-detail82.exe';csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';r=subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'PaletteTable82.cs'),str(H.parent/'source-palette58/SourcePalette58.cs')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 detail=G/'build/PALETTE_DETAIL83.bin';out=G/'build/PALETTE_DETAIL83.rgb';subprocess.run([str(exe),str(G/'build/INPUT.bin'),str(out),str(detail)],check=True);assert out.read_bytes()==(G/'PALETTE82.rgb').read_bytes()
 addresses=np.load(G/'SOURCE_FIELD82.npz')['colourAddress'];orders=np.load(G/'ORDER_INPUT82.npz')['orders'];refs=np.array(json.loads((G/'HIERARCHY82.json').read_text())['references']);levels=json.loads((G/'DISPLAY82.json').read_text())['settingsUnchangedFrom67']['count'];p=np.fromfile(out,np.uint8).reshape(len(refs),levels,3);d=np.fromfile(detail,'<f8').reshape(len(refs),levels,2);rows=[]
 for k in range(levels):
  row={'shade':k,'violations':0,'continuousTransformReversesY':0,'RGB8OnlyLoss':0,'outputRGBEqual':0,'examples':[]}
  for a,b in orders:
   lo,hi=map(int,[addresses[int(a)],addresses[int(b)]]);before=luminance(refs[[lo,hi]]);after=luminance(p[[lo,hi],k]);continuous=d[[lo,hi],k,0];assert before[0]<before[1]
   if after[0]>=after[1]:
    row['violations']+=1;bad=continuous[0]>=continuous[1];row['continuousTransformReversesY']+=int(bad);row['RGB8OnlyLoss']+=int(not bad);row['outputRGBEqual']+=int(np.array_equal(p[lo,k],p[hi,k]))
    if len(row['examples'])<4:row['examples'].append({'nativeReferences':refs[[lo,hi]].tolist(),'sourceY':before.tolist(),'continuousTransformedY':continuous.tolist(),'paletteRGB8':p[[lo,hi],k].tolist(),'paletteY':after.tolist()})
  rows.append(row)
 result={'existingCSharp58Reused':True,'changedPaletteBytes':False,'CPUOnly':True,'rows':rows,'interpretation':'Independent per-reference OKLCH ramps do not guarantee cross-family linear-Y contrast order; this audit does not infer semantic face regions or prescribe new art parameters.'};(G/'PALETTE_ORDER_CAUSE83.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
