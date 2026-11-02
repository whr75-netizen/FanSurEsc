"""Read cached SM5 tokens on CPU only. Does not load a DLL or execute shaders."""
from pathlib import Path
import json, struct

H = Path(__file__).resolve().parent
names = '''add and break breakc call callc case continue continuec cut default deriv_rtx deriv_rty discard div dp2 dp3 dp4 else emit emitthencut endif endloop endswitch eq exp frc ftoi ftou ge iadd if ieq ige ilt imad imax imin imul ine ineg ishl ishr itof label ld ld_ms log loop lt mad min max customdata mov movc mul ne nop not or resinfo ret retc round_ne round_ni round_pi round_z rsq sample sample_c sample_c_lz sample_l sample_d sample_b sqrt switch sincos udiv ult uge umul umad umax umin ushr utof xor dcl_resource dcl_constant_buffer dcl_sampler dcl_index_range dcl_gs_output_primitive_topology dcl_gs_input_primitive dcl_max_output_vertex_count dcl_input dcl_input_sgv dcl_input_siv dcl_input_ps dcl_input_ps_sgv dcl_input_ps_siv dcl_output dcl_output_sgv dcl_output_siv dcl_temps dcl_indexable_temp dcl_global_flags'''.split()
ops = dict(enumerate(names))
ops.update({134: 'countbits', 140: 'bfi', 155: 'dcl_thread_group', 158: 'dcl_uav_structured', 162: 'dcl_resource_structured', 167: 'ld_structured', 168: 'store_structured', 170: 'atomic_or'})
types = {0: 'r', 1: 'v', 2: 'o', 3: 'x', 4: 'l', 5: 'd', 7: 't', 8: 'cb', 30: 'u', 32: 'threadID'}

def operand(words, pos):
    token = words[pos]; pos += 1
    comps = token & 3
    typ = (token >> 12) & 255
    dimension = (token >> 20) & 3
    ext = bool(token & 0x80000000)
    modifiers = []
    while ext:
        extension = words[pos]; pos += 1
        modifiers.append(extension)
        ext = bool(extension & 0x80000000)
    indices = []
    for index in range(dimension):
        rep = (token >> (22 + index * 3)) & 7
        immediate = 0
        if rep in (0, 1, 3, 4):
            immediate = words[pos]; pos += 1
            if rep in (1, 4):
                immediate |= words[pos] << 32; pos += 1
        relative = None
        if rep in (2, 3, 4):
            relative, pos = operand(words, pos)
        indices.append({'immediate': immediate, 'relative': relative})
    values = []
    if typ in (4, 5):
        count = 1 if comps == 1 else 4
        if typ == 5: count *= 2
        values = words[pos:pos + count]; pos += count
    return {'type': typ, 'components': comps, 'selection': (token >> 2) & 3, 'selectors': (token >> 4) & 255,
            'indices': indices, 'values': values, 'modifiers': modifiers}, pos

def fmt(op):
    if op['type'] in (4, 5): return 'l(' + ','.join(hex(v) for v in op['values']) + ')'
    out = types.get(op['type'], 'type' + str(op['type']))
    for idx in op['indices']:
        out += '[' + str(idx['immediate']) + ('+' + fmt(idx['relative']) if idx['relative'] else '') + ']'
    if op['components'] == 2:
        mode = op['selection']; value = op['selectors']
        if mode == 0: out += '.' + ''.join('xyzw'[i] for i in range(4) if value & (1 << i))
        elif mode == 1: out += '.' + ''.join('xyzw'[(value >> (i * 2)) & 3] for i in range(4))
        elif mode == 2: out += '.' + 'xyzw'[value & 3]
    return out + ('{modifier:' + str(op['modifiers']) + '}' if op['modifiers'] else '')

def decode():
    packet = json.loads((H / 'CACHED_EVALUATE_TOKENS115.json').read_text())
    rows = []
    declarations = {89, 95, 104, 105, 106, 155, 158, 162}
    for row in packet['instructions']:
        opcode = row['opcode']; words = row['words']
        out = dict(row, name=ops.get(opcode, 'opcode' + str(opcode)))
        if opcode not in declarations:
            pos = 1
            if words[0] & 0x80000000:
                while True:
                    extended = words[pos]; pos += 1
                    if not extended & 0x80000000: break
            operands = []
            while pos < len(words):
                op, pos = operand(words, pos); operands.append(op)
            assert pos == len(words), row
            out['operands'] = operands
        rows.append(out)
    (H / 'CACHED_EVALUATE_DECODED115.json').write_text(json.dumps(dict(packet, instructions=rows), indent=2) + '\n')
    lines = []
    for row in rows:
        if 'operands' in row:
            text = ', '.join(fmt(op) for op in row['operands'])
        else: text = ','.join(hex(x) for x in row['words'][1:])
        lines.append(str(row['offset']) + ': ' + row['name'] + ' ' + text)
    (H / 'CACHED_EVALUATE_DISASM115.txt').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'decoded': len(rows), 'compilerExecuted': False, 'DLLLoaded': False, 'GPUExecuted': False}))

if __name__ == '__main__': decode()
