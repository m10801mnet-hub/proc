---
name: 3dprint-slicing
description: 3Dプリント前のデータ検査とスライス。FDM（Cura / CuraEngine CLI）と光造形（CHITUBOX、代替CLIとしてUVtools）。穴なし検査、肉厚、向き、サポート、中空化と排出穴、スケール、G-code/ctb出力。「3Dプリント」「キュラ」「Cura」「チツボックス」「CHITUBOX」「スライス」「サポート」で発動。
---

# 3Dプリント：検査とスライス（台本は検証済み）

## 1. データ検査 — `scripts/print_check.py`（検証済み）
```
pip install trimesh numpy scipy rtree
python print_check.py model.stl [--scale-to-height 100] [--resin]
```
出力：watertight／境界エッジ／非多様体エッジ／ボディ数／寸法mm／体積とPLA・レジン重量／薄肉率（FDM 1.2mm・光造形0.8mm未満）／45°超オーバーハング率→サポート要否。終了コード 0=スライス可、1=修復が先（photo-to-3d-print の finalize_mesh.py へ）。
- 44万面のメッシュで約1分。光線判定は50本ずつに分けて実行（一括だとメモリ不足で落ちた）。
- 光造形の中空化：肉厚2〜3mm、排出穴 φ3〜4mm を2か所以上。

## 2. FDM：`scripts/slice_cura.py`（CuraEngine 5.13 で検証済み）
CuraEngine 単体は画面版Curaが計算する設定を受け取れず `no value given: X` で止まる。この台本はプリンター定義の継承チェーン＋エクストルーダー定義を解決して全設定を渡し、それでも足りない値は自動補完して再試行する。
```
# Windows（Curaインストール済み）
python slice_cura.py model.stl out.gcode --printer creality_ender3 --cura "C:\Program Files\UltiMaker Cura 5.13.0"
# 設定の上書き
python slice_cura.py model.stl out.gcode --printer creality_k1max --cura "<Cura>" --set layer_height=0.2 --set infill_sparse_density=20
```
- 既定プロファイル（フィギュア向け）：積層0.12mm、壁3、インフィル12%、ツリーサポート、ブリム。
- プリンター名は `<Cura>\share\cura\resources\definitions\*.def.json` のファイル名（creality_ender3, creality_k1max, prusa_i3 …）。
- 実測（ピカチュウ100mm・軽量版STL）：Ender-3 0.12mm → 832層・12時間29分・76g／K1 Max 0.2mm → 499層・7時間12分・76g。G-codeは温度215/60℃、開始G-code入り、造形範囲中央に配置。
- 注意：CLIで書かれたG-codeヘッダーの `;TIME:6666`・`;Filament used: 0m`・MINX等は**仮の値**。正しい時間と材料はエンジンのログ（台本が表示）を使う。
- Linuxでは AppImage を `--appimage-extract` し、同梱ローダー（runtime/compat/lib64/ld-linux）経由で起動する（台本が自動対応）。Windowsはそのまま。
- コマンド長は約2.4万字（Windows上限3.2万字以内）。

## 3. 光造形：CHITUBOX
- 公式CLIが無い → 自律操作は **PC上のClaudeデスクトップ＋コンピュータ操作**が必要。
- 代替：UVtools（無料・CLIあり）でスライス済みファイルの検査（島・レジン溜まり）。メッシュのスライス自体はできない。
- 標準手順：30〜45°傾け（顔はサポート跡が付かない向き）→ 中空化2mm＋排出穴 → 自動サポート（中）＋手動追加（指先・耳先・尻尾）→ 層厚0.05mm → 露光はレジンの推奨値 → `.ctb` 出力。

## 4. 出力前チェック
スケール／向き／サポート接点が見せ面に無い／ブリム・ラフト／所要時間と材料量を報告。
