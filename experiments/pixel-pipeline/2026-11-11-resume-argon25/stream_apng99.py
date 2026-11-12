"""Bounded streaming RGB APNG. PNG/APNG chunk contract matches Pillow's writer.
No Unity, device, source-image edit or temporal RGB blend.
"""
from pathlib import Path
import struct,zlib,hashlib,json
import numpy as np
from PIL import Image
class APNG99:
 def __init__(self,path,width,height,frames):
  if not(0<width*height<=1048576 and 0<frames<=1800):raise ValueError('99 bounded animation dimensions')
  self.path=Path(path);self.width=width;self.height=height;self.frames=frames;self.count=0;self.sequence=0;self.hashes=[];self.file=self.path.open('xb');self.file.write(b'\x89PNG\r\n\x1a\n');self.chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0));self.chunk(b'sRGB',b'\0');self.chunk(b'acTL',struct.pack('>2I',frames,0))
 def chunk(self,kind,data):
  self.file.write(struct.pack('>I',len(data)));self.file.write(kind);self.file.write(data);self.file.write(struct.pack('>I',zlib.crc32(data,zlib.crc32(kind))&0xffffffff))
 def append(self,image):
  a=np.asarray(image)
  if a.dtype!=np.uint8 or a.shape!=(self.height,self.width,3)or self.count>=self.frames:raise ValueError('99 animation frame ABI')
  self.chunk(b'fcTL',struct.pack('>5I2H2B',self.sequence,self.width,self.height,0,0,1,60,0,0));self.sequence+=1;scan=np.empty((self.height,self.width*3+1),np.uint8);scan[:,0]=0;scan[:,1:]=a.reshape(self.height,-1);data=zlib.compress(scan.tobytes(),6)
  if self.count==0:self.chunk(b'IDAT',data)
  else:self.chunk(b'fdAT',struct.pack('>I',self.sequence)+data);self.sequence+=1
  self.hashes.append(hashlib.sha256(a.tobytes()).hexdigest());self.count+=1
 def finish(self):
  if self.count!=self.frames:raise ValueError('99 partial animation must not receive complete marker')
  self.chunk(b'IEND',b'');self.file.close();reader=Image.open(self.path);assert reader.n_frames==self.frames
  for i,expected in enumerate(self.hashes):reader.seek(i);assert hashlib.sha256(reader.convert('RGB').tobytes()).hexdigest()==expected
  reader.close();digest=hashlib.sha256()
  with self.path.open('rb')as source:
   for block in iter(lambda:source.read(1048576),b''):digest.update(block)
  return {'frames':self.frames,'seconds':self.frames/60,'allRGBDecodedExact':True,'streamingWorkingImagesAtMost':3,'bytes':self.path.stat().st_size,'sha256':digest.hexdigest()}

def test():
 p=Path(__file__).resolve().parent/'face99/APNG_TEST99.png';writer=APNG99(p,17,11,100)
 for i in range(100):
  a=np.zeros((11,17,3),np.uint8);a[:,:,0]=i;a[:,i%17,1]=255;writer.append(a)
 result=writer.finish();(p.parent/'CPU_APNG99.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':test()
