---
name: pc-file-organizer
description: Windows PCのデスクトップ・ドキュメント・外付けハードディスクのファイル整理を安全に自律実行する。棚卸しCSV→分類ルール→ドライラン→移動（削除しない）→重複はハッシュで検出→ログと元に戻すスクリプト。「デスクトップ整理」「ハードディスク整理」「ファイル整理」「重複ファイル」で発動。
---

# PC／HDD ファイル整理（安全第一）

## 絶対ルール
1. **削除しない**。不要候補は `_整理待ち\YYYYMMDD\` へ移動し、本人確認後に削除。
2. 最初に必ず**棚卸し（読み取りのみ）**→ 分類案を提示 → 承認後に移動。
3. Windows・Program Files・AppData・OneDriveの同期設定・ドライブ直下のシステムフォルダには触れない。
4. すべての移動を CSV ログ（元パス, 新パス, サイズ, SHA256）に残し、ログから戻す `undo.ps1` を同時生成。

## 台本：`scripts/organize.ps1`（PowerShell 7 で検証済み）
```
pwsh -File organize.ps1 -Mode Inventory -Root "$env:USERPROFILE\Desktop"   # 棚卸し（読み取りのみ）
pwsh -File organize.ps1 -Mode Plan -Root "$env:USERPROFILE\Desktop"        # 計画 plan.csv（移動しない）
pwsh -File organize.ps1 -Mode Apply                                       # 承認後に実行（move_log.csv）
pwsh -File organize.ps1 -Mode Undo                                        # 元に戻す
# 外付けHDD： -Root "E:\" -Dest "E:\整理済み" -Recurse
```
- 作業ファイル：`ドキュメント\クロードコード\file-organizer\`、整理先の既定：`ドキュメント\整理済み\`
- 拡張子で 3D（STL_印刷用/スライス済/Blender/Rhino/Fusion_STEP/ZBrush/交換形式）・図面・写真（年\年-月）・動画・ドキュメント・アーカイブに分類。
- 重複は SHA256 で判定し、パスが短い方を残して `_整理待ち\日付\重複` へ。インストーラーも `_整理待ち` へ。
- `.lnk/.url/desktop.ini`・隠し/システムファイルは触らない。同名衝突は `_2` を付与。
- 検証内容：12ファイル（重複2組・ショートカット・サブフォルダ・2024年の写真）で 計画→実行→元に戻す を通し、11件の移動と11件の復元を確認。
- Windows PowerShell 5.1 でも動く書き方だが、PowerShell 7（pwsh）推奨。実行ポリシーで止まる場合は `-ExecutionPolicy Bypass`。

## 1. 棚卸し（PowerShell・読み取りのみ）
```powershell
$root = "$env:USERPROFILE\Desktop"
Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue |
  Select FullName, Extension, Length, LastWriteTime |
  Export-Csv "$env:USERPROFILE\Documents\inventory_desktop.csv" -NoTypeInformation -Encoding UTF8
```
外付けHDDは `$root = "E:\"` 等。容量上位100件と拡張子別集計を報告する。

## 2. 分類ルール（本人向け既定）
```
ドキュメント\クロードコード\YYYY_MM\        ← Claudeとの成果物
仕事\案件\YYYY_案件名\{01_図面,02_写真,03_3D,04_見積,05_納品}
ポートフォリオ\YYYY\{原稿,写真,出力PDF}
3D\{Blender,Rhino,Fusion,ZBrush,STL_印刷用,スライス済}
写真\YYYY\YYYY-MM\        ← EXIF撮影日で振り分け
就職活動\{履歴書,職務経歴書,応募先別}
```
ファイル名：`YYYYMMDD_案件名_内容_v01.ext`（日付は先頭、版数は末尾）。

## 3. 重複検出
```powershell
Get-ChildItem $root -Recurse -File | Get-FileHash -Algorithm SHA256 |
  Group-Object Hash | Where-Object Count -gt 1 | ForEach-Object { $_.Group.Path }
```
重複は最新・最も整理された場所の1つを残し、他は `_整理待ち` へ。

## 4. 実行
- ドライラン：移動予定表（元→先）を表示して承認を取る。
- 本番：`Move-Item -LiteralPath`（同名衝突は `_2` 付与）＋ログ。大容量のHDD間コピーは `robocopy src dst /E /COPY:DAT /R:1 /W:1 /LOG:log.txt`。

## 前提
クラウドセッションからはPCのファイルに触れない。PC上のClaude Code（CLI/デスクトップ）で実行する。
