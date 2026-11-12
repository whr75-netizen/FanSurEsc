from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_profile71 import fit_profiles
from source_hysteresis80 import linked
from profile_regions76 import support,children
H=Path(__file__).resolve().parent;G=H/'face80'

def count8(mask):return len(linked(mask,mask)[1])

def main():
 G.mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3].astype(float);mask=native['mask'];a=np.load(H/'face70/RIDGE_EVIDENCE70.npz');fine=a['strong1'];rows=np.argwhere(fine);nx,ny,px,py=[a[k]for k in['nx','ny','px','py']];fit=fit_profiles(rgb,rows,nx,ny,px,py);allowed=np.zeros(mask.shape,bool);winning=fit['lineWins'];allowed[rows[winning,0],rows[winning,1]]=True;seeds=allowed&a['persistent'];retained,cc=linked(allowed,seeds);keep=retained[rows[:,0],rows[:,1]];selected_rows=rows[keep];selected_fit={k:v[keep]for k,v in fit.items()};fg,source=support(rgb,mask,selected_rows,selected_fit,nx,ny,px,py);parent=np.load(H/'face76/SOURCE_REGIONS76.npz')['parent'];labels,child=children(parent,mask,fg);old=np.load(H/'face76/SOURCE_REGIONS76.npz')['foreground'];probes=[]
 for x,y in[(382,704),(380,704),(384,704)]:probes.append({'xy':[x,y],'nativeRGB':rgb[y,x].astype(int).tolist(),'oldForeground':bool(old[y,x]),'newForeground':bool(fg[y,x]),'fineLineEvidence':bool(allowed[y,x]),'retainedRidge':bool(retained[y,x]),'newRegion':int(labels[y,x])})
 result={'fineScaleStrongPixels':int(fine.sum()),'fineScaleLineWinningPixels':int(allowed.sum()),'crossScaleLineSeeds':int(seeds.sum()),'retainedSourceRows':int(retained.sum()),'seedComponents':count8(seeds),'linkedComponents':len(cc),'newChildRegions':len(child),'newChildSingletons':sum(len(c['coords'])==1 for c in child),'newObservedForegroundTexels':int((fg&~old).sum()),'oldForegroundLost':int((old&~fg).sum()),'probes':probes,'allNewRidgesAlreadyObservedFineScale':bool((retained&~allowed).sum()==0),'semanticColourFamiliesAssigned':0,'sourceRGBChanged':0,'GPUExecuted':False,'wholeFacePaletteOrArtAdopted':False};(G/'HYSTERESIS_RESULT80.json').write_text(json.dumps(result,indent=2));np.savez_compressed(G/'SOURCE_SUPPORT80.npz',labels=labels,foreground=fg,parent=parent,mask=mask,retained=retained,rows=selected_rows,source=source);print(json.dumps(result))
 box=(300,620,440,740);x0,y0,x1,y1=box;raw=rgb[y0:y1,x0:x1].astype(np.uint8);debug=raw.copy();debug[old[y0:y1,x0:x1]]=[255,150,30];debug[(fg&~old)[y0:y1,x0:x1]]=[0,220,240];board=Image.new('RGB',(840,420),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(v,title)in enumerate([(raw,'Native source, unchanged'),(debug,'Orange old support | cyan newly measured support')]):board.paste(Image.fromarray(v).resize((420,360),Image.Resampling.NEAREST),(i*420,32));draw.text((i*420+5,7),title,fill='white')
 draw.text((5,397),'CPU source evidence only. No RGB output, inferred endpoint or palette adoption.',fill='white');board.save(G/'MEASURED_ENDS80.png')
if __name__=='__main__':main()
