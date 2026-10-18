using System;using System.Collections.Generic;using UnityEngine;
[Serializable]public class Walk257Inputs{public string status,error,clip;public float clipLength;public List<Walk257Frame>frames=new();}
[Serializable]public class Walk257Frame{public int index;public float frame;public Vector3 sourceOrigin;public Matrix4x4 head,backingToWorld;public Vector3[]anchors;public Walk257Provider[]providers;}
[Serializable]public class Walk257Provider{public int role;public float eyeEnabled,apertureEnabled;public Vector4 scales,apertureScale,headAnchor0,headAnchor1,eyeAnchor0,eyeAnchor1,centre0,centre1;public Matrix4x4 toHead,toWorld;}
