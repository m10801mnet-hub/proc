# 的場道雄 スキル集（Claude Code / claude.ai 共通）

これまでClaudeと行った作業から抽出したノウハウ。各フォルダの `SKILL.md` が1スキル、`scripts/` が実行用の台本。

| スキル | 用途 | 台本 | 検証状況 |
|---|---|---|---|
| portfolio-a3-spread | ポートフォリオ48p・A3見開き・図面｜実物比較 | build_portfolio_48p.py | ✅ 48p PPTX→PDF 生成を確認 |
| photo-to-3d-print | 実物写真→Tripo多視点3D→穴なしSTL/OBJ | finalize_mesh.py | ✅ 実モデルで watertight・非多様体0 を確認 |
| blender-headless | Blenderのスクリプト操作・六面図・SDFモデリング | sdf_character_example.py, render_scene.py | ✅ Blender 4.0 で生成・レンダー確認 |
| 3dprint-slicing | 検査・CuraEngine自動スライス・CHITUBOX手順 | print_check.py, slice_cura.py | ✅ Cura 5.13 で Ender-3 / K1 Max のG-code生成を確認 |
| rhino-drawings | Rhino 8 自動化・Make2D三面図・.3dm読み書き | rhino3dm_tools.py, make2d_three_views.py | ✅ rhino3dm ／ ⚠ Make2DはPCで要確認 |
| pc-file-organizer | デスクトップ/HDD整理（削除しない・ログ・元に戻す） | organize.ps1 | ✅ PowerShell 7 で 計画→実行→復元 を確認 |
| fusion360-automation | Fusion 設定変更・APIスクリプト | ParamBoxExport/ | ⚠ 構文のみ。PCで要確認 |
| unreal-engine-automation | UE5 取り込み・4方向4K静止画 | import_and_shoot.py | ⚠ 構文のみ。PCで要確認 |
| career-job-search | 求人リサーチ・職務経歴書・MATOBA MODEL判断 | — | 手順 |
| work-reports | 朝報告・ルーティン報告・スレッド統合 | — | 雛形（過去の報告書で要追記） |
| pc-autonomy-setup | クラウド/PC/コンピュータ操作の使い分け・許可設定 | — | 手順 |

## インストール
- **PC（全プロジェクトで使う・推奨）**：リポジトリ直下の `install_skills.bat` をダブルクリック
  → `%USERPROFILE%\.claude\skills\` に11本をコピー（既存の同名スキルは `%USERPROFILE%\.claude\skills_backup\日時\` に退避）。
  最新化して入れ直す：`pwsh -File install_skills.ps1 -Pull`
- **このリポジトリで開いたセッション**：自動で読み込まれる（設定不要）。
- **claude.ai（スマホ・Web）**：`dist/` のスキル別 zip を 設定 → 機能 → スキル からアップロード。

## 呼び出し方
`/portfolio-a3-spread` のようにスラッシュで呼ぶか、「ポートフォリオを作って」「STLにして」等の依頼で自動発動。
