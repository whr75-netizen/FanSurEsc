// Current source-carrier contract already established by the parent kernel.
// Region IDs and palette family are distinct; this fixture has one exact-source
// family with multiple connected regions. Other source colours stay unknown.
Texture2D<float4> _SourceRegionMask67,_SourcePalette67;
RWTexture2D<float4> _PaletteReceipt67;
int2 _SourceMaskSize67,_SourceWrap67;int _SourceLevels67,_PaletteEnabled67;
int WrapSource67(int p,int size,int mode){
 if(mode==1)return clamp(p,0,size-1);
 int period=mode==2?2*size:size;int r=((p%period)+period)%period;
 return mode==2&&r>=size?2*size-1-r:r;
}
float4 SourceRegion67(int2 p){return _SourceRegionMask67.Load(int3(WrapSource67(p.x,_SourceMaskSize67.x,_SourceWrap67.x),WrapSource67(p.y,_SourceMaskSize67.y,_SourceWrap67.y),0));}
bool ResolveSourcePalette67(float4 uv,out float3 rgb,out float4 receipt){
 rgb=0;receipt=float4(0,-1,uv.z,0);if(_PaletteEnabled67==0)return false;
 float2 texel=uv.xy*float2(_SourceMaskSize67)-.5;if(!all(isfinite(texel))||any(abs(texel)>2147483000.0)){receipt.w=-2;return false;}int2 p=(int2)floor(texel);
 float4 a=SourceRegion67(p),b=SourceRegion67(p+int2(1,0)),c=SourceRegion67(p+int2(0,1)),d=SourceRegion67(p+1);
 if(a.a!=1||any(a!=b)||any(a!=c)||any(a!=d))return false;
 float region=dot(round(a.rgb*255),float3(1,256,65536));
 if(region<1||_SourceLevels67<2||_SourceLevels67>256){receipt.w=-1;return false;}
 int k=(int)round(uv.z*(_SourceLevels67-1));if(k<0||k>=_SourceLevels67||uv.z!=(float)k/(float)(_SourceLevels67-1)){receipt.w=-1;return false;}
 rgb=_SourcePalette67.Load(int3(k,0,0)).rgb;receipt=float4(region,k,uv.z,1);return true;
}
