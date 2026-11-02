"""Classify the 22 paired-coordinate counterfactuals from measured113 inputs.

Not a115 GPU capture. Do not turn unsupported carrier positions into occluders.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
def load114(name):
    local=H.parent/'eye-failures114'/name
    if local.exists():return json.loads(local.read_text(encoding='utf-8'))
    repo=H.parent/'2026-11-02-eye-failures114'
    direct=repo/name
    if direct.exists():return json.loads(direct.read_text(encoding='utf-8'))
    with zipfile.ZipFile(repo/'DATA114.zip')as z:
        names=[n for n in z.namelist()if Path(n).name==name]
        assert len(names)==1
        return json.loads(z.read(names[0]))
def main():
    data=load114('PAIRING_ALL114.json');rows=[]
    for frame in data['rows']:
        for c in frame['issues']:
            if not c['finalRGBAChanged']:continue
            old,new=c['oldFinal'],c['correctPointFinal']
            valid=c['correctPointCarrier16'];lo,hi=c['correctPointFaceInterval']
            assert lo==hi
            hits=[h for q in c['faceHits4x']for h in q['hits']]
            nonexempt=[h for h in hits if not h['exempt113']]
            if new['status']==-113:
                category='unresolved_hair_interval_canvas_fallback'
                verdict='Not a proven restoration: uncertainty includes missing destination carrier; canvas skin is fallback, not evidence that skin owns the pixel.'
            elif new['status']==-116:
                category='carrier_support_below_majority'
                verdict='Confirmed support shortage under centre sampling. Not evidence of actual occlusion; native coverage is clipping a selected feature.'
                assert not nonexempt and lo==valid and valid<8
            elif new['status']==-117 and valid==16:
                category='face_occlusion_under_explicit_12mm_policy'
                verdict='Coordinate correction follows current2.3 policy: actual opaque own-component hits exceed12mm. Model-scale policy, not new source colour or a universal ownership proof.'
                assert all(h['unilateralRingComponent']and h['depthGapMetres']>.012 for h in nonexempt)
            elif new['status']==-117:
                category='carrier_shortage_plus_one_real_face_hit'
                verdict='Eight unsupported positions plus one real non-exempt opaque hit leave7/16. Do not describe the whole-cell skin result as majority physical occlusion.'
                assert valid==8 and lo==7 and len(nonexempt)==1 and not nonexempt[0]['unilateralRingComponent']
            elif old['role']==4 and new['role']==7:
                category='lid_recovered_at_matched_destination'
                verdict='Matched carrier has8/16, visible8/16 and no hair. Supported recovery under the existing majority rule; aesthetic quality not certified.'
                assert valid==8 and lo==8 and c['correctPointHairInterval']==[0,0]
            elif old['role']==4 and new['role']>=12:
                category='definite_hair_at_matched_destination'
                verdict='Actual saved S4 hair data has a certain-majority foreground count. Hair identity/RGB are original recorded values.'
                assert c['correctPointHairInterval'][0]>=8
            elif old['role']>=12 and new['role']>=12:
                category='foreground_hair_source_reselection'
                verdict='Both outputs choose actual foreground hair. Exact query location changes which original hair surface wins the existing nearest-hair-depth policy; not an invented palette colour.'
                assert c['correctPointHairInterval'][0]>=8
            else:raise AssertionError((frame['frame'],c))
            rows.append({'sourceId':frame['sourceId'],'frame':frame['frame'],'mainXYBottomLeft':c['mainXY'],'canonicalXY':c['canonicalXY'],'part':c['part'],'owner':c['owner'],'category':category,'verdict':verdict,'oldFinal':old,'pairedPointCPUFinal':new,'validCarrier16':valid,'missingCarrier16':16-valid,'visibleFace16':[lo,hi],'actualBlockedAmongCarriers':valid-lo,'hairInterval16':c['correctPointHairInterval'],'nonExemptActualFaceHits':nonexempt})
    counts=dict(Counter(r['category']for r in rows))
    expected={'lid_recovered_at_matched_destination':4,'definite_hair_at_matched_destination':2,'foreground_hair_source_reselection':2,'face_occlusion_under_explicit_12mm_policy':2,'carrier_shortage_plus_one_real_face_hit':2,'carrier_support_below_majority':4,'unresolved_hair_interval_canvas_fallback':6}
    assert len(rows)==22 and counts==expected,(counts,expected)
    out={'schema':'paired-coordinate-classification115/v1','inputs':'Actual113 source geometry/alpha/S4 buffers; independent paired4x computation from114','notRuntime115Result':True,'existing12mmModelPolicyUnchanged':True,'counts':counts,'rows':rows}
    (H/'DELTA_CLASSIFICATION115.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'counts':counts},ensure_ascii=False))
if __name__=='__main__':main()
