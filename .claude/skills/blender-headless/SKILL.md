---
name: blender-headless
description: Blenderをコマンドライン（blender -b -P script.py）とPythonで自律操作する。モデリング（SDF/メタボール的な有機形状→marching cubes）、マテリアル（ノードで色分けマスク）、ライト・カメラ、正投影の6面図（正面/左右/背面/上/下）レンダー、.blend保存、STL/OBJ/GLB書き出し。「ブレンダー」「Blender」「レンダー」「三面図を出して」「モデリング」で発動。
---

# Blender ヘッドレス自動化

## 基本
- 実行：`blender -b -P script.py -- 引数...`（`sys.argv[sys.argv.index('--')+1:]` で受け取る）
- 空シーンから：`bpy.ops.wm.read_factory_settings(use_empty=True)`
- 大量メッシュは `me.vertices.foreach_set('co', ...)` 等の foreach 系で流し込む（from_pydata は遅い）。
- ユーザーPCで「今開いているBlender」を触るには、PC上のセッション（デスクトップアプリ＋コンピュータ操作、または Blender MCP）が必要。クラウドからは .blend をGitHub等で受け取って処理する。

## 正投影の三面図／六面図（図面用）
```python
cam.data.type='ORTHO'; cam.data.ortho_scale=1.62
views={'01_front':(0,-5,0),'02_left':(5,0,0),'03_back':(0,5,0),'04_right':(-5,0,0)}
# 上面：rotation (0,0,0)、下面：rotation (pi,0,0)（ライトも下へ回す）
```
- 背景は白・床は非表示（Image-to-3D入力にも使える）。

## レンダー設定（Cycles・CPU）
- `sc.render.engine='CYCLES'`、確認用16〜24サンプル、本番160。
- apt版Blender 4.0 は OpenImageDenoise 無し → `use_denoising=False`（ONだと Error で止まる）。
- 色管理：`view_transform='Filmic'`, `look='Medium High Contrast'`（4.0ではlook名に "Filmic - " を付けない）。AgX は黄色が淡くなる。
- 3点照明：Key 650W（左前上）、Fill 160W、Rim 600W（後ろ上）、Area size 2〜3m。

## マテリアルの色分け（UV不要・境界がシャープ）
Texture Coordinate(Object) → Vector Math（DOT/DISTANCE）→ Map Range(SMOOTHSTEP) でマスクを作り、Mix(RGBA) で塗り分け。例：耳先の黒＝耳軸方向の比率t>0.64、ほっぺ＝中心からの距離<0.063。

## 有機形状モデリング（scripts/sdf_character_example.py）
- numpy で SDF（楕円体・round cone・smooth min）→ `skimage.measure.marching_cubes` → Blender に流し込み → Corrective Smooth。
- 指・足指の隙間は「掌と各指を個別に smin → 指同士は min」で隙間を残す。隙間はボクセル2個分以上（0.003刻みなら0.006以上）。
- 溝（耳の境界線・口）は SDF に gauss で凹みを加算。

## 書き出し
- Blender 4.0：STL は `bpy.ops.export_mesh.stl`（`wm.stl_export` は4.2以降）。
- 穴なし検査は trimesh で数値確認（photo-to-3d-print スキル参照）。

## 教訓
- キャラクターの「作り直し」は、自作SDFより実物写真からの多視点再構成の方が評価が高かった。キャラクターの再現なら photo-to-3d-print を先に検討する。
- 長時間レンダーはバックグラウンド実行＋ログ監視。止めるときに `pkill -f` のパターンが自分のコマンドに当たらないよう注意。
