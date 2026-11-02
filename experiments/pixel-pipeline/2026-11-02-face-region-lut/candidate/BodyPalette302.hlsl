float _Style297Enabled,_Style297SkinMode,_Style297OwnShade;
float _Restore250Bottom;float4 _Restore250LowerLit,_Restore250LowerShade;
#define MToonFragment Auto245NativeOriginalFragment
#include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_fragment.hlsl"
#undef MToonFragment
float _Auto249Probe,_Auto249VisibilityOne;
float _Auto245Stage,_Auto245Local,_Auto245MembershipEnabled;
sampler2D _Auto245CreamMember,_Auto245StockMember,_Auto245FaceSkinMember,_Auto245BodySkinMember;
float4 _Auto245CreamShade,_Auto245SkinShade,_Auto245StockLit,_Auto245StockShade;

#include "FaceSceneLight335.hlsl"

// Reuse installed MToon reflectance. Radiance RGB is never passed to the palette.
half Auto245Shadow(const Varyings input,const MToonInput material){
 if(_Auto245Local<.5){UnityLighting lighting=GetUnityLighting(input,material.normalWS);if(_Auto249VisibilityOne>.5)lighting.directLightAttenuation=1;half ndotl=GetMToonLighting_DotNL(lighting,material);return GetMToonLighting_Shade(lighting,material,ndotl)>=.5?0:1;}
 half anyLit=0;
 #if defined(_ADDITIONAL_LIGHTS)
 uint pixelLightCount=GetAdditionalLightsCount();
 #if defined(USE_FORWARD_PLUS)
 InputData inputData=(InputData)0;inputData.normalizedScreenSpaceUV=GetNormalizedScreenSpaceUV(input.pos);inputData.positionWS=input.positionWS;
 LIGHT_LOOP_BEGIN(pixelLightCount)
 #else
 for(uint lightIndex=0u;lightIndex<pixelLightCount;lightIndex++){
 #endif
 UnityLighting lighting=GetAdditionalUnityLighting(input,material.normalWS,lightIndex);half ndotl=GetMToonLighting_DotNL(lighting,material);half lit=GetMToonURPAdditionalLighting_Shade(lighting,material,ndotl);

 // Hard shadow/range only decide membership; attenuation never scales final RGB.
 anyLit=max(anyLit,(lit>=.5&&lighting.directLightAttenuation.x>0)?1:0);
 #if defined(USE_FORWARD_PLUS)
 LIGHT_LOOP_END
 #else
 }
 #endif
 #endif
 return 1-anyLit;
}
void Auto245Palette(float2 uv,half3 ownLit,out half3 lit,out half3 shade){
 lit=ownLit;shade=MTOON_SAMPLE_TEXTURE2D(_ShadeTex,uv).rgb*_ShadeColor.rgb;
 if(_Auto245MembershipEnabled<.5)return;
 int role=(int)round(_Auto245Role);
 if(role>=11&&role<=14){lit=HairBase335(ownLit,role);shade=lit;}
 if(role==8&&_Restore250Bottom>.5){lit=_Restore250LowerLit.rgb;shade=_Restore250LowerShade.rgb;}
 if(role==10&&tex2D(_Auto245CreamMember,uv).r>.5){shade=_Auto245CreamShade.rgb;}
 if(role==3){shade=ownLit*.72;} // Existing A241 own-pigment shade endpoint, automatic mask replaces its old hand-authored region.
 if(role==7){if(tex2D(_Auto245StockMember,uv).r>.5){lit=_Auto245StockLit.rgb;shade=_Auto245StockShade.rgb;}else if(tex2D(_Auto245BodySkinMember,uv).r>.5){shade=_Auto245SkinShade.rgb;
 // 302 changes only true BodySkin shade RGB. Original pigment, lit RGB, masks, visibility and lighting decision stay intact.
 if(_Style297Enabled>.5 && _Style297SkinMode>.5)shade=ownLit*_Style297OwnShade;
 }}
}
float4 MToonFragment(const FragmentInput fragmentInput):SV_Target{
 const Varyings input=fragmentInput.varyings;UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
 const float2 uv=GetMToonGeometry_Uv(input.uv);const half4 source=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;const half alpha=GetMToonGeometry_Alpha(source);
 if(_Auto249Probe>.5)return float4(uv,_Auto245Role+1,alpha);
 MToonInput material;material.uv=uv;material.normalWS=GetMToonGeometry_Normal(input,fragmentInput.facing,uv);material.viewDirWS=normalize(input.viewDirWS);material.litColor=source.rgb;material.alpha=alpha;
 if(_Auto245Stage<.5)return half4(source.rgb,alpha);
 if(_SurfaceLayers335>.5&&LayeredRole335((int)round(_Auto245Role))){half3 baseColour,shadeEndpoint;Auto245Palette(uv,source.rgb,baseColour,shadeEndpoint);float continuous=ContinuousSurfaceLight335(input,material);float level=QuantizedSurfaceLight335(continuous,(int)round(_Auto245Role));level=ProviderSurfaceLevel335(level,(int)round(_Auto245Role),input.pos.xy,-TransformWorldToView(input.positionWS).z);float3 factor=ShadeFactor335(uv,(int)round(_Auto245Role),level);return float4(SurfaceLayerOutput335(baseColour,factor,continuous,level,(uint2)input.pos.xy),alpha);}
 half shadow=Auto245Shadow(input,material);
 if(_Auto245Stage<1.5)return half4(shadow.xxx,alpha);
 half3 lit,shade;Auto245Palette(uv,source.rgb,lit,shade);
 if(_Auto245Stage>3.5)return half4(shade,alpha);
 if(_Auto245Stage>2.5)return half4(lit,alpha);
 return half4(shadow>.5?shade:lit,alpha);
}
