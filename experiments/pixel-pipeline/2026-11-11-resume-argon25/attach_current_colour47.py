"""Add an immutable pre-native-history colour receipt, not a colour replacement."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face47';p=G/'capture/RUN.cs.txt'
assert not(G/'capture/REQUEST.json').exists()
s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
rep('Fields=new RTHandle[16]','Fields=new RTHandle[17]');rep('Fields[15]=Target(4*QROI.width,QROI.height,uav:true);','Fields[15]=Target(4*QROI.width,QROI.height,uav:true);Fields[16]=Target(QROI.width,QROI.height);')
rep('native42.owner,main41.resolvedUV','native42.owner,main41.resolvedUV,main41.colour');rep('new[]{Fields[12],Fields[13],Fields[14],Fields[15]}','new[]{Fields[12],Fields[13],Fields[14],Fields[15],Fields[16]}')
rep('nativeMin42=new Vector2Int','if(qx<0||qy<0||qx+QROI.width>480||qy+QROI.height>272||main41.colour.rt.graphicsFormat!=Fields[16].rt.graphicsFormat)throw new InvalidOperationException("47 current source-colour receipt bounds/format");nativeMin42=new Vector2Int')
rep('cmd.CopyTexture(native42.output.rt,0,0,nativeMin42.x','cmd.CopyTexture(main41.colour.rt,0,0,QROI.x+join41.x,272-QROI.y-QROI.height+join41.y,QROI.width,QROI.height,Fields[16].rt,0,0,0,0);cmd.CopyTexture(native42.output.rt,0,0,nativeMin42.x')
rep('report["frameInfo"]=producer.FrameInfo40;','var ec47=producer.FieldExtent40(false,16);tasks.Add(new Plane(false,16,"currentColour47",ec47.x,ec47.y));report["frameInfo"]=producer.FrameInfo40;')
p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/currentColour47.dll');r=json.loads((G/'PREPARED47.json').read_text());r['newRTs']=2;r['sameFrameCurrentColourBeforeNativeHistoryReceipt']=True;r['captureSHA256']=hashlib.sha256(p.read_bytes()).hexdigest();(G/'PREPARED47.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print('47 current colour receipt compiled; no GPU execution or imported shader change')
