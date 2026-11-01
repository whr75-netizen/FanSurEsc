from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'final-eye95/capture-scale-correct';OUT=HERE/'capture'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
    OUT.mkdir(exist_ok=False)
    base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'final-eye95/MotionScope95.cs',HERE/'WholeEye96.cs',HERE/'NativeRetarget96.cs',HERE/'GraphSources96.cs',HERE/'LiveSurface96.cs',HERE/'LiveGraph96.cs',HERE/'LiveFinal96.cs']
    for mode in ['Read','Compile','Capture','Post','Verify']:
        s=(OLD/(mode+'95B.cs')).read_text().replace(str(OLD),str(OUT)).replace('eye95b-','eye96-').replace('STATE95B-','STATE96-').replace('TRACE95B-','TRACE96-').replace('CURRENT95B.json','CURRENT96.json').replace('POST95B.json','POST96.json').replace('VERIFY95B.json','VERIFY96.json').replace('PRIOR47_CURRENT95B.json','PRIOR47_CURRENT96.json')
        if mode in ['Compile','Capture']:
            s=s.replace('NativeRetarget95','NativeRetarget96').replace('GraphSources95','GraphSources96')
            s=s.replace('GraphSources96 current91;','GraphSources96 current91;LiveGraph96 joint96;LiveFinal96 final96;')
            s=s.replace('current91=new GraphSources96(probeEye,retarget89);','joint96=new LiveGraph96(probeEye,retarget89,@"'+str(ROOT/'native-feature89/REGISTRATION89.json')+'");current91=new GraphSources96(probeEye,retarget89,joint96);final96=new LiveFinal96(n,retarget89,joint96,current91);')
            s=s.replace('current91?.Dispose();','final96?.Dispose();joint96?.Dispose();report["joint96Disposed"]=joint96==null||joint96.Disposed;current91?.Dispose();')
            # The native product output remains untouched. Capture both branches.
            needle='report["frameIndex"]=frameIndex;report["mainSerial"]=serial;'
            addition='''
    final96.Present(nativeROI87,probeROI);if(final96.Frame!=frameIndex||final96.Serial!=serial)throw new InvalidOperationException("96 source/frame/serial mismatch");
    for(int channel96=0;channel96<4;channel96++){var t96=final96.Output[channel96];string name96="live96-final"+channel96;CpuSourceCapture64.WriteOwnedPlane(Path.Combine(output,name96+".plane"),nativeFrame87,t96,new RectInt(0,0,t96.width,t96.height),"96 real-time GPU BVH, joint selection and current native composition","literal colour/Native395 owner/depth/audit","linear Float32","native crop bottom-left");planes.Add(new Obj58{["file"]=name96+".plane",["sourceId"]=sourceId,["frameIndex"]=frameIndex,["renderSerial"]=serial});}
    var engine96=joint96.Source.Engine;foreach(var field96 in new[]{new{n="visibility",b=engine96.Visibility},new{n="colour",b=engine96.Colour},new{n="identity",b=engine96.Identity},new{n="decision",b=engine96.Decisions}}){if(field96.b.count*16>1024*1024)throw new InvalidOperationException("96 bounded diagnostics");var a96=new Vector4[field96.b.count];field96.b.GetData(a96);using(var w96=new BinaryWriter(new FileStream(Path.Combine(output,"live96-"+field96.n+".buffer"),FileMode.CreateNew))){w96.Write(a96.Length);foreach(var q96 in a96){w96.Write(q96.x);w96.Write(q96.y);w96.Write(q96.z);w96.Write(q96.w);}}}
    var stats96=new uint[8];engine96.Stats.GetData(stats96);if(stats96[0]==0||stats96[4]!=0)throw new InvalidOperationException("96 queries absent or stack overflow");report["live96"]=new Obj58{["scope"]=joint96.Source.Scope,["frame"]=joint96.RecordedFrame,["serial"]=final96.Serial,["queryCount"]=stats96[0],["BVHVisits"]=stats96[1],["maximumNodesVisited"]=stats96[2],["triangleTests"]=stats96[3],["stackOverflow"]=stats96[4],["canonicalUnknown"]=stats96[5],["ownedBufferBytes"]=engine96.OwnedBytes,["runtimeReadbackCalls"]=0,["diagnosticReadbacksInCaptureOnly"]=true,["productOutputChanged"]=false};
'''
            assert needle in s;s=s.replace(needle,addition+'\n    '+needle)
        p=OUT/(mode+'96.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'96.cs.txt'))
    (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
    relay=(OLD/'relay95.py').read_text().replace("'Verify95B')","'Verify95B','Read96','Compile96','Capture96','Post96','Verify96')");(OUT/'relay96.py').write_text(relay,encoding='utf-8')
    print('Prepared live-source Graph + final composition capture; not executed.')
if __name__=='__main__':main()
