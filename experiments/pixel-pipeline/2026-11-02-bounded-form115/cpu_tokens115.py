"""Bounded CPU interpretation of the existing cached EvaluateForm115 SM5 tokens.

Not a GPU/driver emulator or proof of actual submitted GPU constant contents.
Uses the frozen fixture and host-intended uniform values; never calls Unity,
loads graphics libraries, compiles shaders, dispatches, or changes shader caches.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import json, hashlib, struct
import numpy as np

H = Path(__file__).resolve().parent
U = np.uint32

def bits(values): return np.array(values, dtype=np.float32).view(np.uint32)
def floats(values): return np.array(values, dtype=np.uint32).view(np.float32)
def wrap(values): return np.array([int(v) & 0xffffffff for v in values], dtype=np.uint32)

class VM:
    def __init__(self, packet, fixture, tid):
        self.rows = packet['instructions']; self.tid = U([tid, 0, 0, 0])
        self.r = np.full((14, 4), 0x7fc00000, dtype=np.uint32)
        self.x = np.full((5, 32, 4), 0x7fc00000, dtype=np.uint32)
        self.cb = np.zeros((36, 4), dtype=np.uint32)
        self.cb[30, 1:3] = U([2, 1]); self.cb[31, 0] = 20; self.cb[35, :2] = U([18, 8])
        slots = ['tags', 'frame', 'points', 'moments', 'references', 'state', 'candidates', 'metrics']
        self.buffers = {}
        for index, name in enumerate(slots):
            if name == 'state': data = struct.pack('<8I', 2, 0, 0, 0, 0, 0, 0, 0)
            elif name == 'metrics': data = bytes(160)
            else: data = (H / fixture['files'][name]['file']).read_bytes()
            self.buffers[('u', index)] = bytearray(data)
        self.buffers[('t', 0)] = bytearray((H / 'keys.bin').read_bytes())
        self.strides = {('u', i): v for i, v in enumerate([16, 16, 16, 32, 32, 16, 16, 80])}
        self.strides[('t', 0)] = 48
        self.branches = {}; self.loops = {}; self.enclosing = {}; stack = []; ifs = []
        for i, row in enumerate(self.rows):
            op = row['name']
            if op == 'loop': stack.append(i)
            if stack: self.enclosing[i] = stack[-1]
            if op == 'endloop':
                start = stack.pop(); self.loops[start] = i; self.loops[i] = start
            if op == 'if': ifs.append([i, None])
            if op == 'else': ifs[-1][1] = i
            if op == 'endif':
                start, otherwise = ifs.pop()
                self.branches[start] = otherwise if otherwise is not None else i
                if otherwise is not None: self.branches[otherwise] = i
        assert not stack and not ifs
        self.steps = 0; self.loopVisits = Counter(); self.memory = Counter(); self.maxIndex = {}

    def indices(self, op):
        out = []
        for item in op['indices']:
            value = item['immediate']
            if item['relative']: value += int(self.read(item['relative'], integer=True)[0])
            out.append(value)
        return out

    @staticmethod
    def lanes(op):
        if op['components'] != 2: return list(range(4))
        if op['selection'] == 0: return [i for i in range(4) if op['selectors'] & (1 << i)]
        if op['selection'] == 2: return [op['selectors'] & 3]
        raise AssertionError('Unexpected destination selector')

    def read(self, op, integer=False):
        typ = op['type']; idx = self.indices(op)
        if typ == 4:
            values = op['values']
            out = U(values * 4 if len(values) == 1 else values)
        elif typ == 0: out = self.r[idx[0]].copy()
        elif typ == 3:
            assert 0 <= idx[0] < 5 and 0 <= idx[1] < 32, ('private array bounds', idx)
            self.maxIndex['private'] = max(self.maxIndex.get('private', 0), idx[1])
            out = self.x[idx[0], idx[1]].copy()
        elif typ == 8: out = self.cb[idx[1]].copy()
        elif typ == 32: out = self.tid.copy()
        else: raise AssertionError(('read operand type', typ))
        if op['components'] == 2:
            if op['selection'] == 1: out = U([out[(op['selectors'] >> (i * 2)) & 3] for i in range(4)])
            elif op['selection'] == 2: out = np.full(4, out[op['selectors'] & 3], dtype=np.uint32)
        for ext in op['modifiers']:
            mod = (ext >> 6) & 255
            if mod in (2, 3): out &= U(0x7fffffff)
            if mod in (1, 3): out = wrap(-out.astype(np.int64)) if integer else out ^ U(0x80000000)
            assert mod in (0, 1, 2, 3)
        return out

    def write(self, op, value):
        if op['type'] == 13: return
        idx = self.indices(op)
        if op['type'] == 0: dst = self.r[idx[0]]
        elif op['type'] == 3:
            assert 0 <= idx[0] < 5 and 0 <= idx[1] < 32, ('private array write', idx)
            dst = self.x[idx[0], idx[1]]
        else: raise AssertionError(('write operand type', op['type']))
        for lane in self.lanes(op): dst[lane] = value[lane]

    def condition(self, row, value):
        return bool(int(value[0]) != 0) == bool(row['words'][0] & 0x40000)

    def memory_key(self, resource):
        return ('u' if resource['type'] == 30 else 't', self.indices(resource)[0])

    def load(self, resource, index, offset, lanes):
        key = self.memory_key(resource); data = self.buffers[key]; stride = self.strides[key]
        out = U([0, 0, 0, 0]); selectors = resource['selectors']
        for lane in lanes:
            component = (selectors >> (lane * 2)) & 3
            address = index * stride + offset + component * 4
            assert index >= 0 and index < len(data) // stride and 0 <= offset + component * 4 <= stride - 4, ('structured read bounds', key, index, offset, component)
            out[lane] = struct.unpack_from('<I', data, address)[0]
        self.memory[str(key)] += 1; self.maxIndex[str(key)] = max(self.maxIndex.get(str(key), 0), index)
        return out

    def store(self, resource, index, offset, value):
        key = self.memory_key(resource); data = self.buffers[key]; stride = self.strides[key]
        for lane in self.lanes(resource):
            assert 0 <= index < len(data) // stride and 0 <= offset + lane * 4 <= stride - 4
            struct.pack_into('<I', data, index * stride + offset + lane * 4, int(value[lane]))
        self.memory[str(key)] += 1; self.maxIndex[str(key)] = max(self.maxIndex.get(str(key), 0), index)

    def run(self, budget=200000):
        pc = 0
        with np.errstate(all='ignore'):
            while pc < len(self.rows):
                self.steps += 1
                assert self.steps <= budget, ('CPU execution budget exhausted', pc, self.rows[pc]['offset'])
                row = self.rows[pc]; name = row['name']; ops = row.get('operands', [])
                if name.startswith('dcl_') or name in ('endif', 'loop'):
                    if name == 'loop': self.loopVisits[str(row['offset'])] += 1
                elif name == 'if':
                    if not self.condition(row, self.read(ops[0], integer=True)): pc = self.branches[pc]
                elif name == 'else': pc = self.branches[pc]
                elif name == 'endloop':
                    pc = self.loops[pc]; self.loopVisits[str(self.rows[pc]['offset'])] += 1
                elif name in ('continue', 'breakc'):
                    if name == 'continue' or self.condition(row, self.read(ops[0], integer=True)):
                        start = self.enclosing[pc]
                        pc = start if name == 'continue' else self.loops[start]
                        if name == 'continue': self.loopVisits[str(self.rows[start]['offset'])] += 1
                elif name == 'ret': break
                elif name == 'ld_structured':
                    self.write(ops[0], self.load(ops[3], int(self.read(ops[1], True)[0]), int(self.read(ops[2], True)[0]), self.lanes(ops[0])))
                elif name == 'store_structured': self.store(ops[0], int(self.read(ops[1], True)[0]), int(self.read(ops[2], True)[0]), self.read(ops[3], True))
                elif name == 'atomic_or':
                    key = self.memory_key(ops[0]); address = self.read(ops[1], True); data = self.buffers[key]; stride = self.strides[key]
                    pos = int(address[0]) * stride + int(address[1]); assert 0 <= pos <= len(data) - 4
                    struct.pack_into('<I', data, pos, struct.unpack_from('<I', data, pos)[0] | int(self.read(ops[2], True)[0]))
                elif name in ('imul', 'udiv'):
                    a = self.read(ops[2], True); b = self.read(ops[3], True)
                    if name == 'imul':
                        product = a.view(np.int32).astype(np.int64) * b.view(np.int32).astype(np.int64)
                        self.write(ops[0], wrap(product >> 32)); self.write(ops[1], wrap(product))
                    else:
                        assert np.all(b != 0), 'integer divide by zero'
                        self.write(ops[0], a // b); self.write(ops[1], a % b)
                else:
                    integer = name in ('and', 'or', 'xor', 'not', 'iadd', 'imad', 'ineg', 'ishl', 'ishr', 'ushr', 'ige', 'ilt', 'ieq', 'ine', 'ult', 'uge', 'imax', 'imin', 'umin', 'countbits', 'bfi', 'itof', 'utof')
                    vals = [self.read(op, integer) for op in ops[1:]]
                    a = vals[0]; b = vals[1] if len(vals) > 1 else None
                    if name == 'mov': value = a
                    elif name == 'movc': value = np.where(a != 0, b, vals[2]).astype(np.uint32)
                    elif name == 'and': value = a & b
                    elif name == 'or': value = a | b
                    elif name == 'xor': value = a ^ b
                    elif name == 'not': value = ~a
                    elif name == 'iadd': value = wrap(a.astype(np.uint64) + b.astype(np.uint64))
                    elif name == 'imad': value = wrap(a.astype(np.uint64) * b.astype(np.uint64) + vals[2].astype(np.uint64))
                    elif name == 'ineg': value = wrap(-a.astype(np.int64))
                    elif name == 'ishl': value = wrap(a.astype(np.uint64) << (b & U(31)).astype(np.uint64))
                    elif name == 'ushr': value = a >> (b & U(31))
                    elif name == 'ishr': value = (a.view(np.int32) >> (b & U(31))).astype(np.uint32)
                    elif name in ('imin', 'imax'): value = (np.minimum if name == 'imin' else np.maximum)(a.view(np.int32), b.view(np.int32)).astype(np.uint32)
                    elif name == 'umin': value = np.minimum(a, b)
                    elif name in ('ieq', 'ine', 'ige', 'ilt', 'ult', 'uge'):
                        aa, bb = (a, b) if name.startswith('u') else (a.view(np.int32), b.view(np.int32))
                        test = {'ieq': np.equal, 'ine': np.not_equal, 'ige': np.greater_equal, 'ilt': np.less, 'ult': np.less, 'uge': np.greater_equal}[name](aa, bb)
                        value = np.where(test, U(0xffffffff), U(0)).astype(np.uint32)
                    elif name in ('itof', 'utof'): value = bits(a.view(np.int32) if name == 'itof' else a)
                    elif name == 'countbits': value = U([int(v).bit_count() for v in a])
                    elif name == 'bfi':
                        value = U([((int(base) & ~(int(((1 << (int(width) & 31)) - 1) << (int(off) & 31)))) | ((int(ins) << (int(off) & 31)) & int(((1 << (int(width) & 31)) - 1) << (int(off) & 31)))) & 0xffffffff for width, off, ins, base in zip(*vals)])
                    else:
                        aa = floats(a); bb = floats(b) if b is not None else None
                        if name == 'add': value = bits(aa + bb)
                        elif name == 'mul': value = bits(aa * bb)
                        elif name == 'div': value = bits(aa / bb)
                        elif name == 'min': value = bits(np.minimum(aa, bb))
                        elif name == 'max': value = bits(np.maximum(aa, bb))
                        elif name == 'round_ne': value = bits(np.rint(aa))
                        elif name in ('eq', 'ne', 'ge', 'lt'):
                            test = {'eq': np.equal, 'ne': np.not_equal, 'ge': np.greater_equal, 'lt': np.less}[name](aa, bb)
                            value = np.where(test, U(0xffffffff), U(0)).astype(np.uint32)
                        else: raise AssertionError(('unsupported opcode', name, row['offset']))
                    self.write(ops[0], value)
                pc += 1
        data = self.buffers[('u', 7)]; start = int(self.tid[0]) * 80
        metric = np.frombuffer(data[start:start + 80], dtype='<u4')
        return {'tid': int(self.tid[0]), 'steps': self.steps, 'loopVisits': dict(self.loopVisits), 'structuredAccesses': dict(self.memory), 'maxIndices': self.maxIndex, 'metricWords': metric.tolist(), 'metricFloats': metric[:16].view(np.float32).tolist(), 'info': metric[16:].tolist()}

def main():
    from dxbc_read115 import decode
    decode()
    packet = json.loads((H / 'CACHED_EVALUATE_DECODED115.json').read_text())
    fixture = json.loads((H / 'FIXTURE115.json').read_text())
    assert all(hashlib.sha256((H / row['file']).read_bytes()).hexdigest() == row['SHA256'] for row in fixture['files'].values())
    results = [VM(packet, fixture, tid).run() for tid in range(2)]
    for item in results:
        assert item['info'] == [63, 0, 0, 0], item
        lo = item['metricFloats'][:4] + item['metricFloats'][8:10]
        hi = item['metricFloats'][4:8] + item['metricFloats'][12:14]
        exact = [Fraction(v) for v in fixture['expectedRationalMetrics'][item['tid']]]
        item['enclosesRationalOracle'] = [Fraction(float(a)) <= target <= Fraction(float(b)) for a, target, b in zip(lo, exact, hi)]
        assert all(item['enclosesRationalOracle']), item
    report = {'GPUCommands': 0, 'UnityCommands': 0, 'CompilerInvocations': 0, 'cacheSHA256': packet['SHA256'],
              'cache': packet['cache'], 'CPUInterpretationOnly': True,
              'limitations': ['Host-intended uniforms and fixtures; actual GPU constant/resource contents were not echoed.', 'Does not emulate driver translation, device execution, memory scheduling, FTZ or readback transport.'], 'results': results}
    (H / 'CPU_TOKEN_RESULT115.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'terminated': True, 'results': [{'tid': r['tid'], 'steps': r['steps'], 'info': r['info'], 'enclosures': r['enclosesRationalOracle']} for r in results]}))

if __name__ == '__main__': main()
