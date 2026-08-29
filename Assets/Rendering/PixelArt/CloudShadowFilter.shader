Shader "Hidden/FantasySurvival/CloudShadowFilter"
{
    Properties
    {
        _MainTex ("Cloud Shadow Cookie", 2D) = "white" {}
        _SoftnessMip ("Softness Mip", Range(0, 3)) = 0
        _Opacity ("Opacity", Range(0, 1)) = 1
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        Cull Off
        ZWrite Off
        ZTest Always

        Pass
        {
            Name "CloudShadowPrefilter"

            CGPROGRAM
            #pragma target 3.0
            #pragma vertex vert_img
            #pragma fragment Frag

            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float _SoftnessMip;
            float _Opacity;

            fixed4 Frag(v2f_img input) : SV_Target
            {
                fixed transmission = tex2Dlod(
                    _MainTex,
                    float4(input.uv, 0.0, _SoftnessMip)).r;
                transmission = lerp(1.0, transmission, saturate(_Opacity));
                return fixed4(transmission, transmission, transmission, 1.0);
            }
            ENDCG
        }
    }

    Fallback Off
}
