import unittest,numpy as np
from visible_ribbon96 import area,intersect,difference,subtract,positive_area_evidence,visible
from types import SimpleNamespace

def source(triangle,z,unknown=False):
 xy=np.asarray(triangle,float)[None];row={'renderer':0,'submesh':0,'xy':xy,'lo':xy.min(1),'hi':xy.max(1),'det':np.array([1.]),'z':np.full((1,3),z),'uv':np.zeros((1,3,2))};material={'cull':0,'scroll':[0,0],'alphaTest':False,'alphaBlend':False}
 return SimpleNamespace(rows=[row],materials={(0,0):material},spec={'alphaTestGlobal':unknown,'alphaBlendGlobal':False})
class Tests(unittest.TestCase):
 def test_roundoff_sliver_is_not_positive_visibility_evidence(self):
  p=np.array([[229.18,223.95],[229.20,223.99],[229.20,223.99+3e-14]])
  self.assertEqual(positive_area_evidence([p]),0)
 def test_small_actual_feature_is_not_minimum_area_filtered(self):
  p=np.array([[229.,224.],[229.00001,224.],[229.00001,224.00001],[229.,224.00001]])
  self.assertGreater(positive_area_evidence([p]),0)
 def test_front_actor_coverage_removes_only_intersection(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=source([[.5,-2],[5,-2],[.5,5]],1.);r=visible(q,p,np.array([[0.,0],[1,0],[0,1]]),[2,2,2]);self.assertGreater(r['lowerArea'],.49);self.assertLess(r['upperArea'],.51)
 def test_actor_fully_in_front_is_not_transparent(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=source([[-2,-2],[5,-2],[-2,5]],1.);r=visible(q,p,np.array([[0.,0],[1,0],[0,1]]),[2,2,2]);self.assertEqual(r['upperArea'],0.)
 def test_unknown_alpha_is_unknown_not_empty(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=source([[-2,-2],[5,-2],[-2,5]],1.,True);r=visible(q,p,np.array([[0.,0],[1,0],[0,1]]),[2,2,2]);self.assertEqual(r['lowerArea'],0.);self.assertAlmostEqual(r['upperArea'],1.);self.assertGreater(r['unknownAlphaOccluders'],0)
 def test_actor_behind_does_not_occlude(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=source([[-2,-2],[5,-2],[-2,5]],3.);r=visible(q,p,np.array([[0.,0],[1,0],[0,1]]),[2,2,2]);self.assertAlmostEqual(r['lowerArea'],1.)
 def test_colour_surface_does_not_occlude_itself(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=source([[-2,-2],[5,-2],[-2,5]],2.);r=visible(q,p,np.array([[0.,0],[1,0],[0,1]]),[2,2,2],exclude=(0,0,0));self.assertAlmostEqual(r['lowerArea'],1.)
 def test_partial_cover_keeps_uncovered_part(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=np.array([[.5,0],[1,0],[1,1],[.5,1]]);r=difference(p,q);self.assertAlmostEqual(sum(area(v)for v in r),.5)
 def test_entire_cover_has_no_visible_area(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);self.assertFalse(difference(p,p))
 def test_boundary_touch_is_not_occlusion(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=p+[1,0];self.assertEqual(area(intersect(p,q)),0);self.assertAlmostEqual(sum(area(v)for v in difference(p,q)),1)
 def test_occluder_union_subtraction(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);a=np.array([[0.,0],[.6,0],[.6,1],[0,1]]);b=a+[.4,0];self.assertFalse(subtract(subtract([p],a),b))
 def test_rotations_reflections_do_not_change_visible_mass(self):
  p=np.array([[0.,0],[1,0],[1,1],[0,1]]);q=np.array([[.25,0],[.8,0],[.8,1],[.25,1]])
  for k in range(4):
   for sign in[-1,1]:
    m=np.linalg.matrix_power(np.array([[0.,-1],[1,0]]),k)@np.diag([sign,1]);self.assertAlmostEqual(sum(area(v)for v in difference(p@m.T,q@m.T)),.45)
if __name__=='__main__':unittest.main()
