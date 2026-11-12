"""One new bounded raster consumer; normal6 motion, no default switch.

Current source/value table and explicit original-hue policy are distinct from
the legacy face tint. Previous actual GPU Q leases/invalidation reuse85.
"""
from pathlib import Path
import json,hashlib,numpy as np
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face89'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 for d in ['build','capture','final','post/final','import','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final','import'])
 info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());values=np.load(H/'face88/SOURCE_VALUE88.npz');a=np.zeros((1024,1024),'<f4');ox,oy=info['cropOffset'];h,w=values['mask'].shape;a[oy:oy+h,ox:ox+w]=np.where(values['mask'],values['labels']+1,0);a[::-1].copy().tofile(H/'face88/ADDRESS89.r32');table={'width':1024,'height':1024,'renderer':spec['rendererOrdinal'],'submesh':spec['subMesh'],'modelSHA':info['modelSHA256'],'imageSHA':info['sourceImageSHA256'],'sourceValueCount':len(values['referenceIndices']),'addressSHA':sha(H/'face88/ADDRESS89.r32'),'referenceSHA':sha(H/'face88/REFERENCE88.rgb'),'ordersSHA':sha(H/'face88/ORDERS88.i32'),'controlSHA':sha(H/'face88/PALETTE88.rgb'),'sourceSupportNotColourAddress':True,'completeObservedSourceMask':True};(H/'face88/TABLE89.json').write_text(json.dumps(table,indent=2))
 shader=(H/'ShadeHistory85.shader').read_text().replace('EValidation/ShadeHistory85','EValidation/SourceValue89').replace('Texture2D<float4> _PreviousAtlas85','int _Role89;Texture2D<float4> _PreviousAtlas85').replace('meta.y==4','meta.y==_Role89');shader=shader.replace('float4 F84(V v):SV_Target{','''Texture2D<float> _Address89;Texture2D<float4> _Control89,_Palette89,_Original89;int _Families89;float2 _Size89,_Wrap89;
 int Wrap89(int p,int n,int mode){if(mode==1)return clamp(p,0,n-1);if(mode==0)return(p%n+n)%n;int q=(p%(2*n)+2*n)%(2*n);return q<n?q:2*n-1-q;}
 float4 F84(V v):SV_Target{''')
 needle='if(plane==15)return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));return Candidate85(hp,cls,meta,uv,hu,hm);';assert shader.count(needle)==1
 shader=shader.replace(needle,'''if(plane==15)return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));float4 history=Candidate85(hp,cls,meta,uv,hu,hm);if(plane==16)return history;
  float4 before=_Before84.Load(int3(np,0));if(!known){if(plane==20||plane==21)return 0;return before;}
  int2 site=(int2)floor(uv.xy*_Size89);site=int2(Wrap89(site.x,(int)_Size89.x,(int)_Wrap89.x),Wrap89(site.y,(int)_Size89.y,(int)_Wrap89.y));int family=(int)round(_Address89.Load(int3(site,0)))-1;int k=(int)round(cls.x*(_Levels85-1)),kh=(int)round(history.x*(_Levels85-1));bool valid=family>=0&&family<_Families89&&k>=0&&k<_Levels85&&kh>=0&&kh<_Levels85&&history.w==1;
  if(plane==20)return float4(valid?family+1:-1,k,kh,1);if(plane==21)return _Original89.Load(int3(site,0));if(!valid)return float4(-10,0,0,-1);
  float4 colour=plane==17?_Control89.Load(int3(kh,family,0)):_Palette89.Load(int3(plane==18?k:kh,family,0));return float4(colour.rgb,before.a);''');(H/'SourceValue89.shader').write_text(shader,encoding='utf-8',newline='\n')
 s=(H/'face85/pulse120/capture/RUN.cs.txt').read_text();s='#define CAPTURE89\n'+s;s=s.replace('resume-20261111\\face85\\pulse120\\capture','resume-20261111\\face89\\capture').replace('face85-source-Q-pulse120-','face89-source-value-Q-').replace('motion40.FirstTarget,120,16,motion40.Snapshot','motion40.FirstTarget,6,1,motion40.Snapshot').replace('["plannedSourceFrames"]=120','["plannedSourceFrames"]=6')
 # Retain the same supported move/idle path for this initial six-frame capture.
 # Both RGB candidates and the native control use each exact same source frame.
 s=s.replace('W77*17','W77*22').replace('17*W77','22*W77').replace('bottom-left17layers selectedLight84/sourceQhistory85','bottom-left22layers sourceValue89/currentQ-and-historyQ').replace('["layers"]=17','["layers"]=22')
 s=s.replace('readonly SourceVertexWidth72 width72;readonly SourceZeroWidth69 zero69;','public readonly SourceField89 field89;readonly SourceVertexWidth72 width72;readonly SourceZeroWidth69 zero69;').replace('SourceFlatResource67(string root,EyeFeature348 eye)','SourceFlatResource67(string root,EyeFeature348 eye,string evidence89=null)').replace('new SourceFlatResource67(Path.Combine(H,"face67"),n.host.headEyes)','new SourceFlatResource67(Path.Combine(H,"face67"),n.host.headEyes,Root)')
 needle='   zero69=new SourceZeroWidth69(';assert s.count(needle)==1;s=s.replace(needle,'   field89=new SourceField89(Path.GetFullPath(Path.Combine(root,"..","face88")),eye,width,height,evidence89);\n'+needle)
 s=s.replace('if(disposed)return;width72?.Dispose();','if(disposed)return;field89?.Dispose();width72?.Dispose();').replace('public Obj40 Info()=>new Obj40{["vertexWidth72"]','public Obj40 Info()=>new Obj40{["sourceValue89"]=field89.Info(),["vertexWidth72"]')
 s=s.replace('Assets/EUnityValidation01/ShadeHistory85/ShadeHistory85.shader','Assets/EUnityValidation01/SourceValue89/SourceValue89.shader')
 needle='void PrepareCurve81(){previousLease85=false;';assert s.count(needle)==1;s=s.replace(needle,needle+'sourceFlat67.field89.Validate();')
 needle='   p.SetInt("_Width84",W77);';assert s.count(needle)==1;s=s.replace(needle,'''   p.SetTexture("_Address89",sourceFlat67.field89.address);p.SetTexture("_Control89",sourceFlat67.field89.control);p.SetTexture("_Palette89",sourceFlat67.field89.palette);p.SetTexture("_Original89",sourceFlat67.field89.original);p.SetInt("_Role89",sourceFlat67.MappedRole72);p.SetInt("_Families89",sourceFlat67.field89.palette.height);p.SetVector("_Size89",new Vector4(sourceFlat67.width,sourceFlat67.height,0,0));p.SetVector("_Wrap89",new Vector4(sourceFlat67.wrapU,sourceFlat67.wrapV,0,0));
'''+needle)
 # Refuse a partial source lookup rather than emit a successful mixed-LUT frame.
 needle='receipt["observedActorCells77"]=actorCount77;';assert s.count(needle)==1;s=s.replace(needle,'for(int yy=0;yy<W77;yy++)for(int xx=0;xx<W77;xx++){int b89=16*(yy*W77*22+20*W77+xx);if(BitConverter.ToSingle(bytes,b89)<0)throw new InvalidOperationException("89 incomplete visible source lookup; reject whole frame");}'+needle)
 s+='\n'+(H/'PaletteRuntime89.cs').read_text()+'\n'+(H/'SourceField89.cs.txt').read_text();assert 'EvaluateForm115'not in s and 'BoundRun115'not in s
 if G.name.startswith('fix'):s=s.replace('resume-20261111\\face89\\capture','resume-20261111\\face89\\'+G.name+'\\capture')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/colour89.dll')
 for mode in ['final','post/final']:
  t=(H/'face85/pulse120'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face85\\pulse120','resume-20261111\\face89'+('\\'+G.name if G.name.startswith('fix')else''));(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'89.dll'))
 imp=(H/'face85/import/RUN.cs.txt').read_text().replace('resume-20261111\\face85','resume-20261111\\face89').replace('ShadeHistory85','SourceValue89')
 old='string guid=(string)expected["guid"];if(!String.IsNullOrEmpty(AssetDatabase.GUIDToAssetPath(guid)))throw new InvalidOperationException("81 GUID collision");';assert imp.count(old)==1;imp=imp.replace(old,'string guid=null;')
 a=imp.index('CreateOnly40.Text(Target+".meta"');b=imp.index('using(var f=new FileStream(Target',a);imp=imp[:a]+imp[b:]
 imp=imp.replace('var shader=AssetDatabase.LoadAssetAtPath<Shader>(Target);','guid=AssetDatabase.AssetPathToGUID(Target);if(String.IsNullOrEmpty(guid)||AssetDatabase.GUIDToAssetPath(guid)!=Target)throw new InvalidOperationException("89 Unity-generated asset identity invalid");var shader=AssetDatabase.LoadAssetAtPath<Shader>(Target);')
 (G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import89.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'shaderSHA256':sha(H/'SourceValue89.shader'),'UnityGeneratesMeta':True},indent=2));(G/'console/ARGS.json').write_text((H/'face85/console/ARGS.json').read_text());result={'externalCSharp9Compiled':True,'plannedFrames':6,'newComputeDispatches':0,'newRasterPasses':1,'atlasBytes':22*26*26*16,'sourceAddressTextureBytes':4194304,'staticSourceAddresses':len(values['referenceIndices']),'CPUSelectionUploaded':False,'actualRuntimeLinearFloorRequired':True,'legacyFaceTintReapplied':False,'pixelColourOperation':'finite LUT load only','priorGPUQLeaseReused':True,'product77Changed':False,'GPUExecuted':False,'shaderSHA256':sha(H/'SourceValue89.shader')};(G/'CPU_PREPARED89.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
 import sys
 if '--fix1'in sys.argv:G=G/'fix1'
 if '--fix2'in sys.argv:G=G/'fix2'
 main()
