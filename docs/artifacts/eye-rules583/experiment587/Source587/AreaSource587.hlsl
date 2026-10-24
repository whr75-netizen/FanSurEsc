#ifndef EYE_AREA_SOURCE_587
#define EYE_AREA_SOURCE_587
float _AreaDensity587;
float4 _AreaCentre587,_AreaAxisX587,_AreaAxisY587,_AreaUpper587;
// Same source alpha/material/cull/depth path. Density changes integration
// coordinates, not the original four-samples-per-cell texture footprint.
float4 AreaSource587(Varyings v,bool facing) {
 float2 uv=GetMToonGeometry_Uv(v.uv);
 float2 dx=ddx(uv)*(_AreaDensity587/4),dy=ddy(uv)*(_AreaDensity587/4);
 half4 src=SAMPLE_TEXTURE2D_GRAD(_MainTex,sampler_MainTex,uv,dx,dy)*_Color;
 half alpha=GetMToonGeometry_Alpha(src);if(alpha<=1e-6)discard;
 float3 d=v.restHead348-_AreaCentre587.xyz;
 float u=dot(d,_AreaAxisX587.xyz)/_AreaAxisX587.w;
 float y=-dot(d,_AreaAxisY587.xyz)/_AreaAxisY587.w;
 float upper=_AreaUpper587.x+_AreaUpper587.y*u*u;
 bool band=abs(u)<=1.08&&y>=upper-.36&&y<=upper+.22;
 return float4(-TransformWorldToView(v.positionWS).z,alpha,round(v.e202Owner)*(facing?1:-1),band?1:0);
}
#endif
