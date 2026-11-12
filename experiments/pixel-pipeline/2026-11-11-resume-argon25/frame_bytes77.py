import struct
def decode(data,expected=248832):
 if len(data)<12 or data[:4]!=b'R77F':raise ValueError('R77F header')
 mode,n=struct.unpack_from('<II',data,4)
 if n!=expected or n<1 or n>262144 or n%16:raise ValueError('bounded byte ABI')
 if mode==0:
  if len(data)!=12+n:raise ValueError('raw byte count')
  return data[12:]
 if mode!=1:raise ValueError('unsupported record encoding')
 result=bytearray();p=12
 while len(result)<n:
  if p+4>len(data):raise ValueError('truncated token')
  token,=struct.unpack_from('<I',data,p);p+=4;count=token&0x7fffffff
  if count<1 or len(result)+count*16>n:raise ValueError('bounded token run')
  size=16 if token&0x80000000 else count*16
  if p+size>len(data):raise ValueError('truncated payload')
  result.extend(data[p:p+16]*count if token&0x80000000 else data[p:p+size]);p+=size
 if p!=len(data):raise ValueError('trailing data')
 return bytes(result)
