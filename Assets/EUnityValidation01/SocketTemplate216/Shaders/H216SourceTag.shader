Shader "EValidation/H216SourceTagOnly"
{
    Properties
    {
        _E189GarmentField("B24 authored UV0 class data",2D)="black"{}
        _E170OwnedEnabled("B17 owned UV1 colour",Float)=0
        _E170OwnedMask("B17 linear Point Clamp mask",2D)="black"{}
        _E164SemanticEnabled("Fixed source13 hair fields",Float)=0
        _E164HairBase("Source13 base linear",Vector)=(0,0,0,1)
        _E164HairShadow("Source13 shade linear",Vector)=(0,0,0,1)
        _E164HairHighlight("Source13 highlight linear",Vector)=(0,0,0,1)
        _E162ApertureEnabled("Source physical aperture warp",Float)=0
        _E162ApertureScale("Physical aperture X/Y",Vector)=(1.2,1.15,0,0)
        _E158Enabled("Native provider scaling",Float)=0
        _E158Scales("R iris/L iris/white/lid",Vector)=(1.44,1.4575,1.275,1.275)
        _E151Role("Original material ID",Float)=0
        _E151Style("Colour candidate stage",Float)=0
        _E152PaintPolicy("Paint value quantization",Float)=1
        _E152BandPolicy("World-normal band",Float)=1
        _E152GlossPolicy("Procedural hair gloss",Float)=1
        _E153Enable("Hair proxy normal input",Float)=0
        _E154AnchorActive("Head frame active",Float)=0
        _E153ProxyCenter("Proxy center/shoulder",Vector)=(0,0,0,0)
        _E153ProxyInvSq("Proxy inverse radii squared",Vector)=(1,1,1,0)
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
    SubShader { Tags { "RenderPipeline"="UniversalPipeline" } Pass {
            Name "IndependentEye202" Tags { "LightMode"="Eye202Independent" }
            Cull [_M_CullMode] ZWrite On ZTest LEqual Blend One Zero
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex MToonVertex
            #pragma fragment H216TaggedFragment
            #pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
            #pragma multi_compile __ _NORMALMAP
            #pragma multi_compile __ _MTOON_EMISSIVEMAP
            #pragma multi_compile __ _MTOON_RIMMAP
            #pragma multi_compile __ _MTOON_PARAMETERMAP
            #define MTOON_URP
            #define E202_INDEPENDENT
            #include "../../EyeContoursLayers202/Shaders/Colour151Input.hlsl"
            #include "../../EyeContoursLayers202/Shaders/Hair153Vertex.hlsl"
            #include "../../EyeContoursLayers202/Shaders/Colour151Fragment.hlsl"
            #include "../../EyeContoursLayers202/Shaders/Eye202Fragment.hlsl"
float _H216SourceTag;
Eye202Output H216TaggedFragment(const FragmentInput f){Eye202Output o=Eye202Fragment(f);o.uvControl.w=_H216SourceTag;return o;}
            ENDHLSL
        } } }