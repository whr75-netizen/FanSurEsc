"""Inspect saved actual GPU data; no additional Unity execution."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,struct
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
d=load('GPU58.json');source=load('SOURCE58.json');oracle=load('JS_CSHARP58.json');assert not d.get('error') and d['phase']=='finished'
recheck=load('CSHARP_RECHECK58.json');assert recheck['passed'] and recheck['originalExpressionDepthMismatches']==63 and recheck['uploadedFloat32ComponentMismatches']==0
n=d['sampleCount'];read=lambda name:np.frombuffer((R/name).read_bytes(),dtype='<f4').reshape(n,4)
initial=read('INITIAL58.float4');join=read('JOIN_INPUT58.float4');final=read('FINAL58.float4');classes=read('CLASS58.float4');factors=read('FACTOR58.float4');pixels=np.frombuffer((R/'FINAL58.rgba').read_bytes(),dtype=np.uint8).reshape(n,4)
decode=lambda x:x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
maxError=0;oldCount=0;changed=0;sourceExcluded=0;metadataMismatches=[];rgbExpected=[]
for i,row in enumerate(d['rows']):
    a=row['initialRGB8'];b=row['finalRGB8'];alpha=row['nativeAlpha8'];bound=row['boundOpaque'];family=row['family'];case=source['cases'][i]
    count=len(source['records'][family]['palette']['rgb8'])
    maxError=max(maxError,*[abs(float(initial[i,c])-decode(a[c]/255)) for c in range(3)],*[abs(float(final[i,c])-decode(b[c]/255)) for c in range(3)])
    assert list(pixels[i,:3])==b and pixels[i,3]==alpha
    assert abs(float(initial[i,3])-alpha/255)<1e-6 and initial[i,3]==final[i,3]
    # Compare uploaded Float32 seed values, not an unmaterialized C# expression
    # with potentially wider intermediate precision (original checker failure).
    targetK=row['kPrime'] if bound else row['k'];expectedClass=[f32(targetK/(count-1)),f32(case['g']),f32(float(f32(.4))+i*float(f32(.001))),f32(.7)]
    if list(classes[i])!=expectedClass:metadataMismatches.append({'i':i,'expected':expectedClass,'actual':classes[i].tolist()})
    expectedFactor=[1,1,1,f32(.6)] if bound else [f32(.3),f32(.7),f32(.4),f32(.6)]
    assert list(factors[i])==expectedFactor
    if bound:
        palette=source['records'][family]['palette']['rgb8'];assert b==palette[row['kPrime']]
        if row['k']==row['kPrime']:
            assert list(join[i,:3])==[1,0,1];oldCount+=1
        else:changed+=1
    else:
        assert np.array_equal(join[i],initial[i]) and np.array_equal(final[i],initial[i])
        if row['sourceSampleId']is not None:sourceExcluded+=1
    rgbExpected.append(a+[alpha])
assert not metadataMismatches,metadataMismatches
assert maxError<1e-6 and oldCount==d['oldEqualsCorrectedStressCount'] and d['ownedResourcesReleased'] and not d['stateChanges']
for variant,record in zip(d['variants'],source['records']):
    assert variant['independent'] and variant['baseK']==variant['paletteChangedK'] and variant['changedK']!=variant['baseK']
    assert variant['palette']['rgb8']!=record['palette']['rgb8']
def console(name):return load(name).get('data',{}).get('logs',[])
key=lambda r:tuple(r.get(k,'') for k in ['type','message','stackTrace'])
extra=Counter(map(key,console('CONSOLE_gpu_AFTER.json')))-Counter(map(key,console('CONSOLE_gpu_BEFORE.json')))
new=[{'type':k[0],'message':k[1],'count':v}for k,v in extra.items()];assert not [x for x in new if x['type'].lower()in['warning','error','exception','assert']]
finalImage=Image.frombytes('RGBA',(n,1),(R/'FINAL58.rgba').read_bytes());finalImage.save(R/'FINAL58.png');finalImage.resize((n*8,8),Image.Resampling.NEAREST).save(R/'FINAL58_8x.png')
panel=Image.new('RGB',(650,164),(28,28,30));draw=ImageDraw.Draw(panel)
for y,label,values in [(18,'Original UV colour',[s.get('sourceRGB8',[17,93,141])+[d['rows'][i]['nativeAlpha8']] for i,s in enumerate(source['cases'])]),(58,'Initial LUT',rgbExpected),(98,'Final LUT',pixels.tolist())]:
    draw.text((8,y+7),label,fill='white');im=Image.frombytes('RGBA',(n,1),bytes(c for row in values for c in row)).resize((n*8,24),Image.Resampling.NEAREST).convert('RGB');panel.paste(im,(130,y))
draw.text((130,135),'63 original UV samples + 1 unbound sentinel; NOT a character render',fill='white');draw.text((130,149),'Final join stress: 52 unchanged-q inputs deliberately poisoned before LUT',fill='white');panel.save(R/'SOURCE_INITIAL_FINAL58.png')
result={'gpuOutputVerified':True,'samples':n,'opaqueBound':oldCount+changed,'oldEqualsCorrectedForcedLUT':oldCount,'changedCorrectedIndex':changed,'partialSourcePreserved':sourceExcluded,'unboundSentinelPreserved':1,
    'sRGBRGBAExact':n,'paletteOutsideBoundOpaque':0,'maxLinearError':maxError,'metadataFloat32Exact':n,'alphaExact':n,'factorExact':n,
    'originalCSharpReportFlag':d['gpuPass'],'originalCSharpCheckerFalsePositiveCount':d['classMismatches'],
    'checkerCorrection':'Expected depth must be rounded to uploaded Float32 before equality. Saved class data matches all64 Float32 seeds; original GPU report is preserved and not rewritten.',
    'gpuReexecutedForChecker':False,'correctedCSharpSavedDataCheckPassed':recheck['passed'],'newConsoleWarningsOrErrors':new,'stateChanges':d['stateChanges'],'resourcesReleased':d['ownedResourcesReleased'],
    'sourceAndGPUInputLimit':'Original primitive UV samples plus diagnostic g/kPrime; not live renderer visible cells. Final join has an explicit negative control, not uninterrupted candidate frame flow.',
    'memoryDelta':{k:d['memoryAfter'][k]-d['memoryBefore'][k]for k in d['memoryBefore']if k!='utc'},
    'texture2DIdentitiesSame':d['before']['texture2DIds']==d['after']['texture2DIds'],'rtIdentitiesSame':d['before']['rtIds']==d['after']['rtIds'],
    'sourceSHA256':hashlib.sha256((R/'SOURCE58.json').read_bytes()).hexdigest()}
(R/'VERIFIED58.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
