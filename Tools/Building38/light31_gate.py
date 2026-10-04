"""N31 actual GPU/CPU shadow-loss gate; never creates GPU or Play observations."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOAT_TOLERANCE = 1e-5
PARITY_TOLERANCE = 1e-6
LUMA = (.2126729, .7151522, .0721750)


def cases():
    z = (0., 0., 0.); a = (.4, .15, .04); w = (1., 1., 1.)
    result = {}
    def add(name, albedo, e, loss=z, stepped=z):
        result[name] = (albedo, e, loss, stepped)
    for i, e in enumerate(((.08,)*3, (.2,)*3, (.5,)*3, (.03,.045,.085), (.4,.1,.03), (.2,0.,0.))):
        add(f'P0{i}', a, e)
    add('Z00',a,z);add('Z01',z,(.1,.2,.3),(.2,.1,0.),(.22,)*3)
    add('Z02',a,z,(.3,.2,.1))
    add('C00',w,(.3,.1,.3));add('C01',w,(.1,.1,.3),(.2,0.,0.))
    for i, v in enumerate((1.,.75,.5,0.)):
        add(f'M0{i}',a,(.198+.04*v,)*3,(.04*(1-v),)*3)
    add('S00',a,(.03,.045,.085),(.05,0.,0.))
    add('S01',a,(.03,.045,.085),(.05,0.,0.),(.22,)*3)
    for i, level in enumerate((.1199,.1201,.3999,.4001)):
        add(f'T0{i}',a,(level*.5,)*3,(level*.5,)*3)
    add('E00',a,(1e-7,)*3)
    return result


def vector(v):
    return isinstance(v,list) and len(v)==3 and all(isinstance(x,(int,float)) and
        not isinstance(x,bool) and math.isfinite(x) for x in v)


def reference(a,e,loss,stepped):
    opened=[max(x,0.)+max(l,0.) for x,l in zip(e,loss)]
    peak=max(opened); y=sum(x*l for x,l in zip(opened,LUMA))
    q=.55 if y<.12 else (.78 if y<.4 else 1.)
    return [aa*((q*max(x,0.)/peak if peak>1e-6 else 0.)+max(s,0.))
            for aa,x,s in zip(a,e,stepped)]


def error(a,b):
    return max(abs(x-y) for x,y in zip(a,b))


def read(path):
    def reject(value):raise ValueError('Nonfinite JSON number: '+value)
    data=json.loads(path.read_text(encoding='utf-8-sig'),parse_constant=reject)
    if not isinstance(data,dict):raise ValueError('JSON object required: '+str(path))
    return data


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def fixture(output):
    receipt=read(output/'fixture.json'); expected=cases(); samples=receipt.get('samples',[])
    checks={'linear_color_space':receipt.get('colorSpace')=='Linear',
            'fixture_shader_errors_zero':type(receipt.get('shaderErrors')) is int and receipt['shaderErrors']==0}
    records={}; invalid=[]; mismatches=[]; max_cpu=0.;max_legacy=0.;max_parity=0.
    keys=('albedo','shadowedIrradiance','shadowLoss','steppedIrradiance','gpu','legacyGpu')
    if not isinstance(samples,list):raise ValueError('Fixture samples list required')
    for i,s in enumerate(samples):
        if not isinstance(s,dict) or s.get('id') not in expected or s.get('id') in records or not all(vector(s.get(k)) for k in keys):
            invalid.append(i);continue
        ident=s['id'];inputs=expected[ident]
        if any(error(s[k],v)>PARITY_TOLERANCE for k,v in zip(keys[:4],inputs)):invalid.append(i);continue
        records[ident]=s
        cpu=reference(*inputs);legacy=reference(inputs[0],inputs[1],(0.,)*3,inputs[3])
        ce=error(s['gpu'],cpu);le=error(s['legacyGpu'],legacy)
        max_cpu=max(max_cpu,ce);max_legacy=max(max_legacy,le)
        if ce>FLOAT_TOLERANCE or le>FLOAT_TOLERANCE:mismatches.append({'id':ident,'cpuError':ce,'legacyError':le})
        if ident.startswith('P'):
            max_parity=max(max_parity,error(s['gpu'],s['legacyGpu']))
    complete=len(samples)==len(expected) and set(records)==set(expected) and not invalid
    checks.update({'explicit_cases_complete':complete,'gpu_matches_cpu':complete and not mismatches,
                   'no_shadow_legacy_parity':complete and max_parity<=PARITY_TOLERANCE})
    if complete:
        checks['black_and_zero_zero']=all(max(abs(x) for x in records[i]['gpu'])<=PARITY_TOLERANCE for i in ('Z00','Z01','Z02','E00'))
        opened=records['C00']['gpu'];shadowed=records['C01']['gpu']
        checks['red_only_occluded']=shadowed[0]<opened[0]-PARITY_TOLERANCE and error(shadowed[1:],opened[1:])<=PARITY_TOLERANCE
        checks['visibility_monotonic_same_open_Q']=all(records[f'M0{i+1}']['gpu'][c]<=records[f'M0{i}']['gpu'][c]+PARITY_TOLERANCE
            for i in range(3) for c in range(3))
        checks['weak_shadow_survives_same_Q']=records['M00']['gpu'][0]-records['M03']['gpu'][0]>.1*.4
        a=expected['S00'][0];delta=[x-y for x,y in zip(records['S01']['gpu'],records['S00']['gpu'])]
        checks['moving_stepped_difference_preserved']=error(delta,[x*.22 for x in a])<=PARITY_TOLERANCE
        checks['open_Q_thresholds_exercised']=records['T01']['gpu'][0]>records['T00']['gpu'][0]+PARITY_TOLERANCE and records['T03']['gpu'][0]>records['T02']['gpu'][0]+PARITY_TOLERANCE
    else:
        for name in ('black_and_zero_zero','red_only_occluded','visibility_monotonic_same_open_Q','weak_shadow_survives_same_Q',
                     'moving_stepped_difference_preserved','open_Q_thresholds_exercised'):checks[name]=False
    result={'checks':checks,'passed':all(checks.values()),'metrics':{'caseCount':len(samples),'expectedCaseCount':len(expected),
            'maximumCPUError':max_cpu,'maximumLegacyCPUError':max_legacy,'maximumNoShadowParityError':max_parity,
            'invalidSampleIndices':invalid,'mismatches':mismatches},'art_approval_claimed':False}
    write(output/'fixture-validation.json',result)
    return result


def actual(output):
    # Field names are the root observer's measured values, never inferred from file existence.
    before=read(output/'before/observation.json');after=read(output/'after/observation.json')
    checks={'actual_play_observation':all(r.get('playMode') is True for r in (before,after)),
            'same_geometry':all(r.get('sameGeometry') is True for r in (before,after)) and bool(after.get('geometry')) and before.get('geometry')==after.get('geometry'),
            'same_lighting':all(r.get('sameLighting') is True for r in (before,after)) and bool(after.get('lighting')) and before.get('lighting')==after.get('lighting'),
            # Separate Play runs create distinct entities. Each phase must retain its actual entities.
            'same_player_camera_within_each_phase':all(r.get('samePlayer') is True and r.get('sameCamera') is True for r in (before,after)),
            'integer_2px':all(isinstance(r.get('screenPixelsPerCell'),(int,float)) and abs(r['screenPixelsPerCell']-2)<=FLOAT_TOLERANCE for r in (before,after)),
            'same_camera_angles':all(isinstance(after.get(k),(int,float)) and isinstance(before.get(k),(int,float)) and abs(after[k]-before[k])<=PARITY_TOLERANCE for k in ('cameraPitch','cameraYaw')),
            'book_shadow_max_byte_at_least_8':type(after.get('bookMaxByte')) is int and after['bookMaxByte']>=8,
            'book_shadow_stronger_than_before':type(after.get('bookMaxByte')) is int and type(before.get('bookMaxByte')) is int and after['bookMaxByte']>before['bookMaxByte'],
            'book_shadow_actual_changed_pixels':type(after.get('bookChangedPixels')) is int and after['bookChangedPixels']>0,
            'lamps_control_observed':type(after.get('lampsControlPixels')) is int and after['lampsControlPixels']>0,
            'moving_control_observed':type(after.get('movingControlPixels')) is int and after['movingControlPixels']>0,
            'controls_restored':all(r.get('controlsRestored') is True for r in (before,after)),
            'actual_shader_errors_zero':all(type(r.get('shaderErrors')) is int and r['shaderErrors']==0 for r in (before,after))}
    natural=after.get('natural',[])
    checks['actual_day_night_natural_recorded']=isinstance(natural,list) and len(natural)==2 and {r.get('hour') for r in natural}=={12,21} and all(
        isinstance(r.get('ambientIntensity'),(int,float)) and math.isfinite(r['ambientIntensity']) and bool(r.get('ambientMode')) and
        isinstance(r.get('directional'),list) and bool(r['directional']) and
        all(isinstance(r.get(k),dict) and all(isinstance(r[k].get(c),(int,float)) and math.isfinite(r[k][c]) for c in ('r','g','b','a'))
            for k in ('ambientSky','ambientEquator','ambientGround')) for r in natural)
    hashes=read(output/'baseline-hashes.json')
    checks['source_hashes_preserved']=bool(hashes) and isinstance(hashes,dict) and all((ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in hashes.items())
    return checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--fixture-only',action='store_true')
    args=parser.parse_args();output=Path(args.output).resolve();result=fixture(output/'fixture')
    if not args.fixture_only:
        result['checks'].update(actual(output));result['passed']=all(result['checks'].values());write(output/'validation31.json',result)
    print(json.dumps({'passed':result['passed'],'checks':result['checks'],'metrics':result['metrics']},ensure_ascii=False))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
