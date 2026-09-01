Shader "Hidden/FantasySurvival/Character Silhouette Composite"
{
    Properties
    {
        _OutlineColor("Outline Color", Color) = (0.025, 0.025, 0.03, 1)
        _ArtPixelSize("Screen Pixels Per Art Cell", Range(1, 8)) = 3
        _CoverageThreshold("Mask Threshold", Range(0.05, 0.95)) = 0.35
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+100"
        }

        Pass
        {
            Name "CharacterSilhouetteComposite"

            Blend SrcAlpha OneMinusSrcAlpha
            Cull Off
            ZWrite Off
            ZTest Always

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_CharacterSilhouetteMask);

            CBUFFER_START(UnityPerMaterial)
                half4 _OutlineColor;
                float _ArtPixelSize;
                float _CoverageThreshold;
            CBUFFER_END

            struct Attributes
            {
                uint vertexID : SV_VertexID;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            half Occupancy(float2 cell, float2 gridSize)
            {
                float2 sampleUv = saturate((cell + 0.5) / gridSize);
                half mask = SAMPLE_TEXTURE2D(_CharacterSilhouetteMask, sampler_PointClamp, sampleUv).r;
                return step(_CoverageThreshold, mask);
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float artPixelSize = max(1.0, round(_ArtPixelSize));
                float2 gridSize = max(floor(_ScreenParams.xy / artPixelSize), 1.0);
                float2 cell = floor(saturate(input.uv) * gridSize);

                half center = Occupancy(cell, gridSize);
                half nearest = 0;
                nearest = max(nearest, Occupancy(cell + float2(-1, -1), gridSize));
                nearest = max(nearest, Occupancy(cell + float2( 0, -1), gridSize));
                nearest = max(nearest, Occupancy(cell + float2( 1, -1), gridSize));
                nearest = max(nearest, Occupancy(cell + float2(-1,  0), gridSize));
                nearest = max(nearest, Occupancy(cell + float2( 1,  0), gridSize));
                nearest = max(nearest, Occupancy(cell + float2(-1,  1), gridSize));
                nearest = max(nearest, Occupancy(cell + float2( 0,  1), gridSize));
                nearest = max(nearest, Occupancy(cell + float2( 1,  1), gridSize));

                half outerSilhouette = nearest * (1.0h - center);
                return half4(_OutlineColor.rgb, _OutlineColor.a * outerSilhouette);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
