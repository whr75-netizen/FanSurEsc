"""Read saved frame95 geometry; single-cell CPU selection replay, no Unity start."""
from pathlib import Path
import sys, json, hashlib, collections, datetime
import numpy as np
from PIL import Image, ImageDraw

O=Path(__file__).resolve().parent;R=O.parents[1]
sys.path.insert(0,str(R))
from geometry_edges import Geometry
from coverage35 import read
load=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')


def cell_raster(G,scale,offset=(.5,.5),reverse=False):
    """Same fixed [7,8]x[29,30] footprint; vary CPU integration points only."""
    depth=np.full((scale,scale),np.inf);owner=np.full((scale,scale),-1,int)
    X,Y=np.meshgrid(7+(np.arange(scale)+offset[0])/scale,29+(np.arange(scale)+offset[1])/scale)
    indices=np.flatnonzero(G.valid & np.all(G.p.max(axis=1)>=[7,29],axis=1)&np.all(G.p.min(axis=1)<=[8,30],axis=1))
    if reverse:indices=indices[::-1]
    for index in indices:
        p=G.p[index];d=np.stack([X,Y],-1)-p[0];uv=d@G.inv[index].T;b=np.dstack([1-uv.sum(axis=-1),uv])
        valid=b.min(axis=-1)>=-1e-12;z=np.sum(b*G.z[index],axis=-1);update=valid&(z<depth)
        depth[update]=z[update];owner[update]=G.chart[index]
    return owner,depth


def select(owner,scale,offset,pool,original_chart):
    ids,counts=np.unique(owner[owner>=0],return_counts=True);candidates=[];centres={}
    for chart,count in zip(ids,counts):
        points=np.argwhere(owner==chart)
        centre=np.array([7,29])+(points[:,::-1].mean(axis=0)+np.array(offset))/scale
        centres[int(chart)]=centre.tolist()
        for row in pool:
            if row['chart']!=chart or np.max(np.abs(np.array(row['point'])-[7.5,29.5]))>.751:continue
            distance=float(np.sum((np.array(row['point'])-centre)**2))
            candidates.append((int(count),int(chart)==original_chart,distance,row))
    best=max(p[0]for p in candidates);short=[p for p in candidates if p[0]==best]
    old=[p for p in short if p[1]]
    if old:short=old
    chosen=min(short,key=lambda p:(p[2],p[3]['sampleKind']!='centre480',p[3]['fineY'],p[3]['fineX']))
    return chosen[3],{'coverageCounts':{int(c):int(n)for c,n in zip(ids,counts)},'hairSamples':int((owner>=0).sum()),
                      'samples':scale**2,'centroids':centres,'sourceCandidates':[{'chart':p[3]['chart'],'areaCount':p[0],
                       'originalPreference':bool(p[1]),'distanceSquared':p[2],'Q':sum(p[3]['g']>=t for t in THRESHOLDS),
                       'packet':p[3]}for p in sorted(candidates,key=lambda p:(-p[0],not p[1],p[2],p[3]['sampleKind']!='centre480',p[3]['fineY'],p[3]['fineX']))]}


def main():
    source=load(R/'source-export/bundle/prelight-source.json');frame=load(R/'source-export/bundle/frame-source-data.json')
    binding=load(R/'geometry-export/GEOMETRY_BINDING.json');pool=load(R/'coverage-v3/PACKET_POOL.json')
    selected=load(R/'ribbon-path/GEOMETRY_PACKETS.json')[935]
    centre=next(p for p in pool if p['sampleKind']=='centre480' and p['fineX']==15 and p['fineY']==58)
    G=Geometry();checks=[]
    def check(name,value):
        assert value,name
        checks.append({'name':name,'pass':True})
    check('paired source/frame sourceId identical',source['sourceId']==frame['sourceId'])
    check('both representative packets found exactly in the same frozen pool',centre in pool and selected in pool)
    check('source centre g/UV/primitive agree',centre['g']==source['cells'][935]['g'] and centre['uv']==source['cells'][935]['uv'] and centre['primitive']==source['cells'][935]['primitiveId'])
    raw480,raw960=read('light480-3'),read('light960-3')
    check('both g values exactly match their hashed saved light buffers',float(raw480[29,7,1])==centre['g'] and float(raw960[selected['fineY'],selected['fineX'],1])==selected['g'])
    for name in ['light480-3.bin','light960-3.bin','source480-6.bin','source960-6.bin']:
        check(name+' hash belongs to this sourceId',sha(R/'source-export'/name)==source['rawBuffers'][name])
    hit_a,hit_b=G.hit(centre['point']),G.hit(selected['point']);envelope=G.envelope(centre['point'],selected['point'])
    check('old and selected sample positions each hit their own front chart/depth',centre['chart']in hit_a['charts'] and selected['chart']in hit_b['charts'] and abs(hit_a['depth']-centre['depth'])<=G.tolerance and abs(hit_b['depth']-selected['depth'])<=G.tolerance)
    cases=[];images=[]
    for scale in [8,16,32,64]:
        owner,depth=cell_raster(G,scale)
        picked,info=select(owner,scale,(.5,.5),pool,centre['chart'])
        cases.append({'scale':scale,'offset':[.5,.5],'selection':picked,'details':info})
        if scale in [8,16]:
            stored=np.load(R/f'coverage-v3/visibility-{scale}.npz')['chart'][29*scale:30*scale,7*scale:8*scale]
            check(f'saved {scale}x{scale} coverage reproduced exactly',np.array_equal(stored,owner))
        reverse,_=cell_raster(G,scale,reverse=True)
        check(f'{scale}x{scale} reversed triangle iteration selects same owner/packet',np.array_equal(owner,reverse) and select(reverse,scale,(.5,.5),pool[::-1],centre['chart'])[0]==picked)
        images.append((scale,owner))
    check('fixed-cell owner and representative packet agree at all four integration resolutions',all(v['selection']==selected for v in cases))
    # Integration offsets vary inside the same fixed pixel. This is numerical
    # sensitivity of an area estimate, NOT moving the camera/surface/pixel cell.
    offset_cases=[]
    for ox in [.25,.5,.75]:
        for oy in [.25,.5,.75]:
            owner,_=cell_raster(G,16,(ox,oy));p,info=select(owner,16,(ox,oy),pool,centre['chart'])
            offset_cases.append({'offset':[ox,oy],'chart':p['chart'],'g':p['g'],'Q':sum(p['g']>=t for t in THRESHOLDS),'packet':p,'coverageCounts':info['coverageCounts']})
    check('nine fixed-footprint 16x16 quadrature offsets retain selected packet',all(p['packet']==selected for p in offset_cases))
    # Representative order determinism without changing geometry or input values.
    orders=[];owner,_=cell_raster(G,16)
    for seed in range(8):
        shuffled=list(pool);np.random.default_rng(seed).shuffle(shuffled)
        p,_=select(owner,16,(.5,.5),shuffled,centre['chart']);orders.append(p==selected)
    check('eight shuffled packet orders do not change this selection',all(orders))
    row={'sourceId':source['sourceId'],'modelSHA256':source['modelSHA256'],'frozenFrameLabel':source['frame'],
         'sourceUTC':source['timestampUTC'],'oldCentre':centre,'coverageRepresentative':selected,
         'gAndQ':{'centre':[centre['g'],sum(centre['g']>=t for t in THRESHOLDS)],'selected':[selected['g'],sum(selected['g']>=t for t in THRESHOLDS)]},
         'frontAtOriginal':hit_a,'frontAtSelected':hit_b,'segmentGeometry':envelope,
         'geometryWasCapturedLater':True,'geometryReceipt':binding,'integrationCases':cases,'fixedFootprintOffsets':offset_cases,
         'interpretation':'Different representatives of different visible surfaces within the SAME frozen cell/pose. Not an observed temporal Q3-to-Q2 transition.',
         'limits':['later evaluated geometry matched to earlier frozen pose; not same live capture time','hair-only CPU visibility; face/body unseen surfaces not included','integration8/16/32/64 and9 offsets do not prove all camera/subpixel/animation stability','coverage-first art policy is not automatically the best feature-preservation policy']}
    dump('EVIDENCE.json',row);dump('VERIFIED.json',{'passed':len(checks),'checks':checks,'newUnityCalls':0,'newGpuReads':0,'productChanges':0})
    # Explain the actual surfaces and representative points, no recoloured final rendering.
    board=Image.new('RGB',(4*266,300),(25,29,36));draw=ImageDraw.Draw(board)
    colors={-1:(25,29,36),130013:(65,186,151),130027:(215,157,76),130030:(113,134,222)}
    for col,(scale,owner)in enumerate(images):
        arr=np.zeros((scale,scale,3),np.uint8)
        for chart in np.unique(owner):arr[owner==chart]=colors[int(chart)]
        board.paste(Image.fromarray(arr).resize((256,256),Image.Resampling.NEAREST),(col*266,35));draw.text((col*266+4,8),f'fixed cell (7,29), CPU {scale}x{scale}',fill='white')
        for p,color in [(centre,(255,255,255)),(selected,(255,60,100))]:
            xy=(np.array(p['point'])-[7,29])*256+[col*266,35];draw.ellipse((xy[0]-4,xy[1]-4,xy[0]+4,xy[1]+4),fill=color)
    board.save(O/'coverage-replay.png')
    print(json.dumps({'checks':len(checks),'sourceId':source['sourceId'],'coverage16':cases[1]['details']['coverageCounts'],
                      'coverage64':cases[-1]['details']['coverageCounts'],'geometry':envelope['category'],
                      'fixedFootprintSelections':list({(p['chart'],p['g'])for p in offset_cases}),
                      'sourceCentreQ':row['gAndQ']['centre'][1],'selectedQ':row['gAndQ']['selected'][1]}))


THRESHOLDS=load(R/'source-export/bundle/frame-source-data.json')['thresholds']
if __name__=='__main__':main()
