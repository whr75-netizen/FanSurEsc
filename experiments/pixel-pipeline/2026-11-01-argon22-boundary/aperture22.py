"""Argon2.2 boundary hypothesis, explicit canonical-grid domain.

The actual positive-alpha native pigment curve is the reference, not skin-ring.
Each intersected column gets floor(arc-length mean y within that column).
This makes the document's 'centre' operational and records the choice. It is
NOT asserted to be an anatomical aperture boundary or a universally 8-connected
raster. Those claims are tested by the caller. Source visibility/alpha/depth
remain separate from drawing a whole cell. No RGB, mass quota or glyph size.
"""
import math,numpy as np

def column_rows(points,visible=None):
    q=np.asarray(points,float);visible=np.ones(len(q),bool)if visible is None else np.asarray(visible,bool);acc={};counts={}
    for i,(a,b)in enumerate(zip(q,q[1:])):
        if not(visible[i]and visible[i+1]):continue
        delta=b-a;length=float(np.linalg.norm(delta))
        if length==0:continue
        if delta[0]==0:
            x=math.floor(a[0]);acc.setdefault(x,[0.,0.]);acc[x][0]+=length*(a[1]+b[1])*.5;acc[x][1]+=length;counts[x]=counts.get(x,0)+1;continue
        for x in range(math.floor(min(a[0],b[0])),math.floor(max(a[0],b[0]))+1):
            t0=(x-a[0])/delta[0];t1=(x+1-a[0])/delta[0];lo=max(0,min(t0,t1));hi=min(1,max(t0,t1))
            if hi<=lo:continue
            y0=a[1]+delta[1]*lo;y1=a[1]+delta[1]*hi;weight=length*(hi-lo);acc.setdefault(x,[0.,0.]);acc[x][0]+=weight*(y0+y1)*.5;acc[x][1]+=weight;counts[x]=counts.get(x,0)+1
    rows={x:math.floor(v[0]/v[1])for x,v in acc.items()};means={x:v[0]/v[1]for x,v in acc.items()};dx=np.diff(q[:,0]);nonzero=dx[dx!=0];monotone=not len(nonzero)or np.all(nonzero>0)or np.all(nonzero<0)
    jumps=[{'columns':[a,b],'rows':[rows[a],rows[b]]}for a,b in zip(sorted(rows),sorted(rows)[1:])if b==a+1 and abs(rows[b]-rows[a])>1]
    return rows,{'definition':'floor(arc-length mean y of visible curve clipped to each canonical column)','columnMeans':means,'xMonotone':bool(monotone),'adjacentColumnJumpsOverOne':jumps,'onePerColumnDoesNotProveConnectivity':True}

def classify(lowI,highI,lowW,highW,rows,carrier,closeSourceEmpty=False):
    """Boundary partition + existing102 foreground-half policy below it.
    Exact child ties/visibility intervals remain explicit, not array order.
    carrier is current face/Close only; external hair never changes shape.
    """
    h,w=lowI.shape;labels=np.zeros((h,w),np.int8);reason={};tie=[];missing=[];suppressed=[]
    for y in range(h):
        for x in range(w):
            row=rows.get(x);iL,iU,wL,wU=map(float,[lowI[y,x],highI[y,x],lowW[y,x],highW[y,x]])
            if row is not None and y<row:
                if iU+wU>0:suppressed.append({'cellYX':[y,x],'sourceIrisWhiteMass':[iL,wL],'reason':'above proposed pigment boundary, not a proof of physical skin'})
                continue
            if row is not None and y==row:
                if carrier[y,x]:labels[y,x]=3
                else:labels[y,x]=-1;missing.append([y,x])
                continue
            if closeSourceEmpty:continue
            lo=iL+wL;hi=iU+wU
            if hi<.5:continue
            exact=iL==iU and wL==wU
            if not(lo>.5 or exact and lo==.5):labels[y,x]=-1;reason[(y,x)]='uncertain foreground/canvas';continue
            if iL>wU:labels[y,x]=1
            elif wL>iU:labels[y,x]=2
            elif exact and iL==wL and iL>0:labels[y,x]=-1;tie.append([y,x])
            else:labels[y,x]=-1;reason[(y,x)]='uncertain child partition'
    return labels,{'childExactTies':tie,'uncertainCells':[{'cellYX':list(k),'reason':v}for k,v in reason.items()],'boundaryCellsWithoutCertainCurrentCarrier':missing,'positiveSourceSuppressedAboveProposedBoundary':suppressed,
      'boundaryRowsOutsideCapturedROI':[[x,y]for x,y in rows.items()if not(0<=x<w and 0<=y<h)],'foregroundHalfPolicyFrom102':True,'fixedPartCount':False,'externalHairInShape':False,'canonicalGridOnly':True,'strictBoundaryProseRuleNotOutsideEyeExceptionEquation':True}

def component_count(mask,diagonal=True):
    s={tuple(map(int,v))for v in np.argwhere(mask)};result=[]
    while s:
        todo=[s.pop()];n=0
        while todo:
            y,x=todo.pop();n+=1
            for p in list(s):
                if (max(abs(p[0]-y),abs(p[1]-x))==1 if diagonal else abs(p[0]-y)+abs(p[1]-x)==1):s.remove(p);todo.append(p)
        result.append(n)
    return result

def domain_counterexamples():
    # Literal x-column rule, NOT a silent y-dominant replacement.
    source=np.array([[.2,.2],[5.8,1.8]]);a,_=column_rows(source);rot=source@np.array([[0,1],[-1,0]]).T;b,_=column_rows(rot)
    # Rotate each source square by the same D4 map for a fair grid comparison.
    expected={(-y-1,x)for x,y in a.items()};got={(x,y)for x,y in b.items()}
    steep=np.array([[.2,.2],[2.8,7.8]]);_,info=column_rows(steep)
    return {'literalScreenXRuleRotationCovariant':expected==got,'unrotatedCells':len(a),'rotatedCells':len(b),'steepCurveColumnJumps':info['adjacentColumnJumpsOverOne'],
       'validImplementationRequiresRegisteredFeatureFrameAndCurveRasterContract':True,'notClaimedUniversalSolution':True}
