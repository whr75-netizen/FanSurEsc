"""Isolated continuous producer/consumer wiring. Never import or dispatch here."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;R=H.parents[1]
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
ASSET='Assets/EUnityValidation01/HeadHair25/ForwardEye113_HeadHair25.compute'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    base=REPO/'Assets/EUnityValidation01/Direct24Carrier/ForwardEye113_Geometry24.compute'
    code=base.read_text(encoding='utf-8')
    old='float2 Destination24(int2 p,int si){uint x=(uint)si%4u,y=(uint)si/4u;return float2(_ForwardROI102.x+p.x+(x+.5)/4,272-(_ForwardROI102.y+p.y+(y+.5)/4));}'
    new='''Texture2D<float4> _HeadHairRGBA25,_HeadHairMeta25;int2 _HeadHairSize25;
// Full319View335.Project basis: X right/Y DOWN. Raw RT address Y is reversed.
float2 Destination24(int2 p,int si){
 float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));
 int2 cell=(int2)floor(centre-_ForwardAnchor102.xy);uint x=(uint)si%4u,y=(uint)si/4u;
 return _ForwardAnchor102.xy+float2(cell)+float2((x+.5)/4,1-(y+.5)/4);
}'''
    assert code.count(old)==1;code=code.replace(old,new)
    old='for(int y=0;y<4;y++)for(int x=0;x<4;x++){int i=y*4+x;float4 h=_HairMeta102.Load(int3(p*4+int2(x,y),0)),v=_HairRGBA102.Load(int3(p*4+int2(x,y),0));if(h.x<=0||h.w<=0||v.a<=0)continue;'
    new='''for(int y=0;y<4;y++)for(int x=0;x<4;x++){int i=y*4+x;float4 h,v;
  if(chosenPart>0){
   int2 hp=int2(cell.x*4+x,(_CellsSize113.y-1-cell.y)*4+y);
   if(any(_HeadHairSize25!=_CellsSize113*4)||any(hp<0)||any(hp>=_HeadHairSize25)){hairHi+=1;continue;}
   h=_HeadHairMeta25.Load(int3(hp,0));v=_HeadHairRGBA25.Load(int3(hp,0));
  }else{h=_HairMeta102.Load(int3(p*4+int2(x,y),0));v=_HairRGBA102.Load(int3(p*4+int2(x,y),0));}
  if(h.x<=0||h.w<=0||v.a<=0)continue;'''
    assert code.count(old)==1;code=code.replace(old,new)
    code='\n'.join(l.rstrip()for l in code.splitlines()).rstrip()+'\n'
    assert 'EvaluateForm115'not in code and 'BoundRun115'not in code
    assert code.count('#pragma kernel')==base.read_text().count('#pragma kernel')
    compute=H/'ForwardEye113_HeadHair25.compute';compute.write_text(code,encoding='utf-8',newline='\n')
    surface=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeSurface348.shader'
    code=surface.read_text(encoding='utf-8')
    old='Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);'
    new='float4x4 _HeadHairGPUVP25;\nVaryings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.pos=mul(_HeadHairGPUVP25,float4(o.positionWS,1));'
    assert code.count(old)==1;code=code.replace(old,new).replace('Shader "EValidation/EyeSurface348"','Shader "Hidden/EValidation/HeadHair25"')
    shader=H/'HeadHair25.shader';shader.write_text(code,encoding='utf-8',newline='\n')
    forward=R/'bounded-form115/runtime24/Forward113_Geometry24.cs';code=forward.read_text(encoding='utf-8')
    code=code.replace('Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute',ASSET)
    code=code.replace('public readonly RegionDriver113 Region;','public readonly HeadHair25 HeadHair;public readonly RegionDriver113 Region;')
    code=code.replace('["region113"]=Region.Info,','["headHair25"]=new Obj58{["origin"]=new Arr58(HeadHair.Origin.x,HeadHair.Origin.y),["size"]=new Arr58(HeadHair.Width,HeadHair.Height),["frame"]=HeadHair.RenderedFrame,["gpuVP"]=new Arr58(Enumerable.Range(0,16).Select(i=>(double)HeadHair.GPUVP[i])),["ownedBytes"]=HeadHair.OwnedBytes},["region113"]=Region.Info,')
    old='Region=new RegionDriver113(e);';assert code.count(old)==1;code=code.replace(old,'HeadHair=new HeadHair25(e);'+old)
    code=code.replace('catch{Region?.Dispose();','catch{HeadHair?.Dispose();Region?.Dispose();')
    old='Curves.Update(native.Anchor96,native.Bounds96);Targets();';assert code.count(old)==1
    code=code.replace(old,'Curves.Update(native.Anchor96,native.Bounds96);HeadHair.Record(graph,resources,native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y),engine.Width,engine.Height);Targets();')
    old='foreach(var t in Fields.Concat(BaselineFields).Concat(LegacyFields))';assert code.count(old)==1
    code=code.replace(old,'foreach(var t in HeadHair.Fields)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);'+old)
    old='Region.ComposeBindings(cmd,cs,k,CarrierSource.Engine);';assert code.count(old)==1
    code=code.replace(old,old+'HeadHair.Bind(cmd,cs,k,native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y));')
    code=code.replace('canvas.AssertRendered();native.AssertRendered();','canvas.AssertRendered();HeadHair.AssertRendered();native.AssertRendered();')
    code=code.replace('if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;Region?.Dispose();','if(canvas.AfterCanvas==Record)canvas.AfterCanvas=null;HeadHair?.Dispose();Region?.Dispose();')
    source=H/'Forward113_HeadHair25.cs';source.write_text(code,encoding='utf-8',newline='\n')
    report={'baseSHA256':sha(base),'sourceShaderSHA256':sha(surface),'candidateShaderSHA256':sha(compute),'headSurfaceSHA256':sha(shader),'forwardSHA256':sha(source),
        'outsideAssets':True,'newComputeKernels':0,'newBuffers':0,'newDraws':4,'maxFinePixels':32768,'maxOwnedRTBytes':32768*84,
        'safety':['No globals or InputSettings changes','No EvaluateForm115/BoundRun115','Physical S4 retained for control/non-eye canvas','Unknown capture is not transparent'],
        'UnityGPUCalls':0,'runtimeApplied':False}
    (H/'PREPARED.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(json.dumps(report))
if __name__=='__main__':main()
