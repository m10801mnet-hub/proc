"""Printability check for STL/OBJ/3MF/PLY.
usage: python print_check.py model.stl [--scale-to-height MM] [--fdm|--resin]
Reports: watertight / non-manifold / bodies / size(mm) / volume / est. material /
         thin-wall share (ray test) / overhang share (>45deg from vertical, downward).
Exit code 0 = OK to slice, 1 = needs repair.
needs: pip install trimesh numpy scipy rtree
"""
import sys, argparse, numpy as np, trimesh

ap = argparse.ArgumentParser()
ap.add_argument('path')
ap.add_argument('--scale-to-height', type=float)
ap.add_argument('--resin', action='store_true')
a = ap.parse_args()

m = trimesh.load(a.path, force='mesh')
if a.scale_to_height:
    m.apply_scale(a.scale_to_height / np.ptp(m.vertices[:, 2]))
_, cnt = np.unique(m.edges_sorted, axis=0, return_counts=True)
boundary, nonman = int((cnt == 1).sum()), int((cnt > 2).sum())
size = np.ptp(m.vertices, 0)
ok = m.is_watertight and nonman == 0 and boundary == 0
vol_cm3 = abs(m.volume) / 1000 if m.is_volume else float('nan')

# thin walls: shoot rays inward from sampled surface points, measure distance to opposite wall
min_wall = 0.8 if a.resin else 1.2
pts, fi = trimesh.sample.sample_surface(m, 1500, seed=1)
dirs = -m.face_normals[fi]
th = np.full(len(pts), np.inf)
for s in range(0, len(pts), 50):  # small chunks keep the rtree candidate set (and RAM) bounded
    sl = slice(s, s + 50)
    locs, ri, _ = m.ray.intersects_location(pts[sl] + dirs[sl] * 1e-3, dirs[sl], multiple_hits=False)
    th[s + ri] = np.linalg.norm(locs - pts[sl][ri], axis=1)
thin_share = float((th < min_wall).mean())

# overhang: downward faces steeper than 45deg, excluding the bed (z near min)
n = m.face_normals
zc = m.triangles_center[:, 2]
down = (n[:, 2] < -np.cos(np.radians(45))) & (zc > m.bounds[0, 2] + 0.5)
overhang_share = float(m.area_faces[down].sum() / m.area)

print(f'file            : {a.path}')
print(f'watertight      : {m.is_watertight}   boundary edges: {boundary}   non-manifold edges: {nonman}')
print(f'bodies          : {m.body_count}')
print(f'size (mm)       : X {size[0]:.1f}  Y {size[1]:.1f}  Z {size[2]:.1f}')
print(f'volume          : {vol_cm3:.2f} cm3   est. {"resin" if a.resin else "PLA"} {vol_cm3 * (1.1 if a.resin else 1.24):.1f} g (solid)')
print(f'thin walls      : {thin_share*100:.1f}% of samples thinner than {min_wall} mm')
print(f'overhang >45deg : {overhang_share*100:.1f}% of surface  -> {"supports needed" if overhang_share > 0.02 else "supports optional"}')
print('RESULT          :', 'OK to slice' if ok else 'REPAIR FIRST (see photo-to-3d-print/scripts/finalize_mesh.py)')
sys.exit(0 if ok else 1)
