from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent;P=R/'argon23-runtime113'
source=(P/'ForwardEye113.compute').read_text(encoding='utf8');region=(P/'Region113.hlsl').read_text(encoding='utf8');candidate=(R/'eye-failures114/paired-point-patch/Region113.hlsl').read_text(encoding='utf8')
# Existing113 kernels are preserved for the actual same-frame control.
body=(H/'Form115.hlsl').read_text(encoding='utf8')
a=region.index('[numthreads(8,8,1)]void PrepareCells113');b=region.index('\nfloat Interval113',a);prepare=region[a:b].replace('void PrepareCells113','void PrepareCells115')
prepare=prepare.replace('float4 mass=0,ci=0,cw=0;','for(int key115=0;key115<_KeyCount113;key115++)_CellKey115[cell*_KeyCount113+key115]=StatZero115();float4 mass=0,ci=0,cw=0;')
old='float lower=lo[part-1]*1024,upper=hi[part-1]*1024;'
assert old in prepare
prepare=prepare.replace(old,'Stat115 moment115=_CellKey115[cell*_KeyCount113+key];_CellKey115[cell*_KeyCount113+key]=StatAdd115(moment115,lo[part-1],(float2(p*8+int2(x,y))+.5)/8);'+old)
dest='''
#pragma kernel CarrierQueries115
#pragma kernel ComposeRegion115
int2 _CarrierSize115;float4 _CarrierOrigin115;
[numthreads(64,1,1)]void CarrierQueries115(uint3 tid:SV_DispatchThreadID){uint n=(uint)(_CarrierSize115.x*_CarrierSize115.y);if(tid.x>=n*4)return;uint part=tid.x/n,at=tid.x%n;float4 meta=_SrcLayers113[(part*5+1)*n+at];float2 xy=_CarrierOrigin115.xy+(float2(at%(uint)_CarrierSize115.x,at/(uint)_CarrierSize115.x)+.5)/4;_WriteQueries113[tid.x]=float4(xy,meta.x,round(meta.z));}
'''
a=candidate.index('[numthreads(8,8,1)]void ComposeRegion113');compose=candidate[a:].replace('void ComposeRegion113','void ComposeRegion115').replace('_CarrierSize113','_CarrierSize115').replace('_CarrierOrigin113','_CarrierOrigin115').replace('_CarrierSampleScale113','4')
out=source+'\n'+body+'\n'+prepare+'\n'+dest+compose
(H/'ForwardEye115.compute').write_text(out,encoding='utf8');print('Generated isolated115 compute, original113 kernels preserved; no import')
