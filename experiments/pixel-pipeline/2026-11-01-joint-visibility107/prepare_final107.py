"""New immutable final source bundles. Existing executed107 bundles are untouched."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;R=H.parent;D=H/'capture-final';C=H/'capture';OLD=R/'live-curve106'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
def plans():
    files={};s=(R/'hair-isolation100/HairDrawScope100.cs').read_text(encoding='utf-8').replace('HairDrawScope100','HairDrawScope107')
    marker=' static bool Equal(SubMeshDescriptor a,SubMeshDescriptor b)=>'
    pos=s.index(marker);end=s.index('\n',pos)
    exact=s[pos:end];draw=exact.replace('static bool Equal(','static bool EqualDraw(').replace('&&a.bounds==b.bounds','')
    s=s[:end]+'\n'+draw+s[end:]
    s=s.replace('void RestoreHair(){','void RestoreHair(bool full=true){').replace('for(int i=0;i<x.Value.Length;i++)x.Key.SetSubMesh(i,x.Value[i],MeshUpdateFlags.DontRecalculateBounds);','for(int i=0;i<x.Value.Length;i++){var d=x.Value[i];if(!full)d.bounds=x.Key.GetSubMesh(i).bounds;x.Key.SetSubMesh(i,d,MeshUpdateFlags.DontRecalculateBounds);}')
    line=next(x for x in s.splitlines()if x.startswith(' bool HairRestored()=>'));s=s.replace(line,line+'\n'+line.replace('HairRestored()','DrawRestored()').replace('Equal(d,','EqualDraw(d,'))
    inspect='''
 int inspectionFrame107=-1;
 static Obj58 Descriptor107(SubMeshDescriptor d)=>new Obj58{["start"]=d.indexStart,["count"]=d.indexCount,["topology"]=(int)d.topology,["base"]=d.baseVertex,["first"]=d.firstVertex,["vertices"]=d.vertexCount,["centre"]=new Arr58(d.bounds.center.x,d.bounds.center.y,d.bounds.center.z),["size"]=new Arr58(d.bounds.size.x,d.bounds.size.y,d.bounds.size.z)};
 void Inspect107(){if(inspectionFrame107==Time.frameCount)return;inspectionFrame107=Time.frameCount;var rows=new Arr58();foreach(var x in meshes)for(int i=0;i<x.Value.Length;i++){var a=x.Value[i];var b=x.Key.GetSubMesh(i);rows.Add(new Obj58{["mesh"]=x.Key.GetEntityId().ToString(),["submesh"]=i,["drawEqual"]=EqualDraw(a,b),["boundsEqual"]=a.bounds==b.bounds,["before"]=Descriptor107(a),["current"]=Descriptor107(b)});}CreateOnly73.Text(Path.Combine(directory,"HAIR_OBSERVATION107-frame"+Time.frameCount+".json"),new Obj58{["frame"]=Time.frameCount,["stage"]=index,["descriptors"]=rows,["renderers"]=new Arr58(renderers.Select(x=>new Obj58{["id"]=x.Key.GetEntityId().ToString(),["before"]=x.Value,["current"]=x.Key.enabled}))}.ToString());}
'''
    s=s.replace(' public Obj58 Snapshot(){',' '+inspect+'\n public Obj58 Snapshot(){Inspect107();')
    s=s.replace('index!=1&&!HairRestored()','index!=1&&!DrawRestored()').replace('index==1?false:HairRestored()','index==1?false:DrawRestored()')
    s=s.replace('else if(index==2){RestoreHair();if(!HairRestored())','else if(index==2){RestoreHair(false);if(!DrawRestored())')
    files[str(H/'HairDrawScope107.cs')]=s
    for mode in ['Read','Compile','Capture','Post']:
        s=(C/(mode+'107.cs')).read_text(encoding='utf-8').replace(str(C),str(D))
        if mode in ['Compile','Capture']:
            start=s.index(' Vector4[] JointSlice107(');s=s[:start]+(H/'CaptureFragment107.cs').read_text(encoding='utf-8')+'\n}\n'
        files[str(D/(mode+'Final107.cs'))]=s
    files[str(C/'ImportFinal107.cs')]=(C/'Import107c.cs').read_text(encoding='utf-8').replace('IMPORT107c.json','IMPORT_FINAL107.json')
    print(json.dumps(files),flush=True)
def build():
    base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',H/'NativeDense107.cs',H/'LiveSurface107.cs',H/'WholeEye107.cs',R/'live-underlay98/MotionScope97.cs',H/'HairDrawScope107.cs',OLD/'SourceCurves106.cs',H/'ForwardCanvas107.cs',OLD/'MotionClose106.cs',H/'HoldMorph107.cs',H/'Sequence107.cs']
    for mode in ['Read','Compile','Capture','Post']:
        target=C/('RUN_'+mode+'Final107.cs.txt');assert not target.exists(),target
        bundle((deps if mode in ['Compile','Capture']else base)+[D/(mode+'Final107.cs')],target)
    bundle(base+[C/'ImportFinal107.cs'],C/'RUN_ImportFinal107.cs.txt')
    (D/'GLOBAL_NAMES66.json').write_bytes((OLD/'capture/GLOBAL_NAMES66.json').read_bytes())
    wrapper=(C/'relay107.py').read_text(encoding='utf-8');lines=wrapper.splitlines();i=next(i for i,l in enumerate(lines)if l.startswith('assert mode in ('));lines[i]=lines[i].replace('(',"('ReadFinal107','CompileFinal107','CaptureFinal107','PostFinal107','ImportFinal107',",1);(C/'relay107.py').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Shader generation only, never rebuild old executed source bundles.
    shader='RWStructuredBuffer<float4> _QueryEvidence107;\n#pragma kernel ResolveCurve107\n'+(OLD/'ForwardEye106.compute').read_text(encoding='utf-8')+'\n'+(H/'JointCurve107.hlsl').read_text(encoding='utf-8')
    shader=shader.replace('_Visibility96[id.x]=0;if(meta.x<=0','_Visibility96[id.x]=0;_QueryEvidence107[id.x*2]=0;_QueryEvidence107[id.x*2+1]=0;if(meta.x<=0')
    shader=shader.replace('trans*=1-abounds.yx;if(trans.y<=0)break;', 'if(abounds.y>0&&(_QueryEvidence107[id.x*2].x==0||zz<_QueryEvidence107[id.x*2].y)){_QueryEvidence107[id.x*2]=float4(nd.z+1,zz,t.verticesMaterial.w+1,abounds.x);_QueryEvidence107[id.x*2+1]=float4(uv,abounds.y,depth);}trans*=1-abounds.yx;if(trans.y<=0)break;')
    (H/'ForwardEye107.compute').write_bytes(shader.encode('utf-8'));print('final107 bundles prepared once; previous sources remain frozen')
if __name__=='__main__':{'plans':plans,'build':build}[sys.argv[1]]()
