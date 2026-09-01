Shader "Hidden/FantasySurvival/Character Silhouette Mask"
{
    Properties
    {
        [HideInInspector] _CharacterArtPixelSize("Character Art Pixel Size", Float) = 3
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
        }

        HLSLINCLUDE
        #pragma target 3.5

        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        float4 _CharacterPixelGridAnchorWS;
        float _CharacterArtPixelSize;

        struct Attributes
        {
            float4 positionOS : POSITION;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };

        struct Varyings
        {
            float4 positionCS : SV_POSITION;
            UNITY_VERTEX_OUTPUT_STEREO
        };

        Varyings Vert(Attributes input)
        {
            Varyings output;
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
            output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
            return output;
        }

        half4 FragRaw(Varyings input) : SV_Target
        {
            return half4(1, 0, 0, 1);
        }

        half4 FragSeed(Varyings input) : SV_Target
        {
            float artPixelSize = max(1.0, round(_CharacterArtPixelSize));
            float2 fragmentUv = GetNormalizedScreenSpaceUV(input.positionCS.xy);
            float2 anchorUv = ComputeNormalizedDeviceCoordinates(
                _CharacterPixelGridAnchorWS.xyz,
                UNITY_MATRIX_VP);
            float2 pixelIndex = floor(fragmentUv * _ScaledScreenParams.xy);
            float2 anchorPixelIndex = floor(anchorUv * _ScaledScreenParams.xy);
            float2 offset = pixelIndex - anchorPixelIndex;
            float2 remainder = offset - floor(offset / artPixelSize) * artPixelSize;
            half seed =
                (1.0h - step(0.5h, (half)remainder.x)) *
                (1.0h - step(0.5h, (half)remainder.y));
            clip(seed - 0.5h);
            return half4(0, 1, 0, 1);
        }
        ENDHLSL

        Pass
        {
            Name "CharacterSilhouetteRawMask"

            Cull Back
            ZWrite Off
            ZTest LEqual
            ColorMask R

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragRaw
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "CharacterSilhouettePixelSeeds"

            Cull Back
            ZWrite Off
            ZTest LEqual
            ColorMask G

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragSeed
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "CharacterVisibleStencil"

            Cull Back
            ZWrite Off
            ZTest Equal
            ColorMask 0

            // Keep bit 1 for this feature. URP may claim bits 2-3 when its
            // optional stencil LOD cross-fade path is enabled.
            Stencil
            {
                Ref 2
                WriteMask 2
                Comp Always
                Pass Replace
            }

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragRaw
            #pragma multi_compile_instancing
            ENDHLSL
        }
    }

    FallBack Off
}
