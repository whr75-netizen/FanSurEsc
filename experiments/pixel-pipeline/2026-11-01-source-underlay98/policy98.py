"""Explicit offline design alternatives, using saved current visibility/RGBA.

No new geometric visibility inference. Baseline composition must exactly reproduce
all four actual GPU output fields before alternatives may be shown.
"""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import rgb8
from input98 import packet
from analyse_capture68 import camera
sys.path.insert(0,str(ROOT/'live-joint96'));from validate96 import read
F=np.float32

def inputs(d):
    m=d['m'];cw,ch=np.asarray(m['retarget89']['size'])//4
    ids=read(d['path']/'live96-identity.buffer').reshape(ch,cw,4).copy();colour=read(d['path']/'live96-colour.buffer').reshape(ch,cw,4).copy();decision=read(d['path']/'live96-decision.buffer').reshape(ch,cw,4).copy();vis=read(d['path']/'live96-visibility.buffer').reshape(4,ch*4,cw*4,4);layers=[[np.flipud(d['a'][f'retarget-part{p}-{k}'])for k in range(5)]for p in range(4)]
    return ids,colour,decision,vis,layers

def compose(d,ids,colours,dec,vis,layers):
    a=d['a'];m=d['m'];base=a['native-final-rgba'];own=a['native-final-owner'].copy();out=base.copy();depth=a['native-final-depth'].copy();h,w=out.shape[:2];ch,cw=ids.shape[:2];ref=m['nativeFinalReference89'];yy,xx=np.mgrid[:h,:w];absolute=np.stack([xx+ref['nativeROI'][0],yy+ref['nativeROI'][1]],-1).astype('f4');origin=np.asarray(ref['origin'],'f4');join=np.asarray(m['trace86']['headJoinOffset'],'f4')+np.asarray(m['camera86']['deliveredDelta'][:2],'f4');bottom=(absolute+F(.5)-origin)/F(ref['scale'])-join;top=bottom.copy();top[...,1]=F(272)-bottom[...,1];anchor=np.asarray(m['retarget89']['anchor'],'f4')+np.asarray(m['retarget89']['bounds'][:2],'f4');local=top-anchor;cell=np.floor(local).astype(int);cx,cy=cell[...,0],cell[...,1];inside=(cx>=0)&(cy>=0)&(cx<cw)&(cy<ch);kx=np.clip(cx,0,cw-1);ky=np.clip(cy,0,ch-1);selected=ids[ky,kx];newer=inside&(selected[...,0]>0);offset=F(camera(d['path']/'source.camera')['view'][2,3]-camera(d['path']/'main.camera')['view'][2,3]);z=selected[...,2]+offset
    hx,hy=np.floor(bottom).astype(int).transpose(2,0,1);rx,ry,rw,rh=d['roi'];inhead=(hx>=rx)&(hy>=ry)&(hx<rx+rw)&(hy<ry+rh);old=a['old-eye-owner'][np.clip(hy-ry,0,rh-1),np.clip(hx-rx,0,rw-1)];intr=a['old-intrinsic'][np.clip(hy-ry,0,rh-1),np.clip(hx-rx,0,rw-1)];oldFeature=inhead&(((np.rint(old[...,0])==2)&(intr[...,0]>0))|(np.rint(old[...,0])==7))
    ex,ey,ew,eh=d['eyeROI'];rp=(hx>=ex)&(hy>=ey)&(hx<ex+ew)&(hy<ey+eh);r=d['records'][np.clip(hy-ey,0,eh-1),np.clip(hx-ex,0,ew-1)];protected=rp&(np.rint(r[...,3,0])==5)&((r[...,14,2]>F(.5))|(r[...,14,3]==77))
    foreignRole=(np.rint(own[...,0])==6)|((np.rint(own[...,0])>=8)&(np.rint(own[...,0])<=15));foreign=newer&((foreignRole&(own[...,2]>0)&(own[...,2]<z-F(3e-5)))|(z>depth[...,0]+F(.0001)));bad=inside&(dec[ky,kx,0]<0)&(oldFeature|newer)
    for y,x in np.argwhere(bad&foreignRole&(depth[...,3]>0)&(own[...,2]>0)):
        sy,sx=ky[y,x]*4,kx[y,x]*4;potential=vis[1:,sy:sy+4,sx:sx+4,1]>0;zz=vis[1:,sy:sy+4,sx:sx+4,2]+offset;closest=zz[potential].min(initial=np.finfo('f4').max)
        if own[y,x,2]<closest-F(3e-5):bad[y,x]=False;foreign[y,x]=True
    audit=np.zeros_like(out);paint=newer&~foreign&~protected&~bad;out[paint]=colours[ky[paint],kx[paint]];own[paint]=np.stack([selected[...,0]+1,selected[...,1],z,selected[...,3]],-1)[paint];depth[paint]=np.stack([depth[...,0],z,np.ones_like(z),np.ones_like(z)],-1)[paint];audit[paint,0]=1
    roi=m['currentSources91']['roiTopLeft'];skin=a['current91-g2-0'];sm=a['current91-g2-1'];su=a['current91-g2-3'];nc=a['current-non-eye98-0'];nm=a['current-non-eye98-1'];nu=a['current-non-eye98-2'];vacated=oldFeature&~newer&~protected&~foreign&~bad
    for y,x in np.argwhere(vacated):
        p=np.floor((bottom[y,x]-np.asarray([roi[0],272-roi[1]-roi[3]],'f4'))*F(2)).astype(int);px,py=p;physical=0<=px<skin.shape[1]and 0<=py<skin.shape[0];valid=False;uncertain=False;kind=2;bc=bm=None;primitive=F(0)
        if physical:
            bc=skin[py,px];bm=sm[py,px];valid=bm[0]>0 and round(float(bm[1]))==4 and bc[3]==1
            if valid:primitive=su[py,px,2]
        if not valid and inside[y,x]:
            tx,ty=np.floor(local[y,x]*F(4)).astype(int)
            if 0<=tx<vis.shape[2]and 0<=ty<vis.shape[1]and vis[0,ty,tx,0]>=1:
                bc=layers[0][0][ty,tx];bm=layers[0][1][ty,tx];valid=bc[3]==1 and round(float(bm[1]))==4
                if valid:primitive=layers[0][3][ty,tx,2];kind=3
        if not valid and physical:
            cc=nc[py,px];mm=nm[py,px];uv=nu[py,px];role=round(float(mm[1]))
            if mm[0]>0:
                valid=role>0 and role not in [2,3,5,7]and cc[3]==1 and mm[3]==1 and uv[2]>0 and uv[3]>=1
                if valid:bc=cc;bm=mm;primitive=uv[2];kind=4
                else:uncertain=True
        if valid:
            zz=F(bm[0]+offset)
            if foreignRole[y,x]and own[y,x,2]>0 and own[y,x,2]<zz-F(3e-5):foreign[y,x]=True
            elif zz>depth[y,x,0]+F(.0001):bad[y,x]=True
            else:out[y,x]=bc;own[y,x]=[bm[1],bm[2],zz,primitive];depth[y,x]=[depth[y,x,0],zz,1,1];audit[y,x,0]=kind
        elif not uncertain and physical:
            proof=a['actual-world98-1'][y,x]
            if proof[3]>0:out[y,x]=a['actual-world98-0'][y,x];own[y,x]=0;depth[y,x]=[proof[3],0,0,0];audit[y,x,0]=5
            else:bad[y,x]=True
        else:bad[y,x]=True
    audit[...,1]=np.where(inside,selected[...,0],0);audit[...,2]=protected;audit[...,3]=foreign;audit[bad,0]=-1
    return [out,own,depth,audit]

def choose(d,policy):
    ids,c,dec,vis,layers=inputs(d);events=[]
    for y,x in np.argwhere(dec[...,0]<0):
        mass=np.zeros(4,'f4');upper=np.zeros(4,'f4');weights=np.zeros((3,16),'f4')
        for sy in range(4):
            for sx in range(4):
                yy,xx=y*4+sy,x*4+sx;lo=vis[1:,yy,xx,0];hi=vis[1:,yy,xx,1];z=np.array([vis[p,yy,xx,2]if layers[p][1][yy,xx,0]>0 else np.finfo('f4').max for p in [1,2,3]]);tl=th=F(1)
                for p in np.argsort(z,kind='stable'):
                    weights[p,sy*4+sx]=F(tl*lo[p]);mass[p]=F(mass[p]+F(tl*lo[p]));upper[p]=F(upper[p]+F(th*hi[p]));tl=F(tl*F(1-hi[p]));th=F(th*F(1-lo[p]))
                mass[3]=F(mass[3]+tl);upper[3]=F(upper[3]+th)
        maxlo=mass.max();possible=[p for p in range(4)if upper[p]>0 and upper[p]>=maxlo-F(1e-7)];exact=all(mass[p]==upper[p]for p in possible)
        if not exact or len(possible)<2:continue
        # These are explicit design alternatives, not a default correctness rule.
        priority=[0,1,2,3]if policy=='eye-first'else[3,1,0,2];pick=next(p for p in priority if p in possible);role=[1,4,6,0][pick];dec[y,x,0]=role;dec[y,x,1]=3;ids[y,x]=0;c[y,x]=0;event={'cell':[int(x),int(y)],'massBounds':{str(k):[float(mass[p]),float(upper[p])]for p,k in enumerate([1,4,6,0])},'possible':[1 if p==0 else 4 if p==1 else 6 if p==2 else 0 for p in possible],'chosenRole':role,'designPolicy':policy,'adopted':False}
        if role:
            si=int(np.argmax(weights[pick]));yy=y*4+si//4;xx=x*4+si%4;meta=layers[pick+1][1][yy,xx];rgba=layers[pick+1][0][yy,xx].copy();rgba[3]=1;ids[y,x]=[role,round(float(meta[2])),meta[0],layers[pick+1][3][yy,xx,2]];c[y,x]=rgba;event.update(sourceSample=[int(xx),int(yy)],literalSourceRGBA=rgba.tolist(),sourcePrimitive=float(ids[y,x,3]),sourceEye=float(ids[y,x,1]))
        events.append(event)
    return compose(d,ids,c,dec,vis,layers),events

def main():
    state=json.loads(sorted((HERE/'capture-c').glob('STATE98C*'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError');out=HERE/'policy-review-c';out.mkdir(exist_ok=True);rows=[];boards={};baselineChecks=[]
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));data=inputs(d);base=compose(d,*data);a=d['a'];exact=[np.array_equal(field,a[f'live96-final{i}'])for i,field in enumerate(base)];baselineChecks.append({'frame':e['frame'],'fieldsExact':exact,'maxDifference':[float(abs(field-a[f'live96-final{i}']).max())for i,field in enumerate(base)]});assert all(exact),baselineChecks[-1]
        if e['testStage82']not in ['turn','evaluated-blink']:continue
        allpics=[('strict original pass-through',base[0])];row={'frame':e['frame'],'sourceId':e['sourceId'],'stage':e['testStage82'],'index':e['stageIndex82'],'policies':[]}
        for policy in ['eye-first','background-first']:
            fields,events=choose(d,policy);changed=np.any(fields[0]!=base[0],axis=-1);Image.fromarray(np.flipud(rgb8(fields[0][...,:3]))).save(out/f'frame{e["frame"]}-{policy}-native1x.png');coords=[]
            for y,x in np.argwhere(changed):coords.append({'nativeROIxy':[int(x),int(y)],'beforeRGBA':base[0][y,x].tolist(),'afterRGBA':fields[0][y,x].tolist(),'owner':fields[1][y,x].tolist()})
            row['policies'].append({'name':policy,'events':events,'changedNativeRGBPixels':len(coords),'changes':coords,'remainingInvalidNative':int((fields[3][...,0]<0).sum()),'GPUValidated':False,'adopted':False});allpics.append((policy+' - offline, not adopted',fields[0]))
        im0=Image.fromarray(np.flipud(rgb8(base[0][...,:3])));im0.save(out/f'frame{e["frame"]}-strict-native1x.png');w,h=im0.size;board=Image.new('RGB',(w*8*3,h*8+24),'#20242a');dr=ImageDraw.Draw(board)
        for i,(name,pic)in enumerate(allpics):im=Image.fromarray(np.flipud(rgb8(pic[...,:3])));board.paste(im.resize((w*8,h*8),Image.Resampling.NEAREST),(i*w*8,24));dr.text((i*w*8+4,4),f'{name} {e["testStage82"]}{e["stageIndex82"]}',fill='white')
        board.save(out/f'frame{e["frame"]}-comparison8.png');boards.setdefault(e['testStage82'],[]).append(board);rows.append(row)
    for stage,pics in boards.items():
        w=max(im.width for im in pics);h=max(im.height for im in pics);fixed=[]
        for im in pics:canvas=Image.new('RGB',(w,h),'#20242a');canvas.paste(im,(0,0));fixed.append(canvas)
        fixed[0].save(out/(stage+'.gif'),save_all=True,append_images=fixed[1:],duration=350,loop=0)
    (HERE/'POLICIES98C.json').write_text(json.dumps({'status':'DESIGN_COMPARISON_NOT_ADOPTED','baselineCPUAll35GPUFieldsExact':True,'strictHasNoUnjustifiedPriority':True,'originalPartDepthHierarchyAlreadyUsedBeforeCellCoverage':'source depth determines sample-level occlusion; it does not decide equal aggregate iris/white coverage','cacheRule':'same original visible source texel only; weaker role-only or wrong canonical-origin reuse is not justified','policyAlternatives':'eye-first: iris > sclera > line > background, background-first: background > sclera > iris > line, only exact current coverage ties; unknown alpha unchanged','GPUValidations':'strict baseline actual; alternatives offline only','baseline':baselineChecks,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'baselineFrames':len(baselineChecks),'allFourFieldsExact':True,'alternativeFrames':len(rows),'policyChoicesAdopted':False}))
if __name__=='__main__':main()
