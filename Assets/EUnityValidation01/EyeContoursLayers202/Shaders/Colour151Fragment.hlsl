#define MToonFragment E152OriginalMToonFragment
#include "Packages/com.vrmc.vrm/MToon10/Shaders/vrmc_materials_mtoon_forward_fragment.hlsl"
#undef MToonFragment
#include "./Colour151Ramps.hlsl"
float _E189Diag;
float4 _E190FixedTestUV;
float _E189FieldEnabled;
#include "./GarmentAuthoredLumaClass24.hlsl"
float _E152Diagnostic;
float _E155ProtectedCapture;
float _E158CaptureMode;
float _E170CaptureMode;
float _E158HideFace;
float _E160HideIrisGlint;
float _E158HideLine;
bool E151Protected(uint role){return role==0u||role==1u||role==2u||role==4u||role==5u||role==6u;}
float _E202MainHideEyes;
float4 MToonFragment(const FragmentInput f):SV_Target {
    uint earlyRole=(uint)round(_E151Role);
#if !defined(E202_INDEPENDENT)
if(_E202MainHideEyes>.5&&(earlyRole==1u||earlyRole==2u||earlyRole==4u||earlyRole==6u))clip(-1);
#endif
    if((_E158HideFace>.5&&earlyRole==3u)||(_E158HideLine>.5&&earlyRole==6u)||(_E160HideIrisGlint>.5&&(earlyRole==1u||earlyRole==2u)))clip(-1);
    half4 col=E152OriginalMToonFragment(f);
    uint role=(uint)round(_E151Role);
    float2 uv=GetMToonGeometry_Uv(f.varyings.uv);
    float4 source=MTOON_SAMPLE_TEXTURE2D(_MainTex,uv)*_Color;
    float alpha=GetMToonGeometry_Alpha(source);
    float3 n=normalize(MTOON_IS_FRONT_VFACE(f.facing,f.varyings.normalWS,-f.varyings.normalWS));
    float3 light=normalize(GetMainLight().direction);
    float ndotl=dot(n,light);
    float shadow=role==8u?.88:role==9u?.85:role==10u?.9:role>=11u?.82:1;
    float threshold=role>=11u?.1:.15;
    float legacyBand=ndotl<threshold?shadow:1;
    float y=dot(source.rgb,float3(.2126,.7152,.0722));
    float target=y>=.025?E151Ramp(role,y):y;
    float originalTarget=target;
    float4 authoredField=MTOON_SAMPLE_TEXTURE2D(_E189GarmentField,uv);
    target=B24AuthoredGarmentTarget(role,y,target,authoredField.r,_E189FieldEnabled>.5&&_E151Style>=2&&_E152PaintPolicy>.5&&!MToon_IsOutlinePass());
    float peak=max(max(source.r,source.g),source.b);
    float legacyScale=y>=.025?min(target/y,1/max(peak,1e-8)):1;
    float3 h=normalize(light+normalize(f.varyings.viewDirWS));
    bool legacyGloss=role>=11u && ndotl>.55 && dot(n,h)>.975;
    if(_E151Style>0 && !MToon_IsOutlinePass()) {
        if(E151Protected(role))col=float4(source.rgb,alpha);
        else {
            float3 rgb=source.rgb;
            if(_E151Style>=2 && _E152PaintPolicy>.5)rgb*=legacyScale;
            rgb*=(_E152BandPolicy>.5?legacyBand:1);
            if(_E151Style>=2 && _E152GlossPolicy>.5 && legacyGloss)rgb+=min(float3(.025,.025,.025),1-rgb);
            col=float4(rgb,alpha);
        }
    }
    if(_E152Diagnostic==1)return float4(source.rgb,alpha);
    else if(_E152Diagnostic==2)return float4(y,y*legacyScale,legacyBand,alpha);
    else if(_E152Diagnostic==3)return float4(role,legacyGloss?1:0,ndotl*.5+.5,alpha);
    else if(_E152Diagnostic==4)return float4(target,legacyScale,legacyScale<target/max(y,1e-8)?1:0,alpha);
    if(_E155ProtectedCapture>.5)col.rgb=(role==5u||role>=11u)?1:0;
    float4 e158Result=col;
    if(_E164SemanticEnabled>.5 && role>=11u && _E155ProtectedCapture<.5 && !MToon_IsOutlinePass()){
        bool shade=f.varyings.semanticMask.x>=.5;
        bool highlight=f.varyings.semanticMask.y>=.5 && !shade;
        e158Result.rgb=shade?_E164HairShadow.rgb:highlight?_E164HairHighlight.rgb:_E164HairBase.rgb;
    }
    if(_E170OwnedEnabled>.5 && role>=11u && _E155ProtectedCapture<.5 && !MToon_IsOutlinePass()){
        float4 mask=MTOON_SAMPLE_TEXTURE2D(_E170OwnedMask,f.varyings.ownedUV);
        bool high=mask.g>=.5;bool shade=mask.r>=.5&&!high;
        e158Result.rgb=high?_E164HairHighlight.rgb:shade?_E164HairShadow.rgb:_E164HairBase.rgb;
    }
    if(_E170CaptureMode>.5){
        bool hair=role>=11u&&!MToon_IsOutlinePass();
        float4 mask=MTOON_SAMPLE_TEXTURE2D(_E170OwnedMask,f.varyings.ownedUV);
        bool high=_E170OwnedEnabled>.5?mask.g>=.5:(f.varyings.semanticMask.y>=.5&&f.varyings.semanticMask.x<.5);
        bool shade=_E170OwnedEnabled>.5?(mask.r>=.5&&!high):f.varyings.semanticMask.x>=.5;
        e158Result.rgb=hair?(_E170CaptureMode<1.5?float3(shade?1:0,high?1:0,1):float3(f.varyings.ownedUV,1)):0;
    }
    if(_E158CaptureMode>.5){
        bool eyeRole=_E158CaptureMode<1.5?(role==1u||role==2u||role==4u||role==6u):_E158CaptureMode<2.5?(role==4u):_E158CaptureMode<3.5?(role==1u||role==2u):(role==6u);
        float3 a0=(role==1u||role==2u)?_E158EyeAnchor0.xyz:_E158HeadAnchor0.xyz;
        float3 a1=(role==1u||role==2u)?_E158EyeAnchor1.xyz:_E158HeadAnchor1.xyz;
        bool right=dot(f.varyings.positionWS-a0,f.varyings.positionWS-a0)<dot(f.varyings.positionWS-a1,f.varyings.positionWS-a1);
        e158Result.rgb=eyeRole?float3(right?1:0,right?0:1,role==1u?1:0):0;
    }

    bool ownedHair=role>=11u&&(_E170OwnedEnabled>.5||_E164SemanticEnabled>.5)&&!MToon_IsOutlinePass();
    bool bypass=E151Protected(role)||ownedHair||MToon_IsOutlinePass();
    float3 flatBase=source.rgb;
    if(_E151Style>=2&&!E151Protected(role)&&_E152PaintPolicy>.5)flatBase*=legacyScale;
    if(ownedHair)flatBase=e158Result.rgb;else flatBase=(half3)flatBase;
    if(MToon_IsOutlinePass())flatBase=col.rgb;
    float bandOn=(!bypass&&_E152BandPolicy>.5)?1:0;
    float glossOn=(!bypass&&_E151Style>=2&&_E152GlossPolicy>.5&&role>=11u)?1:0;
    if(_E189Diag>0&&_E189Diag!=4&&alpha<=1e-6)clip(-1);
    if(_E189Diag==11){
        float3 hard=normalize(cross(ddx(f.varyings.positionWS),ddy(f.varyings.positionWS)));
        float3 hn=TransformWorldToViewDir(hard);
        float pixel=2.0*unity_OrthoParams.y/517.0;
        return float4(-TransformWorldToView(f.varyings.positionWS).z,role+1,
            abs(hn.x)/max(abs(hn.z),.1)*pixel,abs(hn.y)/max(abs(hn.z),.1)*pixel);
    }
    if(_E189Diag==17)return MTOON_SAMPLE_TEXTURE2D(_MainTex,_E190FixedTestUV.xy)*_Color;
    if(_E189Diag==16)return float4(MTOON_SAMPLE_TEXTURE2D(_E189GarmentField,_E190FixedTestUV.xy).r,role,1,1);
    if(_E189Diag==13)return float4(y,originalTarget,target,1);
    if(_E189Diag==14)return float4(uv,authoredField.r,1);
    if(_E189Diag==15)return float4(source.rgb,alpha);
    if(_E189Diag==12)return float4(ndotl,legacyBand,role,1);
    if(_E189Diag==1)return float4(uv,0,1);
    if(_E189Diag==2)return float4(f.varyings.positionWS,1);
    if(_E189Diag==3)return float4(n,1);
    if(_E189Diag==4)return float4(flatBase,(half)alpha);
    if(_E189Diag==5)return float4(role,bandOn,glossOn,1);
    if(_E189Diag==6)return float4(-TransformWorldToView(f.varyings.positionWS).z,1,role,1);
    float4 hm=MTOON_SAMPLE_TEXTURE2D(_E170OwnedMask,f.varyings.ownedUV);
    bool high=hm.g>=.5;bool shade=hm.r>=.5&&!high;
    if(_E189Diag==7)return float4(role>=11u?1:0,role>=11u&&shade?1:0,role>=11u&&high?1:0,1);
    if(_E189Diag==8)return float4(role+1,role,role>=11u?(high?2:shade?1:0):-1,1);
    if(_E189Diag==9)return float4(alpha,1,role,1);
    if(_E189Diag==10)return float4(f.varyings.ownedUV,0,1);
    return e158Result;
}

