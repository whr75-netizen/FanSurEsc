from pathlib import Path
import struct,json,re,sys
import numpy as np
O=Path(__file__).resolve().parent;R=O/(sys.argv[1]if len(sys.argv)>1 else'Probe');rows=[]
def read(path):
 b=path.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4),(x,y)
def cell(prefix,name,x,y):
 a,(ox,oy)=read(R/(prefix+'_'+name+'.bin'));return a[y-oy,x-ox].tolist()
for f,x in [(35,217),(36,217),(41,218)]:
 for mode in [14,15]:
  pre=f'{f}_{mode}';s=(R/(pre+'_PARAMS.txt')).read_text();hq=re.search(r'headXY=(\d+),(\d+)',s);hx,hy=map(int,hq.groups());d={'frame':f,'mode':mode,'params':s,'mainCentre':cell(pre,'MAIN_CENTRE_META',x,49),'headCentre':cell(pre,'HEAD_CENTRE_META',hx,hy),'headBareOwner':cell(pre,'HEAD_BARE_OWNER',hx,hy),'mainReplayOwner':cell(pre,'MAIN_REPLAY_Owner',x,49),'mainReplayMeta':cell(pre,'MAIN_REPLAY_PreparedMeta',x,49),'mainReplayUV':cell(pre,'MAIN_REPLAY_PreparedUV',x,49),'headReplayMeta':cell(pre,'HEAD_REPLAY_PreparedMeta',hx,hy),'headReplayUV':cell(pre,'HEAD_REPLAY_PreparedUV',hx,hy),'actualJoinedOwner':cell(pre,'MAIN_BARE_OWNER',x,49),'native4':[]}
  for yy in range(2):
   for xx in range(2):
    sx,sy=2*x+xx,2*49+1-yy;d['native4'].append({'xx':xx,'yy':yy,'score':(xx-1)**2+(yy-1)**2,'meta':cell(pre,'MAIN_NATIVE5',sx,sy),'uv':cell(pre,'MAIN_NATIVE6',sx,sy)})
  rows.append(d)
(O/('TRACE_'+R.name.upper()+'541.json')).write_text(json.dumps(rows,indent=2));print(json.dumps([{k:d[k]for k in ['frame','mode','mainCentre','mainReplayOwner','headBareOwner','actualJoinedOwner']}for d in rows]))
