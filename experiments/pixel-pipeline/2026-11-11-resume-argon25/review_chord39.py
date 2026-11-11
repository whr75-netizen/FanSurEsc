from pathlib import Path
import json,numpy as np
from source_chord39 import chord_intervals,monotone
H=Path(__file__).resolve().parent;G=H/'face39'
def main():
 data=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=data['rgba'][...,:3];mask=data['mask'];old=json.loads((H/'face28/SOURCE_EXTREMA28.json').read_text());rows=[]
 for p in old['points']:
  x,y=p['cropXY'];r=4;strip=rgb[y,x-r:x+r+1];assert mask[y,x-r:x+r+1].all();q=chord_intervals(strip,strip[0],strip[-1]);rows.append({'sourceXY':[x,y],'flankAnchorsRGB8':[strip[0].tolist(),strip[-1].tolist()],'stripRGB8':strip.tolist(),'compatibleWithFlankChord':q['compatible'].tolist(),'monotoneIncreasing':monotone(q),'monotoneDecreasing':monotone(q,True),'priorPositiveExtremum':p['positiveTwoSidedExtremum'],'regionOrFamilyAssigned':False})
 report={'source':'Unchanged source28 native image; RGB8 uncertainty intervals in linear light','rows':rows,'result':'An incompatible weak-mark sample cannot be replaced by the flank gradient. Compatible samples remain ambiguous gradient/AA, not new colour regions.','UnityGPUCalls':0,'finalPaletteRegionContractResolved':False};(G/'SOURCE_CHORD39.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
