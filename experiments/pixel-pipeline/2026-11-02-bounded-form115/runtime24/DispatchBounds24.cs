// Pure integer/finite guards. No Unity, graphics device or side effects.
namespace Execution24 {
public static class DispatchBounds24 {
 public static int Product(int width,int height,int multiple,int maximum){
  if(width<1||height<1||multiple<1||width%multiple!=0||height%multiple!=0||(long)width*height>maximum)throw new System.ArgumentException("24 grid/product bound");
  return width*height;
 }
 public static void Grid(int tw,int th,int sw,int sh,int cw,int ch,int rw,int rh,int keys,int curves){
  Product(tw,th,4,32768);Product(sw,sh,8,32768);Product(cw,ch,8,32768);Product(rw,rh,1,512);
  Product(sw/8,sh/8,1,512);
  if(tw!=sw/2||th!=sh/2||cw!=sw||ch!=sh||keys<1||keys>32||curves<1||curves>1024)throw new System.ArgumentException("24 source/carrier/layout contract");
 }
 public static void Topology(int vertices,int triangles,int materials,int primitiveStride,int partCount,int alphaCount){
  if(vertices<1||vertices>131072||triangles<1||triangles>262144||materials<1||materials>System.Int32.MaxValue/48||primitiveStride<1||(long)primitiveStride*4!=partCount||alphaCount<0||alphaCount>16777216)throw new System.ArgumentException("24 topology/resource bound");
 }
 public static void Triangle(int a,int b,int c,int material,int vertices,int materials){
  if(a<0||a>=vertices||b<0||b>=vertices||c<0||c>=vertices||material<0||material>=materials)throw new System.ArgumentException("24 triangle index");
 }
 public static void PartIndex(int index,int triangles){if(index< -1||index>=triangles)throw new System.ArgumentException("24 primitive map index");}
 public static void Finite(float value){if(System.Single.IsNaN(value)||System.Single.IsInfinity(value))throw new System.ArgumentException("24 non-finite geometry/matrix");}
 public static void Texture(float slot,float width,float height,float mode){
  Finite(slot);Finite(width);Finite(height);Finite(mode);
  if(mode!=0&&(slot<0||slot>=32||slot!=(int)slot||width<1||height<1||width!=(int)width||height!=(int)height))throw new System.ArgumentException("24 alpha texture descriptor");
 }
}
}
