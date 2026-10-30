"""Standard-library snapshot integrity and bounded static dependency checks."""
from pathlib import Path
import ast, hashlib, io, json, re, sys, tokenize

R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=load(R/'PACKAGE_MANIFEST.json')
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)

actual={p.relative_to(R).as_posix():p for p in R.rglob('*')if p.is_file()and p.name!='PACKAGE_MANIFEST.json'}
check('package inventory is complete',set(actual)==set(manifest['files']))
for name,entry in manifest['files'].items():
    p=actual[name]
    check('SHA256 '+name,sha(p)==entry['sha256'] and p.stat().st_size==entry['bytes'])
source=load(R/'SOURCE_MANIFEST.json')['files']
copies={n:r for n,r in source.items()if r['mode']=='byte-exact copy'}
check('every copied original has matching SHA256',all(sha(R/n)==row['sha256']for n,row in copies.items()))
check('no runtime Assets/Packages or continuous46',not any(any(x in Path(n).parts for x in ['Assets','Packages','continuous46'])for n in actual))
check('no original model/texture/container or large generated output',all(p.stat().st_size<400000 and p.suffix.lower()not in {'.vrm','.fbx','.blend','.asset','.gz','.zip','.bin'}for p in actual.values()))
patterns=[re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(r'\bAKIA[0-9A-Z]{16}\b'),re.compile(r'\bgh[pousr]_[A-Za-z0-9]{25,}\b'),re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'),re.compile(r'(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"\x27][^\"\x27\r\n]{12,}[\"\x27]')]
hits=[];emails=[]
text_files={n:p for n,p in actual.items()if p.suffix in {'.py','.cjs','.mjs','.js','.json','.md'}}
for n,p in text_files.items():
    if p.name=='verify_snapshot.py':continue
    s=p.read_text(encoding='utf-8-sig')
    if any(pattern.search(s)for pattern in patterns):hits.append(n)
    email_text=s
    if p.suffix=='.py':
        # NumPy's matrix operator is not an email delimiter. Inspect Python
        # string/comment tokens, including docstrings and quoted addresses.
        email_text='\n'.join(t.string for t in tokenize.generate_tokens(io.StringIO(s).readline)if t.type in {tokenize.STRING,tokenize.COMMENT})
    if re.search(r'(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',email_text):emails.append(n)
check('no credential/private-key patterns',not hits)
check('no email addresses',not emails)
modules={p.stem for p in actual.values()if p.suffix=='.py'}
third_party={'numpy','PIL'};stdlib=sys.stdlib_module_names
missing=[]
for n,p in actual.items():
    if p.suffix!='.py':continue
    for node in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
        if isinstance(node,ast.Import):imports=[x.name.split('.')[0]for x in node.names]
        elif isinstance(node,ast.ImportFrom):imports=[(node.module or '').split('.')[0]]
        else:continue
        for name in imports:
            if name and name not in stdlib|third_party|modules:missing.append([n,name])
check('all Python local source modules preserved',not missing)
relative_missing=[]
for n,p in text_files.items():
    if p.suffix not in {'.cjs','.mjs','.js'}:continue
    for rel in re.findall(r'(?:require\(|from\s*)[\"\x27](\.[^\"\x27]+)[\"\x27]',p.read_text(encoding='utf-8')):
        if not (p.parent/rel).is_file():relative_missing.append([n,rel])
check('all literal JavaScript relative imports preserved',not relative_missing)
print(json.dumps({'suite':'snapshot integrity/size/secrets/local-module closure','passed':len(checks),'files':len(actual)+1,'bytes':sum(p.stat().st_size for p in R.rglob('*')if p.is_file()),'credentialHits':hits,'emailFiles':emails,'missingPythonModules':missing,'missingJSModules':relative_missing,'checks':checks},indent=2))
