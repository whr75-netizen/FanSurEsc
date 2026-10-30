"""Offline shared-isoline candidate on the paired, unmodified source frame.

No Unity calls. Source material/UV identity is provenance, not a semantic strand.
Schneider-style fitting is in ../feature_curves.py; this is not Superpixelator.
"""
from pathlib import Path
import sys,json,base64,hashlib,math,time
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).parent.parent))
from feature_curves import fit,sample_curves,marching_paths,winding
R=Path(__file__).parent;B=R/'source-export/bundle';O=R/'candidate-v1'

def lab(rgb):
    rgb=np.asarray(rgb);lms=rgb@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
    return np.cbrt(lms)@np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])
def srgb(rgb):
    return np.uint8(np.clip(np.rint(np.where(rgb<=.0031308,12.92*rgb,1.055*np.maximum(rgb,0)**(1/2.4)-.055)*255),0,255))
def binary_components(mask,diagonal=False):
    h,w=mask.shape;labels=np.full((h,w),-1,int);groups=[];steps=[(1,0),(-1,0),(0,1),(0,-1)]+([(1,1),(1,-1),(-1,1),(-1,-1)] if diagonal else [])
    for y,x in np.argwhere(mask):
        if labels[y,x]>=0:continue
        q=[(int(x),int(y))];labels[y,x]=len(groups)
        for xx,yy in q:
            for dx,dy in steps:
                nx,ny=xx+dx,yy+dy
                if 0<=nx<w and 0<=ny<h and mask[ny,nx] and labels[ny,nx]<0:labels[ny,nx]=labels[y,x];q.append((nx,ny))
        groups.append(q)
    return labels,groups
def topology(k,mask):
    # Preserve labels' connected sets/holes/adjacencies, including separate islands.
    out={};adj=set();h,w=k.shape
    for value in np.unique(k[mask]):
        _,groups=binary_components(mask&(k==value));inv=np.pad(~(mask&(k==value)),1,constant_values=True);_,bg=binary_components(inv,True);holes=sum(not any(x in (0,w+1) or y in (0,h+1) for x,y in g) for g in bg)
        out[int(value)]=(len(groups),holes)
    for y,x in np.argwhere(mask):
        for dx,dy in [(1,0),(0,1)]:
            if y+dy<h and x+dx<w and mask[y+dy,x+dx] and k[y,x]!=k[y+dy,x+dx]:adj.add(tuple(sorted((int(k[y,x]),int(k[y+dy,x+dx])))))
    # Junction order anchored by its 2x2 labels, not just count of regions.
    junctions=[]
    for y in range(h-1):
        for x in range(w-1):
            a=[int(k[y,x]),int(k[y,x+1]),int(k[y+1,x+1]),int(k[y+1,x])]
            if mask[y:y+2,x:x+2].all() and len(set(a))>=3:junctions.append((x,y,tuple(a)))
    return out,adj,junctions
def same_components(before,after,mask):
    if topology(before,mask)!=topology(after,mask):return False
    for value in np.unique(before[mask]):
        a,aa=binary_components(mask&(before==value));b,bb=binary_components(mask&(after==value))
        for left,right in [(a,b),(b,a)]:
            for index in np.unique(left[left>=0]):
                overlap=set(right[left==index]);overlap.discard(-1)
                if len(overlap)!=1:return False
    return True
def normalised_edges(k,mask,level):
    rows=[];h,w=k.shape
    for y,x in np.argwhere(mask):
        for dx,dy in [(1,0),(0,1)]:
            if x+dx>=w or y+dy>=h or not mask[y+dy,x+dx] or ((k[y,x]>=level)==(k[y+dy,x+dx]>=level)):continue
            if dx:a=np.array([x+1,y]);b=a+[0,1]
            else:a=np.array([x,y+1]);b=a+[1,0]
            rows.append((a.astype(float),np.asarray(b,float)))
    return rows
def nearest(poly,points):
    a,b=poly[:-1],poly[1:];v=b-a;den=np.sum(v*v,axis=1);good=(den>1e-16)&np.isfinite(den);a=a[good];v=v[good];den=den[good]
    delta=points[:,None,:]-a[None,:,:];t=np.clip(np.sum(delta*v[None,:,:],axis=2)/den[None,:],0,1);err=delta-t[...,None]*v;d2=np.sum(err*err,axis=2);idx=np.argmin(d2,axis=1);return np.sqrt(d2[np.arange(len(points)),idx]),v[idx]/np.sqrt(den[idx,None])
def boundary_cost(k,mask,level,reference):
    e=normalised_edges(k,mask,level)
    if not e:return dict(distance=0,tangent=0,edges=0)
    points=np.array([(a+b)/2 for a,b in e]);d,t=nearest(reference,points);directions=np.array([b-a for a,b in e]);return dict(distance=float(np.mean(d*d)),tangent=float(np.mean(1-np.sum(directions*t,axis=1)**2)),edges=len(e))
def local_cost(k,mask,level,reference,cell):
    x,y=cell;e=[]
    for a,b in normalised_edges(k,mask,level):
        p=(a+b)/2
        if abs(p[0]-(x+.5))<=1 and abs(p[1]-(y+.5))<=1:e.append((a,b))
    if not e:return None
    p=np.array([(a+b)/2 for a,b in e]);d,t=nearest(reference,p);directions=np.array([b-a for a,b in e]);return dict(position=float(np.sum(d*d)),tangent=float(np.sum(1-np.sum(directions*t,axis=1)**2)),maxDistance=float(d.max()),edges=len(e))
def staircase_cost(k,mask,level,reference):
    edges=[(tuple(a.astype(int)),tuple(b.astype(int))) for a,b in normalised_edges(k,mask,level)];adj={}
    for i,(a,b) in enumerate(edges):adj.setdefault(a,[]).append(i);adj.setdefault(b,[]).append(i)
    used=set();errors=[]
    for start in sorted(adj,key=lambda p:(len(adj[p])==2,p)):
        for index in adj[start]:
            if index in used:continue
            p=[start];at=start;edge=index
            while edge not in used:
                used.add(edge);a,b=edges[edge];other=b if a==at else a;p.append(other)
                if other==start or len(adj[other])!=2:break
                remain=[i for i in adj[other] if i not in used]
                if not remain:break
                at=other;edge=remain[0]
            p=np.array(p,float);runs=[]
            for i,step in enumerate(np.diff(p,axis=0)):
                direction=tuple(step.astype(int))
                if runs and runs[-1][0]==direction:runs[-1][2]=p[i+1]
                else:runs.append([direction,p[i],p[i+1]])
            for left,right in zip(runs,runs[1:]):
                v=right[2]-left[1];mid=(right[2]+left[1])/2;dist,tangent=nearest(reference,np.array([mid]));length=np.linalg.norm(v)
                if length and dist[0]<=.8:errors.append(1-float(np.dot(v/length,tangent[0])**2))
    return {'count':len(errors),'mean':float(np.mean(errors)) if errors else 0.,'sum':float(np.sum(errors))}
def raster_candidate(k,mask,references,cuts,reverse=False):
    """One source-frozen pass of shared-boundary cell relocation.
    Both distance AND tangent error must improve; no arbitrary weighted art score.
    All interacting proposals are judged as one batch, never in-place scan updates.
    """
    h,w=k.shape;proposals=[];protected=set(v for e in cuts for v in e)
    cells=np.argwhere(mask)
    if reverse:cells=cells[::-1]
    for y,x in cells:
        if (int(x),int(y)) in protected:continue
        values={int(k[yy,xx]) for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] if 0<=xx<w and 0<=yy<h and mask[yy,xx]}
        options=[]
        for new in sorted(values):
            old=int(k[y,x]);level=max(old,new)
            if abs(old-new)!=1 or level not in references:continue
            trial=k.copy();trial[y,x]=new
            if not same_components(k,trial,mask):continue
            a=local_cost(k,mask,level,references[level],(x,y));b=local_cost(trial,mask,level,references[level],(x,y))
            if not a or not b or b['maxDistance']>.8:continue
            if b['position']<a['position']-1e-9 and b['tangent']<a['tangent']-1e-9:options.append({'cell':[int(x),int(y)],'before':old,'after':new,'level':level,'costBefore':a,'costAfter':b})
        if len(options)==1:proposals.append(options[0])
        # Ambiguous two-sided changes are not resolved by scan order or a hidden tie weight.
    proposalMask=np.zeros(mask.shape,bool)
    for p in proposals:proposalMask[p['cell'][1],p['cell'][0]]=True
    _,batches=binary_components(proposalMask,True);after=k.copy();records=[]
    for group in batches:
        entries=[p for p in proposals if tuple(p['cell']) in set(group)];trial=k.copy()
        for p in entries:trial[p['cell'][1],p['cell'][0]]=p['after']
        preserve=same_components(k,trial,mask);improves=True
        for p in entries:
            a=p['costBefore'];b=local_cost(trial,mask,p['level'],references[p['level']],p['cell'])
            improves&=bool(b and b['position']<a['position']-1e-9 and b['tangent']<a['tangent']-1e-9 and b['maxDistance']<=.8)
        spans={}
        for level in set(p['level'] for p in entries):
            aa=staircase_cost(k,mask,level,references[level]);bb=staircase_cost(trial,mask,level,references[level]);spans[str(level)]={'before':aa,'after':bb};improves&=bb['mean']<=aa['mean']+1e-9 and bb['sum']<=aa['sum']+1e-9
        accept=preserve and improves;records.append({'entries':entries,'topologyPreserved':preserve,'jointMetricsImprove':bool(improves),'staircaseMetrics':spans,'accepted':bool(accept)})
        if accept:
            for p in entries:after[p['cell'][1],p['cell'][0]]=p['after']
    if not same_components(k,after,mask):return k.copy(),records,'rejected whole batch: cross-batch topology interaction'
    for level,ref in references.items():
        aa=staircase_cost(k,mask,level,ref);bb=staircase_cost(after,mask,level,ref)
        if bb['mean']>aa['mean']+1e-9 or bb['sum']>aa['sum']+1e-9:return k.copy(),records,'rejected whole batch: combined staircase-tangent regression'
    return after,records,None
def split_fit(points,closed,tolerance):
    p=np.asarray(points);cuts={0,len(p)-1}
    if closed:
        for axis in range(2):cuts.add(int(np.argmin(p[:-1,axis])));cuts.add(int(np.argmax(p[:-1,axis])))
    # Raw marching isoline corners are physical input constraints, not grid staircase turns.
    for i in range(1,len(p)-1):
        a=p[i]-p[i-1];b=p[i+1]-p[i]
        if np.linalg.norm(a)*np.linalg.norm(b)>1e-12 and np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))<math.cos(math.radians(70)):cuts.add(i)
    pieces=[]
    for a,b in zip(sorted(cuts),sorted(cuts)[1:]):
        if b>a:pieces.extend(fit(p[a:b+1],tolerance))
    return pieces
def load():
    s=json.loads((B/'prelight-source.json').read_text());f=json.loads((B/'frame-source-data.json').read_text());assert s['sourceId']==f['sourceId'];h,w=s['height'],s['width'];mask=np.array([c is not None for c in s['cells']]).reshape(h,w);g=np.array([c['g'] if c else 0 for c in s['cells']]).reshape(h,w);rgb=np.array([c['baseRGBAlinear'][:3] if c else [0,0,0] for c in s['cells']]).reshape(h,w,3);normal=np.array([c['normalWS'] if c else [0,0,0] for c in s['cells']]).reshape(h,w,3);depth=np.array([c['depthHeadCamera'] if c else 0 for c in s['cells']]).reshape(h,w);return s,f,mask,g,rgb,normal,depth
def domains(s,f,mask,rgb,normal,depth):
    h,w=mask.shape;cap=json.loads((R/'source-export/CAPTURE.json').read_text());view=np.array(cap['view']).reshape(4,4,order='F')[:3,:3];n=normal@view.T;pitch=f['regionGeometry']['worldPixel'];l=lab(rgb);cuts={};colourcuts={};provenance=np.full(mask.shape,-1,int);top=np.load(R/'SOURCE_TOPOLOGY.npz')
    for i,c in enumerate(s['cells']):
        if c:provenance.flat[i]=c['materialId']*10000+int(top['welded'+str(c['materialId'])][c['primitiveId']])
    for y,x in np.argwhere(mask):
        for dx,dy in [(1,0),(0,1)]:
            xx,yy=x+dx,y+dy
            if xx>=w or yy>=h or not mask[yy,xx]:continue
            a=n[y,x];b=n[yy,xx];key=tuple(sorted(((int(x),int(y)),(int(xx),int(yy)))));actual=(depth[yy,xx]-depth[y,x])/pitch;pred=[]
            for v in [a,b]:
                if abs(v[2])>.15:pred.append((v[0]*dx-v[1]*dy)/v[2])
            residual=abs(actual-np.mean(pred)) if len(pred)==2 else None;angle=float(np.degrees(np.arccos(np.clip(np.dot(a,b),-1,1))))
            # A source piece alone is never a feature cut. Require measured depth disagreement.
            if provenance[y,x]!=provenance[yy,xx] and residual is not None and residual>1:cuts[key]={'reason':'disconnected source surface and >1 logical-pixel tangent-plane depth residual','residualPixels':float(residual),'angleDegrees':angle}
            de=float(np.linalg.norm(l[y,x]-l[yy,xx]))
            if de>.06:colourcuts[key]={'reason':'strong actual unlit-source colour contrast (candidate threshold, not semantic truth)','deltaOK':de}
    def build(blocked):
        ids=np.full(mask.shape,-1,int);groups=[]
        for y,x in np.argwhere(mask):
            if ids[y,x]>=0:continue
            q=[(int(x),int(y))];ids[y,x]=len(groups)
            for xx,yy in q:
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx,ny=xx+dx,yy+dy;key=tuple(sorted(((xx,yy),(nx,ny))))
                    if 0<=nx<w and 0<=ny<h and mask[ny,nx] and ids[ny,nx]<0 and key not in blocked:ids[ny,nx]=ids[y,x];q.append((nx,ny))
            groups.append(q)
        return ids,groups
    feature,groups=build(cuts);colour,cgroups=build(set(cuts)|set(colourcuts));return feature,colour,provenance,cuts,colourcuts,groups,cgroups
def run():
    O.mkdir(exist_ok=True);s,f,mask,g,rgb,normal,depth=load();h,w=mask.shape;tau=np.array(f['thresholds']);k=np.sum(g[...,None]>=tau,axis=-1).astype(int);k[~mask]=-1;feature,colour,provenance,cuts,colourcuts,groups,cgroups=domains(s,f,mask,rgb,normal,depth);after=k.copy();rows=[];all_paths=[];centres=np.array([(x+.5,y+.5) for y in range(h) for x in range(w)]);start=time.perf_counter()
    references={};rawReferences={}
    for level,threshold in enumerate(tau,1):
        # Colour is an independent, immutable layer. A shade isoline may cross it;
        # doing so does not reassign or average the cell's original pigment.
        paths=marching_paths(g,mask,np.zeros_like(feature),threshold,set(cuts),spacing=1,origin=(.5,.5));levelpoly=[]
        fittedPaths=[]
        if paths:rawReferences[level]=np.concatenate([np.vstack([v['points'],[np.nan,np.nan]]) for v in paths if len(v['points'])>1])
        for j,path in enumerate(paths):
            p=path['points'];curves=split_fit(p,path['closed'],.30);q=sample_curves(curves)
            if len(p)<3 or len(q)<2:fittedPaths.append(p);continue
            fittedPaths.append(q)
            delta=winding(q,centres)-winding(p,centres);ys,xs=np.divmod(np.flatnonzero(delta),w);changed=[];trial=after.copy()
            # The signed area strip must agree with the raw field's side of the curve.
            for y,x in zip(ys,xs):
                if not mask[y,x] or abs(k[y,x]-(level-.5))>.5:continue
                new=level if k[y,x]==level-1 else level-1;trial[y,x]=new;changed.append((int(x),int(y)))
            all_paths.append({'id':f'{level}:{j}','level':level,'threshold':float(threshold),'closed':path['closed'],'reference':p.tolist(),'fitted':q.tolist(),'cubics':[c.tolist() for c in curves],'proposedCells':changed})
            if not changed:continue
            # Compare both representations on this reference chain and all other level paths.
            # Keep unrelated open paths separated: no fictitious connecting chord.
            ref=np.concatenate([np.vstack([v['points'],[np.nan,np.nan]]) for v in paths if len(v['points'])>1])
            beforecost=boundary_cost(after,mask,level,ref);aftercost=boundary_cost(trial,mask,level,ref);preserve=same_components(k,trial,mask)
            improves=aftercost['distance']<beforecost['distance']-1e-10 and aftercost['tangent']<=beforecost['tangent']+1e-10
            accepted=preserve and improves
            rows.append({'path':f'{level}:{j}','cells':changed,'beforeCost':beforecost,'afterCost':aftercost,'topologyPreserved':preserve,'accepted':accepted})
            if accepted:after=trial
        if fittedPaths:references[level]=np.concatenate([np.vstack([p,[np.nan,np.nan]]) for p in fittedPaths])
    # Curve-strip rasterization is diagnostic. Select the source-frozen grid relocation
    # only when it improves both independently measured reference terms.
    stripAfter=after.copy();after,rasterRows,batchError=raster_candidate(k,mask,references,cuts)
    elapsed=(time.perf_counter()-start)*1000
    changed=[]
    for y,x in np.argwhere(k!=after):changed.append({'x':int(x),'y':int(y),'logicalX':int(x+f['logicalX']),'logicalYTop':int(y+f['logicalYTop']),'before':int(k[y,x]),'after':int(after[y,x]),'g':float(g[y,x]),'material':s['cells'][y*w+x]['materialId'],'primitive':s['cells'][y*w+x]['primitiveId'],'feature':int(feature[y,x]),'colourRegion':int(colour[y,x])})
    costs={str(level):{'rawBefore':boundary_cost(k,mask,level,rawReferences[level]),'rawAfter':boundary_cost(after,mask,level,rawReferences[level]),'fittedBefore':boundary_cost(k,mask,level,ref),'fittedAfter':boundary_cost(after,mask,level,ref)} for level,ref in references.items()}
    result={'sourceId':s['sourceId'],'maskCells':int(mask.sum()),'featureComponents':len(groups),'colourComponents':len(cgroups),'sourceGeometryPieces':len(np.unique(provenance[mask])),'geometricCutEdges':len(cuts),'sourceColourCutEdges':len(colourcuts),'featureThresholds':{'depthPlaneResidualWorldPixel':1,'sourceColourDeltaOK':.06,'normalNzForPlane':.15,'curveToleranceLogicalPixel':.30,'inputCurveCornerAngle':70},'paths':len(all_paths),'curveStripProposals':rows,'rasterBatches':rasterRows,'batchError':batchError,'changed':changed,'boundaryCosts':costs,'topologyPreserved':same_components(k,after,mask),'offlineTimeMilliseconds':elapsed,'notClaimed':['semantic artistic-strand recognition','full Superpixelator','temporal stability','art completion','production integration']}
    (O/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'CURVES.json').write_text(json.dumps(all_paths));(O/'FEATURE_EDGES.json').write_text(json.dumps({'geometry':[{'a':a,'b':b,**v} for (a,b),v in cuts.items()],'sourceColour':[{'a':a,'b':b,**v} for (a,b),v in colourcuts.items()]},indent=2));np.savez_compressed(O/'maps.npz',mask=mask,g=g,k=k,after=after,feature=feature,colour=colour,sourceGeometryPiece=provenance,rgb=rgb,normal=normal,depth=depth)
    # A 34-compatible *separate input*; never attach this map to its old frame/sourceId.
    export={'kind':'shared-boundary-candidate','sourceId':s['sourceId'],'width':w,'height':h,'cell':2,'origin':'top-left','logicalX':f['logicalX'],'logicalYTop':f['logicalYTop'],'labelsBefore':(k+1).reshape(-1).tolist(),'labelsAfter':(after+1).reshape(-1).tolist(),'featureDomains':(feature+1).reshape(-1).tolist(),'sourceColourRegions':(colour+1).reshape(-1).tolist(),'sharedCurves':'CURVES.json','sourceFrame':'../source-export/bundle/frame-source-data.json'};(O/'LAYERS.json').write_text(json.dumps(export))
    render(s,f,mask,g,rgb,normal,depth,k,after,feature,colour,cuts,colourcuts)
    print(json.dumps(result,ensure_ascii=False))
def render(s,f,mask,g,rgb,normal,depth,k,after,feature,colour,cuts,colourcuts):
    h,w=mask.shape;orig=np.frombuffer(base64.b64decode(f['originalRGBA']),np.uint8).reshape(h*2,w*2,4).copy();pal=np.array([[7,2,3],[20,8,9],[34,18,19],[50,28,29]],np.uint8)
    def layer(a,name):
        if a.ndim==2:
            rgba=np.zeros((h,w,4),np.uint8);ids=np.maximum(a,0);rgba[...,:3]=np.stack([(ids*67+73)%196+35,(ids*101+41)%196+35,(ids*37+107)%196+35],axis=-1);rgba[...,3]=mask*255
        else:rgba=a
        im=Image.fromarray(np.uint8(rgba)).resize((w*2,h*2),Image.Resampling.NEAREST);im.save(O/(name+'.png'));return im
    layers=[('original-final',Image.fromarray(orig))];rgba=np.dstack([srgb(rgb),mask*255]).astype(np.uint8);layers.append(('source-unlit',layer(rgba,'source-unlit')))
    layers.append(('source-geometry-pieces',layer(np.load(O/'maps.npz')['sourceGeometryPiece'],'source-geometry-pieces')));layers.append(('geometry-domains',layer(feature,'geometry-domains')));layers.append(('source-colour-regions',layer(colour,'source-colour-regions')))
    rgba=np.dstack([np.uint8(np.clip((normal*.5+.5)*255,0,255)),mask*255]);layers.append(('normal',layer(rgba,'normal')))
    for name,labels in [('shade-before',k),('shade-after',after)]:
        rgba=np.dstack([pal[np.maximum(labels,0)],mask*255]).astype(np.uint8);im=layer(rgba,name);composite=orig.copy();mm=np.repeat(np.repeat(mask,2,0),2,1);composite[mm]=np.asarray(im)[mm];Image.fromarray(composite).save(O/(name+'-composite.png'));layers.append((name,Image.fromarray(composite)))
    scale=5;cols=4;tilew=350;tileh=440;sheet=Image.new('RGB',(cols*tilew,2*tileh),(34,37,44));d=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(layers):
        x=(i%cols)*tilew;y=(i//cols)*tileh;d.text((x+10,y+7),name,fill='white');sheet.paste(im.resize((w*2*scale,h*2*scale),Image.Resampling.NEAREST),(x+10,y+28),im.resize((w*2*scale,h*2*scale),Image.Resampling.NEAREST))
    sheet.save(O/'layers.png');Image.fromarray(orig).save(O/'original-final.png')
if __name__=='__main__':run()
