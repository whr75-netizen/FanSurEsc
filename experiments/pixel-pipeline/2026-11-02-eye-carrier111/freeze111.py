"""Select completed experiment INPUTS only; no native settings/auth/tool logs."""
from pathlib import Path
import json,hashlib,zipfile,shutil
from geometry111 import H,R,read,load,packet_list
from ray111 import NativeAlpha
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    records=[];states={};manifest=[];ids=[]
    for kind in['original','geometry']:
        state,paths=packet_list(kind);assert state['PlayExited']and not state.get('error')and not state.get('restorationError');fields=['PlayEntries','PlayExited','error','restorationError','beforeMemory','afterMemory','nativeComparisons72','optionsRestored','timeRestored','pipelineRestored','backgroundRestored','playerSettingsRunInBackgroundRestored','carrierSourceDisposed111','carrierNativeDisposed111','editInputRestoration82','motionRestoration82','globalRestoreErrors','sequencePackets'];states[kind]={k:state[k]for k in fields if k in state}
        for p in paths:
            m=read(p/'RAW_MANIFEST.json');data=(p/'RAW_MANIFEST.json').read_bytes();assert(p/'RAW_COMPLETE76.marker').read_text().strip()==sha(data);prefix=f'{kind}/frame{m["frameIndex"]}';records.append({'kind':kind,'frame':m['frameIndex'],'sourceId':m['sourceId'],'archivePrefix':prefix});ids.append(m['sourceId'])
    assert len(ids)==24 and len(set(ids))==24
    with zipfile.ZipFile(H/'RAW111.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for kind in['original','geometry']:
            _,paths=packet_list(kind);reg=paths[0].parent/'REGISTRATION_CURRENT102.json';blob=reg.read_bytes();name=kind+'/REGISTRATION_CURRENT102.json';z.writestr(name,blob);manifest.append({'file':name,'bytes':len(blob),'sha256':sha(blob)})
            for p in paths:
                m=read(p/'RAW_MANIFEST.json');prefix=f'{kind}/frame{m["frameIndex"]}'
                for f in sorted(p.iterdir()):
                    keep=f.name.startswith(('D-lid-','D-part1-','D-part2-','C-part1-','C-part2-','C-part3-','S4-'))or f.name in['RAW_MANIFEST.json','RAW_COMPLETE76.marker','SOURCE_GEOMETRY111.bin','SOURCE_TRANSFORMS111.json','dense-three-part-visibility.f32','carrier-three-part-visibility.f32','canonical-layers.f32','canonical-visibility.f32','H-product77-final.plane','L0-LIGHT.plane','curve-segments106.f32']
                    if not f.is_file()or not keep:continue
                    b=f.read_bytes();name=prefix+'/'+f.name;z.writestr(name,b);manifest.append({'file':name,'bytes':len(b),'sha256':sha(b)})
    (H/'CAPTURE_INDEX111.json').write_text(json.dumps({'packets':records,'states':states,'archive':'RAW111.zip','entries':manifest,'privateNativeSettingsAndRelayLibraryLogsExcluded':True},indent=2)+'\n')
    _,paths=packet_list();ctx=load(paths[0]);alpha=NativeAlpha(ctx);audit=read(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json'));out=H/'inputs';out.mkdir(exist_ok=False);images=[]
    for info in alpha.sources.values():
        mat=next(v for v in audit['materials']if v['image']['imageId']==info['imageIndex']);src=Path(mat['image']['file']);name=f'image-{info["imageIndex"]}.png';assert sha(src.read_bytes())==info['sha256'];shutil.copy2(src,out/name);images.append(info|{'file':name})
    (out/'ALPHA111.json').write_text(json.dumps({'images':images,'captureSourceIds':ids,'sourceModelVerifiedBeforeFreeze':True,'sampler':'recorded actual material mode/cutoff/wrap, original native texture alpha; GPU query validation recorded separately'},indent=2)+'\n')
    print(json.dumps({'capturedSources':24,'archiveEntries':len(manifest),'rawSelectedBytes':sum(v['bytes']for v in manifest),'zipBytes':(H/'RAW111.zip').stat().st_size,'alphaImages':len(images),'originalInputsUnchanged':True}))
if __name__=='__main__':main()
