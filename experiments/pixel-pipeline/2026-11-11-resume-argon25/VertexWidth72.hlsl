// Bounded source scalar interpolation. Unity's sampler_ name uses the original
// texture's actual sampler. Vertex UV coordinates are the imported mesh UVs.
Texture2D<float2> _VertexUV72;
Texture2D<float4> _OriginalWidth72;SamplerState sampler_OriginalWidth72;
int _MappedRole72,_MappedCount72,_VertexUVStride72,_UseWidthMap72,_ExteriorRadius72;
float2 VertexUV72(int i){return _VertexUV72.Load(int3(i%_VertexUVStride72,i/_VertexUVStride72,0));}
bool SourceWidth72(int role,int primitive,float2 uvPoint,out float green){
 green=1;
 if(_UseWidthMap72==0||role!=_MappedRole72)return true;
 if(primitive<0||primitive>=_MappedCount72)return false;
 float2 a=VertexUV72(3*primitive),b=VertexUV72(3*primitive+1),c=VertexUV72(3*primitive+2);
 float3 values=float3(_OriginalWidth72.SampleLevel(sampler_OriginalWidth72,a,0).g,_OriginalWidth72.SampleLevel(sampler_OriginalWidth72,b,0).g,_OriginalWidth72.SampleLevel(sampler_OriginalWidth72,c,0).g);
 if(!all(isfinite(values))||any(values<0)||any(values>1))return false;
 if(values.x==values.y&&values.y==values.z){green=values.x;return true;}
 float2 ab=b-a,ac=c-a,ap=uvPoint-a;float det=ab.x*ac.y-ab.y*ac.x;
 // A UV-degenerate triangle with unequal vertex scalars has no inverse UV
 // carrier. Reject it; do not manufacture a barycentric coordinate or colour.
 if(det==0||!isfinite(det))return false;
 float v=(ap.x*ac.y-ap.y*ac.x)/det,w=(ab.x*ap.y-ab.y*ap.x)/det;float3 bary=float3(1-v-w,v,w);
 if(!all(isfinite(bary))||any(bary<0)||any(bary>1))return false;
 green=dot(values,bary);return isfinite(green)&&green>=0&&green<=1;
}
