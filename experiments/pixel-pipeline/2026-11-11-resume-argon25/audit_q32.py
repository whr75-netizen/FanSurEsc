"""Read source and saved metadata only; no Editor/device/driver interaction."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;G=H/'face32';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 specs={
 'initial335':('Assets/EUnityValidation01/MinimalRestore335/Shaders/LegacySignals335.shader',['Blend One Zero','struct O335','O335 Eye333Fragment']),
 'initial502':('Assets/EUnityValidation01/HeadRegion502/Shaders/Legacy502.shader',['Blend One Zero','_FORWARD_PLUS','O335 Eye333Fragment']),
 'correction335':('Assets/EUnityValidation01/MinimalRestore335/Shaders/RestoreStyle335.compute',['bool ShadeNeighbour335','bool uncertain=','p+2*back','float old=cls.x','_ShadeClassOut335[p]=cls']),
 'routing502':('Assets/EUnityValidation01/HeadRegion502/Runtime/HeadRegion502.cs',['public static bool Draw','!Ready || current != f || renderer == 0','ShaderNames[kind]','cmd.DrawMesh(pieces']),
 'pipeline367':('Assets/EUnityValidation01/HeadLocal367/Runtime/FullFeature367.cs',['sealed class LegacySignals','cmd.SetComputeTextureParam(cs,k,"_ShadeClass335"','_ShadeCurvature335','_ShadeStride335','_ShadeApply335']),
 'region502':('Assets/EUnityValidation01/HeadRegion502/Shaders/Region502.hlsl',['Varyings Region502Vertex','void Region502Clip','_Region502Mask.Load'])}
 rows={}
 for key,(name,needles)in specs.items():
  p=R/name;s=p.read_text(encoding='utf-8-sig');rows[key]={'path':name,'SHA256':sha(p),'lines':[{'line':i,'text':line.strip()}for i,line in enumerate(s.splitlines(),1)if any(t in line for t in needles)]}
 run=json.loads(next((H/'producer/support/surface27/pigment-run').glob('STATE113-*-finished.json')).read_text());packet=Path(run['sequencePackets'][0]['output']);raw=packet/'RAW_MANIFEST.json';m=json.loads(raw.read_text());assert sha(raw)==(packet/'RAW_COMPLETE76.marker').read_text().strip()
 planeNames=[p['file']for p in m['planes']];qnames=[p for p in planeNames if any(t in p.lower()for t in ['class','qprime','initial-q'])];route=[k for k in m if'502'in k.lower()or'headregion'in k.lower()]
 result={
 'source':rows,
 'QprimeEquation':'Qprime=proposal iff apply && ShadeRole(meta) && abs(Q0-proposal)>=0.01; otherwise Qprime=Q0. This assumes initial inputs/producer schema match.',
 'conditionalSchemaDefect':'Legacy502 outputs classifier=(binary shadow,role+1,depth,alpha), whereas ShadeBoundary reads classifier.y as continuous illumination. For supported roles3,7..14 Y>=4, threshold in[0,1], uncertainty radius<=0.1: proposal cannot change under binary labels.',
 'conditionalRoute':'FullFeature367 LegacySignals calls HeadRegion502.Draw(kind4). Ready/current renderer1 or2 uses Legacy502; renderer0 or inactive route falls through. Present live route was not queried.',
 'haloContract':{'logicalInitialTransition':1,'logicalQprimeCentre':2,'logicalQprimeTransition':3,'generalOnePass':'2*ShadeStride + queryRadius','nativeStride2LogicalQuery2':6},
 'MRTReview':{'blendOneZero':True,'QMeta31Stage':'initial Q only','QMeta31OwnerChannel':'constant0, not a substitute for original per-surface/feature owner','missingForQprime':['same shader/geometry/clip/alpha/sample domain','actual initial Q and continuous Y','original owner/depth/normal/UV membership used by ShadeNeighbour','matching light/keyword/mode/level/world-pixel inputs'],'formatCapabilities':'ReadbackPreflight32 review checks render/load-store/readpixels and exact target format; not executed'},
 'savedPacket':{'sourceId':m['sourceId'],'frame':m['frameIndex'],'manifestSHA256':sha(raw),'initialProposalQprimePlaneNames':qnames,'routeFlagKeys':route,'realFrameDeltaMeasured':False},
 'callbackReview':{'foundGap':'producer end barrier does not cover later observer readbacks','reviewPatch':'UNAPPLIED_ConsumerLifetime32.patch','policy':'all public consumers go through a bounded opaque-ticket lease; copy native data during callback; release lease after callback; producer+consumer both required before RT release','exitDispatch':'callback only queues; explicit observer pump validates creating-thread identity before Editor actions','remaining':['actual GPU callback/exit lifetime','actual constructor/pump placement on Editor main thread','domain/assembly reload and device error','current private URP job ownership','actual shader import/MRT variants/raster-lighting parity']},
 'UnityGPUCalls':0,'AssetsWrites':0,'patchesApplied':False}
 G.mkdir(exist_ok=True);(G/'SOURCE_AUDIT32.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'sourceFiles':len(rows),'savedQPairAvailable':bool(qnames),'currentRouteObserved':False,'UnityGPUCalls':0}))
if __name__=='__main__':main()
