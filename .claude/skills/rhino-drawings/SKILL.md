---
name: rhino-drawings
description: Rhinoceros 8（＋Grasshopper）をスクリプトで操作し、製作図面・三面図（Make2D）・展開・分割検討・DWG/DXF/PDF/STL書き出しを行う。図面から立体を起こす、立体から三面図を出す作業もこれ。「ライノ」「Rhino」「Make2D」「三面図」「図面から立体」「DXF」で発動。
---

# Rhino 8 自動化と図面化

## 実行方法（PC上のセッションで）
- **RhinoCode CLI**：Rhino 8 の `rhinocode` で起動中のRhinoにスクリプト送信  
  `rhinocode list` → `rhinocode script path\to\job.py`（Python 3 / CPython）
- **バッチ**：`Rhino.exe /nosplash /runscript="_-RunPythonScript path\job.py _-Exit"` 
- **Rhino不要の処理**：`pip install rhino3dm` で .3dm の読み書き（形状の作成・属性・レイヤー）。Make2D等のコマンドは不可。
- クラウド環境では Rhino は動かない。.3dm を受け取り rhino3dm で解析・変換まで、図面化はPC側で。

## 台本
- `scripts/rhino3dm_tools.py`（Rhino不要・**検証済み**）
  - `python rhino3dm_tools.py inspect model.3dm`：単位・レイヤー・オブジェクト・全体寸法の一覧
  - `python rhino3dm_tools.py mesh2dm in.stl out.3dm MESH_スキャン`：STL/OBJ/PLY → .3dm（mm）
  - `python rhino3dm_tools.py box out.3dm 2000 2000 2400`：輸送寸法・分割検討用の外形の箱
- `scripts/make2d_three_views.py`（Rhino 8 内で実行。**構文チェックのみ、PCで要検証**）
  - 選択物から 正面・右側面・平面 を Make2D → `DRAW_外形/DRAW_隠れ線/DIM_寸法` レイヤーに整理 → 全体寸法 → `ドキュメント\クロードコード\make2d\three_views.dxf`
  - 実行：`rhinocode script make2d_three_views.py`

## 三面図（Make2D）手順
1. 対象を選択 → ビューを Front/Right/Top/Back に切替 → `_-Make2D` （隠れ線を別レイヤー、投影は第三角法）。
2. 出力を図面レイヤー（`DRAW_外形`, `DRAW_隠れ線`, `DIM_寸法`）に整理。
3. 寸法：`_DimLinear` 全幅・全高・全奥行＋分割位置。縮尺は 1/10・1/20・1/50 を案件で固定。
4. 書き出し：`_-Export file.dxf`（AutoCAD 2018 形式, mm）、PDFは `_-Print` で用紙A3横。

## 図面から立体（既存図面→3D）
1. 三面図画像/PDFを各ビューに `_Picture` で配置、縮尺合わせ（既知寸法で `_Scale1D`）。
2. 外形をカーブでトレース → `_ExtrudeCrv`／`_Loft`／`_NetworkSrf`。有機形状は SubD（`_SubDFromMesh` 等）か ZBrush へ。
3. 写真しかない場合は photo-to-3d-print スキルで多視点再構成 → Rhinoで寸法合わせ。

## 造形（FRP・大型）向けの検討
- 分割：輸送寸法（例 2,000×2,000×2,400 以内）とFRP型の抜き勾配で分割線を決める。
- 肉厚：FRP 3〜5mm、補強リブ、設置アンカー位置を図面に明記。
- 発泡（スチロール）切削用には面を STL（0.5mm 許容差）で出力。

## 出力チェックリスト
単位mm／縮尺表記／第三角法表記／全体寸法3方向／分割線／素材・仕上げ注記／改訂日。
