"""Validate the frozen actual seven-frame composite and numerical GPU replay."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import Reader,rgb8
from solve95 import resolve_identity_tie

def main():
    tests=[]
    def ck(name,value):
        assert value,name
        tests.append(name)
    report=json.loads((HERE/'RESULT95-source-cache.json').read_text());gpu=json.loads((HERE/'gpu-final/FINAL_GPU95_FINAL.json').read_text());folder=Path(gpu['output'])
    ck('GPU dispatch21 completed, own resources released, no product/Play/global writes',gpu['dispatchComplete']and gpu['ownedResourcesReleased']and len(gpu['rows'])==21 and not gpu.get('error')and gpu['PlayEntries']==gpu['globalWrites']==0 and not gpu['productActivation'])
    ck('GPU RT count stable',gpu['before']['RTcount']==gpu['after']['RTcount']==30)
    ck('create-only completion marker', (folder/'DISPATCH_COMPLETE89.marker').exists())
    actual=[]
    for row in report['frames']:
        frame=row['frame'];z=np.load(HERE/f'candidate-source-cache/frame{frame}.npz');scope=z['scope'];outside=~scope;protected=z['protected'];foreground=z['foreground']
        ck(f'{frame}: no unresolved/missing actual native pixels',row['invalidNativePixels']==row['missingBackingNativePixels']==row['canonicalUnknownCells']==0 and not z['invalid'].any())
        ck(f'{frame}: evaluated mesh matches source BakeMesh(true)',row['evaluatedError']==0)
        for field,name,base in [(0,'colour','base'),(1,'owner','baseOwner'),(2,'depth','baseDepth')]:
            b=Reader(folder/f'{frame:04d}-field{field}-0.bin');ck(f'{frame}/{name}: GPU packet contract',b.s()=='final-palette89-GPU/v1');sid,variant=b.s(),b.s();f,serial,w,h=[b.i()for _ in range(4)];a=b.a(w*h*4).reshape(h,w,4);b.end()
            ck(f'{frame}/{name}: GPU equals frozen CPU table exactly',sid==row['sourceId']and f==frame and np.array_equal(a,z[name]))
            ck(f'{frame}/{name}: outside scope and native-lid pass-through exact',np.array_equal(a[outside],z[base][outside])and np.array_equal(a[protected],z[base][protected]))
            ck(f'{frame}/{name}: actual nearer foreign owner preserved',np.array_equal(a[foreground],z[base][foreground]))
            indices=z['mapping'][scope,0].astype(int)-1;table=z['paletteAtoms'][:,field*4:field*4+4]
            ck(f'{frame}/{name}: every selected output is literal P[index]',np.array_equal(a[scope],table[indices]))
            if field==0:Image.fromarray(np.flipud(rgb8(a[...,:3]))).save(HERE/f'GPU_FINAL95-frame{frame}-native1x.png')
        owner=z['owner'];edited=np.any(owner!=z['baseOwner'],axis=-1)
        ck(f'{frame}: owner.w carries positive integral source primitive, never alpha substitution',np.all(owner[edited,3]>=1)and np.all(owner[edited,3]==np.rint(owner[edited,3])))
        ck(f'{frame}: colour alpha remains separate from primitive',np.all(z['colour'][scope,3]==1))
        if row['Close']==100:
            ck(f'{frame}: full evaluated Close emits no iris or sclera in joint support',row['canonicalRoleCells']['1']==row['canonicalRoleCells']['4']==0)
            ck(f'{frame}: final corrected scope has no iris/sclera owner',not np.isin(owner[scope,0],[2,5]).any())
        actual.append({k:row[k]for k in ['frame','sourceId','Close','candidateNativePixels','currentBackingNativePixels','protectedNativePixels','foregroundPixels','invalidNativePixels']})
    frames={r['frame']:r for r in report['frames']}
    ck('observed open and evaluated reopen recover identical canonical support',len({frames[i]['canonicalSignature']for i in [99,100,107,108]})==1)
    tie=report['sourceIdentityTieEvents'];ck('only observed exact tie is frame102 cell12,4',len(tie)==1 and tie[0]['frame']==102 and tie[0]['cell']==[12,4]and tie[0]['sourceTexelKey']==[1,1,220,79])
    decision={'possibleLabels':[1,4],'massBounds':{'1':[7,7],'4':[7,7],'0':[2,2]}};prior={'key':[1,1,220,79]};key=(1,1,220,79)
    ck('source witness tie preserves currently visible original texel',resolve_identity_tie(prior,decision,{key})==1)
    ck('cold cache does not invent key-form',resolve_identity_tie(None,decision,{key})is None)
    ck('fully occluded or different current source never gets ghost label',resolve_identity_tie(prior,decision,set())is None and resolve_identity_tie(prior,decision,{(1,1,221,79)})is None)
    ck('other eye cannot borrow identity',resolve_identity_tie(prior,decision,{(2,1,220,79)})is None)
    uncertain={'possibleLabels':[1,4],'massBounds':{'1':[6,8],'4':[7,7],'0':[2,2]}}
    ck('uncertain alpha/visibility cannot be overridden by tie cache',resolve_identity_tie(prior,uncertain,{key})is None)
    bg={'possibleLabels':[0,1],'massBounds':{'1':[7,7],'0':[7,7]}}
    ck('foreground/background tie is not auto feature preservation',resolve_identity_tie(prior,bg,{key})is None)
    # Earlier source-phase/occlusion witnesses are retained, not rerendered.
    old=json.loads((ROOT/'feature-layer88/TEST88.json').read_text());ck('88 source-local289phase regression evidence retained',old['passed']>=20)
    old90=json.loads((ROOT/'eye-close90/TEST90.json').read_text());ck('90 exact-ray, unknown, role decode regression evidence retained',old90['passed']>=10)
    result={'status':'SEVEN_OBSERVED_STATES_EXACT_GPU_LUT_REPLAY_NOT_LIVE_PRODUCT_INTEGRATION','passed':len(tests),'tests':tests,'frames':actual,'maxGPUFloatError':0,'paletteEscape':0,'ownerSchema':'Native395 role+1, sourceEye, mainViewDepth, sourcePrimitive; alpha separate','product':77,'PlayEntriesThisReplay':0,'maximumReadbackBytes':max(x['largestReadbackBytes']for x in gpu['rows']),'RTBefore':gpu['before']['RTcount'],'RTAfter':gpu['after']['RTcount'],'allocatedDeltaBytes':gpu['after']['allocated']-gpu['before']['allocated'],'limits':['7 conditional snapshots, not full motion sequence','Joint allocation/source queries computed offline; GPU replays frozen selection and literal lookup','Cold exact tie remains unresolved; cache generation tokens required for live C#/HLSL port','Native source skin is literal MToon; style matching not artist-approved','Quantitative checks do not establish aesthetic success']}
    (HERE/'FINAL_VALIDATION95.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='tests'},indent=2))

if __name__=='__main__':main()
