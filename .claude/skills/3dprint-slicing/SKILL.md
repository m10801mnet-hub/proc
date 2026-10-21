---
name: 3dprint-slicing
description: 3Dプリント前のデータ検査とスライス。FDM（Cura / CuraEngine CLI）と光造形（CHITUBOX、代替CLIとしてUVtools）。穴なし検査、肉厚、向き、サポート、中空化と排出穴、スケール、G-code/ctb出力。「3Dプリント」「キュラ」「Cura」「チツボックス」「CHITUBOX」「スライス」「サポート」で発動。
---

# 3Dプリント：検査とスライス

## 1. データ検査（必須・数値で）
trimesh で：watertight=True／非多様体エッジ0／境界エッジ0／body_count（意図通り）／寸法mm。NGなら photo-to-3d-print の修復手順へ。
- 最小肉厚：FDM 1.2mm以上（ノズル0.4×3）、光造形 0.8mm以上（細部0.5mm）。
- 光造形の中空化：肉厚2〜3mm、排出穴 φ3〜4mm を2か所以上（底面付近と対角）。中空のまま穴なしはカッピングで破損。

## 2. FDM：Cura
- GUI：プリンタープロファイルを選択 → 0.2mm標準 → サポート（オーバーハング角 55°）→ ブリム（細い足のフィギュアは必須）。
- CLI（自律実行）：CuraEngine
```
CuraEngine slice -v -j "<Cura>/share/cura/resources/definitions/creality_ender3.def.json" ^
  -s layer_height=0.2 -s infill_sparse_density=15 -s support_enable=true -s adhesion_type=brim ^
  -l model.stl -o model.gcode
```
  ※ `-j` はプリンター定義。設定キーは fdmprinter.def.json の名称。
- フィギュア推奨：0.12mm、壁3、インフィル10〜15%、ツリーサポート。

## 3. 光造形：CHITUBOX
- CHITUBOX には公式CLIが無い → 自律操作は **PC上のClaudeデスクトップ＋コンピュータ操作**が必要。
- 代替：**UVtools**（無料・CLIあり）でスライス済みファイルの検査・修正（島検出、レジン溜まり）。
- 標準手順：向き 30〜45°傾け（顔はサポート跡が付かない面に）→ 中空化2mm＋排出穴 → 自動サポート（中）＋手動追加（指先・耳先・尻尾）→ 層厚0.05mm → 露光はレジンメーカー推奨値 → `.ctb` 出力。

## 4. 出力前チェック
スケール（100mm指定等）／向き／サポート接点が顔・見せ面に無い／ブリム・ラフト／推定時間と材料量を報告。
