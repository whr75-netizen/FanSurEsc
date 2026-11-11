// Candidate only. Screen queries: bottom-left +Y; hair ROI: top-left +Y.
// One common 4x footprint, including the existing 4x sampling quantization.
// No eye template, colour, source visibility or skin-ownership rule is changed.
int2 HeadShift25(int2 p){
 float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));
 int2 cell=(int2)floor(centre-_ForwardAnchor102.xy);
 float2 snapDelta=centre-(_ForwardAnchor102.xy+float2(cell)+.5);
 return (int2)round(float2(-snapDelta.x,snapDelta.y)*4);
}
float2 Destination24(int2 p,int si){
 uint x=(uint)si%4u,y=(uint)si/4u;
 float2 physical=float2(_ForwardROI102.x+p.x+(x+.5)/4,272-(_ForwardROI102.y+p.y+(y+.5)/4));
 int2 shift=HeadShift25(p);
 return physical+float2(shift.x,-shift.y)*.25;
}
