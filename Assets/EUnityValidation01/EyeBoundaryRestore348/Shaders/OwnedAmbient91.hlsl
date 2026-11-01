#ifndef OWNED_AMBIENT91_INCLUDED
#define OWNED_AMBIENT91_INCLUDED
// Packing comes from Unity's CopySHCoefficientArraysFrom at this exact draw.
// This is material-owned input delivery, not an arbitrary ambient/colour gain.
float _BindSH91;
float4 _SHAr91,_SHAg91,_SHAb91,_SHBr91,_SHBg91,_SHBb91,_SHC91;
half3 OriginalBuiltinSH91(half3 normalWS){return SampleSH(normalWS);}
half3 BoundSH91(half3 normalWS){
 if(_BindSH91<.5)return OriginalBuiltinSH91(normalWS);
 return max(0,SHEvalLinearL0L1(normalWS,_SHAr91,_SHAg91,_SHAb91)+SHEvalLinearL2(normalWS,_SHBr91,_SHBg91,_SHBb91,_SHC91));
}
// URP was included by forward_vertex above. Change only calls made by the owned
// downstream MToon/FaceSceneLight functions, never the shared package source.
#define SampleSH(normalWS) BoundSH91(normalWS)
#define MToon_SampleSH(normalWS) BoundSH91(normalWS)
#endif
