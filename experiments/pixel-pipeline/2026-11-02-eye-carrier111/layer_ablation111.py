"""Fixed canonical labels; separate pigment, carrier and canvas-ownership gates.
No tuning, source mutation, new Play or finalRGB. Canvas binding is a hypothesis.
"""
import json
from geometry111 import H,read,load,packet_list
from ray111 import NativeAlpha,FaceRay
from analyse111 import expose
import numpy as np
def main():
    _,paths=packet_list();out=[]
    for frame in [99,103,105,107,115,122,125,128]:
        p=next(p for p in paths if read(p/'RAW_MANIFEST.json')['frameIndex']==frame);ctx=load(p);alpha=NativeAlpha(ctx);rays=FaceRay(ctx,alpha);a=read(H/f'ANALYSIS111-frame{frame}.json');eyes=[]
        for e in a['eyes']:
            v=next(v for v in e['variants']if v['componentFirst']);policies=[]
            for policy in ['native','geometry-only','feature-canvas']:
                ex=v['exposure']if policy=='native'else[expose(ctx,alpha,rays,e['owner'],np.array(label),policy)for label in v['labels']];policies.append({'policy':policy,'sameCanonicalLabels':True,'exposure':ex,'eyePartSamples':[ [{'cellYX':c['cellYX'],'part':c['part'],'visibleNumerator':c['visibleCarrierFractionBounds'],'denominator':16}for c in cells if c['part']in[1,2]]for cells in ex]})
            eyes.append({'owner':e['owner'],'sourceMass':{'iris':e['irisSourceMass'],'white':e['whiteSourceMass']},'canonicalLabelSets':v['labels'],'policies':policies})
        row={'sourceId':ctx['sourceId'],'frame':frame,'stage':ctx['manifest']['motion82'],'eyes':eyes,'actualNewGPUForCanvasHypothesis':False,'notAnatomicalLidInference':True,'notProductApplied':True};(H/f'LAYER_ABLATION111-frame{frame}.json').write_text(json.dumps(row,indent=2)+'\n');out.append({'frame':frame,'eyes':[{'owner':e['owner'],'policies':[{'policy':v['policy'],'parts':v['eyePartSamples']}for v in e['policies']]}for e in eyes]});print(json.dumps(out[-1]),flush=True)
    (H/'LAYER_ABLATION111.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
