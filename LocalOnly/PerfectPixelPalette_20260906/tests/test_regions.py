import colorsys
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from perfect_pixel.regions import RegionSpec,classify_regions,extract_region,rgb_to_hsv


class RegionTests(unittest.TestCase):
    def test_hsv_reference(self):
        a = np.random.default_rng(12).integers(0,256,(200,3),dtype=np.uint8)
        ref = np.array([colorsys.rgb_to_hsv(*(v/255 for v in p)) for p in a])
        ref[:,0] *= 360
        np.testing.assert_allclose(rgb_to_hsv(a),ref,atol=0.0001)

    def test_seed_connectivity_multiseed_and_no_recolor(self):
        a = np.full((12,20,3),(230,230,250),dtype=np.uint8)
        a[2:5,2:5] = (220,140,140)
        a[2:5,12:15] = (220,140,140)
        before = a.copy()
        bounds = ((350,15,.2,1,.3,1),)
        labels,meta = classify_regions(a,[RegionSpec('pink',bounds,((3,3),))])
        self.assertEqual(np.sum(labels==0),9)
        self.assertEqual(labels[3,13],-1)
        labels,meta = classify_regions(a,[RegionSpec('pink',bounds,((3,3),(13,3)))])
        self.assertEqual(np.sum(labels==0),18)
        out = extract_region(a,labels,0)
        np.testing.assert_array_equal(out[labels==0,:3],a[labels==0,:3])
        np.testing.assert_array_equal(a,before)

    def test_distinct_accent_priority_and_unknown(self):
        a = np.full((20,30,3),(160,110,70),dtype=np.uint8)
        a[3:5,3:5] = (220,140,140)
        a[0,0] = (0,0,255)
        specs = [RegionSpec('pink',((350,12,.2,.9,.4,1),),priority=10),
                 RegionSpec('warm',((0,50,.1,1,.1,1),),priority=0)]
        labels,_ = classify_regions(a,specs)
        self.assertEqual(np.sum(labels==0),4)
        self.assertEqual(labels[0,0],-1)
        self.assertEqual(labels[10,10],1)

    def test_equal_priority_conflict_and_roi(self):
        a = np.full((10,12,3),(180,120,80),dtype=np.uint8)
        bounds = ((0,360,0,1,0,1),)
        specs = [RegionSpec('A',bounds,boxes=((0,0,6,10),)),
                 RegionSpec('B',bounds,boxes=((3,0,9,10),))]
        labels,meta = classify_regions(a,specs)
        self.assertTrue((labels[:,:3]==0).all())
        self.assertTrue((labels[:,3:6]==-2).all())
        self.assertTrue((labels[:,6:9]==1).all())
        self.assertTrue((labels[:,9:]==-1).all())
        self.assertEqual(meta['conflict_pixels'],30)

    def test_warm_gray_transparency_and_missed_seed(self):
        a = np.array([[[180,120,80,255],[140,140,140,255],[180,120,80,0],[180,120,80,100]]],dtype=np.uint8)
        spec = RegionSpec('warm',((15,40,.1,1,0,1),))
        labels,_ = classify_regions(a,[spec])
        np.testing.assert_array_equal(labels,[[0,-1,-3,0]])
        self.assertEqual(extract_region(a,labels,0)[0,3,3],100)
        _,meta = classify_regions(a,[RegionSpec('warm',spec.hsv_ranges,((1,0),))])
        self.assertEqual(meta['regions'][0]['missed_seeds'],[[1,0]])
        self.assertEqual(meta['regions'][0]['selected_pixels'],0)

    def test_invalid_and_deterministic(self):
        a = np.full((10,12,3),120,dtype=np.uint8)
        spec = RegionSpec('all',((0,360,0,1,0,1),),((2,2),))
        l1,m1 = classify_regions(a,[spec]); l2,m2 = classify_regions(a,[spec])
        np.testing.assert_array_equal(l1,l2)
        self.assertEqual(m1,m2)
        for s in [RegionSpec('bad',((0,400,0,1,0,1),)),RegionSpec('bad',spec.hsv_ranges,((12,3),)),RegionSpec('bad',spec.hsv_ranges,boxes=((0,0,14,5),))]:
            with self.assertRaises(ValueError): classify_regions(a,[s])


if __name__ == '__main__':
    unittest.main()
