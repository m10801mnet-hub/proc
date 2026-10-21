# 的場道雄 スキル集（Claude Code / claude.ai 共通）

これまでClaudeと行った作業から抽出したノウハウ。各フォルダの `SKILL.md` が1スキル。

| スキル | 用途 | 状態 |
|---|---|---|
| portfolio-a3-spread | ポートフォリオ48p・A3見開き・図面｜実物比較、生成スクリプト付き | 実証済み |
| photo-to-3d-print | 実物写真→Tripo多視点3D→穴なしSTL/OBJ、仕上げスクリプト付き | 実証済み |
| blender-headless | Blenderのスクリプト操作・六面図レンダー・SDFモデリング | 実証済み |
| 3dprint-slicing | 検査・Cura(CLI)・CHITUBOX/UVtools | 手順化（PCで要検証） |
| rhino-drawings | Rhino 8 自動化・Make2D三面図・図面→立体 | 手順化（PCで要検証） |
| fusion360-automation | Fusion 設定変更・APIスクリプト | 手順化（PCで要検証） |
| unreal-engine-automation | UE5 Python・取り込み・スクショ | 手順化（PCで要検証） |
| pc-file-organizer | デスクトップ/HDD整理（削除しない・ログ・undo） | 手順化（PCで要検証） |
| career-job-search | 求人リサーチ・職務経歴書・MATOBA MODEL判断 | 手順化 |
| work-reports | 朝報告・ルーティン報告・スレッド統合 | 雛形（要追記） |
| pc-autonomy-setup | クラウド/PC/コンピュータ操作の使い分け・許可設定 | 手順化 |

## 使い方
- このリポジトリで開いたセッション：自動で読み込まれる。`/portfolio-a3-spread` のように呼ぶか、内容に応じて自動発動。
- PCの全セッションで使う：各フォルダを `%USERPROFILE%\.claude\skills\` にコピー。
- claude.ai（スマホ・Web含む全体）：`dist/` の zip を 設定 → 機能 → スキル からアップロード。
