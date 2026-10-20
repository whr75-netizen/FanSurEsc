#ifndef HEAD_REGION_502
#define HEAD_REGION_502
Texture2D<float4> _Region502Mask;
float4x4 _Region502ViewProjection;
int _Region502Quad,_Region502Hair;
float _Region502Scale;
float4 _Region502OwnedShift;
Varyings Region502Vertex(const Attributes v)
{
    Attributes lighting=v;if(_Region502Quad!=0)lighting.vertex=v.semantic1;
    Varyings o=MToonVertex(lighting);
    float3 targetWS=TransformObjectToWorld(v.vertex.xyz);
    float4 projected=mul(_Region502ViewProjection,float4(targetWS,1));
    o.semanticMask.yz=float2(projected.x/projected.w*.5+.5,.5-projected.y/projected.w*.5)*float2(480,272);
    if(_Region502Quad!=0){o.pos=TransformWorldToHClip(targetWS);o.semanticMask.x=v.semantic0.x;}
    return o;
}
void Region502Clip(Varyings v)
{
    // SV_POSITION and Texture.Load share the actual attachment origin. Every
    // 2x2 native block belongs to the same canonical cell, regardless of the
    // original source's quarter-cell native sampling phase.
    int2 p=(int2)floor(v.pos.xy/_Region502Scale);if(any(p<0)||any(p>=int2(480,272)))discard;
    float4 m=_Region502Mask.Load(int3(p,0));
    if((_Region502Hair!=0?m.g:m.r)<.5)discard;
}
#endif
