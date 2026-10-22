---
name: pc-autonomy-setup
description: ClaudeがユーザーのPC（Windows）上のアプリ（Blender・Rhino・Fusion・Unreal・Cura・CHITUBOX・エクスプローラー）を自律操作できる環境を整える／どの方法で実行すべきか判断する。クラウドセッションとPCセッションの使い分け、許可プロンプトを減らす設定、MCP、コンピュータ操作の有効化。「PCを操作して」「自律的に」「許可を出さないで」「開いているアプリで」で発動。
---

# PC自律操作の環境と判断

## まず判定：今どこで動いているか
| セッション | できること | できないこと |
|---|---|---|
| クラウド（claude.ai/code・スマホから起動） | GitHubリポジトリ、Google Drive(10MB上限)、Higgsfield等のMCP、Linux上でBlender/LibreOffice | PCのファイル・PCで開いているアプリ |
| PCのClaude Code（CLI） | PCのファイル操作、PowerShell、各アプリのCLI/スクリプト | GUIのクリック操作 |
| PCのClaudeデスクトップアプリ＋コンピュータ操作 | 画面を見てGUI操作（設定画面・CHITUBOX等CLIのないアプリ） | 速度・精度はスクリプトに劣る |

**原則：スクリプト/CLIがあるものはスクリプトで（精度が高い）。GUIしかないものだけコンピュータ操作。**

## アプリ別の最適な操作方法
- Blender：`blender -b -P`（blender-headless）／開いているBlenderならBlender MCPアドオン
- Rhino 8：`rhinocode` CLI（rhino-drawings）
- Fusion：APIスクリプト/アドイン。基本設定の変更はコンピュータ操作（fusion360-automation）
- Unreal：Python＋`UnrealEditor-Cmd`（unreal-engine-automation）
- Cura：CuraEngine CLI／CHITUBOX：コンピュータ操作（3dprint-slicing）
- ファイル整理：PowerShell（pc-file-organizer）

## 許可プロンプトを減らす（ユーザー自身が設定）
- Claudeアプリでセッションの許可モードを **Auto** または **Bypass permissions** にする。
- PCの `%USERPROFILE%\.claude\settings.json` に許可ルールを追加（例）：
```json
{ "permissions": { "allow": ["Bash", "Read", "Edit", "Write", "WebSearch", "WebFetch", "mcp__higgsfield__*"] } }
```
- Claude自身はこの設定を書き換えられない（安全制限で拒否される）。必要なら手順を案内する。

## スキルを全セッションで使う
- このリポジトリの `.claude/skills/` はこのリポジトリで開いたセッションでのみ有効。
- PCのどこでも使うには：リポジトリ（github.com/m10801mnet-hub/proc）を clone して `install_skills.bat` を実行 → `%USERPROFILE%\.claude\skills\` に全スキルが入る。更新は `pwsh -File install_skills.ps1 -Pull`。
- claude.ai 全体に配るには：`.claude/skills/dist/*.zip` を 設定→機能→スキル にアップロード。
- PowerShell台本（.ps1）は日本語を含むので **UTF-8 BOM付き** で保存する（BOM無しだとWindows PowerShell 5.1で文字化けしフォルダ名が壊れる）。

## クラウドからの受け渡しの定石
- 大きいファイル（>10MB）はGoogle Driveでは取れない → GitHubへアップロード（1ファイル25MB）してもらう。
- 成果物はSendUserFileで渡し、保存先（例：ドキュメント\クロードコード\YYYY_MM）を明記。
