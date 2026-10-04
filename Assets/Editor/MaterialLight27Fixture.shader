Shader "Hidden/FantasySurvival/MaterialLight27Fixture"
{
    SubShader
    {
        Pass
        {
            ZTest Always ZWrite Off Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "Assets/Rendering/LocalLighting/MaterialLightResponse27.hlsl"
            float4 _Albedo, _BaseIrradiance, _SteppedIrradiance;
            float4 vert(float4 p : POSITION) : SV_POSITION { return UnityObjectToClipPos(p); }
            float4 frag() : SV_Target
            {
                return float4(Material27Readable(_Albedo.rgb, _BaseIrradiance.rgb,
                    _SteppedIrradiance.rgb), 1);
            }
            ENDHLSL
        }
    }
}
