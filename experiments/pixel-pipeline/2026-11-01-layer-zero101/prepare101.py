from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; OLD=ROOT/'hair-isolation100/capture'; OUT=HERE/'capture'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle

def main():
 global OUT
 if sys.argv[1:]:
  assert sys.argv[1:]==['--revision-b'];OUT=HERE/'captureB'
 OUT.mkdir(exist_ok=False)
 base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs']
 deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'hair-isolation100/HairDrawScope100.cs',ROOT/'source-palette58/SourcePalette58.cs',ROOT/'renderer-family59/RendererFamily59.cs',HERE/'SkinSource101.cs',HERE/'LayerZero101.cs']
 for mode in ['Read','Compile','Capture','Post','Verify']:
  s=(OLD/(mode+'100.cs')).read_text(encoding='utf-8').replace(str(OLD),str(OUT)).replace('100','101').replace('HairDrawScope101','HairDrawScope100')
  if mode in ['Compile','Capture']:
   s=s.replace('bool armed101;','bool armed101; LayerZero101 layer101;')
   s=s.replace('calibrated89=true;armed101=true;','layer101=new LayerZero101(probeEye,@"'+str(ROOT/'renderer-family59/SOURCE_REGISTRY59.json')+'");calibrated89=true;armed101=true;')
   s=s.replace('void Release76(){','void Release76(){layer101?.Dispose();report["layer101Disposed"]=layer101==null||layer101.Disposed;')
   s=s[:s.index(' void Capture(')]+(HERE/'CaptureFragment101.cs').read_text(encoding='utf-8')+'\n}\n'
  p=OUT/(mode+'101.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture'] else base)+[p],OUT/('RUN_'+mode+'101.cs.txt'))
 (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
 s=(OLD/'relay100.py').read_text(encoding='utf-8').replace("'Post100','Verify100')","'Post100','Verify100','Read101','Compile101','Capture101','Post101','Verify101','Import101')")
 (OUT/'relay101.py').write_text(s,encoding='utf-8')
 shader=(ROOT/'live-underlay98/CurrentNonEye98.shader').read_text(encoding='utf-8')
 shader=shader.replace('Shader "','Shader "',1)
 first=shader.index('{');shader='Shader "Hidden/EUnity/LayerZero101"\n'+shader[first:]
 a=shader.index('float4x4 _ProbeGPUVP91;');b=shader.index('ENDHLSL',a)
 shader=shader[:a]+(HERE/'LayerZeroFragment101.hlsl').read_text(encoding='utf-8')+'\n'+shader[b:]
 (HERE/'LayerZero101.shader').write_text(shader,encoding='utf-8')
 print('Prepared101: isolated clean canvas, source registry + native skin UV ring, original product77 unchanged')
if __name__=='__main__':main()
