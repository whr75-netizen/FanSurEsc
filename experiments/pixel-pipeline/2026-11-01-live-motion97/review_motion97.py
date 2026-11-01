from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,rgb8
from validate96 import read
def main():
    out=HERE/'review97';out.mkdir(exist_ok=True);s=json.loads(sorted((HERE/'motion').glob('STATE97*'))[-1].read_text());rows=[];panels={};ref=None
    for e in s['sequencePackets']:
        d=packet(Path(e['output']));m=d['m'];a=d['a'];ids=read(d['path']/'live96-identity.buffer');colour=read(d['path']/'live96-colour.buffer');stage=m['motion82']['stage'];frame=e['frame'];r={'frame':frame,'stage':stage,'index':m['motion82']['index'],'sourceId':e['sourceId'],'roleOwnerSignature':hashlib.sha256(ids[:,:2].tobytes()).hexdigest(),'colourSignature':hashlib.sha256(colour.tobytes()).hexdigest(),'invalidNative':int((a['live96-final3'][...,0]<0).sum()),'rawProjectedRoot':m['motion82']['worldRootProjectedRaw'],'canonicalUnknown':m['live96']['canonicalUnknown']}
        if stage=='measured-phase':
            if ref is None:ref=(ids.copy(),colour.copy(),np.array(r['rawProjectedRoot']))
            r['roleOwnerDifferentCellsFromFirst']=int(np.any(ids[:,:2]!=ref[0][:,:2],axis=-1).sum());r['colourDifferentCellsFromFirst']=int(np.any(colour!=ref[1],axis=-1).sum());r['measuredPhaseX']=r['rawProjectedRoot'][0]-ref[2][0];r['measuredPhaseY']=r['rawProjectedRoot'][1]-ref[2][1]
        pics=[]
        for label,key in [('product77','native-final-rgba'),('live97','live96-final0')]:
            im=Image.fromarray(np.flipud(rgb8(a[key][...,:3])));im.save(out/f'frame{frame}-{label}-native1x.png');pics.append(im)
        h=max(x.height for x in pics);w=max(x.width for x in pics);panel=Image.new('RGB',(w*16,h*8+24),'#20242a');draw=ImageDraw.Draw(panel)
        for i,im in enumerate(pics):panel.paste(im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST),(i*w*8,24));draw.text((i*w*8+4,5),f'{"Product77"if i==0 else"Live97"} {stage} #{r["index"]} frame{frame} unknown{r["invalidNative"]}',fill='white')
        panel.save(out/f'frame{frame}-nearest8.png');panels.setdefault(stage,[]).append(panel);rows.append(r)
    for stage,p in panels.items():
        # Crop-size changes are shown against a fixed canvas, never auto-rescaled.
        w=max(x.width for x in p);h=max(x.height for x in p);fixed=[]
        for im in p:canvas=Image.new('RGB',(w,h),'#20242a');canvas.paste(im,(0,0));fixed.append(canvas)
        fixed[0].save(out/(stage+'.gif'),save_all=True,append_images=fixed[1:],duration=250,loop=0)
    phase=[r for r in rows if r['stage']=='measured-phase'];r={'sourceStates':len(rows),'sourceSequenceIds':list({x['sourceId'].rsplit('-frame',1)[0]for x in rows}),'phaseRoleOwnerSignatures':len({x['roleOwnerSignature']for x in phase}),'phaseColourSignatures':len({x['colourSignature']for x in phase}),'phaseXRange':[min(x['measuredPhaseX']for x in phase),max(x['measuredPhaseX']for x in phase)],'phaseYRange':[min(x['measuredPhaseY']for x in phase),max(x['measuredPhaseY']for x in phase)],'unknownNativeByFrame':{str(x['frame']):x['invalidNative']for x in rows if x['invalidNative']},'rows':rows,'notAestheticSuccess':True};(HERE/'MOTION_REVIEW97.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
