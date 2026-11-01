// Same expression order as ContinuousSurfaceLight335; outputs only. No RGB correction.
float ProbeLight91(const Varyings input,const MToonInput material,float facing91,out float4 normal91,out float4 sh91,out float4 sum91){
 float3 normalWS=normalize(material.normalWS);
 float3 shRGB91=SampleSH(normalWS);float ambient=Luminance335(shRGB91);
 float lit=ambient,available=ambient;
 float4 shadowCoord=TransformWorldToShadowCoord(input.positionWS);
 #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
 shadowCoord=ComputeScreenPos(TransformWorldToHClip(input.positionWS));
 #endif
 half4 shadowMask=SAMPLE_SHADOWMASK(input.lightmapUV);
 Light mainLight=GetMainLight(shadowCoord,input.positionWS,shadowMask);
 AccumulateSurfaceLight335(mainLight,normalWS,lit,available);float mainLit91=lit-ambient,mainAvailable91=available-ambient;
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
 normal91=float4(normalWS,facing91);sh91=float4(shRGB91,ambient);sum91=float4(lit,available,mainLit91,mainAvailable91);return available>1e-6?saturate(lit/available):0;
}
