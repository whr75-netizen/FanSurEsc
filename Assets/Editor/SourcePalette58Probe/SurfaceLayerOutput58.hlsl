#include "SourcePalette54.hlsl"
int _SurfaceLayerView335;
// Narrow clone of the current function; extra source family is explicit.
float3 SurfaceLayerOutput335(float3 colour,float3 factor,float continuous,float quantized,uint sourceFamily58){
 if(_SurfaceLayerView335==1)return colour;
 if(_SurfaceLayerView335==2)return continuous.xxx;
 if(_SurfaceLayerView335==3)return quantized.xxx;
 return SourceRGB8ToLinear54(SourceLookup54(sourceFamily58,SourceShade54(sourceFamily58,continuous)).rgb);
}
