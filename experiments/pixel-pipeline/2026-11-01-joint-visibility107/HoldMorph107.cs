using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

// Observer stimuli only. Algorithm receives no Close value or test-stage flag.
public sealed class HoldMorph107:IDisposable{
 readonly NativePlayer395 n;readonly SkinnedMeshRenderer source;readonly int morph;readonly float previous,desired;readonly Action hook;
 readonly UnityEngine.Mesh expected;readonly List<Vector3> wanted=new List<Vector3>(),actual=new List<Vector3>();bool disposed;int waits;
 public bool Restored{get;private set;}public float Error{get;private set;}public Obj58 Report{get;private set;}
 void Apply(){if(source)source.SetBlendShapeWeight(morph,desired);}
 public HoldMorph107(NativePlayer395 native,string path,float value){desired=value;if(value<0||value>100)throw new ArgumentOutOfRangeException(nameof(value));n=native;source=n.host.main.motion.surface.source[1];morph=source.sharedMesh.GetBlendShapeIndex("Fcl_EYE_Close");if(morph<0)throw new InvalidOperationException("106 supported Close source missing");previous=source.GetBlendShapeWeight(morph);hook=n.host.afterPose;CreateOnly73.Text(Path.Combine(path,"CLOSED_MOTION_BEFORE106.json"),new Obj58{["morph"]=morph,["value"]=previous,["sourceId"]=source.GetEntityId().ToString(),["hookPresent"]=hook!=null}.ToString());expected=new UnityEngine.Mesh{name="106 owned closed motion reference",hideFlags=HideFlags.DontSave};n.host.afterPose+=Apply;}
 public bool Ready(){if(disposed||!source||source.GetBlendShapeWeight(morph)!=desired)return false;source.BakeMesh(expected,true);expected.GetVertices(wanted);var filter=n.host.head.motion.surface.outputs[1];filter.sharedMesh.GetVertices(actual);if(wanted.Count!=actual.Count)throw new InvalidOperationException("106 closed motion evaluated topology mismatch");var map=filter.transform.worldToLocalMatrix*source.localToWorldMatrix;Error=0;for(int i=0;i<wanted.Count;i++)Error=Mathf.Max(Error,(map.MultiplyPoint3x4(wanted[i])-actual[i]).magnitude);if(Error<=2e-6f){waits=0;return true;}if(++waits>12)throw new InvalidOperationException("106 evaluated Close motion source mismatch; no timeout extension");return false;}
 public void Dispose(){if(disposed)return;disposed=true;var errors=new Arr58();try{if(!n||!n.host||!source)throw new InvalidOperationException("106 borrowed morph/hook owner lost");n.host.afterPose-=Apply;if(n.host.afterPose!=hook)throw new InvalidOperationException("106 borrowed hook changed");source.SetBlendShapeWeight(morph,previous);}catch(Exception e){errors.Add(e.ToString());}if(expected)UnityEngine.Object.DestroyImmediate(expected);Restored=errors.Count==0&&source&&source.GetBlendShapeWeight(morph)==previous;Report=new Obj58{["restored"]=Restored,["errors"]=errors,["ownedReferenceDisposed"]=!expected};}
}

