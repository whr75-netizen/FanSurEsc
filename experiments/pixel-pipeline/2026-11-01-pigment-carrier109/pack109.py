"""NEW bounded raw archive; never moves/deletes/overwrites source packets."""
from pathlib import Path
import json,zipfile,hashlib
from native109 import H,R,read,sha

def main():
    assert not(H/'RAW109.zip').exists(),'Inspect existing archive instead of recreating it'
    rows=[];entry105=read(sorted((R/'closed-support105/direct').glob('STATE102-*'))[-1])['sequencePackets'];entry87=[x for x in read(sorted((R/'feature-audit86/run87').glob('STATE87*.json'))[-1])['sequencePackets']if x['testStage82']in ['walk','sweep','blink']]
    with zipfile.ZipFile(H/'RAW109.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for kind,entries in [('105',entry105),('87',entry87)]:
            for e in entries:
                p=Path(e['output']);m=read(p/'RAW_MANIFEST.json');assert m['frameIndex']==e['frame'];names=['RAW_MANIFEST.json','current-face105.mesh','canonical-layers.f32','canonical-visibility.f32']if kind=='105'else['RAW_MANIFEST.json','eye-evaluated.mesh']
                for name in names:
                    q=p/name;b=q.read_bytes();archive=kind+'/frame'+str(e['frame'])+'/'+name;z.writestr(archive,b);rows.append({'file':archive,'sourceId':m['sourceId'],'frame':e['frame'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    static=[('SOURCE_SURFACES52.npz',R/'whole-eye52/SOURCE_SURFACES52.npz'),('WHOLE_KEYFORM52.json',R/'whole-eye52/WHOLE_KEYFORM52.json'),('REGISTRATION89.json',R/'native-feature89/REGISTRATION89.json'),('SOURCE_FIXTURE88.json',R/'feature-layer88/SOURCE_FIXTURE88.json'),('SOURCE_CURVE105.json',R/'closed-support105/direct/SOURCE_CURVE105.json'),('SOURCE_AUDIT.json',Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json')),('image-9.png',Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\image-9.png'))];extra=[]
    (H/'inputs').mkdir(exist_ok=True)
    for name,p in static:
        q=H/'inputs'/name
        with q.open('xb')as f:f.write(p.read_bytes())
        assert sha(q)==sha(p);extra.append({'file':'inputs/'+name,'sha256':sha(p),'bytes':p.stat().st_size})
    index={'rawFiles':rows,'static':extra,'entries105':entry105,'entries87':entry87,'archiveSHA256':sha(H/'RAW109.zip'),'bytes':(H/'RAW109.zip').stat().st_size,'newUnityCalls':0}
    (H/'RAW_INPUT109_INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf8');print(json.dumps({'rawFiles':len(rows),'staticFiles':len(extra),'archiveBytes':index['bytes'],'archiveSHA256':index['archiveSHA256']}))
if __name__=='__main__':main()
