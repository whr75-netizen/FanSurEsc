from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlparse
import subprocess,json
O=Path(__file__).resolve().parent;B=O/'Browser547';B.mkdir(exist_ok=True);M=Path(json.loads((O/'MAIN547.json').read_text())['target'])
class Scan(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.files=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='section'and d.get('id')=='current547':self.active=True
  if self.active:
   for k,v in a:
    if k in['src','href']and v and v.startswith('file:'):self.files.append(Path(unquote(urlparse(v).path).lstrip('/')))
 def handle_endtag(self,t):
  if t=='section':self.active=False
s=Scan();s.feed(M.read_text(encoding='utf8'));assert len(s.files)>=7 and all(p.exists()for p in s.files)
results=[]
for name,p in [('MAIN547',M),('PIPELINE547',O/'PIPELINE547.html')]:
 cmd=['C:/Program Files/Google/Chrome/Application/chrome.exe','--headless=new','--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check','--disk-cache-size=1048576','--user-data-dir='+str(B/'profile'),'--window-size=1440,1500','--hide-scrollbars','--virtual-time-budget=1500','--screenshot='+str(B/(name+'.png')),'--dump-dom',p.as_uri()]
 with(B/(name+'.html')).open('wb')as out,(B/(name+'_stderr.txt')).open('wb')as err:
  proc=subprocess.Popen(cmd,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);code=proc.wait(timeout=50)
 dom=(B/(name+'.html')).read_text(encoding='utf8',errors='replace');assert code==0 and (B/(name+'.png')).exists()
 if name=='MAIN547':assert dom.index('id="current547"')<dom.index('id="current543"')and'FULL_WALK547.webp'in dom
 else:assert '형상 영역과 명암/그림자 영역'in dom and'100000'in dom
 results.append({'page':name,'exit':code,'screenshot':str(B/(name+'.png')),'bytes':p.stat().st_size})
(B/'BROWSER547.json').write_text(json.dumps({'pages':results,'newSectionLocalLinks':len(s.files),'linksExist':True,'delivery':'local; Library403 not retried'},indent=2));print(json.dumps(results))
