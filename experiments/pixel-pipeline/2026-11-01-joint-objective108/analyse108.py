"""Recalculate all frozen states, with separate policy outputs and no Unity."""
from pathlib import Path
import json,sys,time,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from joint108 import solve,problem,tests,EPS

H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import buffer,components,font
sys.path.insert(0,str(R/'live-curve106'));from curve_reference106 import distance

def json_out(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def map_labels(d,owner,result,which):
    a=np.zeros(d['support'].shape[1:],int)
    if which not in result:return a
    for (y,x),p in zip(result['points'],result[which]['labels']):a[y,x]=p
    return a

def curve_metrics(d,owner,a):
    ss=d['sourceSegments'][d['sourceSegments'][:,0,3]==owner];pix=np.argwhere(a==3);segments=[(q[0,:2].astype(float),q[1,:2].astype(float))for q in ss]
    if not segments or not len(pix):return {'selectedLidCells':len(pix),'sourceToSelectedCellMax':None,'selectedCentreToReferenceMax':None}
    # Sample every source polyline segment with fixed integration resolution;
    # these are diagnostic distances to the registered reference, not art truth.
    probes=np.concatenate([a[None]+np.linspace(0,1,33)[:,None]*(b-a)[None]for a,b in segments])
    boxes=pix[:,::-1].astype(float);delta=np.maximum(0,np.maximum(boxes[None]-probes[:,None],probes[:,None]-(boxes[None]+1)))
    dist=np.sqrt((delta*delta).sum(2)).min(1)
    centres=boxes+.5;back=[min(distance(q,a,b)for a,b in segments)for q in centres]
    return {'selectedLidCells':len(pix),'sourceToSelectedCellMax':float(dist.max()),'sourceToSelectedCellMean':float(dist.mean()),'selectedCentreToReferenceMax':float(max(back)),
            'referenceIsValidatedPigmentContour':False,'components4':components(a==3)}

def audit(d,owner,q,carrier=False):
    if q['status']!='exact-optima-under-stated-policy':return q
    p=problem(d,owner,False,False,carrier);ids=[0]+[i for i,k in enumerate(d['keys'])if k[0]==owner]
    for name in ['massFirst','dataFirst']:
        a=map_labels(d,owner,q,name);v=q[name]
        assert all(label in domain for label,domain in zip(v['labels'],p['domains']))
        assert all(k in v['labels']for k in range(1,4)if p['required']>>(k-1)&1)
        v['curveMetrics']=curve_metrics(d,owner,a)
        v['components4']={str(k):components(a==k)for k in [1,2,3]}
        v['sourceMassAtSelectedCells']=[float(d['lower'][ids[k]][a==k].sum())for k in range(1,4)]
        v['outsideSameCellCertainSupport']=int(sum(((a==k)&~d['support'][ids[k]]).sum()for k in range(1,4)))
    return q

def source_allocation(d,filename):
    p=Path(filename);a=buffer(p).reshape(*d['support'].shape[1:],4);out=np.zeros(a.shape[:2],int)
    for key,(owner,part)in enumerate(d['keys']):
        if key:out[(np.rint(a[...,0])==part)&(np.rint(a[...,1])==owner)]=key
    return out

def previous_metrics(d,labels):
    result=[]
    for owner in [1,2]:
        ids=[i for i,k in enumerate(d['keys'])if k[0]==owner];local=np.where(np.isin(labels,ids),labels,0);counts=[int((local==k).sum())for k in ids];lo=d['lower'][ids].sum((1,2));hi=d['upper'][ids].sum((1,2))
        bad=int(sum(((local==k)&~d['support'][k]).sum()for k in ids))
        result.append({'owner':owner,'counts':counts,'massError':float(sum(max(0,l-n,n-h)for n,l,h in zip(counts,lo,hi))),
          'unsupportedLabelCells':bad,'lostVisibleParts':[int(d['keys'][k,1])for k,n in zip(ids,counts)if n==0 and d['support'][k].any()]})
    return result

def render_board(rows,results,names,filename,title):
    colours=['#202a35','#395ee8','#e9edf6','#d78745','#7148d4','#d6e6dc','#e35e56']
    columns=['saved GPU RGB','saved labels','mass, no curve','data, no curve','mass + arc4','mass + arc8'];cellw=202;rowh=200
    board=Image.new('RGB',(40+len(columns)*cellw,100+len(names)*rowh),'#111923');dr=ImageDraw.Draw(board);dr.text((18,12),title,font=font(19),fill='white')
    dr.text((18,40),'RGB column = saved GPU107 / 105. Other columns = label diagnostics only, NOT final RGB/palette.',font=font(14),fill='#ffce78')
    for j,col in enumerate(columns):dr.text((20+j*cellw,70),col,font=font(15),fill='white')
    for ri,name in enumerate(names):
        row=next(x for x in rows if x['name']==name);d=np.load(H/'fixtures'/(name+'.npz'));h,w=d['support'].shape[1:];rec=results[name];old=source_allocation(d,Path(row['sourcePacket'])/'curve-identity.f32')if name.startswith('actual107')else source_allocation(d,Path(row['sourcePacket'])/'canonical-identity.f32')
        maps=[old]
        for policy,objective in [('noCurve','massFirst'),('noCurve','dataFirst'),('arc4','massFirst'),('arc8','massFirst')]:
            a=np.zeros((h,w),int)
            for owner in [1,2]:
                q=rec[policy][str(owner)]
                if objective in q:
                    for (y,x),v in zip(q['points'],q[objective]['labels']):
                        if v:a[y,x]=(owner-1)*3+v
            maps.append(a)
        y=100+ri*rowh;label=name.replace('actual107-frame','F').replace('closed105-frame','105F')
        rgbfile=Path(row['sourcePacket'])/('curve-colour.f32'if name.startswith('actual107')else'canonical-colour.f32')
        rgb=buffer(rgbfile).reshape(h,w,4)[...,:3];rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.maximum(rgb,0)**(1/2.4)-.055);rgb=Image.fromarray(np.clip(np.rint(rgb*255),0,255).astype('uint8'))
        images=[rgb]+[Image.fromarray(np.array([[tuple(int(colours[k][t:t+2],16)for t in [1,3,5])for k in line]for line in a],np.uint8))for a in maps]
        for j,im in enumerate(images):
            scale=min(9,170//h,180//w);im=im.resize((w*scale,h*scale),Image.Resampling.NEAREST);x=20+j*cellw
            board.paste(im,(x,y+27));dr.text((x,y),label,font=font(14),fill='white')
            if j>1:
                pol='noCurve'if j<4 else'arc4'if j==4 else'arc8';obj='dataFirst'if j==3 else'massFirst';qq=rec[pol]
                err=sum(v[obj]['mass']for v in qq.values()if obj in v);missing=[o for o,v in qq.items()if obj not in v and v['status']!='no-visible-pigment']
                dr.text((x,y+160),f'mass L1={err:.3f}'+(' / INFEASIBLE eye'+','.join(missing)if missing else''),font=font(12),fill='#ffbf72'if missing else'#a8cddf')
    board.save(H/filename)

def main():
    started=time.perf_counter();rows=json.loads((H/'INPUT108.json').read_text());results={};statuses={};outside=0;flow=0
    for i,row in enumerate(rows):
        d=np.load(H/'fixtures'/(row['name']+'.npz'));assert not np.any(d['support'][1:4].any(0)&d['support'][4:7].any(0))
        rec={}
        for policy,curve,diag,carrier in [('noCurve',False,False,False),('arc4',True,False,False),('arc8',True,True,False),('relaxedCarrier4',True,False,True)]:
            rec[policy]={str(o):audit(d,o,solve(d,o,curve,diag,carrier),carrier)for o in [1,2]}
            for o,q in rec[policy].items():
                statuses[policy+':'+q['status']]=statuses.get(policy+':'+q['status'],0)+1;flow+=q.get('flowSubproblems',0)
        p=Path(row['sourcePacket']);rec['previous']=previous_metrics(d,source_allocation(d,p/('curve-identity.f32'if row['name'].startswith('actual107')else'canonical-identity.f32')))
        results[row['name']]=rec
        if i%10==0:print(json.dumps({'done':i+1,'of':len(rows),'seconds':time.perf_counter()-started}),flush=True)
    json_out(H/'RESULTS108.json',results)
    report={'fixtures':len(rows),'actual107States':54,'independent105ClosedState':1,'notAContinuousSequence':True,'newPlay':0,'newGPU':0,'productChanged':False,'candidateAccepted':False,
       'statusCounts':statuses,'flowSubproblems':flow,'seconds':time.perf_counter()-started,'tests':tests(),'completeParetoFrontier':False,
       'modelDoesNotContain':['authored full-eye shape/readability objective','validated native pigment contour','temporal surface tracking','finite lid palette/AA colour policy'],
       'ownerSeparableBecauseNoSharedCandidateCells':True,'hardPresenceIsFeaturePolicyNotUniversalSemanticTruth':True}
    json_out(H/'SUMMARY108.json',report)
    names=['actual107-frame99','actual107-frame101','actual107-frame103','actual107-frame107','actual107-frame115','actual107-frame192','closed105-frame104']
    render_board(rows,results,names,'JOINT_MODEL108.png','108: source mass and curve reachability are separate, conflicting policies')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
