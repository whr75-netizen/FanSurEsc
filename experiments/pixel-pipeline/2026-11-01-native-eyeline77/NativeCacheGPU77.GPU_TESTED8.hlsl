// Owned per-renderer source cache. XYZ remains immutable. Metadata uses only W.
// One CountFeatures19 thread publishes it; Evaluate reads after that dispatch.
#define NATIVE_TRI_LIMIT77 256
#define NATIVE_DESC_START77 21
void NativeMeta77(int index,float value){float4 v=_RestTriangles348[index];v.w=value;_RestTriangles348[index]=v;}
float NativeInput77(int i,int count,int offset,int size){if(i==0)return count;if(i==1)return offset;if(i==2)return size;int v=i-3;if(v<8)return _Centres348[v/4][v&3];v-=8;return _AxesY348[v/4][v&3];}
bool NativeSameInput77(int count,int offset,int size){bool same77=true;for(int i77=0;i77<19;i77++)same77=same77&&_RestTriangles348[1+i77].w==NativeInput77(i77,count,offset,size);return same77;}
// Union-find lives in this owner's cache W, never in a 256-element per-thread
// local array. Only this Count invocation accesses it until the next dispatch.
int NativeLabel77(int offset,int index){return abs((int)round(_RestTriangles348[offset+3*index].w))-1;}
int NativeRoot77(int offset,int index,int count){[loop]for(int step77=0;step77<count;step77++){int parent77=NativeLabel77(offset,index);if(parent77==index)break;index=parent77;}return index;}
void NativeInit77(){
 uint size77,stride77;_RestTriangles348.GetDimensions(size77,stride77);if(size77==0)return;int count77=(int)_TriangleRanges348[6].y,base77=(int)_TriangleRanges348[6].x;
 if(stride77!=16||count77<=0||count77>NATIVE_TRI_LIMIT77||base77<NATIVE_DESC_START77+4*count77||base77+3*count77>(int)size77){NativeMeta77(0,-77);return;}
 float header77=_RestTriangles348[0].w;if((header77==77||header77==-77)&&NativeSameInput77(count77,base77,size77))return;
 // Never adopt unknown W content. A new owned renderer buffer uploads W=0.
 if(header77!=0&&header77!=77&&header77!=-77)return;
 for(int i77=0;i77<19;i77++)NativeMeta77(1+i77,NativeInput77(i77,count77,base77,size77));
 if(all(_Centres348[0].xyz==_Centres348[1].xyz)||_Centres348[0].w==_Centres348[1].w||_AxesY348[0].w<=0||_AxesY348[1].w<=0){NativeMeta77(0,-77);return;}
 [loop]for(int i77=0;i77<count77;i77++)NativeMeta77(base77+3*i77,i77+1);
 [loop]for(int a77=0;a77<count77;a77++){
  float3 a0=_RestTriangles348[base77+3*a77].xyz,a1=_RestTriangles348[base77+3*a77+1].xyz,a2=_RestTriangles348[base77+3*a77+2].xyz;
  if(!all(isfinite(a0))||!all(isfinite(a1))||!all(isfinite(a2))){NativeMeta77(0,-77);return;}
  [loop]for(int b77=0;b77<a77;b77++){
   float3 b0=_RestTriangles348[base77+3*b77].xyz,b1=_RestTriangles348[base77+3*b77+1].xyz,b2=_RestTriangles348[base77+3*b77+2].xyz;
   bool shared77=all(a0==b0)||all(a0==b1)||all(a0==b2)||all(a1==b0)||all(a1==b1)||all(a1==b2)||all(a2==b0)||all(a2==b1)||all(a2==b2);
   if(shared77){int ra77=NativeRoot77(base77,a77,count77),rb77=NativeRoot77(base77,b77,count77);NativeMeta77(base77+3*max(ra77,rb77),min(ra77,rb77)+1);}
  }
 }
 [loop]for(int i77=0;i77<count77;i77++)NativeMeta77(base77+3*i77,NativeRoot77(base77,i77,count77)+1);
 // First validate every group. Publish only after the complete source contract.
 [loop]for(int pass77=0;pass77<2;pass77++){
  int upper0=0,upper1=0;bool valid77=true;
  [loop]for(int root77=0;root77<count77;root77++){
   if(NativeLabel77(base77,root77)!=root77)continue;float3 sum77=0;float total77=0;
   [loop]for(int t77=0;t77<count77;t77++){if(NativeLabel77(base77,t77)!=root77)continue;float3 a=_RestTriangles348[base77+3*t77].xyz,b=_RestTriangles348[base77+3*t77+1].xyz,c=_RestTriangles348[base77+3*t77+2].xyz;float area77=length(cross(b-a,c-a))*.5;sum77+=(a+b+c)*(area77/3);total77+=area77;}
   valid77=valid77&&total77>0;float3 mean77=sum77/max(total77,1e-30);float3 d0=mean77-_Centres348[0].xyz,d1=mean77-_Centres348[1].xyz;float e0=dot(d0,d0),e1=dot(d1,d1);valid77=valid77&&e0!=e1;int eye77=e0<e1?0:1;float vertical77=-dot(mean77-_Centres348[eye77].xyz,_AxesY348[eye77].xyz)/_AxesY348[eye77].w;valid77=valid77&&isfinite(vertical77)&&vertical77!=0;
   if(vertical77<0){if(eye77==0)upper0++;else upper1++;}
   if(pass77==1){int signed77=vertical77<0?root77+1:-(root77+1);NativeMeta77(NATIVE_DESC_START77+4*root77,_Centres348[eye77].w);NativeMeta77(NATIVE_DESC_START77+1+4*root77,mean77.x);NativeMeta77(NATIVE_DESC_START77+2+4*root77,mean77.y);NativeMeta77(NATIVE_DESC_START77+3+4*root77,mean77.z);
    [loop]for(int t77=0;t77<count77;t77++)if(NativeLabel77(base77,t77)==root77)NativeMeta77(base77+3*t77,signed77);
   }
  }
  if(pass77==0&&(!valid77||upper0!=1||upper1!=1)){NativeMeta77(0,-77);return;}
 }
 NativeMeta77(0,77);
}
bool NativeSourceReady77(){return _RestTriangles348[0].w==77;}
int NativeComponent77(int primitive){if(primitive<=0||primitive>(int)_TriangleRanges348[6].y)return 0;return(int)round(_RestTriangles348[(int)_TriangleRanges348[6].x+3*(primitive-1)].w);}
float3 NativeCentre77(int component){int root77=abs(component)-1;return float3(_RestTriangles348[NATIVE_DESC_START77+1+4*root77].w,_RestTriangles348[NATIVE_DESC_START77+2+4*root77].w,_RestTriangles348[NATIVE_DESC_START77+3+4*root77].w);}
int NativeEye77(int component){return(int)round(_RestTriangles348[NATIVE_DESC_START77+4*(abs(component)-1)].w);}
