---
name: fusion360-automation
description: Autodesk Fusion（Fusion 360）の設定変更・API（Python）スクリプト・アドインでのモデリング自動化、STL/3MF/STEP書き出し。マウス操作（パン/ズーム/オービット）をTinkercad等の方式に変える設定も。「フュージョン」「Fusion 360」「パラメトリック」「STEP」で発動。
---

# Fusion 自動化

## 操作設定（よく聞かれる）
- マウスの「パン・ズーム・オービット」方式：右上の名前 → **基本設定 (Preferences) → 一般 → 「パン、ズーム、オービットのショートカット」** → `Tinkercad` / `Fusion` / `Alias` / `Inventor` / `SolidWorks` / `PowerMill` から選択 → 適用。
- これはGUI設定なので、Claude が行うには **PC上のClaudeデスクトップアプリでコンピュータ操作（Computer use）を有効**にした会話が必要。クラウドやCLIセッションからは変更できない（実例：2026-10-21 のセッションで不可）。

## 台本：`scripts/ParamBoxExport/`（構文チェック済み・PCで要検証）
フォルダごと `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\` にコピー → Shift+S → 実行。
`PARAMS = {'W','D','H','T'}`（mm）を書き換えるだけで、ユーザーパラメータ付きの肉厚シェル箱を作り、`ドキュメント\クロードコード\fusion\` に STL（高精度）と STEP を書き出す。案件ごとの外形・カバー・治具の雛形として使う。

## API スクリプト（自律実行の基本）
- 置き場所：`%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\<名前>\<名前>.py`（+ .manifest）
- 実行：ユーティリティ → アドイン → スクリプトとアドイン（Shift+S）→ 実行。完全自動化はアドインの起動時実行（`runOnStartup: true`）。
```python
import adsk.core, adsk.fusion
def run(context):
    app = adsk.core.Application.get(); des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(10,5,0))  # cm単位
    prof = sk.profiles.item(0)
    ext = root.features.extrudeFeatures.addSimple(prof, adsk.core.ValueInput.createByString('20 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    em = des.exportManager
    opt = em.createSTLExportOptions(root, r'C:\out\part.stl'); opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    em.execute(opt)
```
- 内部単位は **cm**。mm で渡すときは ValueInput の文字列に単位を付ける。
- 寸法はユーザーパラメータ（`des.userParameters.add`）で管理し、案件ごとに値だけ差し替える。

## 書き出し
STL（3Dプリント）／3MF（色・複数ボディ）／STEP（他CAD・Rhinoへ）／DXF（スケッチ）。
