"""Rhino 不要で .3dm を扱う（pip install rhino3dm trimesh numpy）。
usage:
  python rhino3dm_tools.py inspect model.3dm              # レイヤー・オブジェクト・全体寸法の一覧
  python rhino3dm_tools.py mesh2dm in.stl out.3dm [LAYER] # STL/OBJ/PLY → .3dm（単位mm、指定レイヤー）
  python rhino3dm_tools.py box out.3dm W D H              # 寸法確認用の箱（輸送・分割検討の外形）
"""
import sys
import rhino3dm as r3


def inspect(path):
    f = r3.File3dm.Read(path)
    if f is None:
        sys.exit(f'cannot read {path}')
    print(f'file: {path}  units: {f.Settings.ModelUnitSystem}  objects: {len(f.Objects)}  layers: {len(f.Layers)}')
    for i in range(len(f.Layers)):
        L = f.Layers[i]
        print(f'  layer[{L.Index}] {L.FullPath}')
    bb = None
    for o in f.Objects:
        g = o.Geometry
        b = g.GetBoundingBox()
        bb = b if bb is None else r3.BoundingBox.Union(bb, b)
        print(f'  {type(g).__name__:<14} layer={o.Attributes.LayerIndex} name="{o.Attributes.Name}" '
              f'size=({b.Max.X-b.Min.X:.1f}, {b.Max.Y-b.Min.Y:.1f}, {b.Max.Z-b.Min.Z:.1f})')
    if bb:
        print(f'overall size: X {bb.Max.X-bb.Min.X:.1f}  Y {bb.Max.Y-bb.Min.Y:.1f}  Z {bb.Max.Z-bb.Min.Z:.1f}')


def new_file():
    f = r3.File3dm()
    f.Settings.ModelUnitSystem = r3.UnitSystem.Millimeters
    return f


def add_layer(f, name, rgb=(0, 0, 0)):
    L = r3.Layer(); L.Name = name; L.Color = (*rgb, 255)
    return f.Layers.Add(L)


def mesh2dm(src, dst, layer='MESH_IMPORT'):
    import trimesh
    t = trimesh.load(src, force='mesh')
    m = r3.Mesh()
    for v in t.vertices:
        m.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    for a, b, c in t.faces:
        m.Faces.AddFace(int(a), int(b), int(c))
    m.Normals.ComputeNormals(); m.Compact()
    f = new_file()
    li = add_layer(f, layer, (200, 120, 0))
    at = r3.ObjectAttributes(); at.LayerIndex = li; at.Name = src.split('/')[-1]
    f.Objects.AddMesh(m, at)
    f.Write(dst, 8)
    print(f'wrote {dst}: {len(t.vertices)} verts, {len(t.faces)} faces on layer {layer}')


def box(dst, w, d, h):
    f = new_file()
    li = add_layer(f, 'DIM_外形', (255, 0, 0))
    at = r3.ObjectAttributes(); at.LayerIndex = li; at.Name = f'{w}x{d}x{h}'
    bb = r3.BoundingBox(r3.Point3d(0, 0, 0), r3.Point3d(w, d, h))
    f.Objects.AddBrep(r3.Brep.CreateFromBox(r3.Box(bb)), at)
    f.Write(dst, 8)
    print(f'wrote {dst}: box {w}x{d}x{h} mm')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'inspect':
        inspect(sys.argv[2])
    elif cmd == 'mesh2dm':
        mesh2dm(sys.argv[2], sys.argv[3], *(sys.argv[4:5]))
    elif cmd == 'box':
        box(sys.argv[2], *map(float, sys.argv[3:6]))
    else:
        print(__doc__)
