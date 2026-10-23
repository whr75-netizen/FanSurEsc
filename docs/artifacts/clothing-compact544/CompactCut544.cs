using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
// Algebraic elimination of strict fixed labels in the existing cut objective.
// It changes neither the area input nor the span groups nor any design weight.
public static class CompactCut544
{
 public static bool[] Select(float[] areas,int width,int height,List<int[]> groups)
 {
  var held=new bool[areas.Length];if(groups!=null)foreach(var g in groups)foreach(int i in g)held[i]=true;
  var map=new int[areas.Length];var output=new bool[areas.Length];int count=0;
  for(int i=0;i<areas.Length;i++)
  {
   int x=i%width,y=i/width;bool border=x==0||y==0||x==width-1||y==height-1;
   if(!held[i]&&(border||areas[i]==0||areas[i]==1)){map[i]=-1;output[i]=!border&&areas[i]==1;}else map[i]=count++;
  }
  int source=count,sink=count+1;var flow=new Cut(count+2);
  void Pair(int i,int j,float weight)
  {
   int a=map[i],b=map[j];if(a>=0&&b>=0)flow.Link(a,b,weight);
   else if(a>=0){if(output[j])flow.Add(source,a,weight);else flow.Add(a,sink,weight);}
   else if(b>=0){if(output[i])flow.Add(source,b,weight);else flow.Add(b,sink,weight);}
  }
  for(int y=0;y<height;y++)for(int x=0;x<width;x++)
  {
   int i=y*width+x,v=map[i];if(v>=0){flow.Add(source,v,areas[i]);flow.Add(v,sink,x==0||y==0||x==width-1||y==height-1?100000:1-areas[i]);}
   if(x+1<width)Pair(i,i+1,HeadRegion502.BoundaryCost*.58578644f);
   if(y+1<height)Pair(i,i+width,HeadRegion502.BoundaryCost*.58578644f);
   if(y+1<height&&x+1<width)Pair(i,i+width+1,HeadRegion502.BoundaryCost*.29289322f);
   if(y+1<height&&x>0)Pair(i,i+width-1,HeadRegion502.BoundaryCost*.29289322f);
  }
  if(groups!=null)foreach(var g in groups)for(int j=1;j<g.Length;j++)flow.Link(map[g[0]],map[g[j]],100000);
  var labels=flow.Solve(source,sink);for(int i=0;i<map.Length;i++)if(map[i]>=0)output[i]=labels[map[i]];return output;
 }
 sealed class Cut
 {
  sealed class E{public int to,reverse;public float capacity;}
  readonly List<E>[] graph;readonly int[] level,cursor;
  public Cut(int n){graph=Enumerable.Range(0,n).Select(_=>new List<E>()).ToArray();level=new int[n];cursor=new int[n];}
  public void Add(int a,int b,float c){var e=new E{to=b,reverse=graph[b].Count,capacity=c};var r=new E{to=a,reverse=graph[a].Count};graph[a].Add(e);graph[b].Add(r);}
  public void Link(int a,int b,float c){Add(a,b,c);Add(b,a,c);}
  float Send(int at,int sink,float value){if(at==sink)return value;for(;cursor[at]<graph[at].Count;cursor[at]++){var e=graph[at][cursor[at]];if(e.capacity<=1e-7f||level[e.to]!=level[at]+1)continue;float sent=Send(e.to,sink,Mathf.Min(value,e.capacity));if(sent<=1e-7f)continue;e.capacity-=sent;graph[e.to][e.reverse].capacity+=sent;return sent;}return 0;}
  bool Levels(int source,int sink){Array.Fill(level,-1);var q=new Queue<int>();level[source]=0;q.Enqueue(source);while(q.Count>0){int a=q.Dequeue();foreach(var e in graph[a])if(e.capacity>1e-7f&&level[e.to]<0){level[e.to]=level[a]+1;q.Enqueue(e.to);}}return level[sink]>=0;}
  public bool[] Solve(int source,int sink){while(Levels(source,sink)){Array.Clear(cursor,0,cursor.Length);while(Send(source,sink,float.PositiveInfinity)>1e-7f){}}return level.Select(x=>x>=0).ToArray();}
 }
}
