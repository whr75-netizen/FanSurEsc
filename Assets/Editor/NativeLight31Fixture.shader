Shader "Hidden/FantasySurvival/NativeLight31Fixture"
{
    SubShader
    {
        Pass
        {
            ZTest Always ZWrite Off Cull Off
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "Assets/Rendering/LocalLighting/MaterialLightResponse27.hlsl"
            #include "Assets/Shaders/World/NativeLight31.hlsl"
            float4 _Albedo, _ShadowedIrradiance, _ShadowLoss, _SteppedIrradiance;
            float _Legacy;
            float4 vert(float4 p : POSITION) : SV_POSITION { return UnityObjectToClipPos(p); }
            float4 frag() : SV_Target
            {
                float3 color = _Legacy > 0.5 ?
                    Material27Readable(_Albedo.rgb, _ShadowedIrradiance.rgb, _SteppedIrradiance.rgb) :
                    Native31Readable(_Albedo.rgb, _ShadowedIrradiance.rgb, _ShadowLoss.rgb, _SteppedIrradiance.rgb);
                return float4(color, 1);
            }
            ENDHLSL
        }
    }
}
