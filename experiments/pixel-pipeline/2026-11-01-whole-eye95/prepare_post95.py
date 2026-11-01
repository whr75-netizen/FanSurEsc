from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'post-final';OUT.mkdir(exist_ok=False)
CAP=HERE/'capture-scale-correct'
s=(CAP/'Post95B.cs').read_text().replace(str(CAP/'POST95B.json'),str(OUT/'POST95FINAL.json'))
extra='''
  var rows95=new Arr58();foreach(var row95 in Json58.Parse(File.ReadAllText(@"SNAPSHOT_ROOT/NATIVE_BEFORE73.json")))rows95.Add(new Obj58{["path"]=row95["path"],["type"]=row95["type"],["snapshot"]=row95["snapshot"]});
  CreateOnly73.Text(@"VERIFY_OUT",NativeSnapshot73.Compare(@"SNAPSHOT_ROOT",rows95).ToString());
'''.replace('SNAPSHOT_ROOT',str(CAP)).replace('VERIFY_OUT',str(OUT/'NATIVE95FINAL.json'))
s=s.replace('  result.Log(',extra+'  result.Log(')
(OUT/'Post95Final.cs').write_text(s,encoding='utf-8')
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs',OUT/'Post95Final.cs'],OUT/'RUN_Post95Final.cs.txt')
relay=(CAP/'relay95.py').read_text().replace("'Verify95B')","'Verify95B','Post95Final')");(OUT/'relay95.py').write_text(relay,encoding='utf-8')
print('Prepared single read-only public/native final comparison, no state changes.')
