"""CuraEngine CLI wrapper: slices an STL to G-code without opening Cura.
CuraEngine alone does not evaluate Cura's formula settings, so it stops with
"Trying to retrieve setting with no value given: X". This wrapper resolves the
printer definition chain (inherits) + extruder, fills every setting's default_value,
then retries and fills anything still missing.

usage:
  python slice_cura.py model.stl out.gcode --printer creality_ender3 [--set key=value ...]
  Windows: --cura "C:\\Program Files\\UltiMaker Cura 5.13.0"   (folder that has CuraEngine.exe and share\\cura\\resources)
  Linux AppImage: extract with --appimage-extract and pass --cura <squashfs-root>
Prints a summary (layers, print time, filament) at the end.
"""
import argparse, json, os, platform, re, subprocess, sys

PROFILE = {  # figure-friendly defaults
    'layer_height': 0.12, 'wall_line_count': 3, 'infill_sparse_density': 12,
    'support_enable': True, 'support_structure': 'tree', 'adhesion_type': 'brim',
    'machine_center_is_zero': False,
}

ap = argparse.ArgumentParser()
ap.add_argument('stl'); ap.add_argument('out')
ap.add_argument('--printer', default='creality_ender3')
ap.add_argument('--cura', default=os.environ.get('CURA_HOME', ''))
ap.add_argument('--set', action='append', default=[])
a = ap.parse_args()

home = os.path.abspath(a.cura)
res = os.path.join(home, 'share', 'cura', 'resources')
defs, exts = os.path.join(res, 'definitions'), os.path.join(res, 'extruders')


def load_chain(folder, name, fallback=None):
    vals, chain = {}, []
    while name:
        p = os.path.join(folder, name + '.def.json')
        if not os.path.exists(p) and fallback:
            p = os.path.join(fallback, name + '.def.json')
        d = json.load(open(p, encoding='utf-8'))
        chain.append(d); name = d.get('inherits')
    for d in reversed(chain):  # base first, children override
        def walk(node):
            for k, v in node.items():
                if isinstance(v, dict):
                    if 'default_value' in v:
                        vals[k] = v['default_value']
                    if 'children' in v:
                        walk(v['children'])
        walk(d.get('settings', {}))
        for k, v in d.get('overrides', {}).items():
            if 'default_value' in v:
                vals[k] = v['default_value']
            elif 'value' in v and re.fullmatch(r'-?[\d.]+|True|False|"[^"]*"|\'[^\']*\'', str(v['value']).strip()):
                vals[k] = eval(str(v['value']))
    return vals, chain


machine, chain = load_chain(defs, a.printer)
extruder_name = None
for d in chain:
    ex = d.get('metadata', {}).get('machine_extruder_trains', {})
    if ex:
        extruder_name = ex.get('0') or list(ex.values())[0]; break
extruder = load_chain(exts, extruder_name, defs)[0] if extruder_name else {}

settings = {**machine, **PROFILE}
for kv in a.set:
    k, v = kv.split('=', 1); settings[k] = v
# place model at bed centre
# with machine_center_is_zero=false CuraEngine shifts a model centred on the origin to the bed centre (verified)
settings.setdefault('mesh_position_x', 0); settings.setdefault('mesh_position_y', 0)


def fmt(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    return str(v)


exe = os.path.join(home, 'CuraEngine.exe' if platform.system() == 'Windows' else 'CuraEngine')
prefix = []
compat_ld = os.path.join(home, 'runtime', 'compat', 'lib64', 'ld-linux-x86-64.so.2')
if platform.system() == 'Linux' and os.path.exists(compat_ld):  # AppImage needs its own loader + libstdc++
    lp = ':'.join(os.path.join(home, p) for p in ['', 'runtime/compat', 'runtime/compat/lib/x86_64-linux-gnu',
                  'runtime/compat/usr/lib/x86_64-linux-gnu', 'usr/lib/x86_64-linux-gnu', 'lib/x86_64-linux-gnu', 'usr/lib'])
    prefix = [compat_ld, '--library-path', lp]

stl, out = os.path.abspath(a.stl), os.path.abspath(a.out)
env = {**os.environ, 'CURA_ENGINE_SEARCH_PATH': os.pathsep.join([defs, exts])}
missing_fill = {}
for attempt in range(40):
    cmd = prefix + [exe, 'slice', '-j', os.path.join(defs, a.printer + '.def.json')]
    for k, v in {**settings, **missing_fill}.items():
        cmd += ['-s', f'{k}={fmt(v)}']
    cmd += ['-e0']
    for k, v in {**extruder, **missing_fill}.items():
        cmd += ['-s', f'{k}={fmt(v)}']
    cmd += ['-l', stl, '-o', out]
    p = subprocess.run(cmd, cwd=home, env=env, capture_output=True, text=True)
    log = p.stdout + p.stderr
    m = re.search(r'no value given: (\w+)', log)
    if p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000:
        break
    if not m:
        sys.exit('CuraEngine failed:\n' + log[-3000:])
    missing_fill[m.group(1)] = 0  # setting only had a formula; 0 is a safe neutral fallback
else:
    sys.exit('too many missing settings')

head = open(out, encoding='utf-8', errors='ignore').read(4000)
info = dict(re.findall(r';(TIME|LAYER_COUNT|FLAVOR):\s*(.+)', head))
# CLI leaves ';Filament used: 0m' and MINX/MAXX placeholders (the Cura GUI fills them) -> compute from E values
seg_max = base = total = 0.0
layers = 0
for line in open(out, encoding='utf-8', errors='ignore'):
    if line.startswith(';LAYER:'):
        layers += 1
    elif line.startswith('G92'):
        m = re.search(r'E(-?[\d.]+)', line)
        if m:
            total += max(0.0, seg_max - base); base = seg_max = float(m.group(1))
    elif line.startswith(('G1', 'G0')):
        m = re.search(r'E(-?[\d.]+)', line)
        if m:
            seg_max = max(seg_max, float(m.group(1)))
total += max(0.0, seg_max - base)
dia = float(settings.get('material_diameter', 1.75))
cm3 = total * 3.14159265 * (dia / 2) ** 2 / 1000
print(f'OK  printer={a.printer}  gcode={out}  size={os.path.getsize(out)/1e6:.1f}MB  layers={layers}')
print(f'    filament={total/1000:.2f} m  = {cm3:.1f} cm3  = {cm3*1.24:.0f} g PLA')
print(f'    CuraEngine time estimate={int(float(info.get("TIME", 0)))//60} min (real printers are usually 1.5-2x slower)')
if missing_fill:
    print('    filled formula-only settings with 0:', ', '.join(missing_fill))
