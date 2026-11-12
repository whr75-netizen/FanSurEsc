// CPU-only adapter of observed ordinary source-carrier receipts. No region or
// colour-family inference. No texture sampling, Unity object, GPU or history.
using System;
public static class SelectedShade65 {
 public sealed class Observed {
  public ResolvedShade52.Stamp stamp;
  public int registeredRole,triangleCount,levels;
  public bool layeredSurface,styleEnabled,headRegionEnabled;
  public float[] selectedUV,selectedSource,nativeOwner,carrier,nativeCell;
 }
 public sealed class Packet {
  public ResolvedShade52.Shade shade;public int[] k,primitive;
  public float[] sourceUV;public int observed,excluded;
 }
 static void Require(bool ok,string why){if(!ok)throw new ArgumentException(why);}
 static bool Finite(float f){return !Single.IsNaN(f)&&!Single.IsInfinity(f);}
 static bool Tuple(float[] a,int j){return Finite(a[j])&&Finite(a[j+1])&&Finite(a[j+2])&&Finite(a[j+3]);}
 public static Packet Build(Observed o){
  Require(o!=null&&o.stamp!=null,"65 observed scope required");var s=o.stamp;
  Require(!String.IsNullOrEmpty(s.actor)&&!String.IsNullOrEmpty(s.view)&&!String.IsNullOrEmpty(s.sourceId)&&s.frame>=0&&s.serial>=0&&s.width>0&&s.height>0&&(long)s.width*s.height<=Int32.MaxValue/4,"65 valid observed identity/extent required");
  Require(s.stage=="selected-surface/after-Restore-Join-Resolve"&&s.producer=="Restore335.class.x->PreparedUV.z->GridJoin367->Resolve333->SourceNativeHull60.receipt1","65 exact selected surface stage required; not initial Q or final RGB");
  Require(o.registeredRole>0&&o.triangleCount>0&&o.levels>=2&&o.levels<=256&&o.layeredSurface&&o.styleEnabled&&!o.headRegionEnabled,"65 validated layered ordinary-source path required");
  int n=s.width*s.height;foreach(var a in new[]{o.selectedUV,o.selectedSource,o.nativeOwner,o.carrier,o.nativeCell})Require(a!=null&&a.Length==4*n,"65 exact raster receipt arrays required");
  var stamp=new ResolvedShade52.Stamp{actor=s.actor,view=s.view,sourceId=s.sourceId,stage=s.stage,producer=s.producer,frame=s.frame,serial=s.serial,width=s.width,height=s.height};
  var p=new Packet{shade=new ResolvedShade52.Shade{stamp=stamp,appliedQ=new float[n],levels=new int[n],known=new bool[n]},k=new int[n],primitive=new int[n],sourceUV=new float[n*2]};
  for(int i=0;i<n;i++){
   int j=4*i;if(o.carrier[j]!=o.registeredRole){p.excluded++;continue;}
   Require(Tuple(o.selectedUV,j)&&Tuple(o.selectedSource,j)&&Tuple(o.nativeOwner,j)&&Tuple(o.carrier,j)&&Tuple(o.nativeCell,j),"65 nonfinite ordinary-source receipt");
   float primitive=o.selectedSource[j+3];
   Require(o.nativeCell[j+2]==1&&o.selectedSource[j]==o.nativeOwner[j+2]&&o.selectedSource[j+1]==o.nativeOwner[j]&&o.selectedSource[j+2]==o.nativeOwner[j+1]&&o.selectedSource[j+1]==o.registeredRole&&o.carrier[j+1]==o.registeredRole&&o.carrier[j+2]==o.selectedSource[j+2]&&o.carrier[j+3]==primitive&&primitive>=1&&primitive<=o.triangleCount&&primitive==(float)Math.Round(primitive),"65 native/source/role/primitive ownership mismatch");
   float q=o.selectedUV[j+2];int k=(int)Math.Round(q*(o.levels-1));
   Require(k>=0&&k<o.levels&&q==(float)k/(float)(o.levels-1),"65 observed selected Q outside exact producer levels; never repair or infer it");
   p.shade.known[i]=true;p.shade.appliedQ[i]=q;p.shade.levels[i]=o.levels;p.k[i]=k;p.primitive[i]=(int)primitive;p.sourceUV[2*i]=o.selectedUV[j];p.sourceUV[2*i+1]=o.selectedUV[j+1];p.observed++;
  }
  return p;
 }
}
