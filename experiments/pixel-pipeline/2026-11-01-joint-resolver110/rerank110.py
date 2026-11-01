"""Reuses completed CSP/footprints. No field rerender or repeated mesh solve."""
import gzip,json
from pathlib import Path
from fields110 import H,read,template
from stored110 import P108,P109
from identity110 import transport,rank,rank_with_relative,observed_key_centres,encode
from reconstruct110 import recover

def main():
    rows=read(P108/'INPUT108.json');domain,templates=template();cache=read(P109/'NATIVE_CACHE109.json');prior={1:[],2:[]};scope={1:None,2:None};out=[]
    for path in sorted(H.glob('frame*-eye*-result.json'),key=lambda p:(int(p.name.split('-')[0][5:]),p.name)):
        q=read(path);f=q['metadata']['frame'];owner=q['owner'];row=next(v for v in rows if v['name']=='actual107-frame'+str(f));ctx,_,_=recover(row,domain,templates)
        with gzip.open(H/f'frame{f}-eye{owner}-footprint.json.gz','rt',encoding='utf8')as fp:data=json.load(fp)
        ids,available,canonical,check=transport(row,owner,ctx,data['footprints'],data['reference'],domain,cache);ss=(ctx['manifest']['forward102']['scope'],cache['cacheKey'])
        if scope[owner]!=ss:prior[owner]=[];scope[owner]=ss
        if q.get('solutions'):
            old,_,_=rank(q['solutions'],q['cells'],ids,available,canonical,prior[owner]);chosen,hist,info=rank_with_relative(q['solutions'],q['cells'],ids,available,canonical,prior[owner],observed_key_centres(row,owner));q['histogramOnlyConditionalWinners']=old;q['selectedIndicesWithinEnumeratedOptima']=chosen;q['sourceIdentity']=info|check;q['sourceHistograms']=[encode(v)for v in hist];prior[owner]=hist
        else:prior[owner]=[]
        # The map is an offline hypothesis; no final pixel is certified merely
        # because its per-part ID, geometric score or tied witness was chosen.
        q['adopted']=False;path.write_text(json.dumps(q,indent=2)+'\n',encoding='utf8');out.append(q)
    (H/'RESULTS110.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'states':len(out),'conditionalChoices':[(q['metadata']['frame'],q['owner'],len(q.get('selectedIndicesWithinEnumeratedOptima',[])))for q in out]}))
if __name__=='__main__':main()
