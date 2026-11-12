using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
namespace LineGeometry97 {
 public sealed class Strip103 {
  public readonly Triangle triangle;public readonly int edge;public readonly double a,b,c;
  public Strip103(Triangle triangle,int edge,double a,double b,double c){this.triangle=triangle;this.edge=edge;this.a=a;this.b=b;this.c=c;}
 }
 public sealed class RowStats103 {public int workers,splitRow;public long topCandidateCells,bottomCandidateCells;public double mainMs,workerMs,joinMs,totalMs;public bool allWorkersCompleted,queryViewsReleased;}
 public static class RowParallel103 {
  // TickCount is a public monotonic millisecond clock in the already supplied
  // mscorlib. Unsigned subtraction handles its wrap; outer high-resolution
  // Editor timing still measures the entire preparation phase on its owner.
  static double Elapsed103(int start){return unchecked((uint)(Environment.TickCount-start));}
  public static int Split103(Raster raster,List<Strip103> strips,out long top,out long bottom){
   // Partition only scheduling, using the exact candidate-cell bounds of Add.
   // No source shape/colour/visibility or output selection is changed.
   var rows=new long[raster.width];long total=0;
   foreach(var s in strips){var t=s.triangle;if(t.det==0)continue;
    int x0=Math.Max(0,(int)Math.Floor(Math.Min(t.a.x,Math.Min(t.b.x,t.c.x))-raster.origin.x)),x1=Math.Min(raster.width-1,(int)Math.Floor(Math.Max(t.a.x,Math.Max(t.b.x,t.c.x))-raster.origin.x)),y0=Math.Max(0,(int)Math.Floor(Math.Min(t.a.y,Math.Min(t.b.y,t.c.y))-raster.origin.y)),y1=Math.Min(raster.width-1,(int)Math.Floor(Math.Max(t.a.y,Math.Max(t.b.y,t.c.y))-raster.origin.y));
    if(x0>x1)continue;for(int y=y0;y<=y1;y++){rows[y]+=x1-x0+1;total+=x1-x0+1;}
   }
   int split=1;long prefix=0,best=long.MaxValue;top=0;bottom=total;
   for(int y=1;y<raster.width;y++){prefix+=rows[y-1];long cost=Math.Max(prefix,total-prefix);if(cost<best){best=cost;split=y;top=prefix;bottom=total-prefix;}}
   return split;
  }
  // Scene geometry/index, source images and feature registration are immutable
  // until both row partitions complete. No Unity API or GPU resource is used
  // by the worker. Each pixel and its feature dictionaries have one writer.
  public static RowStats103 Run(Scene scene,Raster raster,CurveOpacity98 collector,List<Strip103> strips){
   if(strips==null||strips.Count>2048)throw new ArgumentException("103 bounded source strips");int clock=Environment.TickCount;var result=new RowStats103();collector.SealFeatures103();
   if(raster.width<2||Environment.ProcessorCount<2){foreach(var s in strips)raster.Add(s.triangle,s.edge,s.a,s.b,s.c);result.workers=1;result.allWorkersCompleted=true;result.queryViewsReleased=scene.ActiveQueryViews103==0;result.totalMs=Elapsed103(clock);return result;}
   Scene top=null,bottom=null;Raster first=null,second=null;Task worker=null;var errors=new List<Exception>();int split=Split103(raster,strips,out result.topCandidateCells,out result.bottomCandidateCells);result.splitRow=split;double workerMs=0;result.workers=2;
   try{
    top=scene.ForkQueries103();bottom=scene.ForkQueries103();first=new Raster(top,raster,0,split);second=new Raster(bottom,raster,split,raster.width);first.fragmentVisitor=collector.Visit;second.fragmentVisitor=collector.Visit;Scene firstQuery=top,secondQuery=bottom;collector.QueryForRow103=y=>y<split?firstQuery:secondQuery;
    var immutable=strips.ToArray();Raster firstRaster=first;worker=Task.Factory.StartNew(()=>{int watch=Environment.TickCount;try{foreach(var s in immutable)firstRaster.Add(s.triangle,s.edge,s.a,s.b,s.c);}finally{workerMs=Elapsed103(watch);}},CancellationToken.None,TaskCreationOptions.None,TaskScheduler.Default);
    int mainClock=Environment.TickCount;try{foreach(var s in immutable)second.Add(s.triangle,s.edge,s.a,s.b,s.c);}catch(Exception e){errors.Add(e);}finally{result.mainMs=Elapsed103(mainClock);}
   }catch(Exception e){errors.Add(e);}
   finally{
    // Always join, including main-partition failure. A read lease is never
    // released by a timeout while a task might still be using its source.
    int join=Environment.TickCount;if(worker!=null)try{worker.Wait();}catch(Exception e){errors.Add(e);}result.joinMs=Elapsed103(join);result.workerMs=workerMs;result.allWorkersCompleted=worker==null||worker.IsCompleted;collector.QueryForRow103=null;if(top!=null)top.ReleaseQueries103();if(bottom!=null)bottom.ReleaseQueries103();result.queryViewsReleased=scene.ActiveQueryViews103==0;
   }
   if(errors.Count!=0)throw new AggregateException("103 CPU row work failed after all tasks joined",errors);
   scene.queries+=top.queries+bottom.queries;scene.visits+=top.visits+bottom.visits;raster.fragments=first.fragments+second.fragments;if(scene.queries>131072||scene.visits>16777216||raster.fragments>8192)throw new InvalidOperationException("103 aggregate CPU budget before GPU submission");result.totalMs=Elapsed103(clock);return result;
  }
 }
}
