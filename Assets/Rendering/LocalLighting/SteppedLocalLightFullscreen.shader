Shader "Hidden/FantasySurvival/SteppedLocalLightFullscreen"
{
    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        // Legacy world has no albedo buffer. Modulate its existing lit colour
        // rather than paint independent RGB over it. Native/character use
        // their own true material response and are stencil-excluded below.
        // This gain is not a reconstruction of missing diffuse reflectance.
        Blend DstColor One
        ColorMask RGB

        Pass
        {
            Name "SteppedLocalLightFullscreen"

            // A post-opaque visible-fragment pass marks only character pixels
            // that survived the scene depth test. Skipping those pixels here
            // prevents a second, normal-driven light pass from revealing the
            // 3D surface or cutting character shapes out of foreground walls.
            Stencil
            {
                Ref 2
                ReadMask 2
                Comp NotEqual
                Pass Keep
            }

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

            #include "Assets/Rendering/LocalLighting/SteppedLocalLightCommon.hlsl"

            float GeometryMask(float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    return step(0.000001, rawDepth);
                #else
                    return 1.0 - step(0.999999, rawDepth);
                #endif
            }

            float3 ReconstructWorldPosition(float2 uv, float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    float deviceDepth = rawDepth;
                #else
                    float deviceDepth = lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif

                return ComputeWorldSpacePosition(uv, deviceDepth, UNITY_MATRIX_I_VP);
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float2 uv = saturate(input.texcoord.xy);
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                if (GeometryMask(rawDepth) <= 0.0)
                {
                    return half4(0.0, 0.0, 0.0, 0.0);
                }

                float3 positionWS = ReconstructWorldPosition(uv, rawDepth);
                float3 normalWS = SteppedSafeNormalize(
                    SampleSceneNormals(uv, sampler_PointClamp));
                return half4(
                    EvaluateSteppedLocalLights(positionWS, normalWS, 1.0),
                    0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
