using System;using System.Collections.Generic;using UnityEngine;using UnityEngine.LowLevel;using UnityEngine.PlayerLoop;
public static class Socket216Stage{
 sealed class Marker{}static Socket216View current;public static bool installed;public static string nativeStage="";
 static bool Insert(ref PlayerLoopSystem n){var a=n.subSystemList;if(a==null)return false;for(int i=0;i<a.Length;i++){if(a[i].type==typeof(PostLateUpdate.UpdateAllSkinnedMeshes)){var l=new List<PlayerLoopSystem>(a);l.Insert(i+1,new PlayerLoopSystem{type=typeof(Marker),updateDelegate=Render});n.subSystemList=l.ToArray();nativeStage=a[i].type.FullName;return true;}if(Insert(ref a[i])){n.subSystemList=a;return true;}}return false;}
 static void Strip(ref PlayerLoopSystem n){if(n.subSystemList==null)return;var l=new List<PlayerLoopSystem>();foreach(var a in n.subSystemList){if(a.type==typeof(Marker))continue;var b=a;Strip(ref b);l.Add(b);}n.subSystemList=l.ToArray();}
 public static void Install(Socket216View v){if(current&&current!=v)throw new Exception("H210 stage occupied");current=v;var l=PlayerLoop.GetCurrentPlayerLoop();Strip(ref l);if(!Insert(ref l))throw new Exception("Required native skin stage missing");PlayerLoop.SetPlayerLoop(l);installed=true;}
 static void Render(){if(current&&Application.isPlaying)current.Render();}
 public static void Remove(Socket216View v){if(current!=v)return;var l=PlayerLoop.GetCurrentPlayerLoop();Strip(ref l);PlayerLoop.SetPlayerLoop(l);current=null;installed=false;}
}
