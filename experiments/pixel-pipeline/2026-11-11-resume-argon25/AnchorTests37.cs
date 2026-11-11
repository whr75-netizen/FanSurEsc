using System;using System.Collections.Generic;using System.Text.Json;
class AnchorTests37 {
 static List<string> checks=new List<string>();static void Check(bool ok,string name){if(!ok)throw new Exception(name);checks.Add(name);}static bool Same(double[]a,double[]b){for(int i=0;i<a.Length;i++)if(Math.Abs(a[i]-b[i])>1e-12)return false;return true;}
 static void Reject(Action a,string name){try{a();}catch(ArgumentException){checks.Add(name);return;}throw new Exception(name);}
 static void Main(){
  var t=new[]{new double[]{0,0,0},new double[]{2,0,0},new double[]{0,2,0}};var identity=new double[]{1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};var b=new double[]{.5,.25,.25};Check(Same(SourceAnchorMath37.World(t,b,identity),new double[]{.5,.5,0}),"interior source barycentric point");
  for(int i=0;i<3;i++){var w=new double[3];w[i]=1;Check(Same(SourceAnchorMath37.World(t,w,identity),t[i]),"source corner "+i);}
  var moved=(double[])identity.Clone();moved[12]=3;moved[13]=-2;moved[14]=7;Check(Same(SourceAnchorMath37.World(t,b,moved),new double[]{3.5,-1.5,7}),"world translation follows source carrier");
  var rotate=new double[]{0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1};Check(Same(SourceAnchorMath37.World(t,b,rotate),new double[]{-.5,.5,0}),"world rotation follows source carrier");
  var stretch=(double[])identity.Clone();stretch[0]=2;stretch[5]=3;Check(Same(SourceAnchorMath37.World(t,b,stretch),new double[]{1,1.5,0}),"nonuniform affine scale");
  var deformed=new[]{new double[]{0,0,1},new double[]{2,0,3},new double[]{0,2,5}};Check(Same(SourceAnchorMath37.World(deformed,b,identity),new double[]{.5,.5,2.5}),"evaluated deformation updates source anchor");
  for(int phase=0;phase<=8;phase++){var m=(double[])identity.Clone();m[12]=phase/8.0;var p=SourceAnchorMath37.World(t,b,m);Check(Math.Abs(p[0]-(.5+phase/8.0))<1e-12,"continuous world translation phase "+phase);}
  Reject(()=>SourceAnchorMath37.World(t,new double[]{.5,.5,.5},identity),"invalid barycentric sum");Reject(()=>SourceAnchorMath37.World(t,new double[]{-1,1,1},identity),"outside triangle not clamped");Reject(()=>SourceAnchorMath37.World(t,new double[]{Double.NaN,0,1},identity),"nonfinite anchor rejected");var bad=(double[])identity.Clone();bad[3]=.5;Reject(()=>SourceAnchorMath37.World(t,b,bad),"perspective matrix is not a local transform");Reject(()=>SourceAnchorMath37.World(new[]{new double[]{0,Double.NaN,0},t[1],t[2]},b,identity),"invalid evaluated source rejected");
  Console.WriteLine(JsonSerializer.Serialize(new{checks=checks.Count,passed=checks,UnityGPUCalls=0}));
 }
}
