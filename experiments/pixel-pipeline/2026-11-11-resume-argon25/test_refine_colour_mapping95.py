import unittest,numpy as np
from refine_colour_mapping95 import refine
class Tests(unittest.TestCase):
 def run_case(self,rgb,initial,refs,pairs=(),orders=(),bounds=None):
  rgb=np.asarray(rgb);bounds=np.tile([[0,0,0],[255,255,255]],(len(rgb),1,1))if bounds is None else bounds;return refine(rgb,initial,refs,bounds,pairs,orders)
 def test_orthogonal_false_step_removed_without_new_colour(self):
  rgb=np.array([[253,238,220],[253,242,225],[254,239,226],[255,239,226]])
  r=self.run_case(rgb,[0,1,0,1],[0,1]);out=rgb[r['referenceIndices'][r['colourAddress']]];np.testing.assert_array_equal(out[2],out[3]);self.assertTrue(r['converged']);self.assertEqual(r['newRepresentatives'],0)
 def test_profile_contrast_kept(self):
  rgb=np.array([[0,0,0],[1,1,1],[2,2,2],[4,4,4]])
  r=self.run_case(rgb,[0,0,1,1],[0,3],[(1,2)],[(1,2)]);out=rgb[r['referenceIndices'][r['colourAddress']]];self.assertTrue((out[2]>out[1]).all())
 def test_exact_constant_interval_kept(self):
  rgb=np.array([[0,0,0],[2,2,2],[3,3,3]]);bounds=np.tile([[0,0,0],[255,255,255]],(3,1,1));bounds[2]=[rgb[2],rgb[2]]
  r=self.run_case(rgb,[0,1,2],[0,1,2],bounds=bounds);out=rgb[r['referenceIndices'][r['colourAddress']]];np.testing.assert_array_equal(out[2],rgb[2])
 def test_no_improvement_does_not_move(self):
  r=self.run_case([[0,0,0],[1,1,1],[2,2,2]],[0,0,1],[0,2]);self.assertEqual(sum(x['moves']for x in r['history']),0)
 def test_reference_order_does_not_select_a_different_rgb(self):
  rgb=np.array([[0,0,0],[1,1,1],[2,2,2],[3,3,3]]);a=self.run_case(rgb,[0,0,1,1],[0,3]);b=self.run_case(rgb,[1,1,0,0],[3,0]);np.testing.assert_array_equal(rgb[a['referenceIndices'][a['colourAddress']]],rgb[b['referenceIndices'][b['colourAddress']]])
if __name__=='__main__':unittest.main()
