"""Native sample-coordinate/packing oracles, not shader/GPU success claims."""
import unittest,math,numpy as np
class Tests(unittest.TestCase):
 def test_four_centres_in_half_open_cell(self):
  for q in [-20,-1,0,1,211,479]:
   for phase in [-1.25,-.75,-.5,-.25,-1e-6,0,1e-6,.25,.5,.75,1.25]:
    lo=2*(q+phase);first=math.ceil(lo-.5)
    expected=[p for p in range(math.floor(lo)-2,math.ceil(lo)+4)if lo<=p+.5<lo+2]
    self.assertEqual(expected,[first,first+1])
 def test_cell_replication_is_not_four_source_samples(self):
  raw=np.array([1,5,9,13]);present=np.repeat(raw[3],4)
  self.assertEqual(len(set(present)),1);self.assertEqual(len(set(raw)),4)
 def test_no_packet_growth(self):
  self.assertEqual(24*26*26*16,259584);self.assertLessEqual(24*26*26*16,262144)
 def test_packing_identity(self):
  a=np.arange(24*26*26*4,dtype='<f4').reshape(26,24,26,4)
  for plane in range(24):
   for y,x in [(0,0),(7,6),(25,25)]:
    self.assertEqual(a[y,plane,x,0],np.frombuffer(a.tobytes(),'<f4')[4*(y*26*24+plane*26+x)])
if __name__=='__main__':unittest.main()
