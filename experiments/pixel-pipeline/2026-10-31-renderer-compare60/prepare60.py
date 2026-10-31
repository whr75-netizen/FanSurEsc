from pathlib import Path
import hashlib,json,re,subprocess,uuid
R=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game');A='Assets/Editor/RendererCompare60Probe'
H=R/'probe-assets';H.mkdir(exist_ok=True)
def read(p):return(P/p).read_text(encoding='utf-8-sig')
include='#include "'+A+'/SourcePalette54.hlsl"\nfloat _SourceFamily60;\n'
s=read('Assets/EUnityValidation01/MinimalRestore335/Shaders/LegacySignals335.shader')
s=s.replace('Shader "EValidation/Restore335LegacySignals"','Shader "Hidden/Renderer60/LegacySignals"',1)
at='#include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"';assert s.count(at)==1;s=s.replace(at,at+'\n'+include)
at='float3 factor=ShadeFactor335(uv,(int)round(_Auto245Role),level);';assert s.count(at)==1
branch='''if(_SourceFamily60>0){uint family=(uint)round(_SourceFamily60)-1;uint k=SourceShade54(family,continuous);uint n=_SourcePalette54Families[family].y;o.colour=float4(SourceRGB8ToLinear54(SourceLookup54(family,k).rgb),alpha);o.lit=float4(lit,alpha);o.shade=float4(1,1,1,alpha);o.classifier=float4((float)k/max(1,n-1),continuous,-TransformWorldToView(v.positionWS).z,alpha);return o;}'''
s=s.replace(at,branch+at);(H/'LegacySignals60.shader').write_text(s,encoding='utf8')
s=read('Assets/EUnityValidation01/GameMapIntegration333/Shaders/Independent333.shader');s=s.replace('Shader "EValidation/GameMap333Independent"','Shader "Hidden/Renderer60/Independent"',1)
if 'Hidden/Renderer60/Independent'not in s:s=re.sub(r'Shader "[^"]+"','Shader "Hidden/Renderer60/Independent"',s,count=1)
assert s.count('#include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"')==1;s=s.replace(at if False else '#include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"','#include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"\n'+include)
at='O333 o;o.rgba=c;';assert s.count(at)==1
branch='''if(_SourceFamily60>0&&_SurfaceLayers335>.5){MToonInput m;m.uv=uv;m.normalWS=GetMToonGeometry_Normal(v,f.facing,uv);m.viewDirWS=normalize(v.viewDirWS);m.litColor=src.rgb;m.alpha=alpha;float continuous=ContinuousSurfaceLight335(v,m);uint family=(uint)round(_SourceFamily60)-1;uint k=SourceShade54(family,continuous);float n=_SourcePalette54Families[family].y;float q=ProviderSurfaceLevel335((float)k/max(1,n-1),role,v.pos.xy,-TransformWorldToView(v.positionWS).z);k=(uint)clamp(round(q*max(1,n-1)),0,n-1);c=float4(SourceRGB8ToLinear54(SourceLookup54(family,k).rgb),alpha);}'''
s=s.replace(at,branch+at);(H/'Independent60.shader').write_text(s,encoding='utf8')
s=read('Assets/EUnityValidation01/MinimalRestore335/Shaders/RestoreStyle335.compute');s=s.replace('#pragma kernel Restore','#pragma kernel Restore\n#include "'+A+'/SourcePalette54.hlsl"\nStructuredBuffer<uint> _RoleFamily60;',1)
at='float old=cls.x,q=mask.x;if(abs(old-q)<.01)return;';assert s.count(at)==1
branch='''float old=cls.x,q=mask.x;int role60=(int)round(m.y)-1;uint familyOne=role60>=0&&role60<16?_RoleFamily60[role60]:0;if(familyOne>0){uint family=familyOne-1,n=_SourcePalette54Families[family].y;uint k=(uint)clamp(round(q*max(1,n-1)),0,n-1);float4 colour=_ShadeLit335.Load(int3(p,0));cls.x=q;_ShadeColourOut335[p]=float4(SourceRGB8ToLinear54(SourceLookup54(family,k).rgb),colour.a);_ShadeFactorOut335[p]=float4(1,1,1,cls.a);_ShadeClassOut335[p]=cls;return;}if(abs(old-q)<.01)return;'''
s=s.replace(at,branch);(H/'RestoreStyle60.compute').write_text(s,encoding='utf8')
(H/'SourcePalette54.hlsl').write_bytes((R.parent/'source-palette58/SourcePalette54.hlsl').read_bytes())
for p in list(H.iterdir()):
 if p.suffix=='.meta':continue
 meta=p.with_name(p.name+'.meta')
 if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n',encoding='utf8')
shaderGlobals={}
for root in [P/'Assets/EUnityValidation01',P/'Assets/Scripts']:
 for p in root.rglob('*.cs'):
  if 'Editor' in p.parts:continue
  s=p.read_bytes().decode('latin1') # ASCII setter scan; do not rewrite mixed-encoding source.
  for typ,name in re.findall(r'(?:Shader|cmd|c\.cmd)\.SetGlobal(Float|Int|Vector|Matrix|Texture)\s*\(\s*"([^"]+)"',s):
   shaderGlobals.setdefault(name,set()).add(typ)
globalsList=[{'name':n,'type':sorted(t)[0]}for n,t in sorted(shaderGlobals.items()) if len(t)==1]
(R/'GLOBAL_NAMES60.json').write_text(json.dumps(globalsList,indent=2),encoding='utf8')
def git(*args):
 r=subprocess.run(['git','-C',str(P),*args],capture_output=True,encoding='utf8');assert r.returncode==0,r.stderr;return r.stdout
baseline={'head':git('rev-parse','HEAD').strip(),'status':git('status','--porcelain=v1','--untracked-files=all').splitlines(),'protected':{n:hashlib.sha256((P/n).read_bytes()).hexdigest()for n in git('diff','--name-only').splitlines()if(P/n).is_file()},'globals':len(globalsList),'shaderAssets':[A+'/'+p.name for p in H.iterdir()],'playExecuted':False}
(R/'DISK_BASELINE60.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'assets':len(baseline['shaderAssets']),'knownScalarTextureGlobals':len(globalsList),'protectedFiles':len(baseline['protected']),'head':baseline['head']}))
