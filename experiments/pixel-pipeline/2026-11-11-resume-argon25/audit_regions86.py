from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_regions86 import partition,colour_fields
H=Path(__file__).resolve().parent;G=H/'face86'
def edges(a,b,mask):return int(np.count_nonzero(mask[:,1:]&mask[:,:-1]&(a[:,1:]!=a[:,:-1])&(b[:,1:]==b[:,:-1]))+np.count_nonzero(mask[1:]&mask[:-1]&(a[1:]!=a[:-1])&(b[1:]==b[:-1])))
def debug(labels):
 x=labels.astype(np.uint32);out=np.stack([(x*73+41)%256,(x*151+19)%256,(x*199+113)%256],2).astype(np.uint8);out[x==0]=0;return out
def main():
 G.mkdir(exist_ok=True);old=np.load(H/'face80/SOURCE_SUPPORT80.npz');native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3];p=partition(old['mask'],old['foreground']);assert np.array_equal(p['foreground'],old['foreground']);fields=colour_fields(rgb,p);oldcount=len(np.unique(old['labels'][old['foreground']]));cut=edges(old['labels'],p['regions'],p['foreground']);probes=[]
 for x,y in [(382,704),(380,704),(384,704)]:probes.append({'xy':[x,y],'RGB8':rgb[y,x].tolist(),'foregroundPreserved':bool(p['foreground'][y,x]),'newRegion':int(p['regions'][y,x]),'oldRegion':int(old['labels'][y,x])})
 result={'sourceRGBChanged':0,'foregroundTexelsAddedOrLost':0,'oldColourParentCutForegroundRegions':oldcount,'sourceConnectedForegroundRegions':p['pigmentCount'],'sourceBaseRegions':p['baseCount'],'nativeUVIslands':p['islandCount'],'artificialParentCutEdgesRemoved':cut,'exactConstantRGBRegions':sum(x['exactConstantRGB']for x in fields),'nonConstantRegions':sum(not x['exactConstantRGB']for x in fields),'nonConstantAffineWithinHalfCode':sum(x['affineWithinNativeHalfCodeInterval']and not x['exactConstantRGB']for x in fields),'paletteFamiliesAssigned':0,'GPUExecuted':False,'semanticRegionsOrAAAlphaProven':False,'fullFaceArtAdopted':False,'probes':probes};(G/'SOURCE_REGIONS86.json').write_text(json.dumps(result,indent=2));(G/'COLOUR_FIELDS86.json').write_text(json.dumps(fields,indent=2));np.savez_compressed(G/'REGIONS86.npz',**{k:p[k]for k in ['regions','pigment','base','island','foreground','mask']});print(json.dumps(result))
 box=(300,620,440,740);x0,y0,x1,y1=box;images=[(rgb,'Original source RGB'),(debug(np.where(old['mask'],old['labels']+1,0)),'Old parent-colour cut regions'),(debug(p['regions']),'Source-support regions; NOT palette colours')];board=Image.new('RGB',(1260,420),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(im,title)in enumerate(images):board.paste(Image.fromarray(im[y0:y1,x0:x1]).resize((420,360),Image.Resampling.NEAREST),(420*i,32));draw.text((420*i+5,7),title,fill='white')
 draw.text((5,394),'Identity only. No RGB emitted, no region declared one constant colour, no inferred AA matte.',fill='white');board.save(G/'SOURCE_REGION_COMPARISON86.png')
if __name__=='__main__':main()
