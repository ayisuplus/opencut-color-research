"""Freeze source-owned mixed-color stimuli and predictions before native observation."""
import ast
import hashlib
import itertools
import json
from pathlib import Path
import struct
import zlib

import numpy as np

root = Path(__file__).resolve().parents[1]
output = root / 'experiments/output/hdr-mixed-input'
output.mkdir(parents=True, exist_ok=True)
width, height = 1920, 1080
levels = [0.025, 0.13, 0.45]
permutations = list(itertools.permutations(range(3)))
colors = [tuple(levels[j] for j in p) for p in permutations] * 2
colors += [(v, v, v) for v in levels] + [(0., 0., 0.)]
pixels = np.empty((height, width, 3), dtype='>u2')
samples = []
for i, color in enumerate(colors):
    linear = np.array(color)
    encoded = np.where(linear <= .0031308, 12.92 * linear,
                       1.055 * linear ** (1 / 2.4) - .055)
    codes = np.floor(encoded * 65535 + .5).astype('>u2')
    normalized = codes.astype(float)/65535
    realized = np.where(normalized <= .04045, normalized/12.92,
                        ((normalized+.055)/1.055)**2.4)
    row, column = divmod(i, 4)
    x, y = column * 480, row * 270
    pixels[y:y+270, x:x+480] = codes
    samples.append({'id': i, 'sample_xy': [x+240, y+135],
                    'roi_xyxy': [x+208, y+103, x+272, y+167],
                    'intended_linear_rgb': list(color),
                    'encoded_rgb_u16': codes.astype(int).tolist(),
                    'encoded_rgb_normalized': (codes.astype(float)/65535).tolist(),
                    'realized_linear_rgb': realized.tolist(),
                    'duplicate_of': i-6 if 6 <= i < 12 else None})

def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))

png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 16, 2, 0, 0, 0))
       + chunk(b'sRGB', b'\0')
       + chunk(b'IDAT', zlib.compress(b''.join(b'\0'+row.tobytes() for row in pixels)))
       + chunk(b'IEND', b''))
image = output / 'mixed-permutations-srgb16.png'
image.write_bytes(png)

# Reuse only the frozen public transfer-function definitions, with no module side effects.
source = root / 'experiments/evaluate-hdr-domain-candidates.py'
tree = ast.parse(source.read_text(encoding='utf8'))
nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name.startswith('bt709_')) or
         (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'bt709_threshold' for t in n.targets))]
ns = {'np': np}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
encoded = np.array([s['encoded_rgb_normalized'] for s in samples])
linear = ns['bt709_decode'](encoded)
weights = np.array([.2126, .7152, .0722])
q = np.log2(np.clip(linear @ weights / .18, 2.**-8, 2.**8))
position = (q+8)/16*1024-.5
index = np.floor(position).astype(int)
fraction = position-index
predictions = {}
for e in [-1., 0., 1.]:
    models = {'BT709_exp2_only': ns['bt709_encode'](linear*2.**e)}
    table = np.float32(np.float32(np.arange(1024, dtype=np.float32) * np.float32(16/1023)) - np.float32(8))
    table = np.float32(table+np.float32(e))
    original = table.copy()
    total = float(original[0])
    right = float(original[-1])
    for i in range(1, 52):
        total = (total+float(original[2*i-1]))+float(original[2*i])
        right = (right+float(original[1024-2*i]))+float(original[1023-2*i])
        table[i] = np.float32(total/float(2*i+1))
        table[1023-i] = np.float32(right/float(2*i+1))
    for i in range(52, 973):
        total = (float(original[i+51])-float(original[i-52]))+total
        table[i] = np.float32(total/103.)
    for name, alpha in [('static_table_ideal_alpha', fraction),
                        ('static_table_nearest_1_256_alpha', np.round(fraction*256)/256)]:
        sampled = table[np.clip(index, 0, 1023)]*(1-alpha)+table[np.clip(index+1, 0, 1023)]*alpha
        prediction = ns['bt709_encode'](linear*2.**(sampled[:, None]-q[:, None]))
        models[name] = encoded.copy() if e == 0 else prediction
    assert all(np.isfinite(v).all() for v in models.values())
    predictions[str(int(e))] = {k: v.tolist() for k, v in models.items()}

report = {
    'scope': 'pre_native_freeze_for_unseen_mixed_input_no_fitted_parameters',
    'source_owned': True, 'dimensions': [width, height],
    'encoding': 'opaque full-range RGB16 PNG with sRGB chunk intent 0',
    'fixture': {'path': image.relative_to(root).as_posix(), 'bytes': len(png),
                'sha256': hashlib.sha256(png).hexdigest()},
    'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'transfer_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'samples': samples, 'predictions': predictions,
    'candidate_assumptions': {'working_Y_weights': weights.tolist(),
        'working_Y_scale': '100 * weighted decoded RGB', 'table_entries': 1024,
        'smoothing_radius': 51, 'smoothing_accumulator': 'float64, float32 output',
        'zero': 'Explicit gain-disabled case; other controls assumed neutral.',
        'last_writer': 'Global is assumed the last type-0 writer; verify native grade.'},
    'measurements_planned': ['neutral-before', 'minus1', 'zero', 'plus1',
                            'plus1-replay', 'neutral-restored'],
    'checks_planned': ['neutral input decoding at centers and 64x64 ROIs',
        'zero and restored neutral whole-RGB equality', 'plus1 replay whole-RGB equality',
        'same-color spatial duplicates at centers and corresponding ROIs',
        'common per-patch linear multiplier under frozen BT709 decode',
        'same input component across different RGB contexts',
        'three frozen candidate residuals; report raw errors without invented pass tolerance'],
    'limits': ['No native frames have been read for this fixture.',
        'Predictions use frozen assumptions, not recovered working-color matrices or runtime textures.',
        'Six unique mixed colors, three grays and black are not arbitrary-image validation.',
        'PNG sRGB metadata does not determine the actual HDR working transfer function.'],
}
(root / 'docs/experiments/hdr-mixed-input-freeze.json').write_text(
    json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
print(json.dumps({'fixture_sha256': report['fixture']['sha256'], 'patches': len(samples),
                  'spatial_pairs': 6, 'models': list(predictions['1'])}))
