"""Completed live packet integrity and final colour/source invariants only."""
from pathlib import Path
import hashlib,json
import numpy as np
from inputs113 import plane,buffer,load_packets
H=Path(__file__).resolve().parent
def same(a,b):return np.array_equal(a,b)
def main():
    _,ps=load_packets(H);source=json.loads((H/'SOURCE113.json').read_text(encoding='utf8'))
    rows=[]
    for entry,path in ps:
        m=json.loads((path/'RAW_MANIFEST.json').read_text(encoding='utf8'))
        assert m['sourceId']==entry['sourceId']and m['frameIndex']==entry['frame']and m['mainSerial']==entry['serial']
        assert hashlib.sha256((path/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(path/'RAW_COMPLETE76.marker').read_text().strip()
        assert m['algorithmValid113']and m['regionErrorFlags113']==0
        assert m['runtimeShaderName113']=='ForwardEye113(Clone)'and m['forward102']['region113']['runtimeGPUReadbacks']==0
        motion=m['motion82'];error=motion['evaluatedVsOwnedBakeMax']if'evaluatedVsOwnedBakeMax'in motion else motion['evaluatedCloseError111']
        assert m['frameUnchangedDuringReadback']and error==0
        final=plane(path/'F-FinalRGBA.plane')[1];owner=plane(path/'F-FinalOwner.plane')[1]
        palette_errors=[];counts={}
        for eye in[1,2]:
            for part,role in[(1,2),(4,5),(6,7)]:
                selected=final[(owner[...,0]==role)&(owner[...,1]==eye)];counts[f'{eye}/{part}']=len(selected)
                keys=source['lidPalette']if part==6 else source['keys']
                expected=np.asarray([k['linear']for k in keys if k['owner']==eye and(part==6 or k['part']==part)],np.float32)
                for c in selected:
                    if c[3]!=1 or not np.any((expected==c[:3]).all(1)):palette_errors.append([eye,part,c.tolist()])
        assert not palette_errors,'Final GPU eye RGB is not an exact finite source LUT value'
        rows.append({'sourceId':entry['sourceId'],'finalEyeCellsByOwnerPart':counts,'finalLinearPaletteErrors':len(palette_errors)})
    def buf(i,name):return buffer(ps[i][1]/name)
    hair_parts=all(same(buf(9,'curve-identity.f32')[:,:2],buf(i,'curve-identity.f32')[:,:2])for i in[10,11])
    hair_colours=all(same(buf(9,'curve-colour.f32'),buf(i,'curve-colour.f32'))for i in[10,11])
    reopen=all(same(buf(0,f),buf(8,f))for f in['curve-identity.f32','curve-colour.f32','curve-decision.f32','REGION113-cells.f32'])
    assert hair_parts and hair_colours and reopen
    close_iw=sum(n for k,n in rows[4]['finalEyeCellsByOwnerPart'].items()if k.endswith(('/1','/4')))
    assert close_iw==0,'Complete Close must not resurrect I/W via cache'
    out={'passes':True,'liveFrames':12,'rows':rows,'hairONOFFCanonicalPartOwnerEqual':hair_parts,'hairONOFFCanonicalRGBEqual':hair_colours,'hairONOFFRawDepthIdentityEqual':False,'hairDepthCaveat':'Distinct sourceId/frame; canonical depth floats differ. No assertion that all raw geometry bytes equal.','reopenExactCanonicalInputsAndOutputs':reopen,'completeCloseFinalIrisWhiteCells':close_iw,'sourceFormHistoryImplemented':False,'fullFaceOrOutlineValidated':False}
    (H/'CHECK113.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in out.items()if k!='rows'},ensure_ascii=False))
if __name__=='__main__':main()
