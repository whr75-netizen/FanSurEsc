import struct,zlib
from pathlib import Path
def read(path):
 data=Path(path).read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';p=8;compressed=b''
 while p<len(data):
  n=struct.unpack_from('>I',data,p)[0];kind=data[p+4:p+8];value=data[p+8:p+8+n];p+=n+12
  if kind==b'IHDR':w,h,bits,colour,*_=struct.unpack('>IIBBBBB',value)
  if kind==b'IDAT':compressed+=value
 assert bits==8 and colour in [2,6],(bits,colour)
 channels=4 if colour==6 else 3;raw=zlib.decompress(compressed);p=0;previous=bytearray(w*channels);out=bytearray()
 def paeth(a,b,c):
  v=a+b-c;x,y,z=abs(v-a),abs(v-b),abs(v-c)
  return a if x<=y and x<=z else b if y<=z else c
 for _ in range(h):
  f=raw[p];row=bytearray(raw[p+1:p+1+w*channels]);p+=1+w*channels
  for i in range(len(row)):
   a=row[i-channels]if i>=channels else 0;b=previous[i];c=previous[i-channels]if i>=channels else 0
   row[i]=(row[i]+[0,a,b,(a+b)//2,paeth(a,b,c)][f])%256
  if channels==4:out+=row
  else:
   for i in range(0,len(row),3):out+=row[i:i+3]+b'\xff'
  previous=row
 return w,h,bytes(out)
def write(path,w,h,rgba):
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4]for y in range(h)),9))+chunk(b'IEND',b''))
def zoom(raw,w,h,z):return bytes(raw[((y//z)*w+x//z)*4+c]for y in range(h*z)for x in range(w*z)for c in range(4))
