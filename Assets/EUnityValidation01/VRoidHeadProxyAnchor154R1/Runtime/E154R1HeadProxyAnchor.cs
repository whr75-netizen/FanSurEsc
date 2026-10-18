using System;using UnityEngine;
[DisallowMultipleComponent]
public sealed class E154R1HeadProxyAnchor:MonoBehaviour{
 public Transform head;public SkinnedMeshRenderer hair;
 public Matrix4x4 neutralHeadToWorld=Matrix4x4.identity,neutralHairToWorld=Matrix4x4.identity;
 public bool ready;public float lastActive;public Matrix4x4 lastProxyToWorld=Matrix4x4.identity;
 MaterialPropertyBlock block;
 public void Initialize(Transform headBone,SkinnedMeshRenderer hairRenderer){head=headBone;hair=hairRenderer;neutralHeadToWorld=head.localToWorldMatrix;neutralHairToWorld=hair.localToWorldMatrix;ready=true;Apply();}
 public void Apply(){if(!ready||head==null||hair==null)return;var hw=head.localToWorldMatrix;float delta=0;for(int i=0;i<16;i++)delta=Mathf.Max(delta,Mathf.Abs(hw[i]-neutralHeadToWorld[i]));lastActive=delta<=1e-6f?0:1;lastProxyToWorld=lastActive==0?neutralHairToWorld:hw*neutralHeadToWorld.inverse*neutralHairToWorld;var inv=lastProxyToWorld.inverse;block??=new MaterialPropertyBlock();var mats=hair.sharedMaterials;for(int i=0;i<mats.Length;i++){if(!mats[i]||!mats[i].HasProperty("_E154AnchorActive"))continue;block.Clear();hair.GetPropertyBlock(block,i);block.SetFloat("_E154AnchorActive",lastActive);block.SetMatrix("_E154WorldToProxy",inv);block.SetMatrix("_E154ProxyNormalToWorld",inv.transpose);hair.SetPropertyBlock(block,i);}}
 void LateUpdate(){if(Application.isPlaying){hair.forceMatrixRecalculationPerRender=true;Apply();}}
}
