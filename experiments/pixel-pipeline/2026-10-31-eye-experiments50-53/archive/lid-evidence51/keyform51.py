"""Bind retained authored contours and native lid geometry to one eye key form.

No design curve, pigment or raster lid is synthesized. Native morph geometry and
low-resolution pixel key-form availability are distinct states.
"""
import copy
import numpy as np

class KeyForm51:
    def __init__(self,bundle):
        self.source=copy.deepcopy(bundle)
        self.key=(bundle['modelTopologySHA256'],bundle['referenceContourSHA256'],bundle['templateRoleSHA256'])
    def reference_layer(self,key,state,translation):
        if tuple(key)!=self.key:raise ValueError('Source binding changed')
        if state!='existing-open-reference':raise ValueError('No registered low-resolution state; do not reuse open pixels')
        t=np.floor(np.asarray(translation,float)+.5).astype(int)
        cells=copy.deepcopy(self.source['cells']);eyes=copy.deepcopy(self.source['eyes'])
        for c in cells:c['xy']=(np.array(c['referenceXY'])+t).tolist()
        for e in eyes:
            for name in['parent','iris']:e[name]=(np.array(e[name])+t).tolist()
            for name in['pivot','irisAnchor']:e[name]=(np.array(e[name])+t).tolist()
            e['upperLidPath']=[e['parent'][i]for i in e['upperParentArcIndices']]
            e['lowerLidPath']=[e['parent'][i]for i in e['lowerParentArcIndices']]
        return dict(cells=cells,eyes=eyes,translation=t.tolist(),newLidRasterOrColour=False)
    def native_lid_geometry(self,name,eye,weight):
        if weight not in[0,50,100]:raise ValueError('Only explicitly exported native geometry states')
        data=self.source['nativeClosingMorphs'][name]
        state=next(q for q in data['nativeRingStates']if q['eye']==eye)
        points=next(s['restHeadPoints']for s in state['states']if s['weight']==weight)
        return dict(nativeRestHeadPoints=copy.deepcopy(points),pixelKeyFormAvailable=weight==0,
            approvedPixelDesign=False,source=name,eye=eye,weight=weight)
