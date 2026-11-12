from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face62'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for n in['capture','shaders','build','import']:(G/n).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 old=(H/'face60/shaders/SourceNativeHull60.compute').read_text();c=old.replace('_SelectedSource48,_FeatureDomain49;','_SelectedSource48,_FeatureDomain49,_ChildVisible62;')
 a='bool source=stroke.a==1&&all(stroke.rgb==_Ink41.rgb)&&proof.x>0&&all(proof.yz>=0)&&all(proof.yz<=1)&&proof.w>=1'
 b='bool source=stroke.a==1&&all(stroke.rgb==_Ink41.rgb)&&proof.x>0&&proof.w>=1'
 assert c.count(a)==1;c=c.replace(a,b)
 needle='bool use=source&&style&&visible;'
 layer='''int2 hp62=local+_HeadTextureOrigin41;bool inHead62=all(hp62>=0)&&all(hp62<int2(480,272));float4 cv62=inHead62?_ChildVisible62.Load(int3(hp62,0)):0;float4 originalOwner=_NativeOwner47.Load(int3(p,0));float kind62=round(cv62.x);float role62=kind62==1?5:(kind62>=2&&kind62<=4)?2:(kind62==5||kind62==7)?7:0;float4 parentDomain62=inside?_FeatureDomain49.Load(int3(q,0)):0;bool child62=all(isfinite(cv62))&&cv62.x==kind62&&role62>0&&cv62.y>0&&cv62.z>0&&parentDomain62.x>=.5&&cell.z==1&&originalOwner.x==role62;bool blocked62=source&&style&&visible&&child62;bool use=source&&style&&visible&&!child62;'''
 assert c.count(needle)==1;c=c.replace(needle,layer);needle='float4 originalOwner=_NativeOwner47.Load(int3(p,0));float4 originalUV='
 assert c.count(needle)==1;c=c.replace(needle,'float4 originalUV=');c+='\n'
 needle='_OwnerReceipts47[local]=originalOwner;'
 assert c.count(needle)==1;c=c.replace(needle,'_OwnerReceipts47[local+int2(4*_Size41.x,0)]=float4(cv62.xyz,blocked62?1:0);'+needle)
 assert'while('not in c and'for('not in c;(G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 s=(H/'face61/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face61\\capture','resume-20261111\\face62\\capture').replace('face61-width-calibration-','face62-parent-outline-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('readonly RTHandle[] Fields=new RTHandle[27]','readonly RTHandle[] Fields=new RTHandle[28]')
 rep('Fields[15]=Target(4*QROI.width,QROI.height,uav:true);','Fields[15]=Target(5*QROI.width,QROI.height,uav:true);')
 rep('Fields[26]=Target(8*QROI.width,2*QROI.height);','Fields[26]=Target(8*QROI.width,2*QROI.height);Fields[27]=Target(8*QROI.width,QROI.height);')
 rep('Fields[16],Fields[17],Fields[26]}','Fields[16],Fields[17],Fields[26],Fields[27]}')
 rep('T("_FeatureDomain49",main41.domain);','T("_FeatureDomain49",main41.domain);T("_ChildVisible62",eye.visible);')
 rep('if(role48<1||role48>16)throw new InvalidOperationException("48 registered source role missing");','if(role48!=4)throw new InvalidOperationException("62 parent-outline policy requires confirmed face source role4");')
 a='cmd.CopyTexture(Fields[14].rt,0,0,0,0,2*QROI.width,2*QROI.height,Fields[26].rt,0,0,c61*2*QROI.width,0);'
 rep(a,a+'cmd.CopyTexture(Fields[12].rt,0,0,15*QROI.width,0,QROI.width,QROI.height,Fields[27].rt,0,0,c61*2*QROI.width,0);cmd.CopyTexture(Fields[15].rt,0,0,4*QROI.width,0,QROI.width,QROI.height,Fields[27].rt,0,0,(c61*2+1)*QROI.width,0);')
 rep('new[]{20,21,22,23,24,25,26}','new[]{20,21,22,23,24,25,26,27}')
 rep('c61==26?"widthCompositeAtlas61":"widthCaseField"+c61','c61==26?"widthCompositeAtlas61":c61==27?"widthOwnerAndLayerAtlas62":"widthCaseField"+c61')
 rep('["artPolicyAdopted"]=false','["artPolicyAdopted"]=false,["parentLayer62"]="Face outline decoration below visible same-actor iris/sclera/lid only if current native owner role confirms the child; canvas and actual hair/world not bypassed",["perCaseFinalOwnerCaptured62"]=true,["UVSamplerContract62"]="finite raw source UV; wrap/clamp belongs to original material sampler, not clamped in resolver"')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/parent62.dll')
 prefix=(H/'face49/capture/RUN.cs.txt').read_text();prefix=prefix[:prefix.index('// Prepared helper only')];imp=prefix+(H/'UpdateOwned62.cs.txt').read_text();(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/update62.dll')
 imported=json.loads((H/'face60/import/COMPLETE.json').read_text());guid=next(x['guid']for x in imported['imported']if x['path'].endswith('.compute'))
 (G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':sha(H/'face60/shaders/SourceNativeHull60.compute'),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':guid},indent=2))
 (G/'CPU_PREPARED62.json').write_text(json.dumps({'fullExternalCSharp9Compiled':True,'sameExistingOwnedComputeGUID':guid,'computeLoops':0,'newStructuredBuffers':0,'extraRTOver61':1,'extraRTBytesAt28x28':100352,'scales':[0,1,8,32],'sameFrameChildRoleReceiptRequired':True,'defaultSourceWidthUnchanged':True,'product77Changed':False,'GPUExecuted':False,'captureSHA256':sha(G/'capture/RUN.cs.txt')},indent=2));print((G/'CPU_PREPARED62.json').read_text())
if __name__=='__main__':main()
