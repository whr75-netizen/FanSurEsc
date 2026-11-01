"""Recheck frozen actual packets and restoration; does not call Unity or render."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
try: from reader68 import plane,camera
except ImportError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'apply-capture66'))
    from analyse_capture68 import plane,camera
HERE=Path(__file__).resolve().parent

def main():
    result=json.loads((HERE/'RESULT94.json').read_text()); summary=json.loads((HERE/'SUMMARY94.json').read_text()); checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    z=zipfile.ZipFile(HERE/'RAW94.zip')if (HERE/'RAW94.zip').exists()else None
    source=zipfile.Path(z)if z else None
    for row in result['frames']:
        p=source/f"frame-{row['frame']}"if source else Path(summary['packets'][row['index']]['output'])
        manifest=(p/'RAW_MANIFEST.json').read_bytes(); marker=(p/'RAW_COMPLETE76.marker').read_text()
        check('marker SHA frame '+str(row['frame']),hashlib.sha256(manifest).hexdigest()==marker)
        files=[x for x in p.iterdir()if x.name.endswith('.plane')]
        check('34 finite same-source planes '+str(row['frame']),len(files)==34 and all((lambda h,a:h['sourceId']==row['sourceId']and h['frameIndex']==row['frame']and h['renderSerial']==row['serial']and np.isfinite(a).all())(*plane(x))for x in files))
        cam=camera(p/'source.camera')
        check('same-frame camera '+str(row['frame']),cam['sourceId']==row['sourceId']and cam['frameIndex']==row['frame']and cam['renderSerial']==row['serial'])
    check('all actual S3 RGBA/meta equal graph',all(r['RGBA_product_vs_graph_max']==0 and r['meta_product_vs_graph_max']==0 for r in result['frames']))
    check('packed actual normal SH main-light and g exact',result['normalSHLightEquality']and all(max(r['producer_vs_graph'].values())==0 for r in result['frames']if r['packed']))
    check('retarget and original producers all8 fields exact',all(r['original_vs_retargetGraph_all8_max']==0 for r in result['frames']if r['packed']))
    check('backing coverage owner role alpha exact',all(r['backingCoverageExact']and r['backingRoleOwnerAlphaExact']for r in result['frames']))
    check('one remaining backing RGB8 code counterexample retained',sum(r['backingPreview_sRGB8_differentSamples']for r in result['frames'])==1 and max(r['backingPreview_sRGB8_maxCodeDelta']for r in result['frames'])==1 and not result['backing4xEquality'])
    check('getter is not evaluated mesh state',result['CloseReopenValidated']is False and result['frames'][2]['requestedCloseGetter']==100 and result['frames'][2]['evaluatedVerticesDeltaFromFirst']==0 and result['frames'][3]['requestedCloseGetter']==0 and result['frames'][3]['evaluatedVerticesDeltaFromFirst']>.02)
    check('public settings Input devices and dirty31 restored',summary['publicStateDifferences']==[]and summary['dirtyBefore']==summary['dirtyAfter']==31 and summary['nativeExact']==summary['nativeTotal']==47)
    check('own sources materials globals and RT lifetime restored',all(summary[k]for k in ['inputRestored','materialsRestored','samplesOnlyRestored','ownPassDisposed','motionRestored','observerRemoved'])and summary['globalRestoreErrors']==[]and summary['RTBefore']==summary['RTAfter']==30)
    check('no new console errors, historical errors not reclassified',summary['newConsoleErrors']==[]and summary['newLogExceptionTitles']==[])
    check('not final-art, product77 preserved',result['notFinalEyeComposition']and not result['automaticAdoption']and result['productDefault']==77)
    if z:z.close()
    print(json.dumps({'passed':len(checks),'checks':checks,'GPUReexecuted':False},indent=2))

if __name__=='__main__':main()
