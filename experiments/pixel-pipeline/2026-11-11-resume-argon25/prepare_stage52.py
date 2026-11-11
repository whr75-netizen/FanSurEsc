"""CPU-only same-stage LUT/metadata candidate; no Unity imports or GPU compiler."""
from pathlib import Path
import difflib,hashlib,json,subprocess

H=Path(__file__).resolve().parent
BASE=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\experiments\pixel-pipeline\2026-11-02-face-region-lut')
G=H/'face52';C=G/'candidate';B=G/'build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 C.mkdir(parents=True,exist_ok=True);B.mkdir(exist_ok=True)
 sources={n:sha(BASE/n)for n in ['ResolvedRegionInput.cs','ResolvedRegionPalette.hlsl','CpuTests.cs','FIXTURE58.json','candidate/SourcePalette54.hlsl','candidate/SourcePalette58.cs','candidate/RestoreStyle335.compute']}
 for name in ['ResolvedShade52.cs','ResolvedShade52.hlsl','StageTests52.cs']:(C/name).write_bytes((H/name).read_bytes())
 for name,source in [('ResolvedRegionPalette.hlsl',BASE/'ResolvedRegionPalette.hlsl'),('SourcePalette54.hlsl',BASE/'candidate/SourcePalette54.hlsl')]:(C/name).write_bytes(source.read_bytes())
 old=(BASE/'candidate/RestoreStyle335.compute').read_text(encoding='utf-8-sig')
 new=old.replace('#include "ResolvedRegionPalette.hlsl"','#include "ResolvedShade52.hlsl"')
 new=new.replace('float3 paletteRGB;\n if(TryResolvedRegionPalette((uint2)p,paletteRGB)){','float3 paletteRGB;float appliedQ52;\n if(_ShadeView335==0&&TryResolvedShade52((uint2)p,paletteRGB,appliedQ52)){')
 needle='cls.x=_ShadeMaskRead335.Load(int3(p,0)).x;'
 assert new.count(needle)==1
 new=new.replace(needle,'cls.x=appliedQ52;')
 assert 'TryResolvedShade52((uint2)p,paletteRGB,appliedQ52)'in new
 (C/'RestoreStyle335.compute').write_text(new,encoding='utf-8',newline='\n')
 (G/'same-stage52.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='face-region-lut/candidate/RestoreStyle335.compute',tofile='face52/candidate/RestoreStyle335.compute')),encoding='utf-8')
 csc=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe');exe=B/'Stage52.exe'
 args=[str(csc),'/nologo','/utf8output','/target:exe','/main:StageTests52','/r:System.Core.dll','/r:System.Web.Extensions.dll','/out:'+str(exe),str(BASE/'candidate/SourcePalette58.cs'),str(BASE/'ResolvedRegionInput.cs'),str(BASE/'CpuTests.cs'),str(C/'ResolvedShade52.cs'),str(C/'StageTests52.cs')]
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8');(B/'diagnostics52.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
 r=subprocess.run([str(exe),str(BASE/'FIXTURE58.json')],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
 result=json.loads(r.stdout);result['upstreamHashes']=sources;result['noSourceMathChanges']=True;result['actualStageRasterSupplierImplemented']=False;result['newRuntimeBuffer']='_ResolvedRegionAppliedQ: float, same index/extent as binding and k; no live upload performed';result['shaderCompiledOrImported']=False;result['staticDebugViewUsesLegacyPath']=True
 result['metadataReferenceNormalization']='Float32(k/(N-1)); test Q values are computed from recorded58 k, not observed raw live/GPU Q planes. Actual producer normalization/precision still requires verification.'
 assert sources=={n:sha(BASE/n)for n in sources}
 assert new.index('TryResolvedShade52')<new.index('if(_ShadeApply335==0)')
 assert '_ShadeView335==0&&TryResolvedShade52' in new and 'cls.x=appliedQ52;' in new
 (G/'CPU_STAGE52.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
