"""Compile standalone CPU candidates, compare full observable results and saved45 replay."""
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess,zipfile
H=Path(__file__).resolve().parent;G=H/'face53';B=G/'build'
DOTNET=Path(r'C:\Program Files\dotnet\dotnet.exe');CSC=Path(r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll')
REFS=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0')
ENGINE=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data\Managed\UnityEngine\UnityEngine.CoreModule.dll')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(variant,main):
 folder=B/(variant+'-'+main);folder.mkdir(parents=True,exist_ok=True);dll=folder/'Tests.dll'
 args=['/nologo','/nostdlib+','/target:exe','/langversion:9','/main:'+main,'/utf8output','/out:'+str(dll)]+['/reference:'+str(p)for p in REFS.glob('*.dll')]+['/reference:'+str(ENGINE),str(H/'CurveCarrier43.cs'),str(H/('CurveHistory45.cs'if variant=='linear'else'CurveHistoryIndexed53.cs')),str(H/(main+'.cs'))]
 rsp=folder/'compile.rsp';rsp.write_text('\n'.join('"'+s+'"'for s in args),encoding='utf-8');r=subprocess.run([str(DOTNET),'exec',str(CSC),'/noconfig','@'+str(rsp)],capture_output=True,text=True);(folder/'diagnostics.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
 shutil.copyfile(ENGINE,folder/ENGINE.name);(folder/'Tests.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}))
 inputs=[]
 if main=='ReplayHistory45':
  fixture=H/'face45/ACTUAL_INPUT45.bin'
  if not fixture.exists():
   # Completed raw evidence is archived once; do not rewrite the old snapshot.
   fixture=folder/'actual45.bin'
   with zipfile.ZipFile(H/'face50/ACTUAL_PACKETS45_49.zip')as z:fixture.write_bytes(z.read('face45/ACTUAL_INPUT45.bin'))
  assert sha(fixture)==json.loads((H/'face45/ACTUAL_HISTORY45.json').read_text())['fixtureSHA256']
  inputs=[str(fixture)]
 args=[str(DOTNET),str(dll)]+inputs
 r=subprocess.run(args,capture_output=True,text=True,timeout=40);assert r.returncode==0,r.stdout+r.stderr;return json.loads(r.stdout)
def main():
 G.mkdir(exist_ok=True);old=run('linear','HistoryIndexTests53');new=run('indexed','HistoryIndexTests53')
 assert old['observableSHA256']==new['observableSHA256']
 unit=run('indexed','CurveHistoryTests45');actual=run('indexed','ReplayHistory45');saved=json.loads((H/'face45/ACTUAL_HISTORY45.json').read_text())
 assert all(actual[k]==saved[k]for k in actual)
 a=(H/'CurveHistory45.cs').read_text();b=(H/'CurveHistoryIndexed53.cs').read_text();(G/'history-index53.patch').write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='CurveHistory45.cs',tofile='review-only/CurveHistory45.cs')),encoding='utf-8')
 report={'baseline':old,'indexed':new,'fullObservableResultEqual':True,'oldScopeLifecycleGroups':unit['assertionGroups'],'savedActual12FrameReplayExact':True,'actualReplay':actual,'sourceHash':{'baseline':sha(H/'CurveHistory45.cs'),'candidate':sha(H/'CurveHistoryIndexed53.cs'),'carrierUnchanged':sha(H/'CurveCarrier43.cs'),'savedInput':saved['fixtureSHA256']},'maxSamples4096':{'build':'once per completed frame: O(n log n), no duplicate retained t per edge','lookup':'dictionary edge lookup + <=13 binary comparisons and 2 adjacent distances; preserves both equal minima','previous':'per observation full previous list filter and matching-edge minimum scan'},'managedAllocationComparisonOnly':True,'runtimeSelectionFeedbackImplemented':False,'GPUExecuted':False,'productApplied':False}
 (G/'CPU_INDEX53.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items()if k not in ['actualReplay','sourceHash']}))
if __name__=='__main__':main()
