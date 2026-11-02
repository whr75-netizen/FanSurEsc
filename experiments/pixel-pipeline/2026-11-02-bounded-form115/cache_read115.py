from pathlib import Path
import struct, json, hashlib, re, collections

root = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Library\ShaderCache\compute\ForwardEye115fe1e')
rows = []
for path in root.rglob('*.bin'):
    data = path.read_bytes()
    magic = data.find(b'DXBC')
    row = {'file': str(path.relative_to(root)), 'bytes': len(data), 'SHA256': hashlib.sha256(data).hexdigest(),
           'headHex': data[:40].hex(), 'DXBCoffset': magic, 'containsEvaluateName': b'EvaluateForm115' in data}
    row['resourceStrings'] = [x.decode('ascii') for x in re.findall(rb'_[A-Za-z0-9_]{3,}', data[:magic])]
    if magic >= 0 and magic + 32 <= len(data):
        total, count = struct.unpack_from('<II', data, magic + 24)
        row['DXBCbytes'] = total
        row['chunks'] = []
        if count < 100 and magic + total <= len(data):
            for index in range(count):
                pos = magic + struct.unpack_from('<I', data, magic + 32 + index * 4)[0]
                tag = data[pos:pos + 4].decode('ascii', errors='replace')
                size = struct.unpack_from('<I', data, pos + 4)[0]
                row['chunks'].append({'tag': tag, 'bytes': size})
                if tag in ('SHEX', 'SHDR'):
                    words = struct.unpack_from('<' + 'I' * (size // 4), data, pos + 8)
                    assert words[1] == len(words)
                    instructions = []
                    offset = 2
                    while offset < len(words):
                        token = words[offset]
                        opcode = token & 0x7ff
                        length = words[offset + 1] if opcode == 53 else (token >> 24) & 127
                        assert length and offset + length <= len(words), (path, offset, opcode, length)
                        instructions.append({'offset': offset, 'opcode': opcode, 'words': list(words[offset:offset + length])})
                        offset += length
                    row['instructionCount'] = len(instructions)
                    row['opcodeCounts'] = dict(collections.Counter(x['opcode'] for x in instructions))
                    row['loopInstructions'] = [x for x in instructions if x['opcode'] in (2,3,7,8,22,48)]
                    if '_Metrics115' in row['resourceStrings'] and '_CellKey115' in row['resourceStrings']:
                        Path(__file__).with_name('CACHED_EVALUATE_TOKENS115.json').write_text(json.dumps({'cache': row['file'], 'SHA256': row['SHA256'], 'version': words[0], 'instructions': instructions}, indent=2) + '\n', encoding='utf-8')
    rows.append(row)
output = Path(__file__).with_name('CACHE_READ115.json')
output.write_text(json.dumps({'readOnly': True, 'GPUOrCompilerExecuted': False, 'files': rows}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'fileCount': len(rows), 'totalBytes': sum(x['bytes'] for x in rows), 'rawDXBC': sum(x['DXBCoffset'] >= 0 for x in rows), 'matching': [x for x in rows if '_Metrics115' in x['resourceStrings'] and '_CellKey115' in x['resourceStrings']]}))
