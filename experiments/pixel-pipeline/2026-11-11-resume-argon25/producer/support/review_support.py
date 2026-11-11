"""Inspect real completed candidate packets; unknown preservation stays unknown."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'bounded-form115/runtime24/full-render24'))
from report_full24 import read,plane,buffer,full,rgba

def main():
 root=H/'phase-run';s=read(root/'STATE113-0008-finished.json')
 assert s['PlayExited']and not s.get('error')and not s.get('restorationError')and not s['globalRestoreErrors']
 native=s['nativeComparisons72'];assert not any(v.get('equal')is False for v in native)
 unknown=[v for v in native if v.get('equal')is None]
 assert all(v['path']=='ProjectSettings/ProjectSettings.asset'and v['type']=='UnityEditor.AssetImporter'and v['status']=='Unavailable'for v in unknown)
 assert s['motionRestoration82']['allRestored']and s['editInputRestoration82']['sameAliveReference']and s['editInputRestoration82']['exactJSON']
 lut=read(R/'argon23-runtime113/SOURCE113.json');out=root/'results';out.mkdir(exist_ok=True);rows=[];maps=[];images=[];cropped=0;coordinateCount=0;paletteTests=0
 for i,pkt in enumerate(s['sequencePackets']):
  p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
  assert m['sourceId']==pkt['sourceId']and m['algorithmValid113']and m['frameUnchangedDuringReadback']
  n=m['forward102'];rx,ry,w,h=m['grid102']['eyeTopLeftROI'];o=np.array(n['headHair25']['origin'],np.float32);cw,ch=np.array(n['canonicalSize'])//4
  assert [rx,ry,w,h]==n['outputROI26']and n['physicalHair26']['frame']==m['frameIndex']
  ids=buffer(p/'curve-identity.f32').reshape(ch,cw,4);colour=buffer(p/'curve-colour.f32').reshape(ch,cw,4)
  _,fo=plane(p/'F-FinalOwner.plane');_,fc=plane(p/'F-FinalRGBA.plane');_,eo=plane(p/'F-EyeOwner.plane');q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4)
  cells={}
  for y in range(h):
   for x in range(w):
    c=np.floor(np.asarray([rx+x+.5,ry+h-y-.5],np.float32)-o).astype(int);cx,cy=c
    expected=o+c.astype(np.float32)+np.asarray([[(j%4+.5)/4,1-(j//4+.5)/4]for j in range(16)],np.float32)
    valid=q[y,x,:,2]>0;assert np.array_equal(q[y,x,valid,:2],expected[valid]);coordinateCount+=int(valid.sum())
    if not(0<=cx<cw and 0<=cy<ch)or ids[cy,cx,0]<=0:continue
    cells[int(cx),int(cy)]={'identity':ids[cy,cx].tolist(),'preHair':eo[y,x].tolist(),'final':fo[y,x].tolist(),'RGB':fc[y,x,:3].tolist()}
    role,owner=fo[y,x,:2].astype(int)
    if role in(2,5,7):
     part=role-1;pal=lut['lidPalette']if part==6 else lut['keys'];rgb=np.array([v['linear']for v in pal if v['owner']==owner and(part==6 or v['part']==part)],np.float32)
     assert np.any(np.all(rgb==fc[y,x,:3],axis=1));paletteTests+=1
  missing=[(int(x),int(y))for y,x in np.argwhere(ids[...,0]>0)if(int(x),int(y))not in cells];cropped+=len(missing);assert not missing
  product,sid=full(p,'product77');candidate,sid2=full(p,'candidate113');assert sid==sid2==m['sourceId']
  ox,oy=m['grid102']['headToMainOffset'];xx=rx+round(ox);yy=272-ry-h+round(oy);outside=np.ones(product.shape[:2],bool);outside[yy:yy+h,xx:xx+w]=False;assert np.array_equal(product[outside],candidate[outside])
  for name,a in [('control',product),('candidate',candidate)]:
   im=Image.fromarray(rgba(np.flipud(a)));im.save(out/f'{i:02d}-{name}.png');im.crop((xx,272-yy-h,xx+w,272-yy)).resize((w*16,h*16),Image.Resampling.NEAREST).save(out/f'{i:02d}-{name}-eye.png')
   if name=='candidate':images.append(im)
  maps.append(cells);rows.append({'sourceId':sid,'frame':m['frameIndex'],'serial':m['mainSerial'],'candidateROI':[rx,ry,w,h],
    'originalROI':n['originalROI26'],'allocatedCells':len(cells),'croppedCells':len(missing),'leftLid':cells[0,3],
    'white':cells[3,4],'finalParts':dict(collections.Counter(str(tuple(fo[y,x,:2].astype(int)))for y in range(h)for x in range(w)if int(fo[y,x,0])in(2,5,7)))})
 assert len(rows)==2 and rows[1]['frame']==rows[0]['frame']+1
 assert all(v['leftLid']['final'][:2]==[7,2]and v['white']['final'][:2]==[5,2]for v in rows)
 differences=[{'canonical':list(k),'before':maps[0][k],'after':maps[1][k]}for k in sorted(maps[0])if maps[0][k]['final'][:2]!=maps[1][k]['final'][:2]]
 eyeChanges=[v for v in differences if v['before']['final'][0]in(2,5,7)or v['after']['final'][0]in(2,5,7)];assert not eyeChanges
 result={'actualFrames':rows,'allocatedCellsCropped':cropped,'queryCoordinatesExact':coordinateCount,'linearPaletteExactChecks':paletteTests,'paletteOutside':0,
  'visibleEyeLabelChanges':len(eyeChanges),'nonEyeFallbackChanges':differences,'fullPhaseInvariant':not differences,
  'nativeEqual':sum(v.get('equal')is True for v in native),'nativeUnavailable':unknown,'nativeUnequal':0,
  'PlayNormallyExited':True,'inputSameReferenceAndJSON':True,'globalRestoreErrors':[],
  'memoryBefore':s['beforeMemory'],'memoryAfter':s['afterMemory'],'allocatedDeltaBytes':s['afterMemory']['allocated']-s['beforeMemory']['allocated'],
  'memoryAPI':'Profiler.GetTotalAllocatedMemoryLong; not physical working set','product77DefaultChanged':False,
  'limits':['Two phase states only; full rotation/Close/hair matrix untested for this output change.','Shared skin source gate and full face UV palette/outline remain incomplete.','Unavailable clean LibraryAssetImporter145B is not reported as equality or full native identity preservation.']}
 (H/'GPU_SUPPORT26.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 board=Image.new('RGB',(620,355),(32,32,32));d=ImageDraw.Draw(board)
 for i in range(2):
  for j,name in enumerate(['control','candidate']):
   im=Image.open(out/f'{i:02d}-{name}-eye.png').convert('RGB');board.paste(im,(j*310,i*170+25));d.text((j*310+4,i*170+5),f'{name} GPU frame{rows[i]["frame"]}',fill='white')
 board.save(H/'EYE_SUPPORT26.png');images[0].save(out/'SEQUENCE_SUPPORT26.webp',save_all=True,append_images=images[1:],duration=220,loop=0,lossless=True)
 print(json.dumps({'frames':2,'clippedCells':cropped,'eyeLabelChanges':0,'nonEyeFallbackChanges':len(differences),'nativeEqual':result['nativeEqual'],'nativeUnavailable':len(unknown),'allocatedDeltaMiB':result['allocatedDeltaBytes']/1048576}))
if __name__=='__main__':main()
