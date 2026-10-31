"""Replay saved CPU/GPU/RT evidence only. Never launches or contacts Unity."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image
R=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--source54',type=Path,required=True);args=parser.parse_args()
def load(n):return json.loads((R/n).read_text(encoding='utf-8-sig'))
p=json.loads((args.source54/'PACKET.json').read_text());receipt=load('PACKET_RECEIPT.json');report=load('GPU_RESULT.json');verified=load('VERIFICATION.json')
assert hashlib.sha256((args.source54/'PACKET.json').read_bytes()).hexdigest()==receipt['packet54SHA256']
b=(R/'PACKET57.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==receipt['sha256']
magic,version,np,nt,nf,n=struct.unpack_from('<6I',b);assert (magic,version,np,nt,nf,n)==(0x37504753,1,12,9,3,30)
offset=24
colours=[struct.unpack_from('<4I',b,offset+i*16) for i in range(np)];offset+=np*16
cuts=struct.unpack_from('<9f',b,offset);offset+=nt*4
families=[struct.unpack_from('<4I',b,offset+i*16) for i in range(nf)];offset+=nf*16
cases=[struct.unpack_from('<If',b,offset+i*8) for i in range(n)];offset+=n*8
expected=[struct.unpack_from('<4I',b,offset+i*16) for i in range(n)];offset+=n*16
assert offset==len(b)
assert colours==list(map(tuple,p['rgb8'])) and families==list(map(tuple,p['familyWords']))
assert cuts==tuple(struct.unpack('<f',struct.pack('<f',v))[0] for v in p['thresholds'])
cpu=[]
for family,g in cases:
    start,count,cutStart,cutCount=families[family]
    k=sum(g>=c for c in cuts[cutStart:cutStart+cutCount])
    assert 0<=k<count
    cpu.append(colours[start+k])
assert cpu==expected
actual=[struct.unpack_from('<4I',(R/'COMPUTE57.uint4').read_bytes(),i*16) for i in range(n)]
raw=(R/'RT57.rgba').read_bytes();shown=[tuple(raw[i*4:i*4+4]) for i in range(n)]
assert cpu==actual==shown
original=Image.open(R/'RT57.png').convert('RGBA');assert original.size==(30,1)
assert [original.getpixel((x,0)) for x in range(30)]==shown
large=Image.open(R/'RT57_16x.png').convert('RGBA');assert large.size==(480,16)
assert all(large.getpixel((x,y))==shown[x//16] for y in range(16) for x in range(480))
for name,digest in verified['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
assert not report['error'] and report['computeMismatches']==report['rtMismatches']==0 and report['dispatches']==report['draws']==1
assert report['preservationBefore'] and report['preservationAfter'] and report['ownedResourcesReleased']
assert all(v for k,v in verified['stateChecks'].items() if k!='renderTextureIds')
print(json.dumps({'savedSamplesReplayed':30,'computeExact':30,'sRGBExact':30,'paletteOutside':0,'nearestIntegerScale':16,'UnityRun':False,'liveStateNotRechecked':True}))
