from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;skin='--skin'in sys.argv;mode='ReadAlphaSkin95'if skin else'ReadAlpha95B';OUT=HERE/('alpha-skin-focus'if skin else'alpha-bounded');assert not OUT.exists();OUT.mkdir();chunks=OUT/'requests';chunks.mkdir()
request=json.loads((HERE/('ALPHA_REQUEST_SKIN_FOCUS95.json'if skin else'ALPHA_REQUEST95.json')).read_text()); queries=request.pop('queries'); request['queryCount']=len(queries)
(OUT/'HEADER95.json').write_text(json.dumps(request,separators=(',',':')))
for start in range(0,len(queries),128):
    text=json.dumps({'queries':queries[start:start+128]},separators=(',',':'))
    assert len(text)<65536
    (chunks/f'query-{start//128:03d}.json').write_text(text)
s=(HERE/'alpha/ReadAlpha95.cs').read_text().replace('Path.Combine(Root,"ALPHA_REQUEST95.json")','@"'+str(OUT/'HEADER95.json')+'"').replace('request["queries"].Count>32768','(int)request["queryCount"]>32768').replace('ALPHA_SOURCE95.json','ALPHA_SOURCE_SKIN95.json'if skin else'ALPHA_SOURCE95B.json')
s=s.replace('foreach(var q in request["queries"]){','foreach(string chunk in Directory.GetFiles(@"'+str(chunks)+'","query-*.json").OrderBy(x=>x)){var batch=Json58.Parse(File.ReadAllText(chunk));foreach(var q in batch["queries"]){')
s=s.replace('   report["sources"]=sources;', '   }\n   report["sources"]=sources;',1)
(OUT/(mode+'.cs')).write_text(s,encoding='utf-8')
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
relay=(HERE/'alpha/relay95.py').read_text().replace("'ReadAlpha95')","'ReadAlpha95','"+mode+"')");(OUT/'relay95.py').write_text(relay,encoding='utf-8')
print(json.dumps({'chunks':len(list(chunks.glob('*.json'))),'totalQueries':len(queries),'maxInputChars':max(len(p.read_text())for p in chunks.glob('*.json')),'parserLimitPreserved':65536,'previousFailedProtocolPreserved':True}))
