"""Compile a read-only final check with an explicit original backup path."""
from pathlib import Path
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent

def main():
 source=H/'face99/long960';target=H/'face99/final-review99B';folder=target/'post/final';folder.mkdir(parents=True,exist_ok=True);assert not(folder/'REQUEST.json').exists()
 s=(source/'post/final/RUN.cs.txt').read_text();old='const string Root=@"'+str(source/'post')+'";';new='const string Root=@"'+str(target/'post')+'";';assert s.count(old)==1;s=s.replace(old,new);backup=str(source/'capture/INPUT_BEFORE.json');assert s.count(backup)==1 and(source/'capture/INPUT_BEFORE.json').is_file();p=folder/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,H/'face99/build/final-review99B.dll');print('Read-only final command compiled; original backup path retained; no Unity execution')
if __name__=='__main__':main()
