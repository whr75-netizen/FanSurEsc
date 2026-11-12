from pathlib import Path
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face96/alphaVerified/final'
COMMAND=r'''
internal class CommandScript:IRunCommand {
 const string Root=@@ROOT@@;const string Input=@@INPUT@@;
 public void Execute(ExecutionResult result){
  if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("96 stable Edit required for borrowed source CPU read");
  var doc=Json40.Parse(File.ReadAllText(Path.Combine(Input,"ACTOR_MATERIALS96.json")));var all=Resources.FindObjectsOfTypeAll<Texture2D>();var rows=new Arr40();
  foreach(var old in doc["textures"]){
   int index=(int)old["index"],width=(int)old["width"],height=(int)old["height"];string image=(string)old["imageHash"],name=(string)old["name"],asset=(string)old["asset"];
   var t=all.FirstOrDefault(v=>v&&v.width==width&&v.height==height&&v.name==name&&v.imageContentsHash.ToString()==image&&AssetDatabase.GetAssetPath(v)==asset);if(!t||!t.isReadable||t.updateCount!=(uint)(int)old["updateCount"]||width*height>4194304)throw new InvalidOperationException("96 exact readable original texture absent/changed");
   int stride=t.format==TextureFormat.RGB24?3:4;if(!(t.format==TextureFormat.ARGB32||t.format==TextureFormat.RGBA32||t.format==TextureFormat.BGRA32||t.format==TextureFormat.RGB24))throw new InvalidOperationException("96 unsupported CPU storage");var data=t.GetPixelData<byte>(0);int channel=AlphaChannel96.Find(t,data,stride);string filename="validated-alpha96-"+index+".a8";int n=checked(width*height);
   using(var f=new FileStream(Path.Combine(Input,filename),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){var chunk=new byte[32768];for(int at=0;at<n;){int count=Math.Min(chunk.Length,n-at);for(int k=0;k<count;k++)chunk[k]=channel<0?(byte)255:data[stride*(at+k)+channel];f.Write(chunk,0,count);at+=count;}f.Flush(true);}
   if(t.imageContentsHash.ToString()!=image||t.updateCount!=(uint)(int)old["updateCount"])throw new InvalidOperationException("96 original texture changed during CPU read");rows.Add(new Obj40{["index"]=index,["alphaFile"]=filename,["alphaBytes"]=n,["alphaByteOffset"]=channel,["sourceImageHash"]=image,["publicGetPixelAlphaVerified"]=true});
  }
  CreateOnly40.Text(Path.Combine(Input,"VALIDATED_ALPHA96.json"),new Obj40{["sourceId"]=doc["sourceId"],["textures"]=rows,["GPUReadback"]=false,["originalTextureChanged"]=false}.ToString());CreateOnly40.Text(Path.Combine(Root,"COMPLETE.json"),new Obj40{["utc"]=DateTime.UtcNow.ToString("O"),["textures"]=rows.Count,["publicAlphaVerified"]=true,["PlayOrGPU"]=false}.ToString());result.Log("96 original alpha CPU channel calibrated; borrowed texture unchanged");
 }
}
}
'''
def main():
 G.mkdir(parents=True,exist_ok=True);assert not(G/'REQUEST.json').exists();s=(H/'face96/probe1/final/RUN.cs.txt').read_text();a=s.index('internal class CommandScript:IRunCommand');s=s[:a];root=str(G.resolve());inp=str((H/'face96/probe1/capture').resolve());command=COMMAND.replace('@@ROOT@@','@"'+root+'"').replace('@@INPUT@@','@"'+inp+'"');s+=command+'\n'+(H/'AlphaChannel96.cs.txt').read_text();p=G/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,H/'face96/build/alpha96.dll');print('96 read-only CPU alpha calibration compiled')
if __name__=='__main__':main()
