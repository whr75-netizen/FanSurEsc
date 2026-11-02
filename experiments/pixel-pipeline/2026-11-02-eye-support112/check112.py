"""Small explicit failure/invalidation checks, plus saved actual-frame facts."""
import copy,json,os
import numpy as np
os.environ['PIXEL111_FROZEN_INPUTS']='1'
import support112 as module
from source112 import Source,HERE,P111,load,packet_list,read
from support112 import Support

class ModifiedSource:
    def __init__(self,s,change=None):self.base=s;self.g=copy.deepcopy(s.g);self.change=change
    def accessor(self,i):
        a=self.base.accessor(i)
        return self.change(i,a)if self.change else a
    def binding(self):
        b=self.g['extensions']['VRMC_vrm']['expressions']['preset']['blink']['morphTargetBinds'][0];node=self.g['nodes'][b['node']];return b,node,self.g['meshes'][node['mesh']]
    map_to_capture=Source.map_to_capture

def fails(fn):
    try:fn()
    except(AssertionError,KeyError):return True
    return False

def main():
    s=Source();_,paths=packet_list();c=load(paths[3]);a=Support(s,c);tests=[]
    def check(name,value):assert value,name;tests.append(name)
    check('VRM unilateral binding matches exactly one complete registered ring',a.bindings[1]['expression']=='blinkLeft'and a.bindings[2]['expression']=='blinkRight')
    check('Source glTF/capture primitive identity, UV and winding match',a.m['permutation']==[2,1,0]and a.m['uvErrors']['flipV']==0)
    check('All20 existing native iris/white point attachments are present and verified',len(a.attachedCells)==20 and max(c['UVError']for c in a.attachedCells)<1e-7)
    M=np.array(read(paths[3].parent/'REGISTRATION_CURRENT102.json')['sourceToRestHead']).reshape(4,4,order='F');original=np.c_[a.m['positions']*[-1,1,1],np.ones(len(a.m['positions']))]@M.T;off=a.m['faceVertexOffset'];err=float(abs(original[:,:3]-c['rest'][off:off+len(original)]).max());check('Source handedness and Head-bind rest mapping preserved',err<1e-7)
    bad=ModifiedSource(s);del bad.g['extensions']['VRMC_vrm']['expressions']['preset']['blinkLeft'];check('Missing source semantics rejected with no nearest-eye fallback',fails(lambda:Support(bad,c)))
    bad=ModifiedSource(s);bad.g['extensions']['VRMC_vrm']['expressions']['preset']['blinkRight']['morphTargetBinds'][0]['index']=13;check('Bilateral morph cannot impersonate a unilateral lid owner',fails(lambda:Support(bad,c)))
    uvID=a.m['meshData']['primitives'][0]['attributes']['TEXCOORD_0']
    def wrong_uv(i,x):
        if i==uvID:x[0,0]+=.01
        return x
    check('UV/source binding mismatch fails before cache adoption',fails(lambda:Support(ModifiedSource(s,wrong_uv),c)))
    target=a.m['meshData']['primitives'][0]['targets'][a.bindings[2]['morphTarget']]['POSITION']
    def moved(i,x):
        if i==target:x*=2
        return x
    b=Support(ModifiedSource(s,moved),c);check('Morph content change invalidates static source signature',b.key!=a.key)
    realbank=module.bank_data;bank,groups=realbank()
    try:
        module.bank_data=lambda:({k:np.array([0,0,0])for k in bank},groups)
        check('Palette RGB changes do not change geometric affiliation',Support(s,c).key==a.key)
    finally:module.bank_data=realbank
    q=copy.deepcopy(c);q['triOwners']=q['triOwners'].copy();q['triOwners'][:]=1
    check('Nearest-eye face tag is not used as semantic ownership',Support(s,q).key==a.key)
    report=read(HERE/'AUDIT112.json');check('24 saved current-geometry states checked',report['sameFrameRecords']==24)
    check('Full Close has no iris/white even though skin ring has area',all(x['iris']==x['white']==0 for x in report['fullClose']['sourceMass'])and all(x>0 for x in report['fullClose']['nonzeroNativeRingArea'].values()))
    check('Hair ON/OFF leaves intrinsic canonical allocation unchanged',report['hairOnOffRestoredCanonicalEqual'])
    critical=report['critical'];check('Minimum white counterexample is solid native skin, not missing alpha',len(critical['blockingTriangles'])==9 and all(x['sourceAlphaAllOpaque']for x in critical['blockingTriangles']))
    check('Unknown skin is never converted to transparent',all(x['occlusionOwnership'].startswith('UNRESOLVED')and 'no occluder removed'in x['safeAction']for x in critical['blockingTriangles']))
    cache=a.cache();check('Blink-moved skin joins both eyes and cannot be a per-eye lid mask',len(cache['combinedBlinkAllMovingSkinEdgeComponents'])==1 and all(v==24 for v in cache['combinedBlinkAllMovingSkinEdgeComponents'][0]['ringContacts'].values()))
    check('Blink also moves eyebrows, not only lids',cache['parts'][5]['blinkMovingVertices']==50)
    (HERE/'CHECK112.json').write_text(json.dumps({'passed':len(tests),'tests':tests,'sourceRestMaxAbsoluteErrorMetres':err,'runtimeJointAllocationTested':False,'currentUnityStateQueried':False,'noNewUnityCalls':True},indent=2)+'\n',encoding='utf8')
    # Refresh the metadata hash after final key implementation. No new frame run.
    (HERE/'AFFILIATION_CACHE112.json').write_text(json.dumps(cache,indent=2)+'\n',encoding='utf8')
    from audit112 import picture
    picture(s,a,critical)
    print(json.dumps({'passed':len(tests),'runtimeReady':False,'restErrorMetres':err}))

if __name__=='__main__':main()
