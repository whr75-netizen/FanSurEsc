from pathlib import Path
import hashlib,json,struct,io
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 j=json.loads((HERE/'BACKUP66.json').read_text(encoding='utf-8-sig'))
 for e in j['disk']:assert sha(HERE/'backup/disk'/e['path'])==e['sha256']
 for e in j['native']:
  if e['nativeSnapshot']:assert sha(HERE/'backup/serialized'/(e['path']+'.json'))==e['jsonSHA256']
  if 'publicMeshSHA256' in e:assert sha(HERE/'backup/mesh-readable66.bin')==e['publicMeshSHA256']
 # Independently parse the exact public mesh binary to its end (including all morphs).
 f=io.BytesIO((HERE/'backup/mesh-readable66.bin').read_bytes())
 def i():return struct.unpack('<i',f.read(4))[0]
 def s():
  n=0;shift=0
  while True:
   b=f.read(1)[0];n|=(b&127)<<shift
   if not b&128:break
   shift+=7
  return f.read(n).decode('utf-8')
 def skip(n):assert len(f.read(n))==n
 assert s()=='mesh-readable66/v1';vertices=i();indexformat=i();skip(24)
 attrs=i();skip(attrs*16);streams=i();streambytes=[]
 for _ in range(streams):stride=i();n=i();streambytes.append((stride,n));assert n==stride*vertices;skip(n)
 indexbytes=i();skip(indexbytes);submeshes=i();skip(submeshes*(6*4+24))
 bindposes=i();skip(bindposes*16*4);morphs=i();frames=0
 for _ in range(morphs):
  name=s();n=i();assert name and n>0
  for _ in range(n):skip(4);skip(vertices*3*4*3);frames+=1
 assert f.tell()==len(f.getvalue())
 result={'verified':True,'diskFiles':len(j['disk']),'serializedObjects':sum(e['nativeSnapshot'] for e in j['native']),
         'shaderNativeSkipped':sum(not e['nativeSnapshot'] for e in j['native']),
         'mesh':{'vertices':vertices,'vertexStreams':streambytes,'indexFormat':indexformat,'indexBytes':indexbytes,'submeshes':submeshes,'bindposes':bindposes,'morphs':morphs,'morphFrames':frames,'binaryBytes':len(f.getvalue()),'parsedToEnd':True},
         'limits':'File/content backup verification; no native-object recreation or GPU-cache snapshot.'}
 (HERE/'BACKUP_CHECK66.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':check()
