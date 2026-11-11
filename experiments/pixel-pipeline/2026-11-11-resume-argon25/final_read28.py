"""One small read-only Editor receipt, without rendering or resource mutation."""
from pathlib import Path
import probe
def main():
 root=Path(__file__).resolve().parent/'face28/final-state';root.mkdir(exist_ok=True)
 assert not(root/'READ_REQUEST.json').exists(),'Inspect original read; no repeat'
 text=(probe.H/'ReadState.cs.txt').read_text(encoding='utf-8')
 text=text.replace('public string utc,version,project;','public long allocated,reserved,mono;public int renderTextures;public string utc,version,project;')
 text=text.replace('utc=DateTime.UtcNow.ToString("O"),','allocated=UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong(),reserved=UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong(),mono=UnityEngine.Profiling.Profiler.GetMonoUsedSizeLong(),renderTextures=Resources.FindObjectsOfTypeAll<RenderTexture>().Length,utc=DateTime.UtcNow.ToString("O"),')
 (root/'ReadState.cs.txt').write_text(text,encoding='utf-8');probe.H=root;probe.main()
if __name__=='__main__':main()
