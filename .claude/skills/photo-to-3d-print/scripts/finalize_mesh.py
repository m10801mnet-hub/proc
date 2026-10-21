"""GLB (Image-to-3D output) -> watertight STL/OBJ, Z-up, front -Y, base at Z=0, given height (mm).
usage: python finalize_mesh.py model.glb out_dir NAME [height_mm=100]
needs: trimesh scipy fast-simplification pymeshfix
"""
import sys, os, numpy as np, trimesh

src, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
H = float(sys.argv[4]) if len(sys.argv) > 4 else 100.0
os.makedirs(out, exist_ok=True)


def report(tag, g):
    e = g.edges_sorted
    _, c = np.unique(e, axis=0, return_counts=True)
    print(f'{tag}: F={len(g.faces)} watertight={g.is_watertight} winding={g.is_winding_consistent} '
          f'volume={g.is_volume} bodies={g.body_count} boundary={(c==1).sum()} nonmanifold={(c>2).sum()} '
          f'size_mm={np.ptp(g.vertices,0).round(1).tolist()}')


m = trimesh.load(src, force='mesh')
vc = m.visual.to_color().vertex_colors
g = trimesh.Trimesh(m.vertices, m.faces, vertex_colors=vc, process=False)
g.merge_vertices(merge_tex=True, merge_norm=True)
g.remove_unreferenced_vertices()
# Tripo GLB: Y-up, face toward +X  ->  Z-up, face toward -Y  (verify per model!)
R = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]], float)
T = np.eye(4); T[:3, :3] = R
g.apply_transform(T)
if g.volume < 0:
    g.invert()
g.apply_scale(H / np.ptp(g.vertices[:, 2]))
b = g.bounds
g.apply_translation([-(b[0, 0] + b[1, 0]) / 2, -(b[0, 1] + b[1, 1]) / 2, -b[0, 2]])
report('full', g)
g.export(f'{out}/{name}_{int(H)}mm.stl')
g.export(f'{out}/{name}_{int(H)}mm.obj', include_color=True)

# light version
import fast_simplification, pymeshfix
from scipy.spatial import cKDTree
v, f = fast_simplification.simplify(g.vertices.astype(np.float32), g.faces.astype(np.int32), target_reduction=0.75)
mf = pymeshfix.MeshFix(v, f)
mf.repair(joincomp=False, remove_smallest_components=True)
d = trimesh.Trimesh(mf.points, mf.faces, process=True)
if d.volume < 0:
    d.invert()
_, idx = cKDTree(g.vertices).query(d.vertices)
d.visual.vertex_colors = g.visual.vertex_colors[idx]
report('light', d)
d.export(f'{out}/{name}_{int(H)}mm_light.stl')
d.export(f'{out}/{name}_{int(H)}mm_light.obj', include_color=True)
