Shader "EValidation/CurrentNonEye98"
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
#include "Assets/EUnityValidation01/EyeContoursLayers202/Shaders/ApertureAttributes162.hlsl"
#include "Assets/EUnityValidation01/SourceLight329/Shaders/Input329.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Assets/EUnityValidation01/SkinPalette302/Shaders/BodyPalette302.hlsl"


float4x4 _ProbeGPUVP91;float _RasterScale91;float4 _ROI348;
float4 _ClipShift333,_Profile333;float _Eye253Part,_Eye253Tag;
Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;o.e202Owner=v.e202SourceOwner.x;o.pos=mul(_ProbeGPUVP91,float4(o.positionWS,1));return o;}
struct O333{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 uv:SV_Target2;float4 source:SV_Target3;};
O333 Eye333Fragment(const Varyings input,uint primitiveID:SV_PrimitiveID,bool facing:SV_IsFrontFace){Varyings v=input;v.pos.xy=_ROI348.xy+input.pos.xy/_RasterScale91;FragmentInput f;f.varyings=v;f.facing=facing?1:-1;if(_Eye253Part==5&&max(v.e202Control.x,v.e202Control.y)<=1e-5)discard;
float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half alpha=GetMToonGeometry_Alpha(src);if(alpha<=1e-6)discard;
int role=(int)round(_Auto245Role);float4 c=Auto245NativeOriginalFragment(f);if(_SurfaceLayers335>.5&&role>=11&&role<=14)c=MToonFragment(f);if(role>=7&&role<=10){MToonInput m;m.uv=uv;m.normalWS=GetMToonGeometry_Normal(v,f.facing,uv);m.viewDirWS=normalize(v.viewDirWS);m.litColor=src.rgb;m.alpha=alpha;UnityLighting light=GetUnityLighting(v,m.normalWS);float lit=step(_Profile333.y,GetMToonLighting_DotNL(light,m))*step(_Profile333.z,light.directLightAttenuation.x);c=float4(src.rgb*((_Profile333.w>.5&&lit<.5)?_Profile333.x:1),alpha);}
O333 o;o.rgba=c;o.meta=float4(-TransformWorldToView(v.positionWS).z,role+1,role<=6?round(v.e202Owner):0,alpha);o.uv=float4(uv,primitiveID+1,_Source329Renderer);o.source=float4(role,primitiveID+1,_Source329Renderer,alpha);return o;}
ENDHLSL
        }
}
}
