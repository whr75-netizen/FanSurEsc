import unittest
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from perfect_pixel.color_coherence import color_line_weight,apply_color_coherence


class ColorCoherenceTests(unittest.TestCase):
    def test_known_mix_weights_and_rotation_invariance(self):
        a=np.array([.75,.15,.03]);b=np.array([.8,.03,.05])
        for w in (.25,.5,.75):
            p=b+w*(a-b)
            fit=color_line_weight(p,a,b)
            self.assertIsNotNone(fit)
            self.assertAlmostEqual(fit[0],w)
            angle=1.4
            rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            aa=a.copy();bb=b.copy();pp=p.copy()
            aa[1:]=rotation@aa[1:];bb[1:]=rotation@bb[1:];pp[1:]=rotation@pp[1:]
            rotated=color_line_weight(pp,aa,bb)
            self.assertAlmostEqual(rotated[0],w)

    def test_ambiguous_or_off_line_not_forced(self):
        a=np.array([.75,.15,.03]);b=np.array([.8,.03,.05])
        self.assertIsNone(color_line_weight(a,a,b))
        self.assertIsNone(color_line_weight(np.array([.75,.1,.16]),a,b))
        self.assertIsNone(color_line_weight(a,a,a))

    def test_flat_image_no_change_and_alpha(self):
        a=np.zeros((8,8,4),dtype=np.uint8)
        a[1:7,1:7]=(100,140,180,128)
        target=a.copy();target[1:7,1:7,:3]=(50,150,210)
        mappings=[{'source_rgb':[100,140,180],'target_rgb':[50,150,210],'target_ramp':[[20,70,100],[50,150,210],[150,220,255]]}]
        result,meta=apply_color_coherence(a,target,mappings)
        np.testing.assert_array_equal(result,target)
        self.assertEqual(meta['changed_pixels'],0)
        self.assertFalse(meta['object_or_hue_specific_rules'])

    def test_reference_transfer_integration_preserves_transparent_pixels(self):
        from perfect_pixel.reference_colors import transfer_reference_colors
        a=np.zeros((7,8,4),dtype=np.uint8)
        a[:,:,:3]=(230,10,90)
        a[2:5,2:6]=(80,150,200,255)
        ref=np.array([[[20,80,130],[100,190,245],[170,220,250]]],dtype=np.uint8)
        target,model=transfer_reference_colors(a,ref)
        result,meta=apply_color_coherence(a,target,model['mappings'])
        np.testing.assert_array_equal(result[a[...,3]==0],a[a[...,3]==0])
        np.testing.assert_array_equal(result[...,3],a[...,3])


if __name__=='__main__':unittest.main()
