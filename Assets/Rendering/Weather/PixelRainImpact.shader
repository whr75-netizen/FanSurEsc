Shader "Hidden/FantasySurvival/PixelRainImpact"
{
    Properties
    {
        _PixelRainSplashAtlas("Splash Atlas", 2D) = "black" {}
        _SplashOpacity("Splash Opacity", Range(0, 1)) = 0.82
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "Queue" = "Transparent-100"
            "RenderType" = "Transparent"
        }

        ZTest LEqual
        ZWrite Off
        Cull Off
        Blend SrcAlpha OneMinusSrcAlpha
        ColorMask RGB

        Pass
        {
            Name "PixelRainImpact"

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_PixelRainSplashAtlas);

            CBUFFER_START(UnityPerMaterial)
                float _SplashOpacity;
            CBUFFER_END

            float _FantasyRainIntensity;
            float4 _FantasyRainColor;
            float _SplashFrame;

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionHCS = TransformObjectToHClip(input.positionOS.xyz);
                output.uv = input.uv;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                const int frameWidth = 7;
                const int frameHeight = 4;
                int frame = clamp((int)round(_SplashFrame), 0, 3);
                int2 localPixel = min(
                    (int2)floor(saturate(input.uv) * int2(frameWidth, frameHeight)),
                    int2(frameWidth - 1, frameHeight - 1));
                int2 atlasPixel = int2(
                    frame * frameWidth + localPixel.x,
                    localPixel.y);
                half mask = LOAD_TEXTURE2D(
                    _PixelRainSplashAtlas,
                    atlasPixel).r;
                half alpha = saturate(
                    mask * _SplashOpacity *
                    _FantasyRainIntensity * _FantasyRainColor.a);
                return half4(_FantasyRainColor.rgb, alpha);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
