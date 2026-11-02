"""Reuse111/2.2 source-form and109 source-ID history on113's COMPLETE tie pool.
No new weights or fixed eye size; source absence remains unmeasured.
"""
from pathlib import Path
from fractions import Fraction
import sys,json
import numpy as np
from paths114 import H,R,folder
P=folder('113')
for key in['109','110','22','111','113']:sys.path.insert(0,str(folder(key)))
from inputs113 import load_packets,buffer
from analyse111 import source_fields,source_components
from form22 import rank_source
from identity110 import histogram
from history109 import rank as history_rank
from oracle113 import subsets,scopes,interval,K,F
from trace114 import read
def complete_pool(path,owner,width):
    frame=buffer(path/'REGION113-frame.f32').reshape(64,4);cells=buffer(path/'REGION113-cells.f32').reshape(512,7,4);tags=buffer(path/'REGION113-tags.f32').reshape(512,4).view(np.uint32);gpu=buffer(path/'REGION113-best.f32').reshape(2,3,4);e=owner-1;header=frame[e*32].view(np.uint32);points=[c for c in range(len(cells))if cells[c,3,0]==owner and cells[c,5,0]==1 and cells[c,0,0]+cells[c,0,2]>0];nb=[]
    for c in points:nb.append(sum(1<<p for p,n in enumerate(points)if abs(c%width-n%width)+abs(c//width-n//width)==1))
    sc=scopes(cells,tags,owner,width,points);aa,bb=(subsets(cells,tags,points,p,sc,nb)for p in[0,1]);mass=frame[e*32+1];active=frame[e*32+2].view(np.uint32);canvas=frame[e*32+3,0];target=tuple(np.r_[gpu[e,0],float(gpu[e,2].view(np.uint32)[0])]);found=[]
    for am,ac,ak,an,ad in aa:
        for bm,bc,bk,bn,bd in bb:
            if am&bm:continue
            score=(F((int(active[0])&~ac).bit_count()+(int(active[1])&~bc).bit_count()),interval(F(an+bn)*K,F(mass[0]+mass[2]),F(mass[1]+mass[3])).item(),F(interval(F(an)*K,mass[0],mass[1])+interval(F(bn)*K,mass[2],mass[3])),max(F(F(canvas+ad)+bd),0),(int(active[2])&~(ak|bk)).bit_count())
            if tuple(map(float,score))==target:found.append([1 if am&(1<<p)else 2 if bm&(1<<p)else 0 for p in range(len(points))])
    assert len(found)==int(gpu[e,2].view(np.uint32)[1]),'Pool must enumerate all optima, not an arbitrary cap'
    return [(c//width,c%width)for c in points],found,tuple(map(float,target))
def transport(path,owner,reg,source):
    # analyse111.source_components already fixed the4x nearest/rest-ID issue.
    # This caller explicitly supplies the actual8x dense113 source planes.
    m,a,v=source_fields(path)
    from io109 import joint_arrays
    lo,*_=joint_arrays(a,v);ctx={'projectionX':{int(q['owner']):np.asarray(q['x'])for q in reg['projection']},'projectionY':{int(q['owner']):np.asarray(q['y'])for q in reg['projection']}}
    bank={(k['owner'],k['part'],k['x'],k['y']):np.array(k['RGB8'])for k in source['keys']};groups={(k['owner'],k['part'],k['x'],k['y']):k['componentBit']for k in source['keys']};_,_,records,bad=source_components(ctx,a,lo,owner,bank,groups);assert not bad and all(r['sourceKeyUnique']for r in records)
    maps={};expected={};available={}
    for r in records:
        key=tuple(r['sourceKeys'][0]);part=1 if r['part']==1 else 2;y,x=r['cellYX'];weight=Fraction(r['certainWeight']);q=maps.setdefault((y,x,part),{});q[key]=q.get(key,Fraction(0))+weight;available[key]=Fraction(1);w=expected.setdefault(key,[Fraction(0),Fraction(0),Fraction(0)]);yy,xx=r['fineYX'];w[0]+=weight;w[1]+=weight*Fraction(2*xx+1,16);w[2]+=weight*Fraction(2*yy+1,16)
    expected={k:(v[1]/v[0],v[2]/v[0])for k,v in expected.items()}
    return maps,available,expected,records
def encode(h):return [{'key':list(k),'weight':str(v)}for k,v in sorted(h.items())]
def main():
    _,packets=load_packets(P);source=read(P/'SOURCE113.json');reg=read(H/'REGISTRATION_CURRENT102.json');rows=[]
    for index in[2,6]:
        entry,path=packets[index];owner=2;meta=read(path/'RAW_MANIFEST.json');width=meta['forward102']['canonicalSize'][0]//4;points,layouts,target=complete_pool(path,owner,width);maps,available,expected,records=transport(path,owner,reg,source);form,detail=rank_source(layouts,points,maps,available,available.copy(),expected)
        prev_entry,prev=packets[index-1];pmaps,pavail,_,_=transport(prev,owner,reg,source);pid=buffer(prev/'curve-identity.f32').reshape(-1,4);pwidth=read(prev/'RAW_MANIFEST.json')['forward102']['canonicalSize'][0]//4;ppoints=[(i//pwidth,i%pwidth)for i in range(len(pid))];plabels=[1 if r[0]==1 and r[1]==owner else 2 if r[0]==4 and r[1]==owner else 0 for r in pid];prior=histogram(ppoints,plabels,pmaps)
        hist_winners,_,hist=history_rank(layouts,[prior],maps,available,owner,{'points':points})
        vectors=detail['sourceFormDimensions'];trulyEqual=all(vectors[i]==vectors[form[0]]for i in form)
        selected=sorted(set(form)&set(hist_winners))if len(form)>1 and trulyEqual else form
        # History must not choose between a source-form tradeoff, and the
        # previous captured pose is not proof of adjacent-frame stability.
        if not selected:selected=form
        diff=[{'canonicalXY':[x,y],'labels':[v[i]for v in layouts],'sourceKeys':{str(p):encode(maps.get((y,x,p),{}))for p in[1,2]}}for i,(y,x)in enumerate(points)if len({v[i]for v in layouts})>1]
        rows.append({'sourceId':entry['sourceId'],'frame':entry['frame'],'owner':owner,'fullOptimalPoolCount':len(layouts),'poolIsCompleteNotCap':True,'runtime113SourceKeyCountPenaltyOnly':True,'runtime113RelativeForm':False,'runtime113History':False,'samePrimary113Score':list(target),'pointsYX':points,'layouts':layouts,'difference':diff,'reusedForm111Winners':form,'sourceFormDetail':detail,'historyOnlyDiagnosticWinners':hist_winners,'historyDetail':hist,'previousSourceId':prev_entry['sourceId'],'frameGap':entry['frame']-prev_entry['frame'],'previousCapturedSourceIDHistogram':encode(prior),'currentFormWinnersHaveIdenticalVectors':trulyEqual,'combinedExistingCriteriaWinners':selected,'currentAvailableSourceKeys':encode(available),'actualDenseSourceRecords':len(records),'sourceSampleScale':8,'allSourceKeysUniqueAndRGB8Checked':True,'runtimeApplied':False})
    (H/'TIES114.json').write_text(json.dumps({'rows':rows,'newWeights':False,'newCellBudgets':False,'unmeasuredPairErrorNotZero':True,'actualTemporalStabilityClaim':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps([{'frame':r['frame'],'pool':r['fullOptimalPoolCount'],'difference':r['difference'],'form':r['reusedForm111Winners'],'historyDiagnostic':r['historyOnlyDiagnosticWinners'],'combined':r['combinedExistingCriteriaWinners'],'vectors':r['sourceFormDetail']['sourceFormDimensions']}for r in rows],ensure_ascii=False))
if __name__=='__main__':main()
