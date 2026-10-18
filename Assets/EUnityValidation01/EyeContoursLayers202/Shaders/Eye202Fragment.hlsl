float _E202Part;
struct Eye202Output {float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 uvControl:SV_Target2;float4 world:SV_Target3;};
Eye202Output Eye202Fragment(const FragmentInput f){
 if(_E202Part==5 && max(f.varyings.e202Control.x,f.varyings.e202Control.y)<=1e-5)clip(-1);
 float4 c=MToonFragment(f);if(c.a<=1e-6)clip(-1);
 uint role=(uint)round(_E151Role);float owner=role<=6?round(f.varyings.e202Owner):0;
 Eye202Output o;o.rgba=c;o.meta=float4(-TransformWorldToView(f.varyings.positionWS).z,role+1,owner,c.a);
 o.uvControl=float4(GetMToonGeometry_Uv(f.varyings.uv),f.varyings.e202Control);
 o.world=float4(f.varyings.positionWS,1);return o;
}
