"""blender -b -P scene.py -- mesh.npz outdir views(comma) samples res"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
NPZ, OUTDIR = argv[0], argv[1]
VIEWS = argv[2].split(',') if len(argv) > 2 else ['front']
SAMPLES = int(argv[3]) if len(argv) > 3 else 32
RES = int(argv[4]) if len(argv) > 4 else 600
SAVE = argv[5] if len(argv) > 5 else ''
PRM = json.load(open(NPZ.replace('.npz', '.json')))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------- mesh ----------------
data = np.load(NPZ)
V, F = data['verts'], data['faces']
me = bpy.data.meshes.new('Pikachu')
me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.ravel())
me.polygons.add(len(F))
me.polygons.foreach_set('loop_start', np.arange(0, F.size, 3, dtype=np.int32))
me.polygons.foreach_set('loop_total', np.full(len(F), 3, np.int32))
me.update(); me.validate()
body = bpy.data.objects.new('Pikachu_Body', me)
sc.collection.objects.link(body)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
me.shade_smooth() if hasattr(me, 'shade_smooth') else None
for p in me.polygons:
    p.use_smooth = True
m = body.modifiers.new('Smooth', 'CORRECTIVE_SMOOTH')
m.factor = 0.5; m.iterations = 4; m.smooth_type = 'LENGTH_WEIGHTED'; m.use_only_smooth = True
m.rest_source = 'ORCO'

# ---------------- body material with procedural colour masks ----------------
mat = bpy.data.materials.new('Pikachu_Skin'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; L = nt.links
bsdf = N['Principled BSDF']
X = [0]


def node(t, **kw):
    n = N.new(t); n.location = (X[0], -len(N) * 30)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def link(a, b):
    L.new(a, b)


def val(v):
    return v


def M(op, a, b=None, c=None):
    n = node('ShaderNodeMath', operation=op)
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            link(x, n.inputs[i])
    return n.outputs[0]


def VM(op, a, b=None):
    n = node('ShaderNodeVectorMath', operation=op)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (tuple, list)):
            n.inputs[i].default_value = x
        else:
            link(x, n.inputs[i])
    out = n.outputs['Value'] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs['Vector']
    return out


def smooth(x, lo, hi):
    n = node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
    link(x, n.inputs['Value']); n.inputs['From Min'].default_value = lo; n.inputs['From Max'].default_value = hi
    return n.outputs['Result']


tc = node('ShaderNodeTexCoord')
P = tc.outputs['Object']
sep = node('ShaderNodeSeparateXYZ'); link(P, sep.inputs[0])
px, py, pz = sep.outputs
ax = M('ABSOLUTE', px)

masks = {}
# ear tips (black)
ear_m = None
for e in PRM['ears']:
    t = M('DIVIDE', VM('DOT_PRODUCT', VM('SUBTRACT', P, e['base']), e['u']), e['L'])
    mk = smooth(t, PRM['ear_t0'] - 0.002, PRM['ear_t0'] + 0.002)
    ear_m = mk if ear_m is None else M('MAXIMUM', ear_m, mk)
masks['black'] = ear_m
# cheeks (red)
ch = None
for c in PRM['cheeks']:
    d = VM('DISTANCE', P, c)
    mk = M('SUBTRACT', 1.0, smooth(d, 0.0615, 0.0645))
    ch = mk if ch is None else M('MAXIMUM', ch, mk)
masks['red'] = ch
# back stripes (brown) - taper toward sides
back = M('MULTIPLY', smooth(py, 0.10, 0.125), M('SUBTRACT', 1.0, smooth(py, 0.25, 0.258)))
st = None
for z0, hw0 in ((0.468, 0.021), (0.372, 0.021)):
    zc = M('SUBTRACT', z0, M('MULTIPLY', M('MULTIPLY', px, px), 0.9))
    dz = M('ABSOLUTE', M('SUBTRACT', pz, zc))
    q = M('DIVIDE', ax, 0.175)
    hw = M('MULTIPLY', hw0, M('SUBTRACT', 1.0, M('MULTIPLY', q, q)))
    mk = M('SUBTRACT', 1.0, smooth(M('SUBTRACT', dz, hw), -0.0015, 0.0015))
    mk = M('MULTIPLY', mk, back)
    st = mk if st is None else M('MAXIMUM', st, mk)
# tail root (brown)
tr = M('MULTIPLY', smooth(py, 0.195, 0.205), M('SUBTRACT', 1.0, smooth(py, 0.262, 0.27)))
tr = M('MULTIPLY', tr, M('SUBTRACT', 1.0, smooth(ax, 0.042, 0.048)))
tr = M('MULTIPLY', tr, M('SUBTRACT', 1.0, smooth(pz, 0.33, 0.345)))
masks['brown'] = M('MAXIMUM', st, tr)
# mouth line (dark)
mo = PRM['mouth']
qq = M('MINIMUM', M('DIVIDE', ax, mo['w']), 1.0)
zc = M('SUBTRACT', mo['z0'], M('MULTIPLY', mo['a'], M('SINE', M('MULTIPLY', qq, math.pi))))
ext = M('MULTIPLY', M('MAXIMUM', M('SUBTRACT', ax, mo['w']), 0.0), 0.5)
zc = M('ADD', zc, ext)
dm = M('ABSOLUTE', M('SUBTRACT', pz, zc))
mm = M('SUBTRACT', 1.0, smooth(dm, 0.0016, 0.0028))
mm = M('MULTIPLY', mm, M('SUBTRACT', 1.0, smooth(ax, mo['w'] + 0.009, mo['w'] + 0.012)))
mm = M('MULTIPLY', mm, M('SUBTRACT', 1.0, smooth(py, -0.17, -0.15)))
masks['mouth'] = mm


def mix(col_in, fac, rgba):
    n = node('ShaderNodeMix', data_type='RGBA', blend_type='MIX')
    if isinstance(col_in, tuple):
        n.inputs[6].default_value = col_in
    else:
        link(col_in, n.inputs[6])
    n.inputs[7].default_value = rgba
    link(fac, n.inputs[0])
    return n.outputs[2]


def srgb(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


YEL, BLK, RED, BRN, MTH = srgb('#F9D23C'), srgb('#1E1A17'), srgb('#E5372B'), srgb('#7A4A26'), srgb('#4A1F17')
col = mix(YEL, masks['brown'], BRN)
col = mix(col, masks['red'], RED)
col = mix(col, masks['black'], BLK)
col = mix(col, masks['mouth'], MTH)
link(col, bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.42
bsdf.inputs['Coat Weight'].default_value = 0.15
bsdf.inputs['Coat Roughness'].default_value = 0.25
bsdf.inputs['Subsurface Weight'].default_value = 0.05
bsdf.inputs['Subsurface Radius'].default_value = (0.02, 0.01, 0.005)
body.data.materials.append(mat)


def simple_mat(name, rgba, rough, coat=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = rgba
        b.inputs['Emission Strength'].default_value = emit
    return m


M_EYE = simple_mat('Eye_Black', srgb('#141210'), 0.08, coat=1.0)
M_HI = simple_mat('Eye_Highlight', (1, 1, 1, 1), 0.2, emit=0.6)
M_NOSE = simple_mat('Nose', srgb('#1E1A17'), 0.3, coat=0.5)

# ---------------- eyes / nose placed on the evaluated surface ----------------
dg = bpy.context.evaluated_depsgraph_get()
bev = body.evaluated_get(dg)


def hit(x, z):
    ok, loc, nrm, _ = bev.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    assert ok, (x, z)
    return loc, nrm.normalized()


def oriented(name, loc, n, scale, mat, up=Vector((0, 0, 1))):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1, location=loc)
    o = bpy.context.active_object; o.name = name
    yax = -n
    xax = up.cross(yax).normalized(); zax = yax.cross(xax).normalized()
    R = Matrix((xax, yax, zax)).transposed().to_4x4()
    o.matrix_world = Matrix.Translation(loc) @ R @ Matrix.Diagonal((*scale, 1))
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


for s in (-1, 1):
    loc, n = hit(0.104 * s, 0.805)
    ex, ey, ez = 0.040, 0.022, 0.050
    c = loc - n * 0.006
    oriented(f'Eye_{"L" if s < 0 else "R"}', c, n, (ex, ey, ez), M_EYE)
    up = Vector((0, 0, 1)); xax = up.cross(-n).normalized(); zax = (-n).cross(xax).normalized()
    off = zax * 0.019 + xax * (0.006 * s)
    fz = 0.019 / ez; fx = 0.006 / ex
    depth = ey * math.sqrt(max(0, 1 - fz * fz - fx * fx)) - 0.006
    oriented(f'Eye_Highlight_{"L" if s < 0 else "R"}', c + off + n * (depth + 0.0012), n, (0.0155, 0.004, 0.0155), M_HI)
loc, n = hit(0.0, 0.752)
oriented('Nose', loc - n * 0.001, n, (0.011, 0.005, 0.0075), M_NOSE)

# ---------------- stage ----------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object; floor.name = 'Floor'
floor.data.materials.append(simple_mat('Floor', (0.85, 0.85, 0.85, 1), 0.6))
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.6, 0.68, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.5


def area(name, loc, target, power, size):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size
    o = bpy.data.objects.new(name, ld); sc.collection.objects.link(o); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


area('Key', (-2.2, -3.0, 3.2), (0, 0, 0.7), 650, 2.5)
area('Fill', (3.0, -2.2, 1.6), (0, 0, 0.6), 160, 3.0)
area('Rim', (0.8, 3.2, 2.8), (0, 0, 0.8), 600, 2.0)

sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
try:
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
sc.view_settings.view_transform = 'Filmic'
sc.view_settings.look = 'Medium High Contrast'
sc.render.film_transparent = False

VIEWS_DEF = {
    'front': ((0, -6.5, 0.74), (0, 0, 0.72), 140, 1.0),
    'side': ((6.5, 0.12, 0.74), (0, 0.12, 0.72), 140, 1.0),
    'back': ((0, 6.8, 0.8), (0, 0.15, 0.72), 140, 1.0),
    'q34': ((-3.9, -5.0, 1.9), (0, 0.05, 0.68), 140, 1.0),
    'face': ((0, -3.0, 0.8), (0, 0, 0.76), 180, 1.0),
    'hands': ((0.0, -2.2, 0.62), (0, -0.2, 0.46), 150, 1.4),
    'feet': ((0.35, -1.9, 0.45), (0, -0.1, 0.05), 150, 1.6),
    'ear': ((-1.4, -2.0, 1.55), (-0.26, 0.06, 1.2), 140, 1.0),
}
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam)
sc.camera = cam
sc.render.resolution_y = RES
for v in [v for v in VIEWS if v in VIEWS_DEF]:
    loc, tgt, lens, aspect = VIEWS_DEF[v]
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lens * (1.0 if v in ('front', 'side', 'back', 'q34') else 1.0)
    sc.render.resolution_x = int(RES * 0.8 * aspect)
    sc.render.filepath = f'{OUTDIR}/{v}.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', v, flush=True)

if SAVE:
    cam.location, cam.rotation_euler = VIEWS_DEF['q34'][0], (Vector(VIEWS_DEF['q34'][1]) - Vector(VIEWS_DEF['q34'][0])).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE, compress=True)

# ORTHO_HOOK
import os
if os.environ.get('ORTHO'):
    exec(open(os.environ['ORTHO']).read())
