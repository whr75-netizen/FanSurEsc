"""Read the captured source/Q stages; do not classify final RGB colours as features."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sibling(short,archived):
 p=ROOT.parent/short
 return p if p.exists() else ROOT.parent/archived
CAPTURE=sibling('apply-capture66','2026-10-31-apply-capture66')
sys.path.insert(0,str(CAPTURE))
from analyse_capture68 import plane,rgb8,geometry,camera
sys.path.insert(0,str(sibling('region-stages63','2026-10-31-region-stages63')))
from shared_boundary63 import trace
state=json.loads((CAPTURE/'retry-background/CAPTURE_STATE66.json').read_text());PACKET=CAPTURE/'retry-background'/Path(state['output']).name
assert PACKET.is_dir(),'Matching source packet must be available locally'
def planes():
 return {p.stem:plane(p)[1] for p in PACKET.glob('*.plane') if not p.stem.startswith('final-strip')}
def counts(labels,mask):
 h,w=mask.shape;seen=set();groups=[]
 for y,x in np.argwhere(mask):
  p=(int(y),int(x))
  if p in seen:continue
  seen.add(p);todo=[p];found=[]
  while todo:
   yy,xx=todo.pop();found.append((xx,yy))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    nx,ny=xx+dx,yy+dy
    if 0<=nx<w and 0<=ny<h and mask[ny,nx] and labels[ny,nx]==labels[yy,xx] and (ny,nx) not in seen:seen.add((ny,nx));todo.append((ny,nx))
  groups.append({'label':int(labels[y,x]),'size':len(found),'cells':found})
 edges,paths=trace(labels,mask)
 return {'components':len(groups),'singletons':[g['cells'][0] for g in groups if g['size']==1],'componentSizes':sorted(g['size'] for g in groups),'sharedEdges':len(edges),'paths':len(paths),'groups':groups,'boundaryPaths':paths}
def main():
 a=planes();logicalMeta=np.zeros((272,480,4),np.float32)
 for n,v in a.items():
  if n.startswith('source-meta-strip-'):y=int(n.rsplit('-',1)[1]);logicalMeta[y:y+len(v)]=v
 lx,ly,lw,lh=state['sourceROIBottomLeft'];lm=logicalMeta[ly:ly+lh,lx:lx+lw];nm=a['native-endpoint'];m=(nm[...,0]>0)&(nm[...,1]>=11.5)&(nm[...,1]<=15.5);mask=(lm[...,0]>0)&(lm[...,1]>=11.5)&(lm[...,1]<=15.5)
 records={}
 for name,cl,ma,coord in [('native',a['style-class'],m,[lx*2,ly*2]),('logical',a['shade-class480'],mask,[lx,ly])]:
  q=np.floor(np.clip(cl[...,1],0,1)+.5).astype(int);stored=np.rint(cl[...,0]).astype(int);cs=counts(stored,ma);before=counts(q,ma);diff=np.argwhere(ma&(q!=stored));changes=[{'xy':[int(x+coord[0]),int(271-(y+coord[1]))] if name=='logical' else [int(x+coord[0]),int(543-(y+coord[1]))],'g':float(cl[y,x,1]),'rawQ':int(q[y,x]),'storedQ':int(stored[y,x])} for y,x in diff]
  records[name]={'maskCells':int(ma.sum()),'before':before,'stored':cs,'boundaryPassChanged':changes}
 # All representative figures use this actual hair bounding box and unchanged saved colours.
 yy,xx=np.where(m);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));x0,y0,x1,y1=box
 yy,xx=np.where(mask);lbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));i,j,k,l=lbox
 previews=[]
 for name,img in [('Unlit source / native',rgb8(a['unlit-source'][y0:y1,x0:x1,:3])),('g continuous / native',np.repeat(np.rint(a['style-class'][y0:y1,x0:x1,1:2]*255).clip(0,255).astype('uint8'),3,axis=2)),('Q raw / logical',np.where(np.floor(a['shade-class480'][j:l,i:k,1:2]+.5)>0,np.array([235,160,35]),np.array([25,120,170])).astype('uint8')),('Q stored / logical',np.where(a['shade-class480'][j:l,i:k,0:1]>.5,np.array([235,160,35]),np.array([25,120,170])).astype('uint8')),('Current product / logical',rgb8(a['source-final'][j:l,i:k,:3]))]:
  if name.startswith('Q '):img[~mask[j:l,i:k]]=0
  im=Image.fromarray(np.flipud(img));scale=4 if 'native' in name else 8;im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);previews.append((name,im))
 width=sum(im.width+16 for _,im in previews);height=max(im.height for _,im in previews)+60;board=Image.new('RGB',(width,height),(28,29,34));draw=ImageDraw.Draw(board);x=8
 for name,im in previews:draw.text((x,8),name,fill='white');board.paste(im,(x,35));x+=im.width+16
 board.save(ROOT/'STAGES69.png')
 records.update({'sourceId':state['sourceId'],'nativeBoxInROI':box,'logicalBoxInROI':lbox,'logicalOriginBottomLeft':[lx,ly]})
 (ROOT/'PROBE69.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({n:{'mask':records[n]['maskCells'],'rawComponents':records[n]['before']['components'],'storedComponents':records[n]['stored']['components'],'rawSingletons':records[n]['before']['singletons'],'storedSingletons':records[n]['stored']['singletons'],'boundaryPassChanges':records[n]['boundaryPassChanged']} for n in ['native','logical']},indent=2));print('BOX',box,lbox)
if __name__=='__main__':main()
