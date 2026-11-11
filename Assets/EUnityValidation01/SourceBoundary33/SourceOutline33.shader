Shader "EValidation/SourceBoundary33"{
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

SubShader{Tags{"RenderPipeline"="UniversalPipeline"}

        Pass{Name "SourceDepth29" Cull [_M_CullMode] ZWrite [_M_ZWrite] ZTest LEqual Blend One Zero ColorMask 0
        HLSLPROGRAM
        #pragma fragment Depth29

            #pragma target 4.5
            #pragma vertex Vertex29
            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _MTOON_PARAMETERMAP
            #define MTOON_URP
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_uv.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_alpha.hlsl"
            float4x4 _ProbeGPUVP29,_ProbeView29;float4 _SourceOutline29;
            Varyings Vertex29(Attributes v){Varyings o=MToonVertex(v);o.pos=mul(_ProbeGPUVP29,float4(o.positionWS,1));return o;}
            float Alpha29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half a=GetMToonGeometry_Alpha(src);if(a<=1e-6)discard;return a;}
float4 Depth29(Varyings v):SV_Target{Alpha29(v);return 0;}
        ENDHLSL
        }

        Pass{Name "SourceOutline29" Cull Front ZWrite On ZTest LEqual Offset 1,1 Blend One Zero
        HLSLPROGRAM
        #pragma fragment Outline29
        #define MTOON_PASS_OUTLINE
        #define _MTOON_OUTLINE_WORLD

            #pragma target 4.5
            #pragma vertex Vertex29
            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _MTOON_PARAMETERMAP
            #define MTOON_URP
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_uv.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_alpha.hlsl"
            float4x4 _ProbeGPUVP29,_ProbeView29;float4 _SourceOutline29;
            Varyings Vertex29(Attributes v){Varyings o=MToonVertex(v);o.pos=mul(_ProbeGPUVP29,float4(o.positionWS,1));return o;}
            float Alpha29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half a=GetMToonGeometry_Alpha(src);if(a<=1e-6)discard;return a;}
struct Out29{float4 colour:SV_Target0;float4 meta:SV_Target1;};
        Out29 Outline29(Varyings v){float a=Alpha29(v);Out29 o;o.colour=float4(_SourceOutline29.rgb,a);o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,v.uv,1);return o;}
        ENDHLSL
        }
Pass{Name "SourcePigment29" Cull [_M_CullMode] ZWrite Off ZTest LEqual Blend One Zero
HLSLPROGRAM
#pragma fragment Pigment29
            #pragma target 4.5
            #pragma vertex Vertex29
            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _MTOON_PARAMETERMAP
            #define MTOON_URP
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_vertex.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_uv.hlsl"
            #include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_geometry_alpha.hlsl"
            float4x4 _ProbeGPUVP29,_ProbeView29;float4 _SourceOutline29;
            Varyings Vertex29(Attributes v){Varyings o=MToonVertex(v);o.pos=mul(_ProbeGPUVP29,float4(o.positionWS,1));return o;}
            float Alpha29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;half a=GetMToonGeometry_Alpha(src);if(a<=1e-6)discard;return a;}
struct OutPigment29{float4 colour:SV_Target0;float4 meta:SV_Target1;};
OutPigment29 Pigment29(Varyings v){float2 uv=GetMToonGeometry_Uv(v.uv);half4 src=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;float materialAlpha=Alpha29(v);if(src.a<=1e-6)discard;OutPigment29 o;o.colour=src;o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,uv,materialAlpha);return o;}
ENDHLSL
}
}
}
