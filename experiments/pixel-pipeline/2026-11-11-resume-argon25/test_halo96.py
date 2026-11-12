import unittest,math,numpy as np
class Tests(unittest.TestCase):
 def test_every_overlapping_native_pixel_is_in_halo(self):
  for w in [1,2,26]:
   for lo in [-2.,-1.999,-.5,-.001,0.,.001,.5,.999,210.125]:
    start=math.floor(lo);size=2*w+1
    for cell in range(w):
     a=lo+2*cell;b=a+2;overlap=[p for p in range(math.floor(a)-1,math.ceil(b)+1)if p<b and p+1>a]
     self.assertTrue(all(start<=p<start+size for p in overlap))
 def test_two_centres_are_not_all_overlapping_pixels(self):
  lo=.125;centres=[p for p in range(4)if lo<=p+.5<lo+2];overlap=[p for p in range(4)if p<lo+2 and p+1>lo]
  self.assertEqual(centres,[0,1]);self.assertEqual(overlap,[0,1,2])
 def test_bounded_payload_and_padding(self):
  w=26;end=2*(2*w+1)**2+14*w*w;self.assertEqual(end,15082);self.assertLess(end,24*w*w);self.assertEqual(24*w*w*16,259584)
 def test_field_indexing(self):
  w=26;start=2*(2*w+1)**2;a=np.arange(24*w*w*4,dtype='<f4').reshape(-1,4)
  for plane in range(14):
   for x,y in[(0,0),(6,7),(25,25)]:
    index=start+plane*w*w+y*w+x;self.assertEqual(index-start,plane*w*w+y*w+x);self.assertTrue(np.array_equal(a[index],a[start:start+14*w*w].reshape(14,w,w,4)[plane,y,x]))
if __name__=='__main__':unittest.main()
