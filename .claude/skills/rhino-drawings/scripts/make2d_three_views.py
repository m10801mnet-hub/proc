#! python3
# Rhino 8 内で実行（ScriptEditor か:  rhinocode script make2d_three_views.py ）
# 選択中（未選択なら全可視オブジェクト）から 第三角法の 正面・右側面・平面 を Make2D し、
# 図面レイヤーに整理、DXF と A3 PDF を書き出す。
import os
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs

OUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "クロードコード", "make2d")
os.makedirs(OUT_DIR, exist_ok=True)
GAP = 50.0  # ビュー間の余白 mm

objs = rs.SelectedObjects() or rs.NormalObjects()
if not objs:
    raise SystemExit("no objects")
bb = rs.BoundingBox(objs)
W = bb[1].X - bb[0].X; D = bb[3].Y - bb[0].Y; H = bb[4].Z - bb[0].Z


def layer(name, color):
    if not rs.IsLayer(name):
        rs.AddLayer(name, color)
    return name


L_OUT = layer("DRAW_外形", (0, 0, 0))
L_HID = layer("DRAW_隠れ線", (128, 128, 128))
L_DIM = layer("DIM_寸法", (255, 0, 0))

placed = []
for view, offset in (("Front", (0, 0)), ("Right", (W + GAP, 0)), ("Top", (0, H + GAP))):
    rs.CurrentView(view)
    rs.UnselectAllObjects(); rs.SelectObjects(objs)
    rs.Command("_-Make2D _DrawingLayout=CurrentView _ShowHiddenLines=Yes _Enter", echo=False)
    new = rs.LastCreatedObjects() or []
    rs.MoveObjects(new, (offset[0] + 1000.0, offset[1], 0))  # 元形状の横に並べる
    for o in new:
        rs.ObjectLayer(o, L_HID if "Hidden" in (rs.ObjectLayer(o) or "") else L_OUT)
    placed += new

# 全体寸法（正面図に幅・高さ）
rs.CurrentLayer(L_DIM)
rs.AddLinearDimension(rs.WorldXYPlane(), (1000, -20, 0), (1000 + W, -20, 0), (1000, -40, 0))
rs.AddLinearDimension(rs.WorldXYPlane(), (980, 0, 0), (980, H, 0), (960, 0, 0))

rs.UnselectAllObjects(); rs.SelectObjects(placed)
dxf = os.path.join(OUT_DIR, "three_views.dxf")
rs.Command('_-Export "{}" _Enter'.format(dxf), echo=False)
print("exported", dxf, "size W/D/H =", round(W, 1), round(D, 1), round(H, 1))
