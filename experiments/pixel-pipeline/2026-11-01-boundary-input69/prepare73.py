"""Create a fresh append-only observer experiment. No Unity/API call."""
from pathlib import Path
import re,json,hashlib
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'eye-observer73';OLD=HERE.parent/'apply-capture66';P72=HERE.parent/'eye-observer72';U=HERE.parent/'uv-features64'
def bundle(paths,target):
 uses=[];body=[]
 for p in paths:
  s=p.read_text(encoding='utf-8-sig')
  for x in re.findall(r'(?m)^using [^;\n]+;',s):
   if x not in uses:uses.append(x)
  body.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
 target.write_text('\n'.join(uses)+'\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor\n{\n'+'\n'.join(body)+'\n}\n',encoding='utf-8')
def main():
 OUT.mkdir(exist_ok=False)
 protocol=(HERE/'EyeReadback70.cs').read_text(encoding='utf-8-sig')
 protocol=protocol.replace('using System.IO;','using System.IO;\nusing System.Security.Cryptography;\nusing System.Globalization;')
 protocol=protocol.replace('Check(id,current,cancel);File.Move(target+".partial",target);','Check(id,current,cancel);Complete(target,id,current,cancel);')
 at=protocol.index('  public static void Counts(')
 extra='''  static string CompletionMarker(string path)
  {long n;string hash;using(var h=SHA256.Create())using(var f=File.OpenRead(path)){n=f.Length;hash=BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}return Path.Combine(Path.GetDirectoryName(path),"ok-"+hash+"-"+n.ToString(CultureInfo.InvariantCulture)+".complete");}
  static void Complete(string target,Identity id,Func<Identity> current,Func<bool> cancel)
  {string marker=CompletionMarker(target+".partial");Check(id,current,cancel);using(var f=new FileStream(marker,FileMode.CreateNew,FileAccess.Write,FileShare.Read)){} }
  public static string CompletedPath(string root,string name)
  {string path=Path.Combine(Path.GetFullPath(root),name+".partial");string marker=CompletionMarker(path);if(!File.Exists(marker)||new FileInfo(marker).Length!=0)throw new IOException("No validated zero-byte completion marker");return path;}
'''
 protocol=protocol[:at]+extra+protocol[at:];assert 'File.Move(' not in protocol and 'File.Delete(' not in protocol
 (OUT/'EyeReadback73.cs').write_text(protocol,encoding='utf-8');(OUT/'UnityEyeBuffer70.cs').write_bytes((HERE/'UnityEyeBuffer70.cs').read_bytes())
 test=(HERE/'TestEyeReadback70.cs').read_text(encoding='utf-8-sig')
 test=test.replace('File.OpenRead(Path.Combine(root,"counts.bin"))','File.OpenRead(Readback.CompletedPath(root,"counts.bin"))').replace('File.OpenRead(Path.Combine(root,"records.bin"))','File.OpenRead(Readback.CompletedPath(root,"records.bin"))')
 test=test.replace('Console.WriteLine("RESULT passed="+passed+', '''Test("no marker on incomplete read/frame/cancel",delegate{foreach(string name in new[]{"failure.bin","advance.bin","cancel.bin"})Throws(delegate{Readback.CompletedPath(root,name);});});
  Test("marker detects later byte corruption without overwriting input",delegate{string data=Readback.CompletedPath(root,"counts.bin");string copy=Path.Combine(root,"corrupt.bin.partial");using(var f=new FileStream(copy,FileMode.CreateNew)){f.WriteByte(99);}Throws(delegate{Readback.CompletedPath(root,"corrupt.bin");});Check(File.Exists(data),"original retained");});
  Console.WriteLine("RESULT passed="+passed+''')
 (OUT/'TestEyeReadback73.cs').write_text(test,encoding='utf-8')
 runner=(P72/'relay72.py').read_text(encoding='utf-8').replace("('Read72','Compile72','Capture72','Post72')","('Read73','Compile73','Capture73','Post73')");(OUT/'relay73.py').write_text(runner,encoding='utf-8')
 read=(P72/'Read72.cs').read_text(encoding='utf-8').replace('eye-observer72\\CURRENT72.json','eye-observer73\\CURRENT73.json').replace('["domain"]=AppDomain.CurrentDomain.Id,','["domain"]=AppDomain.CurrentDomain.Id,["runInBackground"]=Application.runInBackground,["playerRunInBackground"]=PlayerSettings.runInBackground,')
 (OUT/'Read73.cs').write_text(read,encoding='utf-8');bundle([OLD/'Json58Linear66.cs',OUT/'Read73.cs'],OUT/'RUN_Read73.cs.txt')
 (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
 repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');old=json.loads((P72/'DISK_BEFORE72.json').read_text());(OUT/'DISK_BEFORE73.json').write_text(json.dumps({'files':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in old['files']}},indent=2)+'\n')
 print('Prepared append-only73 protocol and current-state read; no Unity execution')
if __name__=='__main__':main()
