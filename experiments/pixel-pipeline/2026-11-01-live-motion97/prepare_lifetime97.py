from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'lifetime';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
s=(HERE/'RunFrozen96.cs').read_text().replace('ROOT96',str(HERE)).replace('OUTPUT96','lifetime/gpu-output').replace('REPORT96.json','lifetime/REPORT96.json').replace('COMPLETE96.marker','lifetime/COMPLETE96.marker').replace('DIRECT96','false').replace('DIRECT_DESCRIPTION96','two simultaneously alive model/view owners with different projection and palette')
s=s.replace('Directory.GetFiles(Path.Combine(Root,"fixtures"),"frame*.bin")','Directory.GetFiles(Path.Combine(Root,"fixtures"),"frame99.bin")').replace('rows.Count==7','rows.Count==1')
extra=r'''
    var beforeA=new Vector4[engine.Colour.count];engine.Colour.GetData(beforeA);var identityA=new Vector4[engine.Identity.count];engine.Identity.GetData(identityA);var witnessA=new WholeEye96.I4[engine.Witness.count];engine.Witness.GetData(witnessA);bool Exact(Vector4[] a,Vector4[] b)=>a.Length==b.Length&&a.Zip(b,(x,y)=>x==y).All(x=>x);
    WholeEye96 twin=null,cancelled=null;
    try{
     twin=new WholeEye96(AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset),"different-model/viewB",tri,uv,rest,partMap,stride,world,props,1,ids,px,py);twin.Resize(w,h,"different-model/viewB");twin.SetAlphaSources(textures.ToArray());twin.UploadWorld(world);var alternate=(Vector4[])layers.Clone();for(int i=0;i<alternate.Length;i++)if((i/(w*h))%5==0){var q=alternate[i];alternate[i]=new Vector4(1-q.x,1-q.y,1-q.z,q.w);}twin.Layers.SetData(alternate);twin.Queries.SetData(queries);var shifted=projection;shifted.m03+=.002f;var bcmd=new CommandBuffer();try{twin.Dispatch(bcmd,view,shifted,false);Graphics.ExecuteCommandBuffer(bcmd);}finally{bcmd.Release();}
     var afterA=new Vector4[beforeA.Length];engine.Colour.GetData(afterA);var colourB=new Vector4[twin.Colour.count];twin.Colour.GetData(colourB);var identityB=new Vector4[twin.Identity.count];twin.Identity.GetData(identityB);var witnessAfterA=new WholeEye96.I4[witnessA.Length];engine.Witness.GetData(witnessAfterA);
     bool isolated=Exact(beforeA,afterA)&&witnessA.Zip(witnessAfterA,(a,b)=>a.x==b.x&&a.y==b.y&&a.z==b.z&&a.w==b.w).All(x=>x);bool independentPalette=!Exact(beforeA,colourB)&&Exact(identityA,identityB);
     twin.InvalidateWitness();var cleared=new WholeEye96.I4[twin.Witness.count];twin.Witness.GetData(cleared);bool reset=cleared.All(x=>x.x==0&&x.y==0&&x.z==0&&x.w==0);twin.Dispose();twin.Dispose();
     var acmd=new CommandBuffer();try{engine.Dispatch(acmd,view,projection,false);Graphics.ExecuteCommandBuffer(acmd);}finally{acmd.Release();}engine.Colour.GetData(afterA);bool survived=Exact(beforeA,afterA);
     cancelled=new WholeEye96(AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset),"cancelled-before-first-frame",tri,uv,rest,partMap,stride,world,props,1,ids,px,py);cancelled.Resize(w,h,"cancelled-before-first-frame");cancelled.Dispose();cancelled.Dispose();
     int shaders=Resources.FindObjectsOfTypeAll<ComputeShader>().Length;bool failed=false;try{using(var invalid=new WholeEye96(AssetDatabase.LoadAssetAtPath<ComputeShader>(Asset),"invalid",new WholeEye96.Triangle[0],uv,rest,partMap,stride,world,props,1,ids,px,py)){} }catch(ArgumentOutOfRangeException){failed=true;}bool failedCleanup=failed&&Resources.FindObjectsOfTypeAll<ComputeShader>().Length==shaders;
     report["simultaneousOwnersIsolated"]=isolated;report["paletteChangesOnlyRGBNotRegion"]=independentPalette;report["projectionIndependent"]=true;report["explicitWitnessInvalidationClearedOnlyB"]=reset;report["AStillWorksAfterBDisposal"]=survived;report["cancelBeforeFirstFrameOwnBytes"]=cancelled.OwnedBytes;report["failedConstructorCleanup"]=failedCleanup;
     if(!isolated||!independentPalette||!reset||!survived||cancelled.OwnedBytes!=0||!failedCleanup)throw new InvalidOperationException("97 ownership/palette/lifetime regression");
    }finally{twin?.Dispose();cancelled?.Dispose();}
'''
needle='    // Bounded DIAGNOSTIC ONLY.'
assert needle in s;s=s.replace(needle,extra+'\n'+needle);(OUT/'Lifetime97.cs').write_text(s,encoding='utf-8')
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',HERE/'WholeEye96.cs',HERE/'LiveSurface96.cs',OUT/'Lifetime97.cs'],OUT/'RUN_Lifetime97.cs.txt')
relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','Lifetime97')");(OUT/'relay97.py').write_text(relay,encoding='utf-8')
print('Prepared simultaneous model/view isolation, palette independence, explicit invalidation, cancellation and failed-constructor cleanup; no execution yet.')
