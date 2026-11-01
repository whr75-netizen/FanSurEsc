"""Source-ray bounds -> joint cell label -> current backing -> literal LUT.

Unknown retains the exact original output and is marked invalid. No RGB mixes,
Close-driven deletions, screen history averages, or inferred skin are used.
"""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));sys.path.insert(0,str(ROOT/'eye-close90'))
from analyse89 import packet,geometry,PARTS,PROJ,rgb8
from analyse_capture68 import camera
from surface_query90 import choose_joint_bounds,visibility_bounds

def string(f,s):
    b=s.encode();n=len(b)
    while n>=128:f.write(bytes([(n&127)|128]));n>>=7
    f.write(bytes([n]));f.write(b)


def numpy_scalar_json(value):
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)

def alpha_table(source):
    out={}
    for q in source['queries']:
        mat=source['sources'][str(q['rendererSlot'])+'-'+str(q['sourceSubMesh'])];lo,hi=q['min'],q['max']
        if mat['alphaTest']:bounds=[1.,1.]if lo>=mat['cutoff']else[0.,0.]if hi<mat['cutoff']else[0.,1.]
        elif mat['alphaBlend']:bounds=[max(0.,lo),min(1.,hi)]
        else:bounds=[1.,1.]
        out[q['id']]=bounds
    return out

def source_texel(layers,part,sy,sx):
    if PARTS[part]not in [1,4]:return None
    owner=int(round(float(layers[part][1][sy,sx,2])))
    q=np.r_[layers[part][2][sy,sx,:3],1.]@PROJ[owner]
    tolerance=16*np.finfo(np.float32).eps*max(1.,float(abs(q).max()))
    if np.min(abs(q-np.rint(q)))<=tolerance:return None
    return (owner,PARTS[part],int(np.floor(q[0])),int(np.floor(q[1])))


def resolve_identity_tie(prior,decision,current_witnesses):
    """Only break an exact, observed eye-part tie with a still-visible source key.

    current_witnesses contains keys with strictly positive current lower coverage.
    It never includes screen RGB, inferred texels, or merely possible visibility.
    """
    if prior is None:return None
    possible=decision['possibleLabels'];mass=decision['massBounds'];label=prior['key'][1]
    exact=set(possible).issubset({1,4,6})and len(possible)>1 and label in possible
    exact=exact and all(mass[str(k)][0]==mass[str(k)][1]for k in possible)
    exact=exact and mass[str(label)][0]>mass['0'][1]
    return label if exact and tuple(prior['key'])in current_witnesses else None

def main():
    variant=sys.argv[1]if len(sys.argv)>1 else 'conservative';suffix=''if variant=='conservative'else '-'+variant
    if len(sys.argv)>2:
        tag=sys.argv[2];assert tag.isalnum();suffix+='-'+tag
    cache_mode=variant=='source-cache';skin_mode=variant in ['joint-skin','owned-eye','owned-fragment','source-cache'];owned_mode=variant in ['owned-eye','owned-fragment','source-cache'];fragment_mode=variant in ['owned-fragment','source-cache']
    run=HERE/'capture-scale-correct';state=json.loads(sorted(run.glob('STATE95B*'))[-1].read_text());source=json.loads((HERE/'ALPHA_SOURCE95B.json').read_text());assert source['success']and all(source['unchanged'].values());bounds=alpha_table(source);query={r['frame']:r for r in json.loads((HERE/('QUERIES_OWNED95.json'if owned_mode else'QUERIES_SKIN_FOCUS95.json'if skin_mode else'QUERIES_FACING95.json'if variant=='joint-facing'else'QUERIES95.json')).read_text())['frames']};out=HERE/('candidate'+suffix);out.mkdir(exist_ok=True);inputs=HERE/('final-input'+suffix);inputs.mkdir(exist_ok=True);rows=[];details=[];strips=[];proofs=[]
    if skin_mode:
        extra=json.loads((HERE/'ALPHA_SOURCE_SKIN95.json').read_text());assert extra['success']and all(extra['unchanged'].values())
        for key,mat in extra['sources'].items():
            if key in source['sources']:assert mat==source['sources'][key],key
            else:source['sources'][key]=mat
        oldids={q['id']for q in source['queries']};assert all(q['id']not in oldids for q in extra['queries']);source['queries']+=extra['queries'];bounds=alpha_table(source)
    identity_cache={};previous_scope=None;tie_events=[]
    for entry in state['sequencePackets']:
        d=packet(Path(entry['output']));m=d['m'];a=d['a'];frame=m['frameIndex'];layers,physical,checks=geometry(d);ch,cw=np.array(layers[0][0].shape[:2])//4
        scope_key=(m['sequenceId'],m['eyeFeature']['topologySHA256'],m['retarget89']['sourceMeshId'],m['sourceForm86']['templateRoleId'],tuple(m['retarget89']['bounds']))
        if scope_key!=previous_scope:identity_cache.clear();previous_scope=scope_key
        lower=np.zeros((3,ch*4,cw*4));upper=lower.copy();skin_lower=np.zeros((ch*4,cw*4));skin_upper=skin_lower.copy();blocked=unknown=0
        for q in query[frame]['queries']:
            hits=[];replaced=[]
            for hit in q['hits']:
                mat=source['sources'][str(hit['rendererSlot'])+'-'+str(hit['sourceSubMesh'])];cull=mat['cullMode'];w=hit['projectedWinding']
                if(cull==2 and w!=1)or(cull==1 and w==1):continue
                if owned_mode and hit['rendererSlot']==1 and hit['sourceSubMesh']in [1,2,4,6]and hit['eyeOwner']==q['eyeOwner']:
                    replaced.append(hit);continue
                hits.append(hit)
            proof=visibility_bounds(hits,q['depth'],bounds);candidate_cull=source['sources']['1-'+str(q['sourceRole'])]['cullMode'];candidate_back=variant in ['joint-facing','owned-eye','owned-fragment','source-cache']and((candidate_cull==2 and q['candidatePhysicalWinding']!=1)or(candidate_cull==1 and q['candidatePhysicalWinding']==1));
            if candidate_back:proof['lower']=proof['upper']=0.;proof['resolved']=True
            sx,sy=q['sample'];part=q['partIndex']-1
            if part<0:skin_lower[sy,sx]=q['alpha']*proof['lower'];skin_upper[sy,sx]=q['alpha']*proof['upper']
            else:lower[part,sy,sx]=q['alpha']*proof['lower'];upper[part,sy,sx]=q['alpha']*proof['upper']
            blocked+=proof['upper']==0;unknown+=not proof['resolved']
            proofs.append({'sourceId':m['sourceId'],'frame':frame,'part':q['sourceRole'],'sample':q['sample'],'visibility':[proof['lower'],proof['upper']],'frontHits':proof['hits'],'replacedOriginalEyeHits':replaced})
        depth=np.stack([np.where(layers[p][1][...,0]>0,layers[p][1][...,0],np.inf)for p in [1,2,3]])
        colours=np.zeros((ch,cw,4),'<f4');ids=np.zeros((ch,cw,4),'<f4');uncertain=np.zeros((ch,cw),bool);cell_details=[]
        for y in range(ch):
            for x in range(cw):
                sl=(slice(y*4,y*4+4),slice(x*4,x*4+4));lo=lower[(slice(None),)+sl].reshape(3,16);hi=upper[(slice(None),)+sl].reshape(3,16);z=depth[(slice(None),)+sl].reshape(3,16);decision=choose_joint_bounds(lo,hi,z,[1,4,6]);role=decision['winner']
                preferred=None
                if role is None and cache_mode and (x,y)in identity_cache:
                    prior=identity_cache[x,y];label=prior['key'][1];mass=decision['massBounds'];pp=PARTS.index(label);positions=[(sy+y*4,sx+x*4)for sy,sx in np.argwhere(lo[pp-1].reshape(4,4)>0)]
                    matches=[(sy,sx)for sy,sx in positions if source_texel(layers,pp,sy,sx)==tuple(prior['key'])]
                    if resolve_identity_tie(prior,decision,{source_texel(layers,pp,sy,sx)for sy,sx in positions})is not None:
                        if matches:
                            preferred=max(matches,key=lambda p:lower[pp-1,p[0],p[1]]);role=label;event={'frame':frame,'cell':[x,y],'sourceTexelKey':prior['key'],'referenceFrame':prior['frame'],'massBounds':mass,'chosenRole':label,'reason':'exact eye-part coverage tie; same currently visible source texel identity, not screen RGB history'};tie_events.append(event);decision={**decision,'winner':label,'paletteLookupAllowed':True,'sourceIdentityTie':event}
                if role is None:uncertain[y,x]=True;cell_details.append({'cell':[x,y],'decision':decision});continue
                if role==0:continue
                part=PARTS.index(role);pi=part-1;order=np.argsort(z,axis=0,kind='stable');Tlo=np.ones(16);weight=np.zeros((3,16))
                for rank in range(3):
                    k=order[rank];aa=lo[k,np.arange(16)];bb=hi[k,np.arange(16)]
                    for j in range(3):weight[j,k==j]=Tlo[k==j]*aa[k==j]
                    Tlo*=1-bb
                i=int(np.argmax(weight[pi]));sy,sx=divmod(i,4);sy+=y*4;sx+=x*4
                if preferred is not None:sy,sx=preferred
                rgba=layers[part][0][sy,sx];meta=layers[part][1][sy,sx];colours[y,x]=rgba;colours[y,x,3]=1;ids[y,x]=[role,round(float(meta[2])),meta[0],layers[part][3][sy,sx,2]]
                key=source_texel(layers,part,sy,sx)
                if cache_mode and key is not None:identity_cache[x,y]={'key':list(key),'frame':frame}
                cell_details.append({'cell':[x,y],'decision':decision,'part':role,'eyeOwner':int(ids[y,x,1]),'sample':[sx,sy],'primitiveUV':layers[part][3][sy,sx].tolist(),'literalLinearRGBA':colours[y,x].tolist()})
        base=a['native-final-rgba'];base_owner=a['native-final-owner'];base_depth=a['native-final-depth'];h,w=base.shape[:2];yy,xx=np.mgrid[:h,:w];ref=m['nativeFinalReference89'];offset=np.asarray(m['trace86']['headJoinOffset']);delta=np.asarray(m['camera86']['deliveredDelta'][:2]);bottom=(np.stack([xx+ref['nativeROI'][0]+.5,yy+ref['nativeROI'][1]+.5],-1)-np.asarray(ref['origin']))/ref['scale']-offset-delta;top=bottom.copy();top[...,1]=272-bottom[...,1];local=np.floor(top-np.asarray(m['retarget89']['anchor'])-np.asarray(m['retarget89']['bounds'][:2])).astype(int);lx,ly=local[...,0],local[...,1];inside=(lx>=0)&(lx<cw)&(ly>=0)&(ly<ch);kx=np.clip(lx,0,cw-1);ky=np.clip(ly,0,ch-1)
        rx,ry,rw,rh=d['roi'];hx=np.floor(bottom[...,0]).astype(int)-rx;hy=np.floor(bottom[...,1]).astype(int)-ry;inhead=(hx>=0)&(hx<rw)&(hy>=0)&(hy<rh);px=np.clip(hx,0,rw-1);py=np.clip(hy,0,rh-1);old=a['old-eye-owner'][py,px];intr=a['old-intrinsic'][py,px];old_feature=inhead&(((np.rint(old[...,0])==2)&(intr[...,0]>0))|(np.rint(old[...,0])==7))
        ex,ey,ew,eh=d['eyeROI'];ix=np.floor(bottom[...,0]).astype(int)-ex;iy=np.floor(bottom[...,1]).astype(int)-ey;inrecords=(ix>=0)&(ix<ew)&(iy>=0)&(iy<eh);ix=np.clip(ix,0,ew-1);iy=np.clip(iy,0,eh-1);composed=inrecords&(d['records'][iy,ix,14,2]>.5);native_lid=inrecords&(np.rint(d['records'][iy,ix,3,0])==5)&((d['records'][iy,ix,14,2]>.5)|(d['records'][iy,ix,14,3]==77));protected=composed if variant=='conservative'else native_lid
        head_cam=camera(d['path']/'source.camera');main_cam=camera(d['path']/'main.camera');assert np.max(abs(head_cam['view'][:3,:3]-main_cam['view'][:3,:3]))<1e-6;depth_offset=head_cam['view'][2,3]-main_cam['view'][2,3]
        chosen=base.copy();own=base_owner.copy();za=base_depth.copy();selection=ids[ky,kx];new=inside&(selection[...,0]>0);bad=inside&uncertain[ky,kx]&(old_feature|new);z=selection[...,2]+depth_offset
        foreground=new&((((base_owner[...,0]==6)|((base_owner[...,0]>=8)&(base_owner[...,0]<=15)))&(base_owner[...,2]>0)&(base_owner[...,2]<z-3e-5))|(z>base_depth[...,0]+.0001))
        if fragment_mode:
            closest=np.full((ch,cw),np.inf)
            for cy,cx in np.argwhere(uncertain):
                sl=(slice(cy*4,cy*4+4),slice(cx*4,cx*4+4));pot=upper[(slice(None),)+sl]>0;zs=depth[(slice(None),)+sl];closest[cy,cx]=zs[pot].min(initial=np.inf)+depth_offset
            foreign=inhead&((base_owner[...,0]==6)|((base_owner[...,0]>=8)&(base_owner[...,0]<=15)))&(base_depth[...,3]>0)&(base_owner[...,2]>0)&(base_owner[...,2]<closest[ky,kx]-3e-5)
            known_hidden=bad&foreign;bad&=~known_hidden;foreground|=known_hidden
        paint=new&~foreground&~protected&~bad;chosen[paint]=colours[ky[paint],kx[paint]];own[paint]=np.stack([selection[...,0]+1,selection[...,1],z,selection[...,3]],-1)[paint];za[paint]=np.stack([base_depth[...,0],z,np.ones_like(z),np.ones_like(z)],-1)[paint]
        vacated=old_feature&~new&~protected&~foreground&~bad;missing=np.zeros((h,w),bool);backing_trace=[]
        roi=m['currentSources91']['roiTopLeft'];skin=a['current91-g2-0'];skin_meta=a['current91-g2-1'];head_cells={}
        for y,x in np.argwhere(vacated):
            gx=int(np.floor(bottom[y,x,0]));gy=int(np.floor(272-bottom[y,x,1]));key=(gx,gy)
            if key not in head_cells:
                sx=(gx-roi[0])*2;sy=(roi[1]+roi[3]-gy-1)*2;valid=sx>=0 and sy>=0 and sx+2<=skin.shape[1]and sy+2<=skin.shape[0]
                if valid:
                    mm=skin_meta[sy:sy+2,sx:sx+2];cc=skin[sy:sy+2,sx:sx+2];valid=bool((mm[...,0]>0).all()and(np.rint(mm[...,1])==4).all()and(cc[...,3]==1).all())
                head_cells[key]=(valid,sx,sy)
            valid,sx,sy=head_cells[key]
            physical_fragment=False
            if fragment_mode:
                sx=int(np.floor((bottom[y,x,0]-roi[0])*2));sy=int(np.floor((bottom[y,x,1]-(272-roi[1]-roi[3]))*2));valid=0<=sx<skin.shape[1]and 0<=sy<skin.shape[0]
                if valid:valid=bool(skin_meta[sy,sx,0]>0 and round(float(skin_meta[sy,sx,1]))==4 and skin[sy,sx,3]==1)
                physical_fragment=valid
            transported=False;transport_sample=None
            if not valid and skin_mode and inside[y,x]:
                cx,cy=int(kx[y,x]),int(ky[y,x]);sl=(slice(cy*4,cy*4+4),slice(cx*4,cx*4+4));lo=skin_lower[sl]
                if fragment_mode:
                    continuous=top[y,x]-np.asarray(m['retarget89']['anchor'])-np.asarray(m['retarget89']['bounds'][:2]);tsx,tsy=np.floor(continuous*4).astype(int)
                    if 0<=tsx<skin_lower.shape[1]and 0<=tsy<skin_lower.shape[0]and skin_lower[tsy,tsx]>=1:
                        tc=layers[0][0][tsy,tsx];tm=layers[0][1][tsy,tsx]
                        if tc[3]==1 and round(float(tm[1]))==4:valid=True;transported=True;transport_sample=(int(tsx),int(tsy),tc,tm)
                elif lo.sum()>8:
                    points=np.argwhere(lo>=1)
                    if len(points):
                        pick=points[np.argmin(((points+.5-2)**2).sum(1))];tsy,tsx=(pick+np.array([cy*4,cx*4])).astype(int);tc=layers[0][0][tsy,tsx];tm=layers[0][1][tsy,tsx]
                        if tc[3]==1 and round(float(tm[1]))==4:valid=True;transported=True;transport_sample=(int(tsx),int(tsy),tc,tm)
            if not valid:missing[y,x]=True;continue
            # One literal, actually rendered skin sample per logical cell. Four
            # opaque source samples are required; no fill across a native hole.
            c=skin[sy,sx]if not transported else transport_sample[2];meta=skin_meta[sy,sx]if not transported else transport_sample[3];zz=meta[0]+depth_offset
            target_other=(base_owner[y,x,0]==6 or 8<=base_owner[y,x,0]<=15)and base_owner[y,x,2]>0 and base_owner[y,x,2]<zz-3e-5
            if target_other:foreground[y,x]=True;continue
            if zz>base_depth[y,x,0]+.0001:missing[y,x]=True;continue
            primitive=a['current91-g2-3'][sy,sx,2]if not transported else layers[0][3][transport_sample[1],transport_sample[0],2]
            chosen[y,x]=c;own[y,x]=[meta[1],meta[2],zz,primitive];za[y,x]=[base_depth[y,x,0],zz,1,1];backing_trace.append({'nativeROIxy':[int(x),int(y)],'logicalCell':list(key),'source2xSample':[sx,sy],'linearRGBA':c.tolist(),'sourceMeta':meta.tolist(),'depthOffset':float(depth_offset),'allFourSourceSamplesOpaqueSkin':not transported and not physical_fragment,'physicalNativeFragmentSample':physical_fragment,'transportedSameFrameFeatureSkin':transported,'transportedSourceSample':list(transport_sample[:2])if transported else None})
        bad|=missing;scope=paint|vacated|bad
        # Exact raw Float32 colour/owner/depth triples form finite replay tables.
        atoms=np.concatenate([chosen,own,za],-1).astype('<f4');palette_atoms,inv=np.unique(atoms[scope],axis=0,return_inverse=True);mapping=np.zeros((h,w,4),'<f4');mapping[scope,0]=inv+1;mapping[scope,3]=np.where(bad[scope],-1,1)
        if not len(palette_atoms):palette_atoms=np.zeros((1,12),'<f4')
        for channel,baseline in enumerate([base,base_owner,base_depth]):
            file=inputs/f'{frame:04d}-field{channel}.bin';assert not file.exists()
            with file.open('xb')as f:
                string(f,'final-palette89/v1');string(f,m['sourceId']);string(f,'final95-field'+str(channel));f.write(struct.pack('<5i',frame,m['mainSerial'],w,h,len(palette_atoms)));f.write(baseline.astype('<f4').tobytes());f.write(mapping.tobytes());f.write(palette_atoms[:,channel*4:channel*4+4].astype('<f4').tobytes())
        np.savez_compressed(out/f'frame{frame}.npz',colour=chosen,owner=own,depth=za,base=base,baseOwner=base_owner,baseDepth=base_depth,scope=scope,invalid=bad,protected=protected,foreground=foreground,missing=missing,mapping=mapping,paletteAtoms=palette_atoms,canonicalColour=colours,canonicalIdentity=ids,canonicalUnknown=uncertain)
        row={'frame':frame,'sourceId':m['sourceId'],'Close':m['motion82']['getterClose'],'evaluatedError':m['motion82']['evaluatedVsOwnedBakeMax'],'canonicalRoleCells':{str(p):int((ids[...,0]==p).sum())for p in [1,4,6]},'canonicalUnknownCells':int(uncertain.sum()),'candidateNativePixels':int(paint.sum()),'currentBackingNativePixels':len(backing_trace),'missingBackingNativePixels':int(missing.sum()),'invalidNativePixels':int(bad.sum()),'protectedNativePixels':int(protected.sum()),'foregroundPixels':int(foreground.sum()),'exactRayBlockedSamples':int(blocked),'uncertainRaySamples':int(unknown),'paletteAtoms':len(palette_atoms),'colourChangedPixels':int((abs(chosen-base).max(-1)>0).sum()),'ownerChangedPixels':int((abs(own-base_owner).max(-1)>0).sum()),'depthOffsetFromCameraMatrices':float(depth_offset),'canonicalSignature':hashlib.sha256(ids[...,:2].astype('<i4').tobytes()).hexdigest(),'eyeRGB8':np.unique(rgb8(chosen[paint,:3]),axis=0).tolist()}
        rows.append(row);details.append({'frame':frame,'cells':cell_details,'backing':backing_trace});pics=[]
        for name,image in [('product77',base),('candidate',chosen)]:
            im=Image.fromarray(np.flipud(rgb8(image[...,:3])));im.save(out/f'frame{frame}-{name}-native1x.png');pics.append(im)
        panel=Image.new('RGB',(w*12*2,h*12+28),'#20242a');draw=ImageDraw.Draw(panel)
        for i,pic in enumerate(pics):panel.paste(pic.resize((w*12,h*12),Image.Resampling.NEAREST),(i*w*12,28));draw.text((i*w*12+4,6),f"{'Product77'if i==0 else'Candidate95'} frame{frame} evaluated Close{row['Close']}",fill='white')
        panel.save(out/f'frame{frame}-compare12.png');strips.append(panel)
    (HERE/('RESULT95'+suffix+'.json')).write_text(json.dumps({'status':'ISOLATED_FINAL_CANDIDATE_PENDING_GPU_AND_VISUAL_VERIFICATION','frames':rows,'unknownPolicy':'exact original pass-through with invalid flag; never transparent','paletteProtocol':'literal Float32 source/owner/depth atom tables; no sRGB8 roundtrip in final path','sourceQuantization':'authored bank roles1/4; native-source eyeline; actual current skin backing','productDefault':77,'ownerSchema':'Native395: encoded role+1, source eye owner, main-view depth, source primitive ID; alpha is separate','sourceIdentityTieEvents':tie_events,'cacheColdTiePolicy':'Unresolved; source witness cache is required, never fabricate a key-form'},indent=2)+'\n');(HERE/('CELL_PROVENANCE95'+suffix+'.json')).write_text(json.dumps(details,indent=2,default=numpy_scalar_json)+'\n');(HERE/('VISIBILITY_PROOF95'+suffix+'.json')).write_text(json.dumps(proofs,indent=2,default=numpy_scalar_json)+'\n')
    strip=Image.new('RGB',(strips[0].width,sum(x.height for x in strips)),'#20242a');y=0
    for pic in strips:strip.paste(pic,(0,y));y+=pic.height
    strip.save(HERE/('FINAL_STRIP95'+suffix+'.png'));strips[0].save(HERE/('FINAL_SEQUENCE95'+suffix+'.gif'),save_all=True,append_images=strips[1:],duration=350,loop=0)
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
