Shader "FantasySurvival/World/Isometric Atlas Surface"
{
    Properties
    {
        [MainTexture] _BaseMap("Source Atlas", 2D) = "white" {}
        _MaskMap("Source Component Mask", 2D) = "white" {}
        [MainColor] _BaseColor("Tint and Opacity", Color) = (1,1,1,1)
        _Homography0("Homography Row 0", Vector) = (1,0,0,0)
        _Homography1("Homography Row 1", Vector) = (0,1,0,0)
        _Homography2("Homography Row 2", Vector) = (0,0,1,0)
        [HideInInspector] _VertexAtlasUv("Homogeneous Atlas UV in Vertex", Float) = 0
        [HideInInspector] _MetricLighting("Real Surface Lighting", Float) = 0
        [HideInInspector] _NativeGridEnabled("Native Sprite Grid", Float) = 0
        [HideInInspector] _NativeGridOriginOS("Source UV Zero in Object Space", Vector) = (0,0,0,0)
        [HideInInspector] _NativeGridTexelUOS("One Source Texel U in Object Space", Vector) = (0,0,0,0)
        [HideInInspector] _NativeGridTexelVOS("One Source Texel V in Object Space", Vector) = (0,0,0,0)
        [HideInInspector] _ZWrite("Depth Write", Float) = 1
        [HideInInspector] _SrcBlend("Source Blend", Float) = 1
        [HideInInspector] _DstBlend("Destination Blend", Float) = 0
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

        TEXTURE2D(_BaseMap);
        TEXTURE2D(_MaskMap);
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseColor;
            float4 _Homography0;
            float4 _Homography1;
            float4 _Homography2;
            float _VertexAtlasUv;
            float _MetricLighting;
            float _ZWrite;
            float _NativeGridEnabled;
            float4 _NativeGridOriginOS;
            float4 _NativeGridTexelUOS;
            float4 _NativeGridTexelVOS;
        CBUFFER_END

        struct Attributes
        {
            float3 positionOS : POSITION;
            float3 uv : TEXCOORD0;
            float3 normalOS : NORMAL;
        };

        struct Varyings
        {
            float4 positionCS : SV_POSITION;
            float3 uv : TEXCOORD0;
            half3 light : TEXCOORD1;
            half3 normalWS : TEXCOORD2;
        };

        float2 RasterPosition(float4 positionCS)
        {
            float2 ndc = positionCS.xy / positionCS.w;
            ndc.y *= _ProjectionParams.x;
            return (ndc * 0.5 + 0.5) * _ScaledScreenParams.xy;
        }

        float4 SnapNativeSprite(float4 positionCS)
        {
            if (_NativeGridEnabled < 0.5 || unity_OrthoParams.w < 0.5)
                return positionCS;

            float3 originWS = TransformObjectToWorld(_NativeGridOriginOS.xyz);
            float3 texelUWS = mul((float3x3)unity_ObjectToWorld, _NativeGridTexelUOS.xyz);
            float3 texelVWS = mul((float3x3)unity_ObjectToWorld, _NativeGridTexelVOS.xyz);
            float2 texelUVS = mul((float3x3)UNITY_MATRIX_V, texelUWS).xy;
            float2 texelVVS = mul((float3x3)UNITY_MATRIX_V, texelVWS).xy;
            // This is a translation of the entire visual surface, never a per-vertex
            // reshape. Only the authored orthographic, screen-aligned basis qualifies.
            if (texelUVS.x <= 0.000001 || texelVVS.y <= 0.000001 ||
                abs(texelUVS.y) > texelUVS.x * 0.0001 ||
                abs(texelVVS.x) > texelVVS.y * 0.0001 ||
                abs(texelUVS.x - texelVVS.y) > texelUVS.x * 0.0001)
                return positionCS;

            float4 originCS = TransformWorldToHClip(originWS);
            float2 originRaster = RasterPosition(originCS);
            float2 uRaster = RasterPosition(TransformWorldToHClip(originWS + texelUWS)) - originRaster;
            float2 vRaster = RasterPosition(TransformWorldToHClip(originWS + texelVWS)) - originRaster;
            float integerScale = round(abs(uRaster.x));
            if (integerScale < 1.0 || abs(abs(uRaster.x) - integerScale) > 0.01 ||
                abs(abs(vRaster.y) - integerScale) > 0.01 ||
                abs(uRaster.y) > 0.01 || abs(vRaster.x) > 0.01)
                return positionCS;

            // First align each source origin to one world lattice. Then apply the
            // same camera phase to all surfaces. Rounding moving screen anchors
            // independently would make stationary furniture jitter relative to itself.
            float2 sourceWorld = mul((float3x3)UNITY_MATRIX_V, originWS).xy /
                float2(texelUVS.x, texelVVS.y);
            float2 sourceOffset = round(sourceWorld) - sourceWorld;
            float2 worldZeroRaster = RasterPosition(TransformWorldToHClip(float3(0,0,0)));
            float2 cameraOffset = round(worldZeroRaster / integerScale) * integerScale - worldZeroRaster;
            float2 rasterOffset = sourceOffset * float2(uRaster.x, vRaster.y) + cameraOffset;
            // Undo the platform projection Y sign used by RasterPosition.
            positionCS.xy += rasterOffset * (2.0 / _ScaledScreenParams.xy) *
                float2(1.0, _ProjectionParams.x) * positionCS.w;
            return positionCS;
        }

        Varyings Vert(Attributes input)
        {
            Varyings output;
            output.positionCS = SnapNativeSprite(TransformObjectToHClip(input.positionOS));
            output.uv = input.uv;
            half3 n = TransformObjectToWorldNormal(input.normalOS);
            output.normalWS = n;
            Light mainLight = GetMainLight();
            output.light = SampleSH(n) + LightingLambert(mainLight.color, mainLight.direction, n);
            return output;
        }

        half4 SampleClippedSource(float3 sourceUv)
        {
            // Each physical tile or wall module supplies a unit-square UV domain.
            float3 projected;
            if (_VertexAtlasUv > 0.5)
                projected = sourceUv;
            else
            {
                clip(min(min(sourceUv.x, sourceUv.y), min(1.0 - sourceUv.x, 1.0 - sourceUv.y)) + 1e-5);
                float3 canonical = float3(saturate(sourceUv.xy), 1.0);
                projected = float3(dot(_Homography0.xyz, canonical),
                    dot(_Homography1.xyz, canonical), dot(_Homography2.xyz, canonical));
            }
            clip(projected.z - 1e-6);
            float2 atlasUv = projected.xy / projected.z;
            half component = SAMPLE_TEXTURE2D(_MaskMap, sampler_PointClamp, atlasUv).r;
            clip(component - 0.5h);
            half4 source = SAMPLE_TEXTURE2D(_BaseMap, sampler_PointClamp, atlasUv);
            // Clip the source mask, not the fader opacity: a faded roof may intentionally be below 0.1.
            clip(source.a - 0.1h);
            return source;
        }

        half4 Frag(Varyings input) : SV_Target
        {
            half4 source = SampleClippedSource(input.uv);
            source.rgb *= lerp(half3(1,1,1), input.light, _MetricLighting);
            return source * _BaseColor;
        }

        half DepthFrag(Varyings input) : SV_Target
        {
            // The fader and contact masks opt out of depth ownership. Do not inject
            // their geometry into depth/normal buffers while forward ZWrite is off.
            clip(_ZWrite - 0.5);
            SampleClippedSource(input.uv);
            return input.positionCS.z;
        }

        void DepthNormalsFrag(Varyings input, out half4 outNormalWS : SV_Target0
        #ifdef _WRITE_RENDERING_LAYERS
            , out uint outRenderingLayers : SV_Target1
        #endif
        )
        {
            clip(_ZWrite - 0.5);
            SampleClippedSource(input.uv);
            // Preserve the mesh surface normal; no fictitious sprite material normal.
        #if defined(_GBUFFER_NORMALS_OCT)
            float3 normalWS = normalize(input.normalWS);
            float2 octNormalWS = PackNormalOctQuadEncode(normalWS);
            float2 remappedOctNormalWS = saturate(octNormalWS * 0.5 + 0.5);
            outNormalWS = half4(PackFloat2To888(remappedOctNormalWS), 0.0);
        #else
            outNormalWS = half4(NormalizeNormalPerPixel(input.normalWS), 0.0);
        #endif
        #ifdef _WRITE_RENDERING_LAYERS
            outRenderingLayers = EncodeMeshRenderingLayer();
        #endif
        }

        ENDHLSL

        Pass
        {
            Name "IsometricAtlasSurface"
            Tags { "LightMode"="UniversalForward" }
            Cull Off
            ZTest LEqual
            ZWrite [_ZWrite]
            Blend [_SrcBlend] [_DstBlend]
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            Cull Off
            ZTest LEqual
            ZWrite [_ZWrite]
            ColorMask R
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment DepthFrag
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormalsOnly"
            Tags { "LightMode"="DepthNormalsOnly" }
            Cull Off
            ZTest LEqual
            ZWrite [_ZWrite]
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment DepthNormalsFrag
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/ShaderLibrary/RenderingLayers.hlsl"
            ENDHLSL
        }
    }
}
