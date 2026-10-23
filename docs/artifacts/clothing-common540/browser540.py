from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import subprocess,json,sys
O=Path(__file__).resolve().parent/('Browser'+sys.argv[1]);O.mkdir(exist_ok=True);M=Path('C:/Users/JG/Desktop/작업폴더/메인.html')
class Resources(HTMLParser):
 def __init__(self):super().__init__();self.remote=[];self.current=False;self.files=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='section'and d.get('id')=='current540':self.current=True
  for k,v in a:
   if k in ['src','srcset']and v and('http:'in v or'https:'in v):self.remote.append(v)
   if self.current and k in ['src','href']and v and v.startswith('file:'):self.files.append(Path(unquote(urlparse(v).path).lstrip('/')))
 def handle_endtag(self,t):
  if t=='section':self.current=False
r=Resources();r.feed(M.read_text(encoding='utf8'));assert not r.remote;assert all(p.exists()for p in r.files),[str(p)for p in r.files if not p.exists()]
cmd=['C:/Program Files/Google/Chrome/Application/chrome.exe','--headless=new','--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check','--user-data-dir='+str(O/'profile'),'--window-size=1440,1080','--hide-scrollbars','--screenshot='+str(O/'MAIN540.png'),'--dump-dom',M.as_uri()]
with(O/'dom.html').open('wb')as out,(O/'stderr.txt').open('wb')as err:
 p=subprocess.Popen(cmd,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);print(json.dumps({'browserPID':p.pid,'status':'running'}),flush=True);code=p.wait(timeout=50)
dom=(O/'dom.html').read_text(encoding='utf8',errors='replace');j={'exit':code,'current540':'id="current540"'in dom,'proof540':'id="proof540"'in dom,'productOFF':'왼쪽 현재 제품 OFF'in dom,'bodyRegression':'Body0 시험 미채택'in dom,'allCurrentLinksExist':True,'links':len(r.files),'screenshot':(O/'MAIN540.png').is_file(),'remote':r.remote};assert code==0 and all(j[k]for k in ['current540','proof540','productOFF','bodyRegression','screenshot']);(O/'BROWSER540.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(j))
