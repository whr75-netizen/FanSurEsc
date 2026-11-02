"""Derive an OUTSIDE-Assets candidate from current product77; no Unity calls."""
from pathlib import Path
import hashlib,json,difflib,subprocess

H=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
FILES={
 'FaceSceneLight335.hlsl':'Assets/EUnityValidation01/SkinPalette302/Shaders/FaceSceneLight335.hlsl',
 'BodyPalette302.hlsl':'Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl',
 'RestoreStyle335.compute':'Assets/EUnityValidation01/MinimalRestore335/Shaders/RestoreStyle335.compute',
}
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    out=H/'candidate';out.mkdir(exist_ok=True)
    manifest={'scope':'outside Assets / CPU only / not activated','product':{},'reused':{}}
    patches=[]
    for name,relative in FILES.items():
        raw=(REPO/relative).read_bytes();src=raw.decode('utf-8-sig').replace('\r\n','\n');dst=src
        if name=='FaceSceneLight335.hlsl':
            old='float3 SurfaceLayerOutput335(float3 colour,float3 factor,float continuous,float quantized)'
            assert dst.count(old)==1 and dst.count('return colour*factor;')==1
            dst='#include "ResolvedRegionPalette.hlsl"\n'+dst.replace(old,old[:-1]+',uint2 stagePixel)')
            dst=dst.replace('return colour*factor;',
                'float3 paletteRGB;\n if(TryResolvedRegionPalette(stagePixel,paletteRGB))return paletteRGB;\n // Unresolved/excluded remains legacy and MUST NOT count as finite-LUT success.\n return colour*factor;')
        elif name=='BodyPalette302.hlsl':
            old='SurfaceLayerOutput335(baseColour,factor,continuous,level)'
            assert dst.count(old)==1
            dst=dst.replace(old,'SurfaceLayerOutput335(baseColour,factor,continuous,level,(uint2)input.pos.xy)')
            oldinclude='"Assets/EUnityValidation01/SkinPalette302/Shaders/FaceSceneLight335.hlsl"'
            assert dst.count(oldinclude)==1
            dst=dst.replace(oldinclude,'"FaceSceneLight335.hlsl"')
        else:
            gate='int2 p=id.xy;if(any(p>=_ShadeSize335)||_ShadeApply335==0)return;'
            assert dst.count(gate)==1
            dst=dst.replace(gate,'int2 p=id.xy;if(any(p>=_ShadeSize335))return;')
            old='float4 m=_ShadeMeta335.Load(int3(p,0));if(!ShadeRole335(m))return;'
            assert dst.count(old)==1
            branch='''float3 paletteRGB;
 if(TryResolvedRegionPalette((uint2)p,paletteRGB)){
  float4 colour=_ShadeColourOut335[p];colour.rgb=paletteRGB;_ShadeColourOut335[p]=colour;
  float4 cls=_ShadeClassOut335[p];cls.x=_ShadeMaskRead335.Load(int3(p,0)).x;_ShadeClassOut335[p]=cls;
  float4 factor=_ShadeFactorOut335[p];factor.rgb=1;_ShadeFactorOut335[p]=factor;
  return;
 }
 // No confirmed region: retain legacy output, reported unresolved by CPU input.
 if(_ShadeApply335==0)return;
 '''+old
            dst='#include "ResolvedRegionPalette.hlsl"\n'+dst.replace(old,branch)
        (out/name).write_text(dst,encoding='utf-8',newline='\n')
        manifest['product'][relative]={'sha256':sha(raw),'candidateSHA256':sha(dst.encode())}
        patches.extend(difflib.unified_diff(src.splitlines(True),dst.splitlines(True),fromfile=relative,tofile='candidate/'+name))
    (H/'product-candidate.patch').write_text(''.join(patches),encoding='utf-8',newline='\n')
    for source,name in [(H/'ResolvedRegionPalette.hlsl','ResolvedRegionPalette.hlsl'),(H.parent/'SourcePalette54.hlsl','SourcePalette54.hlsl'),(H.parent/'SourcePalette58.cs','SourcePalette58.cs')]:
        raw=source.read_bytes();(out/name).write_bytes(raw);manifest['reused'][name]=sha(raw)
    suite=H.parent.parent/'source-palette54';reuse=H/'reuse54';reuse.mkdir(exist_ok=True)
    for name in ['test.cjs','source-palette.cjs','colour-math.cjs','adapter.cjs','fixtures.json']:
        raw=(suite/name).read_bytes();(reuse/name).write_bytes(raw);manifest['reused']['reuse54/'+name]=sha(raw)
    tracked=subprocess.check_output(['git','-C',str(REPO),'diff','--name-only'],text=True).splitlines()
    manifest['preservedTrackedChanges']={f:sha((REPO/f).read_bytes())for f in tracked if (REPO/f).is_file()}
    manifest['head']=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
    (H/'BASIS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'candidateFiles':len(FILES),'productModified':False,'reusedMathUnchanged':True}))
if __name__=='__main__':main()
