Shader "Hidden/EUnity/T2_DirectionalProbe154"
{
    Properties
    {
        [HideInInspector] _PartGroup154("Integrated source part ID", Int) = 0
        [HideInInspector] _RegionBase154("Integrated palette region offset", Int) = 0
        [HideInInspector] _StockRampReady154("Authored stocking ramp is bound", Int) = 0
        [HideInInspector] _StockPartMember154("Original stocking membership", 2D) = "black" {}
        [HideInInspector] _UnderHair154("Same-ray nearest non-hair", 2D) = "black" {}
        [HideInInspector] _DirectionalWorld154("Directional world depth", 2D) = "black" {}
        [HideInInspector] _DirectionalSelf154("Root-aligned character depth", 2D) = "black" {}
        _Auto245Role("Original source material index",Float)=0
        _Source329Renderer("Original renderer input index",Float)=0
        // Rendering
        _AlphaMode ("alphaMode", Int) = 0
        _TransparentWithZWrite ("mtoon.transparentWithZWrite", Int) = 0
        _Cutoff ("alphaCutoff", Range(0, 1)) = 0.5 // Unity specified name
        _RenderQueueOffset ("mtoon.renderQueueOffsetNumber", Int) = 0
        _DoubleSided ("doubleSided", Int) = 0

        // Lighting
        _Color ("pbrMetallicRoughness.baseColorFactor", Color) = (1, 1, 1, 1) // Unity specified name
        _MainTex ("pbrMetallicRoughness.baseColorTexture", 2D) = "white" {} // Unity specified name
        _ShadeColor ("mtoon.shadeColorFactor", Color) = (1, 1, 1, 1)
        _ShadeTex ("mtoon.shadeMultiplyTexture", 2D) = "white" {}
        [Normal] _BumpMap ("normalTexture", 2D) = "bump" {} // Unity specified name
        _BumpScale ("normalTexture.scale", Float) = 1.0 // Unity specified name
        _ShadingShiftFactor ("mtoon.shadingShiftFactor", Range(-1, 1)) = -0.05
        _ShadingShiftTex ("mtoon.shadingShiftTexture", 2D) = "black" {} // channel R
        _ShadingShiftTexScale ("mtoon.shadingShiftTexture.scale", Float) = 1
        _ShadingToonyFactor ("mtoon.shadingToonyFactor", Range(0, 1)) = 0.95

        // GI
        _GiEqualization ("mtoon.giEqualizationFactor", Range(0, 1)) = 0.9

        // Emission
        [HDR] _EmissionColor ("emissiveFactor", Color) = (0, 0, 0, 1) // Unity specified name
        _EmissionMap ("emissiveTexture", 2D) = "white" {} // Unity specified name

        // Rim Lighting
        _MatcapColor ("mtoon.matcapFactor", Color) = (0, 0, 0, 1) // 仕様のデフォルト値は白だが、過去の仕様違反 UniVRM 実装アプリケーションのために黒とする。 https://github.com/vrm-c/UniVRM/pull/2594
        _MatcapTex ("mtoon.matcapTexture", 2D) = "black" {}
        _RimColor ("mtoon.parametricRimColorFactor", Color) = (0, 0, 0, 1)
        _RimFresnelPower ("mtoon.parametricRimFresnelPowerFactor", Range(0, 100)) = 5.0
        _RimLift ("mtoon.parametricRimLiftFactor", Range(0, 1)) = 0
        _RimTex ("mtoon.rimMultiplyTexture", 2D) = "white" {}
        _RimLightingMix ("mtoon.rimLightingMixFactor", Range(0, 1)) = 1

        // Outline
        _OutlineWidthMode ("mtoon.outlineWidthMode", Int) = 0
        [PowerSlider(2.2)] _OutlineWidth ("mtoon.outlineWidthFactor", Range(0, 0.05)) = 0
        _OutlineWidthTex ("mtoon.outlineWidthMultiplyTexture", 2D) = "white" {} // channel G
        _OutlineColor ("mtoon.outlineColorFactor", Color) = (0, 0, 0, 1)
        _OutlineLightingMix ("mtoon.outlineLightingMixFactor", Range(0, 1)) = 1

        // UV Animation
        _UvAnimMaskTex ("mtoon.uvAnimationMaskTexture", 2D) = "white" {} // channel B
        _UvAnimScrollXSpeed ("mtoon.uvAnimationScrollXSpeedFactor", Float) = 0
        _UvAnimScrollYSpeed ("mtoon.uvAnimationScrollYSpeedFactor", Float) = 0
        _UvAnimRotationSpeed ("mtoon.uvAnimationRotationSpeedFactor", Float) = 0

        // Unity ShaderPass Mode
        _M_CullMode ("_CullMode", Float) = 2.0
        _M_SrcBlend ("_SrcBlend", Float) = 1.0
        _M_DstBlend ("_DstBlend", Float) = 0.0
        _M_ZWrite ("_ZWrite", Float) = 1.0
        _M_AlphaToMask ("_AlphaToMask", Float) = 0.0

        // etc
        _M_DebugMode ("_DebugMode", Float) = 0.0

        // for Editor
        _M_EditMode ("_EditMode", Float) = 0.0
    }

    // Shader Model 3.0

SubShader{Tags{"RenderPipeline"="UniversalPipeline"}
        Pass
        {
            PackageRequirements
            {
                "unity": "2021.3"
                "com.unity.render-pipelines.universal": "12.0.0"
            }

            Name "SkinSignals288"
            Tags { "LightMode" = "UniversalForward" }

            Cull [_M_CullMode]
            Blend One Zero
            ZWrite On
            ZTest LEqual
            BlendOp Add
            AlphaToMask Off

            HLSLPROGRAM
            #pragma target 4.5
            #pragma multi_compile_local_fragment _ _T2_SPLIT_DIRECTIONAL154

            // Unity defined keywords
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _NORMALMAP
            #pragma multi_compile __ _MTOON_EMISSIVEMAP
            #pragma multi_compile __ _MTOON_RIMMAP
            #pragma multi_compile __ _MTOON_PARAMETERMAP

            // -------------------------------------
            // Universal Pipeline keywords
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _FORWARD_PLUS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile _ LIGHTMAP_SHADOW_MIXING
            #pragma multi_compile _ SHADOWS_SHADOWMASK
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION

            #pragma vertex Eye333Vertex
            #pragma fragment Eye333Fragment

            #define MTOON_URP

            #define E202_INDEPENDENT
#include "Assets/EUnityValidation01/EyeContoursLayers202/Shaders/ApertureAttributes162.hlsl"
#include "Assets/EUnityValidation01/SourceLight329/Shaders/Input329.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"


float4x4 _ProbeGPUVP91;float _RasterScale91;float4 _ROI348;
float4 _ClipShift333,_Profile333;float _Eye253Part,_Eye253Tag;
// Material-local source UV region and finite SourcePalette58 LUT.
Texture2D<float> _Region154;Texture2D<float4> _Palette154;
float4 _Size154,_Wrap154;int _Binding154,_Static154;
// SourcePalette58/SourceShade54: compare with the uploaded Float32 cuts.
// A rounded multiply-add can cross a cut one ULP early.
float4 _ShadeCuts154A,_ShadeCuts154B;
int Shade154(float g,int levels){
 int q=0;g=saturate(g);
 [unroll]for(int i=0;i<7;i++)if(i<levels-1){float t=i<4?_ShadeCuts154A[min(i,3)]:_ShadeCuts154B[max(i-4,0)];q+=g>=t?1:0;}
 return q;
}
int Wrap154(int x,int n,int mode){if(mode==1)return clamp(x,0,n-1);if(mode==2){int p=(x%(2*n)+2*n)%(2*n);return p<n?p:2*n-1-p;}return (x%n+n)%n;}
float3 Palette154(float2 uv,float g,out int region,out int q){
 int2 size=(int2)_Size154.xy;int2 p=(int2)floor(uv*size);
 p=int2(Wrap154(p.x,size.x,(int)_Wrap154.x),Wrap154(p.y,size.y,(int)_Wrap154.y));
 region=(int)round(_Region154.Load(int3(p,0))*255)-1;
 q=Shade154(g,(int)_Size154.z);
 if(region<0||region>=(int)_Size154.w)return float3(1,0,1); // explicit unbound diagnostic
 return _Palette154.Load(int3(q,region,0)).rgb;
}

int _PartGroup154,_RegionBase154,_StockRampReady154;
float4 _StockRamp154[8];
sampler2D _StockPartMember154;
Texture2D<float4> _UnderHair154;
int PartGroup154(float2 uv,int2 cell,float z){
 if(_PartGroup154==11){
  float2 underHair=_UnderHair154.Load(int3(cell,0)).xy;
  // An empty ray uses the base hair layer; overlaps require strict depth.
  if(underHair.y==0)return 1;
  clip(z<underHair.x?1:-1);
  return 10;
 }
 // Same source UV mask and cutoff as Auto245Fragment for material 7.
 return _PartGroup154==2 && tex2D(_StockPartMember154,uv).r>.5 ? 3 : _PartGroup154;
}
int _Full154;float4x4 _DepthGPU154,_View154;float4 _Shift154;
int _Proxy101,_Steps101;float4 _Palette101[16];
Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;o.e202Owner=v.e202SourceOwner.x;o.pos=mul(_ProbeGPUVP91,float4(o.positionWS,1));if(_Full154!=0){o.pos.xy+=_Shift154.xy*o.pos.w;o.pos.z=mul(_DepthGPU154,float4(o.positionWS,1)).z;}return o;}
#if defined(_T2_SPLIT_DIRECTIONAL154)
TEXTURE2D_SHADOW(_DirectionalWorld154);
TEXTURE2D_SHADOW(_DirectionalSelf154);
float4x4 _WorldToDirectional154,_SelfToDirectional154;
float _DirectionalMapSize154;
half SplitMainShadow154(float3 positionWS, half4 shadowMask,out float2 visibility){
 half4 parameters=GetMainLightShadowParams();
 ShadowSamplingData sampling=GetMainLightShadowSamplingData();
 // Keep the original filter footprint in texels after copying the projection
 // to a crop. The atlas origins differ, but the directional pitch is shared.
 const float invSize=rcp(_DirectionalMapSize154);
 sampling.shadowmapSize=float4(invSize,invSize,_DirectionalMapSize154,_DirectionalMapSize154);
 sampling.shadowOffset0=half4(-.5,-.5,.5,-.5)*invSize;
 sampling.shadowOffset1=half4(-.5,.5,.5,.5)*invSize;
 half4 unweighted=parameters;unweighted.x=1;
 float4 w=mul(_WorldToDirectional154,float4(positionWS,1));
 float4 s=mul(_SelfToDirectional154,float4(positionWS,1));
 visibility.x=SampleShadowmap(TEXTURE2D_ARGS(_DirectionalWorld154,sampler_LinearClampCompare),w,sampling,unweighted,false);
 visibility.y=SampleShadowmap(TEXTURE2D_ARGS(_DirectionalSelf154,sampler_LinearClampCompare),s,sampling,unweighted,false);
 // Independent PCF footprints can overlap only partially. The darker
 // visibility governs; do not multiply already filtered penumbras.
 half realtimeShadow=LerpWhiteTo(min(visibility.x,visibility.y),parameters.x);
 #ifdef CALCULATE_BAKED_SHADOWS
  half baked=BakedShadow(shadowMask,_MainLightOcclusionProbes,parameters);
 #else
  half baked=1;
 #endif
 return MixRealtimeAndBakedShadows(realtimeShadow,baked,GetMainLightShadowFade(positionWS));
}
float SplitSurfaceLight154(const Varyings input,const MToonInput material,
 out float4 shadowTerms,out float4 lightingTerms){
 float3 normalWS=normalize(material.normalWS);
 float ambient=Luminance335(SampleSH(normalWS));
 float lit=ambient,available=ambient;
 float4 shadowCoord=TransformWorldToShadowCoord(input.positionWS);
 #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
 shadowCoord=ComputeScreenPos(TransformWorldToHClip(input.positionWS));
 #endif
 half4 shadowMask=SAMPLE_SHADOWMASK(input.lightmapUV);
 Light mainLight=GetMainLight(shadowCoord,input.positionWS,shadowMask);
 float originalShadow=mainLight.shadowAttenuation;
 mainLight.shadowAttenuation=SplitMainShadow154(input.positionWS,shadowMask,shadowTerms.xy);
 shadowTerms.z=mainLight.shadowAttenuation;shadowTerms.w=originalShadow;
 float mainUnshadowed=Luminance335(mainLight.color)*max(mainLight.distanceAttenuation,0)
   *saturate(dot(normalWS,mainLight.direction)*.5+.5);
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
 float originalLit=lit+mainUnshadowed*(originalShadow-mainLight.shadowAttenuation);
 lightingTerms=float4(available>1e-6?saturate(originalLit/available):0,mainUnshadowed,ambient,available);
 return available>1e-6?saturate(lit/available):0;
}
#endif
struct O333{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 uv:SV_Target2;float4 light:SV_Target3;
#if defined(_T2_SPLIT_DIRECTIONAL154)
 float4 shadowTerms:SV_Target4;float4 lightingTerms:SV_Target5;float4 worldPosition:SV_Target6;
#endif
};
O333 Eye333Fragment(const Varyings input,uint primitiveID:SV_PrimitiveID,bool facing:SV_IsFrontFace){
 Varyings v=input;v.pos.xy=_ROI348.xy+input.pos.xy/_RasterScale91;
 float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;
 half alpha=GetMToonGeometry_Alpha(src);if(alpha<=1e-6)discard;
 MToonInput material;material.uv=uv;material.normalWS=GetMToonGeometry_Normal(v,facing?1:-1,uv);material.viewDirWS=normalize(v.viewDirWS);material.litColor=src.rgb;material.alpha=alpha;
 float z154=_Full154!=0?-mul(_View154,float4(v.positionWS,1)).z:-TransformWorldToView(v.positionWS).z;
 int group154=_Full154!=0?PartGroup154(uv,(int2)input.pos.xy,z154):_Proxy101;
 float g;
#if defined(_T2_SPLIT_DIRECTIONAL154)
 float4 shadowTerms,lightingTerms;
 g=SplitSurfaceLight154(v,material,shadowTerms,lightingTerms);
#else
 g=ContinuousSurfaceLight335(v,material);
#endif
 int k,region=-1;
 bool authoredStock=_Full154!=0&&group154==3&&_StockRampReady154!=0;
 int eye=clamp((int)round(v.e202Owner),1,2);float3 c=src.rgb;
 // Native face is an UNLIT source diagnostic in this first stage, not a
 // completed source-region resolver. Only socket skin has an explicit palette.
 if(authoredStock){k=Shade154(g,_Steps101);c=_StockRamp154[k].rgb;}
 else if(_Static154!=0&&_Proxy101==0)c=Palette154(uv,g,region,k);
 else{k=Shade154(g,_Steps101);if(_Proxy101!=0)c=_Palette101[(eye-1)*8+k].rgb;}
 O333 o;o.rgba=float4(c,_Full154!=0?alpha:1);o.meta=float4(z154,_Full154!=0?_Binding154+1:_Proxy101,eye,alpha);o.uv=float4(uv,primitiveID+1,round(_Auto245Role));int canvasRegion=authoredStock?71:(region>=0&&region<(int)_Size154.w?_RegionBase154+region+1:0);
 o.light=float4(g,k,_Full154!=0?canvasRegion:_Steps101,group154);
#if defined(_T2_SPLIT_DIRECTIONAL154)
 o.shadowTerms=shadowTerms;o.lightingTerms=lightingTerms;o.worldPosition=float4(v.positionWS,1);
#endif
 return o;
}

ENDHLSL
        }
}
}
