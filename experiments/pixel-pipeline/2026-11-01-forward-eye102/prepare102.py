from pathlib import Path
import sys
H=Path(__file__).resolve().parent;R=H.parent;O=R/'layer-zero101/captureB';D=H/'capture'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
def main():
 D.mkdir(exist_ok=False);base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
 deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'hair-isolation100/HairDrawScope100.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',R/'live-underlay98/LiveSurface96.cs',R/'live-underlay98/WholeEye96.cs',R/'final-eye95/MotionScope95.cs',H/'ForwardCanvas102.cs',H/'Sequence102.cs']
 for mode in ['Read','Compile','Capture','Post','Verify']:
  s=(O/(mode+'101.cs')).read_text(encoding='utf-8').replace(str(O),str(D)).replace('101','102').replace('HairDrawScope100','Sequence102').replace('LayerZero102','LayerZero101')
  if mode in ['Compile','Capture']:
   s=s.replace('LayerZero101 layer102;','LayerZero101 layer102; ForwardCanvas102 forward102;')
   find='calibrated89=true;armed102=true;';replace='forward102=new ForwardCanvas102(probeEye,layer102,@"'+str(R/'native-feature89/REGISTRATION89.json')+'",Path.Combine(output,"REGISTRATION_CURRENT102.json"));'+find;s=s.replace(find,replace)
   s=s.replace('void Release76(){layer102?.Dispose();','void Release76(){forward102?.Dispose();report["forward102Disposed"]=forward102==null||forward102.Disposed;layer102?.Dispose();')
   s=s.replace('Bounded3-state product77 hair isolation budget','Bounded9-state forward eye/actual evaluated Close budget')
   a=s.index(' void Capture(');s=s[:a]+(H/'CaptureFragment102.cs').read_text(encoding='utf-8')+'\n}\n'
  p=D/(mode+'102.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],D/('RUN_'+mode+'102.cs.txt'))
 (D/'GLOBAL_NAMES66.json').write_bytes((O/'GLOBAL_NAMES66.json').read_bytes());relay=(O/'relay101.py').read_text(encoding='utf-8').replace("'Import101')","'Import101','Read102','Compile102','Capture102','Post102','Verify102','Import102')");(D/'relay102.py').write_text(relay,encoding='utf-8')
 source=(R/'live-underlay98/WholeEye98.compute').read_text(encoding='utf-8')if(R/'live-underlay98/WholeEye98.compute').exists()else None
 if source is None:source=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\EyeBoundaryRestore348\Shaders\WholeEye98.compute').read_text(encoding='utf-8')
 fragment='tests++;Tri96 t=_Triangles96[nd.z];';assert source.count(fragment)==1
 source=source.replace(fragment,fragment+'if(t.source.x!=1||t.source.y!=3)continue; //102 external occlusion does not alter canonical eye allocation\n')
 source='#pragma kernel ComposeForward102\n'+source+'\n'+(H/'ComposeForward102.hlsl').read_text(encoding='utf-8')
 (H/'ForwardEye102.compute').write_text(source,encoding='utf-8')
 s=(R/'layer-zero101/Import101.cs').read_text(encoding='utf-8').replace('101','102').replace('LayerZero102.shader','ForwardEye102.compute').replace('var s=AssetDatabase.LoadAssetAtPath<Shader>(path);','var s=AssetDatabase.LoadAssetAtPath<ComputeShader>(path);').replace('ShaderUtil.GetShaderMessages(s)','ShaderUtil.GetComputeShaderMessages(s)').replace('["supported"]=s.isSupported,','')
 s=s.replace(str(R/'layer-zero102/capture'),str(D));p=H/'Import102.cs';p.write_text(s,encoding='utf-8');bundle([R/'apply-capture66/Json58Linear66.cs',R/'eye-observer73/CreateOnly73.cs',p],D/'RUN_Import102.cs.txt');print('102 prepared: internal native skin visibility only, canonical selection then external hair, no old eye/backing input')
if __name__=='__main__':main()
