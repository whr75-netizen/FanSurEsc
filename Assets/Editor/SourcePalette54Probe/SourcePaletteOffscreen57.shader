Shader "Hidden/SourcePalette54/Offscreen57"
{
    SubShader {
        Pass {
            ZTest Always ZWrite Off Cull Off Blend Off
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert57
            #pragma fragment Frag57
            #include "SourcePalette54.hlsl"
            struct Sample57 { uint family; float g; };
            StructuredBuffer<Sample57> _Cases57;
            uint _Count57;
            float4 Vert57(uint vertexId : SV_VertexID) : SV_POSITION {
                float2 uv = float2((vertexId << 1) & 2, vertexId & 2);
                return float4(uv * 2.0 - 1.0, 0, 1);
            }
            float4 Frag57(float4 position : SV_POSITION) : SV_Target {
                Sample57 s = _Cases57[min((uint)position.x, _Count57 - 1)];
                uint4 rgba = SourceLookup54(s.family, SourceShade54(s.family, s.g));
                return float4(SourceRGB8ToLinear54(rgba.rgb), (float)rgba.a / 255.0);
            }
            ENDHLSL
        }
    }
}
