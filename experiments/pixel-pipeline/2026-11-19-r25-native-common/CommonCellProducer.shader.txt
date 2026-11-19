Shader "__T3IntegratedAperture154/CommonCellProducer"
{
    Properties
    {
        [HideInInspector] _RegionBase154("Palette region base",Int)=0
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


float4 _ClipShift333,_Profile333;float _Eye253Part,_Eye253Tag;float4 _ROI348;float4x4 _WorldToHead348;int _SupportKind348;
Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;o.e202Owner=v.e202SourceOwner.x;o.restHead348=v.texcoord1;return o;}

 Texture2D<float> _Region154;
 float4 _Size154,_Wrap154;
 int _RegionBase154,_Binding154;
 int WrapInput154(int p,int n,int mode){
  if(mode==1)return clamp(p,0,n-1);
  if(mode==2){int t=(p%(2*n)+2*n)%(2*n);return t<n?t:2*n-1-t;}
  return (p%n+n)%n;
 }
 float4 SourceInput154(Varyings v,float2 uv,float4 src,float facing){
  int2 size=(int2)_Size154.xy;
  int2 p=(int2)floor(uv*size);
  p=int2(WrapInput154(p.x,size.x,(int)_Wrap154.x),WrapInput154(p.y,size.y,(int)_Wrap154.y));
  int family=(int)round(_Region154.Load(int3(p,0))*255);
  bool valid=family>0&&family<=(int)_Size154.w;
  MToonInput m;m.uv=uv;m.normalWS=GetMToonGeometry_Normal(v,facing,uv);
  m.viewDirWS=normalize(v.viewDirWS);m.litColor=src.rgb;m.alpha=GetMToonGeometry_Alpha(src);
  float g=ContinuousSurfaceLight335(v,m);
  return float4(g,valid?_RegionBase154+family:0,_Size154.z,_Binding154+1);
 }

struct O333{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 restPosition:SV_Target2;float4 uv:SV_Target3;float4 shade:SV_Target4;};
O333 Eye333Fragment(const Varyings input,uint primitiveID:SV_PrimitiveID,bool facing:SV_IsFrontFace){Varyings v=input;v.pos.xy=_ROI348.xy+input.pos.xy/4;FragmentInput f;f.varyings=v;f.facing=facing?1:-1;
 float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half alpha=GetMToonGeometry_Alpha(src);if(alpha<=1e-6)discard;int role=(int)round(_Auto245Role);
 O333 o;
 o.rgba=float4(src.rgb,alpha);
 o.shade=SourceInput154(v,uv,src,f.facing);
 o.meta=float4(-TransformWorldToView(v.positionWS).z,role+1,round(v.e202Owner),alpha);o.restPosition=float4(v.restHead348,facing?1:-1);o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;}
ENDHLSL
        }
}
}
