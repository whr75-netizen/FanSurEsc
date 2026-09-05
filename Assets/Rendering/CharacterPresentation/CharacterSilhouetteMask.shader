Shader "Hidden/FantasySurvival/Character Silhouette Mask"
{
    Properties
    {
        [HideInInspector] _CharacterArtPixelSize("Character Art Pixel Size", Float) = 3
        [HideInInspector] _CharacterScreenPixelSize("Character Screen Pixel Size", Float) = 5
        [HideInInspector][PerRendererData] _CharacterOutlineGroup("Outline Group", Float) = 0
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
        float _CharacterScreenPixelSize;
        float _CharacterOutlineGroup;

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

        float2 PixelOffsetFromRoot(float4 positionCS)
        {
            float2 fragmentUv = GetNormalizedScreenSpaceUV(positionCS.xy);
            float2 anchorUv = ComputeNormalizedDeviceCoordinates(
                _CharacterPixelGridAnchorWS.xyz,
                UNITY_MATRIX_VP);
            return floor(fragmentUv * _ScaledScreenParams.xy) -
                floor(anchorUv * _ScaledScreenParams.xy);
        }

        half4 FragRaw(Varyings input) : SV_Target
        {
            float pixelSize = clamp(round(_CharacterArtPixelSize), 1.0, 8.0);
            // Preserve the previous centered root-cell phase, while retaining
            // every covered fragment instead of only its cell's center seed.
            float2 offset = PixelOffsetFromRoot(input.positionCS) + floor(pixelSize * 0.5);
            float2 remainder = offset - floor(offset / pixelSize) * pixelSize;
            return half4(1, round(_CharacterOutlineGroup) / 255.0, remainder / 255.0);
        }

        void ClipToCharacterPixelSeed(
            float4 positionCS,
            float pixelSize)
        {
            pixelSize = max(1.0, round(pixelSize));
            float2 offset = PixelOffsetFromRoot(positionCS);
            float2 remainder = offset - floor(offset / pixelSize) * pixelSize;
            half seed =
                (1.0h - step(0.5h, (half)remainder.x)) *
                (1.0h - step(0.5h, (half)remainder.y));
            clip(seed - 0.5h);
        }

        half4 FragSeed(Varyings input) : SV_Target
        {
            ClipToCharacterPixelSeed(
                input.positionCS,
                _CharacterArtPixelSize);
            return half4(0, 1, 0, round(_CharacterOutlineGroup) / 255.0);
        }

        half4 FragScreenPixelSeed(Varyings input) : SV_Target
        {
            // Emit one visible source point per character-local screen cell.
            // The grid phase comes from the presentation root, so rigid motion
            // moves the pixels with the character instead of resampling it
            // against a viewport-fixed grid on every screen-pixel crossing.
            ClipToCharacterPixelSeed(
                input.positionCS,
                _CharacterScreenPixelSize);

            // Store linear eye depth beside occupancy. The later full-screen
            // expansion still depth-tests the enlarged cell against the scene.
            float eyeDepth = LinearEyeDepth(input.positionCS.z, _ZBufferParams);
            return half4(1.0h, (half)max(eyeDepth, 0.0001), 0.0h, 1.0h);
        }
        ENDHLSL

        Pass
        {
            Name "CharacterSilhouetteRawMask"

            // Follow the surfaces actually present in opaque camera depth,
            // including two-sided source materials, without seeing hidden parts.
            Cull Off
            ZWrite Off
            ZTest Equal
            ColorMask RGBA

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragRaw
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            // Reserved pass index: classic coverage no longer schedules seeds.
            // Keep stencil index 2 and screen-pixel seed index 3 unchanged.
            Name "CharacterSilhouettePixelSeeds"

            Cull Off
            ZWrite Off
            ZTest Equal
            ColorMask GA

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragSeed
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "CharacterVisibleStencil"

            Cull Off
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


        Pass
        {
            Name "CharacterScreenPixelSeedMask"

            Cull Back
            ZWrite Off
            ZTest LEqual
            ColorMask RG

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragScreenPixelSeed
            #pragma multi_compile_instancing
            ENDHLSL
        }
    }

    FallBack Off
}
