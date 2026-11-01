 // Parent eye feature competes with canvas BEFORE its child parts compete.
 // [iris2 + white7, canvas7] is a visible 9/16 eye, not an unresolved 7/7 tie.
 int winner=-1,preferred=-1;bool usedWitness=false,coldChoice=false;
 float eyeLower=16-U[3],eyeUpper=16-L[3];bool exact=true;
 [unroll]for(int p=0;p<4;p++)if(L[p]!=U[p])exact=false;
 if(L[3]>eyeUpper)winner=3;
 bool parentVisible=eyeLower>U[3]||(exact&&eyeLower==U[3]&&eyeLower>0);
 if(parentVisible){
  [unroll]for(int p=0;p<3;p++){bool sure=true;[unroll]for(int q=0;q<3;q++)if(p!=q&&L[p]<=U[q])sure=false;if(sure)winner=p;}
  if(winner<0&&exact){
   float maximum=max(L[0],max(L[1],L[2]));float meanDepth[3];float nearest=3.402823e38;int front=-1;bool sameDepth=false;
   [unroll]for(int p=0;p<3;p++){
    meanDepth[p]=3.402823e38;
    if(L[p]==maximum&&L[p]>0){float sum=0,total=0;
     [unroll]for(int i=0;i<16;i++){float w=weight[p*16+i];if(w>0){int at=(id.y*4+(i>>2))*_Size96.x+id.x*4+(i&3);sum+=w*Layer96(p+1,1,at).x;total+=w;}}
     if(total>0)meanDepth[p]=sum/total;
     if(meanDepth[p]<nearest){nearest=meanDepth[p];front=p;sameDepth=false;}
     else if(meanDepth[p]==nearest)sameDepth=true;
    }
   }
   if(front>=0&&!sameDepth)winner=front;
  }
 }
 // Exact half-coverage belongs to the foreground eye layer (inclusive .5),
 // not a minimum pixel budget. Unknown intervals and exact source-depth ties
 // remain explicit. No frame-order/array-order tie or RGB blending is used.
