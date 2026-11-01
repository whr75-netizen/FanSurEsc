"""Read only two prefab-linked original assets; no Unity/Play or interpolation."""
from pathlib import Path
import hashlib,json,re
import numpy as np
HERE=Path(__file__).resolve().parent
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 arrays={};metadata=[]
 for name,fmt,dtype in [('TemplateRGBA',4,np.uint8),('TemplateRole',20,'<f4')]:
  p=REPO/('Assets/EUnityValidation01/SocketTemplate216/Inputs/'+name+'.asset');raw=p.read_bytes();t=raw.decode('utf-8-sig');width=int(re.search(r'm_Width: (\d+)',t)[1]);height=int(re.search(r'm_Height: (\d+)',t)[1]);assert int(re.search(r'm_TextureFormat: (\d+)',t)[1])==fmt
  b=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',t)[1]);assert len(b)==int(re.search(r'm_CompleteImageSize: (\d+)',t)[1]);a=np.frombuffer(b,dtype).reshape(height,width,4).copy();arrays[name]=a
  metadata.append({'file':str(p.relative_to(REPO)),'SHA256':hashlib.sha256(raw).hexdigest(),'width':width,'height':height,'textureFormat':fmt,'encoding':'sRGB8 literal bytes'if fmt==4 else'linear float32 region/eye roles','coordinates':'CPU texture storage bottom-left, source pigment reference is top-left; y=271-topY'})
 np.savez_compressed(HERE/'TEMPLATE_REFERENCE100.npz',**arrays)
 (HERE/'TEMPLATE_REFERENCE100.json').write_text(json.dumps({'provenance':'current ValidatedPresentation399.prefab declared GUIDs, direct public field copied to head; on-disk source reference, not newly captured live binding proof','bindings':'TEMPLATE_BINDINGS100.json','runtimeExportIssue':'Template crops in100 used top-left reference bounds as bottom-left GetPixels coordinates; these raw crops are retained and not used as valid palette evidence. This offline original-asset reference repairs analysis, without mixing frames.','originalAssets':metadata},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Decoded original prefab Template RGBA/role reference without Unity or new frames')
if __name__=='__main__':main()
