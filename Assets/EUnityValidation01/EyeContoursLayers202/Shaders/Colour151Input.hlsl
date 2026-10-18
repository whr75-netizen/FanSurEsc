#include "./ApertureAttributes162.hlsl"
#ifndef VRMC_MATERIALS_MTOON_INPUT_INCLUDED
#define VRMC_MATERIALS_MTOON_INPUT_INCLUDED

#include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_render_pipeline.hlsl"

// Textures
MTOON_DECLARE_TEX2D(_E189GarmentField);
MTOON_DECLARE_TEX2D(_E170OwnedMask);
MTOON_DECLARE_TEX2D(_MainTex);
MTOON_DECLARE_TEX2D(_ShadeTex);
MTOON_DECLARE_TEX2D(_BumpMap);
MTOON_DECLARE_TEX2D(_ShadingShiftTex);
MTOON_DECLARE_TEX2D(_EmissionMap);
MTOON_DECLARE_TEX2D(_MatcapTex);
MTOON_DECLARE_TEX2D(_RimTex);
MTOON_DECLARE_TEX2D(_OutlineWidthTex);
// NOTE: "tex2d() * _Time.y" returns mediump value if sampler is half precision in Android VR platform
MTOON_DECLARE_TEX2D_FLOAT(_UvAnimMaskTex);

CBUFFER_START(UnityPerMaterial)
float _E170OwnedEnabled;
// Vector
float4 _MainTex_ST;
// Colors
half4 _Color;
half4 _ShadeColor;
half4 _EmissionColor;
half4 _MatcapColor;
half4 _RimColor;
half4 _OutlineColor;
// Floats
half _Cutoff;
half _BumpScale;
half _ShadingShiftFactor;
half _ShadingShiftTexScale;
half _ShadingToonyFactor;
half _GiEqualization;
half _RimFresnelPower;
half _RimLift;
half _RimLightingMix;
half _OutlineWidth;
half _OutlineLightingMix;
float _UvAnimScrollXSpeed;
float _UvAnimScrollYSpeed;
float _UvAnimRotationSpeed;
float _E151Role;
float _E151Style;
float _E152PaintPolicy;
float _E152BandPolicy;
float _E152GlossPolicy;
float _E153Enable;
float4 _E153ProxyCenter;
float4 _E153ProxyInvSq;
float _E154AnchorActive;
float4x4 _E154WorldToProxy;
float4x4 _E154ProxyNormalToWorld;
float _E158Enabled;
float4 _E158Scales;
float4 _E158HeadAnchor0;
float4 _E158HeadAnchor1;
float4 _E158EyeAnchor0;
float4 _E158EyeAnchor1;
float _E162ApertureEnabled;
float4 _E162ApertureScale;
float4 _E162Centre0;
float4 _E162Centre1;
float4x4 _E162WorldToHead;
float4x4 _E162HeadToWorld;
float _E164SemanticEnabled;
float4 _E164HairBase;
float4 _E164HairShadow;
float4 _E164HairHighlight;
CBUFFER_END

// No Using on shader
// half _AlphaMode;
// half _TransparentWithZWrite;
// half _RenderQueueOffset;
// half _DoubleSided;
// half _OutlineWidthMode;

#endif
