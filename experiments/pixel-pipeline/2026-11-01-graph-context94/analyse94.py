from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'))
try: from reader68 import plane,Reader,camera
except ImportError: from analyse_capture68 import plane,Reader,camera

def evaluated_mesh(path):
    r=Reader(path); assert r.s()=='aux-mesh67/v1'
    identity=r.identity(); matrix=r.mat(); vertices=r.a(r.i()*3).reshape(-1,3)
    normals=r.a(r.i()*3).reshape(-1,3); uv=r.a(r.i()*2).reshape(-1,2)
    triangles=[r.a(r.i(),'<i4')for _ in range(r.i())]; r.end()
    return identity,matrix,vertices,normals,uv,triangles

def rgb(a):
    a=np.clip(a[...,:3],0,1)
    return np.rint(255*np.where(a<=.0031308,12.92*a,1.055*np.power(a,1/2.4)-.055)).astype('uint8')

def main():
    p=HERE/'capture'; state=json.loads(sorted(p.glob('STATE94-*.json'))[-1].read_text())
    assert state.get('PlayExited') and not state.get('error') and not state.get('restorationError')
    packets=state['sequencePackets']; assert len(packets)==4
    rows=[]; charts=[]; first_vertices=None
    for index,entry in enumerate(packets):
        q=Path(entry['output']); manifest=json.loads((q/'RAW_MANIFEST.json').read_text())
        assert (q/'RAW_COMPLETE76.marker').exists() and manifest['sourceId']==entry['sourceId']
        parsed={f.stem:plane(f) for f in q.glob('*.plane')}
        a={k:v[1]for k,v in parsed.items()}
        assert len(a)==34 and all(np.isfinite(x).all() for x in a.values())
        assert all(h['sourceId']==entry['sourceId'] and h['frameIndex']==entry['frame'] and h['renderSerial']==entry['serial']for h,_ in parsed.values())
        cam=camera(q/'source.camera'); mi,matrix,vertices,*_=evaluated_mesh(q/'eye-evaluated.mesh')
        assert all(i['sourceId']==entry['sourceId']and i['frameIndex']==entry['frame']and i['renderSerial']==entry['serial']for i in [cam,mi])
        if first_vertices is None:first_vertices=vertices
        valid=(a['S3-meta'][...,0]>0)&(a['current91-g0-1'][...,0]>0)
        row={'index':index,'sourceId':manifest['sourceId'],'frame':entry['frame'],'serial':entry['serial'],'packed':manifest['productionPacked92'],'sameFrame':manifest['frameUnchangedDuringReadback'],'requestedCloseGetter':manifest['motion82']['getterClose'],'evaluatedVerticesDeltaFromFirst':float(abs(vertices-first_vertices).max(initial=0)),'sourceFrame':cam['sourceFrame'],'evaluatedFrame':cam['evaluatedFrame'],'planes':len(a),'irisMatchedSamples':int(valid.sum())}
        row['RGBA_product_vs_graph_max']=float(abs(a['S3-rgba']-a['current91-g0-0']).max(initial=0))
        row['meta_product_vs_graph_max']=float(abs(a['S3-meta']-a['current91-g0-1']).max(initial=0))
        row['backingRGBA_same4x_max']=float(abs(a['S0-rgba']-a['current91-g3-0']).max(initial=0))
        row['backingMeta_same4x_max']=float(abs(a['S0-meta']-a['current91-g3-1']).max(initial=0))
        row['opaqueSkin2xSamples']=int((a['current91-g2-0'][...,3]>.999).sum())
        row['backingDepthMax']=float(abs(a['S0-meta'][...,0]-a['current91-g3-1'][...,0]).max(initial=0))
        row['backingRoleOwnerAlphaExact']=np.array_equal(a['S0-meta'][...,1:],a['current91-g3-1'][...,1:])
        row['backingCoverageExact']=np.array_equal(a['S0-rgba'][...,3],a['current91-g3-0'][...,3])
        delta=abs(rgb(a['S0-rgba']).astype(int)-rgb(a['current91-g3-0']).astype(int))
        row['backingPreview_sRGB8_maxCodeDelta']=int(delta.max(initial=0))
        row['backingPreview_sRGB8_differentSamples']=int((delta.max(-1)>0).sum())
        where=np.argwhere(delta.max(-1)>0)
        row['backingPreview_sRGB8_differences']=[{'memoryXY':[int(x),int(y)],'actualRGB8':rgb(a['S0-rgba'])[y,x].tolist(),'graphRGB8':rgb(a['current91-g3-0'])[y,x].tolist(),'actualLinearRGBA':a['S0-rgba'][y,x].tolist(),'graphLinearRGBA':a['current91-g3-0'][y,x].tolist()}for y,x in where]
        if row['packed']:
            prod=np.stack([a['S3-shade'][...,1],a['S3-shade'][...,2],a['S3-shade'][...,3]],-1)
            row['producer_vs_graph']={
                'normal_max':float(abs(a['S3-point'][valid]-a['current91-g0-5'][valid]).max(initial=0)),
                'SH_max':float(abs(a['S3-uv'][valid]-a['current91-g0-6'][valid]).max(initial=0)),
                'lit_available_mainLit_max':float(abs(prod[valid]-a['current91-g0-7'][valid,:3]).max(initial=0)),
                'g_max':float(abs(a['S3-shade'][valid,0]-a['current91-g0-4'][valid,0]).max(initial=0))}
            row['original_vs_retargetGraph_all8_max']=max(float(abs(a[f'current91-g0-{i}']-a[f'current91-g1-{i}']).max(initial=0))for i in range(8))
            error=np.where(valid,abs(a['S3-shade'][...,0]-a['current91-g0-4'][...,0]),-1)
            y,x=np.unravel_index(np.argmax(error),error.shape)
            row['worstSample']={'memoryXY':[int(x),int(y)],'primitiveUV':a['current91-g0-3'][y,x].tolist(),'productionNormal':a['S3-point'][y,x].tolist(),'graphNormal':a['current91-g0-5'][y,x].tolist(),'productionSH':a['S3-uv'][y,x].tolist(),'graphSH':a['current91-g0-6'][y,x].tolist(),'productionLitAvailableMain':prod[y,x].tolist(),'graphLitAvailableMain':a['current91-g0-7'][y,x,:3].tolist(),'productionG':float(a['S3-shade'][y,x,0]),'graphG':float(a['current91-g0-4'][y,x,0])}
        images=[rgb(a['S3-rgba']),rgb(a['current91-g0-0']),rgb(a['S0-rgba']),rgb(a['current91-g3-0'])]
        if row['packed']:
            images += [np.repeat(np.rint(np.clip(a[n][...,0],0,1)*255).astype('uint8')[...,None],3,-1) for n in ['S3-shade','current91-g0-4']]
        else: images += [np.zeros_like(images[0])]*2
        charts.append(images); rows.append(row)
    report={'status':'ACTUAL_FOUR_FRAME_GRAPH_CONTEXT_COMPARISON','frames':rows,'productDefault':77,'notFinalEyeComposition':True,'normalSHLightEquality':all(max(r['producer_vs_graph'].values())==0 for r in rows if r['packed']),'backing4xEquality':all(r['backingRGBA_same4x_max']==0 and r['backingMeta_same4x_max']==0 for r in rows),'automaticAdoption':False,'CloseReopenValidated':False,'note':'Source samples and isolated current-deformed skin only. Close getter does not identify evaluated geometry: deformation appears one frame later, and evaluated reopen was not captured. No shifted-eye final owner/backing integration, no walking temporal claim. RGB8 differences use explicit linear-to-sRGB preview conversion, not actual final compositing.'}
    (HERE/'RESULT94.json').write_text(json.dumps(report,indent=2)+'\n')
    w,h=charts[0][0].shape[1],charts[0][0].shape[0]; scale=5; col=w*scale+14; rh=h*scale+34
    image=Image.new('RGB',(col*6+10,rh*4+34),'#22252a'); draw=ImageDraw.Draw(image)
    labels=['Actual S3 RGB','Graph S3 RGB','Actual skin RGB','Graph skin RGB','Actual g (0..1)','Graph g (0..1)']
    for j,s in enumerate(labels):draw.text((10+j*col,9),s,fill='white')
    for i,ims in enumerate(charts):
        for j,im in enumerate(ims):
            im=np.flipud(im).copy(); pic=Image.fromarray(im); pic.save(HERE/f'frame{i}-field{j}-native.png'); image.paste(pic.resize((w*scale,h*scale),Image.Resampling.NEAREST),(10+j*col,34+i*rh))
        draw.text((10,34+i*rh+h*scale+5),f"f{rows[i]['frame']} requestedClose={rows[i]['requestedCloseGetter']} meshDelta={rows[i]['evaluatedVerticesDeltaFromFirst']:.5f}",fill='white')
    image.save(HERE/'COMPARISON94.png')
    print(json.dumps({'frames':len(rows),'planes':sum(r['planes']for r in rows),'normalSHLightEquality':report['normalSHLightEquality'],'backing4xEquality':report['backing4xEquality'],'examples':[r.get('producer_vs_graph')for r in rows]},indent=2))

if __name__=='__main__':main()
