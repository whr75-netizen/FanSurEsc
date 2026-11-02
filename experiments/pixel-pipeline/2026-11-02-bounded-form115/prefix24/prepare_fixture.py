"""Immutable saved113 source + CPU oracles for four unchanged kernel stages."""
from pathlib import Path
import hashlib,json,struct,sys,uuid
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT))
from direct_support24 import P,sibling
sys.path.insert(0,str(P))
from inputs113 import load_packets,buffer
from oracle113 import subsets as independent_subsets,scopes as independent_scopes,connected as graph_connected
F=np.float32;U=np.uint32;K=F(65536)
def fb(x):return int(np.array([F(x)],'<f4').view('<u4')[0])
def fv(x):return np.array([x],'<u4').view('<f4')[0]
def group_invalid():return U([fb(F('3.402823e38'))]*4+[0]*4+[0xffffffff,0,0,0])
def less(a,b):
    x=a[:4].view('<f4');y=b[:4].view('<f4')
    for i in range(4):
        if x[i]!=y[i]:return x[i]<y[i]
    if fv(a[10])!=fv(b[10]):return fv(a[10])>fv(b[10])
    return a[8]<b[8]
def merge(a,b):
    if a[9]==0:return b.copy()
    if b[9]==0:return a.copy()
    if less(a,b):return a.copy()
    if less(b,a):return b.copy()
    a=a.copy();a[4:8]=[a[4]&b[4],a[5]|b[5],a[6]&b[6],a[7]|b[7]];a[9]+=b[9];return a
def distance(v,lo,hi):return F(lo-v)if v<lo else F(v-hi)if v>hi else F(0)

def main():
    module=json.loads((HERE/'MODULE.json').read_text());_,packets=load_packets(P)
    entry,path=next((e,p)for e,p in packets if e['frame']==103)
    meta=json.loads((path/'RAW_MANIFEST.json').read_text());assert meta['mainSerial']==10
    cells=buffer(path/'REGION113-cells.f32').reshape(512,7,4).copy()
    tags=buffer(path/'REGION113-tags.f32').view('<u4').reshape(512,4).copy()
    frame=buffer(path/'REGION113-frame.f32').view('<u4').reshape(2,32,4)[[1,0]].copy()
    points=buffer(path/'REGION113-points.f32').view('<u4').reshape(2,24,4)[[1,0]].copy()
    old_best=buffer(path/'REGION113-best.f32').view('<u4').reshape(2,12)[[1,0]].copy()
    assert frame[0,0].tolist()==[9,5,6,0]
    point_cells=[int(v)for v in points[0,:9,0]];neighbours=[int(v)for v in points[0,:9,3]]
    sc=[int(v)for v in frame[0,4:20,0]]
    assert independent_scopes(cells,tags,2,18,point_cells)==sc
    table=np.zeros((16384,8),'<u4')
    for part in range(2):
        valid=[]
        for state in range(64):
            out=np.zeros(8,'<u4')
            if state<(1<<int(frame[0,0,part+1])):
                mask=component=keys=n=0;cost=F(0);direct=F(0)
                for p,cell in enumerate(point_cells):
                    index=int(points[0,p,part+1])
                    if index==0xffffffff or not state&(1<<index):continue
                    mass=cells[cell,0];tag=tags[cell];mask|=1<<p;n+=1;component|=int(tag[part]);keys|=int(tag[part+2])
                    cost=F(cost+F(F(F(K-mass[0])-mass[2])-mass[part*2]));direct=F(direct+mass[part*2])
                okay=all(not scope or graph_connected(mask&scope,neighbours)for scope in sc[part*8:part*8+8])
                out[:]=[mask,component,keys,n,fb(cost),int(okay),fb(direct),0]
                if okay:valid.append((mask,component,keys,n,cost))
            table[part*4096+state]=out
        independent=independent_subsets(cells,tags,point_cells,part,sc,neighbours)
        assert valid==independent,'Old subset fields must match independent113 oracle'
    group_rows=[];allstates=[];mass=frame[0,1].view('<f4');active=frame[0,2];canvas=fv(frame[0,3,0])
    for state in range(2048):
        a=table[state&31];b=table[4096+(state>>5)];g=group_invalid()
        if a[5] and b[5] and not(a[0]&b[0]):
            cost=F(F(canvas+fv(a[4]))+fv(b[4]));score=[F((int(active[0])&~int(a[1])).bit_count()+(int(active[1])&~int(b[1])).bit_count()),
                distance(F(a[3]+b[3])*K,F(mass[0]+mass[2]),F(mass[1]+mass[3])),
                F(distance(F(a[3])*K,mass[0],mass[1])+distance(F(b[3])*K,mass[2],mass[3])),max(cost,F(0))]
            g=U([fb(x)for x in score]+[a[0],a[0],b[0],b[0],(int(active[2])&~int(a[2]|b[2])).bit_count(),1,fb(F(fv(a[6])+fv(b[6]))),0])
        allstates.append(g)
    for start in range(0,2048,64):
        shared=[g.copy()for g in allstates[start:start+64]]
        stride=32
        while stride:
            for i in range(stride):shared[i]=merge(shared[i],shared[i+stride])
            stride//=2
        group_rows.append(shared[0])
    best=group_invalid()
    for g in group_rows:best=merge(best,g)
    assert best[4:8].tolist()==[12,12,130,130] and int(best[9])==1
    # Tree/sequential merge must not invent an enumeration-order winner.
    reverse=group_invalid()
    for g in reversed(allstates):reverse=merge(reverse,g)
    assert np.array_equal(best,reverse)
    final_best=old_best.copy();final_best[0]=best
    sentinel=F(-12345.25);output=np.full((4,144,4),sentinel,'<f4')
    for y in range(8):
        for x in range(8):
            cell=y*18+x;info=cells[cell,3];policy=cells[cell,5];owner=int(np.rint(info[0]));eye=0 if owner==2 else 1
            colour=np.zeros(4,'<f4');identity=colour.copy();decision=colour.copy();audit=colour.copy()
            if owner>0 and frame[eye,0,3]==0:
                if policy[0]==2:
                    lid=cells[cell,4]
                    if lid[3]>0:colour=np.r_[lid[:3],F(1)];identity[:]=[6,owner,lid[3],0];decision[:]=[6,113,0,0];audit[0]=3
                    else:audit[0]=-1
                elif policy[0]==1:
                    chosen=final_best[eye]
                    for k in range(int(frame[eye,0,0])):
                        if points[eye,k,0]!=cell:continue
                        bit=1<<k;is_i=bool(chosen[4]&bit);is_w=bool(chosen[6]&bit)
                        uncertain=bool(((chosen[5]^chosen[4])|(chosen[7]^chosen[6]))&bit)
                        if uncertain:decision[0]=-1;audit[0]=-2
                        elif is_i or is_w:
                            colour=cells[cell,1 if is_i else 2].copy();identity[:]=[1 if is_i else 4,owner,info[1 if is_i else 2],0];decision[:]=[1 if is_i else 4,113,0,0];audit[0]=1
                        break
            elif owner>0:decision[0]=-1;audit[:]=[-64,frame[eye,0,3],frame[eye,0,1],frame[eye,0,2]]
            output[:,cell]=np.array([colour,identity,decision,audit])
    folder=HERE/'fixture';folder.mkdir(exist_ok=True);items=[]
    def save(name,array,stage=0):
        data=array.tobytes();(folder/(name+'.bin')).write_bytes(data)
        items.append({'Name':name,'File':name+'.bin','Stage':stage,'Bytes':len(data),'Sha256':hashlib.sha256(data).hexdigest()})
    for name,array in [('cells',cells),('tags',tags),('frame',frame),('points',points),('old-best',old_best)]:save(name,array)
    save('subsets-I',table[:64],1);save('subsets-W',table[4096:4096+64],1);save('groups',np.array(group_rows,'<u4'),2);save('best',best,3)
    for i,name in enumerate(['colour','identity','decision','audit']):save(name,output[i],4)
    guid=hashlib.sha256(('Prefix24/'+module['sourceSHA256']).encode()).hexdigest()[:32]
    meta='fileFormatVersion: 2\nguid: '+guid+'\nComputeShaderImporter:\n  externalObjects: {}\n  preprocessorOverride: 0\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n'
    (HERE/'Prefix24.compute.meta').write_bytes(meta.encode())
    # One approved run identity, never recycled. CPU tests use separate temp roots.
    config=HERE/'CASE.json'
    if config.exists():run_id=json.loads(config.read_text())['RunId']
    else:run_id='prefix24-'+uuid.uuid4().hex
    case={'Schema':'prefix24/case/v1','SourceId':entry['sourceId'],'SourceFrame':103,'SourceSerial':10,'Width':18,'Height':8,'Owner':2,
          'RunId':run_id,'ShaderAssetPath':'Assets/EUnityValidation01/Direct24Prefix/Prefix24.compute','ShaderSha256':module['sourceSHA256'],'ShaderGuid':guid,
          'InputFiles':items,'Globals':json.loads((P/'GLOBAL_NAMES66.json').read_text())}
    # Normalize global DTO field names used by the small DataContract reader.
    case['Globals']=[{'Name':r['name'],'Type':r['type']}for r in case['Globals']]
    encoded=(json.dumps(case,indent=2)+'\n').encode();config.write_bytes(encoded)
    lock='''namespace Prefix24 {
public static class CaseLock24 {
 public const string ManifestSha="%s";
 public const string FixtureRoot=@"%s";
 public const string RunRoot=@"%s";
}
}
'''%(hashlib.sha256(encoded).hexdigest(),HERE,HERE/'runs'/run_id)
    (HERE/'CaseLock24.cs').write_bytes(lock.encode())
    report={'GPUOrUnityCalls':0,'sourceId':entry['sourceId'],'sourceFrame':103,'sourceSerial':10,'header':frame[0,0].tolist(),
            'oracleComparison':'96 source subsets old fields agree with independent113 oracle; complete2048 states; reverse-order merge same',
            'bestMasks':best[4:8].tolist(),'bestCount':int(best[9]),'caseSHA256':hashlib.sha256(encoded).hexdigest(),'bytes':sum(i['Bytes']for i in items),
            'noCPUWinnerUploadedToGPU':True,'notes':'Expected best is oracle data only. Stage3 must produce actual GPU best; stage4 reads only previous GPU receipt output.'}
    (HERE/'FIXTURE_BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
