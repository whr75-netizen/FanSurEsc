"""Validate completed real GPU packets; never generate or substitute GPU data."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw

H=Path(__file__).resolve().parent
R=H.parents[1]
sys.path.insert(0,str(R/'bounded-form115/runtime24/full-render24'))
from report_full24 import plane, buffer, full, rgba, read

def main():
    roots=[Path(x) for x in sys.argv[1:] if not x.startswith('--')]
    root=roots[0] if roots else H/'phase-run'; end=read(root/'STATE113-0008-finished.json')
    assert end['PlayExited'] and not end.get('error') and not end.get('restorationError')
    assert end['forward102Disposed'] and not end['globalRestoreErrors']
    assert all(x['equal'] for x in end['nativeComparisons72'])
    assert end['motionRestoration82']['allRestored']
    imp=read(H/'import/COMPLETE.json'); assert imp['Status']=='complete' and imp['StateEqual']
    lut=read(R/'argon23-runtime113/SOURCE113.json')
    rows=[]; maps=[]; identities=[]; colours=[]; coordinateCount=0
    for packet in end['sequencePackets']:
        declared=Path(packet['output'])
        p=root/declared.parent.name/declared.name
        m=read(p/'RAW_MANIFEST.json')
        assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
        assert m['sourceId']==packet['sourceId'] and m['frameUnchangedDuringReadback'] and m['algorithmValid113']
        hh=m['forward102']['headHair25']; n=m['forward102']['nativeRegistration']
        origin=(np.asarray(n['anchor'],np.float32)+np.asarray(n['bounds'][:2],np.float32)).astype(np.float32)
        assert np.array_equal(origin,np.array(hh['origin'],np.float32)) and hh['frame']==m['frameIndex']
        assert hh['size']==m['forward102']['canonicalSize']
        cw,ch=np.array(hh['size'])//4; rx,ry,w,h=m['grid102']['eyeTopLeftROI']
        ids=buffer(p/'curve-identity.f32').reshape(ch,cw,4)
        colour=buffer(p/'curve-colour.f32').reshape(ch,cw,4)
        q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4)
        v=buffer(p/'ASSIGNED-visibility24.f32').reshape(h,w,16,4)
        fmeta,fo=plane(p/'F-FinalOwner.plane'); _,fc=plane(p/'F-FinalRGBA.plane')
        _,eo=plane(p/'F-EyeOwner.plane'); hm,ha=plane(p/'H25-meta.plane'); _,hc=plane(p/'H25-rgba.plane')
        assert fmeta['sourceId']==hm['sourceId']==m['sourceId'] and hm['frameIndex']==m['frameIndex']
        cells={}; errors=0; tested=0
        for y in range(h):
            for x in range(w):
                centre=np.asarray([rx+x+.5,ry+h-y-.5],np.float32)
                cell=np.floor(centre-origin).astype(int); cx,cy=cell
                dest=origin+cell.astype(np.float32)+np.asarray([[(i%4+.5)/4,1-(i//4+.5)/4]for i in range(16)],np.float32)
                valid=q[y,x,:,2]>0
                assert np.array_equal(q[y,x,valid,:2],dest[valid]); coordinateCount+=int(valid.sum())
                if not (0<=cx<cw and 0<=cy<ch) or ids[cy,cx,0]<=0: continue
                lo=hi=0.; raw=0
                for i in range(16):
                    sy,sx=divmod(i,4); yy=(ch-1-cy)*4+sy; xx=cx*4+sx
                    hair=ha[yy,xx]; a=hc[yy,xx,3]
                    if hair[0]<=0 or hair[3]<=0 or a<=0:continue
                    weight=float(np.clip(hair[3],0,1)); raw+=1
                    if q[y,x,i,2]>0 and hair[0]<q[y,x,i,2]-3e-5:lo+=weight;hi+=weight
                    elif q[y,x,i,2]<=0:hi+=weight
                cells[(int(cx),int(cy))]={'physicalROI':[x,y], 'partOwner':ids[cy,cx,:2].astype(int).tolist(),
                    'preHair':eo[y,x].tolist(),'final':fo[y,x].tolist(), 'headHairOpaqueSamples':raw,
                    'headHairFrontInterval':[lo,hi], 'validCarrier':int(valid.sum()),
                    'faceVisibleInterval':[float(v[y,x,:,0].sum()),float(v[y,x,:,1].sum())]}
                role,owner=fo[y,x,:2].astype(int)
                if role in (2,5,7):
                    part=role-1; pal=lut['lidPalette'] if part==6 else lut['keys']
                    expected=np.asarray([a['linear']for a in pal if a['owner']==owner and(part==6 or a['part']==part)],np.float32)
                    tested+=1; errors+=not np.any(np.all(expected==fc[y,x,:3],axis=1))
        assert errors==0
        product,sid=full(p,'product77'); candidate,sid2=full(p,'candidate113'); assert sid==sid2==m['sourceId']
        maps.append(cells); identities.append(ids); colours.append(colour)
        rows.append({'sourceId':sid,'frame':m['frameIndex'],'serial':m['mainSerial'],
            'origin':origin.tolist(),'physicalOutputROI':[rx,ry,w,h],'headHairOwnedBytes':hh['ownedBytes'],'positiveQueryCoordinates':int((q[...,2]>0).sum()),
            'eyeLinearPaletteExact':tested,'eyeLinearPaletteErrors':int(errors),
            'keyCell':cells[(3,4)],'canonicalOutputCells':len(cells),
            'finalVisibleParts':dict(collections.Counter(str(tuple(fo[y,x,:2].astype(int)))for y in range(h)for x in range(w)if int(fo[y,x,0])in(2,5,7)))})
    assert len(rows)==2 and rows[1]['frame']==rows[0]['frame']+1
    common=set(maps[0])&set(maps[1]); changes=[]
    for k in sorted(common):
        a,b=maps[0][k],maps[1][k]
        if a['final'][:2]!=b['final'][:2]: changes.append({'canonical':list(k),'before':a,'after':b})
    missed=[]
    for i in range(2):
        for y,x in np.argwhere(identities[i][...,0]>0):
            if (int(x),int(y))not in maps[i]:missed.append({'frame':rows[i]['frame'],'canonical':[int(x),int(y)],'partOwner':identities[i][y,x,:2].astype(int).tolist()})
    assert np.array_equal(identities[0][...,:2],identities[1][...,:2])
    assert np.array_equal(colours[0],colours[1])
    assert all(x['keyCell']['final'][:2]==[5.,2.]for x in rows)
    assert all(x['keyCell']['headHairFrontInterval']==[4.,4.]for x in rows)
    before=read(H/'import/BEFORE.json'); nat=read(root/'NATIVE_BEFORE73.json')
    a=collections.Counter(tuple(x.split('|')[:2])for x in before['Native']); b=collections.Counter((x['path'],x['type'])for x in nat)
    delta={k:end['afterMemory'][k]-end['beforeMemory'][k]for k in ['allocated','mono','reserved','renderTextureCount']}
    out={'actualGPUFrames':rows,'positiveCoordinatesExact':coordinateCount,'canonicalPartIdentityEqual':True,'canonicalColourByteEqual':True,
        'keyWhiteCellFixed':True,'commonCanonicalFinalOwnerChanges':changes,'allocatedCanonicalCellsOutsidePhysicalROI':missed,
        'notFullPhaseInvariant':bool(changes or missed),'GPUReadbacksAreObservedOnly':True,'product77DefaultChanged':False,
        'preservation':{'import44NativeEqual':True,'captureNativeEqual':len(nat),'importOnlyNativeComparisons':list((a-b).elements()),
            'inputRestored':end['editInputRestoration82'],'motionRestored':end['motionRestoration82']['allRestored'],
            'PlayExited':end['PlayExited'],'globalRestoreErrors':end['globalRestoreErrors']},
        'memory':{'API':'UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong/GetMonoUsedSizeLong/GetTotalReservedMemoryLong + RT count',
            'before':end['beforeMemory'],'after':end['afterMemory'],'deltaBytesExceptRTCount':delta,'physicalWorkingSetNotMeasured':True,
            'leakOrCacheNotDetermined':True},
        'limits':['Two actual consecutive phase states, not a complete phase/Close/rotation/hair matrix.',
            'Canonical source has18x8 cells, physical output ROI is16x8 then17x8. The left lid(0,3) is clipped in frame101 and present in102.',
            'At(10,3) face-visible7/16 rejects the eye in both frames. Non-eye fallback still uses original physical S4, so final hair/canvas changes.',
            'Shared-skin source-unoccluded gate is unchanged; face UV regions/palette/outline remain unresolved.']}
    (H/'GPU_RESULT25.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if '--oracle' in sys.argv:
        from test_cpu import geometry, alpha_hair, HairRay
        proofs=[]
        for i,packet in enumerate(end['sequencePackets']):
            declared=Path(packet['output']); p=root/declared.parent.name/declared.name
            m=read(p/'RAW_MANIFEST.json'); c=geometry(p,m); alpha,owned=alpha_hair(c); ray=HairRay(c,alpha)
            _,_,qw,qh=m['grid102']['eyeTopLeftROI']
            q=buffer(p/'ASSIGNED-depth24.f32').reshape(qh,qw,16,4)
            x,y=maps[i][(3,4)]['physicalROI']; query=q[y,x]
            cpu=ray.query(query[:,:2],query[:,2]); _,ha=plane(p/'H25-meta.plane'); _,hc=plane(p/'H25-rgba.plane')
            gpu=[]
            for si in range(16):
                sy,sx=divmod(si,4); height=ha.shape[0]//4; hair=ha[(height-1-4)*4+sy,3*4+sx]
                gpu.append(int(hair[0]>0 and hair[0]<query[si,2]-3e-5 and hc[(height-1-4)*4+sy,3*4+sx,3]>0))
            expected=[int(v['exactCutout']>0) for v in cpu]; assert gpu==expected
            proofs.append({'sourceId':m['sourceId'],'frame':m['frameIndex'],'canonical':[3,4],
                'physicalROI':[x,y],'actualHairFront16':gpu,'sameFrameCPUHairFront16':expected,'equal':True,'sourceAlphaBytes':owned})
        (H/'CPU_GPU_HAIR25.json').write_text(json.dumps({'actualGPUComparedToSameFrameGeometry':True,'rows':proofs,
            'testedSamples':32,'sourcePacketsKeptSeparate':True},indent=2)+'\n',encoding='utf-8')
    # Comparison is a view of actual saved frames. Nearest enlargement adds no data.
    tile=Image.new('RGB',(560,350),(35,35,35));draw=ImageDraw.Draw(tile)
    for i in range(2):
        for j,name in enumerate(['control','candidate']):
            im=Image.open(root/f'results/{i:02d}-{name}-eye.png').convert('RGB')
            tile.paste(im,(j*280,i*165+25));draw.text((j*280+4,i*165+4),f'{name} GPU frame {rows[i]["frame"]}',fill='white')
    tile.save(H/'EYE_COMPARE25.png')
    print(json.dumps({'frames':len(rows),'exactCoordinates':coordinateCount,'keyWhiteCellFixed':True,
        'commonFinalOwnerChanges':len(changes),'croppedCanonicalCells':len(missed),'fullPhaseInvariant':False,
        'allocatedDeltaMiB':delta['allocated']/1048576,'allNativeContentsEqual':True},ensure_ascii=False))

if __name__=='__main__':main()
