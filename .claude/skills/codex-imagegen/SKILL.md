---
name: codex-imagegen
description: 画像生成をClaude自身やHiggsfield等ではなく、Codex（OpenAI Codex CLI の画像生成ツール $imagegen）に任せる。Claude Code が codex exec を裏で呼び、生成画像を指定フォルダに保存して受け取る。新規生成・参照画像からの編集・複数案・背景透過。「画像生成」「画像を作って」「絵を描いて」「イメージ図」「パース画像」「コーデックスで」「Codexで」で発動。
---

# 画像生成は Codex に任せる

**原則：画像の生成・編集はこのスキル経由で Codex に依頼する。** Claude はプロンプト設計・結果確認・後処理（トリミング、ポートフォリオ配置等）を担当。
ユーザーが別ツール（Higgsfield / Canva / Figma）を名指しした場合だけそちらを使う。

## 前提（PCで1回だけ）
1. Node.js を入れる → `npm i -g @openai/codex`
2. `codex login` → ChatGPT アカウントでログイン（Plus/Pro 等の枠で画像生成。API キーなら `printenv OPENAI_API_KEY | codex login --with-api-key`）
3. 確認：`python "%USERPROFILE%\.claude\skills\codex-imagegen\scripts\codex_image.py" check` → `"ok": true`

クラウドセッション（claude.ai/code）では Codex にログインできないため **PCの Claude Code で実行する**。クラウドで頼まれたら、その旨を伝えてプロンプト案だけ作る。

## 実行（Claude が Bash で叩く）
スクリプト：`<このスキルのフォルダ>/scripts/codex_image.py`（PC: `%USERPROFILE%\.claude\skills\codex-imagegen\scripts\codex_image.py`）

```bash
# 新規
python codex_image.py gen "プロンプト" -o out/booth.png
# 横長・高品質・3案（out/booth_1.png, _2, _3）
python codex_image.py gen "プロンプト" -o out/booth.png --size 1536x1024 --quality high -n 3
# 参照画像から編集（複数 -i 可）
python codex_image.py gen "この写真の壁面をFRPの擬岩に置き換え" -i photo.jpg -o out/edit.png
# 背景透過（ロゴ・切り抜き素材）
python codex_image.py gen "FRP造形の恐竜オブジェ、単体" --transparent -o out/dino.png
```
- 出力は JSON。`"ok": true` なら `files` のパスを Read で開いて目視確認する。
- 1枚あたり 1〜3 分。複数枚・高品質はもっとかかる。Bash の timeout は 600000ms にする。
- 失敗時は `error` と `codex_log_tail` を読む。exit 3 = 未ログイン。

## プロンプトの組み立て（Claude の仕事）
日本語でよいが、次の5要素を必ず入れる：
1. **用途**（展示会ブースのイメージパース／ポートフォリオ表紙／施工説明図 …）
2. **被写体と寸法感**（W6m×D3m の小間、高さ 2.7m、来場者のスケール人物入り …）
3. **素材・色**（木目、FRP 塗装、白い造作壁、間接照明）
4. **構図・カメラ**（正面アイレベル、斜め 45°俯瞰、35mm 相当）
5. **画風**（フォトリアル／手描きスケッチ風／白模型風）と **入れないもの**（文字・ロゴは入れない 等）

実在のブランド・ロゴ・人物の再現は避ける。文字入れが必要なら画像生成ではなく後工程（PowerPoint 等）で入れる。

## 仕組み（トラブル時）
- `codex exec`（非対話）に「内蔵の画像生成ツールで作れ、コードで描くな」と指示して実行。
- Codex は生成画像を `%USERPROFILE%\.codex\generated_images\...` に保存する。スクリプトは実行前後の差分で新しい画像を拾い、`-o` のパスにコピーする。
- 画像が出ない：`codex features list` で `image_generation ... true` か確認。`codex update` で最新化。
- Codex の実行場所は `-o` のフォルダ（`--sandbox workspace-write`）。他のフォルダは触らない。
- Codex 本体を別パスに入れた場合は環境変数 `CODEX_BIN` で指定。
