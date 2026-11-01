from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,rgb8,PARTS
from validate96 import read
def main():
    state=json.loads(sorted((HERE/'capture').glob('STATE96*'))[-1].read_text());queries=json.loads((HERE/'oracle/QUERIES_OWNED95.json').read_text());proof=json.loads((HERE/'oracle/VISIBILITY_PROOF95-source-cache-actual96.json').read_text());pb={}
    for x in proof:pb.setdefault(x['frame'],[]).append(x)
    rows=[];panels=[];out=HERE/'review';out.mkdir(exist_ok=True)
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));m=d['m'];a=d['a'];frame=e['frame'];cw,ch=np.asarray(m['retarget89']['size'])//4;z=np.load(HERE/f'oracle/candidate-source-cache-actual96/frame{frame}.npz');r={'frame':frame,'sourceId':e['sourceId'],'evaluatedClose':m['motion82']['getterClose'],'CPUVisibilitySamples':len(pb[frame])};vis=read(d['path']/'live96-visibility.buffer').reshape(4,ch*4,cw*4,4);maxv=0;diff=0
        for p in pb[frame]:
            part=PARTS.index(p['part']);x,y=p['sample'];candidateAlpha=a[f'retarget-part{part}-0'][ch*4-1-y,x,3];want=np.asarray(p['visibility'])*candidateAlpha;err=abs(vis[part,y,x,:2]-want);maxv=max(maxv,float(err.max()));diff+=bool((err>1e-6).any())
        r.update(visibilityMax=maxv,differentVisibilitySamples=diff)
        for name,expected in [('colour','canonicalColour'),('identity','canonicalIdentity')]:
            v=read(d['path']/f'live96-{name}.buffer').reshape(ch,cw,4);r[name+'Max']=float(abs(v-z[expected]).max());r[name+'DifferentCells']=int(np.any(v!=z[expected],axis=-1).sum())
        for field,name in enumerate(['colour','owner','depth']):
            v=a[f'live96-final{field}'];r['final'+name+'Max']=float(abs(v-z[name]).max());r['final'+name+'DifferentPixels']=int(np.any(v!=z[name],axis=-1).sum())
        audit=a['live96-final3'];r['invalidNativePixels']=int((audit[...,0]<0).sum());mask=audit[...,2]>0;r['nativeLidExact']=all(np.array_equal(a[f'live96-final{i}'][mask],a[base][mask])for i,base in enumerate(['native-final-rgba','native-final-owner','native-final-depth']));r['sourceOwnerSchema']='Native395 role+1/sourceEye/mainDepth/sourcePrimitive';r['GPUCost']=m['live96'];rows.append(r)
        pics=[]
        for label,key in [('product77','native-final-rgba'),('live96','live96-final0')]:
            im=Image.fromarray(np.flipud(rgb8(a[key][...,:3])));im.save(out/f'frame{frame}-{label}-native1x.png');pics.append(im)
        panel=Image.new('RGB',(pics[0].width*16,pics[0].height*8+24),'#20242a');draw=ImageDraw.Draw(panel)
        for i,im in enumerate(pics):panel.paste(im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST),(i*im.width*8,24));draw.text((i*im.width*8+5,5),f'{"Product77"if i==0 else"Live96"} frame{frame} Close{r["evaluatedClose"]}',fill='white')
        panel.save(out/f'frame{frame}-nearest8.png');panels.append(panel)
    panels[0].save(out/'LIVE96-sequence.gif',save_all=True,append_images=panels[1:],duration=350,loop=0)
    result={'status':'ACTUAL_RENDERER_ISOLATED_GPU_SELECTION_COMPARISON','allFinalExact':all(max(r[k]for k in ['finalcolourMax','finalownerMax','finaldepthMax'])==0 for r in rows),'allCanonicalExact':all(r['colourMax']==r['identityMax']==0 for r in rows),'allVisibilityExact':all(r['visibilityMax']==0 for r in rows),'nativeLidAllExact':all(r['nativeLidExact']for r in rows),'rows':rows,'productDefault':77,'runtimeReadbacks':0,'liveObserverInvokesFinalOnlyAtCapturedStates':True,'fullMotionNotYetValidated':True};(HERE/'LIVE_COMPARISON96.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
