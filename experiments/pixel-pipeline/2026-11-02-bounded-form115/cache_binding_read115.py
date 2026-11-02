from pathlib import Path
import json, struct

H = Path(__file__).resolve().parent
cache = json.loads((H / 'CACHED_EVALUATE_TOKENS115.json').read_text())
root = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Library\ShaderCache\compute\ForwardEye115fe1e')
data = (root / cache['cache']).read_bytes(); limit = data.index(b'DXBC')
rows = []
for name in ['_CurveEyeIds106', '_KeyCount113', '_CellsSize113', '_Keys113', '_CellTags113', '_Frame113', '_Points113', '_CellKey115', '_ReferenceKey115', '_FormState115', '_Candidates115', '_Metrics115']:
    at = data[:limit].index(name.encode())
    after = at + len(name)
    # Unity's cache wrapper is not publicly specified here: retain bytes rather
    # than invent an authoritative schema or assume native binding identity.
    rows.append({'name': name, 'byteOffset': at, 'stringEndOffset': after, 'next32BytesHex': data[after:after + 32].hex(),
                 'nextEightUInt32': list(struct.unpack_from('<8I', data, after))})
(H / 'CACHE_BINDING_BYTES115.json').write_text(json.dumps({'wrapperSchemaVerified': False, 'rows': rows}, indent=2) + '\n')
print(json.dumps(rows[:3] + rows[-2:]))
