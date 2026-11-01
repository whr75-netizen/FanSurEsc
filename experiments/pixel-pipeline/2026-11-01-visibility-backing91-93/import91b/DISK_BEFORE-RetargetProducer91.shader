Shader "EValidation/RetargetProducer91"
{
    Properties
    {
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
#include "Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/Attributes348.hlsl"
#include "Assets/EUnityValidation01/SourceLight329/Shaders/Input329.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"


#include "Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ProbeLight91.hlsl"
float4 _ClipShift333,_Profile333;float _Eye253Part,_Eye253Tag;float4 _ROI348;float4x4 _WorldToHead348;int _SupportKind348;

float4 _NativeSourceX89,_NativeSourceY89,_CanonicalAnchor89;
float4 _SourcePhysicalROI89,_SourcePhysicalSize89,_PhysicalCamera89,_PhysicalForward89;
float4x4 _AuthoredToHead89,_CanonicalGPUProjection89,_PhysicalView89,_PhysicalCropGPUVP89;
int _Control89,_UseBank89,_SelectedOwner89;
float _ScreenSign89;
Texture2D<float4> _FeatureBankRGB89,_FeatureBankRole89;
float4 SourceClip89(float3 world){
 if(_Control89!=0)return mul(_PhysicalCropGPUVP89,float4(world,1));
 float4 rest=mul(_WorldToHead348,float4(world,1));
 float2 q=float2(dot(_NativeSourceX89,rest),dot(_NativeSourceY89,rest));
 float3 projected=mul(_AuthoredToHead89,float4(q,1,0)).xyz;
 float2 local=projected.xy/projected.z-_CanonicalAnchor89.xy;
 float depth=-mul(_PhysicalView89,float4(world,1)).z;
 return mul(_CanonicalGPUProjection89,float4(local.x,-local.y,-depth,1));
}
float2 SourceLogicalScreen89(float3 world){
 float4 p=mul(_PhysicalCropGPUVP89,float4(world,1));
 float2 sv=float2(p.x/p.w*.5+.5,.5+_ScreenSign89*p.y/p.w*.5)*_SourcePhysicalSize89.xy;
 return _SourcePhysicalROI89.xy+sv/4;
}
Varyings Eye333Vertex(const Attributes v){
 Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;
 o.e202Owner=v.e202SourceOwner.x;o.restHead348=v.texcoord1;
 o.viewDirWS=_PhysicalCamera89.w>.5?-_PhysicalForward89.xyz:_PhysicalCamera89.xyz-o.positionWS;
 o.pos=SourceClip89(o.positionWS);return o;
}
struct O333{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 restPosition:SV_Target2;float4 uv:SV_Target3;float4 shade:SV_Target4;float4 normal91:SV_Target5;float4 sh91:SV_Target6;float4 sum91:SV_Target7;};
O333 Eye333Fragment(const Varyings input,uint primitiveID:SV_PrimitiveID,bool facing:SV_IsFrontFace){Varyings v=input;v.pos.xy=_Control89==3?_SourcePhysicalROI89.xy+input.pos.xy/4:SourceLogicalScreen89(v.positionWS);if(_SelectedOwner89>0&&round(v.e202Owner)!=_SelectedOwner89)discard;FragmentInput f;f.varyings=v;f.facing=facing?1:-1;
 float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half alpha=GetMToonGeometry_Alpha(src);int role=(int)round(_Auto245Role);bool bank=_UseBank89>0&&(role==1||role==4);if(!bank&&alpha<=1e-6)discard;
 O333 o;o.shade=0;o.normal91=0;o.sh91=0;o.sum91=0;
 if(bank){
  float4 rest=float4(v.restHead348,1);float2 q=float2(dot(_NativeSourceX89,rest),dot(_NativeSourceY89,rest));
  int2 k=(int2)floor(q);if(any(k<0)||any(k>=int2(480,272)))discard;
  float4 sourceRole=_FeatureBankRole89.Load(int3(k.x,271-k.y,0));
  if(round(sourceRole.x)!=role||round(sourceRole.y)!=round(v.e202Owner))discard;
  float4 colour=_FeatureBankRGB89.Load(int3(k.x,271-k.y,0));if(colour.a<=0)discard;
  o.rgba=colour;o.meta=float4(-mul(_PhysicalView89,float4(v.positionWS,1)).z,role+1,round(v.e202Owner),colour.a);
  o.restPosition=float4(v.restHead348,facing?1:-1);o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;
 }

 // Only the eyeline pigment supplier changes. Other surface RGB remains its existing MToon output.
 if(_SupportKind348==3){MToonInput material;material.uv=uv;material.normalWS=GetMToonGeometry_Normal(v,f.facing,uv);material.viewDirWS=normalize(v.viewDirWS);material.litColor=src.rgb;material.alpha=alpha;float continuous=ProbeLight91(v,material,f.facing,o.normal91,o.sh91,o.sum91);float level=QuantizedSurfaceLight335(continuous,6);float factor=_ShadeLayer335>.5?lerp(_SurfaceOwnShade335,1,level):1;o.rgba=float4(src.rgb,alpha);o.shade=float4(continuous,level,factor,alpha);}
 else{o.rgba=float4(Auto245NativeOriginalFragment(f).rgb,alpha);}
 o.meta=float4(-mul(_PhysicalView89,float4(v.positionWS,1)).z,role+1,round(v.e202Owner),alpha);o.restPosition=float4(v.restHead348,facing?1:-1);o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;}
ENDHLSL
        }
}
}
