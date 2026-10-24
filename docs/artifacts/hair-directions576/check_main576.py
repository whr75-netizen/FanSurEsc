from pathlib import Path
from urllib.parse import urlparse,unquote
import subprocess,json,re
R=Path(__file__).parent
main=Path('C:/Users/JG/Desktop/작업폴더/메인.html')
s=main.read_text(encoding='utf-8');section=s.split('<section id="current576"',1)[1].split('<section id="current575"',1)[0]
links=[]
for url in re.findall(r'(?:src|href)="(file:[^"]+)"',section):
    p=Path(unquote(urlparse(url).path).lstrip('/'))
    assert p.is_file(),p
    links.append({'url':url,'bytes':p.stat().st_size})
profile=R.parent/'Main523/chrome-profile'
assert profile.is_dir(),'Reuse established profile only'
argv=['C:/Program Files/Google/Chrome/Application/chrome.exe','--headless=new','--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check',f'--user-data-dir={profile.resolve()}','--window-size=1440,1080','--hide-scrollbars',f'--screenshot={R.resolve()}/MAIN576_BROWSER.png','--virtual-time-budget=2000','--dump-dom',main.as_uri()]
out=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
(R/'MAIN576_BROWSER.dom.html').write_bytes(out.stdout)
(R/'MAIN576_BROWSER.stderr.txt').write_bytes(out.stderr)
assert out.returncode==0,out.returncode
assert b'current576'in out.stdout and b'WALK576_PARTIAL42.webp'in out.stdout
assert(R/'MAIN576_BROWSER.png').is_file()
record={'exitCode':out.returncode,'main':str(main),'links':links,'freshProfileCreated':False,'browser':'installed Chrome headless CLI; actual Main file','screenshot':str(R/'MAIN576_BROWSER.png'),'partialNotFullLoop':True}
(R/'MAIN576_BROWSER_CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'exitCode':out.returncode,'validLinks':len(links),'screenshotBytes':(R/'MAIN576_BROWSER.png').stat().st_size}))
