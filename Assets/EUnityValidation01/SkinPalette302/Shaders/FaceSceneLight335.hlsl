// Separate unlit colour and illumination; no source RGB feeds light quantization.
#include "Assets/EUnityValidation01/SkinPalette302/Shaders/HairRamp335.hlsl"
// Existing file identity retained when superseding the earlier binary face-light trial.
float _SurfaceLayers335,_ShadeLayer335,_FaceShadeSteps335,_SurfaceShadeSteps335,_SurfaceOwnShade335;
int _SurfaceLayerView335;float4 _SurfaceInvRaster335;
float _FaceShadeTint335,_SurfaceMaskReady335;float4 _FaceShadeChromaticity335;
float _Toon3DEnabled399,_ToonAlbedoSimplify399,_ToonShadeSteps399,_ToonShadowTint399,_ToonHairHighlight399;
Texture2D<float4> _SurfaceShadeMask335;
// Stage 1 (3D Shader): simplify noisy 3D texture albedo into clean cel color blocks BEFORE pixelization.
// Eyes, eyelines, brows, and mouth (roles 0,1,2,4,5,6) remain 100% crisp and untouched.
float3 CelSimplifyAlbedo399(float3 c,int role){
 if(_Toon3DEnabled399<=.5||_ToonAlbedoSimplify399<=.5)return c;
 if(role<=2||role==4||role==5||role==6)return c;
 float3 g=pow(max(c,0.0),1.0/2.2);
 float y=dot(g,float3(.2126,.7152,.0722));
 float bands=6.0;
 float qy=floor(saturate(y)*bands+.5)/bands;
 float ny=lerp(y,qy,.75);
 float3 chroma=(g-y)*1.08;
 return pow(saturate(ny+chroma),2.2);
}
// Provider skin uses the same current-view discrete mask as the surface pass.
float ProviderSurfaceLevel335(float level,int role,float2 position,float depth){
 float result=level;
 if(_SurfaceMaskReady335>.5&&(role==3||(role>=11&&role<=14))){float4 m=_SurfaceShadeMask335.Load(int3((int2)position,0));
  if(abs(m.a-(role+1))<.1&&abs(m.b-depth)<1e-3)result=m.r;}
 return result;
}
bool LayeredRole335(int role){return role==3||(role>=7&&role<=14);}
float Luminance335(float3 c){return dot(max(c,0),float3(.2126,.7152,.0722));}
void AccumulateSurfaceLight335(Light light,float3 normalWS,inout float lit,inout float available){
 float weight=Luminance335(light.color)*max(light.distanceAttenuation,0);
 // Stage 1 (3D Cel): hard-quantize cast shadows so blurry PCF shadows become crisp cel shadow bands.
 float visible=_Toon3DEnabled399>.5?step(.45,saturate(light.shadowAttenuation)):saturate(light.shadowAttenuation);
 float ndl=dot(normalWS,light.direction);
 float diffuse=_Toon3DEnabled399>.5?saturate(ndl*.65+.35):saturate(ndl*.5+.5);
 lit+=weight*visible*diffuse;available+=weight;
}
float ContinuousSurfaceLight335(const Varyings input,const MToonInput material){
 float3 normalWS=normalize(material.normalWS);
 float ambient=Luminance335(SampleSH(normalWS));
 float lit=ambient,available=ambient;
 float4 shadowCoord=TransformWorldToShadowCoord(input.positionWS);
 #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
 shadowCoord=ComputeScreenPos(TransformWorldToHClip(input.positionWS));
 #endif
 half4 shadowMask=SAMPLE_SHADOWMASK(input.lightmapUV);
 Light mainLight=GetMainLight(shadowCoord,input.positionWS,shadowMask);
 AccumulateSurfaceLight335(mainLight,normalWS,lit,available);
 #if defined(_ADDITIONAL_LIGHTS) || USE_CLUSTER_LIGHT_LOOP
 InputData inputData=(InputData)0;inputData.positionWS=input.positionWS;inputData.normalWS=normalWS;
 float2 screenUV=input.pos.xy*_SurfaceInvRaster335.xy;TransformNormalizedScreenUV(screenUV);inputData.normalizedScreenSpaceUV=screenUV;
 #if USE_CLUSTER_LIGHT_LOOP
 [loop] for(uint lightIndex=0;lightIndex<min(URP_FP_DIRECTIONAL_LIGHTS_COUNT,MAX_VISIBLE_LIGHTS);lightIndex++){
  CLUSTER_LIGHT_LOOP_SUBTRACTIVE_LIGHT_CHECK
  Light light=GetAdditionalLight(lightIndex,input.positionWS,shadowMask);
  AccumulateSurfaceLight335(light,normalWS,lit,available);
 }
 #endif
 uint pixelLightCount=GetAdditionalLightsCount();
 LIGHT_LOOP_BEGIN(pixelLightCount)
  Light light=GetAdditionalLight(lightIndex,input.positionWS,shadowMask);
  AccumulateSurfaceLight335(light,normalWS,lit,available);
 LIGHT_LOOP_END
 #endif
 return available>1e-6?saturate(lit/available):0;
}
float QuantizedSurfaceLight335(float continuous,int role){
 float levels=_Toon3DEnabled399>.5?max(2,round(_ToonShadeSteps399)):max(2,round(role==3?_FaceShadeSteps335:_SurfaceShadeSteps335));
 return floor(saturate(continuous)*(levels-1)+.5)/(levels-1);
}
float3 CelShadowTint399(int role){
 float t=saturate(_ToonShadowTint399);
 if(role==3||role==7)return lerp(float3(1,1,1),float3(1.10,.88,.82),t);
 if(role>=11&&role<=14)return lerp(float3(1,1,1),float3(.84,.88,1.14),t);
 return lerp(float3(1,1,1),float3(.86,.90,1.12),t);
}
float3 ShadeFactor335(float2 uv,int role,float level){
 // Illumination never reads the per-pixel colour layer. Preserve its texture detail.
 float3 minimumShade=_SurfaceOwnShade335.xxx;
 if(_Toon3DEnabled399>.5){
  minimumShade=(_SurfaceOwnShade335*.86)*CelShadowTint399(role);
 }else if(role==3&&_FaceShadeTint335>.5){
  minimumShade*=_FaceShadeChromaticity335.rgb;
 }
 if(_Auto245MembershipEnabled>.5&&role==7&&tex2D(_Auto245StockMember,uv).r>.5){
  // Existing region constants, independent of sampled albedo; no new tint.
  float3 reference=_Auto245StockLit.rgb;
  minimumShade=float3(reference.r>0?_Auto245StockShade.r/reference.r:1,reference.g>0?_Auto245StockShade.g/reference.g:1,reference.b>0?_Auto245StockShade.b/reference.b:1);
 }
 if(_Auto245MembershipEnabled>.5&&role>=11&&role<=14)return _ShadeLayer335>.5?HairAnchor335()*lerp(minimumShade,1,level):1;
 return _ShadeLayer335>.5?lerp(minimumShade,1,level):1;
}
// Stage 1 (3D Cel): hard-stepped anime cel hair highlight band ("angel ring") computed in 3D before pixelization.
float3 CelHairHighlight399(const Varyings input,const MToonInput material,float3 baseColour,int role,float level){
 if(_Toon3DEnabled399<=.5||_ToonHairHighlight399<=.5||_ShadeLayer335<=.5)return 0;
 if(role<11||role>14||level<.49)return 0;
 float4 shadowCoord=TransformWorldToShadowCoord(input.positionWS);
 #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
 shadowCoord=ComputeScreenPos(TransformWorldToHClip(input.positionWS));
 #endif
 Light mainLight=GetMainLight(shadowCoord,input.positionWS,SAMPLE_SHADOWMASK(input.lightmapUV));
 float litMask=step(.45,saturate(mainLight.shadowAttenuation))*step(.05,dot(normalize(material.normalWS),mainLight.direction));
 float3 H=normalize(mainLight.direction+material.viewDirWS+float3(0,.22,0));
 float ndh=saturate(dot(normalize(material.normalWS),H));
 float band=step(.84,ndh)*litMask;
 float lum=Luminance335(baseColour);
 float3 darkSheen=float3(.055,.062,.095);
 float3 brightSheen=baseColour*.32+float3(.05,.045,.04);
 return band*lerp(darkSheen,brightSheen,saturate((lum-.04)*6.0));
}
float3 SurfaceLayerOutput335(float3 colour,float3 factor,float continuous,float quantized){
 if(_SurfaceLayerView335==1)return colour;
 if(_SurfaceLayerView335==2)return continuous.xxx;
 if(_SurfaceLayerView335==3)return quantized.xxx;
 return colour*factor;
}
