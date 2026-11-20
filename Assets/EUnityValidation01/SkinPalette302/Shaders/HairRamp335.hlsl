// Material-profile data derived from unchanged source textures and original MToon baseline.
// The algorithm consumes material colours; no screen coordinates or mesh triangles.
#ifndef HAIR_RAMP335_INCLUDED
#define HAIR_RAMP335_INCLUDED
float3 HairLab335(float3 c){float3 lms=mul(float3x3(.4122214708,.5363325363,.0514459929,.2119034982,.6806995451,.1073969566,.0883024619,.2817188376,.6299787005),max(c,0));lms=pow(lms,1.0/3.0);return mul(float3x3(.2104542553,.793617785,-.0040720468,1.9779984951,-2.428592205,.4505937099,.0259040371,.7827717662,-.808675766),lms);}
float3 HairAnchor335(){return float3(0.0852688534,0.1188193462,0.249105814);}
float3 HairBase335(float3 source,int role){float3 result=source;float best=1e30;float3 lab=HairLab335(source);
if(role==11){
{float3 c=float3(0.06124605423,0.02415763245,0.02415763245);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.1441284709,0.06847816984,0.06662593864);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.270497791,0.1746474037,0.1682694002);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.4507857828,0.3139887134,0.2961382708);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.6104955708,0.4507857828,0.4396571738);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
}
if(role==12){
{float3 c=float3(0.0368894504,0.01370208305,0.01370208305);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.09305896285,0.04091519691,0.03954623528);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.1651321945,0.08228270713,0.07818742181);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.2788942635,0.1441284709,0.138431615);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.3967552307,0.2195261997,0.2086368701);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
}
if(role==13){
{float3 c=float3(0.04518620439,0.01680737575,0.01764195449);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.1094617108,0.04970656598,0.04817182423);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.1946178304,0.09989872825,0.09530746663);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.3231432091,0.1746474037,0.1620293756);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.5457244614,0.2874408377,0.2501582847);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
}
if(role==14){
{float3 c=float3(0.1651321945,0.1412632911,0.1412632911);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.1912016827,0.1620293756,0.1620293756);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.2086368701,0.1844749945,0.1844749945);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
{float3 c=float3(0.2345505822,0.2086368701,0.2086368701);float3 d=HairLab335(c)-lab;float e=dot(d,d);if(e<best){best=e;result=c;}}
}
return f16tof32(f32tof16(result));}
float3 HairFinal335(float3 base,float q,float floorValue,bool enabled){if(!enabled)return base;return f16tof32(f32tof16(base*HairAnchor335()*lerp(floorValue,1,q)));}
#endif
