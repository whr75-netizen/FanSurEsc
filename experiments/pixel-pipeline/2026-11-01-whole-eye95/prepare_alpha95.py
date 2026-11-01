from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'alpha';assert not OUT.exists();OUT.mkdir()
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
s=(ROOT/'visibility-backing91/ReadAlpha91.cs').read_text().replace('ROOT91',str(HERE)).replace('ALPHA_REQUEST91.json','ALPHA_REQUEST95.json').replace('ALPHA_SOURCE91.json','ALPHA_SOURCE95.json').replace('request["queries"].Count>256','request["queries"].Count>32768')
start=s.index('   using(var s=new SerializedObject(surface))');end=s.index('string modelSHA;',start)
s=s[:start]+'''   var srcs=new Dictionary<int,SkinnedMeshRenderer>();using(var so=new SerializedObject(surface))for(int i=0;i<so.FindProperty("source").arraySize;i++)srcs[i]=so.FindProperty("source").GetArrayElementAtIndex(i).objectReferenceValue as SkinnedMeshRenderer;
   '''+s[end:]
s=s.replace('var sources=new Obj58();var rows=new Arr58();long reads=0;','var sources=new Obj58();var rows=new Arr58();long reads=0;var footprintBounds=new Dictionary<string,Vector2>();')
s=s.replace('int part=(int)q["sourceSubMesh"];var mat=src.sharedMaterials[part];','int slot=(int)q["rendererSlot"],part=(int)q["sourceSubMesh"];src=srcs[slot];if(!src)throw new InvalidOperationException("Source slot missing");var mat=src.sharedMaterials[part];')
s=s.replace('string keyPart=part.ToString();','string keyPart=slot+"-"+part;').replace('["subMesh"]=part,["material"]','["rendererSlot"]=slot,["subMesh"]=part,["material"]')
start=s.index('float lo=1,hi=0;var corners=');end=s.index('rows.Add(',start)
s=s[:start]+'''string footprint=keyPart+":"+x+":"+y;float lo,hi;if(footprintBounds.TryGetValue(footprint,out var prior)){lo=prior.x;hi=prior.y;}else{lo=1;hi=0;for(int j=0;j<2;j++)for(int i=0;i<2;i++){float a=texture.GetPixel(Wrap(x+i,texture.width,texture.wrapModeU),Wrap(y+j,texture.height,texture.wrapModeV)).a*factor;lo=Mathf.Min(lo,a);hi=Mathf.Max(hi,a);reads++;}footprintBounds.Add(footprint,new Vector2(lo,hi));}if(reads>32768)throw new InvalidOperationException("Unique alpha footprint read budget exceeded");'''+s[end:]
s=s.replace('["alphaCorners"]=corners,','["rendererSlot"]=slot,["footprintKey"]=footprint,').replace(',["CPUbilinearDiagnosticOnly"]=bilinear','')
s=s.replace('report["pixelGetterCalls"]=reads;','report["pixelGetterCalls"]=reads;report["uniqueFootprints"]=footprintBounds.Count;')
(OUT/'ReadAlpha95.cs').write_text(s,encoding='utf-8')
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/'ReadAlpha95.cs'],OUT/'RUN_ReadAlpha95.cs.txt')
relay=(HERE/'capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','ReadAlpha95')");(OUT/'relay95.py').write_text(relay,encoding='utf-8')
print('Prepared read-only original material alpha bounds; cache exact four-texel footprints, no guessed transparency.')
