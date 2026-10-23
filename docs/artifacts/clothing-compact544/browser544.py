from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlparse
import subprocess,json
O=Path(__file__).resolve().parent/'Browser544';O.mkdir(exist_ok=True);M=Path('C:/Users/JG/Desktop/작업폴더/메인.html')
class Scan(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.files=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='section'and d.get('id')=='current543':self.active=True
  if self.active:
   for k,v in a:
    if k in ['src','href']and v and v.startswith('file:'):self.files.append(Path(unquote(urlparse(v).path).lstrip('/')))
 def handle_endtag(self,t):
  if t=='section':self.active=False
s=Scan();s.feed(M.read_text(encoding='utf8'));assert len(s.files)>=6 and all(p.exists()for p in s.files)
cmd=['C:/Program Files/Google/Chrome/Application/chrome.exe','--headless=new','--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check','--user-data-dir='+str(O/'profile'),'--window-size=1440,1080','--hide-scrollbars','--screenshot='+str(O/'MAIN544.png'),'--dump-dom',M.as_uri()]
with (O/'dom.html').open('wb')as out,(O/'stderr.txt').open('wb')as err:
 p=subprocess.Popen(cmd,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);code=p.wait(timeout=50)
dom=(O/'dom.html').read_text(encoding='utf8',errors='replace');result={'exit':code,'newFirstSection':dom.index('id="current543"')<dom.index('id="current540"'),'newImage':'id="proof543"'in dom,'performance544':'id="performance544"'in dom,'linksExist':len(s.files),'screenshot':(O/'MAIN544.png').exists(),'localDeliveryOnly':True};assert code==0 and result['newFirstSection']and result['newImage']and result['screenshot']and result['performance544'];(O/'BROWSER544.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
