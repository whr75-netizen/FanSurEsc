"""Use immutable completed packets, either local capture or RAW113.zip.
No extraction, Unity calls, large JSON parsing, or temporary file deletion.
"""
from pathlib import Path,PurePosixPath
import fnmatch,json,struct,sys,zipfile
import numpy as np
H=Path(__file__).resolve().parent
for name in ['pigment-carrier109','2026-11-01-pigment-carrier109']:
    if(H.parent/name).exists():sys.path.insert(0,str(H.parent/name));break
from io109 import Reader,buffer
class ArchiveNode113:
    def __init__(self,archive,entry):
        self.archive=archive;self.entry=PurePosixPath(entry)
        assert not self.entry.is_absolute()and '..'not in self.entry.parts
    @property
    def name(self):return self.entry.name
    def __truediv__(self,name):return ArchiveNode113(self.archive,self.entry/name)
    def read_bytes(self):
        with zipfile.ZipFile(self.archive)as z:return z.read(str(self.entry))
    def read_text(self,encoding='utf8'):return self.read_bytes().decode(encoding)
    def glob(self,pattern):
        prefix=str(self.entry)+'/'
        with zipfile.ZipFile(self.archive)as z:names=z.namelist()
        return [ArchiveNode113(self.archive,n)for n in names if n.startswith(prefix)and '/'not in n[len(prefix):]and fnmatch.fnmatch(PurePosixPath(n).name,pattern)]
def plane(path):
    r=Reader(path);assert r.i()==0x34365052 and r.i()==1
    h=r.identity();h.update(zip(['producer','channel','encoding','yConvention'],[r.s()for _ in range(4)]))
    h['size']=[r.i(),r.i()];h['roi']=[r.i()for _ in range(4)]
    a=r.a(h['roi'][2]*h['roi'][3]*4).reshape(h['roi'][3],h['roi'][2],4);r.end();return h,a
def load_packets(root=H):
    if(root/'RAW113.zip').exists():
        state=json.loads((root/'CAPTURE_INDEX113.json').read_text(encoding='utf8'))
        packets=[(row,ArchiveNode113(root/'RAW113.zip',row['relativeFolder']))for row in state['sequencePackets']]
    else:
        state=json.loads((root/'attempt5/STATE113-0028-finished.json').read_text(encoding='utf8'))
        packets=[(row,Path(row['output']))for row in state['sequencePackets']]
    return state,packets
