from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_profile71 import fit_profiles
from profile_regions76 import support,children,original_references
H=Path(__file__).resolve().parent;G=H/'face76'
def main():
 G.mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3].astype(float);mask=native['mask'];p=np.load(H.parent/'source-regions104/part3/geodesic-labels.npz');assert np.array_equal(p['mask'],mask);parent=p['labels'];a=np.load(H/'face70/RIDGE_EVIDENCE70.npz');rows=np.argwhere(a['persistent']);fit=fit_profiles(rgb,rows,a['nx'],a['ny'],a['px'],a['py']);foreground,source=support(rgb,mask,rows,fit,a['nx'],a['ny'],a['px'],a['py']);labels,cc=children(parent,mask,foreground);refs=original_references(rgb,mask,labels,cc,source,rows);out=np.zeros_like(rgb,dtype=np.uint8);old=out.copy()
 for label,ref in refs.items():out[mask&(labels==label)]=ref['RGB8']
 for label in np.unique(parent[mask]):
  pts=np.argwhere(mask&(parent==label));col=rgb[pts[:,0],pts[:,1]].astype(np.uint8);code=col[:,0].astype(np.int64)*65536+col[:,1].astype(np.int64)*256+col[:,2];values,counts=np.unique(code,return_counts=True);at=np.flatnonzero(code==values[np.argmax(counts)])[0];old[mask&(parent==label)]=col[at]
 sizes=[len(c['coords'])for c in cc];probes=[]
 for x,y in[(382,704),(380,704),(384,704)]:probes.append({'xy':[x,y],'native':rgb[y,x].astype(int).tolist(),'oldParent':int(parent[y,x]),'newRegion':int(labels[y,x]),'foreground':bool(foreground[y,x]),'oldReference':old[y,x].tolist(),'newReference':out[y,x].tolist()})
 result={'hypothesis':'frozen105 parents plus source-profile native-supported child masks','parentRegions':int(len(np.unique(parent[mask]))),'childRegions':len(cc),'childSingletons':sum(n==1 for n in sizes),'fullCoverage':bool((labels[mask]>=0).all()),'originalSourceRGBChanged':0,'familyPerTexel':False,'newUniqueReferenceColours':len({tuple(v['RGB8'])for v in refs.values()}),'probes':probes,'semanticSegmentationOrArtAdopted':False,'GPUExecuted':False};(G/'CPU_PROFILE_REGIONS76.json').write_text(json.dumps(result,indent=2));(G/'SOURCE_REFERENCES76.json').write_text(json.dumps(refs));np.savez_compressed(G/'SOURCE_REGIONS76.npz',labels=labels,mask=mask,foreground=foreground,parent=parent);print(json.dumps(result))
 regions=np.stack([((labels+1)*73)%255,((labels+1)*137)%255,((labels+1)*211)%255],2).astype(np.uint8);regions[~mask]=0;board=Image.new('RGB',(1000,780),(27,29,35));d=ImageDraw.Draw(board)
 for i,(im,title)in enumerate([(rgb.astype(np.uint8),'Native source'),(old,'105 parent reference only'),(out,'Profile child candidate'),(regions,'Closed label partition')]):
  x=(i%2)*500;y=(i//2)*390;d.text((x+8,y+8),title,fill='white');board.paste(Image.fromarray(im[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(x+8,y+26))
 board.save(G/'PROFILE_CHILD76.png');Image.fromarray(out).save(G/'FULL_REFERENCE76.png')
if __name__=='__main__':main()
